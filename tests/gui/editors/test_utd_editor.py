import os
import pathlib
import sys
import unittest
from unittest import TestCase

try:
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QApplication
except (ImportError, ModuleNotFoundError):
    QTest, QApplication = None, None

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    toolset_path = pathlib.Path(__file__).parents[3] / "toolset"
    if pykotor_path.joinpath("__init__.py").exists() or toolset_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))


K1_PATH = os.environ.get("K1_PATH")


@unittest.skipIf(
    not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").exists(),
    "K1_PATH environment variable is not set or not found on disk.",
)
@unittest.skipIf(
    not QTest or not QApplication,
    "PyQt5 is required, please run pip install -r requirements.txt before running this test.",
)
class UTDEditorTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from toolset.data.installation import HTInstallation
        # Make sure to configure this environment path before testing!
        cls.INSTALLATION = HTInstallation(K1_PATH, "", False, None)

    def setUp(self) -> None:
        from toolset.gui.editors.utd import UTDEditor
        self.app = QApplication([])
        self.ui = UTDEditor(None, self.INSTALLATION)

    def tearDown(self) -> None:
        self.app.deleteLater()

    def test_placeholder(self):
        ...


if __name__ == "__main__":
    unittest.main()
