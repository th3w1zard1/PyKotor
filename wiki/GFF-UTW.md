# UTW (Waypoint)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTW [files](GFF-File-Format) define [waypoint templates](GFF-File-Format#utw-waypoint). Waypoints [ARE](GFF-File-Format#are-area) invisible markers used for spawn points, navigation targets, map notes, and reference points for scripts.

## Documentation References

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Waypoint [format](GFF-File-Format) specification, see [Bioware Aurora Waypoint Format](Bioware-Aurora-Waypoint).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utw.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utw.py)

---

## Core Identity [fields](GFF-File-Format#file-structure)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
|:------|:-----|:------------|
| `TemplateResRef` | [ResRef](GFF-File-Format#resref) | Template identifier for this waypoint |
| `Tag` | [CExoString](GFF-File-Format#cexostring) | Unique tag for script/linking references |
| `LocalizedName` | [CExoLocString](GFF-File-Format#localizedstring) | Waypoint name |
| `Description` | [CExoLocString](GFF-File-Format#localizedstring) | Description (unused) |
| `Comment` | [CExoString](GFF-File-Format#cexostring) | Developer comment/notes |

---

## Map Note Functionality

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
|:------|:-----|:------------|
| `HasMapNote` | Byte | Waypoint has a map note |
| `MapNoteEnabled` | Byte | Map note is initially visible |
| `MapNote` | [CExoLocString](GFF-File-Format#localizedstring) | Text displayed on map |

### Map Notes

- If enabled, shows text on the in-game map
- Can be enabled/disabled via script (`SetMapPinEnabled`)
- Used for quest objectives and locations

---

## Linking & Appearance

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
|:------|:-----|:------------|
| `LinkedTo` | [CExoString](GFF-File-Format#cexostring) | Tag of linked object (unused) |
| `Appearance` | Byte | Appearance type (1=Waypoint) |
| `PaletteID` | Byte | Toolset palette category |

---

## Usage

- **Spawn Points**: `CreateObject` uses waypoint location
- **Patrols**: AI walks between waypoints
- **Teleport**: `JumpToLocation` targets waypoints
- **Transitions**: Doors/Triggers link to waypoint tags
