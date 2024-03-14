from __future__ import annotations

import cProfile
import os
import pathlib
import sys
import pytest

from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

def fix_sys_and_cwd_path(repo_root: pathlib.Path):
    """Fixes sys.path and current working directory for PyKotor.

    This function will determine whether they have the source files downloaded for pykotor in the expected directory. If they do, we
    insert the source path to pykotor to the beginning of sys.path so it'll have priority over pip's pykotor package if that is installed.
    If the toolset dir exists, change directory to that of the toolset. Allows users to do things like `python -m toolset`
    This function should never be used in frozen code.
    This function also ensures a user can run toolset/__main__.py directly.

    Processing Logic:
    ----------------
        - Checks if PyKotor package exists in parent directory of calling file.
        - If exists, removes parent directory from sys.path and adds to front.
        - Also checks for toolset package and changes cwd to that directory if exists.
        - This ensures packages and scripts can be located correctly on import.
    """
    def update_sys_path(path: pathlib.Path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    pykotor_path = repo_root / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)
    pykotor_gl_path = repo_root / "Libraries" / "PyKotorGL" / "src" / "pykotor"
    if pykotor_gl_path.exists():
        update_sys_path(pykotor_gl_path.parent)
    utility_path = repo_root / "Libraries" / "Utility" / "src"
    if utility_path.exists():
        update_sys_path(utility_path)
    toolset_path = repo_root / "Tools" / "HolocronToolset" / "src" / "toolset"
    if toolset_path.exists() and toolset_path.is_dir():
        update_sys_path(toolset_path.parent)
        #os.chdir(toolset_path)

repo_root = pathlib.Path(__file__).parents[4].resolve()
fix_sys_and_cwd_path(repo_root)

from toolset.gui.dialogs.save.ask_restype import ResourceTypeDialog

from pykotor.resource.type import ResourceType
from utility.system.path import Path

@pytest.fixture(scope='module')
def qt_app():
    app = QApplication([])
    yield app
    app.exit()

@pytest.fixture
def resource_dialog(qt_app: QApplication):
    resource_types_to_test = [ResourceType.BMP, ResourceType.TXT]
    dialog = ResourceTypeDialog(resource_types_to_test)
    return dialog

def test_dialog_dimensions(resource_dialog: ResourceTypeDialog):
    resource_dialog.show()  # Show the dialog to test its dimensions
    expected_width = 400
    expected_height = 200
    assert resource_dialog.width() == expected_width
    assert resource_dialog.height() == expected_height

def test_control_visibility(resource_dialog):
    resource_dialog.show()
    assert resource_dialog.combo_box.isVisible()
    assert resource_dialog.combo_box.count() == 2  # Check the correct number of options is available

def test_correct_options(resource_dialog: ResourceTypeDialog):
    resource_dialog.show()
    expected_options = ['BMP - Images (binary)', 'TXT - Text Files (plaintext)']
    actual_options = [resource_dialog.combo_box.itemText(i) for i in range(resource_dialog.combo_box.count())]
    assert actual_options == expected_options

# To run these tests, use the command:
# pytest path_to_test_file.py
if __name__ == "__main__":
    profiler: cProfile.Profile = True  # type: ignore[reportAssignmentType, assignment]
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    result: int | pytest.ExitCode = pytest.main(
        [
            __file__,
            "-v",
            "-ra",
            "-o",
            "log_cli=true",
            "--capture=no",
            "--junitxml=pytest_report.xml",
            "--html=pytest_report.html",
            "--self-contained-html",
            "--tb=no",
            #"-n",
            #"auto"
        ],
    )

    if profiler:
        profiler.disable()
        profiler_output_file = Path.pathify("restype_dialog_pytest.pstat")
        profiler_output_file_str = str(profiler_output_file)
        profiler.dump_stats(profiler_output_file_str)
        # Generate reports from the profile stats
        # stats = pstats.Stats(profiler_output_file_str).sort_stats('cumulative')
        # stats.print_stats()

    sys.exit(result)
    # Cleanup temporary directories after use
    #for temp_dir in temp_dirs.values():
    #    temp_dir.cleanup()  # noqa: ERA001