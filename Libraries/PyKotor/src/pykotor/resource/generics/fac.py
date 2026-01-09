from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class FACFaction:
    """Represents a single faction in the FactionList.

    Attributes:
    ----------
        name: Name of the faction.
            Reference: Bioware-Aurora-Faction.md - FactionName field (CExoString)
        
        global_effect: Whether all members of this faction immediately change their standings
            if one member changes standings.
            Reference: Bioware-Aurora-Faction.md - FactionGlobal field (WORD)
            1 = global effect, 0 = individual effect
        
        parent_id: Index into FactionList specifying the parent faction, or 0xFFFFFFFF for standard factions.
            Reference: Bioware-Aurora-Faction.md - FactionParentID field (DWORD)
            Standard factions (PC, Hostile, Commoner, Merchant) use 0xFFFFFFFF
    """

    def __init__(self):
        self.name: str = ""
        self.global_effect: bool = False
        self.parent_id: int = 0xFFFFFFFF


class FACReputation:
    """Represents a reputation relationship between two factions.

    Attributes:
    ----------
        faction_id1: Index into FactionList for the first faction.
            Reference: Bioware-Aurora-Faction.md - FactionID1 field (DWORD)
        
        faction_id2: Index into FactionList for the second faction.
            Reference: Bioware-Aurora-Faction.md - FactionID2 field (DWORD)
        
        reputation: How Faction2 perceives Faction1.
            Reference: Bioware-Aurora-Faction.md - FactionRep field (DWORD)
            0-10 = Faction2 is hostile to Faction1
            11-89 = Faction2 is neutral to Faction1
            90-100 = Faction2 is friendly to Faction1
    """

    def __init__(self):
        self.faction_id1: int = 0
        self.faction_id2: int = 0
        self.reputation: int = 50  # Default to neutral


class FAC:
    """Stores faction data.

    FAC files are GFF-based format files that store faction definitions and reputation
    relationships between factions. The file is typically named "repute.fac" in modules.

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x004c3960 - CSWSModule::SaveModuleFAC (378 bytes, 69 lines)
                - Main FAC GFF writer entry point
                - Saves faction data to GFF structure
                - Function signature: SaveModuleFAC(void)
                - Called from SaveModuleStart (0x004c8960)
            - 0x0052b5c0 - CFactionManager::LoadFactionsFromSaveGame (455 bytes, 86 lines)
                - Main FAC GFF parser entry point for FactionList
                - Loads factions from GFF structure
                - Function signature: LoadFactionsFromSaveGame(CFactionManager* this, CResGFF* param_1, CResList* param_2)
                - Called from LoadModuleStart (0x004c9050)
            - 0x0052bbe0 - CFactionManager::LoadReputationsFromSaveGame (253 bytes, 44 lines)
                - Main FAC GFF parser entry point for RepList
                - Loads reputation relationships from GFF structure
                - Function signature: LoadReputationsFromSaveGame(CFactionManager* this, CResGFF* param_1, CResList* param_2)
                - Called from LoadModuleStart (0x004c9050)
            - 0x0052b790 - CFactionManager::SaveFactions (146 bytes, 29 lines)
                - Saves FactionList to GFF structure
                - Writes FactionName (CExoString), FactionParentID (DWORD), FactionGlobal (WORD)
            - 0x0052b830 - CFactionManager::SaveReputations (169 bytes, 39 lines)
                - Saves RepList to GFF structure
                - Writes FactionID1 (DWORD), FactionID2 (DWORD), FactionRep (DWORD)
            - Reads FactionList (GFFList):
                - FactionName (CExoString) - faction name
                - FactionParentID (DWORD) - parent faction index (0xFFFFFFFF for standard factions)
                - FactionGlobal (WORD) - global effect flag (1 = global, 0 = individual)
            - Reads RepList (GFFList):
                - FactionID1 (DWORD) - first faction index
                - FactionID2 (DWORD) - second faction index
                - FactionRep (DWORD) - reputation value (0-100, clamped)
        KotOR II / TSL (swkotor2.exe):
            - Functionally identical to K1 implementation
            - Same GFF structure and parsing logic

    Attributes:
    ----------
        factions: List of FACFaction objects defining all factions in the module.
            Reference: Bioware-Aurora-Faction.md - FactionList (List of Faction Structs)
            The list index corresponds to the faction ID used in reputation relationships.
        
        reputations: List of FACReputation objects defining how factions perceive each other.
            Reference: Bioware-Aurora-Faction.md - RepList (List of Reputation Structs)
            Defines how each faction stands with every other faction.
            For N factions, the RepList should contain N*N - N elements (excluding PC faction entries).
    """

    BINARY_TYPE = ResourceType.FAC

    def __init__(self):
        self.factions: list[FACFaction] = []
        self.reputations: list[FACReputation] = []


