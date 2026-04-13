"""
Custom dark theme engine for MovieHub.
Inspired by CineVerse UI — pure black cinematic base with cyan/teal accents.
Single fixed dark theme — cinematic, premium, immersive.
"""

# Primary accent: Cyan-teal (CineVerse style)
ACCENT = "#06B6D4"
# Secondary accent: Warm gold for ratings
ACCENT_GOLD = "#FCD06F"
# Tertiary accent: Purple for genre pills & AI features
ACCENT_PURPLE = "#8B5CF6"
# Success
ACCENT_GREEN = "#10B981"
# Danger
ACCENT_RED = "#EF4444"

def get_accent():
    return ACCENT

def get_colors():
    """Return the fixed dark cinematic theme color palette."""
    return {
        # Backgrounds — near-black like CineVerse
        "bg_main": "#0A0A0F",
        "bg_card": "#12121A",
        "bg_input": "#16161F",
        "bg_sidebar": "#08080D",
        "bg_header": "#0D0D14",
        "bg_hover": "#1A1A26",
        "banner_bg": "#0A0A0F",
        "card_bg": "#12121A",
        "bg_elevated": "#1A1A26",
        # Glass effects
        "glass_bg": "rgba(12, 12, 18, 0.9)",
        "glass_border": "rgba(255, 255, 255, 0.05)",
        "glass_hover": "rgba(26, 26, 38, 0.9)",
        # Text
        "text_primary": "#E8ECF0",
        "text_secondary": "#9CA3AF",
        "text_muted": "#5A5F6B",
        "overlay_text": "#FFFFFF",
        "overlay_desc": "#C8CDD3",
        # Borders
        "border": "#1E1E2A",
        "border_subtle": "#15151F",
        "scroll_bg": "#2A2A3A",
        # Accents
        "accent": ACCENT,
        "accent_gold": ACCENT_GOLD,
        "accent_purple": ACCENT_PURPLE,
        "accent_green": ACCENT_GREEN,
        "accent_red": ACCENT_RED,
        # Gradients
        "gradient_start": "#08080D",
        "gradient_end": "#0D0D14",
        "sidebar_gradient_start": "#08080D",
        "sidebar_gradient_end": "#0A0A12",
        # Card hover
        "card_hover_border": "#06B6D4",
        "card_hover_glow": "rgba(6, 182, 212, 0.12)",
        # Chart-specific
        "chart_bg": "#12121A",
        "chart_grid": "#1E1E2A",
        "chart_text": "#E8ECF0",
        "chart_accent": ACCENT,
        "chart_secondary": ACCENT_GOLD,
    }


def build_app_stylesheet(**kwargs):
    """Generates the full application QSS stylesheet — CineVerse dark."""
    a = ACCENT
    c = get_colors()
    
    return f"""
    /* ========== Global ========== */
    QWidget {{
        background-color: {c['bg_main']};
        color: {c['text_primary']};
        font-family: "Segoe UI", "SF Pro Display", sans-serif;
    }}
    
    QFrame {{
        background-color: {c['bg_card']};
        border-color: {c['border']};
    }}
    QLabel {{
        background-color: transparent;
        color: {c['text_primary']};
    }}
    
    /* ========== Scroll Areas ========== */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        width: 5px;
        background: transparent;
        margin: 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['scroll_bg']};
        border-radius: 2px;
        min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {a};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        height: 5px;
        background: transparent;
        margin: 0 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['scroll_bg']};
        border-radius: 2px;
        min-width: 40px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {a};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}
    
    /* ========== Inputs ========== */
    QLineEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        padding: 10px 16px;
        border: 1px solid {c['border']};
        border-radius: 10px;
        font-size: 14px;
        selection-background-color: {a};
    }}
    QLineEdit:focus {{
        border: 1px solid {a};
    }}
    QLineEdit::placeholder {{
        color: {c['text_muted']};
    }}
    
    /* ========== ComboBox ========== */
    QComboBox {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        padding: 8px 15px;
        border-radius: 10px;
        border: 1px solid {c['border']};
        font-size: 13px;
    }}
    QComboBox:hover {{
        border: 1px solid {c['scroll_bg']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['bg_elevated']};
        color: {c['text_primary']};
        selection-background-color: {a};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    
    /* ========== Tooltips ========== */
    QToolTip {{
        background-color: {c['bg_elevated']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    
    /* ========== Stacked Widget ========== */
    QStackedWidget {{
        background-color: {c['bg_main']};
        border: none;
    }}
    """
