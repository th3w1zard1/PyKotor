# [PLT files](PLT-File-Format) [format](GFF-File-Format) Documentation (Neverwinter Nights)

PLT ([texture](TPC-File-Format) Palette [file](GFF-File-Format)) is a variant [texture](TPC-File-Format) [format](GFF-File-Format) that allows runtime [color](GFF-File-Format#color) palette selection. Instead of fixed [colors](GFF-File-Format#color), [PLT files](PLT-File-Format) store palette group [indices](2DA-File-Format#row-labels) and [color](GFF-File-Format#color) [indices](2DA-File-Format#row-labels) that reference external palette [files](GFF-File-Format), enabling dynamic [color](GFF-File-Format#color) customization for character [models](MDL-MDX-File-Format).

**Note**: [PLT files](PLT-File-Format) [ARE](GFF-File-Format#are-area) used in **Neverwinter Nights** for character customization (skin, hair, armor [colors](GFF-File-Format#color), etc.). While the [PLT](PLT-File-Format) resource type (0x0006) is defined in KotOR's resource system, **[PLT files](PLT-File-Format) [ARE](GFF-File-Format#are-area) not actually used in KotOR games**. KotOR uses standard [TPC](TPC-File-Format)/TGA/DDS [textures](TPC-File-Format) instead. This documentation is provided for completeness and compatibility with Neverwinter Nights tools that may work with KotOR's resource system.

## Table of Contents

- [PLT File Format Documentation (Neverwinter Nights)](#plt-file-format-documentation-neverwinter-nights)
  - [Table of Contents](#table-of-contents)
  - [File Structure Overview](#file-structure-overview)
  - [Palette System](#palette-system)
    - [Palette Groups](#palette-groups)
    - [Color Resolution Process](#color-resolution-process)
  - [Binary Format](#binary-format)
    - [File Header](#file-header)
    - [Pixel Data](#pixel-data)
  - [Implementation Details](#implementation-details)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) Overview

[PLT files](PLT-File-Format) work in conjunction with external palette files (`.pal` [files](GFF-File-Format)) that contain the actual [color](GFF-File-Format#color) [values](GFF-File-Format#data-types). The [PLT file](PLT-File-Format) itself stores:

1. **Palette Group [index](2DA-File-Format#row-labels)**: Which palette group (0-9) to use for each pixel
2. **[color](GFF-File-Format#color) [index](2DA-File-Format#row-labels)**: Which color (0-255) within the selected palette to use

At runtime, the game:

1. Loads the appropriate palette [file](GFF-File-Format) for the selected palette group
2. Uses the palette index (supplied by the content creator) to select a row in the palette [file](GFF-File-Format)
3. Uses the [color](GFF-File-Format#color) [index](2DA-File-Format#row-labels) from the [PLT file](PLT-File-Format) to retrieve the final [color](GFF-File-Format#color) [value](GFF-File-Format#data-types)

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Tim Smith (Torlack)'s reverse-engineered [PLT](PLT-File-Format) [format](GFF-File-Format) documentation

---

## Palette System

### Palette Groups

There [ARE](GFF-File-Format#are-area) ten palette groups, each corresponding to a different [material](MDL-MDX-File-Format#trimesh-header) [type](GFF-File-Format#data-types) on character [models](MDL-MDX-File-Format):

| Group [index](2DA-File-Format#row-labels) | Name      | Description                                    | Palette [file](GFF-File-Format) Example |
| ----------- | --------- | ---------------------------------------------- | -------------------- |
| 0           | Skin      | Character skin tones                           | `pal_skin01.jpg`     |
| 1           | Hair      | Hair [colors](GFF-File-Format#color)                                    | `pal_hair01.jpg`     |
| 2           | Metal 1   | Primary metal/armor [colors](GFF-File-Format#color)                     | `pal_armor01.jpg`    |
| 3           | Metal 2   | Secondary metal/armor [colors](GFF-File-Format#color)                   | `pal_armor02.jpg`    |
| 4           | Cloth 1   | Primary fabric/clothing [colors](GFF-File-Format#color)                 | `pal_cloth01.jpg`    |
| 5           | Cloth 2   | Secondary fabric/clothing [colors](GFF-File-Format#color)               | `pal_cloth01.jpg`    |
| 6           | Leather 1 | Primary leather [material](MDL-MDX-File-Format#trimesh-header) [colors](GFF-File-Format#color)                | `pal_leath01.jpg`    |
| 7           | Leather 2 | Secondary leather [material](MDL-MDX-File-Format#trimesh-header) [colors](GFF-File-Format#color)              | `pal_leath01.jpg`    |
| 8           | Tattoo 1  | Primary tattoo/body paint [colors](GFF-File-Format#color)               | `pal_tattoo01.jpg`   |
| 9           | Tattoo 2  | Secondary tattoo/body paint [colors](GFF-File-Format#color)             | `pal_tattoo01.jpg`   |

**Palette [file](GFF-File-Format) [structure](GFF-File-Format#file-structure)**: Each palette [file](GFF-File-Format) contains 256 rows (one for each palette [index](2DA-File-Format#row-labels) 0-255), with each row containing 256 [color](GFF-File-Format#color) values (one for each [color](GFF-File-Format#color) [index](2DA-File-Format#row-labels) 0-255).

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Palette groups table and description

### [color](GFF-File-Format#color) Resolution Process

To determine the final [color](GFF-File-Format#color) for a pixel in a [PLT](PLT-File-Format) [texture](TPC-File-Format):

1. **Get Palette Group**: Read the palette group index (0-9) from the [PLT](PLT-File-Format) pixel [data](GFF-File-Format#file-structure)
2. **Get Palette [index](2DA-File-Format#row-labels)**: Retrieve the palette index (0-255) for that group from the content creator's settings (supplied at runtime, not stored in [PLT](PLT-File-Format))
3. **Select Palette Row**: Use the palette [index](2DA-File-Format#row-labels) to select a row in the corresponding palette file
4. **Get Color Index**: Read the color index (0-255) from the [PLT](PLT-File-Format) pixel [data](GFF-File-Format#file-structure)
5. **Retrieve [color](GFF-File-Format#color)**: Use the [color](GFF-File-Format#color) [index](2DA-File-Format#row-labels) to get the final RGB [color](GFF-File-Format#color) [value](GFF-File-Format#data-types) from the selected palette row

**Example**: A pixel with palette group [index](2DA-File-Format#row-labels) `2` (Metal 1) and [color](GFF-File-Format#color) [index](2DA-File-Format#row-labels) `128`:

- If the content creator selected palette [index](2DA-File-Format#row-labels) `5` for Metal 1
- The game loads `pal_armor01.jpg` and reads row 5, column 128
- The RGB [value](GFF-File-Format#data-types) at that [position](MDL-MDX-File-Format#node-header) becomes the pixel's [color](GFF-File-Format#color)

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - [color](GFF-File-Format#color) resolution example

---

## Binary [format](GFF-File-Format)

### [file](GFF-File-Format) [header](GFF-File-Format#file-header)

The [PLT file](PLT-File-Format) [header](GFF-File-Format#file-header) is 24 bytes:

| Name      | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                    |
| --------- | ------- | ------ | ---- | ---------------------------------------------- |
| Signature | [char][GFF-File-Format#char](4) | 0 (0x0000) | 4    | Always `"PLT "` (space-padded)                  |
| Version   | [char][GFF-File-Format#char](4) | 4 (0x0004) | 4    | Always `"V1  "` (space-padded)                  |
| Unknown   | [uint32](GFF-File-Format#dword)  | 8 (0x0008) | 4    | Unknown [value](GFF-File-Format#data-types)                                  |
| Unknown   | [uint32](GFF-File-Format#dword)  | 12 (0x000C) | 4    | Unknown [value](GFF-File-Format#data-types)                                  |
| Width     | [uint32](GFF-File-Format#dword)  | 16 (0x0010) | 4    | [texture](TPC-File-Format) width in pixels                         |
| Height    | [uint32](GFF-File-Format#dword)  | 20 (0x0014) | 4    | [texture](TPC-File-Format) height in pixels                       |

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - [PLT file](PLT-File-Format) [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure)

### Pixel [data](GFF-File-Format#file-structure)

Following the [header](GFF-File-Format#file-header), pixel [data](GFF-File-Format#file-structure) is stored as an [array](2DA-File-Format) of 2-[byte](GFF-File-Format#byte) [structures](GFF-File-Format#file-structure). There [ARE](GFF-File-Format#are-area) `width × height` pixel entries.

Each pixel entry is 2 bytes:

| Name              | [type](GFF-File-Format#data-types)   | [offset](GFF-File-Format#file-structure) | [size](GFF-File-Format#file-structure) | Description                                    |
| ----------------- | ------ | ------ | ---- | ---------------------------------------------- |
| [color](GFF-File-Format#color) [index](2DA-File-Format#row-labels)       | [uint8](GFF-File-Format#byte)  | 0 (0x0000) | 1    | [color](GFF-File-Format#color) index (0-255) within the selected palette |
| Palette Group [index](2DA-File-Format#row-labels) | [uint8](GFF-File-Format#byte) | 1 (0x0001) | 1    | Palette group index (0-9)                      |

**Pixel [data](GFF-File-Format#file-structure) Layout**: Pixels [ARE](GFF-File-Format#are-area) stored row by row, left to right, top to bottom. The total pixel [data](GFF-File-Format#file-structure) [size](GFF-File-Format#file-structure) is `width × height × 2` bytes.

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Pixel [data](GFF-File-Format#file-structure) [structure](GFF-File-Format#file-structure)

---

## Implementation Details

**KotOR vs Neverwinter Nights**:

- **Neverwinter Nights**: [PLT files](PLT-File-Format) [ARE](GFF-File-Format#are-area) actively used for character customization. The xoreos engine includes a complete [PLT](PLT-File-Format) implementation (`vendor/xoreos/src/graphics/aurora/pltfile.cpp`) that is used in NWN's creature system (`vendor/xoreos/src/engines/nwn/creature.cpp`).

- **KotOR**: While the [PLT](PLT-File-Format) resource type (0x0006) is defined in KotOR's resource [type](GFF-File-Format#data-types) system, **[PLT files](PLT-File-Format) [ARE](GFF-File-Format#are-area) not actually used in KotOR games**. KotOR uses standard [TPC](TPC-File-Format) [textures](TPC-File-Format) for all [textures](TPC-File-Format), including character [models](MDL-MDX-File-Format). No KotOR-specific implementations load or parse [PLT files](PLT-File-Format).

**Why Document [PLT](PLT-File-Format) for KotOR?**: The [format](GFF-File-Format) is documented here because:

1. The resource [type](GFF-File-Format#data-types) exists in KotOR's resource system (shared Aurora engine heritage)
2. NWN-derived tools may need to understand [PLT](PLT-File-Format) when working with KotOR resources
3. The xoreos-docs specification is part of the Aurora engine documentation corpus

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Complete [PLT](PLT-File-Format) [format](GFF-File-Format) specification  
**Reference**: [`vendor/xoreos/src/graphics/aurora/pltfile.cpp`](vendor/xoreos/src/graphics/aurora/pltfile.cpp) - xoreos [PLT](PLT-File-Format) implementation (NWN-specific)  
**Reference**: [`vendor/xoreos/src/engines/nwn/creature.cpp:573-589`](vendor/xoreos/src/engines/nwn/creature.cpp#L573-L589) - NWN creature [PLT](PLT-File-Format) usage

---

This documentation aims to provide a comprehensive overview of the [PLT file](PLT-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure) and palette system used in Neverwinter Nights (part of the BioWare Aurora engine family).