def construct_fac(
    gff: GFF,
) -> FAC:
    """Constructs a FAC from a GFF structure.

    Args:
    ----
        gff: The GFF structure to construct from.

    Returns:
    -------
        FAC: The constructed FAC object.
    """
    fac = FAC()

    root = gff.root

    # Read FactionList
    faction_list: GFFList = root.acquire("FactionList", GFFList())
    for i, faction_struct in enumerate(faction_list):
        faction = FACFaction()
        faction.name = faction_struct.acquire("FactionName", "")
        faction.global_effect = bool(faction_struct.acquire("FactionGlobal", 0))
        # FactionParentID is DWORD, 0xFFFFFFFF for standard factions
        parent_id_val = faction_struct.acquire("FactionParentID", 0xFFFFFFFF)
        # Handle both signed and unsigned representations of 0xFFFFFFFF
        if parent_id_val == -1 or parent_id_val == 0xFFFFFFFF:
            faction.parent_id = 0xFFFFFFFF
        else:
            faction.parent_id = parent_id_val
        fac.factions.append(faction)

    # Read RepList
    rep_list: GFFList = root.acquire("RepList", GFFList())
    for i, rep_struct in enumerate(rep_list):
        reputation = FACReputation()
        reputation.faction_id1 = rep_struct.acquire("FactionID1", 0)
        reputation.faction_id2 = rep_struct.acquire("FactionID2", 0)
        reputation.reputation = rep_struct.acquire("FactionRep", 50)
        fac.reputations.append(reputation)

    return fac


def dismantle_fac(
    fac: FAC,
) -> GFF:
    """Dismantles a FAC into a GFF structure.

    Args:
    ----
        fac: The FAC object to dismantle.

    Returns:
    -------
        GFF: The constructed GFF structure.
    """
    gff = GFF(GFFContent.FAC)

    root: GFFStruct = gff.root

    # Write FactionList
    faction_list: GFFList = root.set_list("FactionList", GFFList())
    for i, faction in enumerate(fac.factions):
        faction_struct = faction_list.add(i)
        faction_struct.set_string("FactionName", faction.name)
        faction_struct.set_uint16("FactionGlobal", 1 if faction.global_effect else 0)
        # FactionParentID as DWORD (uint32), but handle 0xFFFFFFFF correctly
        if faction.parent_id == 0xFFFFFFFF:
            faction_struct.set_uint32("FactionParentID", 0xFFFFFFFF)
        else:
            faction_struct.set_uint32("FactionParentID", faction.parent_id)

    # Write RepList
    rep_list: GFFList = root.set_list("RepList", GFFList())
    for i, reputation in enumerate(fac.reputations):
        rep_struct = rep_list.add(i)
        rep_struct.set_uint32("FactionID1", reputation.faction_id1)
        rep_struct.set_uint32("FactionID2", reputation.faction_id2)
        rep_struct.set_uint32("FactionRep", reputation.reputation)

    return gff


def read_fac(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> FAC:
    """Reads a FAC from a source.

    Args:
    ----
        source: The source to read from.
        offset: Byte offset into the source.
        size: Number of bytes to read.

    Returns:
    -------
        FAC: The read FAC object.
    """
    gff: GFF = read_gff(source, offset, size)
    return construct_fac(gff)


def write_fac(
    fac: FAC,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.GFF,
):
    """Writes a FAC to a target.

    Args:
    ----
        fac: The FAC object to write.
        target: The target to write to.
        file_format: The file format to use.
    """
    gff: GFF = dismantle_fac(fac)
    write_gff(gff, target, file_format)


def bytes_fac(
    fac: FAC,
    file_format: ResourceType = ResourceType.GFF,
) -> bytes:
    """Converts a FAC to bytes.

    Args:
    ----
        fac: The FAC object to convert.
        file_format: The file format to use.

    Returns:
    -------
        bytes: The FAC as bytes.
    """
    gff: GFF = dismantle_fac(fac)
    return bytes_gff(gff, file_format)

