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

from pykotor.common.misc import EquipmentSlot, Game
from pykotor.extract.installation import Installation
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.utc import construct_utc, dismantle_utc
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFF
    from pykotor.resource.generics.utc import UTC

# Inlined test.utc content converted to XML format
TEST_UTC_XML = """<gff3>
  <struct id="-1">
    <resref label="TemplateResRef">n_minecoorta</resref>
    <byte label="Race">6</byte>
    <byte label="SubraceIndex">1</byte>
    <locstring label="FirstName" strref="76046" />
    <locstring label="LastName" strref="123" />
    <uint16 label="Appearance_Type">636</uint16>
    <byte label="Gender">2</byte>
    <sint32 label="Phenotype">0</sint32>
    <uint16 label="PortraitId">1</uint16>
    <locstring label="Description" strref="123" />
    <exostring label="Tag">Coorta</exostring>
    <resref label="Conversation">coorta</resref>
    <byte label="IsPC">1</byte>
    <uint16 label="FactionID">5</uint16>
    <byte label="Disarmable">1</byte>
    <exostring label="Subrace" />
    <exostring label="Deity" />
    <uint16 label="SoundSetFile">46</uint16>
    <byte label="Plot">1</byte>
    <byte label="Interruptable">1</byte>
    <byte label="NoPermDeath">1</byte>
    <byte label="NotReorienting">1</byte>
    <byte label="BodyBag">1</byte>
    <byte label="BodyVariation">1</byte>
    <byte label="TextureVar">1</byte>
    <byte label="Min1HP">1</byte>
    <byte label="PartyInteract">1</byte>
    <byte label="Hologram">1</byte>
    <byte label="IgnoreCrePath">1</byte>
    <byte label="MultiplierSet">3</byte>
    <byte label="Str">10</byte>
    <byte label="Dex">10</byte>
    <byte label="Con">10</byte>
    <byte label="Int">10</byte>
    <byte label="Wis">10</byte>
    <byte label="Cha">10</byte>
    <sint32 label="WalkRate">7</sint32>
    <byte label="NaturalAC">1</byte>
    <sint16 label="HitPoints">8</sint16>
    <sint16 label="CurrentHitPoints">8</sint16>
    <sint16 label="MaxHitPoints">8</sint16>
    <sint16 label="ForcePoints">1</sint16>
    <sint16 label="CurrentForce">1</sint16>
    <sint16 label="refbonus">1</sint16>
    <sint16 label="willbonus">1</sint16>
    <sint16 label="fortbonus">1</sint16>
    <byte label="GoodEvil">50</byte>
    <byte label="LawfulChaotic">0</byte>
    <float label="BlindSpot">120.0</float>
    <float label="ChallengeRating">1.0</float>
    <byte label="PerceptionRange">11</byte>
    <resref label="ScriptHeartbeat">k_def_heartbt01</resref>
    <resref label="ScriptOnNotice">k_def_percept01</resref>
    <resref label="ScriptSpellAt">k_def_spellat01</resref>
    <resref label="ScriptAttacked">k_def_attacked01</resref>
    <resref label="ScriptDamaged">k_def_damage01</resref>
    <resref label="ScriptDisturbed">k_def_disturb01</resref>
    <resref label="ScriptEndRound">k_def_combend01</resref>
    <resref label="ScriptEndDialogu">k_def_endconv</resref>
    <resref label="ScriptDialogue">k_def_dialogue01</resref>
    <resref label="ScriptSpawn">k_def_spawn01</resref>
    <resref label="ScriptRested" />
    <resref label="ScriptDeath">k_def_death01</resref>
    <resref label="ScriptUserDefine">k_def_userdef01</resref>
    <resref label="ScriptOnBlocked">k_def_blocked01</resref>
    <list label="SkillList">
      <struct id="0">
        <byte label="Rank">1</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">2</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">3</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">4</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">5</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">6</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">7</byte>
        </struct>
      <struct id="0">
        <byte label="Rank">8</byte>
        </struct>
      </list>
    <list label="FeatList">
      <struct id="1">
        <uint16 label="Feat">93</uint16>
        </struct>
      <struct id="1">
        <uint16 label="Feat">94</uint16>
        </struct>
      </list>
    <list label="TemplateList" />
    <list label="SpecAbilityList" />
    <list label="ClassList">
      <struct id="2">
        <sint32 label="Class">0</sint32>
        <sint16 label="ClassLevel">2</sint16>
        <list label="KnownList0">
          <struct id="3">
            <uint16 label="Spell">7</uint16>
            <byte label="SpellMetaMagic">0</byte>
            <byte label="SpellFlags">1</byte>
            </struct>
          </list>
        </struct>
      <struct id="2">
        <sint32 label="Class">1</sint32>
        <sint16 label="ClassLevel">3</sint16>
        <list label="KnownList0">
          <struct id="3">
            <uint16 label="Spell">9</uint16>
            <byte label="SpellMetaMagic">0</byte>
            <byte label="SpellFlags">1</byte>
            </struct>
          <struct id="3">
            <uint16 label="Spell">11</uint16>
            <byte label="SpellMetaMagic">0</byte>
            <byte label="SpellFlags">1</byte>
            </struct>
          </list>
        </struct>
      </list>
    <list label="Equip_ItemList">
      <struct id="2">
        <resref label="EquippedRes">mineruniform</resref>
        <byte label="Dropable">1</byte>
        </struct>
      <struct id="131072">
        <resref label="EquippedRes">g_i_crhide008</resref>
        </struct>
      </list>
    <byte label="PaletteID">3</byte>
    <exostring label="Comment">comment</exostring>
    <list label="ItemList">
      <struct id="0">
        <resref label="InventoryRes">g_w_thermldet01</resref>
        <uint16 label="Repos_PosX">0</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        <byte label="Dropable">1</byte>
        </struct>
      <struct id="1">
        <resref label="InventoryRes">g_w_thermldet01</resref>
        <uint16 label="Repos_PosX">1</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      <struct id="2">
        <resref label="InventoryRes">g_w_thermldet01</resref>
        <uint16 label="Repos_PosX">2</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      <struct id="3">
        <resref label="InventoryRes">g_w_thermldet02</resref>
        <uint16 label="Repos_PosX">3</uint16>
        <uint16 label="Repos_Posy">0</uint16>
        </struct>
      </list>
    </struct>
  </gff3>"""

