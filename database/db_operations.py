"""
CRUD operations for the Movie Discovery System database.
Provides functions for user management, movie queries, and interaction logging.
"""
import sqlite3
from database.db_setup import get_connection


# ==================== USER OPERATIONS ====================

def create_user(username, preferences=""):
    """Register a new user. Returns user_id or None if username exists."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO Users (username, preferences) VALUES (?, ?)",
            (username, preferences)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user(username):
    """Get user details by username."""
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM Users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_users():
    """Get list of all registered usernames."""
    conn = get_connection()
    users = conn.execute("SELECT username FROM Users ORDER BY username").fetchall()
    conn.close()
    return [u["username"] for u in users]


def update_preferences(username, preferences):
    """Update user preferences."""
    conn = get_connection()
    conn.execute(
        "UPDATE Users SET preferences = ? WHERE username = ?",
        (preferences, username)
    )
    conn.commit()
    conn.close()


# ==================== MOVIE OPERATIONS ====================



def get_movies_by_genre(genre_name, limit=50):
    """Get movies filtered by genre name."""
    conn = get_connection()
    movies = conn.execute("""
        SELECT m.* FROM Movies m
        JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        JOIN Genres g ON mg.genre_id = g.genre_id
        WHERE g.genre_name = ?
        ORDER BY m.vote_average DESC
        LIMIT ?
    """, (genre_name, limit)).fetchall()
    conn.close()
    return [dict(m) for m in movies]


def get_all_genres():
    """Get list of all genre names."""
    conn = get_connection()
    genres = conn.execute(
        "SELECT genre_name FROM Genres ORDER BY genre_name"
    ).fetchall()
    conn.close()
    return [g["genre_name"] for g in genres]


def get_top_rated_movies(limit=20):
    """Get top rated movies with minimum vote count threshold."""
    conn = get_connection()
    movies = conn.execute("""
        SELECT m.*, GROUP_CONCAT(g.genre_name, ', ') as genres
        FROM Movies m
        LEFT JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.genre_id
        WHERE m.vote_count >= 100
        GROUP BY m.movie_id
        ORDER BY m.vote_average DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(m) for m in movies]


def search_movies_by_title(query, limit=20):
    """Search movies by title (partial match)."""
    conn = get_connection()
    movies = conn.execute("""
        SELECT m.*, GROUP_CONCAT(g.genre_name, ', ') as genres
        FROM Movies m
        LEFT JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.genre_id
        WHERE m.title LIKE ?
        GROUP BY m.movie_id
        ORDER BY m.popularity DESC
        LIMIT ?
    """, (f"%{query}%", limit)).fetchall()
    conn.close()
    return [dict(m) for m in movies]
    
def get_movie_by_id(movie_id):
    """Get full details of a specific movie including genres."""
    conn = get_connection()
    movie = conn.execute("""
        SELECT m.*, GROUP_CONCAT(g.genre_name, ', ') as genres
        FROM Movies m
        LEFT JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.genre_id
        WHERE m.movie_id = ?
        GROUP BY m.movie_id
    """, (movie_id,)).fetchone()
    conn.close()
    if movie:
        return dict(movie)
    return None


def get_movies_by_ids(movie_ids):
    """Batch-fetch multiple movies by ID in a single query. Returns dict keyed by movie_id."""
    if not movie_ids:
        return {}
    conn = get_connection()
    placeholders = ",".join("?" for _ in movie_ids)
    rows = conn.execute(f"""
        SELECT m.*, GROUP_CONCAT(g.genre_name, ', ') as genres
        FROM Movies m
        LEFT JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.genre_id
        WHERE m.movie_id IN ({placeholders})
        GROUP BY m.movie_id
    """, list(movie_ids)).fetchall()
    conn.close()
    return {row["movie_id"]: dict(row) for row in rows}

def get_movie_stats():
    """Get aggregate statistics for the EDA dashboard."""
    conn = get_connection()
    stats = {}

    stats["total_movies"] = conn.execute("SELECT COUNT(*) FROM Movies").fetchone()[0]
    stats["avg_rating"] = conn.execute(
        "SELECT ROUND(AVG(vote_average), 2) FROM Movies WHERE vote_count >= 10"
    ).fetchone()[0]
    stats["total_genres"] = conn.execute("SELECT COUNT(*) FROM Genres").fetchone()[0]

    top_genre = conn.execute("""
        SELECT g.genre_name, COUNT(*) as cnt FROM Movie_Genre mg
        JOIN Genres g ON mg.genre_id = g.genre_id
        GROUP BY g.genre_name ORDER BY cnt DESC LIMIT 1
    """).fetchone()
    stats["top_genre"] = top_genre["genre_name"] if top_genre else "N/A"

    stats["total_users"] = conn.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
    stats["total_interactions"] = conn.execute(
        "SELECT COUNT(*) FROM User_Interactions"
    ).fetchone()[0]

    conn.close()
    return stats


# ==================== INTERACTION OPERATIONS ====================

def log_interaction(user_id, query_text, result_movie_ids=None):
    """Log a user search interaction."""
    conn = get_connection()
    movie_ids_str = ",".join(map(str, result_movie_ids)) if result_movie_ids else ""
    conn.execute(
        "INSERT INTO User_Interactions (user_id, query_text, result_movie_ids) VALUES (?, ?, ?)",
        (user_id, query_text, movie_ids_str)
    )
    conn.commit()
    conn.close()


def get_user_history(user_id, limit=50):
    """Get search history for a user."""
    conn = get_connection()
    history = conn.execute("""
        SELECT query_text, result_movie_ids, interaction_time
        FROM User_Interactions
        WHERE user_id = ?
        ORDER BY interaction_time DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(h) for h in history]


def get_user_interaction_count(user_id):
    """Get total number of searches by a user."""
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM User_Interactions WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count


def get_all_movies_dataframe():
    """Get all movies as a pandas DataFrame for EDA."""
    import pandas as pd
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT m.*, GROUP_CONCAT(g.genre_name, ', ') as genres
        FROM Movies m
        LEFT JOIN Movie_Genre mg ON m.movie_id = mg.movie_id
        LEFT JOIN Genres g ON mg.genre_id = g.genre_id
        GROUP BY m.movie_id
    """, conn)
    conn.close()
    return df
