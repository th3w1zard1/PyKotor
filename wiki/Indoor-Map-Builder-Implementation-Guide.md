# Indoor Map Builder - Implementation Guide

## Architecture Overview

The Indoor Map Builder is a complex system that combines several subsystems:

1. **Data Layer**: `IndoorMap`, `IndoorMapRoom`, `Kit`, `KitComponent` - Core data structures
2. **UI Layer**: `IndoorMapBuilder`, `IndoorMapRenderer` - Qt-based user interface
3. **Kit System**: Kit loading and component management
4. **Module Converter**: Converts game modules to kit-like components
5. **Build System**: Converts map data to game module files
6. **Rendering System**: 2D top-down view with walkmesh visualization

## Core Data Structures

### IndoorMap

The root data structure representing a complete indoor module.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoormap.py`

**Key Properties**:

- `rooms: list[IndoorMapRoom]` - All rooms in the map
- `module_id: str` - Module identifier (warp code)
- `name: LocalizedString` - Module display name
- `lighting: Color` - Ambient lighting color
- `skybox: str` - Optional skybox model name
- `warp_point: Vector3` - Player spawn location

**Key Methods**:

- `write() -> bytes`: Serializes map to JSON format
- `load(raw: bytes, kits: list[Kit]) -> list[MissingRoomInfo]`: Loads map from JSON
- `build(installation, kits, output_path)`: Builds complete module files
- `rebuild_room_connections()`: Recalculates room hook connections

**File Format** (`.indoor`):

```json
{
  "module_id": "test01",
  "name": {"stringref": -1, "0": "New Module"},
  "lighting": [0.5, 0.5, 0.5],
  "skybox": "",
  "warp": "test01",
  "rooms": [
    {
      "position": [0.0, 0.0, 0.0],
      "rotation": 0.0,
      "flip_x": false,
      "flip_y": false,
      "kit": "kit_name",
      "component": "component_name",
      "walkmesh_override": "base64_encoded_bwm_data"
    }
  ]
}
```

### IndoorMapRoom

Represents a single room instance placed in the map.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoormap.py`

**Key Properties**:

- `component: KitComponent` - The component template
- `position: Vector3` - World position
- `rotation: float` - Rotation in degrees
- `flip_x: bool` - Horizontal flip
- `flip_y: bool` - Vertical flip
- `hooks: list[IndoorMapRoom | None]` - Connected rooms (by hook index)
- `walkmesh_override: BWM | None` - Custom walkmesh (for painting)

**Key Methods**:

- `hook_position(hook, world_offset=True) -> Vector3`: Calculates hook world position
- `rebuild_connections(rooms)`: Rebuilds hook connections
- `walkmesh() -> BWM`: Returns transformed walkmesh
- `base_walkmesh() -> BWM`: Returns untransformed walkmesh (honors override)
- `ensure_walkmesh_override() -> BWM`: Creates writable override copy

**Connection System**:

- Hooks connect when within 0.001 units of each other
- Connections are bidirectional (room1.hooks[i] = room2, room2.hooks[j] = room1)
- Rebuilt automatically when rooms move

### Kit

A collection of reusable room components.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py`

**Key Properties**:

- `name: str` - Kit name
- `components: list[KitComponent]` - Available components
- `doors: list[KitDoor]` - Door types
- `textures: CaseInsensitiveDict[bytes]` - Texture data
- `lightmaps: CaseInsensitiveDict[bytes]` - Lightmap data
- `txis: CaseInsensitiveDict[bytes]` - Texture info data
- `always: dict[Path, bytes]` - Always-included resources
- `side_padding: dict[int, dict[int, MDLMDXTuple]]` - Door width padding models
- `top_padding: dict[int, dict[int, MDLMDXTuple]]` - Door height padding models
- `skyboxes: dict[str, MDLMDXTuple]` - Skybox models

**Loading**:

- Loaded from JSON files in `./kits/` directory
- Each kit has a directory with components, textures, lightmaps, etc.
- See `indoorkit_loader.py` for loading implementation

### KitComponent

A reusable room template.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py`

**Key Properties**:

