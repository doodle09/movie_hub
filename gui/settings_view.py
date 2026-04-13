from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QScrollArea, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from utils.config_manager import ConfigManager
from utils.theme_engine import THEMES, build_app_stylesheet


class SettingsView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        self.layout_content = QVBoxLayout(content_widget)
        self.layout_content.setContentsMargins(0, 0, 0, 0)
        self.layout_content.setSpacing(30)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        self._build_theme_section()
        self._build_api_section()
        self.layout_content.addStretch()

    def _build_theme_section(self):
        frame = self._create_card("Appearance & Theme")
        layout = frame.layout()

        row = QHBoxLayout()
        lbl = QLabel("Base Theme:")
        lbl.setFixedWidth(120)
        lbl.setStyleSheet("color: #A1A1AA; font-size: 14px;")

        self.base_combo = QComboBox()
        self.base_combo.addItems(["Dark", "Light"])
        self.base_combo.setFixedWidth(200)
        from utils.theme_engine import get_base
        self.base_combo.setCurrentText("Light" if get_base() == "light" else "Dark")
        self.base_combo.currentTextChanged.connect(self._change_theme)
        
        row.addWidget(lbl)
        row.addWidget(self.base_combo)
        row.addStretch()
        layout.addLayout(row)
        layout.addSpacing(15)

        row = QHBoxLayout()
        lbl = QLabel("Accent Color:")
        lbl.setFixedWidth(120)
        lbl.setStyleSheet("color: #A1A1AA; font-size: 14px;")

        self.accent_combo = QComboBox()
        self.accent_combo.addItems(list(THEMES.keys()))
        self.accent_combo.setFixedWidth(200)
        self.accent_combo.currentTextChanged.connect(self._change_theme)

        row.addWidget(lbl)
        row.addWidget(self.accent_combo)
        row.addStretch()
        layout.addLayout(row)

    def _build_api_section(self):
        frame = self._create_card("API Configuration ⚙️")
        layout = frame.layout()

        desc = QLabel("Add multiple Gemini keys to automatically rotate on Quota Exceeded (429) errors.")
        desc.setStyleSheet("color: #71717A; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(10)

        existing_keys = ConfigManager.get_gemini_pool()
        self.gemini_entries = []

        for i in range(5):
            row = QHBoxLayout()
            lbl = QLabel(f"Gemini Key {i + 1}:")
            lbl.setFixedWidth(120)
            lbl.setStyleSheet("color: #A1A1AA; font-size: 14px;")

            entry = QLineEdit()
            entry.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
            entry.setPlaceholderText("AIzaSy...")
            entry.setFixedWidth(420)

            if i < len(existing_keys):
                entry.setText(existing_keys[i])

            self.gemini_entries.append(entry)
            row.addWidget(lbl)
            row.addWidget(entry)
            row.addStretch()
            layout.addLayout(row)

        layout.addSpacing(15)

        row = QHBoxLayout()
        omdb_lbl = QLabel("OMDb API Key:")
        omdb_lbl.setFixedWidth(120)
        omdb_lbl.setStyleSheet("color: #A1A1AA; font-size: 14px;")

        self.omdb_entry = QLineEdit()
        self.omdb_entry.setPlaceholderText("Optional fallback...")
        self.omdb_entry.setFixedWidth(420)
        self.omdb_entry.setText(ConfigManager.get_omdb_key())

        row.addWidget(omdb_lbl)
        row.addWidget(self.omdb_entry)
        row.addStretch()
        layout.addLayout(row)

        layout.addSpacing(20)

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setFixedWidth(200)
        self.save_btn.setFixedHeight(42)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #0A84FF; color: white; font-weight: bold;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #0070E0; }
        """)
        self.save_btn.clicked.connect(self._save_config)
        layout.addWidget(self.save_btn)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #10B981; font-weight: bold;")
        layout.addWidget(self.status_lbl)

    def _create_card(self, title_text):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: transparent; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(title_text)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)
        layout.addSpacing(15)

        self.layout_content.addWidget(frame)
        return frame

    def _change_theme(self, text=None):
        accent_hex = THEMES.get(self.accent_combo.currentText(), "#0A84FF")
        base_theme = self.base_combo.currentText().lower()

        # Instantly rebuild and apply the entire application stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_app_stylesheet(accent=accent_hex, base=base_theme))

        # Refresh sidebar button highlights
        self.main_window.switch_view("settings")

        # Update save button color to match new accent
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {accent_hex}; color: white; font-weight: bold;
                border-radius: 8px; border: none;
            }}
            QPushButton:hover {{ background-color: #0070E0; }}
        """)

    def _save_config(self):
        keys = []
        for entry in self.gemini_entries:
            val = entry.text().strip()
            if val:
                keys.append(val)

        config = ConfigManager.load_config()
        config["gemini_keys"] = keys
        config["omdb_key"] = self.omdb_entry.text().strip()
        ConfigManager.save_config(config)

        self.status_lbl.setText("✅ Settings saved successfully.")
        QTimer.singleShot(3000, lambda: self.status_lbl.setText(""))
