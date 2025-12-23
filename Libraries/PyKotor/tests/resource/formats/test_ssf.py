from __future__ import annotations

import os
import pathlib
import sys
import unittest

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

from pykotor.resource.formats.ssf import (
    SSF,
    SSFBinaryReader,
    SSFSound,
    SSFXMLReader,
    read_ssf,
    write_ssf,
)
from pykotor.resource.formats.ssf.ssf_auto import detect_ssf
from pykotor.resource.type import ResourceType

# Inlined test.ssf binary content
BINARY_TEST_DATA = b'SSF V1.1\x0c\x00\x00\x00\xc3\xe0\x01\x00\xc2\xe0\x01\x00\xc1\xe0\x01\x00\xc0\xe0\x01\x00\xbf\xe0\x01\x00\xbe\xe0\x01\x00\xbd\xe0\x01\x00\xbc\xe0\x01\x00\xbb\xe0\x01\x00\xba\xe0\x01\x00\xb9\xe0\x01\x00\xb8\xe0\x01\x00\xb7\xe0\x01\x00\xb6\xe0\x01\x00\xb5\xe0\x01\x00\xb4\xe0\x01\x00\xb3\xe0\x01\x00\xb2\xe0\x01\x00\xb1\xe0\x01\x00\xb0\xe0\x01\x00\xaf\xe0\x01\x00\xae\xe0\x01\x00\xad\xe0\x01\x00\xac\xe0\x01\x00\xab\xe0\x01\x00\xaa\xe0\x01\x00\xa9\xe0\x01\x00\xa8\xe0\x01\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'

# Inlined test.ssf.xml content
XML_TEST_DATA = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<ssf>
  <sound id="0" label="BattleCry1" strref="123075"></sound>
  <sound id="1" label="BattleCry2" strref="123074"></sound>
  <sound id="2" label="BattleCry3" strref="123073"></sound>
  <sound id="3" label="BattleCry4" strref="123072"></sound>
  <sound id="4" label="BattleCry5" strref="123071"></sound>
  <sound id="5" label="BattleCry6" strref="123070"></sound>
  <sound id="6" label="Selected1" strref="123069"></sound>
  <sound id="7" label="Selected2" strref="123068"></sound>
  <sound id="8" label="Selected3" strref="123067"></sound>
  <sound id="9" label="GruntAttack1" strref="123066"></sound>
  <sound id="10" label="GruntAttack2" strref="123065"></sound>
  <sound id="11" label="GruntAttack3" strref="123064"></sound>
  <sound id="12" label="Pain1" strref="123063"></sound>
  <sound id="13" label="Pain2" strref="123062"></sound>
  <sound id="14" label="NearDeath" strref="123061"></sound>
  <sound id="15" label="Death" strref="123060"></sound>
  <sound id="16" label="Critical" strref="123059"></sound>
  <sound id="17" label="WeaponSucks" strref="123058"></sound>
  <sound id="18" label="FoundMine" strref="123057"></sound>
  <sound id="19" label="DisabledMine" strref="123056"></sound>
  <sound id="20" label="Hide" strref="123055"></sound>
  <sound id="21" label="Search" strref="123054"></sound>
  <sound id="22" label="PickLock" strref="123053"></sound>
  <sound id="23" label="CanDo" strref="123052"></sound>
  <sound id="24" label="CantDo" strref="123051"></sound>
  <sound id="25" label="Single" strref="123050"></sound>
  <sound id="26" label="Group" strref="123049"></sound>
  <sound id="27" label="Poisoned" strref="123048"></sound>
  <sound id="28"></sound>
  <sound id="29"></sound>
  <sound id="30"></sound>
  <sound id="31"></sound>
  <sound id="32"></sound>
  <sound id="33"></sound>
  <sound id="34"></sound>
  <sound id="35"></sound>
  <sound id="36"></sound>
  <sound id="37"></sound>
  <sound id="38"></sound>
  <sound id="39"></sound>
