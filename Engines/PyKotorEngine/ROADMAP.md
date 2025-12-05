# PyKotorEngine Development Roadmap

This document tracks the implementation progress of PyKotorEngine, a Panda3D-based engine for rendering Knights of the Old Republic game content. The implementation follows patterns from vendor projects: reone, xoreos, kotor.js, and northernlights.

## Architecture Principles

1. **Use Libraries as much as possible**: Keep engine code focused on Panda3D-specific integration
2. **Follow vendor patterns**: Match reone/xoreos/kotor.js/northernlights implementations as closely as possible
3. **Comprehensive testing**: Write industry-standard pytest tests (no mocks)
4. **Separation of concerns**: Engine = Panda3D integration, Libraries = reusable logic

## Implementation Status

### ✅ Completed

#### Core Engine

- [x] Basic engine initialization (KotorEngine class)
- [x] Panda3D ShowBase integration
- [x] Window configuration and setup
- [x] Default lighting (ambient + directional)
- [x] Scene root creation

#### MDL Model Loading

- [x] Basic MDL/MDX file loading
- [x] Node hierarchy conversion
- [x] Mesh node conversion (basic)
- [x] Vertex format creation (position, normal, UV, tangent space)
- [x] Tangent space computation (moved to Libraries)
- [x] Face winding order handling
- [x] Node type detection (abstracted to PyKotorGL)
- [x] Geometry utilities extraction to Libraries

#### Animation System

- [x] Animation controller base class
- [x] Position controller
- [x] Orientation controller (quaternion SLERP)
- [x] Scale controller
- [x] Color controller
- [x] Alpha controller
- [x] Animation state management
- [x] Animation manager (basic)
- [x] Keyframe interpolation

#### Scene Graph

- [x] Basic scene graph implementation
- [x] Model root management
- [x] Ambient lighting
- [x] Directional lights
- [x] Point lights
- [x] Fog properties

#### Material System

- [x] Basic material manager
- [x] KotOR shader integration (basic)

### 🚧 In Progress

#### MDL Model Loading

- [x] Basic skin mesh geometry (bone weights in vertex format)
- [ ] Skeletal animation (bone transforms, skinning matrices)
- [ ] Dangly mesh physics constraints (displacement, tightness, period)
- [ ] Saber mesh special rendering (saber material flags)
- [ ] AABB/walkmesh collision geometry (invisible collision meshes)
- [x] Light node conversion (point/directional lights)
- [ ] Emitter node conversion (particle systems)
- [ ] Reference node loading (child model loading)

### 📋 Planned

#### Core Engine

- [ ] Resource manager (texture/model caching)
- [ ] Module loading (LYT, GIT, IFO)
- [ ] Area/room management
- [ ] Camera controller
- [ ] Input handling
- [ ] Event system
- [ ] Script integration (NWScript)

#### MDL Model Loading

- [ ] Complete all node type conversions
- [ ] Optimize vertex buffer creation
- [ ] Instance rendering support
- [ ] LOD (Level of Detail) support
- [ ] Model batching/merging

#### Animation System

- [ ] Skeletal animation (bone hierarchy)
- [ ] Animation blending
- [ ] Animation events/callbacks
- [ ] Bezier curve interpolation
- [ ] Animation layers
- [ ] Root motion extraction

#### Rendering Pipeline

- [ ] KotOR-specific shader system
- [ ] Material property mapping
- [ ] Texture atlas support
- [ ] Lightmap rendering
- [ ] Normal mapping
- [ ] Shadow mapping
- [ ] Post-processing effects
- [ ] Render passes (retro/PBR)

#### Particle Systems

- [ ] Emitter node implementation
- [ ] Particle spawning
- [ ] Particle physics
- [ ] Texture animation
- [ ] Billboard rendering

#### Scene Management

- [ ] Walkmesh/collision detection
- [ ] Trigger zones
- [ ] Sound nodes
- [ ] Camera nodes
- [ ] Door/transition handling
- [ ] Placeable objects
- [ ] Creature rendering
- [ ] Item rendering

#### Module System

- [ ] LYT (layout) file loading
- [ ] GIT (game instance template) loading
- [ ] Room/area management
- [ ] Door connections
- [ ] Waypoint system
- [ ] Encounter spawning
- [ ] Store/merchant system

#### Performance

- [ ] Frustum culling
- [ ] Occlusion culling
- [ ] Level-of-detail (LOD)
- [ ] Texture streaming
- [ ] Model instancing
- [ ] Batching optimization

#### Testing

- [ ] Unit tests for MDL loader
- [ ] Unit tests for animation system
- [ ] Unit tests for scene graph
- [ ] Integration tests with real MDL files
- [ ] Performance benchmarks

## Vendor Reference Mapping

### reone (C++)

- `src/libs/scene/graph.cpp` → Scene graph management
- `src/libs/scene/node/model.cpp` → Model loading and node hierarchy
- `src/libs/scene/node/mesh.cpp` → Mesh conversion
- `src/libs/scene/node/light.cpp` → Light nodes
- `src/libs/scene/node/emitter.cpp` → Particle emitters
- `src/libs/scene/animation/` → Animation system
- `src/libs/graphics/mesh.cpp` → Geometry processing

### kotor.js (TypeScript/Three.js)

- `src/three/odyssey/OdysseyModel3D.ts` → Model loading
- `src/odyssey/controllers/` → Animation controllers
- `src/odyssey/OdysseyModelAnimation.ts` → Animation state

### xoreos (C++)

- `src/graphics/mesh.cpp` → Mesh conversion
- `src/graphics/windowman.cpp` → Window management

## File Structure

```
Engines/
├── src/pykotor/engine/panda3d/
│   ├── engine.py              ✅ Basic engine
│   ├── mdl_loader.py          🚧 Model loading (in progress)
│   ├── animation.py            ✅ Animation controllers
│   ├── scene_graph.py         ✅ Scene management
│   ├── module_loader.py       ✅ Module loading (LYT/GIT)
│   ├── materials/
│   │   ├── manager.py         ✅ Material manager
│   │   └── *.frag, *.vert     ✅ Shaders
│   ├── resources/
│   │   └── texture_loader.py  ✅ TPC texture loading
│   └── legacy/                📋 Old code (to be removed)
├── PyKotorEngine/
│   ├── tests/                 📋 Planned
│   └── ROADMAP.md             ✅ This file
```

**Note**: Source code is in `Engines/src/pykotor/engine/` to allow namespace expansion:

- `from pykotor.engine.panda3d.mdl_loader import MDLLoader`
- `from pykotor.engine.panda3d.engine import KotorEngine`

## Next Steps (Priority Order)

1. **Complete MDL node type support** (skin, dangly, saber, emitter, light, reference)
2. **Implement skeletal animation** (bone weights, skinning matrices)
3. **Add particle system support** (emitter nodes)
4. **Implement module loading** (LYT, GIT files)
5. **Add comprehensive testing** (pytest with real game files)
6. **Optimize rendering pipeline** (batching, culling, LOD)

## Notes

- All geometry utilities should be in `Libraries/PyKotor/src/pykotor/common/geometry_utils.py`
- All abstract MDL conversion logic should be in `Libraries/PyKotorGL/src/pykotor/gl/models/mdl_converter.py`
- Engine code should only contain Panda3D-specific integration (NodePath, GeomNode, etc.)
- Follow vendor code patterns closely, but adapt to Python/Panda3D idioms
