from __future__ import annotations

from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import QApplication, QWidget


def _blend(a: QColor, b: QColor, t: float) -> QColor:
    """Blend two colors.

    Args:
    ----
        a: First color
        b: Second color
        t: Blend factor in [0..1] where 0 = a, 1 = b
    """
    t = max(0.0, min(1.0, t))
    return QColor(
        int(a.red() * (1.0 - t) + b.red() * t),
        int(a.green() * (1.0 - t) + b.green() * t),
        int(a.blue() * (1.0 - t) + b.blue() * t),
        int(a.alpha() * (1.0 - t) + b.alpha() * t),
    )


def apply_locstring_background(
    widget: QWidget,
    *,
    from_tlk: bool,
):
    """Apply a palette-driven background to indicate TLK-backed locstrings.

    This avoids hardcoded colors (e.g. white/yellow) that can become unreadable
    in dark themes.
    """
    app_pal = QApplication.palette(widget)
    pal = QPalette(app_pal)

    if from_tlk:
        base = app_pal.color(QPalette.ColorRole.Base)
        highlight = app_pal.color(QPalette.ColorRole.Highlight)
        pal.setColor(QPalette.ColorRole.Base, _blend(base, highlight, 0.18))

    widget.setPalette(pal)


