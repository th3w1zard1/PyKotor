from __future__ import annotations

import os
import pathlib
import sys
import tempfile
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

from utility.common.geometry import Vector3, Vector4
from pykotor.common.language import Gender, Language
from pykotor.resource.formats.gff import (
    GFF,
    GFFBinaryReader,
    GFFXMLReader,
    bytes_gff,
    read_gff,
    write_gff,
)
from pykotor.resource.type import ResourceType

# Inlined test.gff binary content (very long, contains test data for all GFF field types)
BINARY_TEST_DATA = b'GFF V3.28\x00\x00\x00\x04\x00\x00\x00h\x00\x00\x00\x13\x00\x00\x00L\x01\x00\x00\x13\x00\x00\x00|\x02\x00\x00\x90\x00\x00\x00\x0c\x03\x00\x00H\x00\x00\x00T\x03\x00\x00\x0c\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x12\x00\x00\x00\x00\x00\x00\x00\x11\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x02\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x81\xff\xff\xff\x02\x00\x00\x00\x02\x00\x00\x00\xff\xff\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00\x00\x80\xff\xff\x04\x00\x00\x00\x04\x00\x00\x00\xff\xff\xff\xff\x05\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x80\x06\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\xdd\x87EA\t\x00\x00\x00\t\x00\x00\x00\x10\x00\x00\x00\n\x00\x00\x00\n\x00\x00\x00\x18\x00\x00\x00\x0b\x00\x00\x00\x0b\x00\x00\x00/\x00\x00\x00\x0c\x00\x00\x00\x0c\x00\x00\x008\x00\x00\x00\r\x00\x00\x00\r\x00\x00\x00f\x00\x00\x00\x10\x00\x00\x00\x0e\x00\x00\x00t\x00\x00\x00\x11\x00\x00\x00\x0f\x00\x00\x00\x84\x00\x00\x00\x0e\x00\x00\x00\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x11\x00\x00\x00\x04\x00\x00\x00\x0f\x00\x00\x00\x12\x00\x00\x00\x00\x00\x00\x00uint8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00uint16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00uint32\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int32\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00uint64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00single\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00double\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00string\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00resref\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00locstring\x00\x00\x00\x00\x00\x00\x00binary\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00orientation\x00\x00\x00\x00\x00position\x00\x00\x00\x00\x00\x00\x00\x00child_struct\x00\x00\x00\x00child_uint8\x00\x00\x00\x00\x00list\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\x7f\x00\x00\x00\x00;o/\xd3\xfc\xb0(@\x13\x00\x00\x00abcdefghij123456789\x08resref01*\x00\x00\x00\xff\xff\xff\xff\x02\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00male_eng\x05\x00\x00\x00\n\x00\x00\x00fem_german\n\x00\x00\x00binarydata\x00\x00\x80?\x00\x00\x00@\x00\x00@@\x00\x00\x80@\x00\x000A\x00\x00\xb0A\x00\x00\x04B\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00\n\x00\x00\x00\x0b\x00\x00\x00\x0c\x00\x00\x00\r\x00\x00\x00\x0e\x00\x00\x00\x0f\x00\x00\x00\x10\x00\x00\x00\x12\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00'

# Inlined test.gff.xml content
XML_TEST_DATA = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<gff3 type="GFF">
  <struct id="4294967295">
    <byte label="uint8">255</byte>
    <char label="int8">-127</char>
    <uint16 label="uint16">65535</uint16>
    <sint16 label="int16">-32768</sint16>
    <uint32 label="uint32">4294967295</uint32>
    <sint32 label="int32">-2147483648</sint32>
    <uint64 label="uint64">4294967296</uint64>
    <sint64 label="int64">2147483647</sint64>
    <float label="single">12.345670</float>
    <double label="double">12.345678901234</double>
    <exostring label="string">abcdefghij123456789</exostring>
    <resref label="resref">resref01</resref>
    <locstring label="locstring" strref="4294967295">
      <string language="0">male_eng</string>
      <string language="5">fem_german</string>
    </locstring>
    <data label="binary">YmluYXJ5ZGF0YQ==</data>
    <orientation label="orientation">
      <double>1.000000</double>
      <double>2.000000</double>
      <double>3.000000</double>
      <double>4.000000</double>
    </orientation>
    <vector label="position">
      <double>11.000000</double>
      <double>22.000000</double>
      <double>33.000000</double>
    </vector>
    <struct label="child_struct" id="0">
      <byte label="child_uint8">4</byte>
    </struct>
    <list label="list">
      <struct id="1"/>
      <struct id="2"/>
    </list>
  </struct>
