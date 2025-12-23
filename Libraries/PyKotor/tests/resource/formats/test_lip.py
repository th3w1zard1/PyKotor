from __future__ import annotations

import os
import pathlib
import sys
import unittest
from unittest import TestCase

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

from pykotor.resource.formats.lip import LIP, LIPBinaryReader, LIPShape, LIPXMLReader, detect_lip, read_lip, write_lip

from pykotor.resource.type import ResourceType

# Inlined test.lip binary content
BINARY_TEST_DATA = b'LIP V1.0\x00\x00\xc0?\x03\x00\x00\x00\x00\x00\x00\x00\x00Y\x17G?\x05\x00\x00\xa0?\n'

# Inlined test.lip.xml content
XML_TEST_DATA = """<lip duration="1.50">
  <keyframe time="0.0" shape="0" />
  <keyframe time="0.7777" shape="5" />
  <keyframe time="1.25" shape="10" />
</lip>"""

# Inlined test_corrupted.lip binary content
CORRUPT_BINARY_TEST_DATA = b'LIP V1.0345345\x00\x00\x00\x00\x00\x00\x00Y\x17G?\x05\x00\x00\xa0?\n'

# Inlined test_corrupted.lip.xml content
CORRUPT_XML_TEST_DATA = """<lip duration="1.50">
  <keyframe time="0.0" shape="0" />
  <keyframe time="0.7777" shape="5" />
  <keyframe time="1.25" shape="10" /
</lip>"""

DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"


class TestLIP(TestCase):
    def test_binary_io(self):
        assert detect_lip(BINARY_TEST_DATA) == ResourceType.LIP

        lip: LIP = LIPBinaryReader(BINARY_TEST_DATA).load()
        self.validate_io(lip)

        data = bytearray()
        write_lip(lip, data, ResourceType.LIP)
        lip = read_lip(data)
        self.validate_io(lip)

    def test_file_io(self):
        """Test reading from a temporary file to ensure file-based reading still works."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.lip', delete=False) as tmp:
            tmp.write(BINARY_TEST_DATA)
            tmp_path = tmp.name

        try:
            assert detect_lip(tmp_path) == ResourceType.LIP
            lip: LIP = LIPBinaryReader(tmp_path).load()
            self.validate_io(lip)
        finally:
            os.unlink(tmp_path)

    def test_xml_io(self):
        assert detect_lip(XML_TEST_DATA.encode('utf-8')) == ResourceType.LIP_XML

        lip: LIP = LIPXMLReader(XML_TEST_DATA.encode('utf-8')).load()
        self.validate_io(lip)

        data = bytearray()
        write_lip(lip, data, ResourceType.LIP_XML)
        lip = read_lip(data)
        self.validate_io(lip)

    def validate_io(
        self,
        lip: LIP,
    ):
        self.assertAlmostEqual(lip.length, 1.50, 3)
        assert lip.get(0).shape == LIPShape.NEUTRAL, f"Expected {LIPShape.NEUTRAL!r} but got {lip.get(0).shape!r}"
        assert lip.get(1).shape == LIPShape.OOH, f"Expected {LIPShape.OOH!r} but got {lip.get(1).shape!r}"
        assert lip.get(2).shape == LIPShape.TH, f"Expected {LIPShape.TH!r} but got {lip.get(2).shape!r}"
        self.assertAlmostEqual(0.0, lip.get(0).time, 4, f"Expected 0.0 but got {lip.get(0).time}")
        self.assertAlmostEqual(0.7777, lip.get(1).time, 4, f"Expected 0.7777 but got {lip.get(1).time}")
        self.assertAlmostEqual(1.25, lip.get(2).time, 4, f"Expected 1.25 but got {lip.get(2).time}")

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_lip, ".")
        else:
            self.assertRaises(IsADirectoryError, read_lip, ".")
        self.assertRaises(FileNotFoundError, read_lip, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_lip, CORRUPT_BINARY_TEST_DATA)
        self.assertRaises(ValueError, read_lip, CORRUPT_XML_TEST_DATA.encode('utf-8'))

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_lip, LIP(), ".", ResourceType.LIP)
        else:
            self.assertRaises(IsADirectoryError, write_lip, LIP(), ".", ResourceType.LIP)
        self.assertRaises(ValueError, write_lip, LIP(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
