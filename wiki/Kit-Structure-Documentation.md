# Kit structure Documentation

Kits are collections of reusable indoor map components for the Holocron Toolset. They contain [room models](LYT-File-Format#room-definitions), [textures](TPC-File-Format), lightmaps, doors, and other resources that can be assembled into complete game modules.

## Table of Contents

- Kit structure Documentation
  - Table of Contents
  - [Kit Overview](#kit-overview)
  - [Kit Directory structure](#kit-directory-structure)
  - [Kit JSON file](#kit-json-file)
  - [Components](#components)
  - [textures and Lightmaps](#textures-and-lightmaps)
    - [texture Extraction](#texture-extraction)
    - [Resource Resolution Priority](#resource-resolution-priority)
    - [TXI files](#txi-files)
    - [Shared Resources](#shared-resources)
  - [Always Folder](#always-folder)
  - [Doors](#doors)
    - [Door Walkmeshes (DWK)](#door-walkmeshes-dwk)
  - [Placeables](#placeables)
    - [Placeable Walkmeshes (PWK)](#placeable-walkmeshes-pwk)
  - [Skyboxes](#skyboxes)
  - [Doorway Padding](#doorway-padding)
  - [models Directory](#models-directory)
  - [Resource Extraction](#resource-extraction)
    - [Archive file Support](#archive-file-support)
    - [Component Identification](#component-identification)
    - [texture and Lightmap Extraction](#texture-and-lightmap-extraction)
    - [Door Extraction](#door-extraction)
    - [walkmesh Extraction](#walkmesh-extraction)
    - [BWM Re-centering](#bwm-re-centering)
    - [Minimap Generation](#minimap-generation)
    - [Doorhook Extraction](#doorhook-extraction)
  - [Implementation Details](#implementation-details)
    - [Kit Class structure](#kit-class-structure)
    - [Kit Loading](#kit-loading)
    - [Indoor Map Generation](#indoor-map-generation)
    - [coordinate System](#coordinate-system)
  - [Kit types](#kit-types)
    - [Component-Based Kits](#component-based-kits)
    - [texture-Only Kits](#texture-only-kits)
  - [Game Engine Compatibility](#game-engine-compatibility)
  - [Vendor Implementation References](#vendor-implementation-references)
    - [Door Walkmesh (DWK) Extraction](#door-walkmesh-dwk-extraction)
    - [Placeable Walkmesh (PWK) Extraction](#placeable-walkmesh-pwk-extraction)
    - [room model and Component Identification](#room-model-and-component-identification)
    - [Door model Resolution](#door-model-resolution)
    - [Placeable model Resolution](#placeable-model-resolution)
    - [Texture and Lightmap Extraction](#texture-and-lightmap-extraction)
    - [Resource Resolution Priority](#resource-resolution-priority)
    - [BWM/WOK walkmesh Handling](#bwmwok-walkmesh-handling)
    - [module archives Loading](#module-archives-loading)
    - [KEY Discrepancies and Rationale](#key-discrepancies-and-rationale)
  - [Test Comparison Precision](#test-comparison-precision)
    - [Exact Matching (1:1 byte-for-byte)](#exact-matching-11-byte-for-byte)
    - [Approximate Matching (Tolerance-Based)](#approximate-matching-tolerance-based)
    - [structure-Only Verification (No value Comparison)](#structure-only-verification-no-value-comparison)
    - [Recommended Test Improvements](#recommended-test-improvements)
  - [Best Practices](#best-practices)

---

## Kit Overview

A kit is a self-contained collection of resources that can be used to build indoor maps. Kits are stored in `Tools/HolocronToolset/src/toolset/kits/kits/` and consist of:

- **Components**: Room models ([MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format)/[WOK](BWM-File-Format)) with hook points for connecting to other rooms
- **[textures](TPC-File-Format)**: TGA [texture files](TPC-File-Format) with optional [TXI](TXI-File-Format) metadata
- **Lightmaps**: TGA lightmap files with optional [TXI](TXI-File-Format) metadata
- **Doors**: [UTD](GFF-File-Format#utd-door) door templates (K1 and K2 versions) with [DWK](BWM-File-Format) [walkmeshes](BWM-File-Format)
- **Placeables**: [UTP](GFF-File-Format#utp-placeable) [placeable templates](GFF-File-Format#utp-placeable) with [PWK](BWM-File-Format) walkmeshes (optional)
- **Skyboxes**: Optional [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [models](MDL-MDX-File-Format) for sky rendering
- **Always Resources**: Static resources included in every generated module
- **[models](MDL-MDX-File-Format)**: Additional [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [models](MDL-MDX-File-Format) referenced by the module but not used as components

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/`](https://github.com/OldRepublicDevs/PyKotor/tree/master/Tools/HolocronToolset/src/toolset/data/indoorkit)

---

## Kit Directory structure

```shell
kits/
├── {kit_id}/
│   ├── {kit_id}.json          # Kit definition file
│   ├── {component_id}.mdl     # Component model files
│   ├── {component_id}.mdx
│   ├── {component_id}.wok     # Component walkmesh (re-centered to origin)
│   ├── {component_id}.png     # Component minimap image (top-down view)
│   ├── textures/              # Texture files
│   │   ├── {texture_name}.tga
│   │   └── {texture_name}.txi
│   ├── lightmaps/             # Lightmap files
│   │   ├── {lightmap_name}.tga
│   │   └── {lightmap_name}.txi
│   ├── always/                # Always-included resources (optional)
│   │   └── {resource_name}.{ext}
│   ├── skyboxes/              # Skybox models (optional)
│   │   ├── {skybox_name}.mdl
│   │   └── {skybox_name}.mdx
│   ├── doorway/               # Door padding models (optional)
│   │   ├── {side|top}_{door_id}_size{size}.mdl
│   │   └── {side|top}_{door_id}_size{size}.mdx
│   ├── models/                # Additional models (optional)
│   │   ├── {model_name}.mdl
│   │   └── {model_name}.mdx
│   ├── {door_name}_k1.utd     # Door templates
│   ├── {door_name}_k2.utd
│   ├── {door_model}0.dwk      # Door walkmeshes (3 states: 0=closed, 1=open1, 2=open2)
│   ├── {door_model}1.dwk
│   ├── {door_model}2.dwk
│   └── {placeable_model}.pwk  # Placeable walkmeshes (optional)
```

**Example**: `jedienclave/` contains [textures](TPC-File-Format) and lightmaps but no components ([texture](TPC-File-Format)-only kit). `enclavesurface/` contains full components with [models](MDL-MDX-File-Format), [walkmeshes](BWM-File-Format), and minimaps.

---

## Kit JSON file

The kit JSON file (`{kit_id}.json`) defines the kit structure:

```json5
{
    "name": "Kit Display Name",
    "id": "kitid",
    "ht": "2.0.2",
    "version": 1,
    "components": [
        {
            "name": "Component Name",
            "id": "component_id",
            "native": 1,
            "doorhooks": [
                {
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "rotation": 90.0,
                    "door": 0,
                    "edge": 20
                }
            ]
        }
    ],
    "doors": [
        {
            "utd_k1": "door0_k1",
            "utd_k2": "door0_k2",
            "width": 2.0,
            "height": 3.0
        }
    ]
}
```

**fields**:

- `name`: Display name for the kit
- `id`: Unique kit identifier (matches folder name, must be lowercase, sanitized)
- `ht`: Holocron Toolset version compatibility string
- `version`: Kit version number (integer)
- `components`: List of room components (can be empty for [texture](TPC-File-Format)-only kits)
- `doors`: List of door definitions

**Component fields**:

- `name`: Display name for the component
- `id`: Unique component identifier (matches [MDL](MDL-MDX-File-Format)/[WOK](BWM-File-Format) filename without extension)
- `native`: Always 1 (legacy field, indicates native format)
- `doorhooks`: List of door hook points extracted from [BWM](BWM-File-Format) [edges](BWM-File-Format#edges) with transitions

**Door Hook fields**:

- `x`, `y`, `z`: World-space position of the hook point (midpoint of [BWM](BWM-File-Format) [edge](BWM-File-Format#edges) with transition)
- `rotation`: rotation angle in degrees (0-360), calculated from [edge](BWM-File-Format#edges) direction in XY plane
- `door`: index into the kit's `doors` array (mapped from [BWM](BWM-File-Format) [edge](BWM-File-Format#edges) transition index)
- `edge`: Global [edge](BWM-File-Format#edges) index in the BWM (face_index * 3 + local_edge_index)

**Door fields**:

- `utd_k1`: [ResRef](GFF-File-Format#gff-data-types) of K1 door [UTD](GFF-File-Format#utd-door) file (without `.utd` extension)
- `utd_k2`: [ResRef](GFF-File-Format#gff-data-types) of K2 door [UTD](GFF-File-Format#utd-door) file (without `.utd` extension)
- `width`: Door width in world units (default: 2.0)
- `height`: Door height in world units (default: 3.0)

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py:23-260`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py#L23-L260)

---

## Components

Components are reusable [room models](LYT-File-Format#room-definitions) that can be placed and connected to build indoor maps. They are identified during kit extraction as [MDL files](MDL-MDX-File-Format) that:

1. Are listed as [room models](LYT-File-Format#room-definitions) in the module's [LYT file](LYT-File-Format)
2. Have corresponding WOK ([walkmesh](BWM-File-Format)) files
3. Are not skyboxes (skyboxes have [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) but no [WOK](BWM-File-Format))

**Component files**:

- `{component_id}.mdl`: 3D [model](MDL-MDX-File-Format) geometry (BioWare [MDL](MDL-MDX-File-Format) format)
- `{component_id}.mdx`: [material](MDL-MDX-File-Format#trimesh-header)/lightmap index data (BioWare [MDX](MDL-MDX-File-Format) format)
- `{component_id}.wok`: [walkmesh](BWM-File-Format) for pathfinding (BioWare [BWM](BWM-File-Format) format, re-centered to origin)
- `{component_id}.png`: Minimap image (top-down view of [walkmesh](BWM-File-Format), generated from [BWM](BWM-File-Format))

**Component Identification Process**:

1. Load module [LYT file](LYT-File-Format) to get list of [room model](LYT-File-Format#room-definitions) names
2. For each [room model](LYT-File-Format#room-definitions), resolve [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format)/[WOK](BWM-File-Format) using installation-wide resource resolution
3. Components are [room models](LYT-File-Format#room-definitions) that have both [MDL](MDL-MDX-File-Format) and [WOK files](BWM-File-Format)
4. Component IDs are mapped from [model](MDL-MDX-File-Format) names using `_get_component_name_mapping()` to create friendly names

**Component JSON structure**:

```json5
{
    "name": "Hall 1",
    "id": "hall_1",
    "native": 1,
    "doorhooks": [
        {
            "x": -4.476789474487305,
            "y": -17.959964752197266,
            "z": 3.8257503509521484,
            "rotation": 90.0,
            "door": 0,
            "edge": 25
        }
    ]
}
```

**[BWM](BWM-File-Format) Re-centering**: Component [WOK files](BWM-File-Format) are **re-centered to origin (0, 0, 0)** before saving. This is critical because:

- The Indoor Map Builder draws preview images centered at `room.position`
- The [walkmesh](BWM-File-Format) is translated BY `room.position` from its original coordinates
- For alignment, the [BWM](BWM-File-Format) must be centered around (0, 0) so both image and [walkmesh](BWM-File-Format) are at the same position after [transformation](BWM-File-Format#walkable-adjacencies)

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1538-1588`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1538-L1588)

**Door Hooks**:

- `x`, `y`, `z`: World-space position of the hook point (midpoint of [BWM](BWM-File-Format) [edge](BWM-File-Format#edges) with transition)
- `rotation`: rotation angle in degrees (0-360), calculated from [edge](BWM-File-Format#edges) direction using `atan2(dy, dx)`
- `door`: index into the kit's `doors` array (mapped from [BWM](BWM-File-Format) [edge](BWM-File-Format#edges) transition index, clamped to valid range)
- `edge`: Global [edge](BWM-File-Format#edges) index in the BWM (used for door placement during map generation)

**Hook Extraction**: Door hooks are extracted from [BWM](BWM-File-Format) [edges](BWM-File-Format#edges) that have valid transitions (`edge.transition >= 0`). The transition index maps to the door index in the kit's doors array.

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1467-1535`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1467-L1535)

**Hook Connection Logic**: Components are connected when their hook points are within proximity. The toolset automatically links compatible hooks to form room connections.

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py:88-106`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py#L88-L106)

---

## [textures](TPC-File-Format) and Lightmaps

Kits contain all [textures](TPC-File-Format) and lightmaps referenced by their component [models](MDL-MDX-File-Format), plus any additional shared resources found in the module or installation.

### [texture](TPC-File-Format) Extraction

[textures](TPC-File-Format) are extracted from multiple sources using the game engine's resource resolution priority:

1. **Module RIM/[ERF](ERF-File-Format) files**: [textures](TPC-File-Format) directly in the [module archives](ERF-File-Format)
2. **Installation-wide Resolution**: [textures](TPC-File-Format) from:
   - `override/` (user mods, highest priority)
   - `modules/` (module-specific overrides, `.mod` files take precedence over `.rim` files)
   - `textures_gui/` ([GUI](GFF-File-Format#gui-graphical-user-interface) [textures](TPC-File-Format))
   - `texturepacks/` (TPA/[ERF](ERF-File-Format) [texture](TPC-File-Format) packs)
   - `chitin/` (base game [BIF files](BIF-File-Format), lowest priority)

**[texture](TPC-File-Format) Identification**:

- [textures](TPC-File-Format) are identified by scanning all [MDL files](MDL-MDX-File-Format) in the module using `iterate_textures()`
- This extracts [texture](TPC-File-Format) references from [MDL](MDL-MDX-File-Format) [material](MDL-MDX-File-Format#trimesh-header) definitions
- All [models](MDL-MDX-File-Format) from `module.models()` are scanned, including those loaded from CHITIN

**[texture](TPC-File-Format) Naming**:

- [textures](TPC-File-Format): Standard names (e.g., `lda_wall02`, `i_datapad`)
- Lightmaps: Suffixed with `_lm` or prefixed with `l_` (e.g., `m13aa_01a_lm0`, `l_sky01`)

**[TPC](TPC-File-Format) to TGA Conversion**: All [textures](TPC-File-Format) are converted from TPC (BioWare's [texture](TPC-File-Format) format) to TGA (Truevision Targa) format during extraction. The conversion process:

1. Reads [TPC file](TPC-File-Format) data
2. Parses [TPC](TPC-File-Format) structure (mipmaps, format, embedded [TXI](TXI-File-Format))
3. Converts mipmaps to RGBA format if needed
4. Writes TGA file with BGRA pixel order (TGA format requirement)

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:926-948`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L926-L948)

### Resource Resolution Priority

The extraction process uses the same resource resolution priority as the game engine:

1. **OVERRIDE** (priority 0 - highest): User mods in `override/` folder
2. **MODULES** (priority 1-2): Module files
   - `.mod` files (priority 1) - take precedence over `.rim` files
   - `.rim` and `_s.rim` files (priority 2)
3. **TEXTURES_GUI** (priority 3): [GUI](GFF-File-Format#gui-graphical-user-interface) [textures](TPC-File-Format)
4. **TEXTURES_TPA** (priority 4): [texture](TPC-File-Format) packs
5. **CHITIN** (priority 5 - lowest): Base game [BIF files](BIF-File-Format)

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:74-120`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L74-L120)

**Batch Processing**: [texture](TPC-File-Format)/lightmap lookups are batched for performance:

- Single `installation.locations()` call for all [textures](TPC-File-Format)/lightmaps
- Results are pre-sorted by priority once to avoid repeated sorting
- [TPC](TPC-File-Format)/TGA files are grouped by filepath for batch I/O operations

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:814-964`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L814-L964)

### [TXI](TXI-File-Format) files

Each [texture](TPC-File-Format)/lightmap can have an accompanying `.txi` file containing [texture](TPC-File-Format) metadata (filtering, wrapping, etc.). [TXI files](TXI-File-Format) are extracted from:

1. **Embedded [TXI](TXI-File-Format) in [TPC](TPC-File-Format) files**: [TPC files](TPC-File-Format) can contain embedded [TXI](TXI-File-Format) data
2. **Standalone [TXI](TXI-File-Format) files**: [TXI files](TXI-File-Format) in the installation (same resolution priority as [textures](TPC-File-Format))
3. **Empty [TXI](TXI-File-Format) placeholders**: If no [TXI](TXI-File-Format) is found, an empty [TXI file](TXI-File-Format) is created to match expected kit structure

**[TXI](TXI-File-Format) Extraction Process**:

1. Check for embedded [TXI](TXI-File-Format) in [TPC file](TPC-File-Format) during conversion
2. If not found, lookup standalone [TXI file](TXI-File-Format) using batch location results
3. If still not found, create empty [TXI](TXI-File-Format) placeholder

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:849-1020`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L849-L1020)

### Shared Resources

Some kits include [textures](TPC-File-Format)/lightmaps from **other modules** that are not directly referenced by the kit's own [models](MDL-MDX-File-Format). These are typically:

- **Shared Lightmaps**: Lightmaps from other modules stored in `lightmaps3.bif` (CHITIN) that may be used by multiple areas
  - Example: `m03af_01a_lm13`, `m10aa_01a_lm13`, `m14ab_02a_lm13` from `jedienclave` kit
  - These are found in `data/lightmaps3.bif` as shared resources across multiple modules
  - They may be referenced by other modules that share resources with the kit's source module
- **Common [textures](TPC-File-Format)**: [textures](TPC-File-Format) from `swpc_tex_tpa.erf` ([texture](TPC-File-Format) packs) used across multiple modules
  - Example: `lda_*` textures (lda_bark04, lda_flr07, etc.) from [texture](TPC-File-Format) packs
  - These are shared resources that may be used by multiple areas
- **Module Resources**: [textures](TPC-File-Format)/lightmaps found in the module's resource list but not directly referenced by [models](MDL-MDX-File-Format)
  - Some resources may be included even if not directly referenced
  - These ensure the kit is self-contained and doesn't depend on external resources

**Why Include Shared Resources?**:

- **Self-Containment**: Ensures the kit has all resources it might need
- **Compatibility**: Some resources may be referenced indirectly or by other systems
- **Convenience**: Manually curated collections of commonly used resources
- **Future-Proofing**: Resources that might be needed when the kit is used in different contexts

**Reference**: Investigation using `Installation.locations()` shows these resources are found in:

- `data/lightmaps3.bif` (CHITIN) for shared lightmaps
- `texturepacks/swpc_tex_tpa.erf` (TEXTURES_TPA) for common [textures](TPC-File-Format)

---

## Always Folder

The `always/` folder contains resources that are **always included** in the generated module, regardless of which components are used.

**Purpose**:

- **Static Resources**: Resources that should be included in every generated module using the kit
- **Common Assets**: Shared [textures](TPC-File-Format), [models](MDL-MDX-File-Format), or other resources needed by all rooms
- **Override Resources**: Resources that override base game files and should be included in every room
- **Non-Component Resources**: Resources that don't belong to specific components but are needed for the kit to function

**Usage**: When a kit is used to generate a module, all files in the `always/` folder are automatically added to the mod's resource list via `add_static_resources()`. These resources are included in every room, even if they're not directly referenced by component [models](MDL-MDX-File-Format).

**Processing**: Resources in the `always/` folder are processed during indoor map generation:

1. Each file in `always/` is loaded into `kit.always[filename]` during kit loading
2. When a room is processed, `add_static_resources()` extracts the resource name and type from the filename
3. The resource is added to the mod with `mod.set_data(resname, restype, data)`
4. This happens for every room, ensuring the resource is always available

**Example**: The `sithbase` kit includes:

- `CM_asith.tpc`: Common [texture](TPC-File-Format) used across all rooms
- `lsi_floor01b.tpc`, `lsi_flr03b.tpc`, `lsi_flr04b.tpc`: Floor [textures](TPC-File-Format) for all rooms
- `lsi_win01bmp.tpc`: Window [texture](TPC-File-Format) used throughout the base

These are added to every room when using the sithbase kit, ensuring consistent appearance across all generated rooms.

**When to Use**:

- Resources that should be available in every room (e.g., common floor [textures](TPC-File-Format))
- Override resources that replace base game files
- Resources needed for kit functionality but not tied to specific components
- Shared assets that multiple components might reference

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoormap.py:236-256`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoormap.py#L236-L256)

---

## Doors

Doors are defined in the kit JSON and have corresponding [UTD](GFF-File-Format#utd-door) files. Doors connect adjacent rooms at component hook points.

**Door files**:

- `{door_name}_k1.utd`: KotOR 1 door template ([UTD](GFF-File-Format#utd-door) format)
- `{door_name}_k2.utd`: KotOR 2 door template ([UTD](GFF-File-Format#utd-door) format)
- `{door_model}0.dwk`: Door [walkmesh](BWM-File-Format) for closed state
- `{door_model}1.dwk`: Door [walkmesh](BWM-File-Format) for open1 state
- `{door_model}2.dwk`: Door [walkmesh](BWM-File-Format) for open2 state

**Door JSON structure**:

```json5
{
    "utd_k1": "door0_k1",
    "utd_k2": "door0_k2",
    "width": 2.0,
    "height": 3.0
}
```

**Door Properties**:

- `utd_k1`, `utd_k2`: ResRefs of [UTD](GFF-File-Format#utd-door) files (without `.utd` extension)
- `width`: Door width in world units (default: 2.0)
- `height`: Door height in world units (default: 3.0)

**Door Extraction Process**:

1. [UTD](GFF-File-Format#utd-door) files are extracted from module RIM/[ERF](ERF-File-Format) archives
2. Door [model](MDL-MDX-File-Format) names are resolved from [UTD](GFF-File-Format#utd-door) files using `genericdoors.2da`
3. [DWK](BWM-File-Format) [walkmeshes](BWM-File-Format) are extracted for each door model (3 states: 0=closed, 1=open1, 2=open2)
4. Door dimensions are set to fast defaults (2.0x3.0) to avoid expensive extraction

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1253-1304`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1253-L1304)

Doors are placed at component hook points and connect adjacent rooms. The [door templates](GFF-File-Format#utd-door) define appearance, locking, scripts, and other properties.

**Reference**: [`wiki/GFF-File-Format.md#utd-door`](GFF-File-Format#utd-door)

### Door Walkmeshes ([DWK](BWM-File-Format))

Doors have 3 [walkmesh](BWM-File-Format) states that define pathfinding behavior:

- **State 0 (closed)**: `{door_model}0.dwk` - Door is closed, blocks pathfinding
- **State 1 (open1)**: `{door_model}1.dwk` - Door is open in first direction
- **State 2 (open2)**: `{door_model}2.dwk` - Door is open in second direction

**[DWK](BWM-File-Format) Extraction Process**:

1. Load `genericdoors.2da` to map [UTD](GFF-File-Format#utd-door) files to door [model](MDL-MDX-File-Format) names
2. For each door, resolve [model](MDL-MDX-File-Format) name from [UTD](GFF-File-Format#utd-door) using `door_tools.get_model()`
3. Batch lookup all [DWK](BWM-File-Format) files (3 states per door) using `installation.locations()`
4. Extract [DWK](BWM-File-Format) files from module first (fastest), then fall back to installation-wide resolution

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1090-1174`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1090-L1174)

**Game Engine Reference**: [`vendor/reone/src/libs/game/object/door.cpp:80-94`](https://github.com/OldRepublicDevs/PyKotor/blob/master/vendor/reone/src/libs/game/object/door.cpp#L80-L94)

---

## Placeables

Placeables are interactive objects (containers, terminals, etc.) that can be placed in rooms. They are optional and may not be present in all kits.

**Placeable files**:

- `{placeable_model}.pwk`: Placeable [walkmesh](BWM-File-Format) for pathfinding

**Placeable Extraction Process**:

1. [UTP](GFF-File-Format#utp-placeable) files are extracted from module RIM/[ERF](ERF-File-Format) archives
2. Placeable [model](MDL-MDX-File-Format) names are resolved from [UTP](GFF-File-Format#utp-placeable) files using `placeables.2da`
3. [PWK](BWM-File-Format) [walkmeshes](BWM-File-Format) are extracted for each placeable [model](MDL-MDX-File-Format)
4. [PWK](BWM-File-Format) files are written to kit directory root

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1176-1251`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1176-L1251)

### Placeable Walkmeshes ([PWK](BWM-File-Format))

Placeables have [walkmeshes](BWM-File-Format) that define their collision boundaries for pathfinding.

**[PWK](BWM-File-Format) Extraction Process**:

1. Load `placeables.2da` to map [UTP](GFF-File-Format#utp-placeable) files to placeable [model](MDL-MDX-File-Format) names
2. For each placeable, resolve [model](MDL-MDX-File-Format) name from [UTP](GFF-File-Format#utp-placeable) using `placeable_tools.get_model()`
3. Batch lookup all [PWK](BWM-File-Format) files using `installation.locations()`
4. Extract [PWK](BWM-File-Format) files from module first (fastest), then fall back to installation-wide resolution

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1176-1251`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1176-L1251)

**Game Engine Reference**: [`vendor/reone/src/libs/game/object/placeable.cpp:73`](https://github.com/OldRepublicDevs/PyKotor/blob/master/vendor/reone/src/libs/game/object/placeable.cpp#L73)

---

## Skyboxes

Skyboxes are optional [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [models](MDL-MDX-File-Format) used for outdoor area rendering. They are stored in the `skyboxes/` folder.

**Skybox Identification**: Skyboxes are identified as [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) pairs that:

1. Are NOT listed as [room models](LYT-File-Format#room-definitions) in the [LYT file](LYT-File-Format)
2. Do NOT have corresponding [WOK files](BWM-File-Format)
3. Are found in the module's resource list

**Skybox files**:

- `{skybox_name}.mdl`: Skybox [model](MDL-MDX-File-Format) [geometry](MDL-MDX-File-Format#geometry-header)
- `{skybox_name}.mdx`: Skybox [material](MDL-MDX-File-Format#trimesh-header) data

Skyboxes are typically used for outdoor areas and provide the distant sky/background rendering. They are loaded separately from room components and don't have [walkmeshes](BWM-File-Format).

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:740-744`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L740-L744)

---

## Doorway Padding

The `doorway/` folder contains padding [models](MDL-MDX-File-Format) that fill gaps around doors:

**Padding files**:

- `side_{door_id}_size{size}.mdl`: Side padding for horizontal doors
- `top_{door_id}_size{size}.mdl`: Top padding for vertical doors
- Corresponding `.mdx` files

**Padding Purpose**: When doors are inserted into walls, gaps may appear. Padding [models](MDL-MDX-File-Format) fill these gaps to create seamless door transitions.

**Naming Convention**:

- `side_` or `top_`: Padding orientation
- `{door_id}`: Door identifier (matches door index in JSON, extracted using `get_nums()`)
- `size{size}`: Padding size in world units (e.g., `size650`, `size800`)

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py:127-150`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py#L127-L150)

---

## [models](MDL-MDX-File-Format) Directory

The `models/` directory contains additional [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [models](MDL-MDX-File-Format) that are referenced by the module but are not used as components or skyboxes. These are typically:

- **Decorative [models](MDL-MDX-File-Format)**: [models](MDL-MDX-File-Format) used for decoration or atmosphere
- **Non-[room models](LYT-File-Format#room-definitions)**: [models](MDL-MDX-File-Format) that don't have [walkmeshes](BWM-File-Format) and aren't room components
- **Referenced [models](MDL-MDX-File-Format)**: [models](MDL-MDX-File-Format) that are referenced by scripts or other systems

**[models](MDL-MDX-File-Format) Directory structure**:

```shell
models/
├── {model_name}.mdl
└── {model_name}.mdx
```

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1311-1324`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1311-L1324)

---

## Resource Extraction

The kit extraction process (`extract_kit()`) extracts resources from module RIM or [ERF files](ERF-File-Format) and generates a complete kit structure.

### Archive file Support

The extraction process supports multiple archive formats:

- **RIM files**: `.rim` (main module), `_s.rim` (supplementary data)
- **[ERF](ERF-File-Format) files**: `.mod` (module override), `.erf` (generic [ERF](ERF-File-Format)), `.hak` (hakpak), `.sav` (savegame)

**file Resolution Priority**:

1. `.mod` files take precedence over `.rim` files (as per KOTOR resolution order)
2. If extension is specified, use that format directly
3. If no extension, search for both RIM and [ERF files](ERF-File-Format), prioritizing `.mod` files

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:291-550`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L291-L550)

### Component Identification

Components are identified using the following process:

1. **Load Module [LYT files](LYT-File-Format)**: Parse [LYT file](LYT-File-Format) to get list of [room model](LYT-File-Format#room-definitions) names
2. **Batch Resource Resolution**: Batch lookup [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format)/[WOK](BWM-File-Format) for all [room models](LYT-File-Format#room-definitions) using `installation.locations()`
3. **Component Criteria**: A [model](MDL-MDX-File-Format) is a component if:
   - It's listed as a [room model](LYT-File-Format#room-definitions) in the [LYT file](LYT-File-Format)
   - It has both [MDL](MDL-MDX-File-Format) and [WOK files](BWM-File-Format)
   - It's not a skybox (skyboxes have [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) but no [WOK](BWM-File-Format))
4. **Component Name Mapping**: Component IDs are mapped from [model](MDL-MDX-File-Format) names using `_get_component_name_mapping()` to create friendly names (e.g., `danm13_room01` → `room_01`)

**Reference**: [`Libraries/PyKotor/src/pykotor/src/pykotor/tools/kit.py:600-767`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L600-L767)

### [texture](TPC-File-Format) and Lightmap Extraction

[textures](TPC-File-Format) and lightmaps are extracted using a comprehensive process:

1. **[model](MDL-MDX-File-Format) Scanning**: Scan all [MDL files](MDL-MDX-File-Format) from `module.models()` using `iterate_textures()` and `iterate_lightmaps()`
2. **Archive Scanning**: Also extract [TPC](TPC-File-Format)/TGA files directly from RIM/[ERF](ERF-File-Format) archives
3. **Module Resource Scanning**: Check `module.resources` for additional [textures](TPC-File-Format)/lightmaps
4. **Batch Location Lookup**: Single `installation.locations()` call for all [textures](TPC-File-Format)/lightmaps with search order:
   - OVERRIDE
   - MODULES (`.mod` files take precedence over `.rim` files)
   - TEXTURES_GUI
   - TEXTURES_TPA
   - CHITIN
5. **Priority Sorting**: Pre-sort all location results by priority once to avoid repeated sorting
6. **Batch I/O**: Group [TPC](TPC-File-Format)/TGA files by filepath for batch reading operations
7. **TPC to TGA Conversion**: Convert all [TPC files](TPC-File-Format) to TGA format during extraction
8. **TXI Extraction**: Extract [TXI files](TXI-File-Format) from embedded [TPC](TPC-File-Format) data or standalone files

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:769-1020`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L769-L1020)

### Door Extraction

Doors are extracted from module [UTD](GFF-File-Format#utd-door) files:

1. **UTD Extraction**: Extract all [UTD](GFF-File-Format#utd-door) files from module RIM/[ERF](ERF-File-Format) archives
2. **Door [model](MDL-MDX-File-Format) Resolution**: Load `genericdoors.2da` once for all doors
3. **[model](MDL-MDX-File-Format) Name Resolution**: Resolve door [model](MDL-MDX-File-Format) names from [UTD](GFF-File-Format#utd-door) files using `door_tools.get_model()`
4. **[DWK](BWM-File-Format) Extraction**: Extract door walkmeshes (3 states per door) using batch lookup
5. **Door JSON Generation**: Generate door entries in kit JSON with fast defaults (2.0x3.0 dimensions)

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1253-1304`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1253-L1304)

### [walkmesh](BWM-File-Format) Extraction

[walkmeshes](BWM-File-Format) are extracted for components, doors, and placeables:

1. **Component [WOK](BWM-File-Format)**: Extracted from module or installation-wide resolution
2. **Door [DWK](BWM-File-Format)**: Extracted using batch lookup (3 states: 0, 1, 2)
3. **Placeable [PWK](BWM-File-Format)**: Extracted using batch lookup

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1090-1251`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1090-L1251)

### [BWM](BWM-File-Format) Re-centering

Component [WOK files](BWM-File-Format) are **re-centered to origin (0, 0, 0)** before saving. This is critical for proper alignment in the Indoor Map Builder:

**Problem**: Without re-centering:

- Preview image is drawn centered at `room.position`
- [walkmesh](BWM-File-Format) is translated BY `room.position` from original coordinates
- If [BWM](BWM-File-Format) center is at (100, 200) and room.position = (0, 0):
  - Image would be centered at (0, 0)
  - [walkmesh](BWM-File-Format) would be centered at (100, 200) after translate
  - **MISMATCH**: Image and hitbox are in different places

**Solution**: After re-centering [BWM](BWM-File-Format) to (0, 0):

- Image is centered at `room.position`
- [walkmesh](BWM-File-Format) is centered at `room.position` after translate
- **MATCH**: Image and hitbox overlap perfectly

**Re-centering Process**:

1. Calculate [BWM](BWM-File-Format) bounding box (min/max X, Y, Z)
2. Calculate center point
3. Translate all [vertices](MDL-MDX-File-Format#vertex-structure) by negative center to move [BWM](BWM-File-Format) to origin
4. Save re-centered [WOK file](BWM-File-Format)

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1538-1588`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1538-L1588)

### Minimap Generation

Component minimap images are generated from re-centered [BWM](BWM-File-Format) [walkmeshes](BWM-File-Format):

1. **Bounding Box Calculation**: Calculate [bounding box](MDL-MDX-File-Format#model-header) from [BWM](BWM-File-Format) [vertices](MDL-MDX-File-Format#vertex-structure)
2. **Image Dimensions**: scale to 10 pixels per world unit, minimum 256x256
3. **coordinate [transformation](BWM-File-Format#walkable-adjacencies)**: Transform world coordinates to image coordinates (flip Y-axis)
4. **[face](MDL-MDX-File-Format#face-structure) Rendering**: Draw [walkable faces](BWM-File-Format#faces) in white, non-walkable in gray
5. **Image format**: PNG format, saved as `{component_id}.png`

**[walkable face](BWM-File-Format#faces) [materials](MDL-MDX-File-Format#trimesh-header)**: [faces](MDL-MDX-File-Format#face-structure) with [materials](MDL-MDX-File-Format#trimesh-header) 1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22 are considered walkable.

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1348-1465`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1348-L1465)

### Doorhook Extraction

Door hooks are extracted from [BWM](BWM-File-Format) [edges](BWM-File-Format#edges) that have valid transitions:

1. **[edge](BWM-File-Format#edges) Processing**: Iterate through all [BWM](BWM-File-Format) [edges](BWM-File-Format#edges)
2. **Transition Check**: Skip [edges](BWM-File-Format#edges) without transitions (`edge.transition < 0`)
3. **Midpoint Calculation**: Calculate midpoint of [edge](BWM-File-Format#edges) from [vertices](MDL-MDX-File-Format#vertex-structure)
4. **rotation Calculation**: Calculate rotation angle from [edge](BWM-File-Format#edges) direction using `atan2(dy, dx)`
5. **Door index Mapping**: Map transition index to door index (clamped to valid range)
6. **Hook Generation**: Create doorhook entry with position, rotation, door index, and [edge](BWM-File-Format#edges) index

**[edge](BWM-File-Format#edges) index Calculation**: Global [edge](BWM-File-Format#edges) index = `face_index * 3 + local_edge_index`

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1467-1535`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1467-L1535)

---

## Implementation Details

### Kit Class structure

The `Kit` class structure in memory:

```python
class Kit:
    name: str
    always: dict[Path, bytes]  # Static resources
    textures: CaseInsensitiveDict[bytes]  # Texture TGA data
    txis: CaseInsensitiveDict[bytes]  # TXI metadata (for textures and lightmaps)
    lightmaps: CaseInsensitiveDict[bytes]  # Lightmap TGA data
    skyboxes: CaseInsensitiveDict[MDLMDXTuple]  # Skybox models
    doors: list[KitDoor]  # Door definitions
    components: list[KitComponent]  # Room components
    side_padding: dict[int, dict[int, MDLMDXTuple]]  # Side padding by door_id and size
    top_padding: dict[int, dict[int, MDLMDXTuple]]  # Top padding by door_id and size

class KitComponent:
    kit: Kit
    name: str
    image: QImage  # Minimap image
    hooks: list[KitComponentHook]  # Door hook points
    bwm: BWM  # Walkmesh
    mdl: bytes  # Model geometry
    mdx: bytes  # Model extension

class KitComponentHook:
    position: Vector3  # Hook position
    rotation: float  # Rotation angle
    edge: str  # Edge identifier
    door: KitDoor  # Door reference

class KitDoor:
    utd_k1: UTD  # KotOR 1 door blueprint
    utd_k2: UTD  # KotOR 2 door blueprint
    width: float  # Door width
    height: float  # Door height
    utd: UTD  # Primary door blueprint alias (utd_k1)
```

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_base.py)

### Kit Loading

Kits are loaded by `load_kits()` which:

1. **Scans Kits Directory**: Iterates through all `.json` files in the kits directory
2. **Validates JSON**: Skips invalid JSON files and non-dict structures
3. **Loads Kit Metadata**: Extracts `name` and `id` from JSON
4. **Loads Always Resources**: Loads all files from `always/` folder into `kit.always[filename]`
5. **Loads [textures](TPC-File-Format)**: Loads TGA files from `textures/` folder, extracts [TXI files](TXI-File-Format)
6. **Loads Lightmaps**: Loads TGA files from `lightmaps/` folder, extracts [TXI files](TXI-File-Format)
7. **Loads Skyboxes**: Loads [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) pairs from `skyboxes/` folder
8. **Loads Doorway Padding**: Parses padding filenames to extract door_id and size, loads [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) pairs
9. **Loads Doors**: Loads [UTD](GFF-File-Format#utd-door) files for K1 and K2, creates `KitDoor` instances
10. **Loads Components**: Loads [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format)/[WOK files](BWM-File-Format) and PNG minimap images, creates `KitComponent` instances
11. **Populates Hooks**: Extracts doorhook data from JSON and creates `KitComponentHook` instances
12. **Error Handling**: Collects missing files instead of failing fast, returns list of missing files

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py:23-260`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoorkit/indoorkit_loader.py#L23-L260)

### Indoor Map Generation

When generating an indoor map from kits:

1. **Component Placement**: Components are placed at specified positions with rotations/flips
2. **Hook Connection**: Hook points are matched to connect adjacent rooms
3. **[model](MDL-MDX-File-Format) [transformation](BWM-File-Format#walkable-adjacencies)**: [models](MDL-MDX-File-Format) are flipped, rotated, and transformed based on room properties
4. **[texture](TPC-File-Format)/Lightmap Renaming**: [textures](TPC-File-Format) and lightmaps are renamed to module-specific names
5. **[walkmesh](BWM-File-Format) Merging**: Room [walkmeshes](BWM-File-Format) are combined into a single area [walkmesh](BWM-File-Format)
6. **Door Insertion**: Doors are inserted at hook points with appropriate padding
7. **Resource Generation**: are, [GIT](GFF-File-Format#git-game-instance-template), [LYT](LYT-File-Format), [VIS](VIS-File-Format), [IFO](GFF-File-Format#ifo-module-info) files are generated
8. **Minimap Generation**: Minimap images are generated from component PNGs
9. **Static Resources**: Always resources are added to every room via `add_static_resources()`

**Reference**: [`Tools/HolocronToolset/src/toolset/data/indoormap.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/indoormap.py)

### coordinate System

- **World coordinates**: Meters in left-handed coordinate system (X=right, Y=forward, Z=up)
- **Hook positions**: World-space coordinates relative to component origin (after re-centering to 0,0,0)
- **rotations**: Degrees (0-360), counterclockwise from positive X-axis
- **Transforms**: Components can be flipped on X/Y axes and rotated around Z-axis
- **[BWM](BWM-File-Format) coordinates**: Re-centered to origin (0, 0, 0) for proper alignment in Indoor Map Builder

**Reference**: [`wiki/BWM-File-Format.md`](BWM-File-Format) and [`wiki/LYT-File-Format.md`](LYT-File-Format)

---

## Kit types

### Component-Based Kits

Kits with `components` array (e.g., `enclavesurface`, `endarspire`):

- Contain reusable [room models](LYT-File-Format#room-definitions) with [walkmeshes](BWM-File-Format)
- Have hook points for connecting rooms
- Include [textures](TPC-File-Format)/lightmaps referenced by components
- Generate complete indoor maps with room layouts
- Include minimap images for component selection

### [texture](TPC-File-Format)-Only Kits

Kits with empty `components` array (e.g., `jedienclave`):

- Contain only [textures](TPC-File-Format) and lightmaps
- May include shared resources from multiple modules
- Used for [texture](TPC-File-Format) packs or shared resource collections
- Don't generate room layouts (no components to place)
- Useful for [texture](TPC-File-Format) libraries or resource packs

---

## Game Engine Compatibility

Kits are designed to be compatible with the KOTOR game engine's resource resolution and module structure:

**Resource Resolution**: Kits use the same resource resolution priority as the game engine:

1. OVERRIDE (user mods)
2. MODULES (`.mod` files take precedence over `.rim` files)
3. TEXTURES_GUI
4. TEXTURES_TPA
5. CHITIN (base game)

**Module structure**: Generated modules follow the same structure as game modules:

- are files for area definitions
- [GIT files](GFF-File-Format#git-game-instance-template) for instance data
- [LYT files](LYT-File-Format) for room layouts
- [VIS files](VIS-File-Format) for visibility data
- [IFO](GFF-File-Format#ifo-module-info) files for module information

**file formats**: All kit resources use native game formats:

- [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) for 3D [models](MDL-MDX-File-Format)
- [WOK](BWM-File-Format)/[BWM](BWM-File-Format) for [walkmeshes](BWM-File-Format)
- TGA for textures (converted from [TPC](TPC-File-Format) during extraction)
- [TXI](TXI-File-Format) for [texture](TPC-File-Format) metadata
- [UTD](GFF-File-Format#utd-door) for door blueprints
- [DWK](BWM-File-Format)/[PWK](BWM-File-Format) for [walkmeshes](BWM-File-Format)

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:74-120`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L74-L120)

---

## Vendor Implementation References

The kit extraction process is based on reverse-engineered implementations from multiple game engine reimplementations. This section documents how vendor implementations handle the same operations and any discrepancies.

### Door Walkmesh ([DWK](BWM-File-Format)) Extraction

**reone Implementation** (`vendor/reone/src/libs/game/object/door.cpp:80-98`):

- Doors load 3 [walkmesh](BWM-File-Format) states: `{modelName}0.dwk` (closed), `{modelName}1.dwk` (open1), `{modelName}2.dwk` (open2)
- [walkmeshes](BWM-File-Format) are loaded via `_services.resource.walkmeshes.get(modelName + "0", ResType::Dwk)`
- Each [walkmesh](BWM-File-Format) state is stored as a separate `WalkmeshSceneNode` with enabled/disabled state based on door state
- **PyKotor Implementation**: Matches reone exactly - extracts all 3 [DWK](BWM-File-Format) states using the same naming convention

**KotOR.js Implementation** (`vendor/KotOR.js/src/module/ModuleDoor.ts:990-1003`):

- Only loads the closed state [walkmesh](BWM-File-Format): `ResourceLoader.loadResource(ResourceTypes['dwk'], resRef+'0')`
- Open states are handled dynamically through collision state updates, not separate [walkmesh](BWM-File-Format) files
- **Discrepancy**: KotOR.js only loads `{modelName}0.dwk`, while reone and PyKotor extract all 3 states
- **PyKotor Implementation**: Extracts all 3 states to match reone's comprehensive approach

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1090-1174`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1090-L1174)

### Placeable Walkmesh ([PWK](BWM-File-Format)) Extraction

**reone Implementation** (`vendor/reone/src/libs/game/object/placeable.cpp:73-76`):

- Placeables load a single [walkmesh](BWM-File-Format): `_services.resource.walkmeshes.get(modelName, ResType::Pwk)`
- [walkmesh](BWM-File-Format) is stored as a `WalkmeshSceneNode` attached to the placeable's scene [node](MDL-MDX-File-Format#node-structures)
- **PyKotor Implementation**: Matches reone exactly - extracts [PWK](BWM-File-Format) using [model](MDL-MDX-File-Format) name directly

**KotOR.js Implementation** (`vendor/KotOR.js/src/module/ModulePlaceable.ts:682-698`):

- Loads [walkmesh](BWM-File-Format): `ResourceLoader.loadResource(ResourceTypes['pwk'], resRef)`
- Creates `OdysseyWalkMesh` from binary data and attaches to [model](MDL-MDX-File-Format)
- Falls back to empty [walkmesh](BWM-File-Format) if loading fails
- **PyKotor Implementation**: Matches KotOR.js approach - extracts [PWK](BWM-File-Format) using [model](MDL-MDX-File-Format) name

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:1176-1251`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1176-L1251)

### [room model](LYT-File-Format#room-definitions) and Component Identification

**reone Implementation** (`vendor/reone/src/libs/game/object/area.cpp:305-376`):

- Loads [LYT file](LYT-File-Format) via `_services.resource.layouts.get(_name)`
- Iterates through `layout->rooms` to get [room model](LYT-File-Format#room-definitions) names
- For each room, loads [MDL](MDL-MDX-File-Format) [model](MDL-MDX-File-Format): `_services.resource.models.get(lytRoom.name)`
- Loads [WOK](BWM-File-Format) [walkmesh](BWM-File-Format): `_services.resource.[walkmeshes](BWM-File-Format).get(lytRoom.name, ResType::Wok)`
- Rooms are identified as [MDL](MDL-MDX-File-Format) [models](MDL-MDX-File-Format) with corresponding [WOK files](BWM-File-Format) from [LYT](LYT-File-Format)
- **PyKotor Implementation**: Matches reone exactly - uses [LYT](LYT-File-Format) to identify [room models](LYT-File-Format#room-definitions), then resolves [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format)/[WOK](BWM-File-Format)

**KotOR.js Implementation** (`vendor/KotOR.js/src/module/ModuleRoom.ts:331-342`):

- Loads [walkmesh](BWM-File-Format): `ResourceLoader.loadResource(ResourceTypes['wok'], resRef)`
- Creates `OdysseyWalkMesh` from binary data and attaches to [room model](LYT-File-Format#room-definitions)
- Rooms are identified from [LYT file](LYT-File-Format) room definitions
- **PyKotor Implementation**: Matches KotOR.js approach - uses [LYT](LYT-File-Format) [room models](LYT-File-Format#room-definitions) to identify components

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:545-767`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L545-L767)

### Door [model](MDL-MDX-File-Format) Resolution

**reone Implementation** (`vendor/reone/src/libs/game/object/door.cpp`):

- Door [models](MDL-MDX-File-Format) are resolved from [UTD](GFF-File-Format#utd-door) files using `genericdoors.2da`
- The `appearance_id` field in [UTD](GFF-File-Format#utd-door) maps to a row in `genericdoors.2da`
- The `modelname` column in that row provides the door [model](MDL-MDX-File-Format) name
- **PyKotor Implementation**: Matches reone exactly - uses `door_tools.get_model()` which reads `genericdoors.2da`

**KotOR.js Implementation** (`vendor/KotOR.js/src/module/ModuleDoor.ts`):

- Door [models](MDL-MDX-File-Format) are resolved similarly using `[genericdoors.2da](2DA-genericdoors)`
- The appearance ID from [UTD](GFF-File-Format#utd-door) is used to lookup [model](MDL-MDX-File-Format) name
- **PyKotor Implementation**: Matches KotOR.js approach

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/door.py:25-64`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/door.py#L25-L64)

### Placeable [model](MDL-MDX-File-Format) Resolution

**reone Implementation** (`vendor/reone/src/libs/game/object/placeable.cpp`):

- Placeable [models](MDL-MDX-File-Format) are resolved from [UTP](GFF-File-Format#utp-placeable) files using `placeables.2da`
- The `appearance_id` field in [UTP](GFF-File-Format#utp-placeable) maps to a row in `placeables.2da`
- The `modelname` column in that row provides the placeable [model](MDL-MDX-File-Format) name
- **PyKotor Implementation**: Matches reone exactly - uses `placeable_tools.get_model()` which reads `placeables.2da`

**KotOR.js Implementation** (`vendor/KotOR.js/src/module/ModulePlaceable.ts`):

- Placeable [models](MDL-MDX-File-Format) are resolved similarly using `placeables.2da`
- The appearance ID from [UTP](GFF-File-Format#utp-placeable) is used to lookup [model](MDL-MDX-File-Format) name
- **PyKotor Implementation**: Matches KotOR.js approach

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/placeable.py:20-50`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/placeable.py#L20-L50)

### [texture](TPC-File-Format) and Lightmap Extraction

**PyKotor Implementation** (`Libraries/PyKotor/src/pykotor/tools/model.py`):

- Uses `iterate_textures()` and `iterate_lightmaps()` to extract [texture](TPC-File-Format)/lightmap references from [MDL files](MDL-MDX-File-Format)
- Scans all [MDL](MDL-MDX-File-Format) nodes ([mesh](MDL-MDX-File-Format#trimesh-header), skin, emitter) for [texture](TPC-File-Format) references
- Lightmaps are identified by naming patterns (`_lm` suffix or `l_` prefix)
- **Vendor Comparison**: No direct equivalent in reone/KotOR.js - they load [textures](TPC-File-Format) on-demand during rendering
- **Discrepancy**: PyKotor proactively extracts all [textures](TPC-File-Format)/lightmaps, while engines load them lazily during rendering
- **Rationale**: Kit extraction needs all [textures](TPC-File-Format) upfront for self-contained kit structure

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/model.py:99-887`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/model.py#L99-L887)

### Resource Resolution Priority

**reone Implementation** (`vendor/reone/src/libs/resource/provider/`):

- Resource resolution follows KOTOR priority: Override → Modules → Chitin
- `.mod` files take precedence over `.rim` files in Modules directory
- **PyKotor Implementation**: Matches reone exactly - uses same priority order via `_get_resource_priority()`

**KotOR.js Implementation** (`vendor/KotOR.js/src/loaders/ResourceLoader.ts`):

- Resource resolution follows similar priority order
- Override folder checked first, then modules, then chitin
- **PyKotor Implementation**: Matches KotOR.js approach

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:74-120`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L74-L120)

### [BWM](BWM-File-Format)/[WOK](BWM-File-Format) [walkmesh](BWM-File-Format) Handling

**reone Implementation** (`vendor/reone/src/libs/graphics/walkmesh.cpp`):

- [walkmeshes](BWM-File-Format) are loaded from [WOK](BWM-File-Format)/[BWM files](BWM-File-Format)
- [face](MDL-MDX-File-Format#face-structure) [materials](MDL-MDX-File-Format#trimesh-header) determine walkability ([materials](MDL-MDX-File-Format#trimesh-header) 1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 16, 18, 20, 21, 22 are walkable)
- [edge](BWM-File-Format#edges) transitions indicate door connections
- **PyKotor Implementation**: Matches reone - uses same walkable [material](MDL-MDX-File-Format#trimesh-header) values for minimap generation

**KotOR.js Implementation** (`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts`):

- [walkmeshes](BWM-File-Format) are loaded from [WOK](BWM-File-Format) binary data
- [face](MDL-MDX-File-Format#face-structure) [materials](MDL-MDX-File-Format#trimesh-header) and walk types determine walkability
- [edge](BWM-File-Format#edges) transitions are stored in [walkmesh](BWM-File-Format) structure
- **PyKotor Implementation**: Matches KotOR.js - extracts doorhooks from [BWM](BWM-File-Format) [edges](BWM-File-Format#edges) with transitions

**Reference**:

- [`Libraries/PyKotor/src/pykotor/tools/kit.py:1348-1465`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1348-L1465) (Minimap generation)
- [`Libraries/PyKotor/src/pykotor/tools/kit.py:1467-1535`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L1467-L1535) (Doorhook extraction)

### [module archives](ERF-File-Format) Loading

**reone Implementation** (`vendor/reone/src/libs/resource/provider/`):

- Supports RIM and [ERF file](ERF-File-Format) formats
- `.mod` files ([ERF](ERF-File-Format) format) take precedence over `.rim` files
- **PyKotor Implementation**: Matches reone exactly - prioritizes `.mod` files over `.rim` files

**KotOR.js Implementation** (`vendor/KotOR.js/src/loaders/ResourceLoader.ts`):

- Supports RIM and [ERF file](ERF-File-Format) formats
- Module loading follows same priority order
- **PyKotor Implementation**: Matches KotOR.js approach

**Reference**: [`Libraries/PyKotor/src/pykotor/tools/kit.py:291-550`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/tools/kit.py#L291-L550)

### [KEY](KEY-File-Format) Discrepancies and Rationale

1. **[DWK](BWM-File-Format) Extraction**:
   - **KotOR.js**: Only extracts closed state (`{modelName}0.dwk`)
   - **reone/PyKotor**: Extracts all 3 states (closed, open1, open2)
   - **Rationale**: PyKotor matches reone for comprehensive kit extraction

2. **[texture](TPC-File-Format) Extraction**:
   - **Vendor Engines**: Load [textures](TPC-File-Format) lazily during rendering
   - **PyKotor**: Proactively extracts all [textures](TPC-File-Format)/lightmaps upfront
   - **Rationale**: Kits need self-contained resource collections, not lazy loading

3. **[BWM](BWM-File-Format) Re-centering**:
   - **Vendor Engines**: Use BWMs in world coordinates as-is
   - **PyKotor**: Re-centers BWMs to origin (0, 0, 0)
   - **Rationale**: Indoor Map Builder requires centered BWMs for proper image/[walkmesh](BWM-File-Format) alignment

4. **Component Name Mapping**:
   - **Vendor Engines**: Use [model](MDL-MDX-File-Format) names directly (e.g., `m09aa_01a`)
   - **PyKotor**: Maps to friendly names (e.g., `hall_1`) for better UX
   - **Rationale**: Kit components need human-readable identifiers for toolset UI

---

## Test Comparison Precision

The kit generation tests (`Tools/HolocronToolset/tests/data/test_kit_generation.py`) use different comparison strategies depending on the data type:

### Exact Matching (1:1 [byte](GFF-File-Format#gff-data-types)-for-[byte](GFF-File-Format#gff-data-types))

**Binary files** (SHA256 hash comparison):

- **[MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format)**: [model](MDL-MDX-File-Format) [geometry](MDL-MDX-File-Format#geometry-header) and [animations](MDL-MDX-File-Format#animation-header) - must be [byte](GFF-File-Format#gff-data-types)-for-[byte](GFF-File-Format#gff-data-types) identical
- **[WOK](BWM-File-Format)/[BWM](BWM-File-Format)**: [walkmesh](BWM-File-Format) data - must be [byte](GFF-File-Format#gff-data-types)-for-[byte](GFF-File-Format#gff-data-types) identical
- **[DWK](BWM-File-Format)/[PWK](BWM-File-Format)**: Door and placeable [walkmeshes](BWM-File-Format) - must be [byte](GFF-File-Format#gff-data-types)-for-[byte](GFF-File-Format#gff-data-types) identical
- **PNG**: Minimap images - must be [byte](GFF-File-Format#gff-data-types)-for-[byte](GFF-File-Format#gff-data-types) identical
- **[UTD](GFF-File-Format#utd-door)**: Door blueprints - must be [byte](GFF-File-Format#gff-data-types)-for-[byte](GFF-File-Format#gff-data-types) identical
- **[TXI](TXI-File-Format)**: [texture](TPC-File-Format) metadata files - must be [byte](GFF-File-Format#gff-data-types)-for-[byte](GFF-File-Format#gff-data-types) identical

**Rationale**: These files contain critical game data that must match exactly for functional compatibility.

**Reference**: [`Tools/HolocronToolset/tests/data/test_kit_generation.py:912-970`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/tests/data/test_kit_generation.py#L912-L970)

### Approximate Matching (Tolerance-Based)

**Image files** (TGA/[TPC](TPC-File-Format) - pixel-by-pixel comparison):

- **Dimensions**: Must match exactly (width × height)
- **Pixel data**: Allows tolerance for compression artifacts:
  - Up to **2 levels difference** per channel (R, G, B, A) per pixel
  - Up to **1% of pixels** can differ by more than 2 levels
  - Accounts for DXT compression artifacts in [TPC files](TPC-File-Format)

**Rationale**: [TPC files](TPC-File-Format) use DXT compression which can introduce small pixel differences even for identical source images.

**Reference**: [`Tools/HolocronToolset/tests/data/test_kit_generation.py:972-1111`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/tests/data/test_kit_generation.py#L972-L1111)

### structure-Only Verification (No value Comparison)

**JSON Metadata** (structure verification only):

- **Doorhook coordinates**: Only verifies that `x`, `y`, `z`, `rotation` fields exist - **does NOT compare actual values**
- **Door Dimensions**: Only verifies that `width`, `height` fields exist - **does NOT compare actual values**
- **Doorhook count**: Verifies count matches exactly
- **Component count**: Verifies count matches exactly
- **Door count**: Verifies count matches exactly
- **field Presence**: Verifies required fields exist (name, id, door, [edge](BWM-File-Format#edges))

**Current Test Behavior**:

```python
# Lines 1229-1234: Only checks field existence, not values
self.assertIn("x", gen_hook, f"Component {i} hook {j} missing x")
self.assertIn("y", gen_hook, f"Component {i} hook {j} missing y")
self.assertIn("z", gen_hook, f"Component {i} hook {j} missing z")
self.assertIn("rotation", gen_hook, f"Component {i} hook {j} missing rotation")
# NO assertEqual or assertAlmostEqual for coordinate values!

# Lines 1182-1185: Only checks field existence, not values
if "width" in exp_door:
    self.assertIn("width", gen_door, f"Door {i} missing width")
if "height" in exp_door:
    self.assertIn("height", gen_door, f"Door {i} missing height")
# NO assertEqual or assertAlmostEqual for dimension values!
```

**Rationale**: Tests were designed to be lenient during initial development when doorhook extraction and door dimension calculation were incomplete. The comment on line 1114 states: "handling differences in components/doorhooks that may not be fully extracted yet."

**Implications**:

- **Doorhook coordinates are NOT validated** - tests will pass even if coordinates are completely wrong
- **Door dimensions are NOT validated** - tests will pass even if dimensions are incorrect
- **High granularity matching is NOT enforced** - coordinate precision is not verified
- **Error acceptability is currently 100%** - any coordinate values are accepted as long as fields exist

**Reference**: [`Tools/HolocronToolset/tests/data/test_kit_generation.py:1113-1234`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Tools/HolocronToolset/tests/data/test_kit_generation.py#L1113-L1234)

### Recommended Test Improvements

To achieve high granularity coordinate matching, the tests should be enhanced to:

1. **Compare Doorhook coordinates**:

   ```python
   # Use assertAlmostEqual with appropriate tolerance for floating-point comparison
   self.assertAlmostEqual(gen_hook.get("x"), exp_hook.get("x"), places=6, 
                          msg=f"Component {i} hook {j} x coordinate differs")
   self.assertAlmostEqual(gen_hook.get("y"), exp_hook.get("y"), places=6,
                          msg=f"Component {i} hook {j} y coordinate differs")
   self.assertAlmostEqual(gen_hook.get("z"), exp_hook.get("z"), places=6,
                          msg=f"Component {i} hook {j} z coordinate differs")
   self.assertAlmostEqual(gen_hook.get("rotation"), exp_hook.get("rotation"), places=2,
                          msg=f"Component {i} hook {j} rotation differs")
   ```

2. **Compare Door Dimensions**:

   ```python
   # Use assertAlmostEqual with appropriate tolerance
   if "width" in exp_door:
       self.assertAlmostEqual(gen_door.get("width"), exp_door.get("width"), places=2,
                              msg=f"Door {i} width differs")
   if "height" in exp_door:
       self.assertAlmostEqual(gen_door.get("height"), exp_door.get("height"), places=2,
                              msg=f"Door {i} height differs")
   ```

3. **Tolerance Levels**:
   - **Coordinates (x, y, z)**: 6 decimal places (0.000001 units) - matches Python [float](GFF-File-Format#gff-data-types) precision
   - **rotation**: 2 decimal places (0.01 degrees) - sufficient for door placement
   - **Dimensions (width, height)**: 2 decimal places (0.01 units) - sufficient for door sizing

**Current Status**: Tests are **NOT** performing 1:1 coordinate matching. They only verify structure, not values. This means tests can pass even if coordinates are incorrect, which may [mask](GFF-File-Format#gff-data-types) extraction bugs.

---

## Best Practices

1. **Component Naming**: Use descriptive, consistent naming (e.g., `hall_1`, `junction_2`)
2. **[texture](TPC-File-Format) Organization**: Group related [textures](TPC-File-Format) logically
3. **Always Folder**: Use sparingly for truly shared resources
4. **Door Definitions**: Ensure door [UTD](GFF-File-Format#utd-door) files match JSON definitions
5. **Hook Placement**: Place hooks at logical connection points (extracted from [BWM](BWM-File-Format) [edges](BWM-File-Format#edges) with transitions)
6. **Minimap Images**: Generate accurate top-down views for component selection
7. **[BWM](BWM-File-Format) Re-centering**: Always re-center BWMs to origin for proper alignment
8. **Resource Resolution**: Respect game engine resource resolution priority
9. **Batch Processing**: Use batch I/O operations for performance
10. **Error Handling**: Collect missing files instead of failing fast
11. **Vendor Compatibility**: Follow reone/KotOR.js patterns for [walkmesh](BWM-File-Format) and [model](MDL-MDX-File-Format) handling
12. **Comprehensive Extraction**: Extract all [DWK](BWM-File-Format) states and all referenced [textures](TPC-File-Format) for complete kits
13. **Test Precision**: Consider enhancing tests to verify coordinate values, not just structure

---

This documentation provides a comprehensive overview of the kit structure and how kits are used in the Holocron Toolset for generating indoor maps.
