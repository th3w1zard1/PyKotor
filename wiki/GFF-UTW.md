# UTW (Waypoint)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTW files define [waypoint templates](GFF-File-Format#utw-waypoint). Waypoints are invisible markers used for spawn points, navigation targets, map notes, and reference points for scripts.

## Documentation References

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Waypoint format specification, see [Bioware Aurora Waypoint Format](Bioware-Aurora-Waypoint).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utw.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utw.py)

---

## Core Identity fields

| field | type | Description |
|:------|:-----|:------------|
| `TemplateResRef` | [ResRef](GFF-File-Format#gff-data-types) | Template identifier for this waypoint |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique tag for script/linking references |
| `LocalizedName` | [CExoLocString](GFF-File-Format#gff-data-types) | Waypoint name |
| `Description` | [CExoLocString](GFF-File-Format#gff-data-types) | Description (unused) |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment/notes |

---

## Map Note Functionality

| field | type | Description |
|:------|:-----|:------------|
| `HasMapNote` | Byte | Waypoint has a map note |
| `MapNoteEnabled` | Byte | Map note is initially visible |
| `MapNote` | [CExoLocString](GFF-File-Format#gff-data-types) | Text displayed on map |

### Map Notes

- If enabled, shows text on the in-game map
- Can be enabled/disabled via script (`SetMapPinEnabled`)
- Used for quest objectives and locations

---

## Linking & Appearance

| field | type | Description |
|:------|:-----|:------------|
| `LinkedTo` | [CExoString](GFF-File-Format#gff-data-types) | Tag of linked object (unused) |
| `Appearance` | Byte | Appearance type (1=Waypoint) |
| `PaletteID` | Byte | Toolset palette category |

---

## Usage

- **Spawn Points**: `CreateObject` uses waypoint location
- **Patrols**: AI walks between waypoints
- **Teleport**: `JumpToLocation` targets waypoints
- **Transitions**: Doors/Triggers link to waypoint tags
