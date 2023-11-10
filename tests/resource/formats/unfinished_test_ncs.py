import os
from unittest import TestCase

from pykotor.common.stream import BinaryReader

from pykotor.resource.formats.ncs import NCSBinaryReader, NCS
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, write_ncs, read_ncs
from pykotor.tools.path import Path

BINARY_TEST_FILE = "tests/files/test.ncs"


class TestNCS(TestCase):
    def test_binary_io(self):
        ncs = NCSBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(ncs)

        user_profile_path = os.environ.get("USERPROFILE")
        file_path = Path(user_profile_path, "Documents", "ext", "output.ncs")

        write_ncs(ncs, file_path)
        data = bytes_ncs(ncs)
        ncs = read_ncs(data)
        self.validate_io(ncs)

    def validate_io(self, ncs: NCS):
        self.assertEqual(8, len(ncs.instructions))

        self.assertEqual(BinaryReader.load_file(BINARY_TEST_FILE), bytes_ncs(ncs))
