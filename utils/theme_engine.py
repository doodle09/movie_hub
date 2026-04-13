"""Custom QSS theme engine for MovieHub — supports instant live accent color swaps."""

THEMES = {
    "Electric Blue": "#0A84FF",
    "Neon Pink": "#FF375F",
    "Hacker Green": "#30D158",
    "Deep Purple": "#BF5AF2",
}

# Current state — mutable global
_current_accent = "#0A84FF"
_current_base = "dark"

def get_accent():
    return _current_accent

def get_base():
    return _current_base

def build_app_stylesheet(accent=None, base=None):
    """Generates the full application QSS stylesheet with the given accent and base theme."""
    global _current_accent, _current_base
    if accent:
        _current_accent = accent
    if base:
        _current_base = base
        
    a = _current_accent
    
    # Define color palettes
    if _current_base == "light":
        bg_main = "#FAFAFA"
        bg_card = "#FFFFFF"
        bg_input = "#E4E4E7"
        text_primary = "#18181B"
        text_secondary = "#71717A"
        border_color = "#D4D4D8"
        bg_hover = "#F4F4F5"
        scroll_bg = "#E4E4E7"
    else:
        bg_main = "#0E0E10"
        bg_card = "#18181B"
        bg_input = "#18181B"
        text_primary = "#FAFAFA"
        text_secondary = "#A1A1AA"
        border_color = "#27272A"
        bg_hover = "#27272A"
        scroll_bg = "#3F3F46"

    return f"""
    /* ========== Global ========== */
    QWidget {{
        background-color: {bg_main};
        color: {text_primary};
        font-family: "Segoe UI", sans-serif;
    }}
    
    QFrame {{
        background-color: {bg_card};
        border-color: {border_color};
    }}
    QLabel {{
        background-color: transparent;
    }}
    
    /* ========== Scroll Areas ========== */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        width: 8px;
        background: {bg_card};
    }}
    QScrollBar::handle:vertical {{
        background: {scroll_bg};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        height: 8px;
        background: {bg_card};
    }}
    QScrollBar::handle:horizontal {{
        background: {scroll_bg};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* ========== Inputs ========== */
    QLineEdit {{
        background-color: {bg_input};
        color: {text_primary};
        padding: 10px;
        border: 1px solid {border_color};
        border-radius: 6px;
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border: 1px solid {a};
    }}
    
    /* ========== ComboBox ========== */
    QComboBox {{
        background-color: {bg_input};
        color: {text_primary};
        padding: 8px 15px;
        border-radius: 8px;
        border: 1px solid {border_color};
    }}
    QComboBox::drop-down {{
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {bg_input};
        color: {text_primary};
        selection-background-color: {a};
    }}
    """
