"""
Generator module: Google Gemini LLM integration for generating
movie recommendations from retrieved context.
"""
import google.generativeai as genai
from utils.config_manager import ConfigManager
from utils.helpers import get_google_api_key, LLM_MODEL_NAME

# System prompt template
SYSTEM_PROMPT = """You are CineBot, an expert movie recommender and film critic. 
You have deep knowledge of cinema across all genres, eras, and cultures.

Your task is to recommend movies based on the user's query and the movie database 
results provided below. Follow these rules:

1. Recommend the BEST matching movies from the provided database results.
2. For each recommendation, explain WHY it matches the user's request.
3. Mention the movie's rating, year, and genres.
4. Keep explanations concise but insightful — 2-3 sentences each.
5. If the query asks to AVOID certain themes, respect that and explain why excluded movies don't fit.
6. Rank recommendations by relevance to the query, not just by rating.
7. Format your response with clear numbering and movie titles in bold.
8. If none of the retrieved movies match well, say so honestly.
9. CRITICAL: If the user asks for movies "like" or "similar to" a specific movie/franchise,
   you must NEVER recommend that exact movie or sequels/prequels from the same franchise.
   Instead, recommend DIFFERENT movies that share similar themes, genres, or vibes.
   For example: "movies like Harry Potter" should suggest Narnia, Percy Jackson, etc. — NOT Harry Potter films.

Respond in a friendly, conversational tone like a knowledgeable film enthusiast."""

USER_PROMPT_TEMPLATE = """
USER QUERY: {query}
{exclusion_note}
RETRIEVED MOVIES FROM DATABASE:
{context}

Based on the user's query and the retrieved movies above, provide your top recommendations 
with explanations. Recommend up to 5 movies that best match the query.
"""



def generate_recommendations(query, context, api_key=None, exclusion_note=""):
    """
    Generate movie recommendations using Google Gemini with Key Rotation.
    """
    keys_pool = [api_key] if api_key else ConfigManager.get_gemini_pool()
    if not keys_pool and get_google_api_key(): # fallback to env
        keys_pool = [get_google_api_key()]
        
    if not keys_pool:
        return {
            "response": _generate_fallback_response(query, context),
            "success": True,
            "error": "No API Keys found.",
            "is_fallback": True
        }

    user_prompt = USER_PROMPT_TEMPLATE.format(query=query, context=context, exclusion_note=exclusion_note)
    last_error = ""

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
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1500,
                    top_p=0.9,
                )
            )

            if response and response.text:
                return {
                    "response": response.text,
                    "success": True,
                    "error": None,
                    "is_fallback": False
                }
        except Exception as e:
            error_msg = str(e)
            print(f"[WARN] Gemini key failed ({error_msg[:50]}), swapping next key...")
            last_error = error_msg
            continue

    # If we exhaust all keys
    print(f"[ERROR] All Gemini API keys exhausted. Last error: {last_error}")
    return {
        "response": _generate_fallback_response(query, context),
        "success": True,
        "error": f"LLM API exhausted: {last_error}. Showing directly.",
        "is_fallback": True
    }


def _generate_fallback_response(query, context):
    """
    Generate a simple recommendation response without an LLM.
    Used when the API key is missing or the API call fails.
    """
    lines = context.strip().split("\n\n")
    response_parts = [
        f"🎬 **Movie Recommendations for:** *\"{query}\"*\n",
        "*(Showing direct search results — configure your Gemini API key for AI-powered explanations)*\n"
    ]

    movie_num = 0
    current_movie = {}

    for line in context.strip().split("\n"):
        line = line.strip()
        if line.startswith("[Movie"):
            if current_movie:
                movie_num += 1
                title = current_movie.get("Title", "Unknown")
                rating = current_movie.get("Rating", "N/A")
                year = current_movie.get("Year", "N/A")
                genres = current_movie.get("Genres", "N/A")
                overview = current_movie.get("Overview", "")
                response_parts.append(
                    f"**{movie_num}. {title}** ({year}) — ⭐ {rating}\n"
                    f"   🏷️ {genres}\n"
                    f"   {overview[:150]}{'...' if len(overview) > 150 else ''}\n"
                )
            current_movie = {}
        elif ": " in line:
            key, value = line.split(": ", 1)
            current_movie[key] = value

    # Don't forget the last movie
    if current_movie:
        movie_num += 1
        title = current_movie.get("Title", "Unknown")
        rating = current_movie.get("Rating", "N/A")
        year = current_movie.get("Year", "N/A")
        genres = current_movie.get("Genres", "N/A")
        overview = current_movie.get("Overview", "")
        response_parts.append(
            f"**{movie_num}. {title}** ({year}) — ⭐ {rating}\n"
            f"   🏷️ {genres}\n"
            f"   {overview[:150]}{'...' if len(overview) > 150 else ''}\n"
        )

    return "\n".join(response_parts)