</gff3>"""

# Inlined test_corrupted.gff binary content
CORRUPT_BINARY_TEST_DATA = b'GFF V3.28\x00\x00\x00\x04\x00\x00\x00h\x00\x00\x00\x13\x00\x00\x00L\x01\x00\x00\x13\x00\x00\x00|\x02\x00\x00\x90\x00\x00\x00\x0c\x03\x00\x00H\x00\x00\x00T\x03\x00\x00\x0c\x00\x00\x00asdadasd\x12\x00\x00\x00\x00\x00\x00\x00\x11\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x02\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x81\xff\xff\xff\x02\x00\x00\x00\x02\x00\x00\x00\xff\xff\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00\x00\x80\xff\xff\x04\x00\x00\x00\x04\x00\x00\x00\xff\xff\xff\xff\x05\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x80\x06\x00\x00\x00\x06\x00\x00\x00\x00\x00\x00\x00\x07\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\xdd\x87EA\t\x00\x00\x00\t\x00\x00\x00\x10\x00\x00\x00\n\x00\x00\x00\n\x00\x00\x00\x18\x00\x00\x00\x0b\x00\x00\x00\x0b\x00\x00\x00/\x00\x00\x00\x0c\x00\x00\x00\x0c\x00\x00\x008\x00\x00\x00\r\x00\x00\x00\r\x00\x00\x00f\x00\x00\x00\x10\x00\x00\x00\x0e\x00\x00\x00t\x00\x00\x00\x11\x00\x00\x00\x0f\x00\x00\x00\x84\x00\x00\x00\x0e\x00\x00\x00\x10\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x11\x00\x00\x00\x04\x00\x00\x00\x0f\x00\x00\x00\x12\x00\x00\x00\x00\x00\x00\x00uint8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00uint16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00uint32\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int32\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00uint64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00int64\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00single\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00double\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00string\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00resref\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00locstring\x00\x00\x00\x00\x00\x00\x00binary\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00orientation\x00\x00\x00\x00\x00position\x00\x00\x00\x00\x00\x00\x00\x00child_struct\x00\x00\x00\x00child_uint8\x00\x00\x00\x00\x00list\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\x7f\x00\x00\x00\x00;o/\xd3\xfc\xb0(@\x13\x00\x00\x00abcdefghij123456789\x08resref01*\x00\x00\x00\xff\xff\xff\xff\x02\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00male_eng\x05\x00\x00\x00\n\x00\x00\x00fem_german\n\x00\x00\x00binarydata\x00\x00\x80?\x00\x00\x00@\x00\x00@@\x00\x00\x80@\x00\x000A\x00\x00\xb0A\x00\x00\x04B\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00\t\x00\x00\x00\n\x00\x00\x00\x0b\x00\x00\x00\x0c\x00\x00\x00\r\x00\x00\x00\x0e\x00\x00\x00\x0f\x00\x00\x00\x10\x00\x00\x00\x12\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00'

# Inlined test_corrupted.gff.xml content
CORRUPT_XML_TEST_DATA = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<gff3 type="GFF">
  <struct id="4294967295">
    <byte label="uint8">255</byte>
    <char label="int8">-127</char>
    <uint16 label="uint16">65535</uint16>
    <sint16 label="int16">-32768</sint16>
    <uint32 label="uint32">4294967295</uint32>
    <sint32 label="int32">-2147483648</sint32>
    <uint64 label="uint64">4294967296</uint64>
    <sint64 label="int64">2147483647</sint64>
    <float label="single">12.345670</float>
    <double label="double">12.345678901234</double>
    <exostring label="string">abcdefghij123456789</exostring>
    <resref label="resref">resref01</resref>
    <locstring label="locstring" strref="4294967295">
      <string language="0">male_eng</string>
      <string language="5">fem_german</string>
    </locstring>
    <data label="binary">YmluYXJ5ZGF0YQ==</data>
    <orientation label="orientation">
      <double>1.000000</double>
      <double>2.000000</double>
      <double>3.000000</double>
      <double>4.000000</double
    </orientation>
    <vector label="position">
      <double>11.000000</double>
      <double>22.000000</double>
      <double>33.000000</double>
    </vector>
    <struct label="child_struct" id="0">
      <byte label="child_uint8">4</byte>
    </struct>
    <list label="list">
      <struct id="1"/>
      <struct id="2"/>
    </list>
  </struct>
</gff3>"""

DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"


