# Rendering backends in PyKotor GL

## Backend selection and errors

- PyOpenGL is optional. `pykotor.gl.compat` exposes `has_pyopengl()` plus the shared `MissingPyOpenGLError` used when legacy GL is unavailable (`Libraries/PyKotor/src/pykotor/gl/compat.py`:L8-L65).
- Legacy paths raise early when PyOpenGL is missing. `Scene` skips shader creation and `render`/`picker_render`/`screen_to_world` raise `MissingPyOpenGLError`, instructing callers that PyOpenGL is required for these operations (`Libraries/PyKotor/src/pykotor/gl/scene/scene.py`:L82-L194, L348-L477).

## [geometry](MDL-MDX-File-Format#geometry-header) availability without PyOpenGL

- `Mesh`, `Cube`, and `Boundary` skip VAO/VBO/EBO creation when PyOpenGL is absent but still populate [vertex](MDL-MDX-File-Format#vertex-structure)/index blobs for in-memory use. Calling legacy `draw` without PyOpenGL raises `MissingPyOpenGLError` (`Libraries/PyKotor/src/pykotor/gl/models/mesh.py`:L98-L203, `Libraries/PyKotor/src/pykotor/gl/models/cube.py`:L26-L116, `Libraries/PyKotor/src/pykotor/gl/models/boundary.py`:L28-L129).
- [MDL](MDL-MDX-File-Format) variants mirror the same behavior so [model](MDL-MDX-File-Format) parsing remains usable without legacy GL (`Libraries/PyKotor/src/pykotor/gl/models/mdl.py`:L233-L528).

## [texture](TPC-File-Format) pipeline

- [texture](TPC-File-Format) loaders now produce RGBA caches even when PyOpenGL is missing; OpenGL uploads run only when available. `Texture.use()` raises if legacy binding is attempted without PyOpenGL (`Libraries/PyKotor/src/pykotor/gl/shader/texture.py`:L82-L215).

## Texture resolution metadata for UI (no extra lookups)

- The renderer can expose “where a texture came from” to the UI without additional `Installation.location(...)` calls by recording the result of the existing async location resolver. `SceneBase` stores per-texture resolution metadata in `texture_lookup_info` and request names in `requested_texture_names`; these are populated during async resolution and updated on async completion (`Libraries/PyKotor/src/pykotor/gl/scene/scene_base.py`: `_resolve_texture_location`, `texture()`, `poll_async_resources()`).