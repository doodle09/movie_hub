from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QLinearGradient, QColor, QPainter, QBrush

from gui.discover_view import DiscoverView
from gui.analytics_view import AnalyticsView
from gui.settings_view import SettingsView
from utils.theme_engine import get_accent, get_colors


class _GradientFrame(QFrame):
    """A QFrame that paints a vertical gradient background."""
    def __init__(self, color_top, color_bottom, parent=None):
        super().__init__(parent)
        self._color_top = QColor(color_top)
        self._color_bottom = QColor(color_bottom)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, self._color_top)
        gradient.setColorAt(1.0, self._color_bottom)
        painter.fillRect(self.rect(), QBrush(gradient))
        painter.end()


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
        c = get_colors()
        
        self.sidebar = _GradientFrame(c['sidebar_gradient_start'], c['sidebar_gradient_end'])
        self.sidebar.setFixedWidth(230)
        self.sidebar.setObjectName("SidebarFrame")
        self.sidebar.setStyleSheet(f"""
            QFrame#SidebarFrame {{
                border-right: 1px solid {c['border_subtle']};
            }}
        """)

        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(16, 28, 16, 20)
        layout.setSpacing(4)

        # Logo — CineVerse style pill badge
        logo_frame = QWidget()
        logo_frame.setStyleSheet("background-color: transparent;")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(6, 0, 0, 0)
        logo_layout.setSpacing(0)
        
        logo_badge = QLabel("  MovieHub  ")
        logo_badge.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        logo_badge.setFixedHeight(36)
        logo_badge.setStyleSheet(f"""
            background-color: {c['accent']};
            color: white;
            border-radius: 8px;
            padding: 4px 16px;
            font-size: 14px;
        """)
        logo_layout.addWidget(logo_badge)
        logo_layout.addStretch()
        
        layout.addWidget(logo_frame)
        layout.addSpacing(28)

        # Nav section label
        section_lbl = QLabel("MENU")
        section_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        section_lbl.setStyleSheet(f"color: {c['text_muted']}; padding-left: 10px; letter-spacing: 2px; background-color: transparent;")
        layout.addWidget(section_lbl)
        layout.addSpacing(10)

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("discover", "🏠", "Discover"),
            ("analytics", "📊", "Analytics"),
            ("settings", "⚙️", "Settings"),
        ]

        for name, icon, text in nav_items:
            btn = QPushButton(f"  {icon}   {text}")
            btn.setFont(QFont("Segoe UI", 12))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda checked, n=name: self.switch_view(n))
            layout.addWidget(btn)
            self.nav_buttons[name] = btn

        layout.addStretch()
        
        # Separator before footer
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {c['border']};")
        layout.addWidget(sep)
        layout.addSpacing(12)
        
        # Footer
        version_lbl = QLabel("v2.0 · Premium Edition")
        version_lbl.setFont(QFont("Segoe UI", 9))
        version_lbl.setStyleSheet(f"color: {c['text_muted']}; background-color: transparent;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_lbl)
        
        parent_layout.addWidget(self.sidebar)

    def _build_stacked_widget(self, parent_layout):
        self.stacked_widget = QStackedWidget()

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

        self._update_nav_buttons(name)

    def _update_nav_buttons(self, active_name):
        """Style nav buttons — active gets cyan accent."""
        c = get_colors()
        accent = c["accent"]

        for view_name, btn in self.nav_buttons.items():
            if view_name == active_name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(6, 182, 212, 0.12);
                        color: {accent};
                        text-align: left;
                        padding-left: 12px;
                        border-radius: 10px;
                        border: none;
                        border-left: 3px solid {accent};
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {c['text_secondary']};
                        text-align: left;
                        padding-left: 15px;
                        border-radius: 10px;
                        border: none;
                    }}
                    QPushButton:hover {{
                        background-color: {c['bg_hover']};
                        color: {c['text_primary']};
                    }}
                """)
