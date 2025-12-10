# PTH (Path)

Part of the [GFF File Format Documentation](GFF-File-Format).

PTH [files](GFF-File-Format) define pathfinding [data](GFF-File-Format#file-structure) for modules, distinct from the navigation mesh ([walkmesh](BWM-File-Format)). They store a network of waypoints and connections used for high-level AI navigation planning.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/pth.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/pth.py)

## Path Points

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `Path_Points` | List | List of navigation [nodes](MDL-MDX-File-Format#node-structures) |

**Path_Points Struct [fields](GFF-File-Format#file-structure):**

- `X` (Float): X [coordinate](GFF-File-Format#are-area)
- `Y` (Float): Y [coordinate](GFF-File-Format#are-area)
- `Z` (Float): Z Coordinate (unused/flat)

## Path Connections

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `Path_Connections` | List | List of [edges](BWM-File-Format#edges) between [nodes](MDL-MDX-File-Format#node-structures) |

**Path_Connections Struct [fields](GFF-File-Format#file-structure):**

- `Path_Source` (Int): [index](2DA-File-Format#row-labels) of source point
- `Path_Dest` (Int): [index](2DA-File-Format#row-labels) of destination point

## Usage

- **AI Navigation**: Used by NPCs to plot paths across large distances or complex areas where straight-line [walkmesh](BWM-File-Format) navigation fails.
- **Legacy Support**: Often redundant in modern engines with navigation [meshes](MDL-MDX-File-Format#trimesh-header), but used in Aurora/Odyssey for optimization.
- **Editor**: Visualized as a web of lines connecting [nodes](MDL-MDX-File-Format#node-structures).

---
