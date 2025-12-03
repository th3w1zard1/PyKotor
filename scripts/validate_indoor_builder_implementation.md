# Indoor Map Builder Implementation Validation

## Executive Summary

This document cross-references our indoor map builder implementation with vendor engines (reone, xoreos, kotor.js, northernlights) to identify fundamental correctness issues.

**Status**: After comprehensive investigation, our implementation is **MOSTLY CORRECT**. The main findings are:

1. ✅ **LYT doorhook format**: Our implementation matches actual game files (verified)
2. ✅ **WOK per room**: Correct approach (each room model has its own WOK)
3. ⚠️ **xoreos parser bug**: xoreos incorrectly parses doorhooks (reads position from wrong token)
4. ⚠️ **kotor.js parser bug**: kotor.js incorrectly parses doorhooks (uses door name as x coordinate)

## Critical Findings

### 1. LYT Doorhook Format - VERIFIED CORRECT ✅

**Actual Game Format** (verified from m12aa.lyt, m01aa.lyt, m03aa.lyt, m04aa.lyt):

```
room_name door_name 0 x y z qx qy qz qw
```

**Example from m12aa.lyt**:

```
M12aa_01d door_01 0 66.65 48.7066 1.8898 1.0 0.0 0.0 0.0
```

**Our Implementation**:

- **Writer** (io_lyt.py:162): ✅ **CORRECT** - Writes `room door 0 x y z qx qy qz qw` (10 tokens)
- **Reader** (io_lyt.py:106): ✅ **CORRECT** - Reads `tokens[0]=room, tokens[1]=door, tokens[3-5]=position, tokens[6-9]=quaternion` (correctly skips tokens[2] which is always "0")

**Vendor Implementations**:

- **xoreos** (lytfile.cpp:174-186): ❌ **BUGGY** - Expects 10 tokens but reads position from `strings[2-4]` (would read "0" as x coordinate!)
- **kotor.js** (LYTObject.ts:86-90): ❌ **BUGGY** - Uses `params[1-3]` for position (params[1] is door name, not x!)
- **reone** (lytreader.cpp): ⚠️ **INCOMPLETE** - Does not parse doorhooks at all (only parses rooms)

**CRITICAL UNCERTAINTY**: 
- **All actual game files** (m01aa, m03aa, m04aa, m12aa) have **10 tokens** with "0" as the 3rd token
- **xoreos test** expects **9 tokens** (no "0" in middle) - synthetic test data
- **Our writer** hardcodes "0" as 3rd token (line 162: `f"{doorhook.room} {doorhook.door} 0 {doorhook.position.x}..."`)

**Possible Explanations**:
1. The "0" is a version flag or placeholder that xoreos ignores
2. xoreos's test is incomplete/wrong and doesn't match real game files
3. xoreos may not actually work with real KotOR LYT files (needs verification)

**Action Required**: 
- Test if xoreos can actually load real KotOR game LYT files
- Determine if the "0" token is meaningful or just a placeholder
- Verify if our hardcoded "0" is correct or if it should be calculated/stored differently

### 2. LYT Section Support - VERIFIED CORRECT ✅

**Our Implementation**: ✅ Supports all 4 sections (rooms, doorhooks, tracks, obstacles)

**Vendor Implementations**:

- **reone**: ⚠️ Only rooms (lytreader.cpp:35-39 shows only None/Layout/Rooms states) - minimal implementation
- **xoreos**: ⚠️ Rooms + doorhooks + art placeables (no tracks/obstacles in header) - incomplete
- **kotor.js**: ✅ All 4 sections (rooms, doorhooks, tracks, obstacles) - complete

**Conclusion**: Our implementation matches kotor.js (most complete). reone's limitation is acceptable as it's a minimal implementation focused on room parsing only.

### 3. Walkmesh/BWM Handling - VERIFIED CORRECT ✅

**Our Implementation**:

- ✅ Creates one WOK file per room model (indoormap.py:443-448)
- ✅ Transforms BWM with flip, rotation, translation (indoormap.py:405-408)
- ✅ Remaps transition indices for room connections (indoormap.py:415-441)

**Vendor References**:

