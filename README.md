# 🎬 CineDiscover — AI-Powered Movie Discovery System

An intelligent movie recommendation system built using **Retrieval-Augmented Generation (RAG)**. Unlike traditional recommendation engines that rely only on ratings or popularity, CineDiscover uses natural language understanding to find movies that truly match your preferences.

## ✨ Features

- **🔍 Natural Language Search** — Describe the movie you want in plain English
- **🤖 AI Recommendations** — Google Gemini generates personalized explanations
- **📊 EDA Dashboard** — 8 interactive visualizations exploring movie trends
- **👤 User Profiles** — Track search history and save preferences
- **🎯 Smart Filtering** — Filter by genre, rating, and more

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Google Gemini Flash |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB |
| Database | SQLite |
| Visualization | Plotly |
| Dataset | TMDB 5000 Movies (Kaggle) |

## 🏗️ Architecture

```
User Query → Embedding → ChromaDB Similarity Search → Top-K Results
                                                          ↓
                                           Google Gemini (LLM) + Context
                                                          ↓
                                              AI Recommendations
```

## 📁 Project Structure

```
college_project/
├── app.py                          # Main Streamlit entry point
├── requirements.txt                # Dependencies
├── tmdb_5000_movies.csv            # Dataset
├── database/
│   ├── db_setup.py                 # Schema creation & data loading
│   └── db_operations.py            # CRUD operations
├── embeddings/
│   └── vectorstore.py              # ChromaDB + sentence-transformers
├── rag/
│   ├── retriever.py                # Similarity search
│   ├── generator.py                # Gemini LLM integration
│   └── pipeline.py                 # End-to-end RAG orchestration
├── eda/
│   └── visualizations.py           # Plotly charts
├── pages/
│   ├── 1_🔍_Discover.py           # RAG search page
│   ├── 2_📊_Analytics.py          # EDA dashboard
│   └── 3_👤_Profile.py            # User profile
└── utils/
    └── helpers.py                  # Shared configuration
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

### 4. Dataset
Place the `tmdb_5000_movies.csv` file in the project root.
Download from [Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata).

### 5. Run the App
```bash
streamlit run app.py
```

### 6. First-Time Setup
1. The database will initialize automatically on first run
2. Click **"Build Vector Store"** in the sidebar (takes 2-3 minutes)
3. Enter your Gemini API key in the sidebar
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
