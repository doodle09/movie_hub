"""
Database setup: creates SQLite tables and loads TMDB data from CSV.
Implements the ER diagram schema with 5 entities:
Users, Movies, Genres, Movie_Genre, User_Interactions.
"""
import sqlite3
import ast
import pandas as pd
from utils.helpers import DB_PATH, CSV_PATH


def get_connection():
    """Get a SQLite database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create all database tables matching the ER diagram."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) NOT NULL UNIQUE,
            preferences TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Movies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Movies (
            movie_id INTEGER PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            overview TEXT,
            release_date DATE,
            vote_average FLOAT DEFAULT 0.0,
            vote_count INTEGER DEFAULT 0,
            popularity FLOAT DEFAULT 0.0,
            runtime INTEGER,
            tagline TEXT DEFAULT '',
            budget INTEGER DEFAULT 0,
            revenue INTEGER DEFAULT 0,
            poster_path TEXT DEFAULT ''
        )
    """)

    # 3. Genres table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Genres (
            genre_id INTEGER PRIMARY KEY,
            genre_name VARCHAR(100) NOT NULL UNIQUE
        )
    """)

    # 4. Movie_Genre junction table (M:N)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Movie_Genre (
            movie_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (movie_id, genre_id),
            FOREIGN KEY (movie_id) REFERENCES Movies(movie_id),
            FOREIGN KEY (genre_id) REFERENCES Genres(genre_id)
        )
    """)

    # 5. User_Interactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User_Interactions (
            interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query_text TEXT,
            result_movie_ids TEXT DEFAULT '',
            interaction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[OK] All tables created successfully.")


def parse_genres(genres_str):
    """Parse comma-separated genres string from new TMDB CSV."""
    if not isinstance(genres_str, str) or not genres_str.strip():
        return []
    return [g.strip() for g in genres_str.split(',') if g.strip()]


def load_data_from_csv():
    """Load TMDB movie data from CSV into SQLite database."""
    if not CSV_PATH.exists():
        print(f"[ERROR] CSV file not found at {CSV_PATH}")
        print("   Please download the TMDB 5000 Movies dataset from Kaggle")
        print("   and place tmdb_5000_movies.csv in the project root.")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    # Check if data already loaded
    cursor.execute("SELECT COUNT(*) FROM Movies")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"[INFO] Database already contains {count} movies. Skipping load.")
        conn.close()
        return True

    print("[LOAD] Loading TMDB data from CSV...")
    # Load with dtype handling for massive files and filter down to popular/notable movies 
    # to prevent 1-million vector creation which would take days.
    df = pd.read_csv(str(CSV_PATH), low_memory=False)
    
    initial_len = len(df)
    df = df[df["vote_count"] >= 500] 
    print(f"[INFO] Filtered {initial_len} movies down to {len(df)} heavily-rated movies for ingestion.")

    genre_map = {} # Maps genre name to a generated ID
    next_genre_id = 1
    movie_count = 0

    for _, row in df.iterrows():
        movie_id = int(row["id"])
        title = str(row["title"]) if pd.notna(row["title"]) else ""
        overview = str(row["overview"]) if pd.notna(row["overview"]) else ""
        release_date = str(row["release_date"]) if pd.notna(row["release_date"]) else None
        vote_average = float(row["vote_average"]) if pd.notna(row["vote_average"]) else 0.0
        vote_count = int(row["vote_count"]) if pd.notna(row["vote_count"]) else 0
        popularity = float(row["popularity"]) if pd.notna(row["popularity"]) else 0.0
        runtime = int(row["runtime"]) if pd.notna(row["runtime"]) else 0
        tagline = str(row["tagline"]) if pd.notna(row["tagline"]) else ""
        budget = int(row["budget"]) if pd.notna(row["budget"]) else 0
        revenue = int(row["revenue"]) if pd.notna(row["revenue"]) else 0
        poster_path = str(row["poster_path"]) if pd.notna(row["poster_path"]) else ""

        # Insert movie
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO Movies
                (movie_id, title, overview, release_date, vote_average,
                 vote_count, popularity, runtime, tagline, budget, revenue, poster_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (movie_id, title, overview, release_date, vote_average,
                  vote_count, popularity, runtime, tagline, budget, revenue, poster_path))
            movie_count += 1
        except Exception as e:
            print(f"  [WARN] Error inserting movie {title}: {e}")
            continue

        # Parse and insert genres
        genre_names = parse_genres(row["genres"]) if pd.notna(row["genres"]) else []
        for genre_name in genre_names:
            if genre_name not in genre_map:
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO Genres (genre_id, genre_name) VALUES (?, ?)",
                        (next_genre_id, genre_name)
                    )
                    genre_map[genre_name] = next_genre_id
                    next_genre_id += 1
                except sqlite3.Error:
                    pass

            genre_id = genre_map.get(genre_name)
            if genre_id:
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO Movie_Genre (movie_id, genre_id) VALUES (?, ?)",
                        (movie_id, genre_id)
                    )
                except sqlite3.Error:
                    pass

    # Create a default demo user
    cursor.execute(
        "INSERT OR IGNORE INTO Users (username, preferences) VALUES (?, ?)",
        ("demo_user", "Action, Sci-Fi, Drama")
    )

    conn.commit()
    conn.close()
    print(f"[OK] Loaded {movie_count} movies and {len(genre_map)} genres into the database.")
    return True


def initialize_database():
    """Full database initialization: create tables and load data."""
    create_tables()
    return load_data_from_csv()


if __name__ == "__main__":
    initialize_database()
