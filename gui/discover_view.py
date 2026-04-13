import threading
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor

from utils.image_manager import ImageManager
from utils.theme_engine import get_accent
from rag.pipeline import search_movies
from database.db_operations import get_top_rated_movies, get_all_genres, get_movies_by_genre


class _SearchSignal(QObject):
    """Thread-safe signal to post RAG results back to the main thread."""
    result_ready = pyqtSignal(dict)


class DiscoverView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._search_signal = _SearchSignal()
        self._search_signal.result_ready.connect(self._render_results)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_header(main_layout)

        # Main scrollable area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 40)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)

        self._loaded = False

    def refresh_on_load(self):
        if not self._loaded:
            self._load_default_trending()
            self._loaded = True

    def _build_header(self, parent_layout):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #18181B; border-bottom: 1px solid #27272A;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 10, 30, 10)

        title = QLabel("Discover")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white; border: none;")
        h_layout.addWidget(title)
        h_layout.addSpacing(20)

        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Ask the AI for a film... e.g., 'old sci-fi classics'")
        self.search_entry.setFixedHeight(40)
        self.search_entry.returnPressed.connect(self.perform_search)
        h_layout.addWidget(self.search_entry, stretch=1)
        h_layout.addSpacing(10)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["All genres"] + get_all_genres())
        self.genre_combo.setFixedHeight(40)
        self.genre_combo.setFixedWidth(150)
        self.genre_combo.currentTextChanged.connect(self._on_genre_changed)
        h_layout.addWidget(self.genre_combo)
        h_layout.addSpacing(10)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setFixedHeight(40)
        self.clear_btn.setFixedWidth(70)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #F87171; font-weight: bold;
                border-radius: 8px; border: 1px solid #F87171;
            }
            QPushButton:hover { background-color: rgba(248, 113, 113, 0.1); }
        """)
        self.clear_btn.clicked.connect(self._clear_search)
        self.clear_btn.hide()
        h_layout.addWidget(self.clear_btn)
        h_layout.addSpacing(10)

        self.search_btn = QPushButton("Search")
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setFixedHeight(40)
        self.search_btn.setFixedWidth(100)
        accent = get_accent()
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent}; color: white; font-weight: bold;
                border-radius: 8px; border: none;
            }}
            QPushButton:hover {{ background-color: #0070E0; }}
            QPushButton:disabled {{ background-color: #3F3F46; color: #71717A; }}
        """)
        self.search_btn.clicked.connect(self.perform_search)
        h_layout.addWidget(self.search_btn)

        parent_layout.addWidget(header)

    def _clear_search(self):
        self.search_entry.clear()
        self.clear_btn.hide()
        self._load_default_trending()

    # ============= Default Trending Content =============

    def _clear_content(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _on_genre_changed(self, genre_text):
        """When genre dropdown changes, reload trending with filtered data."""
        self._clear_search() # Also resets search UI state
        self._load_default_trending(genre_text)

    def _load_default_trending(self, genre_filter=None):
        self._clear_content()

        if genre_filter and genre_filter != "All genres":
            movies = get_movies_by_genre(genre_filter, limit=15)
            section_title = f"Top {genre_filter} Films 🎬"
        else:
            movies = get_top_rated_movies(limit=15)
            section_title = "Trending Now 🔥"

        if not movies:
            lbl = QLabel("No movies found for this genre.")
            lbl.setStyleSheet("color: #71717A; font-size: 16px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            return

        # Hero Banner
        hero = random.choice(movies[:5])
        self._build_hero_banner(hero)

        # Carousels
        self._build_horizontal_carousel(section_title, movies[:8])

        # Second row with different sorting
        classics = sorted(movies, key=lambda x: str(x.get("release_date", "9999")))
        self._build_horizontal_carousel("Timeless Classics 🎬", classics[:8])

    def _build_hero_banner(self, movie):
        banner = QFrame()
        banner.setFixedHeight(350)
        banner.setStyleSheet("background-color: #0E0E10;")

        layout = QVBoxLayout(banner)
        layout.setContentsMargins(0, 0, 0, 0)

        self.hero_bg = QLabel(banner)
        self.hero_bg.setFixedHeight(350)
        self.hero_bg.setStyleSheet("background-color: #111;")
        # Remove setScaledContents as we are generating an exact 1000x350 fit image in ImageManager
        layout.addWidget(self.hero_bg)
        
        # Async fetch high res poster with cinematic blur background composition
        poster_path = movie.get("poster_path", "")
        if poster_path and str(poster_path) != "nan":
            url = f"https://image.tmdb.org/t/p/w1280{poster_path}"
            ImageManager.load_image_async(url, self.hero_bg, is_banner=True, target_width=1000, target_height=350)

        # Overlay Text
        overlay = QWidget(self.hero_bg)
        self.hero_bg.setFixedSize(1000, 350) # Ensure size is known for absolute positioning or absolute sizing
        o_layout = QVBoxLayout(overlay)
        o_layout.setContentsMargins(40, 40, 40, 40)
        o_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        overlay.setFixedSize(800, 350) # Limit text width
        
        title_text = movie.get('title', 'Unknown')
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", min(36, max(24, 600//max(1, len(title_text)))), QFont.Weight.Bold))
        title.setStyleSheet("color: white; background-color: transparent;")
        
        desc = QLabel(movie.get('overview', ''))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #E0E0E0; font-size: 16px; background-color: transparent;")
        
        o_layout.addWidget(title)
        o_layout.addWidget(desc)

        self.content_layout.addWidget(banner)

    def _build_horizontal_carousel(self, title_text, movies):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 20, 0, 10)

        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        layout.addSpacing(10)

        h_scroll = QScrollArea()
        h_scroll.setWidgetResizable(True)
        h_scroll.setFixedHeight(310)
        h_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        h_scroll.setFrameShape(QFrame.Shape.NoFrame)

        card_container = QWidget()
        c_layout = QHBoxLayout(card_container)
        c_layout.setContentsMargins(0, 5, 20, 5)
        c_layout.setSpacing(20)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for movie in movies:
            card = self._create_movie_card(movie)
            c_layout.addWidget(card)

        h_scroll.setWidget(card_container)
        layout.addWidget(h_scroll)
        self.content_layout.addWidget(container)

    def _create_movie_card(self, movie):
        card = QFrame()
        card.setFixedSize(160, 280)
        card.setStyleSheet("""
            QFrame { background-color: #18181B; border-radius: 12px; }
            QFrame:hover { background-color: #27272A; }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        poster_lbl = QLabel()
        poster_lbl.setFixedSize(140, 200)
        poster_lbl.setStyleSheet("background-color: #27272A; border-radius: 8px;")
        poster_lbl.setScaledContents(True)
        layout.addWidget(poster_lbl)

        p_path = movie.get("poster_path", "")
        if p_path and str(p_path) != "nan":
            url = f"https://image.tmdb.org/t/p/w200{p_path}"
            ImageManager.load_image_async(url, poster_lbl, radius=8, target_width=140, target_height=200)

        title_text = movie.get("title", "")
        if len(title_text) > 18:
            title_text = title_text[:16] + "…"
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        
        rating_val = movie.get('vote_average', 0)
        if isinstance(rating_val, str):
             try: rating_val = float(rating_val)
             except: rating_val = 0.0
        rating = QLabel(f"⭐ {rating_val:.1f}")
        rating.setStyleSheet("color: #F59E0B; font-size: 11px;")
        layout.addWidget(rating)

        return card

    # ============= RAG AI Search =============

    def perform_search(self):
        query = self.search_entry.text().strip()
        if not query:
            self._clear_search()
            return
            
        self.clear_btn.show()

        genre_val = None if self.genre_combo.currentText() == "All genres" else self.genre_combo.currentText()

        self._clear_content()
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Thinking…")

        loading = QLabel("✨ AI is analyzing your request…")
        loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading.setStyleSheet("color: #71717A; font-size: 16px; padding: 60px;")
        self.content_layout.addWidget(loading)

        threading.Thread(target=self._run_rag, args=(query, genre_val), daemon=True).start()

    def _run_rag(self, query, genre):
        try:
            result = search_movies(query=query, n_results=8, genre_filter=genre)
            self._search_signal.result_ready.emit(result)
        except Exception as e:
             self._search_signal.result_ready.emit({"error": str(e), "recommendation": "Search failed.", "retrieved_movies": []})

    def _render_results(self, result):
        self._clear_content()
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")

        accent = get_accent()

        # AI Recommendation Block
        ai_frame = QFrame()
        ai_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #18181B;
                border-radius: 12px;
                border: 1px solid #27272A;
            }}
        """)
        ai_layout = QVBoxLayout(ai_frame)
        ai_layout.setContentsMargins(25, 25, 25, 25)

        ai_title = QLabel("✨ AI Match Selection")
        ai_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        ai_title.setStyleSheet(f"color: {accent}; border: none;")
        ai_layout.addWidget(ai_title)

        rec_text = result.get("recommendation", "No recommendation available.")
        rec = QLabel(rec_text)
        rec.setWordWrap(True)
        rec.setStyleSheet("color: #D4D4D8; font-size: 14px; line-height: 1.6; border: none;")
        ai_layout.addWidget(rec)

        wrapper = QWidget()
        w_layout = QVBoxLayout(wrapper)
        w_layout.setContentsMargins(30, 20, 30, 0)
        w_layout.addWidget(ai_frame)
        self.content_layout.addWidget(wrapper)

        # Movie Results Carousel
        movies = result.get("retrieved_movies", [])
        if movies:
            self._build_horizontal_carousel("Search Results", movies)