- `kit: Kit` - Parent kit
- `name: str` - Component name
- `image: QImage` - Preview image (128x128 or larger)
- `bwm: BWM` - Walkmesh data
- `mdl: bytes` - Model data
- `mdx: bytes` - Model extension data
- `hooks: list[KitComponentHook]` - Connection points

### KitComponentHook

A connection point on a component.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py`

**Key Properties**:

- `position: Vector3` - Local position (relative to component center)
- `rotation: float` - Rotation in degrees
- `edge: str` - Edge index (for transition remapping)
- `door: KitDoor` - Door type for this hook

**Coordinate System**:

- Hooks use **local coordinates** (centered at origin)
- Transformed to world coordinates via `IndoorMapRoom.hook_position()`
- Transformation order: flip → rotate → translate

### KitDoor

Defines a door type with K1/K2 variants.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py`

**Key Properties**:

- `utd_k1: UTD` - K1 door blueprint
- `utd_k2: UTD` - K2 door blueprint
- `width: float` - Door width
- `height: float` - Door height

## Module Converter System

The module converter allows using game modules as component sources.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoorkit/module_converter.py`

### ModuleKit

A dynamically-generated kit from a game module.

**Key Features**:

- Lazy loading: Only loads when selected
- Extracts rooms from module LYT files
- Generates preview images from walkmeshes
- Extracts hooks from BWM transition edges

**Loading Process**:

1. Load module using `Module` class
2. Extract LYT resource
3. For each LYT room:
   - Load WOK (walkmesh) resource
   - Re-center BWM to origin (critical for alignment)
   - Generate preview image from BWM
   - Extract hooks from BWM transitions
   - Create `KitComponent`

**BWM Re-centering**:

- Game BWMs are stored in world coordinates
- Indoor Map Builder expects BWMs centered at origin
- `_recenter_bwm()` calculates bounding box and translates to origin
- Ensures preview image and walkmesh align correctly

**Preview Image Generation**:

- Matches `kit.py:_generate_component_minimap()` exactly
- 10 pixels per unit scale
- Format_RGB888
- Minimum 256x256 pixels
- Mirrored to match kit loader behavior

### ModuleKitManager

Manages lazy loading and caching of ModuleKits.

**Key Methods**:

- `get_module_roots() -> list[str]`: Lists available modules
- `get_module_display_name(module_root) -> str`: Gets display name
- `get_module_kit(module_root) -> ModuleKit`: Gets or creates kit
- `clear_cache()`: Frees memory

## Build Process

The build process converts `IndoorMap` data to game module files.

**Location**: `Tools/HolocronToolset/src/toolset/data/indoormap.py:build()`

### Build Steps

1. **Initialize Resources**:
   - Create ERF (module archive)
   - Create LYT (layout)
   - Create VIS (visibility)
   - Create ARE (area)
   - Create IFO (module info)
   - Create GIT (game instance template)

2. **Process Rooms**:
   - Add rooms to VIS graph
   - Process room components (textures, models, lightmaps)
   - Handle texture renaming (avoid conflicts)
   - Process lightmaps (rename, load from installation if missing)
   - Process BWM (flip, rotate, translate, remap transitions)
   - Add models and walkmeshes to ERF

3. **Handle Doors**:
   - Generate door insertions from room connections
   - Create GIT door objects
   - Create UTD door blueprints
   - Add door padding models (for height/width mismatches)
   - Add doorhooks to LYT

4. **Process Skybox**:
   - Load skybox model from kits
   - Add to LYT and VIS

5. **Generate Minimap**:
   - Render top-down view of all rooms
   - Create 512x256 TPC texture
   - Set ARE map points

6. **Finalize**:
   - Set ARE attributes (lighting, name, map points)
   - Set IFO attributes (module ID, entry point)
   - Write all resources to ERF file

### Texture Renaming

Textures are renamed to avoid conflicts:

- Pattern: `{module_id}_tex{N}`
- All references updated in models and TXI files

### Lightmap Processing

Lightmaps are processed per-room:

- Renamed: `{module_id}_lm{N}`
- Loaded from kit first, then installation if missing
- TXI files included if available

### BWM Processing

Each room's BWM is transformed:

1. Deep copy (preserve original)
2. Apply flip (if `flip_x` or `flip_y`)
3. Apply rotation
4. Apply translation (room position)
5. Remap transition indices (connect to actual room indices)

### Door Insertions

Doors are inserted at hook connection points:

- One door per hook pair
- Door type chosen from larger door (width/height)
- Static doors for unconnected hooks
- Padding models added for size mismatches

## Rendering System

The renderer provides a 2D top-down view of the map.

**Location**: `Tools/HolocronToolset/src/toolset/gui/windows/indoor_builder.py:IndoorMapRenderer`

### Coordinate Systems

**World Coordinates**: Game world space (X, Y, Z)

- Rooms positioned in world space
- Walkmeshes in world space after transformation

**Screen Coordinates**: Widget pixel coordinates (X, Y)

- Mouse position
- Widget size

**Render Coordinates**: Transformed screen coordinates

- Camera transform applied
- Rotation, scale, translation

### Camera System

**Properties**:

- `_cam_position: Vector2` - Camera center in world space
- `_cam_rotation: float` - Camera rotation in radians
- `_cam_scale: float` - Zoom level

**Transform Pipeline**:

1. Translate to center
2. Rotate by camera rotation
3. Scale by zoom
4. Translate by camera position

### Rendering Loop

**Optimization**: Only repaints when dirty

- `_dirty: bool` flag
- `mark_dirty()` called on changes
- ~60 FPS target (16ms timer)

**Render Order**:

1. Background
2. Grid (if enabled)
3. Room walkmeshes
4. Hook markers (red = unconnected, green = connected, blue = selected)
5. Connection lines
6. Cursor preview
7. Snap indicator (anchored at the actual hook snap point)
8. Hover highlight
9. Selection highlights
10. Warp point
11. Marquee selection

### Status Bar

**Location**: `IndoorMapBuilder._setup_status_bar()` / `_update_status_bar()`

- Mirrors the Module Designer style (rich text, emoji-friendly).
- Displays:
  - **Coords**: World X/Y under cursor.
  - **Hover**: Room under cursor (if any).
  - **Selection**: Selected hook (room + index) or selected room count.
  - **Keys/Buttons**: Currently held keyboard modifiers and mouse buttons.
  - **Status**: Paint mode/material, colorization flag, snap modes (grid/hook).
- Updated from renderer mouse/scroll/press/release signals via a callback set on `IndoorMapRenderer`.

### Walkmesh Visualization

Rooms rendered using walkmesh geometry (not preview images):

- Each face colored by material
- Walkable: Light gray
- Non-walkable: Dark gray
- Colorized: Material-specific colors (if enabled)

### Hook Editing (Renderer/UI)

- Hooks rendered on the walkmesh for placed rooms and cursor preview.
- Context menu actions: Add Hook Here, Select Hook, Delete Hook, Duplicate Hook.
- Hooks are draggable once selected (behavior mirrors warp-point drag).
- Delete/Duplicate hotkeys act on the selected hook if one is selected; otherwise they act on selected rooms.
- Editing hooks on a room that shares a component clones the component for that room so other rooms stay unchanged.

### Snapping System

**Grid Snap**:

- Snaps positions to grid lines
- Grid size configurable

**Hook Snap**:

- Finds closest hook pair within threshold
- Calculates snap position (aligns hooks)
- Soft snapping: Disconnects if dragged away (threshold scales with zoom, intentionally easy to break free)

**Snap Calculation**:

```python
# For hook A on room1 and hook B on room2:
# Position room1 so hook A aligns with hook B's world position
snapped_pos = hook_b_world - hook_a_local
```

## Undo/Redo System

Uses Qt's `QUndoStack` for command pattern.

**Location**: `Tools/HolocronToolset/src/toolset/gui/windows/indoor_builder.py`

### Command Classes

- `AddRoomCommand`: Add room to map
- `DeleteRoomsCommand`: Remove rooms
- `MoveRoomsCommand`: Move rooms
- `RotateRoomsCommand`: Rotate rooms
- `FlipRoomsCommand`: Flip rooms
- `DuplicateRoomsCommand`: Duplicate rooms
- `MoveWarpCommand`: Move warp point
- `PaintWalkmeshCommand`: Paint walkmesh materials
- `ResetWalkmeshCommand`: Reset walkmesh overrides

### Command Pattern

Each command implements:

- `undo()`: Revert changes
- `redo()`: Apply changes
- Stores old/new states

## Walkmesh Painting

Allows editing surface materials on room walkmeshes.

### Input

- Painting requires **Shift + Left-click** to avoid conflicting with selection/dragging in the editor.

### Painting Process

1. **Begin Stroke**: `_begin_paint_stroke()`
   - Records original materials
   - Clears stroke data

2. **Apply Paint**: `_apply_paint_at_world()`
   - Picks face under cursor
   - Creates walkmesh override if needed
   - Changes material
   - Records in stroke

3. **Finish Stroke**: `_finish_paint_stroke()`
   - Creates `PaintWalkmeshCommand`
   - Pushes to undo stack

### Walkmesh Overrides

- `walkmesh_override: BWM | None` on `IndoorMapRoom`
- Created on first paint (deep copy of original)
- Preserved in save/load (base64 encoded)
- Can be reset to revert to original

## Hook System

Hooks are connection points between rooms.

### Hook Types

- **Component Hooks**: Defined in `KitComponent` (template)
- **Room Hooks**: Connections in `IndoorMapRoom.hooks` (instances)

### Connection Algorithm

```python
def rebuild_connections(room, all_rooms):
    for hook in room.component.hooks:
        hook_world_pos = room.hook_position(hook)
        for other_room in all_rooms:
            for other_hook in other_room.component.hooks:
                other_hook_world_pos = other_room.hook_position(other_hook)
                if distance(hook_world_pos, other_hook_world_pos) < 0.001:
                    room.hooks[hook_index] = other_room
