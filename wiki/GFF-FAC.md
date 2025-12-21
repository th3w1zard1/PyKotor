# FAC (Faction) File Format

FAC files are GFF-based format files that store faction definitions and reputation relationships between factions in KotOR modules. The file is typically named `repute.fac` in modules.

**Official BioWare Documentation:** For the authoritative BioWare Aurora Engine Faction Format specification, see [Bioware Aurora Faction Format](Bioware-Aurora-Faction.md).

**Source:** This documentation is based on the official BioWare Aurora Engine Faction Format PDF, archived in [`vendor/xoreos-docs/specs/bioware/Faction_Format.pdf`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/bioware/Faction_Format.pdf).

---

## Overview

A Faction is a control system for determining how game objects interact with each other in terms of friendly, neutral, and hostile reactions. Faction information is stored in the `repute.fac` file in a module or savegame. This file uses BioWare's Generic File Format (GFF), and the GFF FileType string in the header of `repute.fac` is `"FAC "`.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/generics/fac.py`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/generics/fac.py)

**Related Files:**
- `repute.2da` - Default faction standings (see [2DA File Format](2DA-File-Format))
- `repadjust.2da` - Reputation adjustment values (see [2DA File Format](2DA-File-Format))

---

## Top Level Struct

The top-level GFF struct contains two lists:

| Label      | Type | Description                                                          |
| ---------- | ---- | -------------------------------------------------------------------- |
| FactionList | List | List of Faction Structs (StructID = list index). Defines what Factions exist in the module. |
| RepList    | List | List of Reputation Structs (StructID = list index). Defines how each Faction stands with every other Faction. |

---

## Faction Struct

Each Faction Struct in the FactionList defines a single faction. The StructID corresponds to the faction's index in the list, which is used as the faction ID in reputation relationships.

| Label          | Type      | Description                                                                                                 |
| -------------- | --------- | ----------------------------------------------------------------------------------------------------------- |
| FactionName    | CExoString | Name of the Faction.                                                                                        |
| FactionGlobal  | WORD      | Global Effect flag. 1 if all members of this faction immediately change their standings with respect to another faction if just one member of this faction changes it standings. 0 if other members of a faction do not change their standings in response to a change in a single member. |
| FactionParentID | DWORD     | Index into the Top Level Struct's FactionList specifying the Faction from which this Faction was derived. The first four standard factions (PC, Hostile, Commoner, and Merchant) have no parents, and use `0xFFFFFFFF` as their FactionParentID. No other Factions can use this value. |

### Standard Factions

KotOR modules typically contain the following standard factions (in order):

1. **PC (Player)** - Index 0, Parent: `0xFFFFFFFF`
2. **Hostile** - Index 1, Parent: `0xFFFFFFFF`
3. **Commoner** - Index 2, Parent: `0xFFFFFFFF`
4. **Merchant** - Index 3, Parent: `0xFFFFFFFF`
5. **Defender** - Index 4, Parent: `0xFFFFFFFF` (KotOR 2 only)

---

## Reputation Struct

Each Reputation Struct in the RepList describes how one faction feels about another faction. Feelings need not be mutual. For example, Exterminators might be hostile to Rats, but Rats may be neutral to Exterminators, so that a Rat would only attack a Hunter or run away from a Hunter if a Hunter attacked the Rat first.

| Label     | Type  | Description                                                                                    |
| --------- | ----- | ---------------------------------------------------------------------------------------------- |
| FactionID1 | DWORD | Index into the Top-Level Struct's FactionList. "Faction1"                                    |
| FactionID2 | DWORD | Index into the Top-Level Struct's FactionList. "Faction2"                                    |
| FactionRep | DWORD | How Faction2 perceives Faction1. 0-10 = Faction2 is hostile to Faction1, 11-89 = Faction2 is neutral to Faction1, 90-100 = Faction2 is friendly to Faction1 |

### Reputation Values

| Range | Relationship              | Description                                                                 |
| ----- | ------------------------- | --------------------------------------------------------------------------- |
| 0-10  | Hostile                   | Faction2 will attack Faction1 on sight.                                    |
| 11-89 | Neutral                   | Faction2 is neutral to Faction1. No automatic aggression.                  |
| 90-100| Friendly                  | Faction2 is friendly to Faction1. Will not attack and may assist.          |

### RepList Completeness

For the RepList to be exhaustively complete, it requires N*N elements, where N = the number of elements in the FactionList. However, the way that the PC Faction (FactionID2 == 0) feels about any other faction is actually meaningless, because PCs are player-controlled and not subject to faction-based AI reactions. Therefore, any Reputation Struct where FactionID2 == 0 (i.e., PC) is not strictly necessary, and can therefore be omitted from the RepList.