K1_PATH = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")


class TestUTC(TestCase):
    def setUp(self):
        self.log_messages = [os.linesep]

    def log_func(self, *msgs):
        self.log_messages.append("\t".join(msgs))

    def test_io_construct(self):
        gff = read_gff(TEST_UTC_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        utc = construct_utc(gff)
        self.validate_io(utc)

    def test_io_reconstruct(self):
        gff = read_gff(TEST_UTC_XML.encode('utf-8'), file_format=ResourceType.GFF_XML)
        gff = dismantle_utc(construct_utc(gff))
        utc = construct_utc(gff)
        self.validate_io(utc)

    def test_file_io(self):
        """Test reading from a temporary file to ensure file-based reading still works."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.utc.xml', delete=False, encoding='utf-8') as tmp:
            tmp.write(TEST_UTC_XML)
            tmp_path = tmp.name

        try:
            gff = read_gff(tmp_path, file_format=ResourceType.GFF_XML)
            utc = construct_utc(gff)
            self.validate_io(utc)
        finally:
            os.unlink(tmp_path)

    def validate_io(self, utc: UTC):
        assert utc.appearance_id == 636
        assert utc.body_variation == 1
        assert utc.blindspot == 120.0
        assert utc.charisma == 10
        assert utc.challenge_rating == 1.0
        assert utc.comment == "comment"
        assert utc.constitution == 10
        assert utc.conversation == "coorta"
        assert utc.fp == 1
        assert utc.current_hp == 8
        assert utc.dexterity == 10
        assert utc.disarmable
        assert utc.faction_id == 5
        assert utc.first_name.stringref == 76046
        assert utc.max_fp == 1
        assert utc.gender_id == 2
        assert utc.alignment == 50
        assert utc.hp == 8
        assert utc.hologram
        assert utc.ignore_cre_path
        assert utc.intelligence == 10
        assert utc.interruptable
        assert utc.is_pc
        assert utc.last_name.stringref == 123
        assert utc.max_hp == 8
        assert utc.min1_hp
        assert utc.multiplier_set == 3
        assert utc.natural_ac == 1
        assert utc.no_perm_death
        assert utc.not_reorienting
        assert utc.party_interact
        assert utc.perception_id == 11
        assert utc.plot
        assert utc.portrait_id == 1
        assert utc.race_id == 6
        assert utc.on_attacked == "k_def_attacked01"
        assert utc.on_damaged == "k_def_damage01"
        assert utc.on_death == "k_def_death01"
        assert utc.on_dialog == "k_def_dialogue01"
        assert utc.on_disturbed == "k_def_disturb01"
        assert utc.on_end_dialog == "k_def_endconv"
        assert utc.on_end_round == "k_def_combend01"
        assert utc.on_heartbeat == "k_def_heartbt01"
        assert utc.on_blocked == "k_def_blocked01"
        assert utc.on_notice == "k_def_percept01"
        assert utc.on_spawn == "k_def_spawn01"
        assert utc.on_spell == "k_def_spellat01"
        assert utc.on_user_defined == "k_def_userdef01"
        assert utc.soundset_id == 46
        assert utc.strength == 10
        assert utc.subrace_id == 1
        assert utc.tag == "Coorta"
        assert utc.resref == "n_minecoorta"
        assert utc.texture_variation == 1
        assert utc.walkrate_id == 7
        assert utc.wisdom == 10
        assert utc.fortitude_bonus == 1
        assert utc.reflex_bonus == 1
        assert utc.willpower_bonus == 1

        assert len(utc.classes) == 2
        assert utc.classes[1].class_id == 1
        assert utc.classes[1].class_level == 3
        assert len(utc.classes[1].powers) == 2
        assert utc.classes[1].powers[0] == 9

        assert len(utc.equipment.items()) == 2
        assert utc.equipment[EquipmentSlot.ARMOR].resref == "mineruniform"
        assert utc.equipment[EquipmentSlot.ARMOR].droppable
        assert utc.equipment[EquipmentSlot.HIDE].resref == "g_i_crhide008"
        assert not utc.equipment[EquipmentSlot.HIDE].droppable

        assert len(utc.feats) == 2
        assert utc.feats[1] == 94

        assert len(utc.inventory) == 4
        assert utc.inventory[0].droppable
        assert not utc.inventory[1].droppable
        assert utc.inventory[1].resref == "g_w_thermldet01"

        assert utc.computer_use == 1
        assert utc.demolitions == 2
        assert utc.stealth == 3
        assert utc.awareness == 4
        assert utc.persuade == 5
        assert utc.repair == 6
        assert utc.security == 7
        assert utc.treat_injury == 8


if __name__ == "__main__":
    unittest.main()
