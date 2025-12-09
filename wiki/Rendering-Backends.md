# Rendering backends in PyKotor GL

## Backend selection and errors

- PyOpenGL is optional. `pykotor.gl.compat` exposes `has_pyopengl()` / `has_moderngl()` plus the shared `MissingPyOpenGLError` used when legacy GL is unavailable (`Libraries/PyKotor/src/pykotor/gl/compat.py`:L8-L65).
- Legacy paths raise early when PyOpenGL is missing. `Scene` skips shader creation and `render`/`picker_render`/`screen_to_world` raise `MissingPyOpenGLError`, instructing callers to use `ModernGLRenderer` instead (`Libraries/PyKotor/src/pykotor/gl/scene/scene.py`:L82-L194, L348-L477).

## Geometry availability without PyOpenGL

- `Mesh`, `Cube`, and `Boundary` skip VAO/VBO/EBO creation when PyOpenGL is absent but still populate vertex/index blobs for ModernGL. Calling legacy `draw` without PyOpenGL raises `MissingPyOpenGLError`, but ModernGL consumers can read `vertex_blob()` / `index_data` (`Libraries/PyKotor/src/pykotor/gl/models/mesh.py`:L98-L203, `Libraries/PyKotor/src/pykotor/gl/models/cube.py`:L26-L116, `Libraries/PyKotor/src/pykotor/gl/models/boundary.py`:L28-L129).
- MDL variants mirror the same behavior so model parsing remains usable without legacy GL (`Libraries/PyKotor/src/pykotor/gl/models/mdl.py`:L233-L528).

## Texture pipeline for ModernGL

- Texture loaders now produce RGBA caches even when PyOpenGL is missing; OpenGL uploads run only when available. `Texture.use()` raises if legacy binding is attempted without PyOpenGL, while `Texture.ensure_modern()` always uploads from the cached RGBA payload (`Libraries/PyKotor/src/pykotor/gl/shader/texture.py`:L82-L215).

## ModernGL renderer coverage

- `ModernGLRenderer` consumes the CPU-side blobs and now renders cubes and boundaries through the plain shader, reusing the same mesh cache path used for standard geometry (`Libraries/PyKotor/src/pykotor/gl/modern_renderer.py`:L156-L339).
