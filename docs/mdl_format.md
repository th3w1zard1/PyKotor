# KotOR Model Format

KotOR Models are separated into two separate files (.mdl/.mdx). All
offsets in mdl do not include the first 12 bytes (file
header).

## Table of Contents

- [Layout](#layout)
- [Binary Format](#binary-format)
  - [File Header](#file-header)
  - [Model Header](#model-header)
  - [Geometry Header](#geometry-header)
  - [Names Header](#names-header)
  - [Animation Header](#animation-header)
  - [Event Structure](#event-structure)
  - [Controller Structure](#controller-structure)
  - [Node Header](#node-header)
  - [Trimesh Header](#trimesh-header)
  - [Danglymesh Header](#danglymesh-header)
  - [Skinmesh Header](#skinmesh-header)
  - [Sabermesh Header](#sabermesh-header)
  - [Light Header](#light-header)
  - [Emitter Header](#emitter-header)
  - [Reference Header](#reference-header)
  - [Vertex](#vertex-binary)
  - [Face](#face-binary)
- [Node Types](#node-types)
  - [Node Type Bitmasks](#node-type-bitmasks)
  - [Node Type Combinations](#node-type-combinations)
- [MDX Data Format](#mdx-data-format)
  - [MDX Row Data Bitmap Masks](#mdx-row-data-bitmap-masks)
  - [Skin Mesh Specific Data](#skin-mesh-specific-data)
  - [MDX Data Size by Node Type](#mdx-data-size-by-node-type)
  - [Row Offsets](#row-offsets)
  - [Special Node Data](#special-node-data)
- [Vertex Data Processing](#vertex-binary-data-processing)
  - [Vertex Normal Calculation](#vertex-binary-normal-calculation)
  - [Tangent Space Calculation](#tangent-space-calculation)
  - [World Space Transformation](#world-space-transformation)
  - [Vertex Data Validation](#vertex-binary-data-validation)
- [Model Classifications](#model-classifications)
- [Additional Controller Types](#additional-controller-types)
  - [Light Controllers](#light-controllers)
  - [Emitter Controllers](#emitter-controllers)
- [File Identification](#file-identification)
  - [Binary vs ASCII Format](#binary-vs-ascii-format)
  - [KotOR 1 vs KotOR 2](#kotor-1-vs-kotor-2)
  - [Function Pointers](#function-pointers)
- [Hierarchy](#mdl-hierarchy)
  - [Node Transforms](#node-transforms)
  - [Node Relationships](#node-relationships)
  - [Vertex Processing](#vertex-binary-processing)
- [Smoothing Groups](#smoothing-groups)
- [Node Data Structures](#node-data-structures)
  - [Light Node Data](#light-node-data)
  - [Emitter Node Data](#emitter-node-data)
  - [Emitter Flags](#emitter-flags)
  - [Mesh Node Data](#mesh-node-data)
  - [Special Node Types](#special-node-types)
  - [Node Transformation](#node-transformation)
- [ASCII MDL Format](#ascii-mdl-format)
  - [Model Header Section](#model-header-section)
  - [Geometry Section](#geometry-section)
  - [Node Definitions](#node-definitions)
  - [Animation Data](#animation-data-ascii)
  - [Special Node Properties](#special-node-properties-ascii)
- [Controller Data Formats](#controller-data-formats)
  - [Single Controllers](#single-controllers)
  - [Keyed Controllers](#keyed-controllers)
  - [Special Controller Types](#special-controller-types)
- [Supernode System](#supernode-system)
- [Vector Operations](#vector-operations)
  - [Vector Comparison](#vector-comparison)
  - [Vector Normalization](#vector-normalization)
  - [Angle Computation](#angle-computation)
- [Editors](#editors)
- [See Also](#see-also)

## Layout

- Model Header (Top-level model metadata)
  - Geometry Header (Core model geometry information)
  - Name Header (Model naming and identification)
    - Name Offsets (Detailed name references)
    - Names (Actual name strings)
  - Animations (Animation sequence data)
    - Animation Header (Metadata for animation sequences)
    - Node Animation (Per-node animation details)
    - Animation Event (Specific animation triggers)
  - Nodes (Hierarchical model structure)
    - Node Header (Individual node metadata)
    - Children Offsets (Node hierarchy references)
    - Controllers (Animation and transformation controllers)
      - Controller Data (Specific controller information)
    - Trimesh Header (Triangle mesh data)
      - Vertices (Mesh vertex information)
      - Faces (Mesh face/polygon data)
    - Skinmesh Header (Skinned mesh details)
      - Bonemap (Bone mapping information)
      - QBones (Quaternion bone transformations)
      - TBones (Additional bone transformations)
    - Danglymesh Header (Soft body/cloth simulation data)
      - Constraints (Physics constraint definitions)
    - Lightsaber Header (Specific lightsaber mesh data)
      - Lightsaber Vertices (Unique lightsaber vertex data)
    - Walkmesh AABB Header (Axis-aligned bounding box for walkable areas)
      - AABB Tree Root Node (Root of collision/navigation space)
    - Reference Header (External model reference)
    - Emitter Header (Particle system metadata)
    - Light Header (Lighting information)
      - Flare Sizes (Light flare size data)
      - Flare Positions (Light flare positioning)
      - Flare Colour Shifts (Light flare color variations)
      - Flare Texture Names (Textures used for light flares)

## Binary Format

### File Header {#file-header}

The file header is 12 bytes and appears at the start of both MDL and MDX files:

| Name       | Type     | Offset | Description                                    |
|------------|----------|--------|------------------------------------------------|
| Signature  | UInt32   | 0      | Must be 0, used to validate MDL files         |
| MDL Size   | UInt32   | 4      | Total size of MDL data (excluding header)     |
| MDX Size   | UInt32   | 8      | Total size of corresponding MDX file          |

Note: All offsets in the MDL file are relative to the end of this header (offset 12).

### Model Header {#model-header}

The model header follows immediately after the file header and consists of:

1. Geometry Header (80 bytes)
2. Model Data (88 bytes)

Total size: 168 bytes

| Name                     | Type             | Offset | Description                                |
|-------------------------|------------------|---------|---------------------------------------------|
| Geometry Header         | Structure        | 0      | See Geometry Header section                |
| Model Type              | UInt8            | 80     | Must be 2 for valid models                 |
| Bounding Box Max        | Float[3]         | 116    |                        |
| Radius                  | Float            | 128    |                        |
| Animation Scale         | Float            | 132    |                        |
| Supermodel Name         | Byte[32]         | 136    |                        |

### Geometry Header {#geometry-header}

Size of 80 bytes.

| Name             | Type        | Offset | Description         |
|------------------|-------------|--------|---------------------|
| | Function Pointer | UInt32 | 0=0x00 | **K1** = 4273776=0x413670<br>**K1 Anim** = 4273392=0x4134F0<br>**TSL** = 4285200=0x416310<br>**TSL Anim** = 4284816=0x416190 |
| | Function Pointer | UInt32 | 4=0x04 | **K1** = 4216096=0x405520<br>**K1 Anim** = 4451552=0x41ECE0<br>**TSL** = 4216320=0x405600<br>**TSL Anim** = 4522928=0x4503B0 |
| | Model Name       | Byte[32]    | 8=0x08  | Name of the model |
| | Root Node Offset | UInt32      | 40=0x28 | Offset to the root node |
| | Node Count       | UInt32      | 44=0x2C | Total number of nodes |
| | Unknown          | UInt32[7]   | 48=0x30 | Reserved/padding |
| | Geometry Type    | Byte        | 76=0x4C | 0x02 = **Root Node**<br>0x05 = **Animation Node** |
| | Padding          | Byte[3]     | 77=0x4D | Alignment padding |

### Names Header {#names-header}

| Name                  | Type     | Description     |
|-----------------------|----------|-----------------|
| Offset To Root Node   | UInt32   |                |
| Unused                | UInt32   |                |
| MDX File Size         | UInt32   |                |
| MDX Offset            | UInt32   |                |
| Names Array Offset    | UInt32   |                |
| Names Count           | UInt32   |                |
| Names Count           | UInt32   | *duplicate*    |

### Animation Header {#animation-header}

| Name              | Type            | Description   |
|-------------------|-----------------|---------------|
| Geometry Header   | Structure       |               |
| Animation Length  | Float           |               |
| Transition Time   | Float           |               |
| Animation Root    | Byte[32=0x20]   |               |
| Event Offset      | UInt32          |               |
| Event Count       | UInt32          |               |
| Event Count       | UInt32          | *duplicate*   |
| Unknown           | UInt32          |               |

### Event Structure {#event-structure}

| Name             | Type    | Description   |
|------------------|---------|---------------|
| Activation Time  | Float   |               |
| Event Name       | String  |               |

### Controller Structure {#controller-structure}

Each Controller is 16 bytes in size.

| Name               | Type     | Description                                       |
|--------------------|----------|---------------------------------------------------|
| Type               | UInt32   | **Header Types**:                                 |
|                    |          | - Position (0x08= 8)                              |
|                    |          | - Orientation (0x14=20)                           |
|                    |          | - Scale (0x24=36)                                 |
|                    |          | **Mesh Types**:                                   |
|                    |          | - Self Illum Color (0x64=100)                     |
|                    |          | - Alpha (0x84=132)                                |
|                    |          | **Light Types**:                                  |
|                    |          | - Color (0x4C=76)                                 |
|                    |          | - Radius (0x58=88)                                |
|                    |          | - Shadow Radius (0x60=96)                         |
|                    |          | - Vertical Displacement (0x64=100)                |
|                    |          | - Multiplier (0x8C=140)                           |
|                    |          | **Emitter**: See Emitter Controller Types section |
| Unknown            | UInt16   | Always 0xFFFF                                     |
| Data Row Count     | UInt16   |                                                   |
| First Key Offset   | UInt16   |                                                   |
| First Data Offset  | UInt16   |                                                   |
| Column Count       | Byte     |                                                   |
| Unknown            | Byte[3]  | Padding, so that struct is 4-byte aligned         |

Each row is a new time key containing the values for the data stored in
the columns.

### Node Header {#node-header}

Size is 80 bytes.

| Name                   | Type       | Offset    | Description            |
|------------------------|------------|-----------|------------------------|
| Node Type              | UInt16     | 0=0x00    | Bitmask for what data  |
|                        |            |           | the node contains.     |
|                        |            |           | 1 = 0x1 = Header<br>2 = 0x2 = Light<br>4  = 0x4 = Emitter<br>8 = 0x8 = Camera<br>16 = 0x10 = Reference<br>32 = 0x20 = Mesh<br>64 = 0x40 = Skin<br>128 = 0x80 = Animation<br>256 = 0x100 = Danglymesh<br>512 = 0x200 = AABB<br>1024 = 0x400 = Walkmesh<br>2048 = 0x800 = Saber<br>           |
| Index Number           | UInt16     | 2=0x02    |                        |
| Node Number            | UInt16     | 4=0x04    |                        |
| Padding                | UInt16     | 6=0x06    |                        |
| Root Node Offset       | UInt32     | 8=0x08    |                        |
| Parent Node Offset     | UInt32     | 12=0xC    |                        |
| Position               | Float[3]   | 16=0x10   |                        |
| Rotation               | Float[4]   | 28=0x1C   |                        |
| Child Array Offset     | UInt32     | 44=0x2C   | Array contains offsets |
|                        |            |           | to child nodes         |
| Child Count            | UInt32     | 48=0x30   |                        |
| Child Count            | UInt32     | 52=0x34   | *duplicate*            |
| Controller Array       | UInt32     | 56=0x38   |                        |
| Offset                 |            |           |                        |
| Controller Count       | UInt32     | 60=0x3C   |                        |
| Controller Count       | UInt32     | 64=0x40   | *duplicate*            |
| Controller Data Offset | UInt32     | 68=0x44   |                        |
| Controller Data Count  | UInt32     | 72=0x48   |                        |
| Controller Data Count  | UInt32     | 76=0x4C   | *duplicate*            |

### Trimesh Header {#trimesh-header}

Size is 332 bytes for KotOR 1 models, 340 bytes for KotOR 2 models.

| Name | Type | Offset | Description |
|------|------|--------|-------------|
| Function Pointer | UInt32 | 0=0x00 | **K1** = 4216656 = 0x405750<br>**K1 Skin** = 4216592 = 0x405710<br>**K1 Dangly** = 4216640 = 0x405740<br>**TSL** = 4216880 = 0x405830<br>**TSL Skin** = 4216816 = 0x4057f0<br>**TSL Dangly** = 4216864 = 0x405820|
| Function Pointer | UInt32 | 4=0x04 | **K1** = 4216672 = 0x405760<br>**K1 Skin** = 4216608 = 0x405720<br>**K1 Dangly** = 4216624 = 0x405730<br>**TSL** = 4216896 = 0x405840<br>**TSL Skin** = 4216832 = 0x405800 <br>**TSL Dangly** = 4216848 = 0x405810 |
| Faces Offset | UInt32 | 8=0x08 | Offset to faces data |
| Faces Count | UInt32 | 12=0x0C | Number of faces |
| Faces Count (duplicate) | UInt32 | 16=0x10 | Duplicate of faces count |
| Bounding Box Min | Float[3] | 20=0x14 | Minimum coordinates of bounding box |
| Bounding Box Max | Float[3] | 32=0x20 | Maximum coordinates of bounding box |
| Radius | Float | 44=0x2C | Bounding sphere radius |
| Average Point | Float[3] | 48=0x30 | Average point of the mesh |
| Diffuse Colour | Float[3] | 60=0x3C | RGB diffuse color (0.0 - 1.0 range) |
| Ambient Colour | Float[3] | 72=0x48 | RGB ambient color (0.0 - 1.0 range) |
| Transparency Hint | UInt32 | 84=0x54 | Transparency information |
| Texture Name | Byte[32] | 88=0x58 | Name of the texture |
| Lightmap Name | Byte[32] | 120=0x78 | Name of the lightmap |
| Unknown | Byte[24] | 152=0x98 | Unidentified data |
| Vertex Indices Count Array Offset | UInt32 | 176=0xB0 | Offset to vertex indices count array |
| Vertex Indices Count Array Count | UInt32 | 180=0xB4 | Count of vertex indices arrays |
| Vertex Indices Count (duplicate) | UInt32 | 184=0xB8 | Duplicate of vertex indices count |
| Vertex Offsets Array Offset | UInt32 | 188=0xBC | Offset to vertex offsets array |
| Vertex Offsets Array Count | UInt32 | 192=0xC0 | Count of vertex offsets arrays |
| Vertex Offsets Array (duplicate) | UInt32 | 196=0xC4 | Duplicate of vertex offsets array count |
| Inverted Counters Array Offset | UInt32 | 200=0xC8 | Offset to inverted counters array |
| Inverted Counters Array Count | UInt32 | 204=0xCC | Count of inverted counters |
| Inverted Counters (duplicate) | UInt32 | 208=0xD0 | Duplicate of inverted counters count |
| Unknown | UInt32[3] | 212=0xD4 | Constant values { -1, -1, 0 } |
| Saber Values | Byte[8] | 224=0xD8 | Values for saber meshes, typically { 3, 0, 0, 0, 0, 0, 0, 0 } |
| Unknown | UInt32 | 232=0xD8 | Unidentified data |
  | Unknown | Float[4] | 236=0xDC | Possibly UV direction, jitter, and jitter speed                                   |
| MDX Data Size | UInt32 | 252=0xE8 | Size of individual vertex data                                                |
| MDX Data Bitmap | UInt32 | 256=0xEC | Bitmask for vertex data types:<br>Vertices = 1 (0x01)<br>Diffusemap = 2 (0x02)<br>Lightmap = 3 (0x03)<br>Normals = 32 (0x20)<br>Bumpmap = 128 (0x80) |
| MDX Vertices Offset        | UInt32 | 260=0xF4       | 0 for most meshes, 0xFFFFFFFF for lightsabers or no vertices |
| MDX Vertices Offset (duplicate) | UInt32 |  260=0xF4 | Duplicate of vertices offset                                 |
| MDX Normals Offset         | UInt32 | 264=0xF8       | Offset to normals data                                       |
| MDX Vertex Colors Offset   | UInt32 | 268=0xFC       | Offset to vertex colors                                      |
| MDX Texture 1 UVs Offset   | UInt32 | 272=0x100      | Offset to first texture UV coordinates                       |
| MDX Lightmap UVs Offset    | UInt32 | 276=0x104      | Offset to lightmap UV coordinates                            |
| MDX Texture 2 UVs Offset   | UInt32 | 280=0x108      | Offset to second texture UV coordinates                      |
| MDX Texture 3 UVs Offset   | UInt32 | 284=0x10C      | Offset to third texture UV coordinates                       |
| ***MDX Unknown Offset 1*** | UInt32 | 288=0x110      | *Contains bumpmap data*                                      |
| ***MDX Unknown Offset 2*** | UInt32 | 292=0x114      |                                                              |
| ***MDX Unknown Offset 3*** | UInt32 | 296=0x118      |                                                              |
| ***MDX Unknown Offset 4*** | UInt32 | 300=0x11C      |                                                              |
| Vertex Count               | UInt16 | 304=0x120      | Number of vertices                                           |
| Texture Count              | UInt16 | 306=0x122      | Number of textures                                           |
| Has Lightmap               | Byte   | 308=0x124      | Flag indicating presence of lightmap                         |
| Rotate Texture             | Byte   | 309=0x125      | Flag for texture rotation                                    |
| Background Geometry       | Byte   | 310=0x126       | Background geometry flag                                     |
| Has Shadow                 | Byte   | 311=0x127      | Shadow presence flag                                         |
| Beaming                   | Byte   | 312=0x128       | Beaming flag                                                 |
| Has Render                | Byte   | 313=0x129       | Render flag                                                  |
| Unknown Flag              | Byte   | 314=0x12A       | Possible UV animation flag                                   |
| Unknown                   | Byte   | 315=0x12B       | Unidentified byte                                            |
| Total Area                | Float  | 316=0x12C       | Total area of the mesh                                       |
| Unknown                   | UInt32 | 320=0x130       | Unidentified data                                            |
| **Unknown 1**             | UInt32 | 324=0x134       | Only present in Kotor 2 Models                               |
| **Unknown 2**             | UInt32 | 328=0x138       | Only present in Kotor 2 Models                               |
| MDX Data Offset           | UInt32 | 324 / 332=0x13C | Offset to MDX data                                           |
| Vertices Offset           | UInt32 | 328 / 336=0x140 | Offset to vertices                                           |

### Danglymesh Header {#danglymesh-header}

Total size is 28 bytes

| Name                    | Type     | Offset    | Description |
|-------------------------|----------|-----------|-------------|
| Offset To Constraints   | UInt32   | 0=0x00    |             |
| Constraints Count       | UInt32   | 4=0x04    |             |
| Constraints Count       | UInt32   | 8=0x08    |             |
| Displacement            | Float    | 12=0x0C   |             |
| Tightness               | Float    | 16=0x10   |             |
| Period                  | Float    | 20=0x14   |             |
| Unknown                 | UInt32   | 24=0x18   |             |

### Skinmesh Header {#skinmesh-header}

Total size is 108 bytes

| Name                                      | Type           |  Offset   | Description |
| ----------------------------------------- | -------------- | --------- | ----------- |
| Compile Weight Array                      | Int[3]         | 0         |             |
| Offset To MDX Skin Weights                | UInt32         | 12=0x0C |             |
| Offset To MDX Skin Bone Refence Indexes   | UInt32         | 16=0x10 |             |
| Offset To Bones Map                       | UInt32         | 20=0x14 |             |
| Bones Map Count                           | UInt32         | 24=0x18 |             |
|                                           | UInt32         | 28=0x1C | QBones      |
|                                           | UInt32         | 32=0x20 |             |
|                                           | UInt32         | 36=0x24 |             |
|                                           | UInt32         | 40=0x28 | TBones      |
|                                           | UInt32         | 44=0x2C |             |
|                                           | UInt32         | 48=0x30 |             |
|                                           | UInt32         | 52=0x34 | ?           |
|                                           | UInt32         | 56=0x38 |             |
|                                           | UInt32         | 60=0x3C |             |
|                                           | UInt16[17]     | 64=0x40 |             |
| Padding                                   | UInt16         | 98=0x62 |             |

### Sabermesh Header {#sabermesh-header}

Total size is 20 bytes

| Name                  | Type     |  Offset  | Description |
|---------------------- | -------- | -------- | ----------- |
| Offset To Vertices    | UInt32   | 0=0x00   |             |
| Offset To TexCoords   | UInt32   | 4=0x04   |             |
| Offset To Normals     | UInt32   | 8=0x08   |             |
| *Unknown*               | UInt32   | 12=0x0C  |             |
| *Unknown*               | UInt32   | 16=0x10  |             |

### Light Header {#light-header}

| Name                         | Type     | Offset  | Description |
|----------------------------- | -------- | ------  | ----------- |
| *Unknown Array*              | UInt32   | 0=0x00  |             |
| *Unknown Array Count*        | UInt32   | 4=0x04  |             |
| *Unknown Array Count*        | UInt32   | 8=0x08  | *duplicate* |
| Lens Flare Sizes Offset      | UInt32   | 12=0x0C |             |
| Lens Flare Sizes Count       | UInt32   | 16=0x10 |             |
| Lens Flare Sizes Count       | UInt32   | 20=0x14 | *duplicate* |
| Flare Positions Offset       | UInt32   | 24=0x18 |             |
| Flare Positions Count        | UInt32   | 28=0x1C |             |
| Flare Positions Count        | UInt32   | 32=0x20 | *duplicate* |
| Flare Color Shifts Offset    | UInt32   | 36=0x24 |             |
| Flare Color Shifts Count     | UInt32   | 40=0x28 |             |
| Flare Color Shifts Count     | UInt32   | 44=0x2C | *duplicate* |
| Flare Texture Names Offset   | UInt32   | 48=0x30 |             |
| Flare Texture Names Count    | UInt32   | 52=0x34 |             |
| Flare Texture Names Count    | UInt32   | 56=0x38 | *duplicate* |
| Flare Radius                 | Float    | 60=0x3C |             |
| Light Priority               | UInt32   | 64=0x40 |             |
| Ambient Only                 | UInt32   | 68=0x44 |             |
| Dynamic Type                 | UInt32   | 72=0x48 |             |
| Affect Dynamic               | UInt32   | 76=0x4C |             |
| Shadow                       | UInt32   | 80=0x50 |             |
| Flare                        | UInt32   | 84=0x54 |             |
| Fading Light                 | UInt32   | 88=0x58 |             |

### Emitter Header {#emitter-header}

| Name                      | Type         | Offset   | Description |
|-------------------------- | ------------ | -------- | ----------- |
| Dead Space                | Float        | 0=0x00   |             |
| Blast Radius              | Float        | 4=0x04   |             |
| Blast Length              | Float        | 8=0x08   |             |
| Branch Count              | UInt32       | 12=0x0C  |             |
| Control Point Smoothing   | Float        | 16=0x10  |             |
| X Grid                    | UInt32       | 20=0x14  |             |
| Y Grid                    | UInt32       | 24=0x18  |             |
| Update                    | Byte[32]     | 28=0x1C  |             |
| Render                    | Byte[32]     | 32=0x20  |             |
| Blend                     | Byte[32]     | 36=0x24  |             |
| Texture                   | Byte[32]     | 40=0x28  |             |
| Chunk Name                | Byte[16]     | 56=0x38  |             |
| Twosided Texture          | UInt32       | 60=0x3C  |             |
| Loop                      | UInt32       | 64=0x40  |             |
| Render Order              | UInt32       | 68=0x44  |             |
| Frame Blending            | UInt32       | 72=0x48  |             |
| Depth Texture Name        | Byte[32]     | 76=0x4C  |             |
| Padding                   | Byte         | 108=0x6C |             |
| Flags                     | UInt32       | 112=0x70 |             |

### Reference Header {#reference-header}

| Name           | Type         | Offset  | Description |
|--------------- | ------------ | ------- | ----------- |
| Model ResRef   | Byte[32]     | 0=0x00  |             |
| Reattachable   | UInt32       | 32=0x20 |             |

### Vertex {#vertex-binary}

| Name   | Type    | Description |
|------- | ------- | ----------- |
| X      | Float   |             |
| Y      | Float   |             |
| Z      | Float   |             |

### Face {#face-binary}

| Name                | Type     | Description |
|-------------------- | -------- | ----------- |
| Normal              | Vertex   |             |
| Plane Coefficient   | Float    |             |
| Material            | UInt32   | *Can be found in `surfacemat.2da`* |
| Face Adjacency 1    | UInt16   |             |
| Face Adjacency 2    | Uint16   |             |
| Face Adjacency 3    | UInt16   |             |
| Vertex 1            | UInt16   |             |
| Vertex 2            | UInt16   |             |
| Vertex 3            | UInt16   |             |

## Node Types {#node-types}

### Node Type Bitmasks {#node-type-bitmasks}

Node types in KotOR models are defined using bitmask combinations. Here are the base bitmasks:

```python
class NodeTypeBitmasks(IntEnum):
    NODE_HAS_HEADER    = 1     # 0x001
    NODE_HAS_LIGHT     = 2     # 0x002
    NODE_HAS_EMITTER   = 4     # 0x004
    NODE_HAS_CAMERA    = 8     # 0x008
    NODE_HAS_REFERENCE = 16    # 0x010
    NODE_HAS_MESH      = 32    # 0x020
    NODE_HAS_SKIN      = 64    # 0x040
    NODE_HAS_ANIM      = 128   # 0x080
    NODE_HAS_DANGLY    = 256   # 0x100
    NODE_HAS_AABB      = 512   # 0x200
    NODE_HAS_SABER     = 2048  # 0x800
```

### Node Type Combinations {#node-type-combinations}

Common node types are created by combining these bitmasks:

```python
class NodeTypeCombinations(IntEnum):
    DUMMY       = NODE_HAS_HEADER                                   = 0x001 = 1
    LIGHT       = NODE_HAS_HEADER + NODE_HAS_LIGHT                  = 0x003 = 3
    EMITTER     = NODE_HAS_HEADER + NODE_HAS_EMITTER                = 0x005 = 5
    REFERENCE   = NODE_HAS_HEADER + NODE_HAS_REFERENCE              = 0x011 = 17
    MESH        = NODE_HAS_HEADER + NODE_HAS_MESH                   = 0x021 = 33
    SKIN_MESH   = NODE_HAS_SKIN + NODE_HAS_MESH + NODE_HAS_HEADER   = 0x061 = 97
    ANIM_MESH   = NODE_HAS_ANIM + NODE_HAS_MESH + NODE_HAS_HEADER   = 0x0A1 = 161
    DANGLY_MESH = NODE_HAS_DANGLY + NODE_HAS_MESH + NODE_HAS_HEADER = 0x121 = 289
    AABB_MESH   = NODE_HAS_AABB + NODE_HAS_MESH + NODE_HAS_HEADER   = 0x221 = 545
    SABER_MESH  = NODE_HAS_SABER + NODE_HAS_MESH + NODE_HAS_HEADER  = 0x821 = 2081
```

## MDX Data Format {#mdx-data-format}

The MDX file contains additional mesh data that complements the MDL file. The data is organized in rows with specific bit flags indicating presence of different data types.

### MDX Row Data Bitmap Masks {#mdx-row-data-bitmap-masks}

The common mesh header contains offsets for 11 different potential row fields. Here are the identified fields:

| Field Name     | Hex Value | Decimal Value | Description |
|----------------|-----------|---------------|-------------|
| VERTICES       | 0x01      | 1            | Vertex coordinates |
| TEX0_VERTICES  | 0x02      | 2            | Primary texture coordinates |
| TEX1_VERTICES  | 0x04      | 4            | Secondary texture coordinates |
| TEX2_VERTICES  | 0x08      | 8            | Tertiary texture coordinates (unconfirmed) |
| TEX3_VERTICES  | 0x10      | 16           | Quaternary texture coordinates (unconfirmed) |
| VERTEX_NORMALS | 0x20      | 32           | Vertex normal vectors |
| VERTEX_COLORS  | 0x40      | 64           | Vertex colors (unconfirmed) |
| TANGENT_SPACE  | 0x80      | 128          | Tangent space data |

### Skin Mesh Specific Data {#skin-mesh-specific-data}

Additional MDX data specific to skin meshes:

| Field Name      | Hex Value | Decimal Value | Description |
|-----------------|-----------|---------------|-------------|
| BONE_WEIGHTS    | 0x0800    | 2048         | Bone weights for vertex skinning |
| BONE_INDICES    | 0x1000    | 4096         | Bone indices for vertex skinning |

### MDX Data Size by Node Type {#mdx-data-size-by-node-type}

- Skin Mesh: 64 bytes base size
- Dangly Mesh: 32 bytes base size
- Basic Mesh: 24 bytes base size (without texture mapping)

### Row Offsets {#row-offsets}

Each node's MDX data contains offsets to different data types:

| Offset Index | Name | Description |
|-------------|------|-------------|
| 0 | Vertex Offset | Offset to vertex coordinates |
| 1 | Normal Offset | Offset to vertex normals |
| 2 | Color Offset | Offset to vertex colors |
| 3 | Tex0 Offset | Offset to primary texture coordinates |
| 4 | Tex1 Offset | Offset to secondary texture coordinates |
| 5 | Tex2 Offset | Offset to tertiary texture coordinates |
| 6 | Tex3 Offset | Offset to quaternary texture coordinates |
| 7 | Tangent Offset | Offset to tangent space data |
| 8 | Reserved1 | Reserved for future use |
| 9 | Reserved2 | Reserved for future use |
| 10 | Reserved3 | Reserved for future use |

Note: Value of -1 indicates data type is not present.

### Special Node Data {#special-node-data}

#### Skin Mesh Additional Data {#skin-mesh-additional-data}

| Name | Description |
|------|-------------|
| MDX Bone Weights Offset | Offset to bone weights data (4 x 4-byte floats per vertex) |
| MDX Bone Indices Offset | Offset to bone indices data (4 x 4-byte floats per vertex) |

## Vertex Data Processing {#vertex-binary-data-processing}

### Vertex Normal Calculation {#vertex-binary-normal-calculation}

Vertex normals are computed using:

1. Face normals from connected faces
2. Optional area weighting
3. Optional angle weighting
4. Optional crease angle limiting

#### Area Weighting {#area-weighting}

Face contribution is weighted by triangle area:

```python
area = length(cross(edge1, edge2)) / 2
weighted_normal = face_normal * area
```

#### Angle Weighting {#angle-weighting}

Face contribution is weighted by vertex angle:

```python
angle = arccos(dot(normalize(v1 - v0), normalize(v2 - v0)))
weighted_normal = face_normal * angle
```

#### Crease Angle Limiting {#crease-angle-limiting}

Faces are excluded if angle between normals exceeds threshold:

```python
default_crease_angle = 60° (π/3 radians)
if angle_between_normals > crease_angle:
    skip_face
```

### Tangent Space Calculation {#tangent-space-calculation}

For normal-mapped meshes:

1. Face Tangent/Bitangent:

    ```python
    deltaPos1 = v1 - v0
    deltaPos2 = v2 - v0
    deltaUV1 = uv1 - uv0
    deltaUV2 = uv2 - uv0

    r = 1.0 / (deltaUV1.x *deltaUV2.y - deltaUV1.y* deltaUV2.x)

    tangent = normalize(
        (deltaPos1 *deltaUV2.y - deltaPos2* deltaUV1.y) * r
    )

    bitangent = normalize(
        (deltaPos2 *deltaUV1.x - deltaPos1* deltaUV2.x) * r
    )
    ```

2. Handedness Correction:

    ```python
    if dot(cross(normal, tangent), bitangent) > 0:
        tangent = -tangent

    if texture_mirrored:
        tangent = -tangent
        bitangent = -bitangent
    ```

3. Vertex Tangent Space:
  Average of connected face tangents/bitangents using same weighting as normals.

### World Space Transformation {#world-space-transformation}

Vertex data can be transformed to world space using node hierarchy:

```python
world_pos = parent_transform *(node_rotation* vertex_pos + node_position)
world_normal = parent_rotation *node_rotation* normal
```

### Vertex Data Validation {#vertex-binary-data-validation}

When processing vertex data:

1. Vertices are uniquified based on position and attributes
2. Vertices are split if:
   - Different UV coordinates
   - Different vertex colors
   - Different bone weights
   - Different smooth groups
   - Different tangent spaces
3. Vertex indices are remapped to maintain face connectivity

## Model Classifications {#model-classifications}

Models in KotOR can be classified into different types using these flags:

| Model Type | Value | Description |
|------------|-------|-------------|
| OTHER | 0x00 | Default/unspecified model type |
| EFFECT | 0x01 | Visual effects and particles |
| TILE | 0x02 | Terrain and level geometry tiles |
| CHARACTER | 0x04 | NPCs and creatures |
| DOOR | 0x08 | Door models |
| LIGHTSABER | 0x10 | Lightsaber models |
| PLACEABLE | 0x20 | Static objects and props |
| FLYER | 0x40 | Flying vehicles and creatures |

## Additional Controller Types {#additional-controller-types}

### Light Controllers {#light-controllers}

| Controller Type | Value | Description |
|----------------|-------|-------------|
| COLOR | 76 | Light color |
| RADIUS | 88 | Light radius |
| SHADOW_RADIUS | 96 | Shadow casting radius |
| VERTICAL_DISPLACEMENT | 100 | Vertical offset |
| MULTIPLIER | 140 | Light intensity multiplier |

### Emitter Controllers {#emitter-controllers}

| Controller Name | Type | Description |
|----------------|------|-------------|
| ALPHA_END | float | Final alpha value |
| ALPHA_START | float | Initial alpha value |
| BIRTH_RATE | float | Particle spawn rate |
| BOUNCE_CO | float | Bounce coefficient |
| COMBINE_TIME | float | Time to combine particles |
| DRAG | float | Particle drag coefficient |
| FPS | float | Frames per second |
| FRAME_END | float | Ending frame |
| FRAME_START | float | Starting frame |
| GRAVITY | float | Gravity effect on particles |
| LIFE_EXPECTANCY | float | Particle lifetime |
| MASS | float | Particle mass |
| P2P_BEZIER_2 | float | Point-to-point Bezier control 2 |
| P2P_BEZIER_3 | float | Point-to-point Bezier control 3 |
| PARTICLE_ROTATION | float | Particle rotation speed |
| RANDOM_VELOCITY | float | Random velocity factor |
| SIZE_START | float | Initial particle size |
| SIZE_END | float | Final particle size |
| SIZE_START_Y | float | Initial Y-axis size |
| SIZE_END_Y | float | Final Y-axis size |

## File Identification {#file-identification}

### Binary vs ASCII Format {#binary-vs-ascii-format}

The first 4 bytes of an MDL file determine whether it's a binary or ASCII format:

- If the first 4 bytes are all nulls (`00 00 00 00`), it's a binary model
- Otherwise, it's an ASCII model

### KotOR 1 vs KotOR 2 {#kotor-1-vs-kotor-2}

The game version can be determined by reading the first 4 bytes of the geometry header (offset 12):

- If the value is 4285200 = 0x416310, it's a KotOR 2 model
- Otherwise, it's a KotOR 1 model

### Function Pointers {#function-pointers}

The geometry header contains function pointers that also indicate the game version:

KotOR 1:

- Regular model: 4273776 = 0x413670
- Animation model: 4273392 = 0x4134F0
- Secondary pointer: 4216096 = 0x405520, 4451552 = 0x43ECE0

KotOR 2:

- Regular model: 4285200 = 0x416310
- Animation model: 4284816 = 0x416190
- Secondary pointer: 4216320 = 0x405600, 4522928 = 0x4503B0

## Model Hierarchy {#mdl-hierarchy}

### Node Transforms {#node-transforms}

Nodes maintain a transform hierarchy that affects their geometry:

1. Position Transform
   - Stored in controller type 8
   - Accumulates through the node hierarchy
   - Applied as translation after orientation

2. Orientation Transform
   - Stored in controller type 20 (0x14)
   - Combines through the hierarchy using quaternion multiplication
   - Applied before position translation

### Node Relationships {#node-relationships}

- Each node can have a parent node (referenced by `parentnodenum`)
- The model has a root node (referenced in the geometry header)
- Head models are identified when the `node1` value differs from the `rootnode` value

```mdlascii
node <type> <name>
  parent <parent_name>
  # Supernode number is internal, not in ASCII format
  # but determines relationship with supermodel
```

### Vertex Processing {#vertex-binary-processing}

For mesh nodes that are rendered (excluding saber and AABB nodes):

1. Vertex positions are transformed by:
   - Applying the accumulated node orientation (quaternion rotation)
   - Adding the accumulated node position

2. Face normals are calculated using:
   - Three vertices defining the face
   - Cross product of edge vectors
   - Normalized to unit length

3. Vertex normals can be computed using different methods:
   - Area-weighted: Using face surface areas
   - Angle-weighted: Using vertex angles
   - Combined: Using both area and angle weights

## Smoothing Groups {#smoothing-groups}

Models support automatic smoothing group computation based on:

1. Face Connectivity:
   - Faces sharing vertices are grouped
   - Edge boundaries are detected between groups

2. Normal Angles:
   - Faces with similar normals are grouped
   - Angle thresholds determine group boundaries

3. Vertex Welding:
   - Vertices at identical positions can be welded
   - Affects normal calculation and smoothing

## Node Data Structures {#node-data-structures}

### Light Node Data {#light-node-data}

Light nodes (`NODE_LIGHT = 3`) contain the following data:

```mdlascii
flareRadius       # Radius of light flare effect
flareSizes        # Array of flare size values
flarePositions    # Array of flare position values
flareColorShifts  # Array of RGB color shift values
textureNames      # Array of flare texture names
lightPriority     # Light rendering priority
ambientOnly       # Whether light affects ambient only
dynamicType       # Dynamic lighting type
affectDynamic     # Whether affects dynamic objects
shadow            # Shadow casting enabled
flare             # Flare effect enabled
fadingLight       # Light fading enabled
```

### Emitter Node Data {#emitter-node-data}

Emitter nodes (`NODE_EMITTER = 5`) contain particle system properties:

```mdlascii
deadspace          # Dead zone space
blastRadius        # Blast effect radius
blastLength        # Blast effect length
numBranches        # Number of particle branches
controlptsmoothing # Control point smoothing
xgrid, ygrid       # Grid dimensions
spawntype          # Particle spawn type
update             # Update behavior
render             # Render behavior
blend              # Blend mode
texture            # Particle texture
chunkname          # Chunk name for effects
twosidedtex        # Two-sided texture rendering
loop               # Loop animation
renderorder        # Rendering order
frameBlending      # Frame blending enabled
```

### Emitter Flags {#emitter-flags}

Emitter nodes use a bitfield for various flags:

```python
class EmitterFlags(IntFlag):
    P2P_MOVEMENT                  =  0x0001       # Point to point movement
    P2P_SELECTION                 =  0x0002       # Point to point selection 
    AFFECTED_BY_WIND              =  0x0004       # Affected by wind
    TINTED_PARTICLES              =  0x0008       # Tinted particles
    BOUNCE_ENABLED                =  0x0010       # Bounce enabled
    RANDOM_BEHAVIOR               =  0x0020       # Random behavior
    INHERIT_PARENT_PROPERTIES     =  0x0040       # Inherit parent properties
    INHERIT_VELOCITY              =  0x0080       # Inherit velocity
    INHERIT_LOCAL_SPACE           =  0x0100       # Inherit local space
    SPLAT_EFFECT                  =  0x0200       # Splat effect
    INHERIT_PARTICLE_PROPERTIES   =  0x0400       # Inherit particle properties
    DEPTH_TEXTURE_ENABLED         =  0x0800       # Depth texture enabled
```

### Mesh Node Data {#mesh-node-data}

Common mesh data for trimesh, skin, dangly, and walkmesh nodes:

```mdlascii
faces          # Face definitions (vertices, normals, UVs)
bboxMin/Max    # Bounding box dimensions
radius         # Mesh radius
average        # Average vertex position
diffuse        # Diffuse color
ambient        # Ambient color
transparency   # Transparency hint
bitmap         # Primary texture
texture0/1     # Additional textures
vertexCount    # Number of vertices
mdxDataSize    # Size of MDX vertex data
mdxDataBitmap  # Vertex data flags
```

### Special Node Types {#special-node-types}  

#### Skin Mesh Node {#skin-mesh-node}

Additional data for skin mesh nodes (`NODE_SKIN = 97`):

```mdlascii
boneWeights    # Vertex bone weights (4 per vertex)
boneIndices    # Vertex bone indices (4 per vertex)
qboneRefInv    # Quaternion bone inverse references
tboneRefInv    # Translation bone inverse references
```

#### Dangly Mesh Node {#dangly-mesh-node}

Additional data for dangly mesh nodes (`NODE_DANGLYMESH = 289 = 0x121`):

```mdlascii
displacement   # Vertex displacement amount
tightness      # Spring tightness
period         # Animation period
constraints    # Vertex movement constraints
```

#### Lightsaber Node {#lightsaber-node}

Special handling for lightsaber nodes (`NODE_SABER = 2081 = 0x821`):

```mdlascii
vertcoords     # Base vertex coordinates
vertcoords2    # Secondary vertex coordinates
tverts         # Texture coordinates
saberVerts     # Lightsaber blade vertices
saberNorms     # Lightsaber blade normals
```

### Node Transformation {#node-transformation}

Nodes maintain transformation data through their hierarchy:

1. Position Data:
   - Stored in controller type 8
   - Accumulates through parent nodes
   - Applied after orientation
   - For animations, values are deltas from initial position

2. Orientation Data:
   - Stored in controller type 20 (0x14)
   - Uses quaternion format (x, y, z, w)
   - Can use compressed format in animations
   - Quaternion compression format:

    ```python
    orientation: tuple[float, float, float, float] = (
      x = (-1.0 + ((bits[0-10] / 2046.0) / 0.5))
      y = (-1.0 + ((bits[11-21] / 2046.0) / 0.5))
      z = (-1.0 + ((bits[22-31] / 1022.0) / 0.5))
      w = sqrt(1 - (x² + y² + z²))
    )
    ```

3. Scale Data:
   - Stored in controller type 36 (0x24)
   - Applied before other transformations

## ASCII MDL Format {#ascii-mdl-format}

KotOR models can be represented in an ASCII text format that is more human-readable than the binary format.

The ASCII format provides a more accessible way to view and edit model data
compared to the binary format, while maintaining all the essential
information needed to represent KotOR models.

The ASCII format follows this hierarchical structure:

### Model Header Section {#model-header-section}

The file begins with model metadata:

```mdlascii
# mdlops version and source info
filedependancy <filename> NULL.mlk
newmodel <model_name>
setsupermodel <model_name> <supermodel_name>  # Optional supermodel reference
classification <type>        # Usually "character", "door", "effect", etc.
classification_unk1 <value> # Unknown classification value, typically 0
ignorefog <0|1>            # Whether model ignores scene fog
setanimationscale <value>  # Animation timing scale factor
compress_quaternions <0|1> # Whether to use compressed quaternions
headlink <0|1>            # For character models with head attachments
```

### Geometry Section {#geometry-section}

The geometry section defines the model's overall bounds:

```mdlascii
beginmodelgeom <model_name>
  bmin <x> <y> <z>       # Minimum bounding box corner
  bmax <x> <y> <z>       # Maximum bounding box corner
  radius <value>         # Bounding sphere radius
```

### Node Definitions {#node-definitions}

Each node in the model hierarchy is defined with:

```mdlascii
node <type> <name>
  parent <parent_name>   # Parent node name, "NULL" for root
  position <x> <y> <z>   # Local position offset
  orientation <x> <y> <z> <w>  # Quaternion orientation
  
  # Optional node properties based on type:
  scale <value>          # Node scale factor
  alpha <value>          # Transparency value
  selfillumcolor <r> <g> <b>  # Self-illumination color
  diffuse <r> <g> <b>    # Diffuse material color
  ambient <r> <g> <b>    # Ambient material color
  transparencyhint <value>  # Transparency rendering hint
  beaming <0|1>          # Special effect flag
  render <0|1>           # Whether node should be rendered
  shadow <0|1>           # Whether node casts shadows
  
  # For mesh nodes:
  bitmap <texture_name>   # Texture filename
  verts <count>          # Number of vertices
    <x> <y> <z>         # Vertex positions
  faces <count>          # Number of faces
    <v1> <v2> <v3> <smoothing_group> <surface_idx> <shader_idx> <material_idx> <flags>
  
  # For skin nodes:
  weights <count>        # Number of vertex weights
    <bone_name> <weight> [<bone_name> <weight>...]  # Bone weights per vertex
endnode
```

Node types include:

- dummy: Empty transform node
- trimesh: Static triangle mesh
- skin: Skinned mesh with bone weights
- saber: Lightsaber mesh
- danglymesh: Physics-enabled mesh
- emitter: Particle system
- light: Light source
- reference: Reference to another model

### Face Data Format {#face-binary-data-format}

Face definitions use the format:

```mdlascii
<vertex1> <vertex2> <vertex3>  <material_id>  <surface_idx> <shader_idx> <material_idx>  <smoothing_group>
```

Where:

- vertex1-3: Indices into vertex list (0-based)
- material_id: Material identifier
- surface_idx: Surface properties index
- shader_idx: Shader properties index
- material_idx: Material properties index
- smoothing_group: Smoothing group ID for normal calculation

### Texture Coordinates {#texture-coordinates}

For textured meshes, UV coordinates are defined after vertices:

```mdlascii
tverts <count>
  <u> <v>    # Texture coordinates per vertex
```

### Skin Weights {#skin-weights}

Skinned meshes include vertex bone weights:

```mdlascii
weights <vertex_count>
  <bone1> <weight1> [<bone2> <weight2>...]  # Space-separated bone/weight pairs
```

Weights must sum to 1.0 per vertex.

### Animation Data {#animation-data}

Animations are defined after the model geometry:

```mdlascii
newanim <animation_name> <model_name>
  length <duration>      # Animation length in seconds
  transtime <value>      # Transition blend time
  animroot <node_name>   # Root node for animation
  
  # Animation events
  event <time> <name>    # Trigger event at timestamp
  
  # Per-node animation data
  node <node_name>
    # Position keyframes
    positionkey <count>
      <time> <x> <y> <z>
    
    # Orientation keyframes  
    orientationkey <count>
      <time> <x> <y> <z> <w>
      
    # Scale keyframes
    scalekey <count>
      <time> <scale>
doneanim
```

### Special Node Properties {#special-node-properties}

Different node types have specific properties:

#### Light Nodes {#light-nodes}

```mdlascii
node light <name>
  ambientonly <0|1>
  shadow <0|1>
  lightpriority <value>
  fadinglight <0|1>
  flare <0|1>
```

#### Emitter Nodes {#emitter-nodes}

```mdlascii
node emitter <name>
  p2p <0|1>              # Point-to-point mode
  render <mode>          # Render mode (normal, linked, etc)
  blend <mode>           # Blend mode
  spawntype <type>       # Particle spawn type
  update <mode>          # Update mode
  render <mode>          # Render mode
  blend <mode>           # Blend mode
  texture <filename>     # Particle texture
  chunkname <name>       # Chunk reference
  twosidedtex <0|1>     # Two-sided texturing
  loop <0|1>            # Loop animation
  renderorder <value>    # Render order priority
```

#### Mesh Nodes {#mesh-nodes}

```mdlascii
node trimesh <name>
  bitmap <texture>       # Diffuse texture
  lightmapped <0|1>     # Use lightmap
  rotatetexture <0|1>   # Rotate texture coordinates
  render <0|1>          # Render enable
  shadow <0|1>          # Cast shadows
  beaming <0|1>         # Use beam effect
  render <0|1>          # Render enable
  transparencyhint <value>  # Transparency mode
```

`

### Animation Data {#animation-data-ascii}

Animations are defined after the model geometry:

```mdlascii
newanim <animation_name> <model_name>
  length <duration>      # Animation length in seconds
  transtime <value>      # Transition blend time
  animroot <node_name>   # Root node for animation
  
  # Animation events
  event <time> <name>    # Trigger event at timestamp
  
  # Per-node animation data
  node <node_name>
    # Position keyframes
    positionkey <count>
      <time> <x> <y> <z>
    
    # Orientation keyframes  
    orientationkey <count>
      <time> <x> <y> <z> <w>
      
    # Scale keyframes
    scalekey <count>
      <time> <scale>
doneanim
```

### Special Node Properties {#special-node-properties-ascii}

Different node types have specific properties:

#### Light Nodes {#light-nodes-ascii}

```mdlascii
node light <name>
  ambientonly <0|1>
  shadow <0|1>
  lightpriority <value>
  fadinglight <0|1>
  flare <0|1>
```

#### Emitter Nodes {#emitter-nodes-ascii}

```mdlascii
node emitter <name>
  p2p <0|1>              # Point-to-point mode
  render <mode>          # Render mode (normal, linked, etc)
  blend <mode>           # Blend mode
  spawntype <type>       # Particle spawn type
  update <mode>          # Update mode
  render <mode>          # Render mode
  blend <mode>           # Blend mode
  texture <filename>     # Particle texture
  chunkname <name>       # Chunk reference
  twosidedtex <0|1>     # Two-sided texturing
  loop <0|1>            # Loop animation
  renderorder <value>    # Render order priority
```

#### Mesh Nodes {#mesh-nodes-ascii}

```mdlascii
node trimesh <name>
  bitmap <texture>       # Diffuse texture
  lightmapped <0|1>     # Use lightmap
  rotatetexture <0|1>   # Rotate texture coordinates
  render <0|1>          # Render enable
  shadow <0|1>          # Cast shadows
  beaming <0|1>         # Use beam effect
  render <0|1>          # Render enable
  transparencyhint <value>  # Transparency mode
```

### Controller Data Formats {#controller-data-formats}

Controllers can be either linear or bezier type. Bezier controllers include
additional control point data for smooth interpolation.

#### Single Controllers {#single-controllers}

Single controllers represent constant values that don't change over time. They are formatted as:

```mdlascii
<controller_name> <value1> <value2> ...
```

#### Keyed Controllers {#keyed-controllers}

Keyed controllers represent animated values that change over time. They can be either linear or bezier interpolation:

```mdlascii
# Linear interpolation
<controller_name>key
  <time> <value1> <value2> ...
endlist

# Bezier interpolation
<controller_name>bezierkey
  <time> <value1> <value2> ... <control_point1> <control_point2> ...
endlist
```

#### Special Controller Types {#special-controller-types}

##### Orientation Controllers {#orientation-controllers}

Orientation data is stored in angle-axis format and converted to quaternions (x, y, z, w) internally:

```mdlascii
orientationkey
  <time> <axis_x> <axis_y> <axis_z> <angle>  # Input format
  # Converted to quaternion: 
  # x = axis_x * sin(angle/2)
  # y = axis_y * sin(angle/2)
  # z = axis_z * sin(angle/2)
  # w = cos(angle/2)
```

##### Position Controllers {#position-controllers}

Position keyframes store deltas from the base geometry position:

```mdlascii
positionkey
  <time> <delta_x> <delta_y> <delta_z>  # Relative to base position
```

## Other information {#other-information}

### Supernode System {#supernode-system}

Models can reference a supermodel, establishing a hierarchical relationship between models. The supernode system maps nodes between the model and its supermodel:

1. Each node in a model is assigned a supernode number
2. Matching nodes between model and supermodel share the same supernode number
3. New nodes get unique supernode numbers

The matching process follows these rules:

- Root nodes are compared first
- Child nodes are matched by name
- If a node has no match in the supermodel:
  - If its parent matched: Assigned next available supernode number
  - If its parent didn't match: Assigned offset number based on total nodes
- Children of unmatched nodes cannot match supermodel nodes

### Vector Operations {#vector-operations}

The ASCII format uses various vector operations for processing model data:

#### Vector Comparison {#vector-comparison}

Vertices and vectors can be compared with configurable precision:

- Two vertices are equal if all components match within tolerance
- tolerance = 5 * 10^(-precision)
- Default precision is 6 decimal places

```mdlascii
# tolerance = 5 * 10^(-precision)
# Default precision is 6 decimal places
```

#### Vector Normalization {#vector-normalization}

Vectors (particularly for normals and orientations) are normalized to unit length:

```mdlascii
# For vector (x, y, z):
magnitude = sqrt(x² + y² + z²)
normalized = (x/magnitude, y/magnitude, z/magnitude)
```

### Angle Computation {#angle-computation}

Angles between vectors (used for vertex normals and orientations) are computed using:

```mdlascii
# For vectors v1 and v2:
dot_product = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z
angle = arccos(dot_product / (|v1| * |v2|))
```

These mathematical operations ensure proper handling of geometric data when converting between binary and ASCII formats.

### Animation Data Compression {#animation-data-compression}

- Orientation keyframes can use compressed quaternions encoded as 3 10-bit floats in a single 32-bit value
- Compression maintains w component positive for engine compatibility
- Compressed format: bits 0-10: x, bits 11-21: y, bits 22-31: z

### Node Type Controller Flags {#node-type-controller-flags}

- Light nodes: Controllers 76 (color), 88 (radius), 140 (multiplier) use flags 255,114,17
- Emitter nodes: Controllers use flags 99,121,17
- Geometry nodes: Position (8) uses 87,73,0; Orientation (20) uses 57,71,0

### MDX Data Padding {#mdx-data-padding}

- Skin mesh MDX data ends with 1e6 terminator values and 16-byte alignment padding
- Regular mesh MDX data ends with 1e7 terminator values and 8-byte alignment padding
- MDX data start offsets are always aligned to 16 bytes (end in 0)

### Walkmesh AABB Trees {#walkmesh-aabb-trees}

Walkmesh collision is accelerated using an AABB (Axis-Aligned Bounding Box) tree. The tree is generated recursively:

1. The faces are sorted along the split axis with the widest bbox dimension (x, y or z)
2. The faces are divided evenly into left and right child nodes
3. Steps 1-2 are repeated for each child node, cycling the split axis, until max depth or <4 faces per node
4. The resulting binary AABB tree is stored in the MDL, with each node containing:
   - Two child node offsets (or face index and count for leaf nodes)
   - Bounding box minimum and maximum extents
   - Split axis bitmap (1=x, 2=y, 4=z)

At runtime, the AABB tree allows efficiently testing if a point or ray intersects the walkmesh by only traversing the tree nodes that the point/ray passes through. This provides significant speedup over brute force testing every face.

## Editors {#editors}

- <https://deadlystream.com/files/file/1150-mdledit/>
- <https://deadlystream.com/files/file/779-mdlops/>
- <https://deadlystream.com/topic/3714-toolkaurora/>
- <https://deadlystream.com/files/file/889-kotorblender/>
- <https://deadlystream.com/files/file/1151-kotormax/>

## See Also {#see-also}

- <https://deadlystream.com/topic/4501-kotortsl-model-format-mdlmdx-technical-details/>
- <https://web.archive.org/web/20151002081059/https://home.comcast.net/~cchargin/kotor/mdl_info.html>
- <https://github.com/xoreos/xoreos/blob/master/src/graphics/aurora/model_kotor.h>
- <https://github.com/xoreos/xoreos/blob/master/src/graphics/aurora/model_kotor.cpp>
