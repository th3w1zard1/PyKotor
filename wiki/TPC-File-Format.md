# KotOR [TPC](TPC-File-Format) file format Documentation

TPC ([texture](TPC-File-Format) Pack Container) is KotOR's native [texture](TPC-File-Format) format. It supports paletteless RGB/RGBA, greyscale, and block-compressed DXT1/DXT3/DXT5 data, optional mipmaps, cube maps, and [flipbook animations](TXI-File-Format#animation-and-flipbooks) controlled by companion [TXI files](TXI-File-Format).

## Table of Contents

- KotOR TPC File Format Documentation
  - Table of Contents
  - File Structure Overview
  - [Header Layout](#header-layout)
  - [Pixel Formats](#pixel-formats)
  - [Mipmaps, Layers, and Animation](#mipmaps-layers-and-animation)
  - [Cube Maps](#cube-maps)
  - [TXI Metadata](#txi-metadata)
  - [Implementation Details](#implementation-details)

---

## file structure Overview

| offset | size | Description |
| ------ | ---- | ----------- |
| 0 (0x00)   | 4    | data size (0 for uncompressed RGB; compressed [textures](TPC-File-Format) store total bytes) |
| 4 (0x04)   | 4    | Alpha test/threshold [float](GFF-File-Format#gff-data-types) |
| 8 (0x08)   | 2    | Width ([uint16](GFF-File-Format#gff-data-types)) |
| 10 (0x0A)   | 2    | Height ([uint16](GFF-File-Format#gff-data-types)) |
| 12 (0x0C)   | 1    | Pixel encoding [flag](GFF-File-Format#gff-data-types) |
| 13 (0x0D)   | 1    | Mipmap count |
| 14 (0x0E)   | 114 (0x72) | Reserved / padding |
| 128 (0x80)   | —    | [texture](TPC-File-Format) data (per layer, per mipmap) |
| ...    | —    | Optional ASCII [TXI](TXI-File-Format) footer |

This layout is identical across PyKotor, Reone, Xoreos, KotOR.js, and the original Bioware tools; KotOR-Unity and NorthernLights consume the same header.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc)

**Vendor References:**

- [`vendor/reone/src/libs/graphics/format/tpcreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/tpcreader.cpp) - Complete C++ [TPC](TPC-File-Format) decoder with DXT decompression
- [`vendor/xoreos/src/graphics/images/tpc.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/images/tpc.cpp) - Generic Aurora [TPC](TPC-File-Format) implementation (shared format)
- [`vendor/KotOR.js/src/resource/TPCObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TPCObject.ts) - TypeScript [TPC](TPC-File-Format) loader with WebGL [texture](TPC-File-Format) upload
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/TextureResource.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/TextureResource.cs) - C# Unity [TPC](TPC-File-Format) loader with cube map support
- [`vendor/NorthernLights/src/Graphics/Textures/TPC.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/src/Graphics/Textures/TPC.cs) - .NET TPC reader with [animation](MDL-MDX-File-Format#animation-header) support
- [`vendor/tga2tpc/`](https://github.com/th3w1zard1/tga2tpc) - Standalone TGA to [TPC](TPC-File-Format) conversion tool
- [`vendor/xoreos-tools/src/images/tpc.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/images/tpc.cpp) - Command-line [TPC](TPC-File-Format) extraction and conversion

**See Also:**

- [TXI File Format](TXI-File-Format) - Metadata companion for [TPC](TPC-File-Format) [textures](TPC-File-Format)
- [MDL/MDX File Format](MDL-MDX-File-Format) - [models](MDL-MDX-File-Format) that reference [TPC](TPC-File-Format) [textures](TPC-File-Format)
- [GFF-GUI](GFF-GUI) - [GUI](GFF-File-Format#gui-graphical-user-interface) files that reference [TPC](TPC-File-Format) [textures](TPC-File-Format) for UI elements

---

## header Layout

| field | Description |
| ----- | ----------- |
| `data_size` | If non-zero, specifies total compressed payload size; uncompressed [textures](TPC-File-Format) set this to 0 and derive size from format/width/height. |
| `alpha_test` | Float threshold used by punch-through rendering (commonly `0.0` or `0.5`). |
| `pixel_encoding` | Bitfield describing format (see next section). |
| `mipmap_count` | Number of mip levels per layer (minimum 1). |
| Reserved | 0x72 bytes reserved; KotOR stores platform hints here but all implementations skip them. |

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:112-167`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L112-L167)

---

## Pixel formats

[TPC](TPC-File-Format) supports the following encodings (documented in `TPCTextureFormat`):

| Encoding | Description | Notes |
| -------- | ----------- | ----- |
| `0x01` (Greyscale) | 8-bit luminance | Stored as linear bytes |
| `0x02` (RGB) | 24-bit RGB | Linear bytes, may be swizzled on Xbox |
| `0x04` (RGBA) | 32-bit RGBA | Linear bytes |
| `0x0C` (BGRA) | 32-bit BGRA swizzled | Xbox-specific swizzle; PyKotor deswizzles on load |
| DXT1 | Block-compressed (4×4 blocks, 8 bytes) | Detected via `data_size` and encoding [flags](GFF-File-Format#gff-data-types) |
| DXT3/DXT5 | Block-compressed (4×4 blocks, 16 bytes) | Chosen based on `pixel_type` and compression [flag](GFF-File-Format#gff-data-types) |

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py:54-178`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py#L54-L178)

---

## Mipmaps, Layers, and [animation](MDL-MDX-File-Format#animation-header)

- Each [texture](TPC-File-Format) can have multiple **layers** (used for cube maps or animated flipbooks).  
- Every layer stores `mipmap_count` levels. For uncompressed [textures](TPC-File-Format), each level’s size equals `width × height × bytes_per_pixel`; for DXT formats it equals the block size calculation.  
- Animated [textures](TPC-File-Format) rely on [TXI](TXI-File-Format) fields (`proceduretype cycle`, `numx`, `numy`, `fps`). PyKotor splits the sprite sheet into layers and recalculates mip counts per frame.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:216-285`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L216-L285)

---

## Cube Maps

- Detected when the stored height is exactly six times the width for compressed textures (`DXT1/DXT5`).  
- PyKotor normalizes cube [faces](MDL-MDX-File-Format#face-structure) after reading (deswizzle + rotation) so that [face](MDL-MDX-File-Format#face-structure) ordering matches the high-level [texture](TPC-File-Format) API.  
- Reone and KotOR.js use the same inference logic, so the cube-map detection below mirrors their behavior.  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:138-285`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L138-L285)

---

## [TXI](TXI-File-Format) Metadata

- If bytes remain after the [texture](TPC-File-Format) payload, they [ARE](GFF-File-Format#are-area) treated as ASCII [TXI](TXI-File-Format) content.  
- [TXI](TXI-File-Format) commands drive [animations](MDL-MDX-File-Format#animation-header), environment mapping, font metrics, downsampling directives, etc. See the [TXI File Format](TXI-File-Format) document for exhaustive command descriptions.  
- PyKotor automatically parses the [TXI](TXI-File-Format) footer and exposes `TPC.txi` plus convenience flags (`is_animated`, `is_cube_map`).  

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py:159-188`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L159-L188)

---

## Implementation Details

- **Binary Reader/Writer:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py)  
- **data [model](MDL-MDX-File-Format) & Conversion Utilities:** [`Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/tpc_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/graphics/format/tpcreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/tpcreader.cpp)  
  - [`vendor/xoreos-tools/src/graphics/tpc.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/graphics/tpc.cpp)  
  - [`vendor/tga2tpc`](https://github.com/th3w1zard1/tga2tpc)
  - [`vendor/KotOR.js/src/loaders/TextureLoader.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/loaders/TextureLoader.ts)  

All of the engines listed above treat the header and mipmap data identically. The only notable difference is that KotOR.js stores [textures](TPC-File-Format) as WebGL-friendly blobs internally, but it imports/exports the same [TPC](TPC-File-Format) binary format.
