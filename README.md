# 🎬 CineDiscover — AI-Powered Movie Discovery System

An intelligent movie recommendation system built using **Retrieval-Augmented Generation (RAG)**. Unlike traditional recommendation engines that rely only on ratings or popularity, CineDiscover uses natural language understanding to find movies that truly match your preferences.

## ✨ Features

- **🔍 Natural Language Search** — Describe the movie you want in plain English
- **🤖 AI Recommendations** — Google Gemini generates personalized explanations
- **📊 EDA Dashboard** — Interactive visualizations exploring movie trends
- **🎯 Smart Filtering** — Filter by genre, rating, and more
- **🎨 Theming** — Customizable accent colors and dark UI

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Desktop GUI | PyQt6 |
| LLM | Google Gemini Flash |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB |
| Database | SQLite |
| Visualization | Matplotlib |
| Dataset | TMDB Movies (Kaggle) |

## 🏗️ Architecture

```
User Query → Query Parser (Gemini) → Structured Filters
                                          ↓
         Refined Query → Embedding → ChromaDB Similarity Search → Top-K Results
                                                                       ↓
                                                        Google Gemini (LLM) + Context
                                                                       ↓
                                                          AI Recommendations → PyQt6 UI
```

## 📁 Project Structure

```
college_project/
├── desktop_app.py                  # Main PyQt6 entry point
├── requirements.txt                # Dependencies
├── TMDB_movie_dataset_v11.csv      # Dataset
├── configs/
│   └── api_keys.json               # Gemini API key pool
├── database/
│   ├── db_setup.py                 # Schema creation & data loading
│   └── db_operations.py            # CRUD operations
├── embeddings/
│   └── vectorstore.py              # ChromaDB + sentence-transformers
├── rag/
│   ├── query_parser.py             # LLM-powered query extraction
│   ├── retriever.py                # Similarity search + enrichment
│   ├── generator.py                # Gemini LLM integration
│   └── pipeline.py                 # End-to-end RAG orchestration
├── eda/
│   └── visualizations.py           # Analytics charts
├── gui/
│   ├── main_window.py              # Main window with sidebar navigation
│   ├── discover_view.py            # RAG search page with hero banner
│   ├── analytics_view.py           # EDA dashboard
│   └── settings_view.py            # API key & theme configuration
└── utils/
    ├── helpers.py                  # Shared constants & configuration
    ├── config_manager.py           # API key pool management
    ├── image_manager.py            # Async poster loading & caching
    └── theme_engine.py             # App-wide stylesheet generation
```

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.11+
- pip

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a Gemini API Key (Free)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create an API key
4. Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_key_here
```
Or add keys via the **Settings** page inside the app.

### 4. Dataset
Place the `TMDB_movie_dataset_v11.csv` file in the project root.
Download from [Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata).

### 5. Run the App
```bash
python desktop_app.py
```

### 6. First-Time Setup
1. The database will initialize automatically on first run
2. The vector store builds automatically if not already present
3. Add your Gemini API key(s) via the **Settings** page
4. Start searching! 🎬

## 📊 ER Diagram

The database implements 5 entities:
- **Users** — User profiles with preferences
- **Movies** — 4,800+ movies from TMDB
- **Genres** — 20 unique genres
- **Movie_Genre** — Many-to-many junction table
- **User_Interactions** — Search history logging

## 🎯 Example Queries

- *"Recommend science-fiction movies set in space about exploration"*
- *"Feel-good comedies from the 2010s with high ratings"*
- *"Dark psychological thrillers like Fight Club"*
- *"Animated family movies with adventure and heart"*

## 📝 License

This project is for educational purposes (college project).
