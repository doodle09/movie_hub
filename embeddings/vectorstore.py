"""
Vector store management using ChromaDB and sentence-transformers.
Generates embeddings for movie overviews and stores them for semantic search.
"""
import chromadb
from chromadb.utils import embedding_functions
from database.db_setup import get_connection
from utils.helpers import CHROMA_DIR, EMBEDDING_MODEL_NAME, CHROMA_COLLECTION_NAME, MIN_OVERVIEW_LENGTH


def get_embedding_function():
    """Get the sentence-transformer embedding function for ChromaDB."""
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )


def get_chroma_client():
    """Get a persistent ChromaDB client."""
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_or_create_collection():
    """Get or create the movies ChromaDB collection."""
    client = get_chroma_client()
    ef = get_embedding_function()
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def build_vectorstore(progress_callback=None):
    """
    Build the vector store from movie data in SQLite.
    Embeds movie overviews and stores them in ChromaDB with metadata.
    
    Args:
        progress_callback: Optional callable(current, total) for progress updates.
    """
    collection = get_or_create_collection()

    # Check if already built
    existing_count = collection.count()
    if existing_count > 0:
        print(f"[INFO] Vector store already contains {existing_count} embeddings. Skipping build.")
        return existing_count

    # Fetch all movies from SQLite
    conn = get_connection()
    cursor = conn.execute("""
        SELECT m.movie_id, m.title, m.overview, m.vote_average, m.release_date,
               GROUP_CONCAT(g.genre_name, ', ') as genres
        FROM Movies m
        LEFT JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.genre_id
        WHERE m.overview IS NOT NULL AND LENGTH(m.overview) > ?
        GROUP BY m.movie_id
    """, (MIN_OVERVIEW_LENGTH,))
    movies = cursor.fetchall()
    conn.close()

    if not movies:
        print("[ERROR] No movies found in database. Run database setup first.")
        return 0

    # Batch insert into ChromaDB
    batch_size = 100
    total = len(movies)
    processed = 0

    for i in range(0, total, batch_size):
        batch = movies[i:i + batch_size]

        ids = []
        documents = []
        metadatas = []

        for movie in batch:
            movie_id = str(movie["movie_id"])
            title = movie["title"] or ""
            overview = movie["overview"] or ""
            genres = movie["genres"] or ""
            vote_avg = movie["vote_average"] or 0.0
            release_date = movie["release_date"] or ""

            # Create rich document text for embedding
            doc_text = f"{title}. {overview}"
            if genres:
                doc_text += f" Genres: {genres}."

            ids.append(movie_id)
            documents.append(doc_text)
            metadatas.append({
                "movie_id": int(movie["movie_id"]),
                "title": title,
                "genres": genres,
                "vote_average": float(vote_avg),
                "release_date": release_date
            })

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        processed += len(batch)
        if progress_callback:
            progress_callback(processed, total)
        print(f"  [PROGRESS] Embedded {processed}/{total} movies...")

    final_count = collection.count()
    print(f"[OK] Vector store built with {final_count} embeddings.")
    return final_count


def query_vectorstore(query_text, n_results=10, genre_filter=None, min_rating=0.0, min_year=None, max_year=None):
    """
    Query the vector store for semantically similar movies.
    
    Args:
        query_text: Natural language search query.
        n_results: Number of results to return.
        genre_filter: Optional genre name to filter by.
        min_rating: Minimum vote_average threshold.
        min_year: Minimum release year.
        max_year: Maximum release year.
        
    Returns:
        List of dicts with movie metadata and similarity distances.
    """
    collection = get_or_create_collection()

    if collection.count() == 0:
        return []

    # Build where clause for metadata filtering
    where_clauses = []
    if min_rating > 0:
        where_clauses.append({"vote_average": {"$gte": min_rating}})
        
    # ChromaDB metadata filtering for years (we stored release_date as "YYYY-MM-DD")
    # For simplicity, we can do string comparison since ISO dates are lexicographical
    if min_year:
        where_clauses.append({"release_date": {"$gte": f"{min_year}-01-01"}})
    if max_year:
        where_clauses.append({"release_date": {"$lte": f"{max_year}-12-31"}})

    where = None
    if len(where_clauses) == 1:
        where = where_clauses[0]
    elif len(where_clauses) > 1:
        where = {"$and": where_clauses}

    # Query ChromaDB
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"[WARN] Vector search error: {e}")
        # Fallback: query without filters
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection.count()),
            include=["documents", "metadatas", "distances"]
        )

    # Format results
    formatted = []
    if results and results["ids"] and results["ids"][0]:
        for idx in range(len(results["ids"][0])):
            formatted.append({
                "movie_id": results["metadatas"][0][idx].get("movie_id"),
                "title": results["metadatas"][0][idx].get("title", ""),
                "genres": results["metadatas"][0][idx].get("genres", ""),
                "vote_average": results["metadatas"][0][idx].get("vote_average", 0),
                "release_date": results["metadatas"][0][idx].get("release_date", ""),
                "document": results["documents"][0][idx],
                "distance": results["distances"][0][idx]
            })

    return formatted


def get_vectorstore_count():
    """Get the number of documents in the vector store."""
    try:
        collection = get_or_create_collection()
        return collection.count()
    except Exception:
        return 0


if __name__ == "__main__":
    build_vectorstore()
