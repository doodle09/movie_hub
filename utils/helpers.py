"""
Shared utility functions and configuration for the Movie Discovery System.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Path Configuration ---
# When packaged with PyInstaller, sys._MEIPASS points to the temp bundle dir.
# We use the directory containing the executable as PROJECT_ROOT so that
# writable / user-editable data (DB, configs) lives next to the .exe.
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    PROJECT_ROOT = Path(sys.executable).parent
else:
    # Running in a normal Python environment
    PROJECT_ROOT = Path(__file__).parent.parent

DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = PROJECT_ROOT / "movie_discovery.db"
CHROMA_DIR = PROJECT_ROOT / "embeddings" / "chroma_db"
CSV_PATH = PROJECT_ROOT / "TMDB_movie_dataset_v11.csv"

# --- API Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# --- Model Configuration ---
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME = "movies"
LLM_MODEL_NAME = "gemini-2.0-flash"

# --- RAG Configuration ---
TOP_K_RESULTS = 10
MIN_OVERVIEW_LENGTH = 20  # Minimum characters for a valid overview


def get_google_api_key():
    """Get and validate the Google API key."""
    key = GOOGLE_API_KEY
    if not key or key == "your_gemini_api_key_here":
        return None
    return key
