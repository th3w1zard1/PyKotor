# Indoor Map Builder - User Guide

## Overview

The Indoor Map Builder is a visual editor for creating indoor modules (areas) for Knights of the Old Republic. It allows you to place room components, connect them with doors, and build complete playable modules without manually editing game files.

## Getting Started

### Opening the Editor

1. Launch Holocron Toolset
2. Navigate to **Tools** → **Indoor Map Builder**
3. Select your game installation when prompted

### Creating a New Map

1. Click **File** → **New** (or press `Ctrl+N`)
2. Configure your module settings:
   - **Module ID**: The warp code used in-game (e.g., `test01`)
   - **Name**: Display name for the module
   - **Lighting**: Ambient lighting color
   - **Skybox**: Optional skybox model
3. Click **OK** to start building

### Opening an Existing Map

1. Click **File** → **Open** (or press `Ctrl+O`)
2. Select a `.indoor` file
3. The map will load with all rooms and connections

## Interface Overview

### Left Sidebar

- **Preview**: Shows a preview image of the selected component
- **Kits**: Traditional kit-based components (deprecated, use Modules instead)
- **Modules**: Components extracted from game modules (recommended)
- **Options**: Grid and snap settings
- **Walkmesh Painter**: Material painting tools

### Status Bar

The bottom status bar now mirrors the Module Designer style and updates live as you work:

- **Coords**: World X/Y under the cursor
- **Hover**: Room under the cursor (if any)
- **Selected**: Hook details when a hook is selected, otherwise the count of selected rooms
- **Keys/Buttons**: Currently held keyboard modifiers and mouse buttons
- **Status**: Paint mode/material, colorization, and active snap modes (grid/hook)

### Main Canvas

The central area where you place and arrange rooms. Use mouse and keyboard controls to navigate and edit.

## Basic Operations

### Placing Rooms

1. **From Modules** (Recommended):
   - Expand the **Modules** section
   - Select a module from the dropdown
   - Choose a component from the list
   - Click on the canvas to place it

2. **From Kits** (Legacy):
   - Expand the **Kits** section
   - Select a kit from the dropdown
   - Choose a component from the list
   - Click on the canvas to place it

### Moving Rooms

- **Click and drag** a room to move it
- **Shift + Click** to select multiple rooms
- **Ctrl + Drag** to pan the camera instead

### Rotating Rooms

- **Scroll wheel** (without Ctrl) to rotate the selected component
- **Right-click** → **Rotate** → Choose angle (90°, 180°, 270°)
- **R key** to rotate selected rooms by the rotation snap amount

### Flipping Rooms

- **Right-click** → **Flip** → **Flip Horizontal** or **Flip Vertical**
- **F key** to quickly flip selected rooms horizontally

### Connecting Rooms

Rooms automatically connect when their **hooks** (red/green circles) are close together:

- **Red hooks**: Unconnected
- **Green hooks**: Connected to another room
- **Blue hooks**: Currently selected

Hooks snap together when you move rooms near each other (if **Snap to Hooks** is enabled).

### Selecting Rooms

- **Click** a room to select it
- **Shift + Click** to add to selection
- **Ctrl + A** to select all rooms
- **Escape** to deselect all
- **Double-click** a room to select all connected rooms

### Deleting Rooms

- Select room(s) and press **Delete**
- Or right-click → **Delete**

### Duplicating Rooms

- Select room(s) and press **Ctrl+D**
- Or right-click → **Duplicate**

## Camera Controls

- **Middle Mouse Button + Drag**: Pan camera
- **Ctrl + Left Mouse Button + Drag**: Pan camera
- **Ctrl + Right Mouse Button + Drag**: Rotate camera
- **Ctrl + Scroll Wheel**: Zoom in/out
- **Home**: Reset view to origin
- **F**: Center view on selected rooms

## Grid and Snapping

### Grid Snap

- **Toggle**: Press **G** or check **Snap to Grid (G)**
- **Grid Size**: Adjust in Options panel
- Snaps room positions to grid lines

### Hook Snap

- **Toggle**: Press **H** or check **Snap to Hooks (H)**
- Automatically aligns room hooks when placing or moving
- **Soft snapping**: Hooks disconnect if you drag far enough away

### Rotation Snap

- Set in **Options** → **Rotation Snap**
- Default: 15°
- Scroll wheel rotation uses this increment

## Walkmesh Painting

The walkmesh painter allows you to change surface materials (walkable/non-walkable areas) on room walkmeshes.

### Enabling Paint Mode

