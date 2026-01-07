# PLT files format Documentation

> **⚠️ NOT USED IN KOTOR**: This format is **Neverwinter Nights-specific** and is **NOT used in KotOR games**. While the PLT resource type (0x0006) exists in KotOR's resource system due to shared Aurora engine heritage, **KotOR does not load, parse, or use PLT files**. KotOR uses standard [TPC](TPC-File-Format)/TGA/DDS [textures](TPC-File-Format) for all [textures](TPC-File-Format), including character [models](MDL-MDX-File-Format). This documentation is provided for reference only, as NWN-derived tools may encounter PLT resource type identifiers when working with KotOR's resource system.

PLT ([texture](TPC-File-Format) Palette file) is a variant [texture](TPC-File-Format) format used in **Neverwinter Nights** that allows runtime color palette selection. Instead of fixed colors, PLT files store palette group indices and color indices that reference external palette files, enabling dynamic color customization for character [models](MDL-MDX-File-Format) (skin, hair, armor colors, etc.).

## Table of Contents

- PLT files format Documentation
  - Table of Contents
  - [file structure Overview](#file-structure-overview)
  - [Palette System](#palette-system)
    - [Palette Groups](#palette-groups)
    - [color Resolution Process](#color-resolution-process)
  - [Binary format](#binary-format)
    - [file header](#file-header)
    - [Pixel data](#pixel-data)
  - [Implementation Details](#implementation-details)

---

## file structure Overview

PLT files work in conjunction with external palette files (`.pal` files) that contain the actual color values. The PLT file itself stores:

1. **Palette Group index**: Which palette group (0-9) to use for each pixel
2. **color index**: Which color (0-255) within the selected palette to use

At runtime, the game:

1. Loads the appropriate palette file for the selected palette group
2. Uses the palette index (supplied by the content creator) to select a row in the palette file
3. Uses the color index from the PLT file to retrieve the final color value

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/plt.html) - Tim Smith (Torlack)'s reverse-engineered PLT format documentation

---

## Palette System

### Palette Groups

There are ten palette groups, each corresponding to a different [material](MDL-MDX-File-Format#trimesh-header) type on character [models](MDL-MDX-File-Format):

| Group index | Name      | Description                                    | Palette file Example |
| ----------- | --------- | ---------------------------------------------- | -------------------- |
| 0           | Skin      | Character skin tones                           | `pal_skin01.jpg`     |
| 1           | Hair      | Hair colors                                    | `pal_hair01.jpg`     |
| 2           | Metal 1   | Primary metal/armor colors                     | `pal_armor01.jpg`    |
| 3           | Metal 2   | Secondary metal/armor colors                   | `pal_armor02.jpg`    |
| 4           | Cloth 1   | Primary fabric/clothing colors                 | `pal_cloth01.jpg`    |
| 5           | Cloth 2   | Secondary fabric/clothing colors               | `pal_cloth01.jpg`    |
| 6           | Leather 1 | Primary leather [material](MDL-MDX-File-Format#trimesh-header) colors                | `pal_leath01.jpg`    |
| 7           | Leather 2 | Secondary leather [material](MDL-MDX-File-Format#trimesh-header) colors              | `pal_leath01.jpg`    |
| 8           | Tattoo 1  | Primary tattoo/body paint colors               | `pal_tattoo01.jpg`   |
| 9           | Tattoo 2  | Secondary tattoo/body paint colors             | `pal_tattoo01.jpg`   |

**Palette file structure**: Each palette file contains 256 rows (one for each palette index 0-255), with each row containing 256 color values (one for each color index 0-255).

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/plt.html) - Palette groups table and description

### color Resolution Process

To determine the final color for a pixel in a PLT [texture](TPC-File-Format):

1. **Get Palette Group**: Read the palette group index (0-9) from the PLT pixel data
2. **Get Palette index**: Retrieve the palette index (0-255) for that group from the content creator's settings (supplied at runtime, not stored in PLT)
3. **Select Palette Row**: Use the palette index to select a row in the corresponding palette file
4. **Get Color index**: Read the color index (0-255) from the PLT pixel data
5. **Retrieve color**: Use the color index to get the final RGB color value from the selected palette row

**Example**: A pixel with palette group index `2` (Metal 1) and color index `128`:

- If the content creator selected palette index `5` for Metal 1
- The game loads `pal_armor01.jpg` and reads row 5, column 128
- The RGB value at that position becomes the pixel's color

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/plt.html) - color resolution example

---

## Binary format

### file header

The PLT file header is 24 bytes:

| Name      | type    | offset | size | Description                                    |
| --------- | ------- | ------ | ---- | ---------------------------------------------- |
| Signature | [char](GFF-File-Format#gff-data-types) | 0 (0x0000) | 4    | Always `"PLT "` (space-padded)                  |
| Version   | [char](GFF-File-Format#gff-data-types) | 4 (0x0004) | 4    | Always `"V1  "` (space-padded)                  |
| Unknown   | [uint32](GFF-File-Format#gff-data-types)  | 8 (0x0008) | 4    | Unknown value                                  |
| Unknown   | [uint32](GFF-File-Format#gff-data-types)  | 12 (0x000C) | 4    | Unknown value                                  |
| Width     | [uint32](GFF-File-Format#gff-data-types)  | 16 (0x0010) | 4    | [texture](TPC-File-Format) width in pixels                         |
| Height    | [uint32](GFF-File-Format#gff-data-types)  | 20 (0x0014) | 4    | [texture](TPC-File-Format) height in pixels                       |

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/plt.html) - PLT file header structure

### Pixel data

Following the header, pixel data is stored as an array of 2-[byte](GFF-File-Format#gff-data-types) structures. There are `width × height` pixel entries.

Each pixel entry is 2 bytes:

| Name              | type   | offset | size | Description                                    |
| ----------------- | ------ | ------ | ---- | ---------------------------------------------- |
| color index       | [uint8](GFF-File-Format#gff-data-types)  | 0 (0x0000) | 1    | color index (0-255) within the selected palette |
| Palette Group index | [uint8](GFF-File-Format#gff-data-types) | 1 (0x0001) | 1    | Palette group index (0-9)                      |

**Pixel data Layout**: Pixels are stored row by row, left to right, top to bottom. The total pixel data size is `width × height × 2` bytes.

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/plt.html) - Pixel data structure

---

## Implementation Details

**KotOR vs Neverwinter Nights**:

- **Neverwinter Nights**: PLT files are actively used for character customization. The xoreos engine includes a complete PLT implementation (`vendor/xoreos/src/graphics/aurora/pltfile.cpp`) that is used in NWN's creature system (`vendor/xoreos/src/engines/nwn/creature.cpp`).

- **KotOR**: While the PLT resource type (0x0006) is defined in KotOR's resource type system, **PLT files are not actually used in KotOR games**. KotOR uses standard [TPC](TPC-File-Format) [textures](TPC-File-Format) for all [textures](TPC-File-Format), including character [models](MDL-MDX-File-Format). No KotOR-specific implementations load or parse PLT files.

**Why Document PLT for KotOR?**: The format is documented here because:

1. The resource type exists in KotOR's resource system (shared Aurora engine heritage)
2. NWN-derived tools may need to understand PLT when working with KotOR resources
3. The xoreos-docs specification is part of the Aurora engine documentation corpus

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/plt.html) - Complete PLT format specification  
**Reference**: [`vendor/xoreos/src/graphics/aurora/pltfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/aurora/pltfile.cpp) - xoreos PLT implementation (NWN-specific)  
**Reference**: [`vendor/xoreos/src/engines/nwn/creature.cpp:573-589`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/creature.cpp#L573-L589) - NWN creature PLT usage

---

This documentation aims to provide a comprehensive overview of the PLT file format, focusing on the detailed file structure and palette system used in Neverwinter Nights (part of the BioWare Aurora engine family).