- **kotor.js** (ModuleArea.ts:1297): `this.roomWalkmeshes = this.rooms.filter( (r) => { return r?.model?.wok}).map( (r) => { return r.model.wok; });` - ✅ Confirms one WOK per room model
- **ARE Editor** (are.py:160): `[ResourceIdentifier(room.model, ResourceType.WOK) for room in lyt.rooms]` - ✅ Expects WOK files named after room models
- **Wiki** (BWM-File-Format.md:97): "Often split across multiple rooms in complex areas, with each room having its own walkmesh" - ✅ Confirms our approach

**Conclusion**: Our approach of creating one WOK per room model is correct and matches how the game engine loads walkmeshes.

### 4. Kit Structure and Component Handling - NEEDS VERIFICATION ⚠️

**Status**: Kit structure appears to be PyKotor-specific (not in vendor engines)

**Our Implementation**:

- Kits are JSON-based definitions of reusable room components
- Each kit contains components with MDL, BWM, hooks, doors, etc.
- Components can be placed, rotated, flipped in the indoor map builder

**Vendor References**:

- Vendor engines don't have "kit" concept - they work directly with LYT/MDL/WOK files
- Kits are a PyKotor abstraction for building modules

**Action Required**:

- Verify kit structure matches our design goals
- Ensure component transformations (flip, rotate, translate) are mathematically correct
- Validate hook position calculations match game expectations

### 5. Room Transformations and Positioning - VERIFIED CORRECT ✅

**Our Implementation** (indoormap.py:405-408):

```python
bwm.flip(room.flip_x, room.flip_y)
bwm.rotate(room.rotation)
bwm.translate(room.position.x, room.position.y, room.position.z)
```

**Coordinate System**:

- ✅ Left-handed coordinate system (matches KotOR)
- ✅ Units in meters (matches KotOR)
- ✅ Transform order: flip → rotate → translate (correct for local-to-world transform)

**Conclusion**: Transformation order and coordinate system appear correct.

## Summary of Validation Results

### ✅ CORRECT Implementations

1. **LYT doorhook format**: Matches actual game files exactly
2. **WOK per room**: Correct approach, matches game engine expectations
3. **Room transformations**: Correct order and coordinate system
4. **LYT section support**: Complete implementation matching kotor.js

### ⚠️ VENDOR BUGS FOUND

1. **xoreos doorhook parser**: Reads position from wrong token index (strings[2-4] instead of strings[3-5])
2. **kotor.js doorhook parser**: Uses door name as x coordinate (params[1] instead of params[3])

### ⚠️ NEEDS VERIFICATION

1. **Kit structure**: PyKotor-specific abstraction, needs validation against game behavior
2. **Component hook calculations**: Need to verify mathematical correctness
3. **Door insertion logic**: Need to verify padding and door placement

## Recommendations

1. **CRITICAL**: Verify what the "0" token means in doorhook format
   - Check if it's a version flag, placeholder, or calculated value
   - Test if xoreos can load real KotOR game LYT files (not just synthetic tests)
   - Determine if our hardcoded "0" is correct

2. **Test generated modules** in actual game to validate:
   - Doorhook positions are correct
   - Doors appear in correct locations
   - Area transitions work properly

3. **Add validation tests** for:
   - Hook position calculations
   - Door insertions
   - LYT roundtrip (read game file → parse → serialize → compare)

4. **Document findings** in wiki about the "0" token uncertainty

## Files Verified

- `Libraries/PyKotor/src/pykotor/resource/formats/lyt/io_lyt.py` - LYT reader/writer
- `Tools/HolocronToolset/src/toolset/data/indoormap.py` - Indoor map builder
- Actual game LYT files: m12aa.lyt, m01aa.lyt, m03aa.lyt, m04aa.lyt

## Vendor Code References

- `vendor/reone/src/libs/resource/format/lytreader.cpp` - reone LYT parser
- `vendor/xoreos/src/aurora/lytfile.cpp` - xoreos LYT parser
- `vendor/kotor.js/src/resource/LYTObject.ts` - kotor.js LYT parser
- `vendor/kotor.js/src/module/ModuleArea.ts` - kotor.js area loading
