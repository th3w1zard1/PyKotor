# Missing Blender IPC Features Analysis

## Overview

This document identifies functionality in `module_designer.py` that should be synchronized with Blender via IPC but is currently missing.

## Currently Implemented ✅

- Selection synchronization (bidirectional)
- Transform changes from Blender → Toolset
- Instance add/remove from Blender → Toolset
- Property updates from Blender → Toolset
- Context menu requests from Blender
- Module loading into Blender

## Missing Features ❌

### 1. Instance Visibility Toggles

**Location**: `update_toggles()` method (line 1630)

**Issue**: When user toggles visibility checkboxes (creatures, placeables, doors, etc.), changes only affect the internal renderer, not Blender.

**What needs to sync**:

- `hide_creatures`
- `hide_placeables`
- `hide_doors`
- `hide_triggers`
- `hide_encounters`
- `hide_waypoints`
- `hide_sounds`
- `hide_stores`
- `hide_cameras`

**Required Changes**:

- Add `set_visibility` command to `BlenderCommands` (IPC client)
- Add `set_visibility` handler in `kotorblender/ipc/handlers.py`
- Call `_blender_controller.set_visibility(...)` in `update_toggles()` when Blender mode is active

### 2. Render Settings

**Location**: `update_toggles()` method (line 1645-1647)

**Issue**: Render settings like backface culling, lightmap usage, and cursor visibility don't sync to Blender.

**What needs to sync**:

- `backface_culling`
- `use_lightmap`
- `show_cursor`

**Required Changes**:

- Add `set_render_settings` command to `BlenderCommands`
- Add handler in `kotorblender/ipc/handlers.py`
- Sync in `update_toggles()` when Blender mode is active

### 3. Toolset → Blender Instance Operations

**Location**: Multiple methods

**Issue**: When instances are modified in the toolset (not from Blender), changes don't sync back to Blender.

**Methods needing sync**:

- `add_instance()` (line 1652) - Should call `add_instance_to_blender()` ✅ (already exists in mixin)
- `delete_selected()` (line 1877) - Should remove from Blender
- `move_selected()` (line 1899) - Should update positions in Blender
- `rotate_selected()` (line 1929) - Should update rotations in Blender

**Required Changes**:

- `delete_selected()`: Call `remove_instance_from_blender()` for each deleted instance
- `move_selected()`: Call `sync_instance_to_blender()` after position changes
- `rotate_selected()`: Call `sync_instance_to_blender()` after rotation changes
- Ensure these only sync when NOT in `_selection_sync_in_progress` to avoid loops

### 4. Camera Operations

**Location**: Camera snap methods (lines 1776, 1797, 1813, 1835)

**Issue**: Camera operations in toolset don't sync to Blender's viewport.

**Methods needing sync**:

- `snap_camera_to_view()` - Sync GIT camera position/orientation to Blender
- `snap_view_to_git_camera()` - Sync Blender viewport to match GIT camera
- `snap_view_to_git_instance()` - Sync Blender viewport to instance position
- `snap_camera_to_entry_location()` - Sync camera to entry point

**Required Changes**:

- Add `set_camera_view` command to `BlenderCommands` (for viewport sync)
- Add `update_camera_instance` command (for GIT camera sync)
- Add handlers in `kotorblender/ipc/handlers.py`
- Implement camera sync in these methods when Blender mode is active

### 5. Layout (LYT) Editing

**Location**: Layout tab handlers (lines 2310-2620)

**Issue**: LYT changes (rooms, door hooks, tracks, obstacles) don't sync to Blender.

**Methods needing sync**:

- `on_add_room()` - Should add room to Blender
- `on_add_door_hook()` - Should add door hook to Blender
- `on_add_track()` - Should add track to Blender
- `on_add_obstacle()` - Should add obstacle to Blender
- `on_room_position_changed()` - Should update room position in Blender
- `on_room_model_changed()` - Should update room model in Blender
- `on_doorhook_room_changed()` - Should update door hook in Blender
- `on_doorhook_name_changed()` - Should update door hook name in Blender
- `duplicate_lyt_element()` - Should duplicate in Blender
- `delete_lyt_element()` - Should delete from Blender

**Required Changes**:

- Add LYT editing commands to `BlenderCommands`:
  - `add_door_hook()`
  - `add_track()`
  - `add_obstacle()`
  - `update_door_hook()`
  - `update_track()`
  - `update_obstacle()`
  - `remove_lyt_element()`
- Add handlers in `kotorblender/ipc/handlers.py`
- Sync in all LYT editing methods when Blender mode is active

### 6. Undo/Redo Synchronization

**Location**: `undo_stack` operations throughout

**Issue**: When undo/redo happens in toolset, Blender's undo stack should be notified to stay in sync.

**Required Changes**:

- Hook into `undo_stack.indexChanged` signal
- Call `_blender_controller.undo()` or `redo()` when toolset undo/redo occurs
- Ensure Blender → Toolset undo/redo is already handled (check if implemented)

### 7. Instance Property Updates from Toolset

**Location**: `edit_instance()` and property dialogs

**Issue**: When properties are edited in toolset dialogs, changes should sync to Blender.

**Required Changes**:

- After `edit_instance()` completes successfully, call `sync_instance_to_blender()` if properties changed
- May need to track which properties changed to send only updates

## Implementation Priority

### High Priority (Core Functionality)

1. **Instance Visibility Toggles** - Essential for workflow
2. **Toolset → Blender Instance Operations** - Critical for bidirectional editing
3. **Delete/Move/Rotate sync** - Core editing operations

### Medium Priority (User Experience)

4. **Camera Operations** - Improves workflow but not critical
5. **Render Settings** - Nice to have for consistency
6. **Undo/Redo Sync** - Important for data integrity

### Low Priority (Advanced Features)

7. **Layout Editing** - Less commonly used, can be added later
8. **Property Update Sync** - Already handled via transform/property update events

## kotorblender Changes Required

### New IPC Commands Needed

1. `set_visibility` - Set visibility of instance types
2. `set_render_settings` - Update render settings
3. `set_camera_view` - Sync viewport camera
4. `update_camera_instance` - Update GIT camera object
5. `add_door_hook` - Add door hook to layout
6. `add_track` - Add track to layout
7. `add_obstacle` - Add obstacle to layout
8. `update_door_hook` - Update door hook properties
9. `update_track` - Update track properties
10. `update_obstacle` - Update obstacle properties
11. `remove_lyt_element` - Remove LYT element

### Handler Implementation Locations

- `vendor/kotorblender/io_scene_kotor/ipc/handlers.py` - Add command handlers
- `vendor/kotorblender/io_scene_kotor/ipc/sync.py` - May need updates for visibility monitoring

## Additional Findings

### Sync Loop Prevention

Currently, `_selection_sync_in_progress` is used to prevent selection sync loops. We need similar flags for:

- Transform sync (`_transform_sync_in_progress`)
- Property sync (`_property_sync_in_progress`)
- Instance operation sync (`_instance_sync_in_progress`)

### Hook Points for Sync

The `_after_instance_mutation()` method (line 1416) is called after instance changes. This could be a good place to sync to Blender, but must check sync flags to avoid loops.

## Notes

- All sync operations should check `is_blender_mode()` before executing
- Use sync flags (`_selection_sync_in_progress`, `_transform_sync_in_progress`, etc.) to prevent feedback loops
- Consider batching multiple updates to reduce IPC traffic
- Test bidirectional sync carefully to avoid infinite loops
- When syncing from toolset → Blender, set appropriate flags before calling Blender methods
- When receiving from Blender → toolset, check flags before applying changes
