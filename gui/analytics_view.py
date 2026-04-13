import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QFrame
)
from PyQt6.QtGui import QFont

from utils.theme_engine import get_colors
from database.db_operations import get_all_movies_dataframe, get_all_genres


class AnalyticsView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.c = get_colors()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Header
        header = QHBoxLayout()
        title = QLabel("Platform Insights")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        header.addWidget(title)
        header.addStretch()

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["All Genres"] + get_all_genres())
        self.genre_combo.setFixedWidth(180)
        self.genre_combo.setFixedHeight(40)
        self.genre_combo.currentTextChanged.connect(self.refresh_charts)
        header.addWidget(self.genre_combo)

        main_layout.addLayout(header)
        main_layout.addSpacing(30)

        # Stats Row
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(20)
        main_layout.addLayout(self.stats_layout)

        main_layout.addSpacing(30)

        # Chart container
        self.canvas_container = QVBoxLayout()
        main_layout.addLayout(self.canvas_container, stretch=1)

        self.canvas_widget = None
        self.base_df = get_all_movies_dataframe()

    def refresh_on_load(self):
        self.refresh_charts()

    def refresh_charts(self, *args):
        c = self.c
        selected_genre = self.genre_combo.currentText()

        if selected_genre == "All Genres":
            df = self.base_df.copy()
        else:
            df = self.base_df[self.base_df["genres"].fillna("").str.contains(selected_genre)]

        # Clear stats
        while self.stats_layout.count():
            child = self.stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        metrics = [
            ("Total Films", f"{len(df):,}"),
            ("Average Rating", f"{df['vote_average'].mean():.1f}" if len(df) > 0 else "0.0"),
            ("Total Revenue", f"${df['revenue'].sum() / 1e9:.1f}B" if len(df) > 0 else "$0"),
        ]

        for label_text, val in metrics:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background-color: {c['bg_card']}; border-radius: 12px; }}")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(30, 25, 30, 25)

            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {c['text_secondary']}; font-size: 14px; font-weight: bold;")
            c_layout.addWidget(lbl)

            v_lbl = QLabel(val)
            v_lbl.setStyleSheet(f"color: {c['accent']}; font-size: 32px; font-weight: bold;")
            c_layout.addWidget(v_lbl)

            self.stats_layout.addWidget(card)

        if len(df) > 0:
            self.draw_charts(df)

    def draw_charts(self, df):
        if self.canvas_widget:
            self.canvas_widget.deleteLater()
            self.canvas_widget = None

        c = self.c
        bg = c["chart_bg"]
        fg = c["chart_text"]
        grid = c["chart_grid"]
        accent = c["chart_accent"]
        secondary = c["chart_secondary"]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), facecolor=bg)

        for ax in [ax1, ax2]:
            ax.set_facecolor(bg)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color(grid)
            ax.spines["bottom"].set_color(grid)
            ax.tick_params(colors=fg, labelsize=9)
            ax.yaxis.grid(True, linestyle="--", color=grid, alpha=0.5)
            ax.xaxis.grid(False)

        # Plot 1: Rating Distribution
        valid_ratings = df[df["vote_average"] > 0]["vote_average"]
        if len(valid_ratings) > 0:
            rating_hist = pd.cut(valid_ratings, bins=15).value_counts().sort_index()
            bins = [interval.mid for interval in rating_hist.index]
            counts = rating_hist.values
            ax1.fill_between(bins, counts, color=accent, alpha=0.2)
            ax1.plot(bins, counts, color=accent, linewidth=2.5)
            ax1.set_title("Audience Ratings Distribution", color=fg, pad=15, weight="bold", size=13)

        # Plot 2: Most Popular Movies
        top_movies = df.nlargest(8, "popularity").sort_values("popularity", ascending=True)
        if not top_movies.empty:
            titles = [t[:18] + "…" if len(t) > 18 else t for t in top_movies["title"]]
            ax2.barh(titles, top_movies["popularity"], height=0.5, color=secondary)
            ax2.set_title("Trending Popularity Scores", color=fg, pad=15, weight="bold", size=13)

        plt.tight_layout(pad=3.0)

        canvas = FigureCanvas(fig)
        self.canvas_container.addWidget(canvas)
        self.canvas_widget = canvas
