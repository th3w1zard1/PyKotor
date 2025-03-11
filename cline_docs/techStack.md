# PyKotor Panda3D Backend Tech Stack

## Core Technologies

### Panda3D
- Version: 1.10.13
- Purpose: 3D rendering engine replacement for OpenGL
- Key Features:
  - Scene graph management
  - Built-in collision system
  - Shader support
  - Model loading
  - Texture management

### Python
- Version: 3.8+
- Key Libraries:
  - numpy: For efficient array operations
  - glm: For math operations (maintaining compatibility)
  - typing: For type hints

## Architecture Decisions

### Scene Management
- Using Panda3D's NodePath system for scene graph
- Custom Scene class inheriting from ShowBase
- Maintaining existing PyKotor scene structure

### Model Loading
- Converting MDL/MDX format to Panda3D's internal format
- Using Panda3D's GeomNode for mesh rendering
- Custom vertex data handling

### Shader System
- Using Panda3D's built-in shader system
- Converting GLSL shaders to Panda3D format
- Custom material system for compatibility

### Texture Management
- Using Panda3D's texture system
- Supporting existing texture formats
- Custom texture stage management for lightmaps

## Development Tools
- Visual Studio Code
- Python debugger
- Panda3D model viewer for testing
