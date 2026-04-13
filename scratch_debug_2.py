import sys
from rag.pipeline import search_movies

print("Debugging search...")
try:
    res = search_movies("give me old sci-fi movies")
    print(res.keys())
    print("Success:", res["success"])
    print("Error:", res.get("error"))
    print("Movies:", len(res["retrieved_movies"]))
except Exception as e:
    import traceback
    traceback.print_exc()