Thus, for the RepList to be sufficiently complete, it requires N*N - N elements, where N = the number of elements in the FactionList, assuming that one of those Factions is the PC Faction.

In practice, however, the RepList may contain anywhere from (N*N - N) to (N*N - 1) elements, due to a small idiosyncrasy in how the toolset generates and saves the list. When a new faction is created, up to two new entries may appear for the PC Faction.

From all the above, it follows that a module that contains no user-defined factions will have exactly N*N - N Faction Structs, where N = 5. Modules containing user-defined factions will have more. The maximum number of Faction Structs in the RepList is N*N - 1, because the Player Faction itself can never be a parent faction.

---

## Related 2DA Files

### repute.2da

The `repute.2da` file defines default faction standings. Each row corresponds to a faction ID, and columns represent how that faction feels about other factions.

**Rows (by faction ID):**
- Row 0: Player
- Row 1: Hostile
- Row 2: Commoner
- Row 3: Merchant
- Row 4: Defender (KotOR 2 only)

**Columns:**
- `LABEL` - String: Programmer label; name of faction being considered by the faction named in each of the other columns. Row number is the faction ID.
- `HOSTILE` - Integer: How the Hostile faction feels about the other factions
- `COMMONER` - Integer: How the Commoner faction feels about the other factions
- `MERCHANT` - Integer: How the Merchant faction feels about the other factions
- `DEFENDER` - Integer: How the Defender faction feels about the other factions

**Note:** Do not add new rows to `repute.2da`. They will be ignored.

### repadjust.2da

The `repadjust.2da` file describes how faction reputation standings change in response to different faction-affecting actions, how the presence of witnesses affects the changes, and by how much the changes occur.

**Rows (action types - hardcoded, do not change order):**
- Attack
- Theft
- Kill
- Help

**Columns:**
- `LABEL` - String: Programmer label; name of an action.
- `PERSONALREP` - Integer: Personal reputation adjustment of how the target feels about the perpetrator of the action named in the LABEL.
- `FACTIONREP` - Integer: Base faction reputation adjustment in how the target's Faction feels about the perpetrator. This reputation adjustment is modified further by the effect of witnesses, as controlled by the columns described below. Note that a witness only affects faction standing if the witness belongs to a Global faction.
- `WITFRIA` - Integer: Friendly witness target faction reputation adjustment.
- `WITFRIB` - Integer: Friendly witness personal reputation adjustment.
- `WITFRIC` - Integer: Friendly witness faction reputation adjustment.
- `WITNEUA` - Integer: Neutral witness target faction reputation adjustment.
- `WITNEUB` - Integer: Neutral witness personal reputation adjustment.
- `WITNEUC` - Integer: Neutral witness faction reputation adjustment.
- `WITENEA` - Integer: Enemy witness target faction reputation adjustment.
- `WITENEB` - Integer: Enemy witness personal reputation adjustment.
- `WITENEC` - Integer: Enemy witness faction reputation adjustment.

**Note:** Do not change the order of rows in `repadjust.2da`. Adding new rows will have no effect.

---

## Usage Examples

### Reading a FAC File

```python
from pykotor.resource.generics.fac import read_fac

# Read from file
fac = read_fac("module/repute.fac")

# Access factions
for i, faction in enumerate(fac.factions):
    print(f"Faction {i}: {faction.name}")
    print(f"  Global Effect: {faction.global_effect}")
    print(f"  Parent ID: {faction.parent_id}")

# Access reputations
for rep in fac.reputations:
    print(f"Faction {rep.faction_id2} perceives Faction {rep.faction_id1} as: {rep.reputation}")
```

### Creating a FAC File

```python
from pykotor.resource.generics.fac import FAC, FACFaction, FACReputation, write_fac

fac = FAC()

# Add standard factions
pc = FACFaction()
pc.name = "PC"
pc.global_effect = False
pc.parent_id = 0xFFFFFFFF
fac.factions.append(pc)

hostile = FACFaction()
hostile.name = "Hostile"
hostile.global_effect = True
hostile.parent_id = 0xFFFFFFFF
fac.factions.append(hostile)

# Add reputation relationship
rep = FACReputation()
rep.faction_id1 = 1  # Hostile
rep.faction_id2 = 0  # PC
rep.reputation = 5   # Hostile (0-10 range)
fac.reputations.append(rep)

# Write to file
write_fac(fac, "output/repute.fac")
```

---

## Implementation Notes

- Faction IDs correspond to list indices in the FactionList
- The PC faction (index 0) typically has no reputation entries where FactionID2 == 0, as PC reactions are player-controlled
- Standard factions use `0xFFFFFFFF` as their parent ID
- Reputation values outside the 0-100 range may cause undefined behavior
- Global factions propagate reputation changes across all members when one member's reputation changes

