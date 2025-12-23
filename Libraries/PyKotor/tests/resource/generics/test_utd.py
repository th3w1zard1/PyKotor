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

from typing import TYPE_CHECKING

from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utd import construct_utd, dismantle_utd
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.generics.utd import UTD

# Inlined test.utd content converted to XML format
TEST_UTD_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">TelosDoor13</exostring>
    <locstring label="LocName" strref="123731" />
    <locstring label="Description" strref="-1" />
    <resref label="TemplateResRef">door_tel014</resref>
    <byte label="AutoRemoveKey">1</byte>
    <byte label="CloseLockDC">0</byte>
    <resref label="Conversation">convoresref</resref>
    <byte label="Interruptable">1</byte>
    <uint32 label="Faction">1</uint32>
    <byte label="Plot">1</byte>
    <byte label="NotBlastable">1</byte>
    <byte label="Min1HP">1</byte>
    <byte label="KeyRequired">1</byte>
    <byte label="Lockable">1</byte>
    <byte label="Locked">1</byte>
    <byte label="OpenLockDC">28</byte>
    <byte label="OpenLockDiff">1</byte>
    <char label="OpenLockDiffMod">1</char>
    <uint16 label="PortraitId">0</uint16>
    <byte label="TrapDetectable">1</byte>
    <byte label="TrapDetectDC">0</byte>
    <byte label="TrapDisarmable">1</byte>
    <byte label="DisarmDC">28</byte>
    <byte label="TrapFlag">0</byte>
    <byte label="TrapOneShot">1</byte>
    <byte label="TrapType">2</byte>
    <exostring label="KeyName">keyname</exostring>
    <byte label="AnimationState">1</byte>
    <uint32 label="Appearance">1</uint32>
    <sint16 label="HP">20</sint16>
    <sint16 label="CurrentHP">60</sint16>
    <byte label="Hardness">5</byte>
    <byte label="Fort">28</byte>
    <byte label="Ref">0</byte>
    <byte label="Will">0</byte>
    <resref label="OnClosed">onclosed</resref>
    <resref label="OnDamaged">ondamaged</resref>
    <resref label="OnDeath">ondeath</resref>
    <resref label="OnDisarm">ondisarm</resref>
    <resref label="OnHeartbeat">onheartbeat</resref>
    <resref label="OnLock">onlock</resref>
    <resref label="OnMeleeAttacked">onmeleeattacked</resref>
    <resref label="OnOpen">onopen</resref>
    <resref label="OnSpellCastAt">onspellcastat</resref>
    <resref label="OnTrapTriggered">ontraptriggered</resref>
    <resref label="OnUnlock">onunlock</resref>
    <resref label="OnUserDefined">onuserdefined</resref>
    <uint16 label="LoadScreenID">0</uint16>
    <byte label="GenericType">110</byte>
    <byte label="Static">1</byte>
    <byte label="OpenState">1</byte>
    <resref label="OnClick">onclick</resref>
    <resref label="OnFailToOpen">onfailtoopen</resref>
    <byte label="PaletteID">1</byte>
    <exostring label="Comment">abcdefg</exostring>
    </struct>
  </gff3>"""

# Inlined k1_utd_same_test.utd content converted to XML format
K1_SAME_TEST_UTD_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">ldr_agtoaj</exostring>
    <locstring label="LocName" strref="-1">
      <string language="0">Door</string>
      </locstring>
    <locstring label="Description" strref="-1">
      <string language="0" />
      </locstring>
    <resref label="TemplateResRef">ldr_agtoaj</resref>
    <byte label="AutoRemoveKey">0</byte>
    <byte label="CloseLockDC">0</byte>
    <resref label="Conversation" />
    <byte label="Interruptable">0</byte>
    <uint32 label="Faction">1</uint32>
    <byte label="Plot">1</byte>
    <byte label="NotBlastable">1</byte>
    <byte label="Min1HP">0</byte>
    <byte label="KeyRequired">0</byte>
    <byte label="Lockable">0</byte>
    <byte label="Locked">0</byte>
    <byte label="OpenLockDC">28</byte>
    <byte label="OpenLockDiff">1</byte>
    <char label="OpenLockDiffMod">0</char>
    <uint16 label="PortraitId">0</uint16>
    <byte label="TrapDetectable">1</byte>
    <byte label="TrapDetectDC">0</byte>
    <byte label="TrapDisarmable">1</byte>
    <byte label="DisarmDC">28</byte>
    <byte label="TrapFlag">0</byte>
    <byte label="TrapOneShot">1</byte>
    <byte label="TrapType">2</byte>
    <exostring label="KeyName" />
    <byte label="AnimationState">0</byte>
    <uint32 label="Appearance">0</uint32>
    <sint16 label="HP">20</sint16>
    <sint16 label="CurrentHP">60</sint16>
    <byte label="Hardness">5</byte>
    <byte label="Fort">28</byte>
    <byte label="Ref">0</byte>
    <byte label="Will">0</byte>
    <resref label="OnClosed" />
    <resref label="OnDamaged" />
    <resref label="OnDeath" />
    <resref label="OnDisarm" />
    <resref label="OnHeartbeat" />
    <resref label="OnLock" />
    <resref label="OnMeleeAttacked" />
    <resref label="OnOpen" />
    <resref label="OnSpellCastAt" />
    <resref label="OnTrapTriggered" />
    <resref label="OnUnlock" />
    <resref label="OnUserDefined" />
    <uint16 label="LoadScreenID">0</uint16>
    <byte label="GenericType">19</byte>
    <byte label="Static">0</byte>
    <byte label="OpenState">0</byte>
    <resref label="OnClick" />
    <resref label="OnFailToOpen" />
    <byte label="PaletteID">6</byte>
    <exostring label="Comment">Hammerhead Door 1</exostring>
    <exostring label="KTInfoVersion">1.0.2210.16738</exostring>
    <exostring label="KTInfoDate">Tuesday, June 9, 2020 11:05:31 PM</exostring>
    <sint32 label="KTGameVerIndex">0</sint32>
    </struct>
  </gff3>"""
