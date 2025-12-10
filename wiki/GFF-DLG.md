# DLG (Dialogue)

Part of the [GFF File Format Documentation](GFF-File-Format).

[DLG files](GFF-File-Format#dlg-dialogue) store conversation trees, forming the core of KotOR's narrative interaction. A [dialogue](GFF-File-Format#dlg-dialogue) consists of a hierarchy of Entry nodes (NPC lines) and Reply nodes (Player options), connected by Links.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Conversation format specification, see [Bioware Aurora Conversation Format](Bioware-Aurora-Conversation).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/dlg/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/generics/dlg/)

## Conversation Properties

| field | type | Description |
| ----- | ---- | ----------- |
| `DelayEntry` | Int | Delay before conversation starts |
| `DelayReply` | Int | Delay before player reply options appear |
| `NumWords` | Int | Total word count (unused) |
| `PreventSkipping` | Byte | Prevents skipping dialogue lines |
| `Skippable` | Byte | Allows skipping dialogue |
| `Sound` | [ResRef](GFF-File-Format#gff-data-types) | Background sound loop |
| `AmbientTrack` | Int | Background music track ID |
| `CameraModel` | [ResRef](GFF-File-Format#gff-data-types) | Camera [model](MDL-MDX-File-Format) for cutscenes |
| `ComputerType` | Byte | Interface style (0=Modern, 1=Ancient) |
| `ConversationType` | Byte | 0=Human, 1=Computer, 2=Other |
| `OldHitCheck` | Byte | Legacy hit check flag (unused) |

**Conversation types:**

- **Human**: Cinematic camera, [voice-over](WAV-File-Format) support, standard UI
- **Computer**: Full-screen terminal interface, no [voice-over](WAV-File-Format), green text
- **Other**: Overhead text bubbles (bark strings)

## Script Hooks

| field | type | Description |
| ----- | ---- | ----------- |
| `EndConversation` | [ResRef](GFF-File-Format#gff-data-types) | Fires when conversation ends normally |
| `EndConverAbort` | [ResRef](GFF-File-Format#gff-data-types) | Fires when conversation is aborted |

## [node](MDL-MDX-File-Format#node-structures) Lists

[DLG](GFF-File-Format#dlg-dialogue) files use two main lists for [nodes](MDL-MDX-File-Format#node-structures) and one for starting points:

| List field | Contains | Description |
| ---------- | -------- | ----------- |
| `EntryList` | DLGEntry | NPC dialogue lines |
| `ReplyList` | DLGReply | Player response options |
| `StartingList` | DLGLink | Entry points into the [dialogue tree](GFF-File-Format#dlg-dialogue) |

**Graph structure:**

- **StartingList** links to **EntryList** nodes (NPC starts)
- **EntryList** [nodes](MDL-MDX-File-Format#node-structures) link to **ReplyList** nodes (Player responds)
- **ReplyList** [nodes](MDL-MDX-File-Format#node-structures) link to **EntryList** nodes (NPC responds)
- Links can be conditional (Script checks)

## DLGNode Structure (Entries & Replies)

Both Entry and Reply [nodes](MDL-MDX-File-Format#node-structures) share common fields:

| field | type | Description |
| ----- | ---- | ----------- |
| `Text` | [CExoLocString](GFF-File-Format#gff-data-types) | Dialogue text |
| `VO_ResRef` | [ResRef](GFF-File-Format#gff-data-types) | Voice-over audio file |
| `Sound` | [ResRef](GFF-File-Format#gff-data-types) | Sound effect [ResRef](GFF-File-Format#gff-data-types) |
| `Script` | [ResRef](GFF-File-Format#gff-data-types) | Script to execute (Action) |
| `Delay` | Int | Delay before text appears |
| `Comment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment |
| `Speaker` | [CExoString](GFF-File-Format#gff-data-types) | Speaker tag (Entry only) |
| `Listener` | [CExoString](GFF-File-Format#gff-data-types) | Listener tag (unused) |
| `Quest` | [CExoString](GFF-File-Format#gff-data-types) | Journal tag to update |
| `QuestEntry` | Int | [journal entry](GFF-File-Format#jrl-journal) ID |
| `PlotIndex` | Int | Plot index (legacy) |
| `PlotXPPercentage` | Float | XP reward percentage |

**Cinematic fields:**

- `CameraAngle`: Camera angle ID
- `CameraID`: Specific camera ID
- `CameraAnimation`: [animation](MDL-MDX-File-Format#animation-header) to play
- `CamFieldOfView`: Camera FOV
- `CamHeightOffset`: Camera height
- `CamVidEffect`: Video effect ID

**[animation](MDL-MDX-File-Format#animation-header) List:**

- List of [animations](MDL-MDX-File-Format#animation-header) to play on participants
- `Participant`: Tag of object to animate
- `Animation`: [animation](MDL-MDX-File-Format#animation-header) ID

## DLGLink structure

Links connect [nodes](MDL-MDX-File-Format#node-structures) and define flow control:

| field | type | Description |
| ----- | ---- | ----------- |
| `Index` | Int | index of target [node](MDL-MDX-File-Format#node-structures) in Entry/Reply list |
| `Active` | [ResRef](GFF-File-Format#gff-data-types) | Conditional script (returns TRUE/FALSE) |
| `Script` | [ResRef](GFF-File-Format#gff-data-types) | Action script (executed on transition) |
| `IsChild` | Byte | 1 if linking to [node](MDL-MDX-File-Format#node-structures) in list, 0 if logic link |
| `LinkComment` | [CExoString](GFF-File-Format#gff-data-types) | Developer comment |

**Conditional Logic:**

- **Active** script determines if link is available
- If script returns FALSE, link is skipped
- Engine evaluates links top-to-bottom
- First valid link is taken (for NPC lines)
- All valid links displayed (for Player replies)

**KotOR 2 Logic Extensions:**

- `Logic`: 0=AND, 1=OR (combines Active conditions)
- `Not`: Negates condition result

## Implementation Notes

**Flow Evaluation:**

1. Conversation starts
2. Engine evaluates `StartingList` links
3. First link with valid `Active` condition is chosen
4. Transition to target `EntryList` [node](MDL-MDX-File-Format#node-structures)
5. Execute Entry `Script`, play `VO`, show `Text`
6. Evaluate Entry's links to `ReplyList`
7. Display all valid Replies to player
8. Player selects Reply
9. Transition to target `ReplyList` [node](MDL-MDX-File-Format#node-structures)
10. Evaluate Reply's links to `EntryList`
11. Loop until no links remain or `EndConversation` called

**Computer Dialogues:**

- `ComputerType=1` (Ancient) changes font/background
- No cinematic cameras
- Used for terminals and datapads

**Bark strings:**

- `ConversationType=2`
- No cinematic mode, text floats over head
- Non-blocking interaction

**Journal Integration:**

- `Quest` and `QuestEntry` fields update [journal entries](GFF-File-Format#jrl-journal) directly
- Eliminates need for scripts to update quests

## Twine Interoperability

PyKotor exposes a Twine bridge for DLGs to support authoring and visualization in story tools:

- Export uses `Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/twine.py::_dlg_to_story` to turn starters, entries, and replies into `TwinePassage` objects. It emits unique names for duplicate speakers, preserves `is_child` and `Active` script on links, and writes KotOR metadata into `PassageMetadata.custom` (camera anim/angle/id, fade type, quest, sound, VO, plus `text_<language>_<gender>` variants).
- Import uses `Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/twine.py::_story_to_dlg` together with `FormatConverter.restore_kotor_metadata` to hydrate `DLGEntry`/`DLGReply` objects, restoring multilingual text from `custom` keys and mapping camera/sound/quest metadata back onto the [nodes](MDL-MDX-File-Format#node-structures).
- Twine-only data (style, script, tag colors, format info, zoom, creator metadata) is stored in `[DLG](GFF-File-Format#dlg-dialogue).comment` as JSON via `FormatConverter.store_twine_metadata` and restored on export; `tag_colors` [ARE](GFF-File-Format#are-area) kept as `Color` values (see `Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/twine_data.py`).
- Start [node](MDL-MDX-File-Format#node-structures) selection mirrors engine behavior: first starter becomes `startnode` when exporting, and missing `startnode` on import falls back to the first entry passage.
