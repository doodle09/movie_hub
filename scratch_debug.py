import sys
from rag.pipeline import search_movies
from utils.helpers import get_google_api_key

print("Starting manual RAG test...")
api_key = get_google_api_key()
print(f"API Key present: {bool(api_key)}")

try:
    result = search_movies("Sci-fi from the 90s", n_results=3, api_key=api_key)
    print("Search Result Success:", result.get("success"))
    if not result.get("success"):
        print("Error:", result.get("error"))
    print("Found movies:", len(result.get("retrieved_movies", [])))
except Exception as e:
    print(f"CRASH: {e}")
