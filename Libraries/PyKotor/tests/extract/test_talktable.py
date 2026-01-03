from __future__ import annotations

import pathlib
import sys

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

import unittest

from pykotor.common.language import Language
from pykotor.extract.talktable import TalkTable

# Inlined test.tlk content converted to XML format
TEST_TLK_XML = """<tlk language="0">
  <string id="0" sound="resref01">abcdef</string>
  <string id="1" sound="resref02">ghijklmnop</string>
  <string id="2">qrstuvwxyz</string>
  </tlk>"""


class TestTalkTable(unittest.TestCase):
    def test_size(self):
        import tempfile
        import os
        from pykotor.resource.formats.tlk import read_tlk, write_tlk
        from pykotor.resource.type import ResourceType

        # Convert XML to binary TLK and save to temp file
        tlk = read_tlk(TEST_TLK_XML.encode('utf-8'), file_format=ResourceType.TLK_XML)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.tlk', delete=False) as tmp:
            tmp_path = tmp.name

        write_tlk(tlk, tmp_path, ResourceType.TLK)

        try:
            talktable = TalkTable(tmp_path)
            assert talktable.size() == 3
        finally:
            os.unlink(tmp_path)

    def test_string(self):
        import tempfile
        import os
        from pykotor.resource.formats.tlk import read_tlk, write_tlk
        from pykotor.resource.type import ResourceType

        # Convert XML to binary TLK and save to temp file
        tlk = read_tlk(TEST_TLK_XML.encode('utf-8'), file_format=ResourceType.TLK_XML)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.tlk', delete=False) as tmp:
            tmp_path = tmp.name

        write_tlk(tlk, tmp_path, ResourceType.TLK)

        try:
            talktable = TalkTable(tmp_path)
            assert talktable.string(0) == "abcdef"
            assert talktable.string(1) == "ghijklmnop"
            assert talktable.string(2) == "qrstuvwxyz"
            assert talktable.string(-1) == ""
            assert talktable.string(3) == ""
        finally:
            os.unlink(tmp_path)

    def test_voiceover(self):
        import tempfile
        import os
        from pykotor.resource.formats.tlk import read_tlk, write_tlk
        from pykotor.resource.type import ResourceType

        # Convert XML to binary TLK and save to temp file
        tlk = read_tlk(TEST_TLK_XML.encode('utf-8'), file_format=ResourceType.TLK_XML)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.tlk', delete=False) as tmp:
            tmp_path = tmp.name

        write_tlk(tlk, tmp_path, ResourceType.TLK)

        try:
            talktable = TalkTable(tmp_path)
            assert str(talktable.sound(0)) == "resref01"
            assert str(talktable.sound(1)) == "resref02"
            assert str(talktable.sound(2)) == ""
            assert str(talktable.sound(-1)) == ""
            assert str(talktable.sound(3)) == ""
        finally:
            os.unlink(tmp_path)

    def test_batch(self):
        import tempfile
        import os
        from pykotor.resource.formats.tlk import read_tlk, write_tlk
        from pykotor.resource.type import ResourceType

        # Convert XML to binary TLK and save to temp file
        tlk = read_tlk(TEST_TLK_XML.encode('utf-8'), file_format=ResourceType.TLK_XML)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.tlk', delete=False) as tmp:
            tmp_path = tmp.name

        write_tlk(tlk, tmp_path, ResourceType.TLK)

        try:
            talktable = TalkTable(tmp_path)
            batch = talktable.batch([2, 0, -1, 3])
            assert batch[0] == ("abcdef", "resref01")
            assert batch[2] == ("qrstuvwxyz", "")
            assert batch[-1] == ("", "")
            assert batch[3] == ("", "")
        finally:
            os.unlink(tmp_path)

    def test_language(self):
        import tempfile
        import os
        from pykotor.resource.formats.tlk import read_tlk, write_tlk
        from pykotor.resource.type import ResourceType

        # Convert XML to binary TLK and save to temp file
        tlk = read_tlk(TEST_TLK_XML.encode('utf-8'), file_format=ResourceType.TLK_XML)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.tlk', delete=False) as tmp:
            tmp_path = tmp.name

        write_tlk(tlk, tmp_path, ResourceType.TLK)

        try:
            talktable = TalkTable(tmp_path)
            assert talktable.language() == Language.ENGLISH
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