```

### Hook Editing

Hooks can be edited per-room:

- `_ensure_room_component_unique()`: Clones component if shared
- `add_hook_at()`: Adds new hook at world position
- `delete_hook()`: Removes hook
- `duplicate_hook()`: Copies hook

## File I/O

### Save Format

`.indoor` files are JSON:

- Human-readable
- Base64-encoded walkmesh overrides
- Preserves all room properties

### Load Process

1. Parse JSON
2. Find kits/components by name
3. Create `IndoorMapRoom` instances
4. Load walkmesh overrides (if present)
5. Rebuild connections
6. Report missing kits/components

## Performance Considerations

### Caching

- **Walkmesh Cache**: `_cached_walkmeshes` in renderer
- Caches transformed walkmeshes per room
- Invalidated on changes

### Lazy Loading

- Module kits loaded on-demand
- Components loaded when module selected
- Preview images generated once

### Rendering Optimization

- Only repaints when dirty
- ~60 FPS target
- Efficient coordinate transforms

## Error Handling

### Missing Resources

- Missing kits: Reported in dialog
- Missing components: Skipped, reported
- Missing files: Collected, reported at end

### Build Failures

- Graceful degradation (skip missing lightmaps)
- Error messages logged
- Build continues with available resources

## Testing

### Unit Tests

- Data structure serialization
- Coordinate transformations
- Connection algorithms

### Integration Tests

- Build process end-to-end
- Module conversion
- File I/O

## References

### Code Locations

- **Data Structures**: `Tools/HolocronToolset/src/toolset/data/indoormap.py`
- **Kit System**: `Tools/HolocronToolset/src/toolset/data/indoorkit/`
- **UI**: `Tools/HolocronToolset/src/toolset/gui/windows/indoor_builder.py`
- **Module Converter**: `Tools/HolocronToolset/src/toolset/data/indoorkit/module_converter.py`

### Related Documentation

- [LYT File Format](LYT-File-Format.md)
- [BWM File Format](BWM-File-Format.md)
- [GFF File Format](GFF-File-Format.md)
- [ERF File Format](ERF-File-Format.md)

### Vendor References

- `vendor/reone/` - Engine implementation
- `vendor/kotor.js/` - JavaScript implementation
- `vendor/xoreos/` - C++ implementation
