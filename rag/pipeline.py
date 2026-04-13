"""
End-to-end RAG pipeline orchestrator.
Combines retrieval and generation into a single search function.
Uses concurrent execution to minimize total latency.
Detects "similar to" queries and searches by genre/theme, not title.
"""
import re
from concurrent.futures import ThreadPoolExecutor
from rag.retriever import retrieve_similar_movies, build_context_string
from rag.generator import generate_recommendations
from rag.query_parser import parse_query
from database.db_operations import log_interaction, search_movies_by_title


# Patterns that indicate "find me something SIMILAR to X"
_SIMILAR_PATTERNS = [
    r"(?:movies?\s+)?(?:like|similar\s+to|same\s+as|in\s+the\s+style\s+of)\s+(.+)",
    r"(?:recommend|suggest|find)\s+(?:me\s+)?(?:something|movies?)\s+(?:like|similar\s+to)\s+(.+)",
    r"(?:if\s+i\s+liked?|i\s+(?:love|enjoy)(?:ed)?)\s+(.+?)(?:\s*,|\s+what|\s+recommend|\s+suggest|$)",
]


def _detect_reference_titles(query):
    """
    Detect if the query is a 'similar to X' pattern and extract the reference title(s).
    Returns a list of lowercase title fragments to exclude from results.
    """
    q = query.strip()
    for pattern in _SIMILAR_PATTERNS:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            raw = match.group(1).strip().rstrip(".,!?")
            titles = re.split(r"\s+and\s+|\s+or\s+|,\s*", raw, flags=re.IGNORECASE)
            return [t.strip().lower() for t in titles if t.strip()]
    return []


def _build_semantic_query_from_reference(reference_titles):
    """
    Look up the reference movie(s) in the database and build a semantic search
    query from their genres and overview — so we search by THEME not by title.
    
    For "movies like Harry Potter" this turns the search into something like:
    "fantasy adventure magic young wizard school" instead of "harry potter"
    """
    semantic_parts = []
    
    for title_fragment in reference_titles:
        results = search_movies_by_title(title_fragment, limit=1)
        if results:
            movie = results[0]
            # Use genres + overview keywords as semantic search
            genres = movie.get("genres", "")
            if isinstance(genres, list):
                genres = ", ".join(genres)
            overview = movie.get("overview", "")
            
            if genres:
                semantic_parts.append(genres)
            if overview:
                # Take a meaningful portion of the overview for semantic embedding
                semantic_parts.append(overview[:300])
    
    if semantic_parts:
        return " ".join(semantic_parts)
    return None


def _is_excluded(movie_title, exclude_titles):
    """Check if a movie title matches any of the excluded reference titles."""
    title_lower = movie_title.lower()
    for exc in exclude_titles:
        if exc in title_lower or title_lower in exc:
            return True
    return False


def search_movies(query, user_id=None, n_results=10, genre_filter=None,
                  min_rating=0.0, api_key=None):
    """
    Full RAG pipeline: Parse + Retrieve (parallel) → Exclude → Filter → Generate → Log.
    
    For "similar to X" queries, looks up movie X in the database and uses its
    genres/overview as the vector search query (search by THEME, not by title).
    """
    # Step 0: Detect "similar to" queries
    exclude_titles = _detect_reference_titles(query)
    
    # If this is a "like X" query, build a semantic search from the reference movie
    search_query = query
    if exclude_titles:
        semantic_query = _build_semantic_query_from_reference(exclude_titles)
        if semantic_query:
            search_query = semantic_query
            print(f"[PIPELINE] 'Like' query detected -> searching by theme: {search_query[:80]}...")
    
    # Step 1: Run parse_query and vector search IN PARALLEL
    parsed = None
    raw_results = None

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_parse = executor.submit(parse_query, query, api_key=api_key)
        future_retrieve = executor.submit(
            retrieve_similar_movies,
            query=search_query,  # Uses semantic query for "like X" searches
            n_results=n_results * 3,
            genre_filter=None,
            min_rating=min_rating,
        )

        parsed = future_parse.result()
        raw_results = future_retrieve.result()

    # Step 2: Exclude reference movies (remove Harry Potter from "movies like Harry Potter")
    if exclude_titles:
        excluded = [m for m in raw_results if not _is_excluded(m.get("title", ""), exclude_titles)]
        if len(excluded) >= 3:
            raw_results = excluded

    # Step 3: Apply parsed filters
    active_genre = genre_filter if genre_filter else parsed.get("genre")
    active_min_rating = max(min_rating, parsed.get("min_rating", 0.0))
    min_year = parsed.get("min_year")
    max_year = parsed.get("max_year")

    filtered_results = raw_results
    
    if min_year or max_year:
        year_filtered = []
        for m in filtered_results:
            release = str(m.get("release_date", ""))[:4]
            if not release or not release.isdigit():
                continue
            year = int(release)
            if min_year and year < min_year:
                continue
            if max_year and year > max_year:
                continue
            year_filtered.append(m)
        if year_filtered:
            filtered_results = year_filtered
    
    if active_genre:
        genre_lower = active_genre.lower()
        genre_filtered = [
            m for m in filtered_results
            if any(genre_lower in g.lower() for g in m.get("genres", []))
        ]
        if genre_filtered:
            filtered_results = genre_filtered
    
    if active_min_rating > 0:
        rating_filtered = [
            m for m in filtered_results
            if (m.get("vote_average") or 0) >= active_min_rating
        ]
        if rating_filtered:
            filtered_results = rating_filtered
    
    retrieved_movies = filtered_results[:n_results]

    if not retrieved_movies:
        return {
            "recommendation": "😔 No movies found matching your query. Try a different search or adjust filters.",
            "retrieved_movies": [],
            "success": False,
            "error": "No results from vector search.",
            "is_fallback": True
        }

    # Step 4: Build context
    context = build_context_string(retrieved_movies)

    # Step 5: Generate LLM recommendations
    exclusion_note = ""
    if exclude_titles:
        titles_str = ", ".join(exclude_titles)
        exclusion_note = f"\n⚠️ IMPORTANT: The user wants movies SIMILAR TO '{titles_str}' — do NOT recommend '{titles_str}' itself or any sequels/prequels from that franchise. Only recommend DIFFERENT movies.\n"

    result = generate_recommendations(
        query=query,
        context=context,
        api_key=api_key,
        exclusion_note=exclusion_note
    )

    # Step 6: Log the interaction
    if user_id:
        movie_ids = [m.get("movie_id") for m in retrieved_movies if m.get("movie_id")]
        try:
            log_interaction(user_id, query, movie_ids[:10])
        except Exception as e:
            print(f"[WARN] Failed to log interaction: {e}")

    return {
        "recommendation": result["response"],
        "retrieved_movies": retrieved_movies,
        "success": result["success"],
        "error": result.get("error"),
        "is_fallback": result.get("is_fallback", False)
    }
