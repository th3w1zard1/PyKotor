"""VS Code-like styling utilities for code editors.

This module provides fonts, colors, and styling configurations that mimic
VS Code's appearance for a professional IDE experience.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QColor, QFont, QFontDatabase, QFontMetrics, QPalette
from qtpy.QtWidgets import QApplication

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


# VS Code's default font stack with fallbacks for all platforms
# These are all monospace fonts with consistent character widths
VSCODE_FONT_FAMILIES = (
    # Modern fonts with ligature support
    "Cascadia Code",
    "Cascadia Mono",
    "Fira Code",
    "JetBrains Mono",
    # Traditional monospace fonts
    "Consolas",          # Windows default
    "SF Mono",           # macOS
    "Monaco",            # macOS fallback
    "Menlo",             # macOS
    "Ubuntu Mono",       # Linux
    "DejaVu Sans Mono",  # Linux
    "Liberation Mono",   # Linux
    "Source Code Pro",
    "Droid Sans Mono",
    # Ultimate fallbacks
    "Courier New",
    "Courier",
    "monospace",         # Generic fallback
)

# Default font size matching VS Code
DEFAULT_FONT_SIZE = 14
DEFAULT_LINE_HEIGHT = 1.5
DEFAULT_TAB_SIZE = 4


def get_best_monospace_font(
    preferred_families: tuple[str, ...] | None = None,
    size: int = DEFAULT_FONT_SIZE,
) -> QFont:
    """Get the best available monospace font from the system.
    
    Checks for available fonts in order of preference and returns
    the first one found. This ensures consistent character width
    across the editor (essential for code alignment).
    
    Args:
        preferred_families: Optional tuple of font families to try first.
        size: Font size in points.
        
    Returns:
        QFont configured with the best available monospace font.
    """
    families_to_try = preferred_families or VSCODE_FONT_FAMILIES
    font_db = QFontDatabase()
    
    # Get list of all available font families
    available_families = set(font_db.families())
    
    # Find first available font from our preferred list
    selected_family = None
    for family in families_to_try:
        if family in available_families:
            # Verify it's actually monospace
            test_font = QFont(family, size)
            test_font.setStyleHint(QFont.StyleHint.Monospace)
            if font_db.isFixedPitch(family) or _is_font_monospace(test_font):
                selected_family = family
                break
    
    # Create the font with proper configuration
    font = QFont()
    if selected_family:
        font.setFamily(selected_family)
    else:
        # Fall back to system monospace
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFamily("monospace")
    
    # Configure font properties for VS Code-like appearance
    font.setPointSize(size)
    font.setFixedPitch(True)
    font.setStyleHint(QFont.StyleHint.Monospace)
    
    # Disable kerning for consistent character spacing
    font.setKerning(False)
    
    # Use medium weight for better readability
    font.setWeight(QFont.Weight.Normal)
    
    # Enable hinting for sharper rendering
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    
    return font


def _is_font_monospace(font: QFont) -> bool:
    """Check if a font is actually monospace by comparing character widths.
    
    Args:
        font: The font to check.
        
    Returns:
        True if the font appears to be monospace.
    """
    metrics = QFontMetrics(font)
    
    # Compare widths of different characters
    # In a true monospace font, all these should be the same
    test_chars = ["i", "m", "W", "l", ".", " "]
    widths = [metrics.horizontalAdvance(char) for char in test_chars]
    
    # Check if all widths are the same (with small tolerance for rendering)
    if not widths:
        return False
    first_width = widths[0]
    return all(abs(w - first_width) <= 1 for w in widths)


def get_editor_stylesheet(
    *,
    use_ligatures: bool = False,
) -> str:
    """Get a VS Code-like stylesheet for code editors.
    
    This stylesheet uses palette colors for theme compatibility
    while providing VS Code-like visual appearance.
    
    Args:
        use_ligatures: Whether to enable font ligatures (requires supported font).
        
    Returns:
        CSS stylesheet string for QPlainTextEdit/QTextEdit widgets.
    """
    ligature_style = "normal" if use_ligatures else "none"
    
    return f"""
        QPlainTextEdit, QTextEdit {{
            background-color: palette(base);
            color: palette(text);
            border: none;
            selection-background-color: palette(highlight);
            selection-color: palette(highlighted-text);
            /* Ensure consistent character spacing */
            font-variant-ligatures: {ligature_style};
        }}
        
        /* Scrollbar styling - VS Code uses thin, unobtrusive scrollbars */
        QPlainTextEdit QScrollBar:vertical,
        QTextEdit QScrollBar:vertical {{
            background-color: transparent;
            width: 14px;
            margin: 0;
        }}
        
        QPlainTextEdit QScrollBar::handle:vertical,
        QTextEdit QScrollBar::handle:vertical {{
            background-color: palette(mid);
            border-radius: 4px;
            min-height: 30px;
            margin: 2px;
        }}
        
        QPlainTextEdit QScrollBar::handle:vertical:hover,
        QTextEdit QScrollBar::handle:vertical:hover {{
            background-color: palette(dark);
        }}
        
        QPlainTextEdit QScrollBar::add-line:vertical,
        QPlainTextEdit QScrollBar::sub-line:vertical,
        QTextEdit QScrollBar::add-line:vertical,
        QTextEdit QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}
        
        QPlainTextEdit QScrollBar:horizontal,
        QTextEdit QScrollBar:horizontal {{
            background-color: transparent;
            height: 14px;
            margin: 0;
        }}
        
        QPlainTextEdit QScrollBar::handle:horizontal,
        QTextEdit QScrollBar::handle:horizontal {{
            background-color: palette(mid);
            border-radius: 4px;
            min-width: 30px;
            margin: 2px;
        }}
        
        QPlainTextEdit QScrollBar::add-line:horizontal,
        QPlainTextEdit QScrollBar::sub-line:horizontal,
        QTextEdit QScrollBar::add-line:horizontal,
        QTextEdit QScrollBar::sub-line:horizontal {{
            width: 0;
            background: none;
        }}
    """


def get_tooltip_stylesheet() -> str:
    """Get a VS Code-like stylesheet for tooltips.
    
    Uses palette colors for automatic theme adaptation while maintaining
    good readability in both light and dark themes.
    
    Returns:
        CSS stylesheet string for QToolTip widgets.
    """
    return """
        QToolTip {
            background-color: palette(window);
            color: palette(window-text);
            border: 1px solid palette(mid);
            border-radius: 4px;
            padding: 8px 12px;
            font-family: "Segoe UI", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
            font-size: 12px;
        }
    """


def configure_code_editor_font(
    widget: QWidget,
    size: int | None = None,
    preferred_families: tuple[str, ...] | None = None,
) -> QFont:
    """Configure a widget with VS Code-like monospace font.
    
    This is the main entry point for configuring code editor fonts.
    It sets up a proper monospace font with all the necessary properties
    for a professional code editing experience.
    
    Args:
        widget: The widget to configure (usually QPlainTextEdit).
        size: Optional font size override.
        preferred_families: Optional preferred font families.
        
    Returns:
        The QFont that was applied to the widget.
    """
    font_size = size or DEFAULT_FONT_SIZE
    font = get_best_monospace_font(preferred_families, font_size)
    
    # Apply font to widget
    widget.setFont(font)
    
    # Set tab stop width to match VS Code (4 spaces by default)
    if hasattr(widget, 'setTabStopDistance'):
        metrics = QFontMetrics(font)
        tab_width = metrics.horizontalAdvance(' ') * DEFAULT_TAB_SIZE
        widget.setTabStopDistance(tab_width)
    elif hasattr(widget, 'setTabStopWidth'):
        # Fallback for older Qt versions
        metrics = QFontMetrics(font)
        tab_width = metrics.horizontalAdvance(' ') * DEFAULT_TAB_SIZE
        widget.setTabStopWidth(int(tab_width))
    
    return font


def get_documentation_tooltip_html(
    title: str,
    signature: str | None = None,
    description: str | None = None,
    widget: QWidget | None = None,
) -> str:
    """Generate VS Code-like documentation tooltip HTML.
    
    Creates a properly formatted tooltip that works with any Qt theme
    by using relative colors and proper styling.
    
    Args:
        title: The main title (e.g., function name).
        signature: Optional signature line (e.g., "int func(int a, int b)").
        description: Optional description text.
        widget: Optional widget to get palette colors from.
        
    Returns:
        HTML string for use with QToolTip.showText().
    """
    # Get colors from palette for theme compatibility
    app = QApplication.instance()
    if widget is not None:
        palette = widget.palette()
    elif app is not None:
        palette = app.palette()
    else:
        # Create default palette as fallback
        palette = QPalette()
    
    # Extract colors
    text_color = palette.color(QPalette.ColorRole.ToolTipText).name()
    bg_color = palette.color(QPalette.ColorRole.ToolTipBase).name()
    
    # Calculate readable colors based on background luminance
    bg = QColor(bg_color)
    is_dark_theme = _get_luminance(bg) < 0.5
    
    if is_dark_theme:
        # Dark theme colors (VS Code Dark+)
        keyword_color = "#569CD6"  # Blue for keywords
        type_color = "#4EC9B0"     # Cyan for types
        param_color = "#9CDCFE"    # Light blue for parameters
        comment_color = "#6A9955"  # Green for descriptions
    else:
        # Light theme colors (VS Code Light+)
        keyword_color = "#0000FF"  # Blue for keywords
        type_color = "#267F99"     # Teal for types
        param_color = "#001080"    # Dark blue for parameters
        comment_color = "#008000"  # Green for descriptions
    
    # Build HTML content
    parts = []
    
    # Title with keyword styling
    parts.append(f'<span style="color: {keyword_color}; font-weight: bold;">{title}</span>')
    
    # Signature with syntax highlighting
    if signature:
        parts.append(f'<br><code style="color: {type_color}; font-family: monospace;">{signature}</code>')
    
    # Description
    if description:
        parts.append(f'<br><br><span style="color: {comment_color};">{description}</span>')
    
    content = "".join(parts)
    
    # Wrap in styled container
    # Using a monospace font for code parts ensures alignment
    return f'''<div style="
        font-family: 'Segoe UI', 'SF Pro Text', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
        line-height: 1.4;
        color: {text_color};
        max-width: 500px;
        white-space: pre-wrap;
        word-wrap: break-word;
    ">{content}</div>'''


def _get_luminance(color: QColor) -> float:
    """Calculate relative luminance of a color.
    
    Uses the WCAG formula for relative luminance.
    
    Args:
        color: The color to calculate luminance for.
        
    Returns:
        Luminance value between 0 (black) and 1 (white).
    """
    def adjust(c: float) -> float:
        c = c / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4
    
    r = adjust(color.red())
    g = adjust(color.green())
    b = adjust(color.blue())
    
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def apply_tooltip_style_to_app(app: QApplication | None = None):
    """Apply VS Code-like tooltip styling to the application.
    
    Should be called once during application initialization to ensure
    all tooltips have consistent, readable styling.
    
    Args:
        app: The QApplication instance. If None, uses current instance.
    """
    if app is None:
        app = QApplication.instance()
    
    if app is None:
        return
    
    # Get current stylesheet and append tooltip styling
    current_style = app.styleSheet() or ""
    tooltip_style = get_tooltip_stylesheet()
    
    # Only add if not already present
    if "QToolTip" not in current_style:
        app.setStyleSheet(current_style + "\n" + tooltip_style)


def get_line_number_font(base_font: QFont) -> QFont:
    """Get a slightly smaller font for line numbers.
    
    VS Code uses a slightly smaller, lighter font for line numbers
    to reduce visual clutter.
    
    Args:
        base_font: The main editor font.
        
    Returns:
        A modified font suitable for line numbers.
    """
    line_num_font = QFont(base_font)
    
    # Slightly smaller than main font
    current_size = base_font.pointSize()
    line_num_font.setPointSize(max(8, current_size - 1))
    
    return line_num_font

