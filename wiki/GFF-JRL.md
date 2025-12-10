# JRL (Journal)

Part of the [GFF File Format Documentation](GFF-File-Format).

[JRL files](GFF-File-Format#jrl-journal) define the [structure](GFF-File-Format#file-structure) of the player's [quest journal](GFF-File-Format#jrl-journal). They organize [quests](GFF-File-Format#jrl-journal) into categories and track progress through individual [journal entries](GFF-File-Format#jrl-journal).

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Journal [format](GFF-File-Format) specification, see [Bioware Aurora Journal Format](Bioware-Aurora-Journal).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/jrl.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/jrl.py)

## Quest [structure](GFF-File-Format#file-structure)

[JRL](GFF-File-Format#jrl-journal) [files](GFF-File-Format) contain a list of `Categories` (Quests), each containing a list of `EntryList` (States).

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `Categories` | List | List of quests |

## Quest Category (JRLQuest)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `Tag` | [CExoString](GFF-File-Format#cexostring) | Unique quest identifier |
| `Name` | [CExoLocString](GFF-File-Format#localizedstring) | Quest title |
| `Comment` | [CExoString](GFF-File-Format#cexostring) | Developer comment |
| `Priority` | Int | Sorting priority (0=Highest, 4=Lowest) |
| `PlotIndex` | Int | Legacy plot [index](2DA-File-Format#row-labels) |
| `PlanetID` | Int | Planet association (unused) |
| `EntryList` | List | List of quest states |

**Priority Levels:**

- **0 (Highest)**: Main quest line
- **1 (High)**: Important side quests
- **2 (Medium)**: Standard side quests
- **3 (Low)**: Minor tasks
- **4 (Lowest)**: Completed/Archived

## Quest Entry (JRLEntry)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `ID` | Int | State identifier (referenced by scripts/dialogue) |
| `Text` | [CExoLocString](GFF-File-Format#localizedstring) | [Journal](GFF-File-Format#jrl-journal) text displayed for this state |
| `End` | Byte | 1 if this state completes the quest |
| `XP_Percentage` | Float | XP reward multiplier for reaching this state |

**Quest Updates:**

- Scripts use `AddJournalQuestEntry("Tag", ID)` to update quests.
- Dialogues use `Quest` and `QuestEntry` [fields](GFF-File-Format#file-structure).
- Only the highest ID reached is typically displayed (unless `AllowOverrideHigher` is set in `global.jrl` logic).
- `End=1` moves the quest to the "Completed" tab.

## Implementation Notes

- **global.jrl**: The master [journal files](GFF-File-Format#jrl-journal) for the entire game.
- **Module JRLs**: Not typically used; most quests [ARE](GFF-File-Format#are-area) global.
- **XP Rewards**: `XP_Percentage` scales the `journal.2da` XP [value](GFF-File-Format#data-types) for the quest.

---
