# DLG (Dialogue)

Part of the [GFF File Format Documentation](GFF-File-Format).


DLG files store conversation trees, forming the core of KotOR's narrative interaction. A dialogue consists of a hierarchy of Entry nodes (NPC lines) and Reply nodes (Player options), connected by Links.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Conversation format specification, see [Bioware Aurora Conversation Format](Bioware-Aurora-Conversation).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/dlg/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/generics/dlg/)

## Conversation Properties

| Field | Type | Description |
| ----- | ---- | ----------- |
| `DelayEntry` | Int | Delay before conversation starts |
| `DelayReply` | Int | Delay before player reply options appear |
| `NumWords` | Int | Total word count (unused) |
| `PreventSkipping` | Byte | Prevents skipping dialogue lines |
| `Skippable` | Byte | Allows skipping dialogue |
| `Sound` | ResRef | Background sound loop |
| `AmbientTrack` | Int | Background music track ID |
| `CameraModel` | ResRef | Camera model for cutscenes |
| `ComputerType` | Byte | Interface style (0=Modern, 1=Ancient) |
| `ConversationType` | Byte | 0=Human, 1=Computer, 2=Other |
| `OldHitCheck` | Byte | Legacy hit check flag (unused) |

**Conversation Types:**

- **Human**: Cinematic camera, VO support, standard UI
- **Computer**: Full-screen terminal interface, no VO, green text
- **Other**: Overhead text bubbles (bark strings)

## Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `EndConversation` | ResRef | Fires when conversation ends normally |
| `EndConverAbort` | ResRef | Fires when conversation is aborted |

## Node Lists

DLG files use two main lists for nodes and one for starting points:

| List Field | Contains | Description |
| ---------- | -------- | ----------- |
| `EntryList` | DLGEntry | NPC dialogue lines |
| `ReplyList` | DLGReply | Player response options |
| `StartingList` | DLGLink | Entry points into the dialogue tree |

**Graph Structure:**

- **StartingList** links to **EntryList** nodes (NPC starts)
- **EntryList** nodes link to **ReplyList** nodes (Player responds)
- **ReplyList** nodes link to **EntryList** nodes (NPC responds)
- Links can be conditional (Script checks)

## DLGNode Structure (Entries & Replies)

Both Entry and Reply nodes share common fields:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Text` | CExoLocString | Dialogue text |
| `VO_ResRef` | ResRef | Voice-over audio file |
| `Sound` | ResRef | Sound effect ResRef |
| `Script` | ResRef | Script to execute (Action) |
| `Delay` | Int | Delay before text appears |
| `Comment` | CExoString | Developer comment |
| `Speaker` | CExoString | Speaker tag (Entry only) |
| `Listener` | CExoString | Listener tag (unused) |
| `Quest` | CExoString | Journal tag to update |
| `QuestEntry` | Int | Journal entry ID |
| `PlotIndex` | Int | Plot index (legacy) |
| `PlotXPPercentage` | Float | XP reward percentage |

**Cinematic Fields:**

- `CameraAngle`: Camera angle ID
- `CameraID`: Specific camera ID
- `CameraAnimation`: Animation to play
- `CamFieldOfView`: Camera FOV
- `CamHeightOffset`: Camera height
- `CamVidEffect`: Video effect ID

**Animation List:**

- List of animations to play on participants
- `Participant`: Tag of object to animate
- `Animation`: Animation ID

## DLGLink Structure

Links connect nodes and define flow control:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Index` | Int | Index of target node in Entry/Reply list |
| `Active` | ResRef | Conditional script (returns TRUE/FALSE) |
| `Script` | ResRef | Action script (executed on transition) |
| `IsChild` | Byte | 1 if linking to node in list, 0 if logic link |
| `LinkComment` | CExoString | Developer comment |

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
4. Transition to target `EntryList` node
5. Execute Entry `Script`, play `VO`, show `Text`
6. Evaluate Entry's links to `ReplyList`
7. Display all valid Replies to player
8. Player selects Reply
9. Transition to target `ReplyList` node
10. Evaluate Reply's links to `EntryList`
11. Loop until no links remain or `EndConversation` called

**Computer Dialogues:**

- `ComputerType=1` (Ancient) changes font/background
- No cinematic cameras
- Used for terminals and datapads

**Bark Strings:**

- `ConversationType=2`
- No cinematic mode, text floats over head
- Non-blocking interaction

**Journal Integration:**

- `Quest` and `QuestEntry` fields update JRL directly
- Eliminates need for scripts to update quests

## Twine Interoperability

PyKotor exposes a Twine bridge for DLGs to support authoring and visualization in story tools:

- Export uses `Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/twine.py::_dlg_to_story` to turn starters, entries, and replies into `TwinePassage` objects. It emits unique names for duplicate speakers, preserves `is_child` and `Active` script on links, and writes KotOR metadata into `PassageMetadata.custom` (camera anim/angle/id, fade type, quest, sound, VO, plus `text_<language>_<gender>` variants).
- Import uses `Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/twine.py::_story_to_dlg` together with `FormatConverter.restore_kotor_metadata` to hydrate `DLGEntry`/`DLGReply` objects, restoring multilingual text from `custom` keys and mapping camera/sound/quest metadata back onto the nodes.
- Twine-only data (style, script, tag colors, format info, zoom, creator metadata) is stored in `DLG.comment` as JSON via `FormatConverter.store_twine_metadata` and restored on export; `tag_colors` are kept as `Color` values (see `Libraries/PyKotor/src/pykotor/resource/generics/dlg/io/twine_data.py`).
- Start node selection mirrors engine behavior: first starter becomes `startnode` when exporting, and missing `startnode` on import falls back to the first entry passage.

