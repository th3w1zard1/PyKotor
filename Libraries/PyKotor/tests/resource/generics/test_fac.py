"""Tests for FAC (Faction) GFF generic type.

Tests FAC file format parsing, construction, and round-trip conversion.
"""

import os
import pathlib
import sys
import unittest
from unittest import TestCase

# Add PyKotor to path
absolute_file_path = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = absolute_file_path.parents[5].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = absolute_file_path.parents[5].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path) -> None:
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from typing import TYPE_CHECKING

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.fac import construct_fac, dismantle_fac, FAC, FACFaction, FACReputation
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    pass

# Test FAC XML with standard factions and reputations
TEST_FAC_XML = """<gff3>
  <struct id="-1">
    <list label="FactionList">
      <struct id="0">
        <exostring label="FactionName">PC</exostring>
        <uint16 label="FactionGlobal">0</uint16>
        <uint32 label="FactionParentID">4294967295</uint32>
      </struct>
      <struct id="1">
        <exostring label="FactionName">Hostile</exostring>
        <uint16 label="FactionGlobal">1</uint16>
        <uint32 label="FactionParentID">4294967295</uint32>
      </struct>
      <struct id="2">
        <exostring label="FactionName">Commoner</exostring>
        <uint16 label="FactionGlobal">0</uint16>
        <uint32 label="FactionParentID">4294967295</uint32>
      </struct>
      <struct id="3">
        <exostring label="FactionName">Merchant</exostring>
        <uint16 label="FactionGlobal">0</uint16>
        <uint32 label="FactionParentID">4294967295</uint32>
      </struct>
    </list>
    <list label="RepList">
      <struct id="0">
        <uint32 label="FactionID1">1</uint32>
        <uint32 label="FactionID2">0</uint32>
        <uint32 label="FactionRep">5</uint32>
      </struct>
      <struct id="1">
        <uint32 label="FactionID1">0</uint32>
        <uint32 label="FactionID2">1</uint32>
        <uint32 label="FactionRep">5</uint32>
      </struct>
      <struct id="2">
        <uint32 label="FactionID1">2</uint32>
        <uint32 label="FactionID2">0</uint32>
        <uint32 label="FactionRep">100</uint32>
      </struct>
      <struct id="3">
        <uint32 label="FactionID1">0</uint32>
        <uint32 label="FactionID2">2</uint32>
        <uint32 label="FactionRep">100</uint32>
      </struct>
      <struct id="4">
        <uint32 label="FactionID1">1</uint32>
        <uint32 label="FactionID2">2</uint32>
        <uint32 label="FactionRep">0</uint32>
      </struct>
      <struct id="5">
        <uint32 label="FactionID1">2</uint32>
        <uint32 label="FactionID2">1</uint32>
        <uint32 label="FactionRep">10</uint32>
      </struct>
      <struct id="6">
        <uint32 label="FactionID1">3</uint32>
        <uint32 label="FactionID2">0</uint32>
        <uint32 label="FactionRep">100</uint32>
      </struct>
      <struct id="7">
        <uint32 label="FactionID1">0</uint32>
        <uint32 label="FactionID2">3</uint32>
        <uint32 label="FactionRep">100</uint32>
      </struct>
      <struct id="8">
        <uint32 label="FactionID1">1</uint32>
        <uint32 label="FactionID2">3</uint32>
        <uint32 label="FactionRep">0</uint32>
      </struct>
      <struct id="9">
        <uint32 label="FactionID1">3</uint32>
        <uint32 label="FactionID2">1</uint32>
        <uint32 label="FactionRep">5</uint32>
      </struct>
      <struct id="10">
        <uint32 label="FactionID1">2</uint32>
        <uint32 label="FactionID2">3</uint32>
        <uint32 label="FactionRep">95</uint32>
      </struct>
      <struct id="11">
        <uint32 label="FactionID1">3</uint32>
        <uint32 label="FactionID2">2</uint32>
        <uint32 label="FactionRep">95</uint32>
      </struct>
    </list>
  </struct>
</gff3>
"""


