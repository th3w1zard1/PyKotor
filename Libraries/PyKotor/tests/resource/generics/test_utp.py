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

from typing import TYPE_CHECKING


from pykotor.resource.type import ResourceType
from pykotor.common.misc import Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utp import UTP, construct_utp, dismantle_utp

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utp import UTP

# Inlined test.utp content converted to XML format
TEST_UTP_XML = """<gff3>
  <struct id="-1">
    <exostring label="Tag">SecLoc</exostring>
    <locstring label="LocName" strref="74450" />
    <locstring label="Description" strref="-1" />
    <resref label="TemplateResRef">lockerlg002</resref>
    <byte label="AutoRemoveKey">1</byte>
    <byte label="CloseLockDC">13</byte>
    <resref label="Conversation">conversation</resref>
    <byte label="Interruptable">1</byte>
    <uint32 label="Faction">1</uint32>
    <byte label="Plot">1</byte>
    <byte label="NotBlastable">1</byte>
    <byte label="Min1HP">1</byte>
    <byte label="KeyRequired">1</byte>
    <byte label="Lockable">0</byte>
    <byte label="Locked">1</byte>
    <byte label="OpenLockDC">28</byte>
    <byte label="OpenLockDiff">1</byte>
    <char label="OpenLockDiffMod">1</char>
    <uint16 label="PortraitId">0</uint16>
    <byte label="TrapDetectable">1</byte>
    <byte label="TrapDetectDC">0</byte>
    <byte label="TrapDisarmable">1</byte>
    <byte label="DisarmDC">15</byte>
    <byte label="TrapFlag">0</byte>
    <byte label="TrapOneShot">1</byte>
    <byte label="TrapType">0</byte>
    <exostring label="KeyName">somekey</exostring>
    <byte label="AnimationState">2</byte>
    <uint32 label="Appearance">67</uint32>
    <sint16 label="HP">15</sint16>
    <sint16 label="CurrentHP">15</sint16>
    <byte label="Hardness">5</byte>
    <byte label="Fort">16</byte>
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
    <resref label="OnTrapTriggered" />
    <resref label="OnUnlock">onunlock</resref>
    <resref label="OnUserDefined">onuserdefined</resref>
    <byte label="HasInventory">1</byte>
    <byte label="PartyInteract">1</byte>
    <byte label="BodyBag">0</byte>
    <byte label="Static">1</byte>
    <byte label="Type">0</byte>
    <byte label="Useable">1</byte>
    <resref label="OnEndDialogue">onenddialogue</resref>
    <resref label="OnInvDisturbed">oninvdisturbed</resref>
    <resref label="OnUsed">onused</resref>
    <resref label="OnFailToOpen">onfailtoopen</resref>
    <list label="ItemList">
      <struct id="0">
        <resref label="InventoryRes">g_w_iongren01</resref>
        <uint16 label="Repos_PosX">0</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      <struct id="1">
        <resref label="InventoryRes">g_w_iongren02</resref>
        <uint16 label="Repos_PosX">1</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        <byte label="Dropable">1</byte>
        </struct>
      </list>
    <byte label="PaletteID">6</byte>
    <exostring label="Comment">Large standup locker</exostring>
    </struct>
  </gff3>"""

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class Test(TestCase):
    def setUp(self):
        self.log_messages: list[str] = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_gff_reconstruct(self):
        gff: GFF = read_gff(TEST_UTP_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        reconstructed_gff: GFF = dismantle_utp(construct_utp(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self):
        gff: GFF = read_gff(TEST_UTP_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        utp: UTP = construct_utp(gff)
        self.validate_io(utp)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTP_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        gff: GFF = dismantle_utp(construct_utp(gff))
        utp: UTP = construct_utp(gff)
        self.validate_io(utp)

    def validate_io(self, utp: UTP):
        assert utp.tag == "SecLoc"
        assert utp.name.stringref == 74450
        assert utp.resref == "lockerlg002"
        assert utp.auto_remove_key == 1
        assert utp.lock_dc == 13
        assert utp.conversation == "conversation"
        assert utp.faction_id == 1
        assert utp.plot == 1
        assert utp.not_blastable == 1
        assert utp.min1_hp == 1
        assert utp.key_required == 1
        assert utp.lockable == 0
        assert utp.locked == 1
        assert utp.unlock_dc == 28
        assert utp.unlock_diff == 1
        assert utp.unlock_diff_mod == 1
        assert utp.key_name == "somekey"
        assert utp.animation_state == 2
        assert utp.appearance_id == 67
        assert utp.min1_hp == 1
        assert utp.current_hp == 15
        assert utp.hardness == 5
        assert utp.fortitude == 16
        assert utp.resref == "lockerlg002"
        assert utp.on_closed == "onclosed"
        assert utp.on_damaged == "ondamaged"
        assert utp.on_death == "ondeath"
        assert utp.on_heartbeat == "onheartbeat"
        assert utp.on_lock == "onlock"
        assert utp.on_melee_attack == "onmeleeattacked"
        assert utp.on_open == "onopen"
        assert utp.on_force_power == "onspellcastat"
        assert utp.on_unlock == "onunlock"
        assert utp.on_user_defined == "onuserdefined"
        assert utp.has_inventory == 1
        assert utp.party_interact == 1
        assert utp.static == 1
        assert utp.useable == 1
        assert utp.on_end_dialog == "onenddialogue"
        assert utp.on_inventory == "oninvdisturbed"
        assert utp.on_used == "onused"
        assert utp.on_open_failed == "onfailtoopen"
        assert utp.comment == "Large standup locker"
        assert utp.description.stringref == -1
        assert utp.interruptable == 1
        assert utp.portrait_id == 0
        assert utp.trap_detectable == 1
        assert utp.trap_detect_dc == 0
        assert utp.trap_disarmable == 1
        assert utp.trap_disarm_dc == 15
        assert utp.trap_flag == 0
        assert utp.trap_one_shot == 1
        assert utp.trap_type == 0
        assert utp.will == 0
        assert utp.on_disarm == "ondisarm"
        assert utp.on_trap_triggered == ""
        assert utp.bodybag_id == 0
        assert utp.trap_type == 0
        assert utp.palette_id == 6

        assert len(utp.inventory) == 2
        assert not utp.inventory[0].droppable
        assert utp.inventory[1].droppable
        assert utp.inventory[1].resref == "g_w_iongren02"



if __name__ == "__main__":
    try:
        import pytest
    except ImportError: # pragma: no cover
        unittest.main()
    else:
        pytest.main(["-v", __file__])