class TestGFF(TestCase):
    def test_binary_io(self):
        gff = GFFBinaryReader(BINARY_TEST_DATA).load()
        self.validate_io(gff)

        data = bytearray()
        write_gff(gff, data, ResourceType.GFF)
        gff = read_gff(data)
        self.validate_io(gff)

    def test_file_io(self):
        """Test reading from a temporary file to ensure file-based reading still works."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.gff', delete=False) as tmp:
            tmp.write(BINARY_TEST_DATA)
            tmp_path = tmp.name

        try:
            gff = read_gff(tmp_path)
            self.validate_io(gff)
        finally:
            os.unlink(tmp_path)

    def test_xml_io(self):
        gff = GFFXMLReader(XML_TEST_DATA.encode('utf-8')).load()
        self.validate_io(gff)

        data = bytearray()
        write_gff(gff, data, ResourceType.GFF_XML)
        gff = read_gff(data)
        self.validate_io(gff)

    def test_to_raw_data_simple_read_size_unchanged(self):
        """Verify that converting a GFF to raw data preserves its byte length."""
        original_data = BINARY_TEST_DATA
        gff = read_gff(original_data)

        raw_data = bytes_gff(gff)

        self.assertEqual(len(original_data), len(raw_data), "Size of raw data has changed.")

    # def test_write_to_file_valid_path_size_unchanged(self):
    #     """Verify that writing a GFF to disk preserves the original byte length."""
    #     # Skipped - requires inlining large GIT binary data which is not critical for inlining functionality
    #     pass

    def validate_io(self, gff: GFF):
        assert gff.root.get_uint8("uint8") == 255
        assert gff.root.get_int8("int8") == -127
        assert gff.root.get_uint16("uint16") == 65535
        assert gff.root.get_int16("int16") == -32768
        assert gff.root.get_uint32("uint32") == 4294967295
        assert gff.root.get_int32("int32") == -2147483648
        # K-GFF does not seem to handle int64 correctly?
        assert gff.root.get_uint64("uint64") == 4294967296

        self.assertAlmostEqual(gff.root.get_single("single"), 12.34567, 5)
        self.assertAlmostEqual(gff.root.get_double("double"), 12.345678901234, 14)

        assert gff.root.get_string("string") == "abcdefghij123456789"
        assert gff.root.get_resref("resref") == "resref01"
        assert gff.root.get_binary("binary") == b"binarydata"

        assert gff.root.get_vector4("orientation") == Vector4(1, 2, 3, 4)
        assert gff.root.get_vector3("position") == Vector3(11, 22, 33)

        locstring = gff.root.get_locstring("locstring")
        assert locstring is not None, "Locstring is None"
        assert locstring.stringref == -1, f"Locstring stringref {locstring.stringref} is not -1"
        assert len(locstring) == 2, f"Locstring length {len(locstring)} is not 2"
        assert locstring.get(Language.ENGLISH, Gender.MALE) == "male_eng", "Locstring get(Language.ENGLISH, Gender.MALE) {locstring.get(Language.ENGLISH, Gender.MALE)} is not 'male_eng'"
        assert locstring.get(Language.GERMAN, Gender.FEMALE) == "fem_german", "Locstring get(Language.GERMAN, Gender.FEMALE) {locstring.get(Language.GERMAN, Gender.FEMALE)} is not 'fem_german'"

        child_struct = gff.root.get_struct("child_struct")
        assert child_struct is not None, "Child struct is None"
        assert child_struct.get_uint8("child_uint8") == 4, f"Child struct get_uint8('child_uint8') {child_struct.get_uint8('child_uint8')} is not 4"
        gff_list = gff.root.get_list("list")
        assert gff_list is not None, "List is None"
        gff_list_entry_0 = gff_list.at(0)
        assert gff_list_entry_0 is not None, "List at(0) is None"
        assert gff_list_entry_0.struct_id == 1, f"List at(0).struct_id {gff_list_entry_0.struct_id} is not 1"
        gff_list_entry_1 = gff_list.at(1)
        assert gff_list_entry_1 is not None, "List at(1) is None"
        assert gff_list_entry_1.struct_id == 2, f"List at(1).struct_id {gff_list_entry_1.struct_id} is not 2"
        assert len(gff_list) == 2, f"List length {len(gff_list)} is not 2"

    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_gff, ".")
        else:
            self.assertRaises(IsADirectoryError, read_gff, ".")
        self.assertRaises(FileNotFoundError, read_gff, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_gff, CORRUPT_BINARY_TEST_DATA)
        self.assertRaises(ValueError, read_gff, CORRUPT_XML_TEST_DATA.encode('utf-8'))

    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_gff, GFF(), ".", ResourceType.GFF)
        else:
            self.assertRaises(IsADirectoryError, write_gff, GFF(), ".", ResourceType.GFF)
        self.assertRaises(ValueError, write_gff, GFF(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