class TestFAC(TestCase):
    def setUp(self) -> None:
        self.log_messages = [os.linesep]

    def log_func(self, *msgs: str) -> None:
        self.log_messages.append("\t".join(msgs))

    def test_gff_reconstruct(self) -> None:
        """Test round-trip GFF reconstruction."""
        gff = read_gff(TEST_FAC_XML.encode(), file_format=ResourceType.GFF_XML)
        reconstructed_gff = dismantle_fac(construct_fac(gff))
        assert gff.compare(reconstructed_gff, self.log_func), os.linesep.join(self.log_messages)

    def test_io_construct(self) -> None:
        """Test constructing FAC from GFF."""
        gff = read_gff(TEST_FAC_XML.encode(), file_format=ResourceType.GFF_XML)
        fac = construct_fac(gff)
        self.validate_io(fac)

    def test_io_reconstruct(self) -> None:
        """Test round-trip construct/dismantle."""
        gff = read_gff(TEST_FAC_XML.encode(), file_format=ResourceType.GFF_XML)
        gff = dismantle_fac(construct_fac(gff))
        fac = construct_fac(gff)
        self.validate_io(fac)

    def validate_io(self, fac: FAC) -> None:
        """Validate FAC structure matches expected test data."""
        # Validate factions
        assert len(fac.factions) == 4, f"Expected 4 factions, got {len(fac.factions)}"

        # PC faction (index 0)
        pc = fac.factions[0]
        assert pc.name == "PC", f"Expected 'PC', got '{pc.name}'"
        assert pc.global_effect is False, f"Expected False, got {pc.global_effect}"
        assert pc.parent_id == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got {pc.parent_id:#x}"

        # Hostile faction (index 1)
        hostile = fac.factions[1]
        assert hostile.name == "Hostile", f"Expected 'Hostile', got '{hostile.name}'"
        assert hostile.global_effect is True, f"Expected True, got {hostile.global_effect}"
        assert hostile.parent_id == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got {hostile.parent_id:#x}"

        # Commoner faction (index 2)
        commoner = fac.factions[2]
        assert commoner.name == "Commoner", f"Expected 'Commoner', got '{commoner.name}'"
        assert commoner.global_effect is False, f"Expected False, got {commoner.global_effect}"
        assert commoner.parent_id == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got {commoner.parent_id:#x}"

        # Merchant faction (index 3)
        merchant = fac.factions[3]
        assert merchant.name == "Merchant", f"Expected 'Merchant', got '{merchant.name}'"
        assert merchant.global_effect is False, f"Expected False, got {merchant.global_effect}"
        assert merchant.parent_id == 0xFFFFFFFF, f"Expected 0xFFFFFFFF, got {merchant.parent_id:#x}"

        # Validate reputations
        assert len(fac.reputations) == 12, f"Expected 12 reputations, got {len(fac.reputations)}"

        # Find specific reputation: Hostile (1) perceives PC (0) as hostile (5)
        hostile_to_pc = next((r for r in fac.reputations if r.faction_id1 == 1 and r.faction_id2 == 0), None)
        assert hostile_to_pc is not None, "Missing reputation: Hostile -> PC"
        assert hostile_to_pc.reputation == 5, f"Expected 5, got {hostile_to_pc.reputation}"

        # Find reputation: Commoner (2) perceives PC (0) as friendly (100)
        commoner_to_pc = next((r for r in fac.reputations if r.faction_id1 == 2 and r.faction_id2 == 0), None)
        assert commoner_to_pc is not None, "Missing reputation: Commoner -> PC"
        assert commoner_to_pc.reputation == 100, f"Expected 100, got {commoner_to_pc.reputation}"

        # Find reputation: Hostile (1) perceives Commoner (2) as hostile (0)
        hostile_to_commoner = next((r for r in fac.reputations if r.faction_id1 == 1 and r.faction_id2 == 2), None)
        assert hostile_to_commoner is not None, "Missing reputation: Hostile -> Commoner"
        assert hostile_to_commoner.reputation == 0, f"Expected 0, got {hostile_to_commoner.reputation}"

        # Find reputation: Commoner (2) perceives Hostile (1) as hostile (10)
        commoner_to_hostile = next((r for r in fac.reputations if r.faction_id1 == 2 and r.faction_id2 == 1), None)
        assert commoner_to_hostile is not None, "Missing reputation: Commoner -> Hostile"
        assert commoner_to_hostile.reputation == 10, f"Expected 10, got {commoner_to_hostile.reputation}"

        # Find reputation: Merchant (3) perceives Commoner (2) as friendly (95)
        merchant_to_commoner = next((r for r in fac.reputations if r.faction_id1 == 3 and r.faction_id2 == 2), None)
        assert merchant_to_commoner is not None, "Missing reputation: Merchant -> Commoner"
        assert merchant_to_commoner.reputation == 95, f"Expected 95, got {merchant_to_commoner.reputation}"

    def test_create_empty_fac(self) -> None:
        """Test creating an empty FAC structure."""
        fac = FAC()
        assert len(fac.factions) == 0
        assert len(fac.reputations) == 0

        gff = dismantle_fac(fac)
        fac2 = construct_fac(gff)
        assert len(fac2.factions) == 0
        assert len(fac2.reputations) == 0

    def test_create_faction_with_custom_parent(self) -> None:
        """Test creating a faction with a custom parent ID."""
        fac = FAC()

        # Add parent faction
        parent = FACFaction()
        parent.name = "ParentFaction"
        parent.global_effect = False
        parent.parent_id = 0xFFFFFFFF
        fac.factions.append(parent)

        # Add child faction
        child = FACFaction()
        child.name = "ChildFaction"
        child.global_effect = True
        child.parent_id = 0  # Parent is at index 0
        fac.factions.append(child)

        gff = dismantle_fac(fac)
        fac2 = construct_fac(gff)

        assert len(fac2.factions) == 2
        assert fac2.factions[1].parent_id == 0

    def test_reputation_ranges(self) -> None:
        """Test reputation value ranges (hostile, neutral, friendly)."""
        fac = FAC()

        # Add factions
        for name in ["Faction1", "Faction2"]:
            faction = FACFaction()
            faction.name = name
            faction.global_effect = False
            faction.parent_id = 0xFFFFFFFF
            fac.factions.append(faction)

        # Add hostile reputation (0-10)
        rep_hostile = FACReputation()
        rep_hostile.faction_id1 = 0
        rep_hostile.faction_id2 = 1
        rep_hostile.reputation = 5
        fac.reputations.append(rep_hostile)

        # Add neutral reputation (11-89)
        rep_neutral = FACReputation()
        rep_neutral.faction_id1 = 1
        rep_neutral.faction_id2 = 0
        rep_neutral.reputation = 50
        fac.reputations.append(rep_neutral)

        # Add friendly reputation (90-100)
        rep_friendly = FACReputation()
        rep_friendly.faction_id1 = 0
        rep_friendly.faction_id2 = 1
        rep_friendly.reputation = 95
        fac.reputations.append(rep_friendly)

        gff = dismantle_fac(fac)
        fac2 = construct_fac(gff)

        hostile_rep = next((r for r in fac2.reputations if r.reputation == 5), None)
        assert hostile_rep is not None and hostile_rep.reputation == 5

        neutral_rep = next((r for r in fac2.reputations if r.reputation == 50), None)
        assert neutral_rep is not None and neutral_rep.reputation == 50

        friendly_rep = next((r for r in fac2.reputations if r.reputation == 95), None)
        assert friendly_rep is not None and friendly_rep.reputation == 95


if __name__ == "__main__":
    unittest.main()