</ssf>"""

# Inlined test_corrupted.ssf binary content
CORRUPT_BINARY_TEST_DATA = b'SSF V1.1asdas\xe0\x01\x00\xc2\xe0\x01\x00\xc1\xe0\x01\x00\xc0\xe0\x01\x00\xbf\xe0\x01\x00\xbe\xe0\x01\x00\xbd\xe0\x01\x00\xbc\xe0\x01\x00\xbb\xe0\x01\x00\xba\xe0\x01\x00\xb9\xe0\x01\x00\xb8\xe0\x01\x00\xb7\xe0\x01\x00\xb6\xe0\x01\x00\xb5\xe0\x01\x00\xb4\xe0\x01\x00\xb3\xe0\x01\x00\xb2\xe0\x01\x00\xb1\xe0\x01\x00\xb0\xe0\x01\x00\xaf\xe0\x01\x00\xae\xe0\x01\x00\xad\xe0\x01\x00\xac\xe0\x01\x00\xab\xe0\x01\x00\xaa\xe0\x01\x00\xa9\xe0\x01\x00\xa8\xe0\x01\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff'

# Inlined test_corrupted.ssf.xml content
CORRUPT_XML_TEST_DATA = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<ssf>
  <sound id="0" label="BattleCry1" strref="123075"></sound>
  <sound id="1" label="BattleCry2" strref="123074"></sound>
  <sound id="2" label="BattleCry3" strref="123073"></sound>
  <sound id="3" label="BattleCry4" strref="123072"></sound>
  <sound id="4" label="BattleCry5" strref="123071"></sound>
  <sound id="5" label="BattleCry6" strref="123070"></sound>
  <sound id="6" label="Selected1" strref="123069"></sound>
  <sound id="7" label="Selected2" strref="123068"></sound>
  <sound id="8" label="Selected3" strref="123067"></sound>
  <sound id="9" label="GruntAttack1" strref="123066"></sound>
  <sound id="10" label="GruntAttack2" strref="123065"></sound
  <sound id="11" label="GruntAttack3" strref="123064"></sound>
  <sound id="12" label="Pain1" strref="123063"></sound>
  <sound id="13" label="Pain2" strref="123062"></sound>
  <sound id="14" label="NearDeath" strref="123061"></sound>
  <sound id="15" label="Death" strref="123060"></sound>
  <sound id="16" label="Critical" strref="123059"></sound>
  <sound id="17" label="WeaponSucks" strref="123058"></sound>
  <sound id="18" label="FoundMine" strref="123057"></sound>
  <sound id="19" label="DisabledMine" strref="123056"></sound>
  <sound id="20" label="Hide" strref="123055"></sound>
  <sound id="21" label="Search" strref="123054"></sound>
  <sound id="22" label="PickLock" strref="123053"></sound>
  <sound id="23" label="CanDo" strref="123052"></sound>
  <sound id="24" label="CantDo" strref="123051"></sound>
  <sound id="25" label="Single" strref="123050"></sound>
  <sound id="26" label="Group" strref="123049"></sound>
  <sound id="27" label="Poisoned" strref="123048"></sound>
  <sound id="28"></sound>
  <sound id="29"></sound>
  <sound id="30"></sound>
  <sound id="31"></sound>
  <sound id="32"></sound>
  <sound id="33"></sound>
  <sound id="34"></sound>
  <sound id="35"></sound>
  <sound id="36"></sound>
  <sound id="37"></sound>
  <sound id="38"></sound>
  <sound id="39"></sound>
</ssf>"""

DOES_NOT_EXIST_FILE = "./thisfiledoesnotexist"


