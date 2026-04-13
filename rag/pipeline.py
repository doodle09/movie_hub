"""
End-to-end RAG pipeline orchestrator.
Combines retrieval and generation into a single search function.
"""
from rag.retriever import retrieve_similar_movies, build_context_string
from rag.generator import generate_recommendations
from rag.query_parser import parse_query
from database.db_operations import log_interaction, get_user


def search_movies(query, user_id=None, n_results=10, genre_filter=None,
                  min_rating=0.0, api_key=None):
    """
    Full RAG pipeline: Retrieve → Generate → Log.
    
    Args:
        query: User's natural language search query.
        user_id: Optional user ID for logging interactions.
        n_results: Number of movies to retrieve for context.
        genre_filter: Optional genre filter.
        min_rating: Minimum rating threshold.
        api_key: Optional Gemini API key override.
    
    Returns:
        Dict with:
            - 'recommendation': LLM-generated text
            - 'retrieved_movies': List of movie dicts
            - 'success': Boolean
            - 'error': Error message or None
            - 'is_fallback': Whether fallback was used
    """
    # Step 1: Parse natural language for metadata if filters aren't hardcoded
    parsed = parse_query(query, api_key=api_key)
    
    # GUI can override parsing, so we use provided filters if they exist
    active_genre = genre_filter if genre_filter else parsed.get("genre")
    active_min_rating = max(min_rating, parsed.get("min_rating", 0.0))
    min_year = parsed.get("min_year")
    max_year = parsed.get("max_year")
    
    refined_query = parsed.get("refined_query", query)

    # Step 2: Retrieve relevant movies from vector store using extracted fields
    retrieved_movies = retrieve_similar_movies(
        query=refined_query,
        n_results=n_results,
        genre_filter=active_genre,
        min_rating=active_min_rating,
        min_year=min_year,
        max_year=max_year
    )

    if not retrieved_movies:
        return {
            "recommendation": "😔 No movies found matching your query. Try a different search or adjust filters.",
            "retrieved_movies": [],
            "success": False,
            "error": "No results from vector search.",
            "is_fallback": True
        }

    # Step 2: Build context string from retrieved movies
    context = build_context_string(retrieved_movies)

    # Step 3: Generate LLM recommendations
    result = generate_recommendations(
        query=query,
        context=context,
        api_key=api_key
    )

    # Step 4: Log the interaction
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
