"""UI styles and themes for HoloPazaak.

This module provides comprehensive theming with inspiration from:
- KOTOR's authentic visual style
- pazaak-eggborne's modern starfield aesthetic
- Sith and Republic color schemes
- Card game visual conventions

Includes CSS stylesheets for all Qt widgets with animations
and visual polish.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ThemeColors:
    """Color scheme for a theme."""
    name: str
    
    # Main colors
    background: str
    background_alt: str
    panel: str
    panel_highlight: str
    
    # Text colors
    text: str
    text_muted: str
    text_accent: str
    
    # Button colors
    button_bg: str
    button_text: str
    button_hover: str
    button_disabled: str
    
    # Card colors
    card_main: str
    card_main_border: str
    card_plus: str
    card_plus_border: str
    card_minus: str
    card_minus_border: str
    card_flip: str
    card_flip_border: str
    card_special: str
    card_special_border: str
    
    # Status colors
    success: str
    warning: str
    error: str
    
    # Board colors
    board_bg: str
    board_border: str
    
    # Score indicator
    score_normal: str
    score_good: str
    score_danger: str
    score_bust: str
    
    def get(self, key: str, default: str = "") -> str:
        """Get a color by key name (dict-like access).
        
        This allows ThemeColors to be used like a dict in widgets.
        """
        # Map simplified keys to attribute names
        key_map = {
            "background": "background",
            "panel": "panel",
            "text": "text",
            "button": "button_bg",
            "button_text": "button_text",
            "card_main": "card_main",
            "card_plus": "card_plus",
            "card_minus": "card_minus",
            "card_flip": "card_flip",
            "card_double": "card_special",
            "card_tiebreaker": "card_special",
            "card_plus_minus_3_6": "card_special",
        }
        
        attr_name = key_map.get(key, key)
        return getattr(self, attr_name, default)


class Theme:
    """Theme definitions for HoloPazaak."""
    
    REPUBLIC = ThemeColors(
        name="Republic",
        
        # Cool blue-gray tones
        background="#1a1f2e",
        background_alt="#232a3d",
        panel="#2d3548",
        panel_highlight="#3a4660",
        
        # Text
        text="#e8eaf0",
        text_muted="#8890a4",
        text_accent="#4ecdc4",
        
        # Buttons - republic blue/green
        button_bg="#2c7d7b",
        button_text="#ffffff",
        button_hover="#3a9694",
        button_disabled="#4a5568",
        
        # Cards
        card_main="#4a6741",
        card_main_border="#6b8f5f",
        card_plus="#3d5a80",
        card_plus_border="#5588bb",
        card_minus="#8b3a3a",
        card_minus_border="#b05050",
        card_flip="#6b5b3d",
        card_flip_border="#9a8560",
        card_special="#5a4a70",
        card_special_border="#8070a0",
        
        # Status
        success="#4ecdc4",
        warning="#f4d35e",
        error="#ee6055",
        
        # Board
        board_bg="#1e2433",
        board_border="#3a4660",
        
        # Score
        score_normal="#e8eaf0",
        score_good="#4ecdc4",
        score_danger="#f4d35e",
        score_bust="#ee6055",
    )
    
    SITH = ThemeColors(
        name="Sith",
        
        # Dark with red accents
        background="#0f0a0a",
        background_alt="#1a1010",
        panel="#251515",
        panel_highlight="#3a2020",
        
        # Text
        text="#e0d0d0",
        text_muted="#8a7575",
        text_accent="#ff4444",
        
        # Buttons - sith red/black
        button_bg="#8b0000",
        button_text="#ffffff",
        button_hover="#aa2020",
        button_disabled="#3a2a2a",
        
        # Cards - darker variants
        card_main="#3a4a30",
        card_main_border="#5a7048",
        card_plus="#304050",
        card_plus_border="#4a6888",
        card_minus="#602020",
        card_minus_border="#883030",
        card_flip="#504020",
        card_flip_border="#786040",
        card_special="#402848",
        card_special_border="#604068",
        
        # Status
        success="#44aa44",
        warning="#dd9922",
        error="#ff4444",
        
        # Board
        board_bg="#120808",
        board_border="#4a2020",
        
        # Score
        score_normal="#e0d0d0",
        score_good="#44aa44",
        score_danger="#dd9922",
        score_bust="#ff4444",
    )
    
    KOTOR_CLASSIC = ThemeColors(
        name="KOTOR Classic",
        
        # Authentic KOTOR amber/brown
        background="#1c1810",
        background_alt="#252015",
        panel="#2e2820",
        panel_highlight="#3d3528",
        
        # Text - amber
        text="#d4c4a0",
        text_muted="#8a7a58",
        text_accent="#e8b030",
        
        # Buttons - gold/amber
        button_bg="#8a6a20",
        button_text="#ffffff",
        button_hover="#aa8830",
        button_disabled="#4a4030",
        
        # Cards
        card_main="#404830",
        card_main_border="#606850",
        card_plus="#305858",
        card_plus_border="#487878",
        card_minus="#583030",
        card_minus_border="#784848",
        card_flip="#585028",
        card_flip_border="#787048",
        card_special="#483858",
        card_special_border="#685078",
        
        # Status
        success="#88aa44",
        warning="#e8b030",
        error="#cc4444",
        
        # Board
        board_bg="#1a1408",
        board_border="#4a4030",
        
        # Score
        score_normal="#d4c4a0",
        score_good="#88aa44",
        score_danger="#e8b030",
        score_bust="#cc4444",
    )
    
    MANDALORIAN = ThemeColors(
        name="Mandalorian",
        
        # Steel gray with blue highlights
        background="#14181c",
        background_alt="#1c2228",
        panel="#252d35",
        panel_highlight="#323e48",
        
        # Text
        text="#c8d0d8",
        text_muted="#7088a0",
        text_accent="#5080c0",
        
        # Buttons - beskar steel
        button_bg="#4a5a6a",
        button_text="#ffffff",
        button_hover="#5a7088",
        button_disabled="#3a4550",
        
        # Cards
        card_main="#3a4840",
        card_main_border="#5a6858",
        card_plus="#304858",
        card_plus_border="#486878",
        card_minus="#583840",
        card_minus_border="#785058",
        card_flip="#4a4838",
        card_flip_border="#6a6858",
        card_special="#3a3858",
        card_special_border="#5a5878",
        
        # Status
        success="#50a0a0",
        warning="#c0a040",
        error="#c05050",
        
        # Board
        board_bg="#0c1014",
        board_border="#3a4850",
        
        # Score
        score_normal="#c8d0d8",
        score_good="#50a0a0",
        score_danger="#c0a040",
        score_bust="#c05050",
    )


# All available themes
THEMES: dict[str, ThemeColors] = {
    "republic": Theme.REPUBLIC,
    "sith": Theme.SITH,
    "kotor": Theme.KOTOR_CLASSIC,
    "mandalorian": Theme.MANDALORIAN,
}


def get_theme(name: str) -> ThemeColors:
    """Get a theme by name."""
    return THEMES.get(name.lower(), Theme.REPUBLIC)


def get_stylesheet(theme: ThemeColors) -> str:
    """Generate a complete Qt stylesheet for the theme.
    
    Includes styles for:
    - Main window and central widget
    - Labels and text
    - Buttons with hover/pressed/disabled states
    - Frames and panels
    - Text edits and log areas
    - Checkboxes and radio buttons
    - List widgets and scroll areas
    - Progress bars
    - Tooltips
    """
    return f"""