class TestSSF(unittest.TestCase):
    def test_binary_io(self):
        assert detect_ssf(BINARY_TEST_DATA) == ResourceType.SSF

        ssf = SSFBinaryReader(BINARY_TEST_DATA).load()
        self.validate_io(ssf)

        data = bytearray()
        write_ssf(ssf, data, ResourceType.SSF)
        ssf = read_ssf(data)
        self.validate_io(ssf)

    def test_xml_io(self):
        assert detect_ssf(XML_TEST_DATA.encode('utf-8')) == ResourceType.SSF_XML

        ssf = SSFXMLReader(XML_TEST_DATA.encode('utf-8')).load()
        self.validate_io(ssf)

        data = bytearray()
        write_ssf(ssf, data, ResourceType.SSF_XML)
        ssf = read_ssf(data)
        self.validate_io(ssf)

    def validate_io(self, ssf: SSF):
        assert ssf.get(SSFSound.BATTLE_CRY_1) == 123075
        assert ssf.get(SSFSound.BATTLE_CRY_2) == 123074
        assert ssf.get(SSFSound.BATTLE_CRY_3) == 123073
        assert ssf.get(SSFSound.BATTLE_CRY_4) == 123072
        assert ssf.get(SSFSound.BATTLE_CRY_5) == 123071
        assert ssf.get(SSFSound.BATTLE_CRY_6) == 123070
        assert ssf.get(SSFSound.SELECT_1) == 123069
        assert ssf.get(SSFSound.SELECT_2) == 123068
        assert ssf.get(SSFSound.SELECT_3) == 123067
        assert ssf.get(SSFSound.ATTACK_GRUNT_1) == 123066
        assert ssf.get(SSFSound.ATTACK_GRUNT_2) == 123065
        assert ssf.get(SSFSound.ATTACK_GRUNT_3) == 123064
        assert ssf.get(SSFSound.PAIN_GRUNT_1) == 123063
        assert ssf.get(SSFSound.PAIN_GRUNT_2) == 123062
        assert ssf.get(SSFSound.LOW_HEALTH) == 123061
        assert ssf.get(SSFSound.DEAD) == 123060
        assert ssf.get(SSFSound.CRITICAL_HIT) == 123059
        assert ssf.get(SSFSound.TARGET_IMMUNE) == 123058
        assert ssf.get(SSFSound.LAY_MINE) == 123057
        assert ssf.get(SSFSound.DISARM_MINE) == 123056
        assert ssf.get(SSFSound.BEGIN_STEALTH) == 123055
        assert ssf.get(SSFSound.BEGIN_SEARCH) == 123054
        assert ssf.get(SSFSound.BEGIN_UNLOCK) == 123053
        assert ssf.get(SSFSound.UNLOCK_FAILED) == 123052
        assert ssf.get(SSFSound.UNLOCK_SUCCESS) == 123051
        assert ssf.get(SSFSound.SEPARATED_FROM_PARTY) == 123050
        assert ssf.get(SSFSound.REJOINED_PARTY) == 123049
        assert ssf.get(SSFSound.POISONED) == 123048

    # sourcery skip: no-conditionals-in-tests
    def test_read_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, read_ssf, ".")
        else:
            self.assertRaises(IsADirectoryError, read_ssf, ".")
        self.assertRaises(FileNotFoundError, read_ssf, DOES_NOT_EXIST_FILE)
        self.assertRaises(ValueError, read_ssf, CORRUPT_BINARY_TEST_DATA)
        self.assertRaises(ValueError, read_ssf, CORRUPT_XML_TEST_DATA.encode('utf-8'))

    # sourcery skip: no-conditionals-in-tests
    def test_write_raises(self):
        if os.name == "nt":
            self.assertRaises(PermissionError, write_ssf, SSF(), ".", ResourceType.SSF)
        else:
            self.assertRaises(IsADirectoryError, write_ssf, SSF(), ".", ResourceType.SSF)
        self.assertRaises(ValueError, write_ssf, SSF(), ".", ResourceType.INVALID)


if __name__ == "__main__":
    unittest.main()
