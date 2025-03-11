# PyKotor Panda3D Backend Codebase Summary

## Key Components and Their Interactions

### Scene Management (pykotor/gl/panda3d/scene)
- Scene class: Main entry point for 3D rendering
- Camera controls and management
- Scene graph organization
- Object picking and selection

### Model System (pykotor/gl/panda3d/models)
- Mesh class: Handles vertex data and rendering
- Node class: Scene graph node management
- Model loading and conversion from MDL format
- Boundary visualization

### Shader System (pykotor/gl/panda3d/shader)
- Shader management and compilation
- Texture handling
- Material system
- Lighting implementation

## Data Flow

1. Resource Loading:
   - PyKotor loads raw MDL/MDX data
   - Conversion to Panda3D format
   - Scene graph construction
   - Texture and material application

2. Rendering Pipeline:
   - Scene graph traversal
   - Shader application
   - Texture binding
   - Final render output

## External Dependencies

### Panda3D
- Core 3D engine functionality
- Scene graph management
- Shader and texture support
- Collision detection

### PyKotor Core
- Resource management
- File format handling
- Game data structures

## Recent Changes

1. Initial Panda3D Integration
   - Basic scene setup
   - Camera system
   - Lighting implementation

2. Model Loading System
   - Vertex data conversion
   - Texture coordination
   - Material handling

## Active Development

1. Current Focus:
   - Scene management completion
   - Model loading system
   - Shader implementation

2. Upcoming:
   - Performance optimization
   - Advanced features
   - Testing and debugging