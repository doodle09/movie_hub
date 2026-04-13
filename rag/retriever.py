"""
Retriever module: handles similarity search against the vector store.
Acts as the 'R' in RAG — fetching relevant movie contexts for the LLM.
"""
from embeddings.vectorstore import query_vectorstore
from database.db_operations import get_movie_by_id


def retrieve_similar_movies(query, n_results=10, genre_filter=None, min_rating=0.0, min_year=None, max_year=None):
    """
    Retrieve movies from the vector store that are semantically similar to the query.
    Enriches results with full movie details from SQLite.
    
    Args:
        query: User's natural language search query.
        n_results: Number of results to retrieve.
        genre_filter: Optional genre to filter by.
        min_rating: Minimum rating threshold.
        min_year: Minimum release year.
        max_year: Maximum release year.
    
    Returns:
        List of enriched movie dicts with similarity scores.
    """
    # Get vector search results - fetch more if filtering by genre to ensure we have enough post-filter
    fetch_count = n_results * 5 if genre_filter else n_results
    vector_results = query_vectorstore(
        query_text=query,
        n_results=fetch_count,
        genre_filter=None, # Passed None as we removed it from vectorstore to avoid crashes
        min_rating=min_rating,
        min_year=min_year,
        max_year=max_year
    )

    if not vector_results:
        return []

    # Enrich with full movie details from SQLite
    enriched_results = []
    for result in vector_results:
        movie_id = result.get("movie_id")
        if movie_id:
            full_movie = get_movie_by_id(movie_id)
            if full_movie:
                full_movie["similarity_score"] = 1 - result.get("distance", 0)
                full_movie["search_document"] = result.get("document", "")
                enriched_results.append(full_movie)
            else:
                # Fallback to vector metadata if SQLite lookup fails
                result["similarity_score"] = 1 - result.get("distance", 0)
                result["genres"] = result.get("genres", "").split(", ") if result.get("genres") else []
                enriched_results.append(result)
                
    # Manual Python-side genre filtering
    if genre_filter:
        filtered_results = []
        for res in enriched_results:
            genres_list = res.get("genres", [])
            if isinstance(genres_list, str):
                genres_list = [g.strip() for g in genres_list.split(",")]
            
            # Simple case-insensitive string match to avoid exact list match issues
            genre_filter_lower = genre_filter.lower()
            if any(genre_filter_lower in g.lower() for g in genres_list):
                filtered_results.append(res)
        enriched_results = filtered_results

    return enriched_results[:n_results]


def build_context_string(movies, max_movies=7):
    """
    Build a context string from retrieved movies for the LLM prompt.
    
    Args:
        movies: List of movie dicts from retrieve_similar_movies.
        max_movies: Maximum number of movies to include in context.
    
    Returns:
        Formatted context string.
    """
    context_parts = []
    for i, movie in enumerate(movies[:max_movies], 1):
        genres = movie.get("genres", [])
        if isinstance(genres, list):
            genres_str = ", ".join(genres)
        else:
            genres_str = str(genres)

        title = movie.get("title", "Unknown")
        overview = movie.get("overview", "No description available.")
        rating = movie.get("vote_average", 0)
        year = str(movie.get("release_date", ""))[:4] if movie.get("release_date") else "N/A"
        score = movie.get("similarity_score", 0)

        context_parts.append(
            f"[Movie {i}]\n"
            f"Title: {title}\n"
            f"Year: {year}\n"
            f"Rating: {rating}/10\n"
            f"Genres: {genres_str}\n"
            f"Overview: {overview}\n"
            f"Relevance Score: {score:.2f}\n"
        )

    return "\n".join(context_parts)