K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestUTD(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    @unittest.skip("This test is known to fail - fixme")  # FIXME:
    def test_gff_reconstruct(self):
        gff = read_gff(K1_SAME_TEST_UTD_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_utd(construct_utd(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff = read_gff(TEST_UTD_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        utd = construct_utd(gff)
        self.validate_io(utd)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTD_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        gff = dismantle_utd(construct_utd(gff))
        utd = construct_utd(gff)
        self.validate_io(utd)

    def validate_io(self, utd: UTD):
        assert utd.tag == "TelosDoor13"
        assert utd.name.stringref == 123731
        assert utd.description.stringref == -1
        assert utd.resref == "door_tel014"
        assert utd.auto_remove_key == 1
        assert utd.lock_dc == 0
        assert utd.conversation == "convoresref"
        assert utd.interruptable == 1
        assert utd.faction_id == 1
        assert utd.plot == 1
        assert utd.not_blastable == 1
        assert utd.min1_hp == 1
        assert utd.key_required == 1
        assert utd.lockable == 1
        assert utd.locked == 1
        assert utd.unlock_dc == 28
        assert utd.unlock_diff_mod == 1
        assert utd.unlock_diff_mod == 1
        assert utd.portrait_id == 0
        assert utd.trap_detectable == 1
        assert utd.trap_detect_dc == 0
        assert utd.trap_disarmable == 1
        assert utd.trap_disarm_dc == 28
        assert utd.trap_flag == 0
        assert utd.trap_one_shot == 1
        assert utd.trap_type == 2
        assert utd.key_name == "keyname"
        assert utd.animation_state == 1
        assert utd.unused_appearance == 1
        assert utd.min1_hp == 1
        assert utd.current_hp == 60
        assert utd.hardness == 5
        assert utd.fortitude == 28
        assert utd.resref == "door_tel014"
        assert utd.willpower == 0
        assert utd.on_closed == "onclosed"
        assert utd.on_damaged == "ondamaged"
        assert utd.on_death == "ondeath"
        assert utd.on_disarm == "ondisarm"
        assert utd.on_heartbeat == "onheartbeat"
        assert utd.on_lock == "onlock"
        assert utd.on_melee == "onmeleeattacked"
        assert utd.on_open == "onopen"
        assert utd.on_power == "onspellcastat"
        assert utd.on_trap_triggered == "ontraptriggered"
        assert utd.on_unlock == "onunlock"
        assert utd.on_user_defined == "onuserdefined"
        assert utd.loadscreen_id == 0
        assert utd.appearance_id == 110
        assert utd.static == 1
        assert utd.open_state == 1
        assert utd.on_click == "onclick"
        assert utd.on_open_failed == "onfailtoopen"
        assert utd.palette_id == 1
        assert utd.comment == "abcdefg"


if __name__ == "__main__":
    unittest.main()
