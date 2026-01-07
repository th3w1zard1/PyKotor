from __future__ import annotations

import pytest

from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.about import About
from toolset.gui.windows.indoor_builder import IndoorMapBuilder
from toolset.gui.windows.kotordiff import KotorDiffWindow


def test_indoor_builder_action_exit_accepts_qaction_triggered_bool(qtbot, installation: HTInstallation) -> None:
    """Regression: QAction.triggered(bool) must not crash when connected to QWidget.close()."""
    builder = IndoorMapBuilder(None, installation)
    qtbot.addWidget(builder)
    builder.show()

    # QAction.trigger() emits triggered(bool) → our connection must drop args.
    builder.ui.actionExit.trigger()

    # Process events; if the slot signature is wrong, this raises TypeError and the test fails.
    qtbot.wait(10)


def test_about_dialog_close_button_accepts_clicked_bool(qtbot) -> None:
    """Regression: QPushButton.clicked(bool) must not crash when connected to QDialog.close()."""
    dlg = About(None)
    qtbot.addWidget(dlg)
    dlg.show()

    dlg.ui.closeButton.click()
    qtbot.wait(10)


def test_kotordiff_close_button_accepts_clicked_bool(qtbot) -> None:
    """Regression: QPushButton.clicked(bool) must not crash when connected to QWidget.close()."""
    win = KotorDiffWindow(None, installations=None, active_installation=None)
    qtbot.addWidget(win)
    win.show()

    win.close_btn.click()
    qtbot.wait(10)