1. Expand **Walkmesh Painter** section
2. Check **Enable Painting (P)** (or press **P**)
3. Select a material from the list

### Painting Materials

- **Shift + Left-click and drag** on walkmesh faces to paint (prevents accidental dragging/selection)
- Materials are colorized by default (toggle with **Colorize Materials**)
- Each material has a distinct color for easy identification

### Resetting Walkmesh

- Select room(s) with modified walkmeshes
- Click **Reset Selected** to revert to original materials

### Material Types

- **Walkable**: Dirt, Grass, Stone, Wood, Water, Carpet, Metal, etc.
- **Non-walkable**: Obscuring, Non-walk, Transparent, Lava, Bottomless Pit, etc.
- **Special**: Door, Trigger

## Advanced Features

### Warp Point

The green crosshair indicates where players spawn when entering the module.

- **Right-click** → **Set Warp Point Here**
- **Click and drag** the warp point to move it
- Grid snap applies if enabled

### Hooks

Hooks are connection points between rooms. You can edit them:

- **Right-click on hook** → **Select Hook** to select it
- **Right-click on hook** → **Delete Hook** to remove it
- **Right-click on hook** → **Duplicate Hook** to copy it
- **Right-click on empty space** → **Add Hook Here** to create a new hook
- **Click and drag** a selected hook to move it
- **Delete / Ctrl+D** act on the selected hook if one is selected; otherwise they act on selected rooms

### Marquee Selection

- **Click and drag** on empty space to create a selection box
- All rooms within the box will be selected
- **Shift + Drag** to add to existing selection

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New map |
| `Ctrl+O` | Open map |
| `Ctrl+S` | Save map |
| `Ctrl+Shift+S` | Save as |
| `Ctrl+B` | Build module |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+X` | Cut |
| `Ctrl+C` | Copy |
| `Ctrl+V` | Paste |
| `Ctrl+D` | Duplicate |
| `Ctrl+A` | Select all |
| `Escape` | Deselect all |
| `Delete` | Delete selected |
| `G` | Toggle grid snap |
| `H` | Toggle hook snap |
| `P` | Toggle paint mode |
| `R` | Rotate selected |
| `F` | Flip selected / Center on selection |
| `Home` | Reset view |
| `F1` | Help |

## Building Your Module

Once your map is complete:

1. Click **File** → **Build Module** (or press `Ctrl+B`)
2. Wait for the build process to complete
3. The module will be saved to your installation's modules folder
4. You can warp to it in-game using: `warp <module_id>`

### Build Output

The build process creates:

- **Module file** (`.mod`): Contains all resources (models, textures, walkmeshes, etc.)
- **Layout file** (`.lyt`): Room positions and door connections
- **Visibility file** (`.vis`): Room visibility relationships
- **Area file** (`.are`): Area properties and settings
- **Game Info file** (`.git`): Doors and placeables
- **Module Info file** (`.ifo`): Module metadata

## Tips and Best Practices

1. **Use Modules instead of Kits**: The Modules system extracts components directly from game modules, ensuring compatibility and accuracy.

2. **Snap to Hooks**: Keep this enabled when connecting rooms to ensure proper door placement.

3. **Check Connections**: Green hooks indicate successful connections. Red hooks need to be connected.

4. **Test Walkability**: Use the walkmesh painter to mark non-walkable areas (lava, pits, etc.) before building.

5. **Organize Your Layout**: Use the grid to keep rooms aligned and organized.

6. **Save Frequently**: The editor supports undo/redo, but saving regularly prevents data loss.

7. **Test in Game**: Always test your module in-game after building to verify connections and walkability.

## Troubleshooting

### Rooms Not Connecting

- Ensure hooks are close together (within ~1.5 units)
- Check that **Snap to Hooks** is enabled
- Verify both rooms have compatible door types

### Missing Components

- If a module component is missing, the module may be corrupted or incomplete
- Try using a different module or component
- Check the error messages in the status bar

### Build Failures

- Ensure all rooms have valid walkmeshes
- Check that module ID is valid (alphanumeric, no spaces)
- Verify installation path is correct

### Performance Issues

- Large maps with many rooms may be slow
- Disable material colorization for better performance
- Close other applications to free up memory

## Related Documentation

- [Indoor Map Builder - Implementation Guide](Indoor-Map-Builder-Implementation-Guide.md) - Technical details for developers
- [LYT File Format](LYT-File-Format.md) - Layout file structure
- [BWM File Format](BWM-File-Format.md) - Walkmesh file structure