/* ========================================
   HoloPazaak Theme: {theme.name}
   ======================================== */

/* Main Window */
QMainWindow {{
    background-color: {theme.background};
    color: {theme.text};
}}

QWidget {{
    background-color: transparent;
    color: {theme.text};
    font-family: "Segoe UI", "San Francisco", "Helvetica Neue", Arial, sans-serif;
}}

/* Labels */
QLabel {{
    color: {theme.text};
    background-color: transparent;
    padding: 2px;
}}

QLabel[class="title"] {{
    font-size: 24px;
    font-weight: bold;
    color: {theme.text_accent};
}}

QLabel[class="score"] {{
    font-size: 18px;
    font-weight: bold;
}}

QLabel[class="muted"] {{
    color: {theme.text_muted};
}}

/* Buttons */
QPushButton {{
    background-color: {theme.button_bg};
    color: {theme.button_text};
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {theme.button_hover};
}}

QPushButton:pressed {{
    background-color: {theme.button_bg};
    transform: translateY(1px);
}}

QPushButton:disabled {{
    background-color: {theme.button_disabled};
    color: {theme.text_muted};
}}

QPushButton[class="action"] {{
    background-color: {theme.success};
    min-width: 120px;
}}

QPushButton[class="action"]:hover {{
    background-color: {theme.success}dd;
}}

QPushButton[class="danger"] {{
    background-color: {theme.error};
}}

