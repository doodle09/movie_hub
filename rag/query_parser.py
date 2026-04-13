import json
import re
import google.generativeai as genai
from utils.config_manager import ConfigManager
from utils.helpers import get_google_api_key, LLM_MODEL_NAME

SYSTEM_PROMPT = """You are a movie query parser.
Your job is to read the user's natural language search query and extract structured filtering metadata for an SQLite database, while also refining the query for vector semantic search.

Rules for temporal extraction:
1. If the user mentions "90s", "1990s", etc. set max_year=1999 and min_year=1990.
2. If the user explicitly asks for "before 2000", set max_year=1999.
3. If the user mentions "recent" or "new", set min_year=2018.
4. If the user mentions subjective words like "old", "classic", or "vintage", DO NOT set year integers. Leave min_year and max_year as null. The vector search will handle subjective terms natively.

Return ONLY a valid JSON object with the following schema:
{
    "refined_query": "The core semantic search terms (e.g., 'artificial intelligence space travel' or 'old subjective terms here')",
    "min_year": integer or null,
    "max_year": integer or null,
    "genre": "Exact match to a known genre or null if none mentioned",
    "min_rating": float or null
}

Known genres: Action, Adventure, Animation, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Mystery, Romance, Science Fiction, TV Movie, Thriller, War, Western
"""

def parse_query(raw_query, api_key=None):
    """
    Pass the user query to Gemini to extract metadata filters and refine the search text.
    Uses JSON structured output parsing.
    """
    default_result = {
        "refined_query": raw_query,
        "min_year": None,
        "max_year": None,
        "genre": None,
        "min_rating": 0.0
    }
    
    keys_pool = [api_key] if api_key else ConfigManager.get_gemini_pool()
    if not keys_pool and get_google_api_key():
        keys_pool = [get_google_api_key()]
        
    if not keys_pool:
        return default_result

    for key in keys_pool:
        if not key.strip() or key.strip() == "your_gemini_api_key_here":
            continue
            
        genai.configure(api_key=key.strip())
        model = genai.GenerativeModel(
            model_name=LLM_MODEL_NAME,
            system_instruction=SYSTEM_PROMPT
        )

        try:
            response = model.generate_content(
                f"User Query: {raw_query}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                )
            )
            parsed = json.loads(response.text)
            return {
                "refined_query": parsed.get("refined_query", raw_query),
                "min_year": parsed.get("min_year"),
                "max_year": parsed.get("max_year"),
                "genre": parsed.get("genre"),
                "min_rating": parsed.get("min_rating", 0.0) or 0.0
            }
        except Exception as e:
            print(f"[WARN] Failed to parse query via LLM: {str(e)[:50]}")
            continue

    return default_result
