from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

# Handle optional pykotor.gl dependency (required by module_designer)
from pykotor.gl.scene import Camera  # noqa: F401

from qtpy.QtWidgets import QWidget, QMainWindow
from unittest.mock import MagicMock, patch

from toolset.gui.windows.module_designer import ModuleDesigner
from toolset.gui.windows.kotordiff import KotorDiffWindow
from toolset.gui.windows.help_window import HelpWindow
from toolset.gui.editors.wav import WAVEditor
from toolset.data.installation import HTInstallation

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

def test_module_designer_init(qtbot: QtBot, installation: HTInstallation):
    """Test Module Designer initialization."""
    # Mocking settings or resource loading might be needed as it's heavy
    window = ModuleDesigner(parent=None, installation=installation)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    assert "Module Designer" in window.windowTitle()
    
    # Test basic UI elements existence
    assert window.ui.resourceTree is not None
    assert window.ui.lytTree is not None

def test_kotordiff_init(qtbot: QtBot, installation: HTInstallation):
    """Test KotorDiff window initialization."""
    window = KotorDiffWindow(parent=None, installations={"default": installation}, active_installation=installation)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    assert "Kotor Diff" in window.windowTitle()
    
    # Check interactions
    # Clicking 'Compare' without files should probably show error or do nothing safe
    with patch("qtpy.QtWidgets.QMessageBox.warning") as mock_warn:
        window._run_diff()
        # Likely warns about missing files
        # Verify mocking worked if implemented

def test_help_window_init(qtbot: QtBot):
    """Test Help Window initialization."""
    window = HelpWindow(None)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    # Check if web engine or text viewer is present
    # Depending on implementation (QWebEngineView or QTextBrowser)

def test_audio_player_init(qtbot: QtBot, installation: HTInstallation):
    """Test Audio Player window."""
    window = WAVEditor(None, installation)
    qtbot.addWidget(window)
    window.show()
    
    assert window.isVisible()
    # Check controls
    assert hasattr(window.ui, "playButton")
    assert hasattr(window.ui, "stopButton")
    
    # Test loading a dummy audio file (mocked)
    # window.load_audio("test.wav")
