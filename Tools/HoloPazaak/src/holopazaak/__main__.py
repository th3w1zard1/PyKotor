"""Main entry point for HoloPazaak.

This module provides the entry point for running HoloPazaak as a module:
    python -m holopazaak

The application uses qtpy for Qt abstraction, targeting PyQt6 by default.
"""
from __future__ import annotations

import sys


def main() -> int:
    """Main entry point for HoloPazaak."""
    # Import Qt application
    from qtpy.QtWidgets import QApplication
    
    from holopazaak.ui.game_window import PazaakWindow
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("HoloPazaak")
    app.setOrganizationName("PyKotor")
    
    # Create and show main window
    window = PazaakWindow()
    window.show()
    
    # Run event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
