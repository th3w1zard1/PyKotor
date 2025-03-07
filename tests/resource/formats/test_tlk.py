from __future__ import annotations

import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.language import Language
from pykotor.common.misc import ResRef
from pykotor.resource.formats.tlk import (
    TLK,
    TLKBinaryReader,
    TLKEntry,
    TLKJSONReader,
    TLKXMLReader,
    detect_tlk,
    read_tlk,
    write_tlk,
)
from pykotor.resource.type import ResourceType

BINARY_TEST_FILE = "tests/files/test.tlk"
XML_TEST_FILE = "tests/files/test.tlk.xml"
JSON_TEST_FILE = "tests/files/test.tlk.json"
DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"
CORRUPT_BINARY_TEST_FILE = "tests/files/test_corrupted.tlk"
CORRUPT_XML_TEST_FILE = "tests/files/test_corrupted.tlk.xml"
CORRUPT_JSON_TEST_FILE = "tests/files/test_corrupted.tlk.json"


class TestTLK(unittest.TestCase):
    def test_resize(self):
        tlk: TLK = TLKBinaryReader(BINARY_TEST_FILE).load()
        assert len(tlk) == 3
        tlk.resize(4)
        assert len(tlk) == 4
        assert TLKEntry("qrstuvwxyz", ResRef("")) == tlk[2]
        assert TLKEntry("", ResRef("")) == tlk[3]
        tlk.resize(1)
        assert len(tlk) == 1
        assert TLKEntry("abcdef", ResRef("resref01")) == tlk.get(0)
        assert tlk.get(1) is None

    def test_binary_io(self):
        assert detect_tlk(BINARY_TEST_FILE) == ResourceType.TLK

        tlk: TLK = TLKBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(tlk)

        data = bytearray()
        write_tlk(tlk, data, ResourceType.TLK)
        tlk = read_tlk(data)
        self.validate_io(tlk)

    def test_xml_io(self):
        assert detect_tlk(XML_TEST_FILE) == ResourceType.TLK_XML

        tlk: TLK = TLKXMLReader(XML_TEST_FILE).load()
        self.validate_io(tlk)

        data = bytearray()
        write_tlk(tlk, data, ResourceType.TLK_XML)
        tlk = read_tlk(data)
        self.validate_io(tlk)

    def test_json_io(self):
        assert detect_tlk(JSON_TEST_FILE) == ResourceType.TLK_JSON

        tlk: TLK = TLKJSONReader(JSON_TEST_FILE).load()
        self.validate_io(tlk)

        data = bytearray()
        write_tlk(tlk, data, ResourceType.TLK_JSON)
        tlk = read_tlk(data)
        self.validate_io(tlk)

    def validate_io(self, tlk: TLK):
        assert tlk.language is Language.ENGLISH

        assert TLKEntry("abcdef", ResRef("resref01")) == tlk[0]
        assert TLKEntry("ghijklmnop", ResRef("resref02")) == tlk[1]
        assert TLKEntry("qrstuvwxyz", ResRef("")) == tlk[2]

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_tlk, ".")
        else:
            self.assertRaises(IsADirectoryError, read_tlk, ".")
        self.assertRaises(FileNotFoundError, read_tlk, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_tlk, CORRUPT_BINARY_TEST_FILE)
        self.assertRaises(ValueError, read_tlk, CORRUPT_XML_TEST_FILE)
        self.assertRaises(ValueError, read_tlk, CORRUPT_JSON_TEST_FILE)

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_tlk, TLK(), ".", ResourceType.TLK)
        else:
            self.assertRaises(IsADirectoryError, write_tlk, TLK(), ".", ResourceType.TLK)
        self.assertRaises(ValueError, write_tlk, TLK(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
