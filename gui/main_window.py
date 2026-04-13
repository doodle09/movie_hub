from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.discover_view import DiscoverView
from gui.analytics_view import AnalyticsView
from gui.settings_view import SettingsView
from utils.theme_engine import get_accent


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MovieHub Desktop Pro")
        self.resize(1280, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._build_sidebar(main_layout)
        self._build_stacked_widget(main_layout)

    def _build_sidebar(self, parent_layout):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #18181B;
                border-right: 1px solid #27272A;
            }
        """)

        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(20, 35, 20, 20)
        layout.setSpacing(8)

        # Logo
        logo_lbl = QLabel("🍿 MovieHub")
        logo_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        logo_lbl.setStyleSheet("color: white; border: none;")
        layout.addWidget(logo_lbl)

        layout.addSpacing(30)

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("discover", "🏠  Discover"),
            ("analytics", "📊  Analytics"),
            ("settings", "⚙️  Settings"),
        ]

        for name, text in nav_items:
            btn = QPushButton(text)
            btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda checked, n=name: self.switch_view(n))
            layout.addWidget(btn)
            self.nav_buttons[name] = btn

        layout.addStretch()
        parent_layout.addWidget(self.sidebar)

    def _build_stacked_widget(self, parent_layout):
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #0E0E10; border: none;")

        self.views = {
            "discover": DiscoverView(self),
            "analytics": AnalyticsView(self),
            "settings": SettingsView(self),
        }

        for view in self.views.values():
            self.stacked_widget.addWidget(view)

        parent_layout.addWidget(self.stacked_widget)
        self.switch_view("discover")

    def switch_view(self, name):
        view = self.views.get(name)
        if view:
            if hasattr(view, "refresh_on_load"):
                view.refresh_on_load()
            self.stacked_widget.setCurrentWidget(view)

        accent = get_accent()
        for view_name, btn in self.nav_buttons.items():
            if view_name == name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {accent};
                        color: white;
                        text-align: left;
                        padding-left: 15px;
                        border-radius: 8px;
                        border: none;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #A1A1AA;
                        text-align: left;
                        padding-left: 15px;
                        border-radius: 8px;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #27272A;
                        color: white;
                    }
                """)
