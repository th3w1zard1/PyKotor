# KotOR [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) Documentation

This document provides a detailed description of the [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) [file](GFF-File-Format) [format](GFF-File-Format) used in Knights of the Old Republic (KotOR) games. The MDL ([model](MDL-MDX-File-Format)) and MDX ([model](MDL-MDX-File-Format) Extension) [files](GFF-File-Format) together define 3D [models](MDL-MDX-File-Format), including [geometry](MDL-MDX-File-Format#geometry-header), [animations](MDL-MDX-File-Format#animation-header), and other related [data](GFF-File-Format#file-structure-overview).

**Related [formats](GFF-File-Format):** [models](MDL-MDX-File-Format) [ARE](GFF-File-Format#are-area) referenced by [GFF files](GFF-File-Format) such as [UTC (Creature)](GFF-File-Format#utc-creature), [UTI (Item)](GFF-File-Format#uti-item), and [UTP (Placeable)](GFF-File-Format#utp-placeable) templates. [models](MDL-MDX-File-Format) may also use [TPC texture files](TPC-File-Format) and [TXI texture info files](TXI-File-Format).

## Table of Contents

- [KotOR MDL/MDX file format Documentation](#kotor-mdlmdx-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [file structure Overview](#file-structure-overview)
  - [file headers](#file-headers)
    - [MDL file header](#mdl-file-header)
    - [model header](#model-header)
    - [geometry header](#geometry-header)
    - [Names header](#names-header)
    - [animation header](#animation-header)
    - [Event structure](#event-structure)
  - [node structures](#node-structures)
    - [node header](#node-header)
    - [Trimesh header](#trimesh-header)
    - [Danglymesh header](#danglymesh-header)
    - [Skinmesh header](#skinmesh-header)
    - [Lightsaber header](#lightsaber-header)
    - [Light header](#light-header)
    - [Emitter header](#emitter-header)
    - [Reference header](#reference-header)
  - [controllers](#controllers)
    - [controller structure](#controller-structure)
  - [Additional controller types](#additional-controller-types)
    - [Light controllers](#light-controllers)
    - [Emitter controllers](#emitter-controllers)
    - [Mesh Controllers](#mesh-controllers)
  - [node types](#node-types)
    - [node type bitmasks](#node-type-bitmasks)
    - [Common node type Combinations](#common-node-type-combinations)
  - [MDX data format](#mdx-data-format)
    - [MDX data Bitmap masks](#mdx-data-bitmap-masks)
    - [Skin mesh Specific data](#skin-mesh-specific-data)
  - [vertex and face data](#vertex-and-face-data)
    - [vertex structure](#vertex-structure)
    - [face structure](#face-structure)
    - [vertex index arrays](#vertex-index-arrays)
  - [vertex data Processing](#vertex-data-processing)
    - [vertex Normal Calculation](#vertex-normal-calculation)
    - [Tangent Space Calculation](#tangent-space-calculation)
  - [model Classification flags](#model-classification-flags)
  - [file Identification](#file-identification)
    - [Binary vs ASCII format](#binary-vs-ascii-format)
    - [KotOR 1 vs KotOR 2 models](#kotor-1-vs-kotor-2-models)
  - [model Hierarchy](#model-hierarchy)
    - [node Relationships](#node-relationships)
    - [node transformations](#node-transformations)
  - [Smoothing Groups](#smoothing-groups)
  - [Binary model format Details (Aurora Engine)](#binary-model-format-details-aurora-engine)
    - [Binary model file Layout](#binary-model-file-layout)
    - [pointers and arrays in Binary models](#pointers-and-arrays-in-binary-models)
    - [model Routines and node type Identification](#model-routines-and-node-type-identification)
    - [Part Numbers](#part-numbers)
    - [controller data Storage](#controller-data-storage)
    - [Bezier Interpolation](#bezier-interpolation)
    - [AABB (Axis-Aligned bounding box) mesh nodes](#aabb-axis-aligned-bounding-box-mesh-nodes)
  - [ASCII MDL format](#ascii-mdl-format)
    - [model header Section](#model-header-section)
    - [geometry Section](#geometry-section)
    - [node Definitions](#node-definitions)
    - [animation data](#animation-data)
  - [controller data formats](#controller-data-formats)
    - [Single controllers](#single-controllers)
    - [Keyed controllers](#keyed-controllers)
    - [Special controller Cases](#special-controller-cases)
  - [Skin meshes and Skeletal animation](#skin-meshes-and-skeletal-animation)
    - [Bone Mapping and Lookup Tables](#bone-mapping-and-lookup-tables)
      - [Bone Map (`bonemap`)](#bone-map-bonemap)
      - [Bone Serial and node Number Lookups](#bone-serial-and-node-number-lookups)
    - [vertex Skinning](#vertex-skinning)
      - [Bone Weight Format (MDX)](#bone-weight-format-mdx)
      - [vertex transformation](#vertex-transformation)
    - [Bind Pose data](#bind-pose-data)
      - [QBones (quaternion rotations)](#qbones-quaternion-rotations)
      - [TBones (Translation vectors)](#tbones-translation-vectors)
      - [Bone matrix Computation](#bone-matrix-computation)
  - [Additional References](#additional-references)
    - [Editors](#editors)
    - [See Also](#see-also)

---

## [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) Overview

KotOR [models](MDL-MDX-File-Format) [ARE](GFF-File-Format#are-area) defined using two [files](GFF-File-Format):

- **[MDL](MDL-MDX-File-Format)**: Contains the primary [model](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview), including [geometry](MDL-MDX-File-Format#geometry-header) and [node](MDL-MDX-File-Format#node-structures) [structures](GFF-File-Format#file-structure-overview).
- **[MDX](MDL-MDX-File-Format)**: Contains additional [mesh](MDL-MDX-File-Format#trimesh-header) [data](GFF-File-Format#file-structure-overview), such as [vertex](MDL-MDX-File-Format#vertex-structure) buffers.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/mdl/`](Libraries/PyKotor/src/pykotor/resource/formats/mdl/)

**Vendor References:**

- [`vendor/reone/src/libs/graphics/format/mdlreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlreader.cpp) - Complete C++ [MDL](MDL-MDX-File-Format)/[MDX](MDL-MDX-File-Format) parser with [animation](MDL-MDX-File-Format#animation-header) support
- [`vendor/reone/include/reone/graphics/model.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/graphics/model.h) - Runtime [model](MDL-MDX-File-Format) class definition
- [`vendor/xoreos/src/graphics/aurora/model.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/aurora/model.cpp) - Generic Aurora [model](MDL-MDX-File-Format) implementation (shared [format](GFF-File-Format))
- [`vendor/KotOR.js/src/odyssey/OdysseyModel.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyModel.ts) - TypeScript [MDL](MDL-MDX-File-Format) parser with WebGL rendering
- [`vendor/KotOR.js/src/odyssey/OdysseyModel3.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyModel3.ts) - Enhanced [model](MDL-MDX-File-Format) loader with skinning support
- [`vendor/KotOR-Unity/Assets/Scripts/FileObjects/AuroraModel.cs`](https://github.com/th3w1zard1/KotOR-Unity/blob/master/Assets/Scripts/FileObjects/AuroraModel.cs) - C# Unity [model](MDL-MDX-File-Format) loader
- [`vendor/NorthernLights/src/Model/`](https://github.com/th3w1zard1/NorthernLights/tree/master/src/Model) - .NET [model](MDL-MDX-File-Format) reader with [animation](MDL-MDX-File-Format#animation-header) [controllers](MDL-MDX-File-Format#controllers)
- [`vendor/kotorblender/io_scene_kotor/format/mdl/`](https://github.com/th3w1zard1/kotorblender/tree/master/io_scene_kotor/format/mdl) - Blender [MDL](MDL-MDX-File-Format) import/export with full [animation](MDL-MDX-File-Format#animation-header) support
- [`vendor/mdlops/mdlops/`](https://github.com/th3w1zard1/mdlops/tree/master/mdlops) - Legacy Python [MDL](MDL-MDX-File-Format) toolkit for conversions
- [`vendor/xoreos-tools/src/aurora/model.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/aurora/model.cpp) - Command-line [model](MDL-MDX-File-Format) extraction tools

**Additional Documentation Sources:**

- [`vendor/xoreos-docs/specs/kotor_mdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/kotor_mdl.html) - Partial KotOR [model](MDL-MDX-File-Format) [format](GFF-File-Format) specification from xoreos-docs
- [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - Tim Smith (Torlack)'s binary [model](MDL-MDX-File-Format) [format](GFF-File-Format) documentation for Aurora engine [models](MDL-MDX-File-Format)

**See Also:**

- [TPC File Format](TPC-File-Format) - [texture](TPC-File-Format) [format](GFF-File-Format) referenced by [MDL](MDL-MDX-File-Format) [materials](MDL-MDX-File-Format#trimesh-header)
- [TXI File Format](TXI-File-Format) - [texture](TPC-File-Format) metadata used with [MDL](MDL-MDX-File-Format) [textures](TPC-File-Format)
- [BWM File Format](BWM-File-Format) - [walkmesh](BWM-File-Format) format ([WOK files](BWM-File-Format)) paired with [room models](LYT-File-Format.md#room-models)
- [GFF File Format](GFF-File-Format) - Templates ([UTC](GFF-File-Format#utc-creature), [UTP](GFF-File-Format#utp-placeable), etc.) that reference [models](MDL-MDX-File-Format)
- [LYT File Format](LYT-File-Format) - [layout files](LYT-File-Format) positioning [models](MDL-MDX-File-Format) in areas

The [MDL file](MDL-MDX-File-Format) begins with a [file](GFF-File-Format) [header](GFF-File-Format#file-header), followed by a [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header), [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header), and various [node](MDL-MDX-File-Format#node-structures) [structures](GFF-File-Format#file-structure-overview). [offsets](GFF-File-Format#file-structure-overview) within the [MDL file](MDL-MDX-File-Format) [ARE](GFF-File-Format#are-area) typically relative to the start of the [file](GFF-File-Format), excluding the first 12 bytes (the [file](GFF-File-Format) [header](GFF-File-Format#file-header)).

Below is an overview of the typical layout:

```plaintext
+-----------------------------+
| MDL File Header             |
+-----------------------------+
| Model Header                |
+-----------------------------+
| Geometry Header             |
+-----------------------------+
| Name Header                 |
+-----------------------------+
| Animations                  |
+-----------------------------+
| Nodes                       |
+-----------------------------+
```

---

## [file](GFF-File-Format) [headers](GFF-File-Format#file-header)

### [MDL](MDL-MDX-File-Format) [file](GFF-File-Format) [header](GFF-File-Format#file-header)

The [MDL file](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) is 12 bytes in [size](GFF-File-Format#file-structure-overview) and contains the following [fields](GFF-File-Format#file-structure-overview):

| Name         | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure-overview) | Description            |
| ------------ | ------- | ------ | ---------------------- |
| Unused       | [uint32](GFF-File-Format#gff-data-types)  | 0 (0x0)     | Always set to `0`.     |
| [MDL](MDL-MDX-File-Format) [size](GFF-File-Format#file-structure-overview)     | [uint32](GFF-File-Format#gff-data-types)  | 4 (0x4)     | [size](GFF-File-Format#file-structure-overview) of the [MDL file](MDL-MDX-File-Format).  |
| [MDX](MDL-MDX-File-Format) [size](GFF-File-Format#file-structure-overview)     | [uint32](GFF-File-Format#gff-data-types)  | 8 (0x8)     | [size](GFF-File-Format#file-structure-overview) of the [MDX file](MDL-MDX-File-Format#mdx-file-header).  |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:162`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L162) - [file](GFF-File-Format) [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:56-59`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L56-L59) - [file](GFF-File-Format) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:100-104`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L100-L104) - [file](GFF-File-Format) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/kotor/docs/mdl.md`](vendor/kotor/docs/mdl.md) - [node](MDL-MDX-File-Format#node-structures) chunk [structure](GFF-File-Format#file-structure-overview) analysis  
**Reference**: [`vendor/KotOR.js/src/loaders/MDLLoader.ts:96-124`](vendor/KotOR.js/src/loaders/MDLLoader.ts) - [MDL](MDL-MDX-File-Format)/[MDX files](MDL-MDX-File-Format) loading and caching implementation

### [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header)

The [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) is 92 bytes in [size](GFF-File-Format#file-structure-overview) and immediately follows the [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header). Together with the [geometry](MDL-MDX-File-Format#geometry-header) Header (80 bytes), the combined [structure](GFF-File-Format#file-structure-overview) is 172 bytes from the start of the [MDL](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) section ([offset](GFF-File-Format#file-structure-overview) 12 in the [file](GFF-File-Format)).

| Name                         | [type](GFF-File-Format#data-types)            | [offset](GFF-File-Format#file-structure-overview) | Description                                                                 |
| ---------------------------- | --------------- | ------ | --------------------------------------------------------------------------- |
| Classification               | [uint8](GFF-File-Format#gff-data-types)           | 0 (0x0)     | [model](MDL-MDX-File-Format) classification type (see [Model Classification Flags](#model-classification-flags)). |
| Subclassification            | [uint8](GFF-File-Format#gff-data-types)           | 1 (0x1)     | [model](MDL-MDX-File-Format) subclassification [value](GFF-File-Format#gff-data-types).                                              |
| Unknown                      | [uint8](GFF-File-Format#gff-data-types)           | 2 (0x2)     | Purpose unknown (possibly smoothing-related).                               |
| Affected By Fog              | [uint8](GFF-File-Format#gff-data-types)           | 3 (0x3)     | `0`: Not affected by fog, `1`: Affected by fog.                             |
| Child [model](MDL-MDX-File-Format) [count](GFF-File-Format#file-structure-overview)            | [uint32](GFF-File-Format#gff-data-types)          | 4 (0x4)     | Number of child [models](MDL-MDX-File-Format).                                                     |
| [animation](MDL-MDX-File-Format#animation-header) [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)       | [uint32](GFF-File-Format#gff-data-types)          | 8 (0x8)     | [offset](GFF-File-Format#file-structure-overview) to the [animation](MDL-MDX-File-Format#animation-header) [array](2DA-File-Format).                                              |
| [animation](MDL-MDX-File-Format#animation-header) [count](GFF-File-Format#file-structure-overview)              | [uint32](GFF-File-Format#gff-data-types)          | 12 (0xC)    | Number of [animations](MDL-MDX-File-Format#animation-header).                                                       |
| [animation](MDL-MDX-File-Format#animation-header) Count (duplicate)  | [uint32](GFF-File-Format#gff-data-types)          | 16 (0x10)    | Duplicate [value](GFF-File-Format#gff-data-types) of [animation](MDL-MDX-File-Format#animation-header) [count](GFF-File-Format#file-structure-overview).                                         |
| Parent [model](MDL-MDX-File-Format) [pointer](GFF-File-Format#file-structure-overview)         | [uint32](GFF-File-Format#gff-data-types)          | 20 (0x14)    | [pointer](GFF-File-Format#file-structure-overview) to parent model (context-dependent).                                |
| [Bounding Box](MDL-MDX-File-Format#model-header) Min             | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)        | 24 (0x18)    | Minimum [coordinates](GFF-File-Format#are-area) of the [bounding box](MDL-MDX-File-Format#model-header) (X, Y, Z).                          |
| [Bounding Box](MDL-MDX-File-Format#model-header) Max             | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)        | 36 (0x24)    | Maximum [coordinates](GFF-File-Format#are-area) of the [bounding box](MDL-MDX-File-Format#model-header) (X, Y, Z).                          |
| Radius                       | [float](GFF-File-Format#gff-data-types)           | 48 (0x30)    | Radius of the [model](MDL-MDX-File-Format)'s bounding sphere.                                      |
| [animation](MDL-MDX-File-Format#animation-header) [scale](MDL-MDX-File-Format#node-header)              | [float](GFF-File-Format#gff-data-types)           | 52 (0x34)    | [scale](MDL-MDX-File-Format#node-header) factor for animations (typically 1.0).                                |
| Supermodel Name              | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)        | 56 (0x38)    | Name of the super[model](MDL-MDX-File-Format) ([null-terminated string](https://en.cppreference.com/w/c/string/byte)).                            |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:164`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L164) - [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:786-805`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L786-L805) - [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) reading and parsing  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:72-88`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L72-L88) - [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:131-150`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L131-L150) - [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:238-240`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L238-L240) - [model](MDL-MDX-File-Format) classification constants definition

**Note:** The [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) immediately follows the [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header). The supermodel name field ([offset](GFF-File-Format#file-structure-overview) 56) is used to reference parent [models](MDL-MDX-File-Format) for inheritance. If the [value](GFF-File-Format#gff-data-types) is "null", it should be treated as empty.

### [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header)

The [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header) is 80 bytes in [size](GFF-File-Format#file-structure-overview) and is located at [offset](GFF-File-Format#file-structure-overview) 12 in the file (immediately after the [file](GFF-File-Format) [header](GFF-File-Format#file-header)). It contains fundamental [model](MDL-MDX-File-Format) information and game engine version identifiers.

| Name                        | [type](GFF-File-Format#data-types)        | [offset](GFF-File-Format#file-structure-overview) | Description                                                                                     |
| --------------------------- | ----------- | ------ | ----------------------------------------------------------------------------------------------- |
| Function [pointer](GFF-File-Format#file-structure-overview) 0          | [uint32](GFF-File-Format#gff-data-types)      | 0 (0x0)     | Game engine version identifier (see [KotOR 1 vs KotOR 2 Models](#kotor-1-vs-kotor-2-models)).  |
| Function [pointer](GFF-File-Format#file-structure-overview) 1          | [uint32](GFF-File-Format#gff-data-types)      | 4 (0x4)     | Function [pointer](GFF-File-Format#file-structure-overview) to parse ASCII [model](MDL-MDX-File-Format) lines (used by the game engine's ASCII [model](MDL-MDX-File-Format) parser).                                             |
| [model](MDL-MDX-File-Format) Name                  | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)    | 8 (0x8)     | Name of the [model](MDL-MDX-File-Format) ([null-terminated string](https://en.cppreference.com/w/c/string/byte)).                                                     |
| Root [node](MDL-MDX-File-Format#node-structures) [offset](GFF-File-Format#file-structure-overview)            | [uint32](GFF-File-Format#gff-data-types)      | 40 (0x28)    | [offset](GFF-File-Format#file-structure-overview) to the root [node](MDL-MDX-File-Format#node-structures) structure (relative to [MDL](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [offset](GFF-File-Format#file-structure-overview) 12).                             |
| [node](MDL-MDX-File-Format#node-structures) [count](GFF-File-Format#file-structure-overview)                  | [uint32](GFF-File-Format#gff-data-types)      | 44 (0x2C)    | Total number of [nodes](MDL-MDX-File-Format#node-structures) in the [model](MDL-MDX-File-Format) hierarchy.                                                   |
| Unknown [array](2DA-File-Format) Definition 1  | [[uint32](GFF-File-Format#gff-data-types)][GFF-File-Format#dword](3)   | 48 (0x30)    | [array](2DA-File-Format) definition structure ([offset](GFF-File-Format#file-structure-overview), [count](GFF-File-Format#file-structure-overview), [count](GFF-File-Format#file-structure-overview) duplicate). Purpose unknown.                   |
| Unknown [array](2DA-File-Format) Definition 2  | [[uint32](GFF-File-Format#gff-data-types)][GFF-File-Format#dword](3)   | 60 (0x3C)    | [array](2DA-File-Format) definition structure ([offset](GFF-File-Format#file-structure-overview), [count](GFF-File-Format#file-structure-overview), [count](GFF-File-Format#file-structure-overview) duplicate). Purpose unknown.                   |
| Reference [count](GFF-File-Format#file-structure-overview)             | [uint32](GFF-File-Format#gff-data-types)      | 72 (0x48)    | Reference [count](GFF-File-Format#file-structure-overview) initialized to 0. When another [model](MDL-MDX-File-Format) references this [model](MDL-MDX-File-Format), this [value](GFF-File-Format#gff-data-types) is incremented. When the referencing [model](MDL-MDX-File-Format) dereferences this [model](MDL-MDX-File-Format), the [count](GFF-File-Format#file-structure-overview) is decremented. When this [count](GFF-File-Format#file-structure-overview) goes to zero, the [model](MDL-MDX-File-Format) can be deleted since it is no longer needed.                                                 |
| [geometry](MDL-MDX-File-Format#geometry-header) [type](GFF-File-Format#data-types)               | [uint8](GFF-File-Format#gff-data-types)       | 76 (0x4C)    | [type](GFF-File-Format#data-types) of [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header): `0x01`: Basic [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header) (not in [models](MDL-MDX-File-Format)), `0x02`: [model](MDL-MDX-File-Format) [geometry](MDL-MDX-File-Format#geometry-header), `0x05`: [animation](MDL-MDX-File-Format#animation-header) [geometry](MDL-MDX-File-Format#geometry-header). If [bit](GFF-File-Format#gff-data-types) 7 (0x80) is set, the [model](MDL-MDX-File-Format) is a compiled binary [model](MDL-MDX-File-Format) loaded from disk and converted to absolute addresses.                    |
| Padding                     | [[uint8](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](3)    | 77 (0x4D)    | Padding bytes for alignment.                                                                    |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:163`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L163) - [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:770-784`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L770-L784) - [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:437-461`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L437-L461) - Version detection using function [pointer](GFF-File-Format#file-structure-overview)  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:61-70`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L61-L70) - [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:106-129`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L106-L129) - [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header) reading

### Names [header](GFF-File-Format#file-header)

The Names [header](GFF-File-Format#file-header) is located at [file](GFF-File-Format) [offset](GFF-File-Format#file-structure-overview) 180 (28 bytes). It contains metadata for [node](MDL-MDX-File-Format#node-structures) name lookup and [MDX file](MDL-MDX-File-Format) information. This section bridges the [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) [data](GFF-File-Format#file-structure-overview) and the [animation](MDL-MDX-File-Format#animation-header)/[node](MDL-MDX-File-Format#node-structures) [structures](GFF-File-Format#file-structure-overview).

| Name                | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure-overview) | Description                                                                 |
| ------------------- | ------- | ------ | --------------------------------------------------------------------------- |
| Root [node](MDL-MDX-File-Format#node-structures) [offset](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)  | 0 (0x0)     | [offset](GFF-File-Format#file-structure-overview) to the root [node](MDL-MDX-File-Format#node-structures) (often a duplicate of the [geometry header](MDL-MDX-File-Format#geometry-header) [value](GFF-File-Format#gff-data-types)).   |
| Unknown/Padding     | [uint32](GFF-File-Format#gff-data-types)  | 4 (0x4)     | Unknown [field](GFF-File-Format#file-structure-overview), typically unused or padding.                                 |
| [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [size](GFF-File-Format#file-structure-overview)       | [uint32](GFF-File-Format#gff-data-types)  | 8 (0x8)     | [size](GFF-File-Format#file-structure-overview) of the [MDX file](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) in bytes.                                         |
| [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [offset](GFF-File-Format#file-structure-overview)     | [uint32](GFF-File-Format#gff-data-types)  | 12 (0xC)    | [offset](GFF-File-Format#file-structure-overview) to [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) within the [MDX file](MDL-MDX-File-Format) (typically 0).                       |
| Names [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)  | [uint32](GFF-File-Format#gff-data-types)  | 16 (0x10)    | [offset](GFF-File-Format#file-structure-overview) to the [array](2DA-File-Format) of name [string](GFF-File-Format#gff-data-types) [offsets](GFF-File-Format#file-structure-overview).                                 |
| Names [count](GFF-File-Format#file-structure-overview)         | [uint32](GFF-File-Format#gff-data-types)  | 20 (0x14)    | Number of [node](MDL-MDX-File-Format#node-structures) names in the [array](2DA-File-Format).                                          |
| Names Count (dup)   | [uint32](GFF-File-Format#gff-data-types)  | 24 (0x18)    | Duplicate [value](GFF-File-Format#gff-data-types) of names [count](GFF-File-Format#file-structure-overview).                                             |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:165`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L165) - Names [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:810-843`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L810-L843) - Names [header](GFF-File-Format#file-header) and name [array](2DA-File-Format) reading  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:88,98-99`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L88-L99) - Names [header](GFF-File-Format#file-header) reading and [node](MDL-MDX-File-Format#node-structures) name parsing  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:128-133`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L128-L133) - [node](MDL-MDX-File-Format#node-structures) name [array](2DA-File-Format) reading with lowercase conversion

**Note:** [Node](MDL-MDX-File-Format#node-structures) names [ARE](GFF-File-Format#are-area) stored as [null-terminated](https://en.cppreference.com/w/c/string/byte) strings (max 32 bytes) and [ARE](GFF-File-Format#are-area) typically converted to lowercase during parsing. The names [array](2DA-File-Format) contains [offsets](GFF-File-Format#file-structure-overview) to [string](GFF-File-Format#gff-data-types) [data](GFF-File-Format#file-structure-overview), not the [strings](GFF-File-Format#gff-data-types) themselves.

### [animation](MDL-MDX-File-Format#animation-header) [header](GFF-File-Format#file-header)

Each [animation](MDL-MDX-File-Format#animation-header) begins with a [Geometry Header](MDL-MDX-File-Format#geometry-header) (80 bytes) followed by an [Animation Header](MDL-MDX-File-Format#animation-header) (56 bytes), for a combined [size](GFF-File-Format#file-structure-overview) of 136 bytes.

| Name                  | [type](GFF-File-Format#data-types)            | [offset](GFF-File-Format#file-structure-overview) | Description                                                |
| --------------------- | --------------- | ------ | ---------------------------------------------------------- |
| [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header)       | GeometryHeader  | 0 (0x0)     | Standard 80-[byte](GFF-File-Format#gff-data-types) [Geometry Header](MDL-MDX-File-Format#geometry-header) ([geometry](MDL-MDX-File-Format#geometry-header) type = `0x01`).|
| [animation](MDL-MDX-File-Format#animation-header) Length      | [float](GFF-File-Format#gff-data-types)           | 80 (0x50)    | Duration of the [animation](MDL-MDX-File-Format#animation-header) in seconds.                      |
| Transition Time       | [float](GFF-File-Format#gff-data-types)           | 84 (0x54)    | Transition/blend time to this [animation](MDL-MDX-File-Format#animation-header) in seconds.        |
| [animation](MDL-MDX-File-Format#animation-header) Root        | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)        | 88 (0x58)    | Root [node](MDL-MDX-File-Format#node-structures) name for the [animation](MDL-MDX-File-Format#animation-header) ([null-terminated](https://en.cppreference.com/w/c/string/byte) [string](GFF-File-Format#gff-data-types)). |
| Event [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)          | 120 (0x78)   | [offset](GFF-File-Format#file-structure-overview) to [animation](MDL-MDX-File-Format#animation-header) events [array](2DA-File-Format).                          |
| Event [count](GFF-File-Format#file-structure-overview)           | [uint32](GFF-File-Format#gff-data-types)          | 124 (0x7C)   | Number of [animation](MDL-MDX-File-Format#animation-header) events.                                |
| Event Count (dup)     | [uint32](GFF-File-Format#gff-data-types)          | 128 (0x80)   | Duplicate [value](GFF-File-Format#gff-data-types) of event [count](GFF-File-Format#file-structure-overview).                            |
| Unknown               | [uint32](GFF-File-Format#gff-data-types)          | 132 (0x84)   | Purpose unknown.                                           |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:169`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L169) - [animation](MDL-MDX-File-Format#animation-header) [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:1339-1363`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1339-L1363) - [animation](MDL-MDX-File-Format#animation-header) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:106-107`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L106-L107) - [animation](MDL-MDX-File-Format#animation-header) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:650-691`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L650-L691) - [animation](MDL-MDX-File-Format#animation-header) loading and event processing

### Event [structure](GFF-File-Format#file-structure-overview)

Each [animation](MDL-MDX-File-Format#animation-header) event is 36 bytes in [size](GFF-File-Format#file-structure-overview) and triggers game actions at specific [animation](MDL-MDX-File-Format#animation-header) timestamps.

| Name            | [type](GFF-File-Format#data-types)      | [offset](GFF-File-Format#file-structure-overview) | Description                                                          |
| --------------- | --------- | ------ | -------------------------------------------------------------------- |
| Activation Time | [float](GFF-File-Format#gff-data-types)     | 0 (0x0)     | Time in seconds when the event triggers during [animation](MDL-MDX-File-Format#animation-header) playback.   |
| Event Name      | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)  | 4 (0x4)     | Name of the event ([null-terminated string](https://en.cppreference.com/w/c/string/byte), e.g., "detonate").        |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:170`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L170) - Event [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:1365`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1365) - [animation](MDL-MDX-File-Format#animation-header) events reading  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp) - [animation](MDL-MDX-File-Format#animation-header) event processing in reone implementation

---

## [node](MDL-MDX-File-Format#node-structures) [structures](GFF-File-Format#file-structure-overview)

### [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header)

The [Node Header](MDL-MDX-File-Format#node-header) is 80 bytes in [size](GFF-File-Format#file-structure-overview) and is present in all [node](MDL-MDX-File-Format#node-structures) [types](GFF-File-Format#gff-data-types). It defines the [node](MDL-MDX-File-Format#node-structures)'s [position](MDL-MDX-File-Format#node-header) in the hierarchy, its transform, and references to child [nodes](MDL-MDX-File-Format#node-structures) and [animation](MDL-MDX-File-Format#animation-header) [controllers](MDL-MDX-File-Format#controllers).

| Name                     | [type](GFF-File-Format#data-types)        | [offset](GFF-File-Format#file-structure-overview) | Description                                                                        |
| ------------------------ | ----------- | ------ | ---------------------------------------------------------------------------------- |
| [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) [flags](GFF-File-Format#gff-data-types)          | [uint16](GFF-File-Format#gff-data-types)      | 0 (0x0)     | [bitmask](GFF-File-Format#gff-data-types) indicating [node](MDL-MDX-File-Format#node-structures) features (see [Node Type Bitmasks](#node-type-bitmasks)). |
| [node](MDL-MDX-File-Format#node-structures) [index](2DA-File-Format#row-labels)               | [uint16](GFF-File-Format#gff-data-types)      | 2 (0x2)     | Sequential [index](2DA-File-Format#row-labels) of this [node](MDL-MDX-File-Format#node-structures) in the [model](MDL-MDX-File-Format).                                        |
| [node](MDL-MDX-File-Format#node-structures) Name [index](2DA-File-Format#row-labels)          | [uint16](GFF-File-Format#gff-data-types)      | 4 (0x4)     | [index](2DA-File-Format#row-labels) into the names [array](2DA-File-Format) for this [node](MDL-MDX-File-Format#node-structures)'s name.                                   |
| Padding                  | [uint16](GFF-File-Format#gff-data-types)      | 6 (0x6)     | Padding for alignment.                                                             |
| Root [node](MDL-MDX-File-Format#node-structures) [offset](GFF-File-Format#file-structure-overview)         | [uint32](GFF-File-Format#gff-data-types)      | 8 (0x8)     | [offset](GFF-File-Format#file-structure-overview) to the [model](MDL-MDX-File-Format)'s root [node](MDL-MDX-File-Format#node-structures).                                                   |
| Parent [node](MDL-MDX-File-Format#node-structures) [offset](GFF-File-Format#file-structure-overview)       | [uint32](GFF-File-Format#gff-data-types)      | 12 (0xC)    | [offset](GFF-File-Format#file-structure-overview) to this [node](MDL-MDX-File-Format#node-structures)'s parent node (0 if root).                                     |
| [position](MDL-MDX-File-Format#node-header)                 | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)    | 16 (0x10)    | [node](MDL-MDX-File-Format#node-structures) [position](MDL-MDX-File-Format#node-header) in local space (X, Y, Z).                                            |
| [orientation](MDL-MDX-File-Format#node-header)              | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](4)    | 28 (0x1C)    | [node](MDL-MDX-File-Format#node-structures) [orientation](MDL-MDX-File-Format#node-header) as quaternion (W, X, Y, Z).                                       |
| Child [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)       | [uint32](GFF-File-Format#gff-data-types)      | 44 (0x2C)    | [offset](GFF-File-Format#file-structure-overview) to [array](2DA-File-Format) of child [node](MDL-MDX-File-Format#node-structures) [offsets](GFF-File-Format#file-structure-overview).                                             |
| Child [count](GFF-File-Format#file-structure-overview)              | [uint32](GFF-File-Format#gff-data-types)      | 48 (0x30)    | Number of child [nodes](MDL-MDX-File-Format#node-structures).                                                             |
| Child Count (dup)        | [uint32](GFF-File-Format#gff-data-types)      | 52 (0x34)    | Duplicate [value](GFF-File-Format#gff-data-types) of child [count](GFF-File-Format#file-structure-overview).                                                    |
| [controller](MDL-MDX-File-Format#controllers) [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)  | [uint32](GFF-File-Format#gff-data-types)      | 56 (0x38)    | [offset](GFF-File-Format#file-structure-overview) to [array](2DA-File-Format) of [controller](MDL-MDX-File-Format#controllers) [structures](GFF-File-Format#file-structure-overview).                                          |
| [controller](MDL-MDX-File-Format#controllers) [count](GFF-File-Format#file-structure-overview)         | [uint32](GFF-File-Format#gff-data-types)      | 60 (0x3C)    | Number of [controllers](MDL-MDX-File-Format#controllers) attached to this [node](MDL-MDX-File-Format#node-structures).                                       |
| [controller](MDL-MDX-File-Format#controllers) Count (dup)   | [uint32](GFF-File-Format#gff-data-types)      | 64 (0x40)    | Duplicate [value](GFF-File-Format#gff-data-types) of [controller](MDL-MDX-File-Format#controllers) [count](GFF-File-Format#file-structure-overview).                                               |
| [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [offset](GFF-File-Format#file-structure-overview)   | [uint32](GFF-File-Format#gff-data-types)      | 68 (0x44)    | [offset](GFF-File-Format#file-structure-overview) to [controller](MDL-MDX-File-Format#controllers) [keyframe](MDL-MDX-File-Format#controller-structure)/[data](GFF-File-Format#file-structure-overview) [array](2DA-File-Format).                                          |
| [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [count](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)      | 72 (0x48)    | Number of floats in [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [array](2DA-File-Format).                                         |
| [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [count](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)      | 76 (0x4C)    | Duplicate [value](GFF-File-Format#gff-data-types) of [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [count](GFF-File-Format#file-structure-overview).                                          |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:172`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L172) - [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:1590-1622`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1590-L1622) - [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:135-150`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L135-L150) - [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:189-250`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L189-L250) - [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header) reading and [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) processing  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:153-155`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L153-L155) - Unsupported [node](MDL-MDX-File-Format#node-structures) [flags](GFF-File-Format#gff-data-types) validation  
**Reference**: [`vendor/kotor/docs/mdl.md:9-27`](vendor/kotor/docs/mdl.md#node-chunk) - [node](MDL-MDX-File-Format#node-structures) chunk [structure](GFF-File-Format#file-structure-overview) analysis with [byte](GFF-File-Format#gff-data-types)-level layout

**Note:** The [orientation](MDL-MDX-File-Format#node-header) [quaternion](MDL-MDX-File-Format#node-header) is stored in W, X, Y, Z order. The [node](MDL-MDX-File-Format#node-structures) index ([offset](GFF-File-Format#file-structure-overview) 2) is a sequential identifier used for [node](MDL-MDX-File-Format#node-structures) lookup. [controllers](MDL-MDX-File-Format#controllers) [ARE](GFF-File-Format#are-area) stored separately from the [node](MDL-MDX-File-Format#node-structures) [structure](GFF-File-Format#file-structure-overview) and referenced via [offsets](GFF-File-Format#file-structure-overview).

### Trimesh [header](GFF-File-Format#file-header)

The Trimesh [header](GFF-File-Format#file-header) defines static [mesh](MDL-MDX-File-Format#trimesh-header) [geometry](MDL-MDX-File-Format#geometry-header) and is 332 bytes in KotOR 1 and 340 bytes in KotOR 2 [models](MDL-MDX-File-Format). This [header](GFF-File-Format#file-header) immediately follows the 80-[byte](GFF-File-Format#gff-data-types) [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header).

| Name                         | [type](GFF-File-Format#data-types)         | [offset](GFF-File-Format#file-structure-overview)     | Description                                                                                 |
| ---------------------------- | ------------ | ---------- | ------------------------------------------------------------------------------------------- |
| Function [pointer](GFF-File-Format#file-structure-overview) 0           | [uint32](GFF-File-Format#gff-data-types)       | 0 (0x0)         | Game engine function pointer (version-specific).                                            |
| Function [pointer](GFF-File-Format#file-structure-overview) 1           | [uint32](GFF-File-Format#gff-data-types)       | 4 (0x4)         | Secondary game engine function [pointer](GFF-File-Format#file-structure-overview).                                                     |
| [faces](MDL-MDX-File-Format#face-structure) [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)           | [uint32](GFF-File-Format#gff-data-types)       | 8 (0x8)         | [offset](GFF-File-Format#file-structure-overview) to [face](MDL-MDX-File-Format#face-structure) definitions [array](2DA-File-Format).                                                           |
| [faces](MDL-MDX-File-Format#face-structure) [count](GFF-File-Format#file-structure-overview)                  | [uint32](GFF-File-Format#gff-data-types)       | 12 (0xC)        | Number of triangular [faces](MDL-MDX-File-Format#face-structure) in the [mesh](MDL-MDX-File-Format#trimesh-header).                                                     |
| [faces](MDL-MDX-File-Format#face-structure) Count (dup)            | [uint32](GFF-File-Format#gff-data-types)       | 16 (0x10)        | Duplicate of [faces](MDL-MDX-File-Format#face-structure) [count](GFF-File-Format#file-structure-overview).                                                                   |
| [bounding box](MDL-MDX-File-Format#model-header) Min             | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)     | 20 (0x14)        | Minimum [bounding box](MDL-MDX-File-Format#model-header) coordinates (X, Y, Z).                                                 |
| [bounding box](MDL-MDX-File-Format#model-header) Max             | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)     | 32 (0x20)        | Maximum [bounding box](MDL-MDX-File-Format#model-header) coordinates (X, Y, Z).                                                 |
| Radius                       | [float](GFF-File-Format#gff-data-types)        | 44 (0x2C)        | Bounding sphere radius.                                                                     |
| Average Point                | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)     | 48 (0x30)        | Average [vertex](MDL-MDX-File-Format#vertex-structure) position (centroid).                                                         |
| Diffuse [color](GFF-File-Format#color)                | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)     | 60 (0x3C)        | [material](MDL-MDX-File-Format#trimesh-header) diffuse color (R, G, B, range 0.0-1.0).                                            |
| Ambient [color](GFF-File-Format#color)                | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)     | 72 (0x48)        | [material](MDL-MDX-File-Format#trimesh-header) ambient color (R, G, B, range 0.0-1.0).                                            |
| Transparency Hint            | [uint32](GFF-File-Format#gff-data-types)       | 84 (0x54)        | Transparency rendering mode.                                                                |
| [texture](TPC-File-Format) 0 Name               | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)     | 88 (0x58)        | Primary diffuse [texture](TPC-File-Format) name ([null-terminated](https://en.cppreference.com/w/c/string/byte)).                                             |
| [texture](TPC-File-Format) 1 Name               | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)     | 120 (0x78)       | Secondary [texture](TPC-File-Format) name, often lightmap ([null-terminated](https://en.cppreference.com/w/c/string/byte)).                                   |
| [texture](TPC-File-Format) 2 Name               | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](12)     | 152 (0x98)       | Tertiary [texture](TPC-File-Format) name ([null-terminated](https://en.cppreference.com/w/c/string/byte)).                                                    |
| [texture](TPC-File-Format) 3 Name               | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](12)     | 164 (0xA4)       | Quaternary [texture](TPC-File-Format) name ([null-terminated](https://en.cppreference.com/w/c/string/byte)).                                                  |
| [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)   | [uint32](GFF-File-Format#gff-data-types)       | 176 (0xB0)       | [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure-overview) [array](2DA-File-Format).                                                       |
| [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)       | 180 (0xB4)       | Number of entries in [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure-overview) [array](2DA-File-Format).                                                   |
| [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)       | 184 (0xB8)       | Duplicate of [indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview).                                                     |
| [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)  | [uint32](GFF-File-Format#gff-data-types)       | 188 (0xBC)       | [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) [array](2DA-File-Format).                                                      |
| [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview)   | [uint32](GFF-File-Format#gff-data-types)       | 192 (0xC0)       | Number of entries in [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) [array](2DA-File-Format).                                                  |
| [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview)   | [uint32](GFF-File-Format#gff-data-types)       | 196 (0xC4)       | Duplicate of [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview).                                                    |
| Inverted Counter [array](2DA-File-Format) [offset](GFF-File-Format#file-structure-overview)| [uint32](GFF-File-Format#gff-data-types)       | 200 (0xC8)       | [offset](GFF-File-Format#file-structure-overview) to inverted counter [array](2DA-File-Format).                                                           |
| Inverted Counter [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview) | [uint32](GFF-File-Format#gff-data-types)       | 204 (0xCC)       | Number of entries in inverted counter [array](2DA-File-Format).                                                |
| Inverted Counter [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview) | [uint32](GFF-File-Format#gff-data-types)       | 208 (0xD0)       | Duplicate of inverted counter [array](2DA-File-Format) [count](GFF-File-Format#file-structure-overview).                                                  |
| Unknown [values](GFF-File-Format#gff-data-types)               | [[int32](GFF-File-Format#gff-data-types)][GFF-File-Format#int](3)     | 212 (0xD4)       | Typically `{-1, -1, 0}`. Purpose unknown.                                                   |
| Saber Unknown [data](GFF-File-Format#file-structure-overview)           | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](8)      | 224 (0xE0)       | [data](GFF-File-Format#file-structure-overview) specific to lightsaber [meshes](MDL-MDX-File-Format#trimesh-header).                                                         |
| Unknown                      | [uint32](GFF-File-Format#gff-data-types)       | 232 (0xE8)       | Purpose unknown.                                                                            |
| UV Direction X               | [float](GFF-File-Format#gff-data-types)        | 236 (0xEC)       | UV [animation](MDL-MDX-File-Format#animation-header) direction X component.                                                         |
| UV Direction Y               | [float](GFF-File-Format#gff-data-types)        | 240 (0xF0)       | UV [animation](MDL-MDX-File-Format#animation-header) direction Y component.                                                         |
| UV Jitter                    | [float](GFF-File-Format#gff-data-types)        | 244 (0xF4)       | UV [animation](MDL-MDX-File-Format#animation-header) jitter amount.                                                                 |
| UV Jitter Speed              | [float](GFF-File-Format#gff-data-types)        | 248 (0xF8)       | UV [animation](MDL-MDX-File-Format#animation-header) jitter speed.                                                                  |
| [MDX](MDL-MDX-File-Format) [vertex](MDL-MDX-File-Format#vertex-structure) [size](GFF-File-Format#file-structure-overview)              | [uint32](GFF-File-Format#gff-data-types)       | 252 (0xFC)       | [size](GFF-File-Format#file-structure-overview) in bytes of each [vertex](MDL-MDX-File-Format#vertex-structure) in [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview).                                                   |
| [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [flags](GFF-File-Format#gff-data-types)               | [uint32](GFF-File-Format#gff-data-types)       | 256 (0x100)       | [bitmask](GFF-File-Format#gff-data-types) of present [vertex](MDL-MDX-File-Format#vertex-structure) attributes (see [MDX Data Bitmap Masks](#mdx-data-bitmap-masks)).|
| [MDX](MDL-MDX-File-Format) [vertices](MDL-MDX-File-Format#vertex-structure) [offset](GFF-File-Format#file-structure-overview)          | [int32](GFF-File-Format#gff-data-types)        | 260 (0x104)       | Relative [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) [positions](MDL-MDX-File-Format#node-header) in MDX (or -1 if none).                                 |
| [MDX](MDL-MDX-File-Format) Normals [offset](GFF-File-Format#file-structure-overview)           | [int32](GFF-File-Format#gff-data-types)        | 264 (0x108)       | Relative [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) normals in MDX (or -1 if none).                                   |
| [MDX](MDL-MDX-File-Format) [vertex](MDL-MDX-File-Format#vertex-structure) [colors](GFF-File-Format#color) [offset](GFF-File-Format#file-structure-overview)     | [int32](GFF-File-Format#gff-data-types)        | 268 (0x10C)       | Relative [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) [colors](GFF-File-Format#color) in MDX (or -1 if none).                                    |
| [MDX](MDL-MDX-File-Format) Tex 0 UVs [offset](GFF-File-Format#file-structure-overview)         | [int32](GFF-File-Format#gff-data-types)        | 272 (0x110)       | Relative [offset](GFF-File-Format#file-structure-overview) to primary [texture](TPC-File-Format) UVs in MDX (or -1 if none).                              |
| [MDX](MDL-MDX-File-Format) Tex 1 UVs [offset](GFF-File-Format#file-structure-overview)         | [int32](GFF-File-Format#gff-data-types)        | 276 (0x114)       | Relative [offset](GFF-File-Format#file-structure-overview) to secondary [texture](TPC-File-Format) UVs in MDX (or -1 if none).                            |
| [MDX](MDL-MDX-File-Format) Tex 2 UVs [offset](GFF-File-Format#file-structure-overview)         | [int32](GFF-File-Format#gff-data-types)        | 280 (0x118)       | Relative [offset](GFF-File-Format#file-structure-overview) to tertiary [texture](TPC-File-Format) UVs in MDX (or -1 if none).                             |
| [MDX](MDL-MDX-File-Format) Tex 3 UVs [offset](GFF-File-Format#file-structure-overview)         | [int32](GFF-File-Format#gff-data-types)        | 284 (0x11C)       | Relative [offset](GFF-File-Format#file-structure-overview) to quaternary [texture](TPC-File-Format) UVs in MDX (or -1 if none).                           |
| [MDX](MDL-MDX-File-Format) Tangent Space [offset](GFF-File-Format#file-structure-overview)     | [int32](GFF-File-Format#gff-data-types)        | 288 (0x120)       | Relative [offset](GFF-File-Format#file-structure-overview) to tangent space [data](GFF-File-Format#file-structure-overview) in MDX (or -1 if none).                               |
| [MDX](MDL-MDX-File-Format) Unknown [offset](GFF-File-Format#file-structure-overview) 1         | [int32](GFF-File-Format#gff-data-types)        | 292 (0x124)       | Relative [offset](GFF-File-Format#file-structure-overview) to unknown [MDX](MDL-MDX-File-Format) data (or -1 if none).                                        |
| [MDX](MDL-MDX-File-Format) Unknown [offset](GFF-File-Format#file-structure-overview) 2         | [int32](GFF-File-Format#gff-data-types)        | 296 (0x128)       | Relative [offset](GFF-File-Format#file-structure-overview) to unknown [MDX](MDL-MDX-File-Format) data (or -1 if none).                                        |
| [MDX](MDL-MDX-File-Format) Unknown [offset](GFF-File-Format#file-structure-overview) 3         | [int32](GFF-File-Format#gff-data-types)        | 300 (0x12C)       | Relative [offset](GFF-File-Format#file-structure-overview) to unknown [MDX](MDL-MDX-File-Format) data (or -1 if none).                                        |
| [vertex](MDL-MDX-File-Format#vertex-structure) [count](GFF-File-Format#file-structure-overview)                 | [uint16](GFF-File-Format#gff-data-types)       | 304 (0x130)       | Number of [vertices](MDL-MDX-File-Format#vertex-structure) in the [mesh](MDL-MDX-File-Format#trimesh-header).                                                             |
| [texture](TPC-File-Format) [count](GFF-File-Format#file-structure-overview)                | [uint16](GFF-File-Format#gff-data-types)       | 306 (0x132)       | Number of [textures](TPC-File-Format) used by the [mesh](MDL-MDX-File-Format#trimesh-header).                                                        |
| Lightmapped                  | [uint8](GFF-File-Format#gff-data-types)        | 308 (0x134)       | `1` if [mesh](MDL-MDX-File-Format#trimesh-header) uses lightmap, `0` otherwise.                                                   |
| Rotate [texture](TPC-File-Format)               | [uint8](GFF-File-Format#gff-data-types)        | 309 (0x135)       | `1` if [texture](TPC-File-Format) should rotate, `0` otherwise.                                                |
| Background [geometry](MDL-MDX-File-Format#geometry-header)          | [uint8](GFF-File-Format#gff-data-types)        | 310 (0x136)       | `1` if background [geometry](MDL-MDX-File-Format#geometry-header), `0` otherwise.                                                  |
| Shadow                       | [uint8](GFF-File-Format#gff-data-types)        | 311 (0x137)       | `1` if [mesh](MDL-MDX-File-Format#trimesh-header) casts shadows, `0` otherwise.                                                   |
| Beaming                      | [uint8](GFF-File-Format#gff-data-types)        | 312 (0x138)       | `1` if beaming effect enabled, `0` otherwise.                                               |
| Render                       | [uint8](GFF-File-Format#gff-data-types)        | 313 (0x139)       | `1` if [mesh](MDL-MDX-File-Format#trimesh-header) is renderable, `0` if hidden.                                                   |
| Unknown [flag](GFF-File-Format#gff-data-types)                 | [uint8](GFF-File-Format#gff-data-types)        | 314 (0x13A)       | Purpose unknown (possibly UV [animation](MDL-MDX-File-Format#animation-header) enable).                                             |
| Padding                      | [uint8](GFF-File-Format#gff-data-types)        | 315 (0x13B)       | Padding [byte](GFF-File-Format#gff-data-types).                                                                               |
| Total Area                   | [float](GFF-File-Format#gff-data-types)        | 316 (0x13C)       | Total surface area of all [faces](MDL-MDX-File-Format#face-structure).                                                            |
| Unknown                      | [uint32](GFF-File-Format#gff-data-types)       | 320 (0x140)       | Purpose unknown.                                                                            |
| **K2 Unknown 1**             | **[uint32](GFF-File-Format#gff-data-types)**   | **324**    | **KotOR 2 only:** Additional unknown [field](GFF-File-Format#file-structure-overview).                                                 |
| **K2 Unknown 2**             | **[uint32](GFF-File-Format#gff-data-types)**   | **328**    | **KotOR 2 only:** Additional unknown [field](GFF-File-Format#file-structure-overview).                                                 |
| [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [offset](GFF-File-Format#file-structure-overview)              | [uint32](GFF-File-Format#gff-data-types)       | 324/332    | Absolute [offset](GFF-File-Format#file-structure-overview) to this [mesh](MDL-MDX-File-Format#trimesh-header)'s [vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) in the [MDX files](MDL-MDX-File-Format).                                 |
| [MDL](MDL-MDX-File-Format) [vertices](MDL-MDX-File-Format#vertex-structure) [offset](GFF-File-Format#file-structure-overview)          | [uint32](GFF-File-Format#gff-data-types)       | 328/336    | [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) [coordinate](GFF-File-Format#are-area) [array](2DA-File-Format) in [MDL](MDL-MDX-File-Format) file (for [walkmesh](BWM-File-Format)/[AABB](BWM-File-Format#aabb-tree) [nodes](MDL-MDX-File-Format#node-structures)).                    |

### Danglymesh [header](GFF-File-Format#file-header)

The Danglymesh [header](GFF-File-Format#file-header) extends the Trimesh [header](GFF-File-Format#file-header) with 28 additional bytes for physics simulation parameters. Total [size](GFF-File-Format#file-structure-overview) is 360 bytes (K1) or 368 bytes (K2). The danglymesh extension immediately follows the trimesh [data](GFF-File-Format#file-structure-overview).

| Name                   | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure-overview)     | Description                                                                      |
| ---------------------- | ------- | ---------- | -------------------------------------------------------------------------------- |
| *Trimesh [header](GFF-File-Format#file-header)*       | *...*   | *0-331*    | *Standard Trimesh Header (332 bytes K1, 340 bytes K2).*                          |
| Constraints [offset](GFF-File-Format#file-structure-overview)     | [uint32](GFF-File-Format#gff-data-types)  | 332/340    | [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) constraint [values](GFF-File-Format#gff-data-types) [array](2DA-File-Format).                                        |
| Constraints [count](GFF-File-Format#file-structure-overview)      | [uint32](GFF-File-Format#gff-data-types)  | 336/344    | Number of [vertex](MDL-MDX-File-Format#vertex-structure) constraints (matches [vertex](MDL-MDX-File-Format#vertex-structure) [count](GFF-File-Format#file-structure-overview)).                             |
| Constraints Count (dup)| [uint32](GFF-File-Format#gff-data-types)  | 340/348    | Duplicate of constraints [count](GFF-File-Format#file-structure-overview).                                                  |
| Displacement           | [float](GFF-File-Format#gff-data-types)   | 344/352    | Maximum displacement distance for physics simulation.                            |
| Tightness              | [float](GFF-File-Format#gff-data-types)   | 348/356    | Tightness/stiffness of the spring simulation (0.0-1.0).                          |
| Period                 | [float](GFF-File-Format#gff-data-types)   | 352/360    | Oscillation period in seconds.                                                   |
| Unknown                | [uint32](GFF-File-Format#gff-data-types)  | 356/364    | Purpose unknown.                                                                 |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:289`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L289) - Danglymesh [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:297-320`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L297-L320) - Danglymesh constraint and [vertex](MDL-MDX-File-Format#vertex-structure) [position](MDL-MDX-File-Format#node-header) reading

### Skinmesh [header](GFF-File-Format#file-header)

The Skinmesh [header](GFF-File-Format#file-header) extends the Trimesh [header](GFF-File-Format#file-header) with 100 additional bytes for skeletal [animation](MDL-MDX-File-Format#animation-header) [data](GFF-File-Format#file-structure-overview). Total [size](GFF-File-Format#file-structure-overview) is 432 bytes (K1) or 440 bytes (K2). The skinmesh extension immediately follows the trimesh [data](GFF-File-Format#file-structure-overview).

| Name                                  | [type](GFF-File-Format#data-types)       | [offset](GFF-File-Format#file-structure-overview)     | Description                                                                      |
| ------------------------------------- | ---------- | ---------- | -------------------------------------------------------------------------------- |
| *Trimesh [header](GFF-File-Format#file-header)*                      | *...*      | *0-331*    | *Standard Trimesh Header (332 bytes K1, 340 bytes K2).*                          |
| Unknown Weights                       | [[int32](GFF-File-Format#gff-data-types)][GFF-File-Format#int](3)   | 332/340    | Purpose unknown (possibly compilation weights).                                  |
| [MDX](MDL-MDX-File-Format) Bone Weights [offset](GFF-File-Format#file-structure-overview)               | [uint32](GFF-File-Format#gff-data-types)     | 344/352    | [offset](GFF-File-Format#file-structure-overview) to bone weight [data](GFF-File-Format#file-structure-overview) in [MDX](MDL-MDX-File-Format) file (4 floats per [vertex](MDL-MDX-File-Format#vertex-structure)).                    |
| [MDX](MDL-MDX-File-Format) Bone [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview)               | [uint32](GFF-File-Format#gff-data-types)     | 348/356    | [offset](GFF-File-Format#file-structure-overview) to bone [index](2DA-File-Format#row-labels) [data](GFF-File-Format#file-structure-overview) in [MDX](MDL-MDX-File-Format) file (4 floats per [vertex](MDL-MDX-File-Format#vertex-structure), cast to [uint16](GFF-File-Format#gff-data-types)).    |
| Bone Map [offset](GFF-File-Format#file-structure-overview)                       | [uint32](GFF-File-Format#gff-data-types)     | 352/360    | [offset](GFF-File-Format#file-structure-overview) to bone map array (maps local bone [indices](2DA-File-Format#row-labels) to skeleton bone numbers).    |
| Bone Map [count](GFF-File-Format#file-structure-overview)                        | [uint32](GFF-File-Format#gff-data-types)     | 356/364    | Number of bones referenced by this mesh (max 16).                                |
| QBones [offset](GFF-File-Format#file-structure-overview)                         | [uint32](GFF-File-Format#gff-data-types)     | 360/368    | [offset](GFF-File-Format#file-structure-overview) to [quaternion](MDL-MDX-File-Format#node-header) bind pose array (4 floats per bone).                        |
| QBones [count](GFF-File-Format#file-structure-overview)                          | [uint32](GFF-File-Format#gff-data-types)     | 364/372    | Number of [quaternion](MDL-MDX-File-Format#node-header) bind poses.                                                 |
| QBones Count (dup)                    | [uint32](GFF-File-Format#gff-data-types)     | 368/376    | Duplicate of QBones [count](GFF-File-Format#file-structure-overview).                                                       |
| TBones [offset](GFF-File-Format#file-structure-overview)                         | [uint32](GFF-File-Format#gff-data-types)     | 372/380    | [offset](GFF-File-Format#file-structure-overview) to translation bind pose array (3 floats per bone).                       |
| TBones [count](GFF-File-Format#file-structure-overview)                          | [uint32](GFF-File-Format#gff-data-types)     | 376/384    | Number of translation bind poses.                                                |
| TBones Count (dup)                    | [uint32](GFF-File-Format#gff-data-types)     | 380/388    | Duplicate of TBones [count](GFF-File-Format#file-structure-overview).                                                       |
| Unknown [array](2DA-File-Format)                         | [[uint32](GFF-File-Format#gff-data-types)][GFF-File-Format#dword](3)  | 384/392    | Purpose unknown.                                                                 |
| Bone [node](MDL-MDX-File-Format#node-structures) Serial Numbers              | [[uint16](GFF-File-Format#gff-data-types)][GFF-File-Format#word](16) | 396/404    | Serial [indices](2DA-File-Format#row-labels) of bone nodes (0xFFFF for unused slots).                          |
| Padding                               | [uint16](GFF-File-Format#gff-data-types)     | 428/436    | Padding for alignment.                                                           |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:181,193`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L181-L193) - Skinmesh [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definitions for K1 and K2  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:263-295`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L263-L295) - Skinmesh [header](GFF-File-Format#file-header) reading and bone [matrix](BWM-File-Format#vertex-data-processing) computation  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:508-529`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L508-L529) - Skinmesh bone map and bind pose processing

### Lightsaber [header](GFF-File-Format#file-header)

The Lightsaber [header](GFF-File-Format#file-header) extends the Trimesh [header](GFF-File-Format#file-header) with 20 additional bytes for lightsaber blade [geometry](MDL-MDX-File-Format#geometry-header). Total [size](GFF-File-Format#file-structure-overview) is 352 bytes (K1) or 360 bytes (K2). The lightsaber extension immediately follows the trimesh [data](GFF-File-Format#file-structure-overview).

| Name                   | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure-overview)     | Description                                                                      |
| ---------------------- | ------- | ---------- | -------------------------------------------------------------------------------- |
| *Trimesh [header](GFF-File-Format#file-header)*       | *...*   | *0-331*    | *Standard Trimesh Header (332 bytes K1, 340 bytes K2).*                          |
| [vertices](MDL-MDX-File-Format#vertex-structure) [offset](GFF-File-Format#file-structure-overview)        | [uint32](GFF-File-Format#gff-data-types)  | 332/340    | [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) [position](MDL-MDX-File-Format#node-header) [array](2DA-File-Format) in [MDL](MDL-MDX-File-Format) file (3 floats × 8 [vertices](MDL-MDX-File-Format#vertex-structure) × 20 pieces).|
| TexCoords [offset](GFF-File-Format#file-structure-overview)       | [uint32](GFF-File-Format#gff-data-types)  | 336/344    | [offset](GFF-File-Format#file-structure-overview) to [texture](TPC-File-Format) [coordinates](GFF-File-Format#are-area) [array](2DA-File-Format) in [MDL](MDL-MDX-File-Format) file (2 floats × 8 [vertices](MDL-MDX-File-Format#vertex-structure) × 20).   |
| Normals [offset](GFF-File-Format#file-structure-overview)         | [uint32](GFF-File-Format#gff-data-types)  | 340/348    | [offset](GFF-File-Format#file-structure-overview) to [vertex](MDL-MDX-File-Format#vertex-structure) normals [array](2DA-File-Format) in [MDL](MDL-MDX-File-Format) file (3 floats × 8 [vertices](MDL-MDX-File-Format#vertex-structure) × 20).        |
| Unknown 1              | [uint32](GFF-File-Format#gff-data-types)  | 344/352    | Purpose unknown.                                                                 |
| Unknown 2              | [uint32](GFF-File-Format#gff-data-types)  | 348/356    | Purpose unknown.                                                                 |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:2081`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L2081) - Lightsaber [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:327-378`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L327-L378) - Lightsaber [vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) reading and reorganization

### Light [header](GFF-File-Format#file-header)

The Light [header](GFF-File-Format#file-header) follows the [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header) and defines light source properties including lens flare effects. Total [size](GFF-File-Format#file-structure-overview) is 92 bytes.

| Name                        | [type](GFF-File-Format#data-types)    | [offset](GFF-File-Format#file-structure-overview) | Description                                                                      |
| --------------------------- | ------- | ------ | -------------------------------------------------------------------------------- |
| Unknown/Padding             | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](4)| 0 (0x0)     | Purpose unknown, possibly padding or reserved [values](GFF-File-Format#gff-data-types).                            |
| Flare Sizes [offset](GFF-File-Format#file-structure-overview)          | [uint32](GFF-File-Format#gff-data-types)  | 16 (0x10)    | [offset](GFF-File-Format#file-structure-overview) to flare sizes array (floats).                                            |
| Flare Sizes [count](GFF-File-Format#file-structure-overview)           | [uint32](GFF-File-Format#gff-data-types)  | 20 (0x14)    | Number of flare [size](GFF-File-Format#file-structure-overview) entries.                                                    |
| Flare Sizes Count (dup)     | [uint32](GFF-File-Format#gff-data-types)  | 24 (0x18)    | Duplicate of flare sizes [count](GFF-File-Format#file-structure-overview).                                                  |
| Flare [positions](MDL-MDX-File-Format#node-header) [offset](GFF-File-Format#file-structure-overview)      | [uint32](GFF-File-Format#gff-data-types)  | 28 (0x1C)    | [offset](GFF-File-Format#file-structure-overview) to flare [positions](MDL-MDX-File-Format#node-header) array (floats, 0.0-1.0 along light ray).               |
| Flare [positions](MDL-MDX-File-Format#node-header) [count](GFF-File-Format#file-structure-overview)       | [uint32](GFF-File-Format#gff-data-types)  | 32 (0x20)    | Number of flare [position](MDL-MDX-File-Format#node-header) entries.                                                |
| Flare [positions](MDL-MDX-File-Format#node-header) Count (dup) | [uint32](GFF-File-Format#gff-data-types)  | 36 (0x24)    | Duplicate of flare [positions](MDL-MDX-File-Format#node-header) [count](GFF-File-Format#file-structure-overview).                                              |
| Flare [color](GFF-File-Format#color) Shifts [offset](GFF-File-Format#file-structure-overview)   | [uint32](GFF-File-Format#gff-data-types)  | 40 (0x28)    | [offset](GFF-File-Format#file-structure-overview) to flare [color](GFF-File-Format#color) shift array (RGB floats).                                  |
| Flare [color](GFF-File-Format#color) Shifts [count](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)  | 44 (0x2C)    | Number of flare [color](GFF-File-Format#color) shift entries.                                             |
| Flare [color](GFF-File-Format#color) Shifts [count](GFF-File-Format#file-structure-overview)    | [uint32](GFF-File-Format#gff-data-types)  | 48 (0x30)    | Duplicate of flare [color](GFF-File-Format#color) shifts [count](GFF-File-Format#file-structure-overview).                                           |
| Flare [texture](TPC-File-Format) Names [offset](GFF-File-Format#file-structure-overview)  | [uint32](GFF-File-Format#gff-data-types)  | 52 (0x34)    | [offset](GFF-File-Format#file-structure-overview) to flare [texture](TPC-File-Format) name [string](GFF-File-Format#gff-data-types) [offsets](GFF-File-Format#file-structure-overview) [array](2DA-File-Format).                               |
| Flare [texture](TPC-File-Format) Names [count](GFF-File-Format#file-structure-overview)   | [uint32](GFF-File-Format#gff-data-types)  | 56 (0x38)    | Number of flare [texture](TPC-File-Format) names.                                                   |
| Flare [texture](TPC-File-Format) Names [count](GFF-File-Format#file-structure-overview)   | [uint32](GFF-File-Format#gff-data-types)  | 60 (0x3C)    | Duplicate of flare [texture](TPC-File-Format) names [count](GFF-File-Format#file-structure-overview).                                          |
| Flare Radius                | [float](GFF-File-Format#gff-data-types)   | 64 (0x40)    | Radius of the flare effect.                                                      |
| Light Priority              | [uint32](GFF-File-Format#gff-data-types)  | 68 (0x44)    | Rendering priority for light culling/sorting.                                    |
| Ambient Only                | [uint32](GFF-File-Format#gff-data-types)  | 72 (0x48)    | `1` if light only affects ambient, `0` for full lighting.                        |
| Dynamic [type](GFF-File-Format#data-types)                | [uint32](GFF-File-Format#gff-data-types)  | 76 (0x4C)    | [type](GFF-File-Format#data-types) of dynamic lighting behavior.                                               |
| Affect Dynamic              | [uint32](GFF-File-Format#gff-data-types)  | 80 (0x50)    | `1` if light affects dynamic objects, `0` otherwise.                             |
| Shadow                      | [uint32](GFF-File-Format#gff-data-types)  | 84 (0x54)    | `1` if light casts shadows, `0` otherwise.                                       |
| Flare                       | [uint32](GFF-File-Format#gff-data-types)  | 88 (0x58)    | `1` if lens flare effect enabled, `0` otherwise.                                 |
| Fading Light                | [uint32](GFF-File-Format#gff-data-types)  | 92 (0x5C)    | `1` if light intensity fades with distance, `0` otherwise.                       |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:175`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L175) - Light [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp) - Light [node](MDL-MDX-File-Format#node-structures) reading (see light processing)  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:227-250`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L227-L250) - Light [header](GFF-File-Format#file-header) reading and flare list processing

### Emitter [header](GFF-File-Format#file-header)

The Emitter [header](GFF-File-Format#file-header) follows the [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header) and defines particle emitter properties and behavior. Total [size](GFF-File-Format#file-structure-overview) is 224 bytes.

| Name                     | [type](GFF-File-Format#data-types)         | [offset](GFF-File-Format#file-structure-overview) | Description                                                                      |
| ------------------------ | ------------ | ------ | -------------------------------------------------------------------------------- |
| Dead Space               | [float](GFF-File-Format#gff-data-types)        | 0 (0x0)     | Minimum distance from emitter before particles become visible.                   |
| Blast Radius             | [float](GFF-File-Format#gff-data-types)        | 4 (0x4)     | Radius of explosive/blast particle effects.                                      |
| Blast Length             | [float](GFF-File-Format#gff-data-types)        | 8 (0x8)     | Length/duration of blast effects.                                                |
| Branch [count](GFF-File-Format#file-structure-overview)             | [uint32](GFF-File-Format#gff-data-types)       | 12 (0xC)    | Number of branching paths for particle trails.                                   |
| Control Point Smoothing  | [float](GFF-File-Format#gff-data-types)        | 16 (0x10)    | Smoothing factor for particle path control points.                               |
| X Grid                   | [uint32](GFF-File-Format#gff-data-types)       | 20 (0x14)    | Grid subdivisions along X axis for particle spawning.                            |
| Y Grid                   | [uint32](GFF-File-Format#gff-data-types)       | 24 (0x18)    | Grid subdivisions along Y axis for particle spawning.                            |
| Padding/Unknown          | [uint32](GFF-File-Format#gff-data-types)       | 28 (0x1C)    | Purpose unknown or padding.                                                      |
| Update Script            | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)     | 32 (0x20)    | Update behavior script name (e.g., "single", "fountain").                        |
| Render Script            | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)     | 64 (0x40)    | Render mode script name (e.g., "normal", "billboard_to_local_z").                |
| Blend Script             | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)     | 96 (0x60)    | Blend mode script name (e.g., "normal", "lighten").                              |
| [texture](TPC-File-Format) Name             | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)     | 128 (0x80)   | Particle [texture](TPC-File-Format) name ([null-terminated](https://en.cppreference.com/w/c/string/byte)).                                         |
| Chunk Name               | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](16)     | 160 (0xA0)   | Associated [model](MDL-MDX-File-Format) chunk name ([null-terminated](https://en.cppreference.com/w/c/string/byte)).                                   |
| Two-Sided [texture](TPC-File-Format)        | [uint32](GFF-File-Format#gff-data-types)       | 176 (0xB0)   | `1` if [texture](TPC-File-Format) should render two-sided, `0` for single-sided.                    |
| Loop                     | [uint32](GFF-File-Format#gff-data-types)       | 180 (0xB4)   | `1` if particle system loops, `0` for single playback.                           |
| Render Order             | [uint16](GFF-File-Format#gff-data-types)       | 184 (0xB8)   | Rendering priority/order for particle sorting.                                   |
| Frame Blending           | [uint8](GFF-File-Format#gff-data-types)        | 186 (0xBA)   | `1` if frame blending enabled, `0` otherwise.                                    |
| Depth [texture](TPC-File-Format) Name       | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32)     | 187 (0xBB)   | Depth/softparticle [texture](TPC-File-Format) name ([null-terminated](https://en.cppreference.com/w/c/string/byte)).                               |
| Padding                  | [uint8](GFF-File-Format#gff-data-types)        | 219 (0xDB)   | Padding [byte](GFF-File-Format#gff-data-types) for alignment.                                                      |
| [flags](GFF-File-Format#gff-data-types)                    | [uint32](GFF-File-Format#gff-data-types)       | 220 (0xDC)   | Emitter behavior [flags](GFF-File-Format#gff-data-types) bitmask (P2P, bounce, inherit, etc.).                     |

### Reference [header](GFF-File-Format#file-header)

The Reference [header](GFF-File-Format#file-header) follows the [node](MDL-MDX-File-Format#node-structures) [header](GFF-File-Format#file-header) and allows [models](MDL-MDX-File-Format) to reference external [model](MDL-MDX-File-Format) [files](GFF-File-Format). Total [size](GFF-File-Format#file-structure-overview) is 36 bytes. This is commonly used for attachable [models](MDL-MDX-File-Format) like weapons or helmets.

| Name          | [type](GFF-File-Format#data-types)     | [offset](GFF-File-Format#file-structure-overview) | Description                                                                      |
| ------------- | -------- | ------ | -------------------------------------------------------------------------------- |
| [model](MDL-MDX-File-Format) [ResRef](GFF-File-Format#gff-data-types)  | [[byte](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](32) | 0 (0x0)     | Referenced [model](MDL-MDX-File-Format) resource name without extension ([null-terminated](https://en.cppreference.com/w/c/string/byte)).              |
| Reattachable  | [uint32](GFF-File-Format#gff-data-types)   | 32 (0x20)    | `1` if [model](MDL-MDX-File-Format) can be detached and reattached dynamically, `0` if permanent.       |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:178,190`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L178-L190) - Reference [header](GFF-File-Format#file-header) [structure](GFF-File-Format#file-structure-overview) definitions for K1 and K2  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:179-180`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L179-L180) - Reference [node](MDL-MDX-File-Format#node-structures) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:311-316`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L311-L316) - Reference [header](GFF-File-Format#file-header) reading

---

## [controllers](MDL-MDX-File-Format#controllers)

### [controller](MDL-MDX-File-Format#controllers) [structure](GFF-File-Format#file-structure-overview)

Each [controller](MDL-MDX-File-Format#controllers) is 16 bytes in [size](GFF-File-Format#file-structure-overview) and defines [animation](MDL-MDX-File-Format#animation-header) [data](GFF-File-Format#file-structure-overview) for a [node](MDL-MDX-File-Format#node-structures) property over time. [controllers](MDL-MDX-File-Format#controllers) reference shared [keyframe](MDL-MDX-File-Format#controller-structure)/[data](GFF-File-Format#file-structure-overview) [arrays](2DA-File-Format) stored separately in the [model](MDL-MDX-File-Format).

| Name              | [type](GFF-File-Format#data-types)     | [offset](GFF-File-Format#file-structure-overview) | Description                                                                                    |
| ----------------- | -------- | ------ | ---------------------------------------------------------------------------------------------- |
| [type](GFF-File-Format#data-types)              | [uint32](GFF-File-Format#gff-data-types)   | 0 (0x0)     | [controller](MDL-MDX-File-Format#controllers) [type](GFF-File-Format#data-types) identifier (e.g., 8=[position](MDL-MDX-File-Format#node-header), 20=[orientation](MDL-MDX-File-Format#node-header), 36=[scale](MDL-MDX-File-Format#node-header)).                       |
| Unknown           | [uint16](GFF-File-Format#gff-data-types)   | 4 (0x4)     | Purpose unknown, typically `0xFFFF`.                                                           |
| Row [count](GFF-File-Format#file-structure-overview)         | [uint16](GFF-File-Format#gff-data-types)   | 6 (0x6)     | Number of [keyframe](MDL-MDX-File-Format#controller-structure) rows (timepoints) for this [controller](MDL-MDX-File-Format#controllers).                                      |
| Time [index](2DA-File-Format#row-labels)        | [uint16](GFF-File-Format#gff-data-types)   | 8 (0x8)     | [index](2DA-File-Format#row-labels) into [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) where time [values](GFF-File-Format#gff-data-types) begin.                                      |
| [data](GFF-File-Format#file-structure-overview) [index](2DA-File-Format#row-labels)        | [uint16](GFF-File-Format#gff-data-types)   | 10 (0xA)    | [index](2DA-File-Format#row-labels) into [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [array](2DA-File-Format) where property [values](GFF-File-Format#gff-data-types) begin.                                  |
| Column [count](GFF-File-Format#file-structure-overview)      | [uint8](GFF-File-Format#gff-data-types)    | 12 (0xC)    | Number of [float](GFF-File-Format#gff-data-types) [values](GFF-File-Format#gff-data-types) per keyframe (e.g., 3 for [position](MDL-MDX-File-Format#node-header) XYZ, 4 for [quaternion](MDL-MDX-File-Format#node-header) WXYZ).        |
| Padding           | [[uint8](GFF-File-Format#gff-data-types)][GFF-File-Format#byte](3) | 13 (0xD)    | Padding bytes for 16-[byte](GFF-File-Format#gff-data-types) alignment.                                                           |

**Note:** If [bit](GFF-File-Format#gff-data-types) 4 ([value](GFF-File-Format#gff-data-types) 0x10) is set in the column [count](GFF-File-Format#file-structure-overview) [byte](GFF-File-Format#gff-data-types), the [controller](MDL-MDX-File-Format#controllers) uses Bezier interpolation and stores 3× the [data](GFF-File-Format#file-structure-overview) per keyframe ([value](GFF-File-Format#gff-data-types), in-tangent, out-tangent).

**Reference**: [`vendor/mdlops/MDLOpsM.pm:199`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L199) - [controller](MDL-MDX-File-Format#controllers) [structure](GFF-File-Format#file-structure-overview) definition  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:1633-1676`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1633-L1676) - [controller](MDL-MDX-File-Format#controllers) reading and parsing  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:1678-1733`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1678-L1733) - [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) reading with Bezier and compressed [quaternion](MDL-MDX-File-Format#node-header) detection  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:150`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L150) - [controller](MDL-MDX-File-Format#controllers) [array](2DA-File-Format) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:441-483`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L441-L483) - [controller](MDL-MDX-File-Format#controllers) reading and [mesh](MDL-MDX-File-Format#trimesh-header)/light/emitter [controller](MDL-MDX-File-Format#controllers) processing

**Note:** [controllers](MDL-MDX-File-Format#controllers) [ARE](GFF-File-Format#are-area) stored in a shared [data](GFF-File-Format#file-structure-overview) [array](2DA-File-Format), allowing multiple [nodes](MDL-MDX-File-Format#node-structures) to reference the same [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview). The Time [index](2DA-File-Format#row-labels) and [data](GFF-File-Format#file-structure-overview) [index](2DA-File-Format#row-labels) [ARE](GFF-File-Format#are-area) [offsets](GFF-File-Format#file-structure-overview) into the [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [array](2DA-File-Format), not absolute [file](GFF-File-Format) [offsets](GFF-File-Format#file-structure-overview). [controllers](MDL-MDX-File-Format#controllers) with row [count](GFF-File-Format#file-structure-overview) of 0 represent constant (non-animated) [values](GFF-File-Format#gff-data-types).

---

## Additional [controller](MDL-MDX-File-Format#controllers) [types](GFF-File-Format#gff-data-types)

### Light [controllers](MDL-MDX-File-Format#controllers)

[controllers](MDL-MDX-File-Format#controllers) specific to light [nodes](MDL-MDX-File-Format#node-structures):

| [type](GFF-File-Format#data-types) | Description                      |
| ---- | -------------------------------- |
| 76   | Color (light [color](GFF-File-Format#color))              |
| 88   | Radius (light radius)            |
| 96   | Shadow Radius                    |
| 100  | Vertical Displacement            |
| 140  | Multiplier (light intensity)     |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:342-346`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L342-L346) - Light [controller](MDL-MDX-File-Format#controllers) [type](GFF-File-Format#data-types) definitions

### Emitter [controllers](MDL-MDX-File-Format#controllers)

[controllers](MDL-MDX-File-Format#controllers) specific to emitter [nodes](MDL-MDX-File-Format#node-structures):

| [type](GFF-File-Format#data-types) | Description                         |
| ---- | ----------------------------------- |
| 80   | Alpha End (final alpha [value](GFF-File-Format#gff-data-types))       |
| 84   | Alpha Start (initial alpha [value](GFF-File-Format#gff-data-types))   |
| 88   | Birth Rate (particle spawn rate)    |
| 92   | Bounce Coefficient                  |
| 96   | Combine Time                        |
| 100  | Drag                                |
| 104  | FPS (frames per second)             |
| 108  | Frame End                           |
| 112  | Frame Start                         |
| 116  | Gravity                             |
| 120  | Life Expectancy                     |
| 124  | Mass                                |
| 128  | P2P Bezier 2                        |
| 132  | P2P Bezier 3                        |
| 136  | Particle [rotation](MDL-MDX-File-Format#node-header)                   |
| 140  | Random Velocity                     |
| 144  | [size](GFF-File-Format#file-structure-overview) Start                          |
| 148  | [size](GFF-File-Format#file-structure-overview) End                            |
| 152  | [size](GFF-File-Format#file-structure-overview) Start Y                        |
| 156  | [size](GFF-File-Format#file-structure-overview) End Y                          |
| 160  | Spread                              |
| 164  | Threshold                           |
| 168  | Velocity                            |
| 172  | X [size](GFF-File-Format#file-structure-overview)                              |
| 176  | Y [size](GFF-File-Format#file-structure-overview)                              |
| 180  | Blur Length                         |
| 184  | Lightning Delay                     |
| 188  | Lightning Radius                    |
| 192  | Lightning [scale](MDL-MDX-File-Format#node-header)                     |
| 196  | Lightning Subdivide                 |
| 200  | Lightning Zig Zag                   |
| 216  | Alpha Mid                           |
| 220  | Percent Start                       |
| 224  | Percent Mid                         |
| 228  | Percent End                         |
| 232  | [size](GFF-File-Format#file-structure-overview) Mid                            |
| 236  | [size](GFF-File-Format#file-structure-overview) Mid Y                          |
| 240  | Random Birth Rate                   |
| 252  | Target [size](GFF-File-Format#file-structure-overview)                         |
| 256  | Number of Control Points            |
| 260  | Control Point Radius                |
| 264  | Control Point Delay                 |
| 268  | Tangent Spread                      |
| 272  | Tangent Length                      |
| 284  | [color](GFF-File-Format#color) Mid                           |
| 380  | [color](GFF-File-Format#color) End                           |
| 392  | [color](GFF-File-Format#color) Start                         |
| 502  | Emitter Detonate                    |

**Reference**: [`vendor/mdlops/MDLOpsM.pm:348-407`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L348-L407) - Emitter [controller](MDL-MDX-File-Format#controllers) [type](GFF-File-Format#data-types) definitions (based on fx_flame01.[MDL](MDL-MDX-File-Format) analysis)  
**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - Comprehensive emitter [controller](MDL-MDX-File-Format#controllers) list with all [controller](MDL-MDX-File-Format#controllers) [types](GFF-File-Format#data-types) and their [node](MDL-MDX-File-Format#node-structures) usage

### [mesh](MDL-MDX-File-Format#trimesh-header) [controllers](MDL-MDX-File-Format#controllers)

[controllers](MDL-MDX-File-Format#controllers) that can be used by all [mesh](MDL-MDX-File-Format#trimesh-header) [node](MDL-MDX-File-Format#node-structures) types (trimesh, skinmesh, animmesh, danglymesh, [AABB](BWM-File-Format#aabb-tree) [mesh](MDL-MDX-File-Format#trimesh-header), saber [mesh](MDL-MDX-File-Format#trimesh-header)):

| [type](GFF-File-Format#data-types) | Description                      |
| ---- | -------------------------------- |
| 100  | SelfIllumColor (self-illumination [color](GFF-File-Format#color)) |
| 128  | Alpha (transparency)              |

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - Mesh [controller](MDL-MDX-File-Format#controllers) types (SelfIllumColor, Alpha) for all [mesh](MDL-MDX-File-Format#trimesh-header) [nodes](MDL-MDX-File-Format#node-structures)

---

## [node](MDL-MDX-File-Format#node-structures) [types](GFF-File-Format#gff-data-types)

### [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) [bitmasks](GFF-File-Format#gff-data-types)

[node](MDL-MDX-File-Format#node-structures) [types](GFF-File-Format#gff-data-types) in KotOR [models](MDL-MDX-File-Format) [ARE](GFF-File-Format#are-area) defined using [bitmask](GFF-File-Format#gff-data-types) combinations. Each type of [data](GFF-File-Format#file-structure-overview) a [node](MDL-MDX-File-Format#node-structures) contains corresponds to a specific [bitmask](GFF-File-Format#gff-data-types).

```c
#define NODE_HAS_HEADER    0x00000001
#define NODE_HAS_LIGHT     0x00000002
#define NODE_HAS_EMITTER   0x00000004
#define NODE_HAS_CAMERA    0x00000008
#define NODE_HAS_REFERENCE 0x00000010
#define NODE_HAS_MESH      0x00000020
#define NODE_HAS_SKIN      0x00000040
#define NODE_HAS_ANIM      0x00000080
#define NODE_HAS_DANGLY    0x00000100
#define NODE_HAS_AABB      0x00000200
#define NODE_HAS_SABER     0x00000800
```

**Reference**: [`vendor/mdlops/MDLOpsM.pm:287-324`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L287-L324) - [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) [bitmask](GFF-File-Format#gff-data-types) definitions and constants  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp) - [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) [flag](GFF-File-Format#gff-data-types) checking (see MdlNodeFlags usage)  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py) - [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) detection and processing

### Common [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) Combinations

Common [node](MDL-MDX-File-Format#node-structures) [types](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) created by combining these [bitmasks](GFF-File-Format#gff-data-types):

| [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types)   | [bitmask](GFF-File-Format#gff-data-types) Combination                                      | [value](GFF-File-Format#gff-data-types)  |
| ----------- | -------------------------------------------------------- | ------ |
| Dummy       | `NODE_HAS_HEADER`                                        | 0x001  |
| Light       | `NODE_HAS_HEADER` \| `NODE_HAS_LIGHT`                    | 0x003  |
| Emitter     | `NODE_HAS_HEADER` \| `NODE_HAS_EMITTER`                  | 0x005  |
| Reference   | `NODE_HAS_HEADER` \| `NODE_HAS_REFERENCE`                | 0x011  |
| [mesh](MDL-MDX-File-Format#trimesh-header)        | `NODE_HAS_HEADER` \| `NODE_HAS_MESH`                     | 0x021  |
| Skin [mesh](MDL-MDX-File-Format#trimesh-header)   | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_SKIN`  | 0x061  |
| Anim [mesh](MDL-MDX-File-Format#trimesh-header)   | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_ANIM`  | 0x0A1  |
| Dangly [mesh](MDL-MDX-File-Format#trimesh-header) | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_DANGLY`| 0x121  |
| [AABB](BWM-File-Format#aabb-tree) [mesh](MDL-MDX-File-Format#trimesh-header)   | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_AABB`  | 0x221  |
| Saber [mesh](MDL-MDX-File-Format#trimesh-header)  | `NODE_HAS_HEADER` \| `NODE_HAS_MESH` \| `NODE_HAS_SABER` | 0x821  |

---

## [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [format](GFF-File-Format)

The [MDX](MDL-MDX-File-Format) [file](GFF-File-Format) contains additional [mesh](MDL-MDX-File-Format#trimesh-header) [data](GFF-File-Format#file-structure-overview) that complements the [MDL file](MDL-MDX-File-Format). The [data](GFF-File-Format#file-structure-overview) is organized based on [flags](GFF-File-Format#gff-data-types) indicating the presence of different [data](GFF-File-Format#file-structure-overview) [types](GFF-File-Format#gff-data-types).

### [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) Bitmap [masks](GFF-File-Format#gff-data-types)

The `MDX Data Flags` [field](GFF-File-Format#file-structure-overview) in the Trimesh [header](GFF-File-Format#file-header) uses [bitmask](GFF-File-Format#gff-data-types) [flags](GFF-File-Format#gff-data-types) to indicate which [vertex](MDL-MDX-File-Format#vertex-structure) attributes [ARE](GFF-File-Format#are-area) present in the [MDX files](MDL-MDX-File-Format):

```c
#define MDX_VERTICES        0x00000001  // Vertex positions (3 floats: X, Y, Z)
#define MDX_TEX0_VERTICES   0x00000002  // Primary texture coordinates (2 floats: U, V)
#define MDX_TEX1_VERTICES   0x00000004  // Secondary texture coordinates (2 floats: U, V) 
#define MDX_TEX2_VERTICES   0x00000008  // Tertiary texture coordinates (2 floats: U, V)
#define MDX_TEX3_VERTICES   0x00000010  // Quaternary texture coordinates (2 floats: U, V)
#define MDX_VERTEX_NORMALS  0x00000020  // Vertex normals (3 floats: X, Y, Z)
#define MDX_VERTEX_COLORS   0x00000040  // Vertex colors (3 floats: R, G, B)
#define MDX_TANGENT_SPACE   0x00000080  // Tangent space data (9 floats: tangent XYZ, bitangent XYZ, normal XYZ)
// Skin Mesh Specific Data (set programmatically, not stored in MDX Data Flags field)
#define MDX_BONE_WEIGHTS    0x00000800  // Bone weights for skinning (4 floats)
#define MDX_BONE_INDICES    0x00001000  // Bone indices for skinning (4 floats, cast to uint16)
```

**Note:** The bone weight and bone [index](2DA-File-Format#row-labels) flags (`0x00000800`, `0x00001000`) [ARE](GFF-File-Format#are-area) not actually stored in the [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [flags](GFF-File-Format#gff-data-types) [field](GFF-File-Format#file-structure-overview) but [ARE](GFF-File-Format#are-area) used internally by parsers to track skin [mesh](MDL-MDX-File-Format#trimesh-header) [vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) presence.

**Reference**: [`vendor/mdlops/MDLOpsM.pm:260-285`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L260-L285) - [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) bitmap definitions and row [structure](GFF-File-Format#file-structure-overview)  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:2324-2404`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L2324-L2404) - [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) reading with interleaved [vertex](MDL-MDX-File-Format#vertex-structure) attributes  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:255-262`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L255-L262) - [MDX](MDL-MDX-File-Format) [vertex](MDL-MDX-File-Format#vertex-structure) layout definition  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:380-384`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L380-L384) - [MDX](MDL-MDX-File-Format) [vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) reading  
**Reference**: [`vendor/KotOR.js/src/enums/odyssey/OdysseyModelMDXFlag.ts`](vendor/KotOR.js/src/enums/odyssey/OdysseyModelMDXFlag.ts) - [MDX](MDL-MDX-File-Format) [flag](GFF-File-Format#gff-data-types) enumeration definitions

**Note:** [MDX](MDL-MDX-File-Format) [vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) is stored in an interleaved [format](GFF-File-Format) based on the [MDX](MDL-MDX-File-Format) [vertex](MDL-MDX-File-Format#vertex-structure) [size](GFF-File-Format#file-structure-overview). Each [vertex](MDL-MDX-File-Format#vertex-structure) attribute is accessed via its relative [offset](GFF-File-Format#file-structure-overview) within the [vertex](MDL-MDX-File-Format#vertex-structure) stride. The [vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) is read from the [MDX files](MDL-MDX-File-Format) starting at the [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [offset](GFF-File-Format#file-structure-overview) specified in the Trimesh [header](GFF-File-Format#file-header).

### Skin [mesh](MDL-MDX-File-Format#trimesh-header) Specific [data](GFF-File-Format#file-structure-overview)

For skin [meshes](MDL-MDX-File-Format#trimesh-header), additional [vertex](MDL-MDX-File-Format#vertex-structure) attributes [ARE](GFF-File-Format#are-area) stored in the [MDX files](MDL-MDX-File-Format) for skeletal [animation](MDL-MDX-File-Format#animation-header):

- **Bone Weights** ([MDX](MDL-MDX-File-Format) Bone Weights [offset](GFF-File-Format#file-structure-overview)): 4 floats per [vertex](MDL-MDX-File-Format#vertex-structure) representing influence weights. Weights sum to 1.0 and correspond to the bone [indices](2DA-File-Format#row-labels). A weight of 0.0 indicates no influence.
  
- **Bone [indices](2DA-File-Format#row-labels)** ([MDX](MDL-MDX-File-Format) Bone [indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview)): 4 floats per vertex (cast to [uint16](GFF-File-Format#gff-data-types)) representing [indices](2DA-File-Format#row-labels) into the [mesh](MDL-MDX-File-Format#trimesh-header)'s bone map [array](2DA-File-Format). Each [index](2DA-File-Format#row-labels) maps to a skeleton bone that influences the [vertex](MDL-MDX-File-Format#vertex-structure).

The [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) for skin [meshes](MDL-MDX-File-Format#trimesh-header) is interleaved based on the [MDX](MDL-MDX-File-Format) [vertex](MDL-MDX-File-Format#vertex-structure) [size](GFF-File-Format#file-structure-overview) and the active [flags](GFF-File-Format#gff-data-types). The bone weight and bone [index](2DA-File-Format#row-labels) [data](GFF-File-Format#file-structure-overview) [ARE](GFF-File-Format#are-area) stored as separate attributes and accessed via their respective [offsets](GFF-File-Format#file-structure-overview).

**Reference**: [`vendor/mdlops/MDLOpsM.pm:2374-2395`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L2374-L2395) - Skin [mesh](MDL-MDX-File-Format#trimesh-header) bone weight processing in [MDX](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview)  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:263-295`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L263-L295) - Skin [mesh](MDL-MDX-File-Format#trimesh-header) [header](GFF-File-Format#file-header) and bone [data](GFF-File-Format#file-structure-overview) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:508-529`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L508-L529) - Skin [mesh](MDL-MDX-File-Format#trimesh-header) bone map and bone [node](MDL-MDX-File-Format#node-structures) processing

**Note:** Bone weights [ARE](GFF-File-Format#are-area) stored as 4 floats per [vertex](MDL-MDX-File-Format#vertex-structure) and should sum to 1.0. Bone [indices](2DA-File-Format#row-labels) [ARE](GFF-File-Format#are-area) stored as 4 floats but [ARE](GFF-File-Format#are-area) cast to [uint16](GFF-File-Format#gff-data-types) when used. A weight of 0.0 indicates no influence from that bone. The bone [indices](2DA-File-Format#row-labels) reference the bone map [array](2DA-File-Format), which maps to skeleton bone numbers.

---

## [vertex](MDL-MDX-File-Format#vertex-structure) and [face](MDL-MDX-File-Format#face-structure) [data](GFF-File-Format#file-structure-overview)

### [vertex](MDL-MDX-File-Format#vertex-structure) [structure](GFF-File-Format#file-structure-overview)

Each [vertex](MDL-MDX-File-Format#vertex-structure) has the following [structure](GFF-File-Format#file-structure-overview):

| Name | [type](GFF-File-Format#data-types)  | Description         |
| ---- | ----- | ------------------- |
| X    | [float](GFF-File-Format#gff-data-types) | X-[coordinate](GFF-File-Format#are-area)        |
| Y    | [float](GFF-File-Format#gff-data-types) | Y-[coordinate](GFF-File-Format#are-area)        |
| Z    | [float](GFF-File-Format#gff-data-types) | Z-[coordinate](GFF-File-Format#are-area)        |

### [face](MDL-MDX-File-Format#face-structure) [structure](GFF-File-Format#file-structure-overview)

Each face (triangle) is defined by:

| Name                | [type](GFF-File-Format#data-types)    | Description                                      |
| ------------------- | ------- | ------------------------------------------------ |
| Normal              | [vertex](MDL-MDX-File-Format#vertex-structure)  | Normal [vector](GFF-File-Format#gff-data-types) of the [face](MDL-MDX-File-Format#face-structure) plane.                 |
| Plane Coefficient   | [float](GFF-File-Format#gff-data-types)   | D component of the [face](MDL-MDX-File-Format#face-structure) plane equation.          |
| [material](MDL-MDX-File-Format#trimesh-header)            | [uint32](GFF-File-Format#gff-data-types)  | [material](MDL-MDX-File-Format#trimesh-header) index (refers to `surfacemat.2da`).     |
| [face](MDL-MDX-File-Format#face-structure) [adjacency](BWM-File-Format#walkable-adjacencies) 1    | [uint16](GFF-File-Format#gff-data-types)  | [index](2DA-File-Format#row-labels) of adjacent [face](MDL-MDX-File-Format#face-structure) 1.                        |
| [face](MDL-MDX-File-Format#face-structure) [adjacency](BWM-File-Format#walkable-adjacencies) 2    | [uint16](GFF-File-Format#gff-data-types)  | [index](2DA-File-Format#row-labels) of adjacent [face](MDL-MDX-File-Format#face-structure) 2.                        |
| [face](MDL-MDX-File-Format#face-structure) [adjacency](BWM-File-Format#walkable-adjacencies) 3    | [uint16](GFF-File-Format#gff-data-types)  | [index](2DA-File-Format#row-labels) of adjacent [face](MDL-MDX-File-Format#face-structure) 3.                        |
| [vertex](MDL-MDX-File-Format#vertex-structure) 1            | [uint16](GFF-File-Format#gff-data-types)  | [index](2DA-File-Format#row-labels) of the first [vertex](MDL-MDX-File-Format#vertex-structure).                       |
| [vertex](MDL-MDX-File-Format#vertex-structure) 2            | [uint16](GFF-File-Format#gff-data-types)  | [index](2DA-File-Format#row-labels) of the second [vertex](MDL-MDX-File-Format#vertex-structure).                      |
| [vertex](MDL-MDX-File-Format#vertex-structure) 3            | [uint16](GFF-File-Format#gff-data-types)  | [index](2DA-File-Format#row-labels) of the third [vertex](MDL-MDX-File-Format#vertex-structure).                       |

**Reference**: [`vendor/mdlops/MDLOpsM.pm`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm) - [face](MDL-MDX-File-Format#face-structure) [structure](GFF-File-Format#file-structure-overview) reading (see [face](MDL-MDX-File-Format#face-structure) [array](2DA-File-Format) processing)  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:390-409`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L390-L409) - [face](MDL-MDX-File-Format#face-structure) [structure](GFF-File-Format#file-structure-overview) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:530-540`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L530-L540) - [face](MDL-MDX-File-Format#face-structure) [structure](GFF-File-Format#file-structure-overview) reading  
**Reference**: [`vendor/kotor/docs/mdl.md:36-42`](vendor/kotor/docs/mdl.md#face) - [face](MDL-MDX-File-Format#face-structure) [structure](GFF-File-Format#file-structure-overview) analysis  
**Reference**: [`vendor/kotor/docs/mdl.md:52-63`](vendor/kotor/docs/mdl.md#node-structure) - Typical [node](MDL-MDX-File-Format#node-structures) hierarchy [structure](GFF-File-Format#file-structure-overview) for creatures, players, and areas

**Note:** [face](MDL-MDX-File-Format#face-structure) normals [ARE](GFF-File-Format#are-area) precomputed and stored with each [face](MDL-MDX-File-Format#face-structure). The plane coefficient (D) is the distance from the origin to the plane along the normal. [face](MDL-MDX-File-Format#face-structure) [adjacency](BWM-File-Format#walkable-adjacencies) [indices](2DA-File-Format#row-labels) [ARE](GFF-File-Format#are-area) used for smooth shading and culling optimization. The [material](MDL-MDX-File-Format#trimesh-header) [index](2DA-File-Format#row-labels) references entries in `surfacemat.2da` for surface properties.

### [vertex](MDL-MDX-File-Format#vertex-structure) [index](2DA-File-Format#row-labels) [arrays](2DA-File-Format)

The Trimesh [header](GFF-File-Format#file-header) contains [arrays](2DA-File-Format) for organizing [vertex](MDL-MDX-File-Format#vertex-structure) [indices](2DA-File-Format#row-labels) used by [faces](MDL-MDX-File-Format#face-structure). These [arrays](2DA-File-Format) allow efficient [vertex](MDL-MDX-File-Format#vertex-structure) sharing and indexing:

- **[indices](2DA-File-Format#row-labels) [count](GFF-File-Format#file-structure-overview) [array](2DA-File-Format)**: Contains the number of [vertex](MDL-MDX-File-Format#vertex-structure) [indices](2DA-File-Format#row-labels) for each [vertex](MDL-MDX-File-Format#vertex-structure) group. Each entry is a [uint32](GFF-File-Format#gff-data-types) indicating how many [indices](2DA-File-Format#row-labels) reference that [vertex](MDL-MDX-File-Format#vertex-structure) [position](MDL-MDX-File-Format#node-header).
- **[indices](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) [array](2DA-File-Format)**: Contains [offsets](GFF-File-Format#file-structure-overview) into the [vertex](MDL-MDX-File-Format#vertex-structure) [index](2DA-File-Format#row-labels) [data](GFF-File-Format#file-structure-overview), allowing access to the actual [index](2DA-File-Format#row-labels) [values](GFF-File-Format#gff-data-types) for each [vertex](MDL-MDX-File-Format#vertex-structure) group.
- **Inverted Counter [array](2DA-File-Format)**: Used for optimization and culling, tracking [face](MDL-MDX-File-Format#face-structure) connectivity information.

The [vertex](MDL-MDX-File-Format#vertex-structure) [indices](2DA-File-Format#row-labels) themselves [ARE](GFF-File-Format#are-area) stored as [uint16](GFF-File-Format#gff-data-types) [values](GFF-File-Format#gff-data-types) and reference [positions](MDL-MDX-File-Format#node-header) in the [vertex](MDL-MDX-File-Format#vertex-structure) [coordinate](GFF-File-Format#are-area) array (either in [MDL](MDL-MDX-File-Format) or [MDX](MDL-MDX-File-Format) depending on the [mesh](MDL-MDX-File-Format#trimesh-header) [type](GFF-File-Format#data-types)).

**Reference**: [`vendor/mdlops/MDLOpsM.pm:221-227`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L221-L227) - [vertex](MDL-MDX-File-Format#vertex-structure) [index](2DA-File-Format#row-labels) [array](2DA-File-Format) [structure](GFF-File-Format#file-structure-overview) definitions  
**Reference**: [`vendor/kotor/docs/mdl.md:17-21`](vendor/kotor/docs/mdl.md#node-chunk) - [vertex](MDL-MDX-File-Format#vertex-structure) [index](2DA-File-Format#row-labels) [array](2DA-File-Format) layout analysis  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:201-214`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L201-L214) - [vertex](MDL-MDX-File-Format#vertex-structure) [index](2DA-File-Format#row-labels) [array](2DA-File-Format) reading

---

## [vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) Processing

### [vertex](MDL-MDX-File-Format#vertex-structure) Normal Calculation

[vertex](MDL-MDX-File-Format#vertex-structure) normals [ARE](GFF-File-Format#are-area) computed using surrounding [face](MDL-MDX-File-Format#face-structure) normals, with optional weighting methods:

1. **Area Weighting**: [faces](MDL-MDX-File-Format#face-structure) contribute to the [vertex](MDL-MDX-File-Format#vertex-structure) normal based on their surface area.

   ```c
   area = 0.5f * length(cross(edge1, edge2))
   weighted_normal = face_normal * area
   ```

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:465-488`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L465-L488) - Heron's formula implementation
   Uses Heron's formula for area calculation.

2. **Angle Weighting**: [faces](MDL-MDX-File-Format#face-structure) contribute based on the angle at the [vertex](MDL-MDX-File-Format#vertex-structure).

   ```c
   angle = arccos(dot(normalize(v1 - v0), normalize(v2 - v0)))
   weighted_normal = face_normal * angle
   ```

3. **Crease Angle Limiting**: [faces](MDL-MDX-File-Format#face-structure) [ARE](GFF-File-Format#are-area) excluded if the angle between their normals exceeds a threshold (e.g., 60 degrees).

### Tangent Space Calculation

For normal/bump mapping, tangent and bitangent [vectors](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) calculated per [face](MDL-MDX-File-Format#face-structure). KotOR uses a specific tangent space convention that differs from standard implementations.

**Reference**: [`vendor/mdlops/MDLOpsM.pm:5470-5596`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5470-L5596) - Complete tangent space calculation  
**Based on**: [OpenGL Tutorial - Normal Mapping](http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/) with KotOR-specific modifications

1. **Per-[face](MDL-MDX-File-Format#face-structure) Tangent and Bitangent**:

   ```c
   deltaPos1 = v1 - v0;
   deltaPos2 = v2 - v0;
   deltaUV1 = uv1 - uv0;
   deltaUV2 = uv2 - uv0;

   float r = 1.0f / (deltaUV1.x * deltaUV2.y - deltaUV1.y * deltaUV2.x);
   
   // Handle divide-by-zero from overlapping texture vertices
   if (r == 0.0f) {
       r = 2406.6388; // Magic factor from p_g0t01.mdl analysis ([mdlops:5510-5512](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5510-L5512))
   }
   
   tangent = (deltaPos1 * deltaUV2.y - deltaPos2 * deltaUV1.y) * r;
   bitangent = (deltaPos2 * deltaUV1.x - deltaPos1 * deltaUV2.x) * r;
   
   // Normalize both vectors
   tangent = normalize(tangent);
   bitangent = normalize(bitangent);
   
   // Fix zero vectors from degenerate UVs ([mdlops:5536-5539, 5563-5566](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5536-L5566))
   if (length(tangent) < epsilon) {
       tangent = vec3(1.0, 0.0, 0.0);
   }
   if (length(bitangent) < epsilon) {
       bitangent = vec3(1.0, 0.0, 0.0);
   }
   ```

2. **KotOR-Specific Handedness Correction**:

   **Important**: KotOR expects tangent space to NOT form a right-handed [coordinate](GFF-File-Format#are-area) system.
   **Reference**: [`vendor/mdlops/MDLOpsM.pm:5570-5587`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5570-L5587)

   ```c
   // KotOR wants dot(cross(N,T), B) < 0 (NOT right-handed)
   if (dot(cross(normal, tangent), bitangent) > 0.0f) {
       tangent = -tangent;
   }
   ```

3. **[texture](TPC-File-Format) Mirroring Detection and Correction**:

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:5588-5596`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L5588-L5596)

   ```c
   // Detect texture mirroring via UV triangle orientation
   tNz = (uv0.x - uv1.x) * (uv2.y - uv1.y) - (uv0.y - uv1.y) * (uv2.x - uv1.x);
   
   // If texture is mirrored, invert both tangent and bitangent
   if (tNz > 0.0f) {
       tangent = -tangent;
       bitangent = -bitangent;
   }
   ```

4. **Per-[vertex](MDL-MDX-File-Format#vertex-structure) Tangent Space**: Averaged from connected [face](MDL-MDX-File-Format#face-structure) tangents and bitangents, using the same weighting methods as normals.

---

## [model](MDL-MDX-File-Format) Classification [flags](GFF-File-Format#gff-data-types)

The [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header)'s Classification byte ([offset](GFF-File-Format#file-structure-overview) 0 in [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header), [offset](GFF-File-Format#file-structure-overview) 92 from [MDL](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) start) uses these [values](GFF-File-Format#gff-data-types) to categorize the [model](MDL-MDX-File-Format) [type](GFF-File-Format#data-types):

| Classification | [value](GFF-File-Format#gff-data-types) | Description                                                    |
| -------------- | ----- | -------------------------------------------------------------- |
| Other          | 0x00  | Uncategorized or generic [model](MDL-MDX-File-Format).                                |
| Effect         | 0x01  | Visual effect model (particles, beams, explosions).            |
| Tile           | 0x02  | Tileset/environmental [geometry](MDL-MDX-File-Format#geometry-header) [model](MDL-MDX-File-Format).                          |
| Character      | 0x04  | Character or creature model (player, NPC, creature).           |
| Door           | 0x08  | Door [model](MDL-MDX-File-Format) with open/close [animations](MDL-MDX-File-Format#animation-header).                         |
| Lightsaber     | 0x10  | Lightsaber weapon [model](MDL-MDX-File-Format) with dynamic blade.                    |
| Placeable      | 0x20  | Placeable object model (furniture, containers, switches).      |
| Flyer          | 0x40  | Flying vehicle or creature [model](MDL-MDX-File-Format).                              |

**Note:** These [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) not [bitmask](GFF-File-Format#gff-data-types) [flags](GFF-File-Format#gff-data-types) and should not be combined. Each [model](MDL-MDX-File-Format) has exactly one classification [value](GFF-File-Format#gff-data-types).

---

## [file](GFF-File-Format) Identification

### Binary vs ASCII [format](GFF-File-Format)

- **Binary [model](MDL-MDX-File-Format)**: The first 4 bytes [ARE](GFF-File-Format#are-area) all zeros (`0x00000000`).
- **ASCII [model](MDL-MDX-File-Format)**: The first 4 bytes contain non-zero values (text [header](GFF-File-Format#file-header)).

**Reference**: [`vendor/mdlops/MDLOpsM.pm:412-435`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L412-L435) - Binary vs ASCII [format](GFF-File-Format) detection  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:100-102`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L100-L102) - Binary [format](GFF-File-Format) validation

### KotOR 1 vs KotOR 2 [models](MDL-MDX-File-Format)

The game version can be determined by examining Function [pointer](GFF-File-Format#file-structure-overview) 0 in the [geometry](MDL-MDX-File-Format#geometry-header) Header ([offset](GFF-File-Format#file-structure-overview) 12 in [file](GFF-File-Format), [offset](GFF-File-Format#file-structure-overview) 0 in [MDL](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview)):

| Platform/Version    | [geometry](MDL-MDX-File-Format#geometry-header) Function Ptr | [animation](MDL-MDX-File-Format#animation-header) Function Ptr |
| ------------------- | --------------------- | ---------------------- |
| KotOR 1 (PC)        | `4273776` (0x413750)  | `4273392` (0x4135D0)   |
| KotOR 2 (PC)        | `4285200` (0x416610)  | `4284816` (0x416490)   |
| KotOR 1 (Xbox)      | `4254992` (0x40EE90)  | `4254608` (0x40ED10)   |
| KotOR 2 (Xbox)      | `4285872` (0x416950)  | `4285488` (0x4167D0)   |

**Usage:** Parsers should check this [value](GFF-File-Format#gff-data-types) to determine:

- Whether the [model](MDL-MDX-File-Format) is from KotOR 1 or KotOR 2 (affects Trimesh [header](GFF-File-Format#file-header) [size](GFF-File-Format#file-structure-overview): 332 vs 340 bytes)
- Whether this is a [model](MDL-MDX-File-Format) [geometry](MDL-MDX-File-Format#geometry-header) header (`0x00`) or [animation](MDL-MDX-File-Format#animation-header) [geometry](MDL-MDX-File-Format#geometry-header) header (`0x01`)

**Reference**: [`vendor/mdlops/MDLOpsM.pm:437-461`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L437-L461) - Version detection using function pointer (KotOR 2 PC: `4285200`)  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:51-53,90`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L51-L53-L90) - TSL version detection  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:107-111`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L107-L111) - Version and platform detection

---

## [model](MDL-MDX-File-Format) Hierarchy

### [node](MDL-MDX-File-Format#node-structures) Relationships

- Each [node](MDL-MDX-File-Format#node-structures) can have a parent [node](MDL-MDX-File-Format#node-structures), forming a hierarchy.
- The root [node](MDL-MDX-File-Format#node-structures) is referenced in the [geometry](MDL-MDX-File-Format#geometry-header) [header](GFF-File-Format#file-header).
- [nodes](MDL-MDX-File-Format#node-structures) inherit [transformations](BWM-File-Format#vertex-data-processing) from their parents.

### [node](MDL-MDX-File-Format#node-structures) [transformations](BWM-File-Format#vertex-data-processing)

1. **[position](MDL-MDX-File-Format#node-header) Transform**:
   - Stored in [controller](MDL-MDX-File-Format#controllers) type `8`.
   - Accumulated through the [node](MDL-MDX-File-Format#node-structures) hierarchy.
   - Applied as translation after [orientation](MDL-MDX-File-Format#node-header).

2. **[orientation](MDL-MDX-File-Format#node-header) Transform**:
   - Stored in [controller](MDL-MDX-File-Format#controllers) type `20`.
   - Uses [quaternion](MDL-MDX-File-Format#node-header) multiplication.
   - Applied before [position](MDL-MDX-File-Format#node-header) translation.

---

## Smoothing Groups

- **Automatic Smoothing**: Groups [ARE](GFF-File-Format#are-area) created based on [face](MDL-MDX-File-Format#face-structure) connectivity and normal angles.
- **Threshold Angles**: [faces](MDL-MDX-File-Format#face-structure) with normals within a certain angle [ARE](GFF-File-Format#are-area) grouped.

**Reference**: [`vendor/mdlops/MDLOpsM.pm`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm) - Smoothing group calculation (see version history notes about cross-[mesh](MDL-MDX-File-Format#trimesh-header) smoothing using world-space normals)  
**Reference**: [`vendor/mdlops/MDLOpsM.pm:92-93`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L92-L93) - Version history notes on cross-[mesh](MDL-MDX-File-Format#trimesh-header) smoothing improvements

---

## Binary [model](MDL-MDX-File-Format) [format](GFF-File-Format) Details (Aurora Engine)

The following information is derived from Tim Smith (Torlack)'s reverse-engineered specifications and xoreos-docs, documenting the Aurora engine's binary [model](MDL-MDX-File-Format) [format](GFF-File-Format) shared across Neverwinter Nights, KotOR, and other BioWare games.

**Source**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - Tim Smith's binary [model](MDL-MDX-File-Format) [format](GFF-File-Format) documentation  
**Source**: [`vendor/xoreos-docs/specs/kotor_mdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/kotor_mdl.html) - Partial KotOR-specific [model](MDL-MDX-File-Format) [format](GFF-File-Format) notes

### Binary [model](MDL-MDX-File-Format) [file](GFF-File-Format) Layout

The binary [model](MDL-MDX-File-Format) [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) consists of three main sections:

1. **[file](GFF-File-Format) [header](GFF-File-Format#file-header)** (12 bytes): Provides [offset](GFF-File-Format#file-structure-overview) and [size](GFF-File-Format#file-structure-overview) information for the raw [data](GFF-File-Format#file-structure-overview) section
2. **[model](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview)**: Contains all [node](MDL-MDX-File-Format#node-structures) [structures](GFF-File-Format#file-structure-overview), [geometry](MDL-MDX-File-Format#geometry-header) [headers](GFF-File-Format#file-header), and [animation](MDL-MDX-File-Format#animation-header) [data](GFF-File-Format#file-structure-overview)
3. **Raw [data](GFF-File-Format#file-structure-overview)**: Contains [vertex](MDL-MDX-File-Format#vertex-structure) buffers, [texture](TPC-File-Format) [coordinates](GFF-File-Format#are-area), and other per-[vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview)

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - Binary [model](MDL-MDX-File-Format) [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) overview

### [pointers](GFF-File-Format#file-structure-overview) and [arrays](2DA-File-Format) in Binary [models](MDL-MDX-File-Format)

Binary [model](MDL-MDX-File-Format) [files](GFF-File-Format) use two [types](GFF-File-Format#gff-data-types) of [pointers](GFF-File-Format#file-structure-overview):

- **[model](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) [pointers](GFF-File-Format#file-structure-overview)**: 32-[bit](GFF-File-Format#gff-data-types) [offsets](GFF-File-Format#file-structure-overview) from the start of the [model](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview) section. A [value](GFF-File-Format#gff-data-types) of `0` represents a NULL [pointer](GFF-File-Format#file-structure-overview).
- **Raw [data](GFF-File-Format#file-structure-overview) [pointers](GFF-File-Format#file-structure-overview)**: 32-[bit](GFF-File-Format#gff-data-types) [offsets](GFF-File-Format#file-structure-overview) from the start of the raw [data](GFF-File-Format#file-structure-overview) section. A [value](GFF-File-Format#gff-data-types) of `0xFFFFFFFF` (or `-1` signed) represents a NULL [pointer](GFF-File-Format#file-structure-overview), since [offset](GFF-File-Format#file-structure-overview) `0` is a valid [position](MDL-MDX-File-Format#node-header) in raw [data](GFF-File-Format#file-structure-overview).

**Note**: After loading from disk, these [offsets](GFF-File-Format#file-structure-overview) can be converted to actual memory [pointers](GFF-File-Format#file-structure-overview) on 32-[bit](GFF-File-Format#gff-data-types) address processors, improving runtime performance.

[arrays](2DA-File-Format) in binary [models](MDL-MDX-File-Format) consist of three elements:

| [offset](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#data-types)   | Description                                    |
| ------ | ------ | ---------------------------------------------- |
| 0x0000 | [uint32](GFF-File-Format#gff-data-types) | [pointer](GFF-File-Format#file-structure-overview)/[offset](GFF-File-Format#file-structure-overview) to the first element            |
| 0x0004 | [uint32](GFF-File-Format#gff-data-types) | Number of used entries in the [array](2DA-File-Format)            |
| 0x0008 | [uint32](GFF-File-Format#gff-data-types) | Number of allocated entries in the [array](2DA-File-Format)       |

For binary [model](MDL-MDX-File-Format) [files](GFF-File-Format), the number of used entries and allocated entries [ARE](GFF-File-Format#are-area) always the same. During runtime or compilation, these [values](GFF-File-Format#gff-data-types) may differ as [arrays](2DA-File-Format) grow dynamically.

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - [arrays](2DA-File-Format) and [pointers](GFF-File-Format#file-structure-overview) explanation

### [model](MDL-MDX-File-Format) Routines and [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) Identification

**Important**: Early reverse-engineering efforts incorrectly used "tokens" (six 4-[byte](GFF-File-Format#gff-data-types) [values](GFF-File-Format#gff-data-types) at the start of [nodes](MDL-MDX-File-Format#node-structures)) to identify [node](MDL-MDX-File-Format#node-structures) [types](GFF-File-Format#gff-data-types). These [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) actually function routine addresses from the Win32/NT image loader (which loads images at `0x0041000`), and should **not** be relied upon for [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) identification.

The proper method to identify [node](MDL-MDX-File-Format#node-structures) [types](GFF-File-Format#gff-data-types) is using the **32-[bit](GFF-File-Format#gff-data-types) [bitmask](GFF-File-Format#gff-data-types)** stored in each [node](MDL-MDX-File-Format#node-structures) header ([offset](GFF-File-Format#file-structure-overview) 0x006C in the [node](MDL-MDX-File-Format#node-structures) [structure](GFF-File-Format#file-structure-overview)). This [bitmask](GFF-File-Format#gff-data-types) identifies which [structures](GFF-File-Format#file-structure-overview) make up the [node](MDL-MDX-File-Format#node-structures).

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - [model](MDL-MDX-File-Format) routines and [node](MDL-MDX-File-Format#node-structures) [type](GFF-File-Format#data-types) identification

### Part Numbers

Part numbers [ARE](GFF-File-Format#are-area) [values](GFF-File-Format#gff-data-types) assigned to [nodes](MDL-MDX-File-Format#node-structures) during [model](MDL-MDX-File-Format) compilation. After [geometry](MDL-MDX-File-Format#geometry-header) compilation, these [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) adjusted:

- If a [model](MDL-MDX-File-Format) has a supermodel, the [geometry](MDL-MDX-File-Format#geometry-header) is compared against the supermodel's [geometry](MDL-MDX-File-Format#geometry-header). [nodes](MDL-MDX-File-Format#node-structures) matching names in the supermodel receive the supermodel's part number. [nodes](MDL-MDX-File-Format#node-structures) not found receive part number `-1`.
- If no supermodel exists, part numbers remain as assigned during compilation.
- After [animation](MDL-MDX-File-Format#animation-header) [geometry](MDL-MDX-File-Format#geometry-header) compilation, the same process matches [animation](MDL-MDX-File-Format#animation-header) [nodes](MDL-MDX-File-Format#node-structures) against the main [model](MDL-MDX-File-Format) geometry (not the supermodel).

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - Part numbers explanation

### [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) Storage

[controllers](MDL-MDX-File-Format#controllers) [ARE](GFF-File-Format#are-area) stored as two [arrays](2DA-File-Format) in the [model](MDL-MDX-File-Format) [data](GFF-File-Format#file-structure-overview):

1. **[controller](MDL-MDX-File-Format#controllers) [structure](GFF-File-Format#file-structure-overview) [array](2DA-File-Format)**: Contains metadata about each controller ([type](GFF-File-Format#data-types), row [count](GFF-File-Format#file-structure-overview), [data](GFF-File-Format#file-structure-overview) [indices](2DA-File-Format#row-labels))
2. **Float [array](2DA-File-Format)**: Contains the actual [controller](MDL-MDX-File-Format#controllers) data (time keys and property [values](GFF-File-Format#gff-data-types))

All time keys [ARE](GFF-File-Format#are-area) stored contiguously, followed by all [data](GFF-File-Format#file-structure-overview) [values](GFF-File-Format#gff-data-types) stored contiguously. For example, if a keyed [controller](MDL-MDX-File-Format#controllers) has 3 rows with time keys starting at [float](GFF-File-Format#gff-data-types) [index](2DA-File-Format#row-labels) 5, the time keys would be at [indices](2DA-File-Format#row-labels) 5, 6, and 7.

**Note**: [controllers](MDL-MDX-File-Format#controllers) that aren't time-keyed [ARE](GFF-File-Format#are-area) still stored as if they [ARE](GFF-File-Format#are-area) time-keyed but with a single row and a time [KEY](KEY-File-Format) [value](GFF-File-Format#gff-data-types) of zero. It's impossible to distinguish between a non-keyed [controller](MDL-MDX-File-Format#controllers) and a keyed [controller](MDL-MDX-File-Format#controllers) with one row at time zero.

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - [controller](MDL-MDX-File-Format#controllers) [structure](GFF-File-Format#file-structure-overview) and [data](GFF-File-Format#file-structure-overview) storage

### Bezier Interpolation

Bezier interpolation provides smooth, non-linear [animation](MDL-MDX-File-Format#animation-header) curves using control points (tangents). In the [controller](MDL-MDX-File-Format#controllers) [structure](GFF-File-Format#file-structure-overview), Bezier interpolation is indicated by ORing `0x10` into the column [count](GFF-File-Format#file-structure-overview) [byte](GFF-File-Format#gff-data-types). When this [flag](GFF-File-Format#gff-data-types) is set, the [controller](MDL-MDX-File-Format#controllers) stores 3 [values](GFF-File-Format#gff-data-types) per column per [keyframe](MDL-MDX-File-Format#controller-structure): ([value](GFF-File-Format#gff-data-types), in-tangent, out-tangent).

**Note**: At the time of [`vendor/xoreos-docs/specs/kotor_mdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/kotor_mdl.html) documentation, it was unclear if any BioWare [models](MDL-MDX-File-Format) actually use bezier interpolation or if the rendering engine supports it. However, the [format](GFF-File-Format) specification includes support for it.

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - Bezier interpolation notes  
**See Also**: [Controller Data Formats - Bezier Interpolation](#bezier-interpolation) section below for ASCII [format](GFF-File-Format) details

### AABB (Axis-Aligned [bounding box](MDL-MDX-File-Format#model-header)) [mesh](MDL-MDX-File-Format#trimesh-header) [nodes](MDL-MDX-File-Format#node-structures)

[AABB](BWM-File-Format#aabb-tree) [mesh](MDL-MDX-File-Format#trimesh-header) [nodes](MDL-MDX-File-Format#node-structures) provide collision detection capabilities. The [AABB](BWM-File-Format#aabb-tree) [structure](GFF-File-Format#file-structure-overview) uses a binary tree for efficient collision queries:

| [offset](GFF-File-Format#file-structure-overview) | [type](GFF-File-Format#data-types)           | Description                                    |
| ------ | -------------- | ---------------------------------------------- |
| 0x0000 | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)       | Min [bounding box](MDL-MDX-File-Format#model-header) [coordinates](GFF-File-Format#are-area)                   |
| 0x000C | [[float](GFF-File-Format#gff-data-types)][GFF-File-Format#float](3)       | Max [bounding box](MDL-MDX-File-Format#model-header) [coordinates](GFF-File-Format#are-area)                   |
| 0x0018 | [AABB](BWM-File-Format#aabb-tree) Entry Ptr | Left child [node](MDL-MDX-File-Format#node-structures) [pointer](GFF-File-Format#file-structure-overview)                        |
| 0x001C | [AABB](BWM-File-Format#aabb-tree) Entry Ptr | Right child [node](MDL-MDX-File-Format#node-structures) [pointer](GFF-File-Format#file-structure-overview)                       |
| 0x0020 | [int32](GFF-File-Format#gff-data-types)          | Leaf [face](MDL-MDX-File-Format#face-structure) part number (or -1 if not a leaf)   |
| 0x0024 | [uint32](GFF-File-Format#gff-data-types)         | Most significant plane [bitmask](GFF-File-Format#gff-data-types)                |

The plane [bitmask](GFF-File-Format#gff-data-types) indicates which axis plane is used for tree splitting:

- `0x01` = Positive X
- `0x02` = Positive Y
- `0x04` = Positive Z
- `0x08` = Negative X
- `0x10` = Negative Y
- `0x20` = Negative Z

**Reference**: [`vendor/xoreos-docs/specs/torlack/binmdl.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/binmdl.html) - [AABB](BWM-File-Format#aabb-tree) [node](MDL-MDX-File-Format#node-structures) [structure](GFF-File-Format#file-structure-overview)

---

## ASCII [MDL](MDL-MDX-File-Format) [format](GFF-File-Format)

KotOR [models](MDL-MDX-File-Format) can be represented in an ASCII [format](GFF-File-Format), which is human-readable.

### [model](MDL-MDX-File-Format) [header](GFF-File-Format#file-header) Section

```plaintext
newmodel <model_name>
setsupermodel <model_name> <supermodel_name>
classification <classification_flags>
ignorefog <0_or_1>
setanimationscale <scale_factor>
```

### [geometry](MDL-MDX-File-Format#geometry-header) Section

```plaintext
beginmodelgeom <model_name>
  bmin <x> <y> <z>
  bmax <x> <y> <z>
  radius <value>
```

### [node](MDL-MDX-File-Format#node-structures) Definitions

```plaintext
node <node_type> <node_name>
  parent <parent_name>
  position <x> <y> <z>
  orientation <x> <y> <z> <w>
  scale <value>
  <additional_properties>
endnode
```

### [animation](MDL-MDX-File-Format#animation-header) [data](GFF-File-Format#file-structure-overview)

```plaintext
newanim <animation_name> <model_name>
  length <duration>
  transtime <transition_time>
  animroot <root_node>
  event <time> <event_name>
  node <node_type> <node_name>
    parent <parent_name>
    <controllers>
  endnode
doneanim <animation_name> <model_name>
```

---

## [controller](MDL-MDX-File-Format#controllers) [data](GFF-File-Format#file-structure-overview) [formats](GFF-File-Format)

### Single [controllers](MDL-MDX-File-Format#controllers)

For constant [values](GFF-File-Format#gff-data-types) that don't change over time:

```plaintext
<controller_name> <value>
```

**Reference**: [`vendor/mdlops/MDLOpsM.pm:3734-3754`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3734-L3754) - Single [controller](MDL-MDX-File-Format#controllers) reading  
**Example**: `position 0.0 1.5 0.0` (static [position](MDL-MDX-File-Format#node-header) at X=0, Y=1.5, Z=0)

### Keyed [controllers](MDL-MDX-File-Format#controllers)

For animated [values](GFF-File-Format#gff-data-types) that change over time:

- **Linear Interpolation**:

  ```plaintext
  <controller_name>key
    <time> <value>
    ...
  endlist
  ```

  **Reference**: [`vendor/mdlops/MDLOpsM.pm:3760-3802`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3760-L3802) - Keyed [controller](MDL-MDX-File-Format#controllers) reading  
  **Example**:

  ```plaintext
  positionkey
    0.0 0.0 0.0 0.0
    1.0 0.0 1.0 0.0
    2.0 0.0 0.0 0.0
  endlist
  ```

  Linear interpolation between [keyframes](MDL-MDX-File-Format#controller-structure).

- **Bezier Interpolation**:

  **Reference**: [`vendor/mdlops/MDLOpsM.pm:1704-1710, 1721-1756`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1704-L1756) - Bezier [flag](GFF-File-Format#gff-data-types) detection and [data](GFF-File-Format#file-structure-overview) reading  
  **[format](GFF-File-Format)**: Each [keyframe](MDL-MDX-File-Format#controller-structure) stores 3 [values](GFF-File-Format#gff-data-types) per column: ([value](GFF-File-Format#gff-data-types), in_tangent, out_tangent)

  ```plaintext
  <controller_name>bezierkey
    <time> <value> <in_tangent> <out_tangent>
    ...
  endlist
  ```

  **Example**:

  ```plaintext
  positionbezierkey
    0.0 0.0 0.0 0.0  0.0 0.3 0.0  0.0 0.3 0.0
    1.0 0.0 1.0 0.0  0.0 0.7 0.0  0.0 0.7 0.0
  endlist
  ```
  
  **Binary Storage**: Bezier [controllers](MDL-MDX-File-Format#controllers) use [bit](GFF-File-Format#gff-data-types) 4 ([value](GFF-File-Format#gff-data-types) 0x10) in the column [count](GFF-File-Format#file-structure-overview) [field](GFF-File-Format#file-structure-overview) to indicate bezier interpolation ([mdlops:1704-1710](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1704-L1710)). When this [flag](GFF-File-Format#gff-data-types) is set, the [data](GFF-File-Format#file-structure-overview) section contains 3 times as many floats per keyframe ([mdlops:1721-1723](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1721-L1723)).
  
  **Interpolation**: Bezier curves provide smooth, non-linear interpolation between [keyframes](MDL-MDX-File-Format#controller-structure) using control points (tangents) that define the curve shape entering and leaving each [keyframe](MDL-MDX-File-Format#controller-structure).

### Special [controller](MDL-MDX-File-Format#controllers) Cases

1. **Compressed [quaternion](MDL-MDX-File-Format#node-header) [orientation](MDL-MDX-File-Format#node-header)** (`MDLControllerType.ORIENTATION` with column_count=2):

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:1714-1719`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1714-L1719) - Compressed [quaternion](MDL-MDX-File-Format#node-header) detection  
   **[format](GFF-File-Format)**: Single 32-[bit](GFF-File-Format#gff-data-types) packed [value](GFF-File-Format#gff-data-types) instead of 4 floats

   ```python
   X: bits 0-10  (11 bits, bitmask 0x7FF, effective range [0, 1023] maps to [-1, 1])
   Y: bits 11-21 (11 bits, bitmask 0x7FF, effective range [0, 1023] maps to [-1, 1])
   Z: bits 22-31 (10 bits, bitmask 0x3FF, effective range [0, 511] maps to [-1, 1])
   W: computed from unit constraint (|q| = 1)
   ```

   Decompression: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:850-868`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L850-L868)
   **Decompression**: Extract [bits](GFF-File-Format#gff-data-types) using [bitmasks](GFF-File-Format#gff-data-types), divide by effective range (1023 for X/Y, 511 for Z), then subtract 1.0 to map to [-1, 1] range.

2. **[position](MDL-MDX-File-Format#node-header) Delta Encoding** (ASCII only):

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:3788-3793`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3788-L3793)  
   In ASCII [format](GFF-File-Format) [animations](MDL-MDX-File-Format#animation-header), [position](MDL-MDX-File-Format#node-header) [controller](MDL-MDX-File-Format#controllers) [values](GFF-File-Format#gff-data-types) [ARE](GFF-File-Format#are-area) stored as deltas from the [geometry](MDL-MDX-File-Format#geometry-header) [node](MDL-MDX-File-Format#node-structures)'s static [position](MDL-MDX-File-Format#node-header).

   ```python
   animated_position = geometry_position + position_controller_value
   ```

3. **Angle-Axis to [quaternion](MDL-MDX-File-Format#node-header) Conversion** (ASCII only):

   **Reference**: [`vendor/mdlops/MDLOpsM.pm:3718-3728, 3787`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L3718-L3787)  
   ASCII [orientation](MDL-MDX-File-Format#node-header) [controllers](MDL-MDX-File-Format#controllers) use angle-axis representation `[x, y, z, angle]` which is converted to [quaternion](MDL-MDX-File-Format#node-header) `[x, y, z, w]` on import:

   ```c
   sin_a = sin(angle / 2);
   quat.x = axis.x * sin_a;
   quat.y = axis.y * sin_a;
   quat.z = axis.z * sin_a;
   quat.w = cos(angle / 2);
   ```

---

## Skin [meshes](MDL-MDX-File-Format#trimesh-header) and Skeletal [animation](MDL-MDX-File-Format#animation-header)

### Bone Mapping and Lookup Tables

Skinned [meshes](MDL-MDX-File-Format#trimesh-header) require bone mapping to connect [mesh](MDL-MDX-File-Format#trimesh-header) [vertices](MDL-MDX-File-Format#vertex-structure) to skeleton bones across [model](MDL-MDX-File-Format) parts.

**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L703-L723) - `prepareSkinMeshes()` bone lookup preparation  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:517-522`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L517-L522) - Bone map to [node](MDL-MDX-File-Format#node-structures) mapping

#### Bone Map (`bonemap`)

Maps local bone indices (0-15) to global skeleton bone numbers. Each skinned [mesh](MDL-MDX-File-Format#trimesh-header) part can reference different bones from the full character skeleton.

**Example**: Body part might use bones 0-10, while head uses bones 5-15. The bone map translates local [indices](2DA-File-Format#row-labels) to the correct skeleton bones.

**Reference**: [`vendor/mdlops/MDLOpsM.pm:1518`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1518) - Bone map processing for skin [nodes](MDL-MDX-File-Format#node-structures)  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:276`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L276) - Bone map [array](2DA-File-Format) reading  
**Reference**: [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:509-516`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L509-L516) - Bone map reading with Xbox platform handling

#### Bone Serial and [node](MDL-MDX-File-Format#node-structures) Number Lookups

After loading, bone lookup tables must be prepared for efficient [matrix](BWM-File-Format#vertex-data-processing) computation:

```python
def prepare_bone_lookups(skin_mesh, all_nodes):
    for local_idx, bone_idx in enumerate(skin_mesh.bonemap):
        # Skip invalid bone slots (0xFFFF)
        if bone_idx == 0xFFFF:
            continue
        
        # Ensure lookup arrays are large enough
        if bone_idx >= len(skin_mesh.bone_serial):
            skin_mesh.bone_serial.extend([0] * (bone_idx + 1 - len(skin_mesh.bone_serial)))
            skin_mesh.bone_node_number.extend([0] * (bone_idx + 1 - len(skin_mesh.bone_node_number)))
        
        # Store serial position and node number
        bone_node = all_nodes[local_idx]
        skin_mesh.bone_serial[bone_idx] = local_idx
        skin_mesh.bone_node_number[bone_idx] = bone_node.node_id
```

### [vertex](MDL-MDX-File-Format#vertex-structure) Skinning

Each [vertex](MDL-MDX-File-Format#vertex-structure) can be influenced by up to 4 bones with normalized weights.

**References**:

- [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-268`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L261-L268) - Bone weight/[index](2DA-File-Format#row-labels) reading
- [`vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-485`](https://github.com/th3w1zard1/kotorblender/blob/master/io_scene_kotor/format/mdl/reader.py#L478-L485) - Skinning [data](GFF-File-Format#file-structure-overview) [structure](GFF-File-Format#file-structure-overview)

#### Bone Weight Format ([MDX](MDL-MDX-File-Format))

Per-[vertex](MDL-MDX-File-Format#vertex-structure) [data](GFF-File-Format#file-structure-overview) stored in [MDX files](MDX-Data-Format):

- 4 bone indices (as floats, cast to int)
- 4 bone weights (as floats, should sum to 1.0)

**Layout**:

```plaintext
Offset   Type        Description
+0       float[4]    Bone indices (cast to uint16)
+16      float[4]    Bone weights (normalized to sum to 1.0)
```

**Reference**: [`vendor/mdlops/MDLOpsM.pm:2374-2395`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L2374-L2395) - Bone weight and [index](2DA-File-Format#row-labels) reading from [MDX](MDL-MDX-File-Format)  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:266-267`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L266-L267) - Bone weight and [index](2DA-File-Format#row-labels) [offset](GFF-File-Format#file-structure-overview) reading

#### [vertex](MDL-MDX-File-Format#vertex-structure) [transformation](BWM-File-Format#vertex-data-processing)

```c
// For each vertex
vec3 skinned_position = vec3(0.0);
vec3 skinned_normal = vec3(0.0);

for (int i = 0; i < 4; i++) {
    if (vertex.bone_weights[i] > 0.0) {
        int bone_idx = vertex.bone_indices[i];
        mat4 bone_matrix = getBoneMatrix(bone_idx);
        
        skinned_position += bone_matrix * vec4(vertex.position, 1.0) * vertex.bone_weights[i];
        skinned_normal += mat3(bone_matrix) * vertex.normal * vertex.bone_weights[i];
    }
}

// Renormalize skinned normal
skinned_normal = normalize(skinned_normal);
```

### Bind Pose [data](GFF-File-Format#file-structure-overview)

**References**:

- [`vendor/mdlops/MDLOpsM.pm:1760-1768`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1760-L1768) - Bind pose [arrays](2DA-File-Format)
- Skin [mesh](MDL-MDX-File-Format#trimesh-header) stores bind pose transforms for each bone

#### QBones ([quaternion](MDL-MDX-File-Format#node-header) [rotations](MDL-MDX-File-Format#node-header))

[array](2DA-File-Format) of [quaternions](MDL-MDX-File-Format#node-header) representing each bone's bind pose [orientation](MDL-MDX-File-Format#node-header):

```c
struct QBone {
    float x, y, z, w;  // Quaternion components
};
```

**Reference**: [`vendor/mdlops/MDLOpsM.pm:1760-1768`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1760-L1768) - QBones [array](2DA-File-Format) reading  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:277-287`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L277-L287) - QBones reading and bone [matrix](BWM-File-Format#vertex-data-processing) computation

#### TBones (Translation [vectors](GFF-File-Format#gff-data-types))

[array](2DA-File-Format) of Vector3 representing each bone's bind pose [position](MDL-MDX-File-Format#node-header):

```c
struct TBone {
    float x, y, z;  // Position in model space
};
```

**Reference**: [`vendor/mdlops/MDLOpsM.pm:1760-1768`](https://github.com/th3w1zard1/mdlops/blob/master/MDLOpsM.pm#L1760-L1768) - TBones [array](2DA-File-Format) reading  
**Reference**: [`vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:278,285-286`](https://github.com/th3w1zard1/reone/blob/master/src/libs/graphics/format/mdlmdxreader.cpp#L278-L286) - TBones reading and bone [matrix](BWM-File-Format#vertex-data-processing) computation

#### Bone [matrix](BWM-File-Format#vertex-data-processing) Computation

```c
mat4 computeBoneMatrix(int bone_idx, Animation anim, float time) {
    // Get bind pose
    quat q_bind = skin.qbones[bone_idx];
    vec3 t_bind = skin.tbones[bone_idx];
    mat4 inverse_bind = inverse(translate(t_bind) * mat4_cast(q_bind));
    
    // Get current pose from animation
    quat q_current = evaluateQuaternionController(bone_node, anim, time);
    vec3 t_current = evaluatePositionController(bone_node, anim, time);
    mat4 current = translate(t_current) * mat4_cast(q_current);
    
    // Final bone matrix: inverse bind pose * current pose
    return current * inverse_bind;
}
```

**Note**: KotOR uses left-handed [coordinate](GFF-File-Format#are-area) system, ensure proper [matrix](BWM-File-Format#vertex-data-processing) conventions.

---

## Additional References

### Editors

- [MDLEdit](https://deadlystream.com/files/file/1150-mdledit/)
- [MDLOps](https://deadlystream.com/files/file/779-mdlops/)
- [Toolbox Aurora](https://deadlystream.com/topic/3714-toolkaurora/)
- [KotorBlender](https://deadlystream.com/files/file/889-kotorblender/)
- [KOTORmax](https://deadlystream.com/files/file/1151-kotormax/)

### See Also

- [KotOR/TSL Model Format MDL/MDX Technical Details](https://deadlystream.com/topic/4501-kotortsl-model-format-mdlmdx-technical-details/)
- [MDL Info (Archived)](https://web.archive.org/web/20151002081059/https://home.comcast.net/~cchargin/kotor/mdl_info.html)
- [xoreos Model Definitions](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/aurora/model_kotor.h)
- [xoreos Model Implementation](https://github.com/th3w1zard1/xoreos/blob/master/src/graphics/aurora/model_kotor.cpp)
- [KotOR.js MDL Loader](vendor/KotOR.js/src/loaders/MDLLoader.ts) - TypeScript implementation  
- [KotOR Model Documentation](vendor/kotor/docs/mdl.md) - Binary [structure](GFF-File-Format#file-structure-overview) analysis  
- [MDLOps Perl Module](vendor/mdlops/MDLOpsM.pm) - Complete Perl implementation with ASCII and binary [format](GFF-File-Format) support  
- [reone MDL/MDX Reader](vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp) - C++ implementation for game engine  
- [KotorBlender MDL Reader](vendor/kotorblender/io_scene_kotor/format/mdl/reader.py) - Python implementation for Blender import

---

This documentation aims to provide a comprehensive and structured overview of the KotOR [MDL](MDL-MDX-File-Format)/[MDX files](MDL-MDX-File-Format) [format](GFF-File-Format), focusing on the detailed [file](GFF-File-Format) [structure](GFF-File-Format#file-structure-overview) and [data](GFF-File-Format#file-structure-overview) [formats](GFF-File-Format) used within the games.