QPushButton[class="danger"]:hover {{
    background-color: {theme.error}dd;
}}

/* Frames and Panels */
QFrame {{
    background-color: {theme.panel};
    border-radius: 8px;
    border: 1px solid {theme.panel_highlight};
}}

QFrame[class="board"] {{
    background-color: {theme.board_bg};
    border: 2px solid {theme.board_border};
    border-radius: 12px;
    min-height: 180px;
}}

QFrame[class="card"] {{
    border-radius: 8px;
    border-width: 2px;
}}

/* Text Edits and Log */
QTextEdit {{
    background-color: {theme.background_alt};
    color: {theme.text};
    border: 1px solid {theme.panel_highlight};
    border-radius: 6px;
    padding: 8px;
    font-family: "Consolas", "Monaco", "Courier New", monospace;
    font-size: 12px;
}}

QPlainTextEdit {{
    background-color: {theme.background_alt};
    color: {theme.text};
    border: 1px solid {theme.panel_highlight};
    border-radius: 6px;
    padding: 8px;
}}

/* Checkboxes */
QCheckBox {{
    color: {theme.text};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {theme.text_muted};
    background-color: {theme.panel};
}}

QCheckBox::indicator:checked {{
    background-color: {theme.success};
    border-color: {theme.success};
}}

QCheckBox::indicator:hover {{
    border-color: {theme.text_accent};
}}

/* List Widgets */
QListWidget {{
    background-color: {theme.background_alt};
    color: {theme.text};
    border: 1px solid {theme.panel_highlight};
    border-radius: 6px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {theme.button_bg};
    color: {theme.button_text};
}}

QListWidget::item:hover {{
    background-color: {theme.panel_highlight};
}}

/* Scroll Areas */
QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: {theme.background_alt};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {theme.panel_highlight};
    border-radius: 4px;
    min-height: 40px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {theme.text_muted};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {theme.background_alt};
    border: none;
    border-radius: 4px;
    height: 8px;
}}

QProgressBar::chunk {{
    background-color: {theme.success};
    border-radius: 4px;
}}

/* Tooltips */
QToolTip {{
    background-color: {theme.panel};
    color: {theme.text};
    border: 1px solid {theme.panel_highlight};
    border-radius: 4px;
    padding: 6px;
}}

/* Dialogs */
QDialog {{
    background-color: {theme.background};
}}

/* Group Box */
QGroupBox {{
    background-color: {theme.panel};
    border: 1px solid {theme.panel_highlight};
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    color: {theme.text_accent};
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 16px;
}}

/* Spin Box */
QSpinBox {{
    background-color: {theme.background_alt};
    color: {theme.text};
    border: 1px solid {theme.panel_highlight};
    border-radius: 4px;
    padding: 4px 8px;
}}

QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {theme.panel};
    border: none;
    width: 20px;
}}

/* Menu Bar */
QMenuBar {{
    background-color: {theme.background_alt};
    color: {theme.text};
    border-bottom: 1px solid {theme.panel_highlight};
}}

QMenuBar::item:selected {{
    background-color: {theme.panel_highlight};
}}

QMenu {{
    background-color: {theme.panel};
    color: {theme.text};
    border: 1px solid {theme.panel_highlight};
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {theme.button_bg};
}}
"""


def get_card_style(theme: ThemeColors, card_type: str, is_selected: bool = False) -> str:
    """Get inline style for a card based on type.
    
    Args:
        theme: Current theme
        card_type: One of "main", "plus", "minus", "flip", "special"
        is_selected: Whether the card is selected
    """
    colors = {
        "main": (theme.card_main, theme.card_main_border),
        "plus": (theme.card_plus, theme.card_plus_border),
        "minus": (theme.card_minus, theme.card_minus_border),
        "flip": (theme.card_flip, theme.card_flip_border),
        "special": (theme.card_special, theme.card_special_border),
    }
    
    bg_color, border_color = colors.get(card_type, colors["main"])
    
    border_width = "3px" if is_selected else "2px"
    if is_selected:
        border_color = theme.success
    
    return f"""
        background-color: {bg_color};
        border: {border_width} solid {border_color};
        border-radius: 8px;
    """


def get_score_color(theme: ThemeColors, score: int) -> str:
    """Get color for score display based on value."""
    if score > 20:
        return theme.score_bust
    elif score == 20:
        return theme.score_good
    elif score >= 17:
        return theme.score_danger
    return theme.score_normal
