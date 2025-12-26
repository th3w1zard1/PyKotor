# ARE (Area)

Part of the [GFF File Format Documentation](GFF-File-Format).

ARE files define static [area properties](GFF-File-Format#are-area) including lighting, weather, ambient audio, grass rendering, fog settings, script hooks, and minimap data. [ARE](GFF-File-Format#are-area) files contain environmental and atmospheric data for game areas, while dynamic object placement is handled by [GIT](GFF-File-Format#git-game-instance-template) files.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine [ARE](GFF-File-Format#are-area) format specification, see [Bioware Aurora Area File Format](Bioware-Aurora-AreaFile).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/are.py`](https://github.com/OldRepublicDevs/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py)

## Core Identity fields

| field | type | Description |
| ----- | ---- | ----------- |
| `Tag` | [CExoString](GFF-File-Format#gff-data-types) | Unique area identifier |
| `Name` | [CExoLocString](GFF-File-Format#gff-data-types) | Area name (localized) |
| `Comments` | [CExoString](GFF-File-Format#gff-data-types) | Developer notes/documentation |
| `Creator_ID` | DWord | Toolset creator identifier (unused at runtime) |
| `ID` | DWord | Unique area ID (unused at runtime) |
| `Version` | DWord | Area version (unused at runtime) |
| `Flags` | DWord | Area flags (unused in KotOR) |

## Lighting & Sun

| field | type | Description |
| ----- | ---- | ----------- |
| `SunAmbientColor` | color | Ambient light color RGB |
| `SunDiffuseColor` | color | Sun diffuse light color RGB |
| `SunShadows` | Byte | Enable shadow rendering |
| `ShadowOpacity` | Byte | Shadow opacity (0-255) |
| `DynAmbientColor` | color | Dynamic ambient light RGB |

**Lighting System:**

- **SunAmbientColor**: Base ambient illumination (affects all surfaces)
- **SunDiffuseColor**: Directional sunlight color
- **SunShadows**: Enables real-time shadow casting
- **ShadowOpacity**: Controls shadow darkness
- **DynAmbientColor**: Secondary ambient for dynamic lighting

## Fog Settings

| field | type | Description |
| ----- | ---- | ----------- |
| `SunFogOn` | Byte | Enable fog rendering |
| `SunFogNear` | Float | Fog start distance |
| `SunFogFar` | Float | Fog end distance |
| `SunFogColor` | color | Fog color RGB |

**Fog Rendering:**

- **SunFogOn=1**: Fog active
- **SunFogNear**: Distance where fog begins (world units)
- **SunFogFar**: Distance where fog is opaque
- **SunFogColor**: Fog tint color (atmosphere)

**Fog Calculation:**

- Linear interpolation from Near to Far
- Objects beyond Far fully obscured
- Creates depth perception and atmosphere

## Moon Lighting (Unused)

| field | type | Description |
| ----- | ---- | ----------- |
| `MoonAmbientColor` | color | Moon ambient light (unused) |
| `MoonDiffuseColor` | color | Moon diffuse light (unused) |
| `MoonFogOn` | Byte | Moon fog toggle (unused) |
| `MoonFogNear` | Float | Moon fog start (unused) |
| `MoonFogFar` | Float | Moon fog end (unused) |
| `MoonFogColor` | color | Moon fog color (unused) |
| `MoonShadows` | Byte | Moon shadows (unused) |
| `IsNight` | Byte | Night time flag (unused) |

**Moon System:**

- Defined in file format but not used by KotOR engine
- Intended for day/night cycle (not implemented)
- Always use Sun settings for lighting

## Grass Rendering

| field | type | Description |
| ----- | ---- | ----------- |
| `Grass_TexName` | [ResRef](GFF-File-Format#gff-data-types) | Grass [texture](TPC-File-Format) name |
| `Grass_Density` | Float | Grass blade density (0.0-1.0) |
| `Grass_QuadSize` | Float | size of grass patches |
| `Grass_Ambient` | color | Grass ambient color RGB |
| `Grass_Diffuse` | color | Grass diffuse color RGB |
| `Grass_Emissive` (KotOR2) | color | Grass emissive color RGB |
| `Grass_Prob_LL` | Float | Spawn probability lower-left |
| `Grass_Prob_LR` | Float | Spawn probability lower-right |
| `Grass_Prob_UL` | Float | Spawn probability upper-left |
| `Grass_Prob_UR` | Float | Spawn probability upper-right |

**Grass System:**

- **Grass_TexName**: [texture](TPC-File-Format) for grass blades (TGA/[TPC](TPC-File-Format))
- **Grass_Density**: Coverage density (1.0 = full coverage)
- **Grass_QuadSize**: Patch size in world units
- **Probability fields**: Control grass distribution across area

**Grass Rendering:**

1. Area divided into grid based on QuadSize
2. Each quad has spawn probability from corner interpolation
3. Density determines blades per quad
4. Grass billboards oriented to camera

## Weather System (KotOR2)

| field | type | Description |
| ----- | ---- | ----------- |
| `ChanceRain` (KotOR2) | Int | Rain probability (0-100) |
| `ChanceSnow` (KotOR2) | Int | Snow probability (0-100) |
| `ChanceLightning` (KotOR2) | Int | Lightning probability (0-100) |

**Weather Effects:**

- Random weather based on probability
- Particle effects for rain/snow
- Lightning provides flash and sound

## Dirty/Dust Settings (KotOR2)

| field | type | Description |
| ----- | ---- | ----------- |
| `DirtyARGBOne` (KotOR2) | DWord | First dust color ARGB |
| `DirtySizeOne` (KotOR2) | [float](GFF-File-Format#gff-data-types) | First dust particle size |
| `DirtyFormulaOne` (KotOR2) | Int | First dust formula type |
| `DirtyFuncOne` (KotOR2) | Int | First dust function |
| `DirtyARGBTwo` (KotOR2) | DWord | Second dust color ARGB |
| `DirtySizeTwo` (KotOR2) | [float](GFF-File-Format#gff-data-types) | Second dust particle size |
| `DirtyFormulaTwo` (KotOR2) | Int | Second dust formula type |
| `DirtyFuncTwo` (KotOR2) | Int | Second dust function |
| `DirtyARGBThree` (KotOR2) | DWord | Third dust color ARGB |
| `DirtySizeThree` (KotOR2) | [float](GFF-File-Format#gff-data-types) | Third dust particle size |
| `DirtyFormulaThre` (KotOR2) | Int | Third dust formula type |
| `DirtyFuncThree` (KotOR2) | Int | Third dust function |

**Dust Particle System:**

- Three independent dust layers
- Each layer has color, size, and behavior
- Creates atmospheric dust/smoke effects

## Environment & Camera

| field | type | Description |
| ----- | ---- | ----------- |
| `DefaultEnvMap` | [ResRef](GFF-File-Format#gff-data-types) | Default environment map [texture](TPC-File-Format) |
| `CameraStyle` | Int | Camera behavior type |
| `AlphaTest` | Byte | Alpha testing threshold |
| `WindPower` | Int | Wind strength for effects |
| `LightingScheme` | Int | Lighting scheme identifier (unused) |

**Environment Mapping:**

- `DefaultEnvMap`: Cubemap for reflective surfaces
- Applied to [models](MDL-MDX-File-Format) without specific envmaps

**Camera Behavior:**

- `CameraStyle`: Determines camera constraints
- Defines zoom, rotation, and collision behavior

## Area Behavior [flags](GFF-File-Format#gff-data-types)

| field | type | Description |
| ----- | ---- | ----------- |
| `Unescapable` | Byte | Cannot use save/travel functions |
| `DisableTransit` | Byte | Cannot travel to other modules |
| `StealthXPEnabled` | Byte | Award stealth XP |
| `StealthXPLoss` | Int | Stealth detection XP penalty |
| `StealthXPMax` | Int | Maximum stealth XP per area |

**Stealth System:**

- **StealthXPEnabled**: Area rewards stealth gameplay
- **StealthXPMax**: Cap on XP from stealth
- **StealthXPLoss**: Penalty when detected

**Area Restrictions:**

- **Unescapable**: Prevents save/load menus (story sequences)
- **DisableTransit**: Locks player in current location

## Skill Check Modifiers

| field | type | Description |
| ----- | ---- | ----------- |
| `ModSpotCheck` | Int | Awareness skill modifier (unused) |
| `ModListenCheck` | Int | Listen skill modifier (unused) |

**Skill Modifiers:**

- Intended to modify detection checks area-wide
- Not implemented in KotOR engine

## Script Hooks

| field | type | Description |
| ----- | ---- | ----------- |
| `OnEnter` | [ResRef](GFF-File-Format#gff-data-types) | Fires when entering area |
| `OnExit` | [ResRef](GFF-File-Format#gff-data-types) | Fires when leaving area |
| `OnHeartbeat` | [ResRef](GFF-File-Format#gff-data-types) | Fires periodically |
| `OnUserDefined` | [ResRef](GFF-File-Format#gff-data-types) | Fires on user-defined events |

**Script Execution:**

- **OnEnter**: Area initialization, cinematics, spawns
- **OnExit**: Cleanup, state saving
- **OnHeartbeat**: Periodic updates (every 6 seconds)
- **OnUserDefined**: Custom event handling

## Minimap coordinate System

The [ARE](GFF-File-Format#are-area) file contains a `Map` struct that defines how the minimap texture (`lbl_map<resname>`) aligns with the world space [walkmesh](BWM-File-Format). This coordinate system allows the game to display the player's position on the minimap and render map notes at correct locations.

### Map Struct fields

| field | type | Description |
| ----- | ---- | ----------- |
| `MapPt1X` | Float | First map point X coordinate (normalized 0.0-1.0) |
| `MapPt1Y` | Float | First map point Y coordinate (normalized 0.0-1.0) |
| `MapPt2X` | Float | Second map point X coordinate (normalized 0.0-1.0) |
| `MapPt2Y` | Float | Second map point Y coordinate (normalized 0.0-1.0) |
| `WorldPt1X` | Float | First world point X coordinate (world units) |
| `WorldPt1Y` | Float | First world point Y coordinate (world units) |
| `WorldPt2X` | Float | Second world point X coordinate (world units) |
| `WorldPt2Y` | Float | Second world point Y coordinate (world units) |
| `NorthAxis` | Int | North direction orientation (0-3) |
| `MapZoom` | Int | Map zoom level |
| `MapResX` | Int | Map [texture](TPC-File-Format) resolution X dimension |

**coordinate System:**

- **Map Points** (`MapPt1X/Y`, `MapPt2X/Y`): Normalized [texture](TPC-File-Format) coordinates (0.0-1.0) that correspond to specific locations on the minimap [texture](TPC-File-Format)
- **World Points** (`WorldPt1X/Y`, `WorldPt2X/Y`): World space coordinates (in game units) that correspond to the same locations in the 3D [walkmesh](BWM-File-Format)
- **NorthAxis**: Determines which axis is "north" and affects coordinate mapping (see below)

### coordinate [transformation](BWM-File-Format#walkable-adjacencies)

The game engine uses a linear [transformation](BWM-File-Format#walkable-adjacencies) to convert between world coordinates and map [texture](TPC-File-Format) coordinates. This allows:

1. **Rendering the minimap [texture](TPC-File-Format)** in world space (overlaying it on the [walkmesh](BWM-File-Format))
2. **Converting player position** to minimap coordinates for the minimap UI
3. **Placing map notes** at correct positions on the minimap

**Mathematical Formula (World → Map [texture](TPC-File-Format) coordinates):**

Reference: `vendor/reone/src/libs/game/gui/map.cpp` - `getMapPosition()`

For **NorthAxis 0 or 1** (PositiveY or NegativeY):

```
scaleX = (MapPt1X - MapPt2X) / (WorldPt1X - WorldPt2X)
scaleY = (MapPt1Y - MapPt2Y) / (WorldPt1Y - WorldPt2Y)
mapPos.x = (world.x - WorldPt1X) * scaleX + MapPt1X
mapPos.y = (world.y - WorldPt1Y) * scaleY + MapPt1Y
```

For **NorthAxis 2 or 3** (PositiveX or NegativeX - swapped mapping):

```
scaleX = (MapPt1Y - MapPt2Y) / (WorldPt1X - WorldPt2X)
scaleY = (MapPt1X - MapPt2X) / (WorldPt1Y - WorldPt2Y)
mapPos.x = (world.y - WorldPt1Y) * scaleY + MapPt1X
mapPos.y = (world.x - WorldPt1X) * scaleX + MapPt1Y
```

**Inverse Transformation (Map [texture](TPC-File-Format) → World coordinates):**

For rendering the minimap [texture](TPC-File-Format) in world space:

```
worldScaleX = (WorldPt1X - WorldPt2X) / (MapPt1X - MapPt2X)
worldScaleY = (WorldPt1Y - WorldPt2Y) / (MapPt1Y - MapPt2Y)
world.x = WorldPt1X + (mapPos.x - MapPt1X) * worldScaleX
world.y = WorldPt1Y + (mapPos.y - MapPt1Y) * worldScaleY
```

For [texture](TPC-File-Format) origin (0,0) in world space:

```
originX = WorldPt1X - MapPt1X * worldScaleX
originY = WorldPt1Y - MapPt1Y * worldScaleY
```

### NorthAxis values

| value | Enum | Description | coordinate Mapping |
| ----- | ---- | ----------- | ------------------ |
| 0 | PositiveY | +Y is north | Direct X/Y mapping |
| 1 | NegativeY | -Y is north | Direct X/Y mapping |
| 2 | PositiveX | +X is north | Swapped: world.x → map.y, world.y → map.x |
| 3 | NegativeX | -X is north | Swapped: world.x → map.y, world.y → map.x |

**NorthAxis Usage:**

- Determines which direction is "north" for the minimap
- Affects how world coordinates map to [texture](TPC-File-Format) coordinates
- Used for rotating the player arrow on the minimap
- Cases 0,1 use direct mapping; cases 2,3 swap X/Y axes

### Map [texture](TPC-File-Format)

The minimap [texture](TPC-File-Format) is loaded from [texture](TPC-File-Format) resource:

- **Resource Name**: `lbl_map<resname>` (e.g., `lbl_maptat001` for area `tat001`)
- **format**: [TPC](TPC-File-Format) ([texture](TPC-File-Format) Pack Container)
- **Typical size**: 435x256 pixels (may vary)
- **Usage**: Displayed in minimap UI and overlaid on [walkmesh](BWM-File-Format) in editor

**Relationship to [walkmesh](BWM-File-Format):**

- The minimap [texture](TPC-File-Format) represents a top-down view of the area's [walkmesh](BWM-File-Format)
- Map points correspond to specific [vertices](MDL-MDX-File-Format#vertex-structure)/[faces](MDL-MDX-File-Format#face-structure) in the walkmesh ([BWM file](BWM-File-Format))
- The blue walkable area shown in editors is rendered from the [walkmesh](BWM-File-Format) [faces](MDL-MDX-File-Format#face-structure)
- Both the minimap [texture](TPC-File-Format) and [walkmesh](BWM-File-Format) must align correctly for proper gameplay
- Misalignment causes the walkable area to appear rotated/flipped relative to the minimap image

### Implementation Notes

**coordinate Precision:**

- Map points [ARE](GFF-File-Format#are-area) normalized (0.0-1.0) and require high precision (6+ decimal places)
- Rounding errors can cause misalignment between [walkmesh](BWM-File-Format) and minimap [texture](TPC-File-Format)
- Always preserve full precision when editing map coordinates

**Common Issues:**

1. **Misaligned Minimap**: Caused by incorrect coordinate [transformation](BWM-File-Format#walkable-adjacencies) or NorthAxis handling
2. **Inverted Mapping**: Negative scales indicate inverted mapping ([texture](TPC-File-Format) needs mirroring)
3. **Precision Loss**: Using insufficient decimal precision in UI spinboxes causes drift

**Editor Rendering:**

When rendering the minimap [texture](TPC-File-Format) over the [walkmesh](BWM-File-Format) in editors:

- Calculate linear scale: `worldScale = worldDelta / mapDelta`
- Calculate origin: `origin = worldPoint1 - mapPoint1 * worldScale`
- Handle NorthAxis swapping for cases 2,3
- Mirror [texture](TPC-File-Format) if scale is negative (inverted mapping)

**Reference Implementations:**

- `vendor/reone/src/libs/game/gui/map.cpp` - `getMapPosition()` function
- `vendor/reone/src/libs/resource/parser/gff/are.cpp` - [ARE](GFF-File-Format#are-area) parsing
- `Libraries/PyKotor/src/pykotor/resource/generics/are.py` - PyKotor [ARE](GFF-File-Format#are-area) implementation
- `Tools/HolocronToolset/src/toolset/gui/widgets/renderer/[walkmesh](BWM-File-Format).py` - Minimap rendering

## Rooms & Audio Zones

| field | type | Description |
| ----- | ---- | ----------- |
| `Rooms` | List | Room definitions for audio zones and minimap regions |

**Rooms Struct fields:**

- `RoomName` ([CExoString](GFF-File-Format#gff-data-types)): Room identifier (referenced by [VIS files](VIS-File-Format))
- `EnvAudio` (Int): Environment audio index for room acoustics
- `AmbientScale` (Float): Ambient audio volume scaling factor
- `DisableWeather` (KotOR2, [byte](GFF-File-Format#gff-data-types)): Disable weather effects in this room
- `ForceRating` (KotOR2, Int): Force rating modifier for this room

**Room System:**

- Defines minimap regions and audio zones
- Each room has audio properties (EnvAudio, AmbientScale)
- Audio transitions smoothly between rooms
- Minimap reveals room-by-room as player explores
- Rooms referenced by [VIS](VIS-File-Format) (visibility) files for audio occlusion
- KotOR2: Rooms can disable weather and modify force rating

## Implementation Notes

### Area Loading Sequence

1. **Parse [ARE](GFF-File-Format#are-area)**: Load static properties from [GFF](GFF-File-Format)
2. **Apply Lighting**: Set sun/ambient colors
3. **Setup Fog**: Configure fog parameters
4. **Load Grass**: Initialize grass rendering if configured
5. **Configure Weather**: Activate weather systems (KotOR2)
6. **Register Scripts**: Setup area event handlers
7. **Load [GIT](GFF-File-Format#git-game-instance-template)**: Spawn dynamic objects (separate file)
8. **Load Minimap**: Parse map coordinates and load minimap [texture](TPC-File-Format)

### Minimap coordinate System Best Practices

**Precision Requirements:**

- Map coordinates (`MapPt1X/Y`, `MapPt2X/Y`) [ARE](GFF-File-Format#are-area) normalized (0.0-1.0) and require **at least 6 decimal places** of precision
- Using insufficient precision (e.g., 2 decimals) causes coordinate drift during roundtrip operations
- Example: `0.6669999957084656` rounded to 2 decimals becomes `0.67`, causing misalignment

**Common Pitfalls:**

1. **Incorrect rotation**: Do NOT rotate map points around (0.5, 0.5) - use direct linear [transformation](BWM-File-Format#walkable-adjacencies)
2. **Precision Loss**: Always use high-precision spinboxes (6+ decimals) for map coordinate editing
3. **NorthAxis Handling**: Remember that cases 2,3 swap X/Y coordinates in the [transformation](BWM-File-Format#walkable-adjacencies)
4. **Negative Scales**: Negative scale values indicate inverted mapping - mirror the [texture](TPC-File-Format) accordingly

**Validation:**

- Always validate map coordinates preserve exactly through save/load roundtrips
- Test minimap alignment visually in editor after coordinate changes
- Verify [walkmesh](BWM-File-Format) and minimap [texture](TPC-File-Format) align correctly for all NorthAxis values

**Lighting Performance:**

- Ambient/Diffuse colors affect all area [geometry](MDL-MDX-File-Format#geometry-header)
- Shadow rendering is expensive (SunShadows=0 for performance)
- Dynamic lighting for special effects only

**Grass Optimization:**

- High density grass impacts framerate significantly
- Probability fields allow targeted grass placement
- Grass LOD based on camera distance

**Audio Zones:**

- Rooms define audio transitions
- EnvAudio from [ARE](GFF-File-Format#are-area) and Rooms determines soundscape
- Smooth fade between zones

**Common Area Configurations:**

**Outdoor Areas:**

- Bright sunlight (high diffuse)
- Fog for horizon
- Grass rendering
- Wind effects

**Indoor Areas:**

- Low ambient lighting
- No fog (usually)
- No grass
- Controlled camera

**Dark Areas:**

- Minimal ambient
- Strong diffuse for dramatic shadows
- Fog for atmosphere

**Special Areas:**

- Unescapable for story sequences
- Custom camera styles for unique views
- Specific environment maps for mood

### Minimap Rendering Implementation Details

**World Space [texture](TPC-File-Format) Rendering:**

When rendering the minimap [texture](TPC-File-Format) over the [walkmesh](BWM-File-Format) in editors, the following steps [ARE](GFF-File-Format#are-area) required:

1. **Calculate World scale Factors:**

   ```
   worldScaleX = (WorldPt1X - WorldPt2X) / (MapPt1X - MapPt2X)
   worldScaleY = (WorldPt1Y - WorldPt2Y) / (MapPt1Y - MapPt2Y)
   ```

   These represent world units per [texture](TPC-File-Format) unit (inverse of reone's scale factors).

2. **Calculate [texture](TPC-File-Format) Origin in World Space:**

   ```
   originX = WorldPt1X - MapPt1X * worldScaleX
   originY = WorldPt1Y - MapPt1Y * worldScaleY
   ```

   This finds where [texture](TPC-File-Format) coordinate (0,0) maps to in world space.

3. **Calculate [texture](TPC-File-Format) End in World Space:**

   ```
   endX = WorldPt1X + (1.0 - MapPt1X) * worldScaleX
   endY = WorldPt1Y + (1.0 - MapPt1Y) * worldScaleY
   ```

   This finds where [texture](TPC-File-Format) coordinate (1,1) maps to in world space.

4. **Handle NorthAxis coordinate Swapping:**
   - For NorthAxis 2 or 3: Swap `originX/originY` and `endX/endY` ([texture](TPC-File-Format) X maps to world Y, [texture](TPC-File-Format) Y maps to world X)

5. **Handle Inverted Mappings:**
   - If `worldScaleX < 0` or `worldScaleY < 0`: Mirror the [texture](TPC-File-Format) horizontally/vertically respectively
   - Negative scales indicate the mapping is inverted ([texture](TPC-File-Format) is flipped relative to world space)

6. **Render [texture](TPC-File-Format):**
   - Draw [texture](TPC-File-Format) in world space rectangle from `(min(originX, endX), min(originY, endY))` to `(max(originX, endX), max(originY, endY))`
   - Apply mirroring if scales [ARE](GFF-File-Format#are-area) negative

**Mathematical Derivation:**

The inverse [transformation](BWM-File-Format#walkable-adjacencies) is derived from reone's forward [transformation](BWM-File-Format#walkable-adjacencies):

Forward (World → Map): `mapPos.x = (world.x - WorldPt1X) * scaleX + MapPt1X`

Solving for world.x:

```
mapPos.x - MapPt1X = (world.x - WorldPt1X) * scaleX
(mapPos.x - MapPt1X) / scaleX = world.x - WorldPt1X
world.x = WorldPt1X + (mapPos.x - MapPt1X) / scaleX
```

Substituting `scaleX = (MapPt1X - MapPt2X) / (WorldPt1X - WorldPt2X)`:

```
world.x = WorldPt1X + (mapPos.x - MapPt1X) * (WorldPt1X - WorldPt2X) / (MapPt1X - MapPt2X)
```

For [texture](TPC-File-Format) origin (mapPos = 0):

```
world.x = WorldPt1X - MapPt1X * (WorldPt1X - WorldPt2X) / (MapPt1X - MapPt2X)
world.x = WorldPt1X - MapPt1X * worldScaleX
```

**Common Rendering Bugs:**

1. **rotation Around Center Bug:**
   - **Symptom**: Walkable area appears rotated/flipped ~180° relative to minimap [texture](TPC-File-Format)
   - **Cause**: Incorrectly rotating map points around (0.5, 0.5) before calculating [texture](TPC-File-Format) position
   - **Fix**: Use direct linear [transformation](BWM-File-Format#walkable-adjacencies) without any rotation of map points
   - **Pattern**: `map_point = rotate(map_point - 0.5, angle) + 0.5` ❌ (WRONG)

2. **Precision Loss Bug:**
   - **Symptom**: coordinates drift during save/load (e.g., 0.667 → 0.67)
   - **Cause**: UI spinboxes with insufficient decimal precision (default 2 decimals)
   - **Fix**: Set spinbox decimals to 6+ for normalized coordinates
   - **Impact**: Causes cumulative misalignment over multiple roundtrips

3. **NorthAxis Swapping Bug:**
   - **Symptom**: Minimap appears correct for NorthAxis 0,1 but wrong for 2,3
   - **Cause**: Not handling coordinate axis swapping for NorthAxis 2,3
   - **Fix**: Swap X/Y coordinates when NorthAxis is 2 or 3

4. **Inverted Mapping Bug:**
   - **Symptom**: Minimap [texture](TPC-File-Format) appears flipped horizontally or vertically
   - **Cause**: Not detecting and handling negative scale values
   - **Fix**: Check scale signs and mirror [texture](TPC-File-Format) accordingly

**[walkmesh](BWM-File-Format) Alignment:**

The blue walkable area rendered in editors comes from the walkmesh ([BWM file](BWM-File-Format)) [faces](MDL-MDX-File-Format#face-structure). The minimap [texture](TPC-File-Format) must align with this [walkmesh](BWM-File-Format):

- **[walkmesh](BWM-File-Format) coordinates**: 3D world space coordinates (X, Y, Z)
- **Minimap [texture](TPC-File-Format)**: 2D [texture](TPC-File-Format) coordinates (0.0-1.0) mapped to world X/Y plane
- **Alignment**: Map points correspond to specific [walkmesh](BWM-File-Format) [vertices](MDL-MDX-File-Format#vertex-structure)/[faces](MDL-MDX-File-Format#face-structure)
- **Verification**: The walkable area outline should match the minimap [texture](TPC-File-Format) boundaries

**Testing & Validation:**

1. **Roundtrip Validation:**
   - Load [ARE](GFF-File-Format#are-area) file → Save without changes → Load saved file
   - Verify all map coordinates (`MapPt1X/Y`, `MapPt2X/Y`, `WorldPt1X/Y`, `WorldPt2X/Y`) preserve exactly (tolerance: 0.0001)
   - Verify NorthAxis, MapZoom, MapResX preserve exactly

2. **Visual Alignment Check:**
   - Open [ARE](GFF-File-Format#are-area) in editor with [walkmesh](BWM-File-Format) loaded
   - Verify blue walkable area aligns with minimap [texture](TPC-File-Format)
   - Check alignment for all NorthAxis values (0, 1, 2, 3)
   - Verify [texture](TPC-File-Format) isn't flipped or rotated incorrectly

3. **coordinate [transformation](BWM-File-Format#walkable-adjacencies) Test:**
   - Pick known world coordinates from [walkmesh](BWM-File-Format)
   - Convert to map coordinates using forward [transformation](BWM-File-Format#walkable-adjacencies)
   - Verify map coordinates [ARE](GFF-File-Format#are-area) within valid range (0.0-1.0)
   - Convert back to world coordinates using inverse [transformation](BWM-File-Format#walkable-adjacencies)
   - Verify roundtrip accuracy (tolerance: 0.01 world units)

**Reference Code Locations:**

- **Reone Forward [transformation](BWM-File-Format#walkable-adjacencies)**: `vendor/reone/src/libs/game/gui/map.cpp:174-199` - `getMapPosition()`
- **Reone [ARE](GFF-File-Format#are-area) Parsing**: `vendor/reone/src/libs/resource/parser/gff/are.cpp:284-297` - Map struct parsing
- **PyKotor [ARE](GFF-File-Format#are-area) Class**: `Libraries/PyKotor/src/pykotor/resource/generics/are.py:250-260` - Map coordinate storage
- **PyKotor Minimap Rendering**: `Tools/HolocronToolset/src/toolset/gui/widgets/renderer/[walkmesh](BWM-File-Format).py:555-603` - [texture](TPC-File-Format) rendering implementation
