from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[6].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.resource.formats.vis import VIS, VISAsciiReader, read_vis, write_vis
from pykotor.resource.type import ResourceType

# Inlined test.vis content
ASCII_TEST_DATA = """room_01 3
  room_02
     room_03
  room_04
room_02 1
     room_01
room_03 2
room_01
  room_04
room_04 2
  room_03
 room_01"""

# Inlined test_corrupted.vis content
CORRUPT_ASCII_TEST_DATA = """room_01 77
  room_02
     room_03
  room_04
room_02 1
     room_01
room_03 2
room_01
  room_04
room_04 2
  room_03
 room_01"""

DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"


class TestVIS(TestCase):
    def test_binary_io(self):
        vis = VISAsciiReader(ASCII_TEST_DATA.encode('utf-8')).load()
        self.validate_io(vis)

        data = bytearray()
        write_vis(vis, data, ResourceType.VIS)
        vis = read_vis(data)
        self.validate_io(vis)

    def test_file_io(self):
        """Test reading from a temporary file to ensure file-based reading still works."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.vis', delete=False, encoding='utf-8') as tmp:
            tmp.write(ASCII_TEST_DATA)
            tmp_path = tmp.name

        try:
            vis = VISAsciiReader(tmp_path).load()
            self.validate_io(vis)
        finally:
            os.unlink(tmp_path)

    def validate_io(self, vis: VIS):
        assert vis.get_visible("room_01", "room_02")
        assert vis.get_visible("room_01", "room_03")
        assert vis.get_visible("room_01", "room_04")

        assert vis.get_visible("room_02", "room_01")
        assert not vis.get_visible("room_02", "room_03")
        assert not vis.get_visible("room_02", "room_04")

        assert vis.get_visible("room_03", "room_01")
        assert vis.get_visible("room_03", "room_04")
        assert not vis.get_visible("room_03", "room_02")

        assert vis.get_visible("room_04", "room_01")
        assert vis.get_visible("room_04", "room_03")
        assert not vis.get_visible("room_04", "room_02")

    def test_read_raises(self):
        # sourcery skip: no-conditionals-in-tests
        if os.name == "nt":
            self.assertRaises(PermissionError, read_vis, ".")
        else:
            self.assertRaises(IsADirectoryError, read_vis, ".")
        self.assertRaises(FileNotFoundError, read_vis, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_vis, CORRUPT_ASCII_TEST_DATA.encode('utf-8'))

    def test_write_raises(self):
        # sourcery skip: no-conditionals-in-tests
        if os.name == "nt":
            self.assertRaises(PermissionError, write_vis, VIS(), ".", ResourceType.VIS)
        else:
            self.assertRaises(IsADirectoryError, write_vis, VIS(), ".", ResourceType.VIS)
        self.assertRaises(ValueError, write_vis, VIS(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
