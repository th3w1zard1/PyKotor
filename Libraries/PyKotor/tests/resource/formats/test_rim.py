from __future__ import annotations

import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH: pathlib.Path = pathlib.Path(__file__).resolve()
PYKOTOR_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[4].joinpath("src")
UTILITY_PATH: pathlib.Path = THIS_SCRIPT_PATH.parents[6].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.resource.formats.rim import RIM, RIMBinaryReader, read_rim, write_rim
from pykotor.resource.type import ResourceType

# Inlined test.rim binary content
BINARY_TEST_DATA = b'RIM V1.0\x00\x00\x00\x00\x03\x00\x00\x00x\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\xd8\x00\x00\x00\x03\x00\x00\x002\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x01\x00\x00\x00\xdb\x00\x00\x00\x03\x00\x00\x003\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x02\x00\x00\x00\xde\x00\x00\x00\x03\x00\x00\x00abcdefghi'

# Inlined test_corrupted.rim binary content
CORRUPT_BINARY_TEST_DATA = b'RIM V1.0\x00\x00\x00\x00dgfgdfgfddg\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\x00\x00\xd8\x00\x00\x00\x03\x00\x00\x002\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x01\x00\x00\x00\xdb\x00\x00\x00\x03\x00\x00\x003\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x02\x00\x00\x00\xde\x00\x00\x00\x03\x00\x00\x00abcdefghi'

DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"


class TestRIM(unittest.TestCase):
    def test_binary_io(self):
        rim: RIM = RIMBinaryReader(BINARY_TEST_DATA).load()
        self.validate_io(rim)

        data: bytearray = bytearray()
        write_rim(rim, data)
        rim = read_rim(data)
        self.validate_io(rim)

    def test_file_io(self):
        """Test reading from a temporary file to ensure file-based reading still works."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.rim', delete=False) as tmp:
            tmp.write(BINARY_TEST_DATA)
            tmp_path = tmp.name

        try:
            rim: RIM = RIMBinaryReader(tmp_path).load()
            self.validate_io(rim)
        finally:
            os.unlink(tmp_path)

    def validate_io(
        self,
        rim: RIM,
    ):
        assert len(rim) == 3, f"{len(rim)!r} != 3"
        assert rim.get("1", ResourceType.TXT) == b"abc", f"{rim.get('1', ResourceType.TXT)!r} != b'abc'"
        assert rim.get("2", ResourceType.TXT) == b"def", f"{rim.get('2', ResourceType.TXT)!r} != b'def'"
        assert rim.get("3", ResourceType.TXT) == b"ghi", f"{rim.get('3', ResourceType.TXT)!r} != b'ghi'"

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_rim, ".")
        else:
            self.assertRaises(IsADirectoryError, read_rim, ".")
        self.assertRaises(FileNotFoundError, read_rim, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_rim, CORRUPT_BINARY_TEST_DATA)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_rim, RIM(), ".", ResourceType.RIM)
        else:
            self.assertRaises(IsADirectoryError, write_rim, RIM(), ".", ResourceType.RIM)
        self.assertRaises(ValueError, write_rim, RIM(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
