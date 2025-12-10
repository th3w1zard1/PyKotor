# KotOR PLT File Format Documentation

PLT (Texture Palette File) is a variant texture format that allows runtime color palette selection. Instead of fixed colors, PLT files store palette group indices and color indices that reference external palette files, enabling dynamic color customization for character models.

**Note**: PLT files are primarily used in Neverwinter Nights, but the format may be supported in KotOR for character customization features.

## Table of Contents

- [KotOR PLT File Format Documentation](#kotor-plt-file-format-documentation)
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

## File Structure Overview

PLT files work in conjunction with external palette files (`.pal` files) that contain the actual color values. The PLT file itself stores:

1. **Palette Group Index**: Which palette group (0-9) to use for each pixel
2. **Color Index**: Which color (0-255) within the selected palette to use

At runtime, the game:

1. Loads the appropriate palette file for the selected palette group
2. Uses the palette index (supplied by the content creator) to select a row in the palette file
3. Uses the color index from the PLT file to retrieve the final color value

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Tim Smith (Torlack)'s reverse-engineered PLT format documentation

---

## Palette System

### Palette Groups

There are ten palette groups, each corresponding to a different material type on character models:

| Group Index | Name      | Description                                    | Palette File Example |
| ----------- | --------- | ---------------------------------------------- | -------------------- |
| 0           | Skin      | Character skin tones                           | `pal_skin01.jpg`     |
| 1           | Hair      | Hair colors                                    | `pal_hair01.jpg`     |
| 2           | Metal 1   | Primary metal/armor colors                     | `pal_armor01.jpg`    |
| 3           | Metal 2   | Secondary metal/armor colors                   | `pal_armor02.jpg`    |
| 4           | Cloth 1   | Primary fabric/clothing colors                 | `pal_cloth01.jpg`    |
| 5           | Cloth 2   | Secondary fabric/clothing colors               | `pal_cloth01.jpg`    |
| 6           | Leather 1 | Primary leather material colors                | `pal_leath01.jpg`    |
| 7           | Leather 2 | Secondary leather material colors              | `pal_leath01.jpg`    |
| 8           | Tattoo 1  | Primary tattoo/body paint colors               | `pal_tattoo01.jpg`   |
| 9           | Tattoo 2  | Secondary tattoo/body paint colors             | `pal_tattoo01.jpg`   |

**Palette File Structure**: Each palette file contains 256 rows (one for each palette index 0-255), with each row containing 256 color values (one for each color index 0-255).

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Palette groups table and description

### Color Resolution Process

To determine the final color for a pixel in a PLT texture:

1. **Get Palette Group**: Read the palette group index (0-9) from the PLT pixel data
2. **Get Palette Index**: Retrieve the palette index (0-255) for that group from the content creator's settings (supplied at runtime, not stored in PLT)
3. **Select Palette Row**: Use the palette index to select a row in the corresponding palette file
4. **Get Color Index**: Read the color index (0-255) from the PLT pixel data
5. **Retrieve Color**: Use the color index to get the final RGB color value from the selected palette row

**Example**: A pixel with palette group index `2` (Metal 1) and color index `128`:

- If the content creator selected palette index `5` for Metal 1
- The game loads `pal_armor01.jpg` and reads row 5, column 128
- The RGB value at that position becomes the pixel's color

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Color resolution example

---

## Binary Format

### File Header

The PLT file header is 24 bytes:

| Name      | Type    | Offset | Size | Description                                    |
| --------- | ------- | ------ | ---- | ---------------------------------------------- |
| Signature | char[4] | 0x0000 | 4    | Always `"PLT "` (space-padded)                  |
| Version   | char[4] | 0x0004 | 4    | Always `"V1  "` (space-padded)                  |
| Unknown   | uint32  | 0x0008 | 4    | Unknown value                                  |
| Unknown   | uint32  | 0x000C | 4    | Unknown value                                  |
| Width     | uint32  | 0x0010 | 4    | Texture width in pixels                         |
| Height    | uint32  | 0x0014 | 4    | Texture height in pixels                       |

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - PLT file header structure

### Pixel Data

Following the header, pixel data is stored as an array of 2-byte structures. There are `width × height` pixel entries.

Each pixel entry is 2 bytes:

| Name              | Type   | Offset | Size | Description                                    |
| ----------------- | ------ | ------ | ---- | ---------------------------------------------- |
| Color Index       | uint8  | 0x0000 | 1    | Color index (0-255) within the selected palette |
| Palette Group Index | uint8 | 0x0001 | 1    | Palette group index (0-9)                      |

**Pixel Data Layout**: Pixels are stored row by row, left to right, top to bottom. The total pixel data size is `width × height × 2` bytes.

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Pixel data structure

---

## Implementation Details

**Note**: PLT file support in KotOR may be limited compared to Neverwinter Nights. The format is documented here for completeness and potential compatibility with NWN-derived tools.

**Reference**: [`vendor/xoreos-docs/specs/torlack/plt.html`](vendor/xoreos-docs/specs/torlack/plt.html) - Complete PLT format specification

---

This documentation aims to provide a comprehensive overview of the PLT file format, focusing on the detailed file structure and palette system used in BioWare Aurora engine games.
