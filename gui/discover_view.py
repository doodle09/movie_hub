import threading
import random
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QScrollArea, QFrame, QGraphicsDropShadowEffect,
    QDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor

from utils.image_manager import ImageManager
from utils.theme_engine import get_colors
from rag.pipeline import search_movies
from database.db_operations import (
    get_top_rated_movies, get_all_genres, get_movies_by_genre,
    search_movies_by_title
)


class _SearchSignal(QObject):
    """Thread-safe signal to post RAG results back to the main thread."""
    result_ready = pyqtSignal(dict)


# ============= Movie Detail Dialog =============

class MovieDetailDialog(QDialog):
    """CineVerse-inspired movie detail panel."""
    
    def __init__(self, movie, parent=None):
        super().__init__(parent)
        self.movie = movie
        self.setWindowTitle(movie.get("title", "Movie Details"))
        self.setFixedSize(920, 820)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        
        c = get_colors()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['bg_main']};
                border: 1px solid {c['border']};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- Hero backdrop section ---
        hero_frame = QFrame()
        hero_frame.setFixedHeight(380)
        hero_frame.setStyleSheet(f"background-color: {c['bg_main']}; border-radius: 16px 16px 0 0;")
        
        # Backdrop image
        hero_bg = QLabel(hero_frame)
        hero_bg.setFixedSize(920, 380)
        hero_bg.setStyleSheet(f"background-color: #0D0D14; border-radius: 16px;")
        
        p_path = movie.get("poster_path", "")
        if p_path and str(p_path) != "nan":
            url = f"https://image.tmdb.org/t/p/w1280{p_path}"
            ImageManager.load_image_async(url, hero_bg, is_banner=True, 
                                          target_width=920, target_height=380)
        
        # Close button
        close_x = QPushButton("✕", hero_frame)
        close_x.setFixedSize(38, 38)
        close_x.move(872, 12)
        close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        close_x.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0,0,0,0.7); color: white;
                border-radius: 19px; font-size: 14px; font-weight: bold; border: none;
            }}
            QPushButton:hover {{ background-color: {c['accent_red']}; }}
        """)
        close_x.clicked.connect(self.accept)
        
        # Title + meta overlay at bottom
        overlay = QWidget(hero_frame)
        overlay.setFixedSize(920, 200)
        overlay.move(0, 180)
        overlay.setStyleSheet("background-color: transparent;")
        
        ov_layout = QVBoxLayout(overlay)
        ov_layout.setContentsMargins(30, 0, 30, 16)
        ov_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        
        # Genre pills
        genres = movie.get("genres", [])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",") if g.strip()]
        if genres:
            gpill_row = QHBoxLayout()
            gpill_row.setSpacing(8)
            gpill_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for g in genres[:4]:
                pill = QLabel(g)
                pill.setStyleSheet(f"""
                    background-color: rgba(6, 182, 212, 0.15); color: {c['accent']};
                    padding: 4px 14px; border-radius: 12px; font-size: 11px;
                    font-weight: bold; border: 1px solid rgba(6, 182, 212, 0.3);
                """)
                pill.setFixedHeight(24)
                gpill_row.addWidget(pill)
            gpill_row.addStretch()
            ov_layout.addLayout(gpill_row)
            ov_layout.addSpacing(6)
        
        title_text = movie.get("title", "Unknown")
        font_size = min(30, max(20, 660 // max(1, len(title_text))))
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background-color: transparent;")
        title.setWordWrap(True)
        ov_layout.addWidget(title)
        
        # Meta row
        meta_widget = QWidget()
        meta_widget.setStyleSheet("background-color: transparent;")
        meta_row = QHBoxLayout(meta_widget)
        meta_row.setContentsMargins(0, 4, 0, 0)
        meta_row.setSpacing(16)
        meta_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        year = str(movie.get("release_date", ""))[:4] or "-"
        rating_val = movie.get("vote_average", 0)
        if isinstance(rating_val, str):
            try: rating_val = float(rating_val)
            except: rating_val = 0.0
        
        year_lbl = QLabel(year)
        year_lbl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px; background-color: transparent;")
        meta_row.addWidget(year_lbl)
        
        dot1 = QLabel("·")
        dot1.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 16px; background-color: transparent;")
        meta_row.addWidget(dot1)
        
        rating_lbl = QLabel(f"⭐ {rating_val:.1f}/10")
        rating_lbl.setStyleSheet("color: #FCD06F; font-size: 13px; font-weight: bold; background-color: transparent;")
        meta_row.addWidget(rating_lbl)
        
        runtime = movie.get("runtime", 0)
        if runtime:
            dot2 = QLabel("·")
            dot2.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 16px; background-color: transparent;")
            meta_row.addWidget(dot2)
            
            rt_lbl = QLabel(f"{runtime} min")
            rt_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 13px; background-color: transparent;")
            meta_row.addWidget(rt_lbl)
        
        ov_layout.addWidget(meta_widget)
        layout.addWidget(hero_frame)
        
        # --- Scrollable content below hero ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(30, 20, 30, 24)
        cl.setSpacing(16)
        
        # Tagline in accent color
        tagline = movie.get("tagline", "")
        if tagline and str(tagline) != "nan" and tagline.strip():
            tag_lbl = QLabel(f"\" {tagline} \"")
            tag_lbl.setWordWrap(True)
            tag_lbl.setStyleSheet(f"color: {c['accent']}; font-size: 15px; font-style: italic; font-weight: bold; padding: 0 0 4px 0;")
            cl.addWidget(tag_lbl)
        
        # Synopsis section
        synopsis_header = QLabel("SYNOPSIS")
        synopsis_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        synopsis_header.setStyleSheet(f"color: {c['text_muted']}; letter-spacing: 2px;")
        cl.addWidget(synopsis_header)
        
        overview_text = movie.get("overview", "No overview available.")
        if not overview_text or str(overview_text) == "nan":
            overview_text = "No overview available for this title."
        
        ov = QLabel(overview_text)
        ov.setWordWrap(True)
        ov.setStyleSheet(f"color: {c['text_secondary']}; font-size: 14px; line-height: 1.7;")
        cl.addWidget(ov)
        
        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {c['border']};")
        cl.addWidget(sep)
        
        # ---- Rating visual bar ----
        rating_section = QWidget()
        rating_section.setStyleSheet("background-color: transparent;")
        rs_layout = QVBoxLayout(rating_section)
        rs_layout.setContentsMargins(0, 4, 0, 4)
        rs_layout.setSpacing(8)
        
        rating_header_row = QHBoxLayout()
        rating_header_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        r_header = QLabel("AUDIENCE RATING")
        r_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        r_header.setStyleSheet(f"color: {c['text_muted']}; letter-spacing: 2px;")
        rating_header_row.addWidget(r_header)
        rating_header_row.addStretch()
        
        r_score = QLabel(f"{rating_val:.1f} / 10")
        r_score.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        r_score.setStyleSheet(f"color: #FCD06F;")
        rating_header_row.addWidget(r_score)
        rs_layout.addLayout(rating_header_row)
        
        # Progress bar for rating
        bar_bg = QFrame()
        bar_bg.setFixedHeight(8)
        bar_bg.setStyleSheet(f"background-color: {c['bg_hover']}; border-radius: 4px;")
        
        bar_fill = QFrame(bar_bg)
        fill_width = max(4, int(660 * (rating_val / 10.0)))
        bar_fill.setFixedSize(fill_width, 8)
        bar_fill.move(0, 0)
        # Color the bar based on rating
        if rating_val >= 7.5:
            bar_color = c['accent_green']
        elif rating_val >= 5.0:
            bar_color = c['accent_gold']
        else:
            bar_color = c['accent_red']
        bar_fill.setStyleSheet(f"background-color: {bar_color}; border-radius: 4px;")
        
        rs_layout.addWidget(bar_bg)
        
        vote_count = movie.get("vote_count", 0)
        if vote_count:
            vc_lbl = QLabel(f"Based on {vote_count:,} votes")
            vc_lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px;")
            rs_layout.addWidget(vc_lbl)
        
        cl.addWidget(rating_section)
        
        # Separator
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {c['border']};")
        cl.addWidget(sep2)
        
        # ---- Detail stats in cards ----
        details_header = QLabel("MOVIE DETAILS")
        details_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        details_header.setStyleSheet(f"color: {c['text_muted']}; letter-spacing: 2px;")
        cl.addWidget(details_header)
        
        details_container = QWidget()
        details_container.setStyleSheet("background-color: transparent;")
        det_layout = QHBoxLayout(details_container)
        det_layout.setContentsMargins(0, 4, 0, 4)
        det_layout.setSpacing(12)
        det_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        stat_items = []
        if movie.get("original_language"):
            stat_items.append(("LANGUAGE", movie['original_language'].upper()))
        stat_items.append(("YEAR", year))
        stat_items.append(("RATING", f"⭐ {rating_val:.1f}"))
        rev = movie.get("revenue", 0)
        if rev and rev > 0:
            stat_items.append(("REVENUE", f"${rev/1e6:.0f}M"))
        budget = movie.get("budget", 0)
        if budget and budget > 0:
            stat_items.append(("BUDGET", f"${budget/1e6:.0f}M"))
        
        popularity = movie.get("popularity", 0)
        if popularity and float(popularity) > 0:
            stat_items.append(("POPULARITY", f"{float(popularity):.0f}"))
            
        for key, val in stat_items:
            item_widget = QFrame()
            item_widget.setStyleSheet(f"""
                QFrame {{
                    background-color: {c['bg_hover']};
                    border-radius: 10px;
                    border: 1px solid {c['border']};
                    padding: 8px 14px;
                }}
            """)
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(10, 8, 10, 8)
            item_layout.setSpacing(3)
            
            k_lbl = QLabel(key)
            k_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            k_lbl.setStyleSheet(f"color: {c['text_muted']}; letter-spacing: 1px; border: none; background: transparent;")
            item_layout.addWidget(k_lbl)
            
            v_lbl = QLabel(val)
            v_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            v_lbl.setStyleSheet(f"color: {c['text_primary']}; border: none; background: transparent;")
            item_layout.addWidget(v_lbl)
            
            det_layout.addWidget(item_widget)
        
        cl.addWidget(details_container)
        
        # ---- Production companies ----
        prod_companies = movie.get("production_companies", "")
        if prod_companies and str(prod_companies) != "nan" and str(prod_companies).strip():
            sep3 = QFrame()
            sep3.setFixedHeight(1)
            sep3.setStyleSheet(f"background-color: {c['border']};")
            cl.addWidget(sep3)
            
            prod_header = QLabel("PRODUCTION")
            prod_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            prod_header.setStyleSheet(f"color: {c['text_muted']}; letter-spacing: 2px;")
            cl.addWidget(prod_header)
            
            prod_lbl = QLabel(str(prod_companies))
            prod_lbl.setWordWrap(True)
            prod_lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 13px;")
            cl.addWidget(prod_lbl)
        
        # ---- Release date (full) ----
        full_date = movie.get("release_date", "")
        if full_date and str(full_date) != "nan" and len(str(full_date)) > 4:
            sep4 = QFrame()
            sep4.setFixedHeight(1)
            sep4.setStyleSheet(f"background-color: {c['border']};")
            cl.addWidget(sep4)
            
            date_row = QHBoxLayout()
            date_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
            date_key = QLabel("RELEASE DATE")
            date_key.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            date_key.setStyleSheet(f"color: {c['text_muted']}; letter-spacing: 2px;")
            date_row.addWidget(date_key)
            date_row.addSpacing(20)
            date_val = QLabel(str(full_date))
            date_val.setFont(QFont("Segoe UI", 13))
            date_val.setStyleSheet(f"color: {c['text_primary']};")
            date_row.addWidget(date_val)
            date_row.addStretch()
            cl.addLayout(date_row)
        
        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_pos') and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)


# ============= Discover View =============

class DiscoverView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._search_signal = _SearchSignal()
        self._search_signal.result_ready.connect(self._render_ai_response)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_header(main_layout)

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
        self._ai_placeholder = None

    def refresh_on_load(self):
        if not self._loaded:
            self._load_default_trending()
            self._loaded = True

    def _build_header(self, parent_layout):
        c = get_colors()
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("DiscoverHeader")
        header.setStyleSheet(f"""
            QFrame#DiscoverHeader {{
                background-color: {c['bg_header']};
                border-bottom: 1px solid {c['border_subtle']};
            }}
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(28, 10, 28, 10)

        # Search bar
        search_icon = QLabel("🔍")
        search_icon.setFixedSize(38, 42)
        search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_icon.setStyleSheet(f"""
            background-color: {c['bg_input']}; 
            border: 1px solid {c['border']}; 
            border-right: none;
            border-radius: 10px 0 0 10px;
            font-size: 14px;
        """)
        h_layout.addWidget(search_icon)
        
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search films, directors, or ask AI...")
        self.search_entry.setFixedHeight(42)
        self.search_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg_input']};
                color: {c['text_primary']};
                padding: 10px 16px;
                border: 1px solid {c['border']};
                border-left: none;
                border-radius: 0 10px 10px 0;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {c['accent']};
                border-left: none;
            }}
        """)
        self.search_entry.returnPressed.connect(self.perform_search)
        h_layout.addWidget(self.search_entry, stretch=1)
        h_layout.addSpacing(10)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["All genres"] + get_all_genres())
        self.genre_combo.setFixedHeight(42)
        self.genre_combo.setFixedWidth(155)
        self.genre_combo.currentTextChanged.connect(self._on_genre_changed)
        h_layout.addWidget(self.genre_combo)
        h_layout.addSpacing(8)
        
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setFixedSize(42, 42)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {c['accent_red']}; font-weight: bold;
                border-radius: 10px; border: 1px solid {c['accent_red']}; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: rgba(239, 68, 68, 0.12); }}
        """)
        self.clear_btn.clicked.connect(self._clear_search)
        self.clear_btn.hide()
        h_layout.addWidget(self.clear_btn)
        h_layout.addSpacing(8)

        self.search_btn = QPushButton("Search")
        self.search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_btn.setFixedHeight(42)
        self.search_btn.setFixedWidth(100)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']}; color: white; font-weight: bold;
                border-radius: 10px; border: none; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #0891B2; }}
            QPushButton:disabled {{ background-color: {c['bg_hover']}; color: {c['text_muted']}; }}
        """)
        self.search_btn.clicked.connect(self.perform_search)
        h_layout.addWidget(self.search_btn)

        parent_layout.addWidget(header)

    def _clear_search(self):
        self.search_entry.clear()
        self.clear_btn.hide()
        self._load_default_trending()

    def _clear_content(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._ai_placeholder = None

    def _on_genre_changed(self, genre_text):
        self._clear_search()
        self._load_default_trending(genre_text)

    def _load_default_trending(self, genre_filter=None):
        self._clear_content()

        if genre_filter and genre_filter != "All genres":
            movies = get_movies_by_genre(genre_filter, limit=15)
            section_title = f"Top {genre_filter} Films"
        else:
            movies = get_top_rated_movies(limit=15)
            section_title = "Trending Movies"

        if not movies:
            c = get_colors()
            lbl = QLabel("No movies found for this genre.")
            lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 16px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(lbl)
            return

        hero = random.choice(movies[:5])
        self._build_hero_banner(hero)
        self._build_horizontal_carousel(section_title, movies[:8])

        classics = sorted(movies, key=lambda x: str(x.get("release_date", "9999")))
        self._build_horizontal_carousel("Timeless Classics", classics[:8])

    # ==================== HERO BANNER — CineVerse Style ====================
    def _build_hero_banner(self, movie):
        c = get_colors()
        banner = QFrame()
        banner.setFixedHeight(440)
        banner.setStyleSheet(f"background-color: {c['banner_bg']}; border: none;")

        layout = QVBoxLayout(banner)
        layout.setContentsMargins(0, 0, 0, 0)

        self.hero_bg = QLabel(banner)
        self.hero_bg.setFixedHeight(440)
        self.hero_bg.setStyleSheet(f"background-color: {c['banner_bg']}; border: none;")
        layout.addWidget(self.hero_bg)
        
        poster_path = movie.get("poster_path", "")
        if poster_path and str(poster_path) != "nan":
            url = f"https://image.tmdb.org/t/p/w1280{poster_path}"
            ImageManager.load_image_async(url, self.hero_bg, is_banner=True, target_width=1080, target_height=440)

        overlay = QWidget(self.hero_bg)
        self.hero_bg.setFixedSize(1080, 440)
        o_layout = QVBoxLayout(overlay)
        o_layout.setContentsMargins(48, 40, 48, 36)
        o_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        overlay.setFixedSize(550, 440)
        
        # Small poster thumbnail (CineVerse style — poster floats at top-left of hero)
        poster_thumb = QLabel()
        poster_thumb.setFixedSize(80, 110)
        poster_thumb.setStyleSheet(f"background-color: {c['bg_hover']}; border-radius: 8px; border: 2px solid rgba(255,255,255,0.1);")
        poster_thumb.setScaledContents(True)
        if poster_path and str(poster_path) != "nan":
            thumb_url = f"https://image.tmdb.org/t/p/w200{poster_path}"
            ImageManager.load_image_async(thumb_url, poster_thumb, radius=8, target_width=80, target_height=110)
        o_layout.addWidget(poster_thumb)
        o_layout.addSpacing(8)
        
        # "Trending Now" badge
        trending_badge = QLabel("  🔥 Trending Now  ")
        trending_badge.setFixedHeight(26)
        trending_badge.setStyleSheet(f"""
            background-color: rgba(6, 182, 212, 0.15);
            color: {c['accent']};
            border: 1px solid rgba(6, 182, 212, 0.35);
            border-radius: 13px;
            font-size: 11px;
            font-weight: bold;
            padding: 0 12px;
        """)
        trending_badge.setFixedWidth(140)
        o_layout.addWidget(trending_badge)
        o_layout.addSpacing(6)
        
        # Title — large bold
        title_text = movie.get('title', 'Unknown')
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", min(38, max(24, 550 // max(1, len(title_text)))), QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['overlay_text']}; background-color: transparent;")
        title.setWordWrap(True)
        o_layout.addWidget(title)
        o_layout.addSpacing(4)
        
        # Description
        overview = movie.get('overview', '')
        if len(overview) > 160:
            overview = overview[:160] + "..."
        desc = QLabel(overview)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {c['overlay_desc']}; font-size: 13px; background-color: transparent; line-height: 1.5;")
        o_layout.addWidget(desc)
        o_layout.addSpacing(4)
        
        # CineVerse accent tagline
        tagline_text = movie.get('tagline', '')
        if tagline_text and str(tagline_text) != 'nan' and tagline_text.strip():
            accent_line = QLabel(tagline_text)
        else:
            accent_line = QLabel("Unlimited Movies & Shows. Anytime, Anywhere.")
        accent_line.setStyleSheet(f"color: {c['accent']}; font-size: 13px; font-weight: bold; background-color: transparent;")
        o_layout.addWidget(accent_line)
        o_layout.addSpacing(10)
        
        # Action button — More Info only
        btn_row_widget = QWidget()
        btn_row_widget.setStyleSheet("background-color: transparent;")
        btn_row = QHBoxLayout(btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(12)
        btn_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        more_info_btn = QPushButton("ⓘ  More Info")
        more_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        more_info_btn.setFixedHeight(40)
        more_info_btn.setFixedWidth(150)
        more_info_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['accent']}; color: white; font-weight: bold;
                border-radius: 20px; border: none; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #0891B2; }}
        """)
        more_info_btn.clicked.connect(lambda: self._show_movie_detail(movie))
        btn_row.addWidget(more_info_btn)
        
        o_layout.addWidget(btn_row_widget)

        self.content_layout.addWidget(banner)

    # ==================== MOVIE CARD CAROUSEL ====================
    def _build_horizontal_carousel(self, title_text, movies):
        c = get_colors()
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 24, 0, 10)

        # Section title — cyan accent like CineVerse
        title_row = QHBoxLayout()
        title_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {c['accent']}; background-color: transparent;")
        title_row.addWidget(title)
        title_row.addStretch()
        
        # Navigation arrows
        nav_left = QLabel("‹")
        nav_left.setFixedSize(30, 30)
        nav_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_left.setStyleSheet(f"""
            color: {c['text_secondary']}; font-size: 22px; 
            background-color: {c['bg_hover']}; border-radius: 15px;
        """)
        nav_left.setCursor(Qt.CursorShape.PointingHandCursor)
        title_row.addWidget(nav_left)
        
        nav_right = QLabel("›")
        nav_right.setFixedSize(30, 30)
        nav_right.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_right.setStyleSheet(f"""
            color: {c['text_secondary']}; font-size: 22px; 
            background-color: {c['bg_hover']}; border-radius: 15px;
            margin-right: 28px;
        """)
        nav_right.setCursor(Qt.CursorShape.PointingHandCursor)
        title_row.addWidget(nav_right)
        
        layout.addLayout(title_row)
        layout.addSpacing(14)

        h_scroll = QScrollArea()
        h_scroll.setWidgetResizable(True)
        h_scroll.setFixedHeight(280)
        h_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        h_scroll.setFrameShape(QFrame.Shape.NoFrame)
        h_scroll.setStyleSheet("background-color: transparent;")

        card_container = QWidget()
        card_container.setStyleSheet("background-color: transparent;")
        c_layout = QHBoxLayout(card_container)
        c_layout.setContentsMargins(0, 5, 28, 5)
        c_layout.setSpacing(16)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for movie in movies:
            card = self._create_movie_card(movie)
            c_layout.addWidget(card)

        # Wire up scroll arrows
        nav_left.mousePressEvent = lambda e: h_scroll.horizontalScrollBar().setValue(
            h_scroll.horizontalScrollBar().value() - 300)
        nav_right.mousePressEvent = lambda e: h_scroll.horizontalScrollBar().setValue(
            h_scroll.horizontalScrollBar().value() + 300)

        h_scroll.setWidget(card_container)
        layout.addWidget(h_scroll)
        self.content_layout.addWidget(container)

    # ==================== MOVIE CARD — CineVerse Style ====================
    def _create_movie_card(self, movie):
        c = get_colors()
        
        # Card with visible border to distinguish from neighbors
        card = QFrame()
        card.setFixedSize(170, 260)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setObjectName("MovieCard")
        card.setStyleSheet(f"""
            QFrame#MovieCard {{
                background-color: {c['bg_card']};
                border-radius: 12px;
                border: 1px solid {c['border']};
            }}
            QFrame#MovieCard:hover {{
                border: 2px solid {c['accent']};
                background-color: {c['bg_elevated']};
            }}
        """)
        
        card.mousePressEvent = lambda event, m=movie: self._show_movie_detail(m)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Poster fills the card
        poster_lbl = QLabel()
        poster_lbl.setFixedSize(170, 260)
        poster_lbl.setStyleSheet(f"background-color: {c['bg_hover']}; border-radius: 12px;")
        poster_lbl.setScaledContents(True)
        layout.addWidget(poster_lbl)

        p_path = movie.get("poster_path", "")
        if p_path and str(p_path) != "nan":
            url = f"https://image.tmdb.org/t/p/w300{p_path}"
            ImageManager.load_image_async(url, poster_lbl, radius=12, target_width=170, target_height=260)

        # Title overlay at bottom of card — gradient fade
        title_overlay = QWidget(card)
        title_overlay.setFixedSize(170, 80)
        title_overlay.move(0, 180)
        title_overlay.setStyleSheet("""
            background-color: transparent;
        """)
        
        to_layout = QVBoxLayout(title_overlay)
        to_layout.setContentsMargins(10, 30, 10, 10)
        to_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        title_text = movie.get("title", "")
        if len(title_text) > 22:
            title_text = title_text[:20] + "..."
        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background-color: transparent;")
        title.setWordWrap(True)
        to_layout.addWidget(title)
        
        # Year sublabel
        year = str(movie.get('release_date', ''))[:4]
        if year:
            year_lbl = QLabel(year)
            year_lbl.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 10px; background-color: transparent;")
            to_layout.addWidget(year_lbl)

        # Rating badge — top right corner
        rating_val = movie.get('vote_average', 0)
        if isinstance(rating_val, str):
            try: rating_val = float(rating_val)
            except: rating_val = 0.0
        
        if rating_val > 0:
            rating_badge = QLabel(f"⭐{rating_val:.1f}", card)
            rating_badge.setFixedSize(56, 22)
            rating_badge.move(108, 8)
            rating_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rating_badge.setStyleSheet("""
                background-color: rgba(0,0,0,0.8); color: #FCD06F;
                border-radius: 11px; font-size: 10px; font-weight: bold;
            """)

        # HD badge — top left corner (for high-rated movies)
        if rating_val >= 7.5:
            hd_badge = QLabel("HD", card)
            hd_badge.setFixedSize(28, 18)
            hd_badge.move(8, 8)
            hd_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hd_badge.setStyleSheet(f"""
                background-color: {c['accent']}; color: white;
                border-radius: 4px; font-size: 9px; font-weight: bold;
            """)

        return card
    
    def _show_movie_detail(self, movie):
        dialog = MovieDetailDialog(movie, parent=self)
        dialog.exec()

    # ============= 2-Phase RAG AI Search =============

    def perform_search(self):
        query = self.search_entry.text().strip()
        if not query:
            self._clear_search()
            return
            
        self.clear_btn.show()
        genre_val = None if self.genre_combo.currentText() == "All genres" else self.genre_combo.currentText()

        self._clear_content()
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Thinking...")

        c = get_colors()

        # ---- PHASE 1: Instant DB results ----
        instant_movies = search_movies_by_title(query, limit=8)
        if instant_movies:
            self._build_horizontal_carousel("Quick Results", instant_movies)
        
        # ---- AI Loading indicator ----
        self._ai_placeholder = QFrame()
        self._ai_placeholder.setObjectName("AILoadingFrame")
        self._ai_placeholder.setStyleSheet(f"""
            QFrame#AILoadingFrame {{
                background-color: {c['bg_card']};
                border-radius: 14px;
                border: 1px solid {c['border']};
            }}
        """)
        ai_ph_layout = QVBoxLayout(self._ai_placeholder)
        ai_ph_layout.setContentsMargins(28, 24, 28, 24)
        
        ai_title = QLabel("✨  AI Analysis")
        ai_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        ai_title.setStyleSheet(f"color: {c['accent']}; border: none; background-color: transparent;")
        ai_ph_layout.addWidget(ai_title)
        
        loading = QLabel("Analyzing your request and personalizing recommendations...")
        loading.setStyleSheet(f"color: {c['text_muted']}; font-size: 13px; border: none; background-color: transparent;")
        ai_ph_layout.addWidget(loading)
        
        # Loading gradient bar
        loading_bar = QFrame()
        loading_bar.setFixedHeight(3)
        loading_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {c['accent']}, stop:0.5 {c['accent_purple']}, stop:1 transparent);
            border-radius: 2px;
        """)
        ai_ph_layout.addWidget(loading_bar)
        
        wrapper = QWidget()
        wrapper.setStyleSheet("background-color: transparent;")
        w_layout = QVBoxLayout(wrapper)
        w_layout.setContentsMargins(28, 20, 28, 0)
        w_layout.addWidget(self._ai_placeholder)
        self.content_layout.addWidget(wrapper)
        
        # ---- PHASE 2: Start async RAG pipeline ----
        threading.Thread(target=self._run_rag, args=(query, genre_val), daemon=True).start()

    def _run_rag(self, query, genre):
        try:
            result = search_movies(query=query, n_results=8, genre_filter=genre)
            self._search_signal.result_ready.emit(result)
        except Exception as e:
             self._search_signal.result_ready.emit({
                 "error": str(e), 
                 "recommendation": "Search failed. Please try again.", 
                 "retrieved_movies": []
             })

    def _render_ai_response(self, result):
        """Phase 2: Movie cards FIRST, then AI text analysis below."""
        self.search_btn.setEnabled(True)
        self.search_btn.setText("Search")

        c = get_colors()

        # Remove loading placeholder
        if self._ai_placeholder:
            parent = self._ai_placeholder.parentWidget()
            if parent:
                parent.deleteLater()
            self._ai_placeholder = None

        # ===== CARDS FIRST =====
        movies = result.get("retrieved_movies", [])
        if movies:
            self._build_horizontal_carousel("AI Recommended Movies", movies)

        # ===== THEN AI TEXT =====
        ai_frame = QFrame()
        ai_frame.setObjectName("AIResultFrame")
        ai_frame.setStyleSheet(f"""
            QFrame#AIResultFrame {{
                background-color: {c['bg_card']};
                border-radius: 14px;
                border: 1px solid {c['border']};
            }}
        """)
        ai_layout = QVBoxLayout(ai_frame)
        ai_layout.setContentsMargins(28, 22, 28, 22)
        ai_layout.setSpacing(10)

        ai_title = QLabel("✨  AI Match Selection")
        ai_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        ai_title.setStyleSheet(f"color: {c['accent']}; border: none; background-color: transparent;")
        ai_layout.addWidget(ai_title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {c['border']};")
        ai_layout.addWidget(sep)

        rec_text = result.get("recommendation", "No recommendation available.")
        rec = QLabel(rec_text)
        rec.setWordWrap(True)
        rec.setStyleSheet(f"color: {c['text_secondary']}; font-size: 14px; line-height: 1.7; border: none; background-color: transparent;")
        ai_layout.addWidget(rec)

        wrapper = QWidget()
        wrapper.setStyleSheet("background-color: transparent;")
        w_layout = QVBoxLayout(wrapper)
        w_layout.setContentsMargins(28, 20, 28, 0)
        w_layout.addWidget(ai_frame)
        self.content_layout.addWidget(wrapper)
