# KotOR TXI file format Documentation

TXI ([texture](TPC-File-Format) Info) files [ARE](GFF-File-Format#are-area) compact ASCII descriptors that attach metadata to [TPC](TPC-File-Format) [textures](TPC-File-Format). They control mipmap usage, filtering, [flipbook animation](#animation-and-flipbooks), environment mapping, font atlases, and platform-specific downsampling. Every TXI file is parsed at runtime to configure how a [TPC](TPC-File-Format) image is rendered.

## Table of Contents

- KotOR TXI file format Documentation
  - Table of Contents
  - [format Overview](#format-overview)
  - [Syntax](#syntax)
    - [Command Lines](#command-lines)
    - [coordinate Blocks](#coordinate-blocks)
  - [Command Reference](#command-reference)
    - [Rendering and Filtering](#rendering-and-filtering)
    - [material and Environment Controls](#material-and-environment-controls)
    - [animation and Flipbooks](#animation-and-flipbooks)
    - [Font Atlas Layout](#font-atlas-layout)
    - [Streaming and Platform Hints](#streaming-and-platform-hints)
  - [Relationship to TPC textures](#relationship-to-tpc-textures)
    - [Empty TXI files](#empty-txi-files)
  - [Implementation Details](#implementation-details)

---

## format Overview

- TXI files [ARE](GFF-File-Format#are-area) plain-text [KEY](KEY-File-Format)/value lists; each command modifies a field in the [TPC](TPC-File-Format) runtime metadata.  
- Commands [ARE](GFF-File-Format#are-area) case-insensitive but conventionally lowercase. values can be integers, floats, booleans (`0`/`1`), [ResRefs](GFF-File-Format#gff-data-types), or multi-line coordinate tables.  
- A single TXI can be appended to the end of a `.tpc` file (as Bioware does) or shipped as a sibling `.txi` file; the parser treats both identically.  

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/txi/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/txi)

**Vendor References:**

- [`vendor/reone/src/libs/graphics/format/txireader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/txireader.cpp) - Complete C++ TXI parser implementation
- [`vendor/xoreos/src/graphics/images/txi.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/images/txi.cpp) - Generic Aurora TXI implementation (shared format)
- [`vendor/KotOR.js/src/resource/TXIObject.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TXIObject.ts) - TypeScript TXI parser with metadata extraction
- [`vendor/KotOR.js/src/enums/graphics/txi/`](https://github.com/th3w1zard1/KotOR.js/tree/master/src/enums/graphics/txi) - TXI command enumerations
- [`vendor/KotOR-Unity/Assets/Scripts/Resource/TXI.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/Resource/TXI.cs) - C# Unity TXI loader

**See Also:**

- [TPC File Format](TPC-File-Format) - [texture](TPC-File-Format) format that TXI metadata describes
- [MDL/MDX File Format](MDL-MDX-File-Format) - [models](MDL-MDX-File-Format) that reference [textures](TPC-File-Format) with TXI metadata  

---

## Syntax

### Command Lines

```
<command> <value(s)>
```

- Whitespace between command and value is ignored beyond the first separator.  
- Boolean toggles use `0` or `1`.  
- Multiple values (e.g., `channelscale 1.0 0.5 0.5`) are space-separated.  
- Comments [ARE](GFF-File-Format#are-area) not supported; unknown commands [ARE](GFF-File-Format#are-area) skipped.  

### coordinate Blocks

Commands such as `upperleftcoords` and `lowerrightcoords` declare the number of rows, followed by that many lines of coordinates:

```
upperleftcoords 96
0.000000 0.000000 0
0.031250 0.000000 0
...
```

Each line encodes a UV triplet; UV coordinates follow standard UV mapping conventions (normalized 0–1, `z` column unused).  

---

## Command Reference

> The tables below summarize the commands implemented by PyKotor’s `TXICommand` enum. values map directly to the fields described in [`txi_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKyor/resource/formats/txi/txi_data.py#L700-L830).

### Rendering and Filtering

| Command | Accepted values | Description |
| ------- | ---------------- | ----------- |
| `mipmap` | `0`/`1` | Toggles engine mipmap usage (KotOR's sampler mishandles secondary mips; Bioware [textures](TPC-File-Format) usually set `0`). |
| `filter` | `0`/`1` | Enables simple bilinear filtering of font atlases; `<1>` applies a blur. |
| `clamp` | `0`/`1` | Forces address mode clamp instead of wrap. |
| `candownsample`, `downsamplemin`, `downsamplemax`, `downsamplefactor` | ints/floats | Hints used by Xbox [texture](TPC-File-Format) reduction. |
| `priority` | integer | Streaming priority for on-demand textures (higher loads earlier). |
| `temporary` | `0`/`1` | Marks a [texture](TPC-File-Format) as discardable after use. |
| `ondemand` | `0`/`1` | Delays [texture](TPC-File-Format) loading until first reference. |

### [material](MDL-MDX-File-Format#trimesh-header) and Environment Controls

| Command | Description |
| ------- | ----------- |
| `blending` | Selects additive or punchthrough blending (see [`TXIBlending.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/graphics/txi/TXIBlending.ts)). |
| `decal` | Toggles decal rendering so polygons project onto [geometry](MDL-MDX-File-Format#geometry-header). |
| `isbumpmap`, `isdiffusebumpmap`, `isspecularbumpmap` | [flag](GFF-File-Format#gff-data-types) the [texture](TPC-File-Format) as a bump/normal map; controls how [material](MDL-MDX-File-Format#trimesh-header) shaders sample it. |
| `bumpmaptexture`, `bumpyshinytexture`, `envmaptexture`, `bumpmapscaling` | Supply companion [textures](TPC-File-Format) and scales for per-pixel lighting. |
| `cube` | Marks the [texture](TPC-File-Format) as a cube map; used with 6-[face](MDL-MDX-File-Format#face-structure) TPCs. |
| `unique` | Forces the renderer to keep a dedicated instance instead of sharing. |

### [animation](MDL-MDX-File-Format#animation-header) and Flipbooks

[texture](TPC-File-Format) flipbook animation relies on sprite sheets that tile frames across the atlas:

| Command | Description |
| ------- | ----------- |
| `proceduretype` | Set to `cycle` to enable flipbook [animation](MDL-MDX-File-Format#animation-header). |
| `numx`, `numy` | Horizontal/vertical frame counts. |
| `fps` | Frames per second for playback. |
| `speed` | Legacy alias for `fps` (still parsed for compatibility). |

When `proceduretype=cycle`, PyKotor splits the [TPC](TPC-File-Format) into `numx × numy` layers and advances them at `fps` (see [`io_tpc.py:169-190`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/tpc/io_tpc.py#L169-L190)).

### Font Atlas Layout

KotOR’s bitmap fonts use TXI commands to describe glyph boxes:

| Command | Description |
| ------- | ----------- |
| `baselineheight`, `fontheight`, `fontwidth`, `caretindent`, `spacingB`, `spacingR` | Control glyph metrics for UI fonts. |
| `rows`, `cols`, `numchars`, `numcharspersheet` | Describe how many glyphs [ARE](GFF-File-Format#are-area) stored per sheet. |
| `upperleftcoords`, `lowerrightcoords` | arrays of UV coordinates for each glyph corner. |
| `codepage`, `isdoublebyte`, `dbmapping` | Support multi-[byte](GFF-File-Format#gff-data-types) font atlases (Asian locales). |

KotOR.js exposes identical structures in [`src/resource/TXI.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TXI.ts#L16-L255), ensuring the coordinates here match the engine’s expectations.

### Streaming and Platform Hints

| Command | Description |
| ------- | ----------- |
| `defaultwidth`, `defaultheight`, `defaultbpp` | Provide fallback metadata for UI [textures](TPC-File-Format) when resolution switching. |
| `xbox_downsample`, `maxSizeHQ`, `maxSizeLQ`, `minSizeHQ`, `minSizeLQ` | Limit [texture](TPC-File-Format) resolution on Xbox hardware. |
| `filerange` | Declares a sequence of numbered files (used by some animated sprites). |
| `controllerscript` | Associates a scripted [controller](MDL-MDX-File-Format#controllers) for advanced animation (rare in KotOR). |

---

## Relationship to [TPC](TPC-File-Format) [textures](TPC-File-Format)

- A TXI modifies the rendering pipeline for its paired [TPC](TPC-File-Format): mipmap [flags](GFF-File-Format#gff-data-types) alter sampler state, [animation](MDL-MDX-File-Format#animation-header) directives convert a single [texture](TPC-File-Format) into multiple layers, and [material](MDL-MDX-File-Format#trimesh-header) directives attach bump/shine maps.  
- When embedded inside a `.tpc` file, the TXI text starts immediately after the binary payload; PyKotor reads it by seeking past the [texture](TPC-File-Format) data and consuming the remaining bytes as ASCII (`io_tpc.py:158-188`).  
- Exported `.txi` files [ARE](GFF-File-Format#are-area) plain UTF-8 text and can be edited with any text editor; tools like `tga2tpc` and KotORBlender reserialize them alongside [TPC](TPC-File-Format) assets.

### Empty TXI files

Many TXI files in the game installation [ARE](GFF-File-Format#are-area) **empty** (0 bytes). These empty TXI files serve as placeholders and indicate that the [texture](TPC-File-Format) should use default rendering settings. When a TXI file is empty or missing, the engine falls back to default [texture](TPC-File-Format) parameters.

**Examples of [textures](TPC-File-Format) with empty TXI files:**

- `lda_bark04.txi` (0 bytes)
- `lda_flr11.txi` (0 bytes)
- `lda_grass07.txi` (0 bytes)
- `lda_grate01.txi` (0 bytes)
- `lda_ivy01.txi` (0 bytes)
- `lda_leaf02.txi` (0 bytes)
- `lda_lite01.txi` (0 bytes)
- `lda_rock06.txi` (0 bytes)
- `lda_sky0001.txi` through `lda_sky0005.txi` (0 bytes)
- `lda_trim02.txi`, `lda_trim03.txi`, `lda_trim04.txi` (0 bytes)
- `lda_unwal07.txi` (0 bytes)
- `lda_wall02.txi`, `lda_wall03.txi`, `lda_wall04.txi` (0 bytes)

**Examples of [textures](TPC-File-Format) with non-empty TXI files:**

- `lda_ehawk01.txi` - Contains `envmaptexture CM_jedcom`
- `lda_ehawk01a.txi` - Contains `envmaptexture CM_jedcom`
- `lda_flr07.txi` - Contains `bumpyshinytexture CM_dantii` and `bumpmaptexture LDA_flr01B`

**Kit Generation Note:** When generating kits from module RIM files, empty TXI files should still be created as placeholders even if they don't exist in the installation. This ensures kit completeness and matches the expected kit structure where many [textures](TPC-File-Format) have corresponding (empty) TXI files.  

---

## Implementation Details

- **Parser:** [`Libraries/PyKotor/src/pykotor/resource/formats/txi/io_txi.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/txi/io_txi.py)  
- **data [model](MDL-MDX-File-Format):** [`Libraries/PyKotor/src/pykotor/resource/formats/txi/txi_data.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/txi/txi_data.py)  
- **Reference Implementations:**  
  - [`vendor/reone/src/libs/graphics/format/txireader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/txireader.cpp)  
  - [`vendor/KotOR.js/src/resource/TXI.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/resource/TXI.ts)  
  - [`vendor/tga2tpc`](https://github.com/th3w1zard1/tga2tpc) (original Bioware converter)  

These sources all interpret commands the same way, so the tables above map directly to the behavior you will observe in-game.

---
