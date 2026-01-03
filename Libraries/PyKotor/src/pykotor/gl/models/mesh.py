from __future__ import annotations

import ctypes

from typing import TYPE_CHECKING

from pykotor.gl.compat import (
    has_pyopengl,
    missing_constant,
    missing_gl_func,
    safe_gl_error_module,
)
from pykotor.gl.glm_compat import mat4, vec3, vec4, value_ptr

HAS_PYOPENGL = has_pyopengl()
gl_error = safe_gl_error_module()

if HAS_PYOPENGL:
    from OpenGL.GL import glGenBuffers, glGenVertexArrays, glVertexAttribPointer
    from OpenGL.GL.shaders import GL_FALSE
    from OpenGL.raw.GL.ARB.tessellation_shader import GL_TRIANGLES
    from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
    from OpenGL.raw.GL.VERSION.GL_1_0 import GL_UNSIGNED_SHORT
    from OpenGL.raw.GL.VERSION.GL_1_1 import glDrawElements
    from OpenGL.raw.GL.VERSION.GL_1_3 import GL_TEXTURE0, GL_TEXTURE1, glActiveTexture
    from OpenGL.raw.GL.VERSION.GL_1_5 import GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, glBindBuffer, glBufferData
    from OpenGL.raw.GL.VERSION.GL_2_0 import glEnableVertexAttribArray
    from OpenGL.raw.GL.VERSION.GL_3_0 import glBindVertexArray
else:
    glGenBuffers = missing_gl_func("glGenBuffers")
    glGenVertexArrays = missing_gl_func("glGenVertexArrays")
    glVertexAttribPointer = missing_gl_func("glVertexAttribPointer")
    glDrawElements = missing_gl_func("glDrawElements")
    glActiveTexture = missing_gl_func("glActiveTexture")
    glBindBuffer = missing_gl_func("glBindBuffer")
    glBufferData = missing_gl_func("glBufferData")
    glEnableVertexAttribArray = missing_gl_func("glEnableVertexAttribArray")
    glBindVertexArray = missing_gl_func("glBindVertexArray")
    GL_FALSE = missing_constant("GL_FALSE")
    GL_TRIANGLES = missing_constant("GL_TRIANGLES")
    GL_FLOAT = missing_constant("GL_FLOAT")
    GL_UNSIGNED_SHORT = missing_constant("GL_UNSIGNED_SHORT")
    GL_TEXTURE0 = missing_constant("GL_TEXTURE0")
    GL_TEXTURE1 = missing_constant("GL_TEXTURE1")
    GL_ARRAY_BUFFER = missing_constant("GL_ARRAY_BUFFER")
    GL_ELEMENT_ARRAY_BUFFER = missing_constant("GL_ELEMENT_ARRAY_BUFFER")
    GL_STATIC_DRAW = missing_constant("GL_STATIC_DRAW")

from pykotor.gl.native import fastmath

if TYPE_CHECKING:
    from pykotor.gl.glm_compat import mat4

    from pykotor.gl.models.node import Node
    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader


class Mesh:
    """Mesh class for rendering 3D geometry.
    
    Performance notes:
    - Uses __slots__ to reduce memory and improve attribute access speed
    - VAO/VBO/EBO are created once and reused
    - Texture lookups go through scene.texture() which has its own caching
    
    Note: We intentionally do NOT cache texture references at the mesh level because:
    1. Textures can be loaded asynchronously and replaced
    2. Scene.texture() already provides O(1) dict lookup
    3. Caching stale texture references causes rendering bugs (wrong textures)
    """
    
    __slots__ = (
        "_scene",
        "_node",
        "texture",
        "lightmap",
        "vertex_data",
        "mdx_size",
        "mdx_vertex",
        "mdx_texture",
        "mdx_lightmap",
        "_index_data",
        "_vao",
        "_vbo",
        "_ebo",
        "_face_count",
        "_vertex_blob_cache",
    )
    
    def __init__(
        self,
        scene: Scene,
        node: Node,
        texture: str,
        lightmap: str,
        vertex_data: bytearray,
        element_data: bytearray,
        block_size: int,
        data_bitflags: int,
        vertex_offset: int,
        normal_offset: int,
        texture_offset: int,
        lightmap_offset: int,
    ):
        self._scene: Scene = scene
        self._node: Node = node

        self.texture: str = "NULL"
        self.lightmap: str = "NULL"

        self.vertex_data: bytearray = vertex_data
        self.mdx_size: int = block_size
        self.mdx_vertex: int = vertex_offset
        self.mdx_texture: int = texture_offset
        self.mdx_lightmap: int = lightmap_offset
        self._index_data: bytes = bytes(element_data)
        self._vertex_blob_cache: bytes | None = None

        if HAS_PYOPENGL:
            self._vao: int = glGenVertexArrays(1)
            self._vbo: int = glGenBuffers(1)
            self._ebo: int = glGenBuffers(1)
            glBindVertexArray(self._vao)
        else:
            self._vao = 0
            self._vbo = 0
            self._ebo = 0

        if HAS_PYOPENGL:
            glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
            # Convert vertex_data bytearray to MemoryView
            vertex_data_mv = memoryview(vertex_data)
            glBufferData(GL_ARRAY_BUFFER, len(vertex_data), vertex_data_mv, GL_STATIC_DRAW)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
            # Convert element_data bytearray to MemoryView
            element_data_mv = memoryview(element_data)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(element_data), element_data_mv, GL_STATIC_DRAW)

            if data_bitflags & 0x0001:
                glEnableVertexAttribArray(1)
                glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(vertex_offset))

            if data_bitflags & 0x0020 and texture and texture != "NULL":
                glEnableVertexAttribArray(3)
                glVertexAttribPointer(3, 2, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(texture_offset))
                self.texture = texture

            if data_bitflags & 0x0004 and lightmap and lightmap != "NULL":
                glEnableVertexAttribArray(4)
                glVertexAttribPointer(4, 2, GL_FLOAT, GL_FALSE, block_size, ctypes.c_void_p(lightmap_offset))
                self.lightmap = lightmap

            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)

        self._face_count: int = len(element_data) // 2

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        override_texture: str | None = None,
    ):
        """Draw the mesh.
        
        Args:
            shader: The shader program to use.
            transform: The model transformation matrix.
            override_texture: Optional texture name to use instead of the mesh's texture.
        """
        if not HAS_PYOPENGL:
            raise gl_error.NullFunctionError("PyOpenGL is unavailable.")
        
        shader.set_matrix4("model", transform)

        # Get textures from scene (scene.texture() has O(1) dict lookup + caching)
        tex_name = override_texture if override_texture else self.texture
        texture = self._scene.texture(tex_name)
        lightmap = self._scene.texture(self.lightmap, lightmap=True)
        
        glActiveTexture(GL_TEXTURE0)
        texture.use()
        
        glActiveTexture(GL_TEXTURE1)
        lightmap.use()

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)

    def _fast_bounds(
        self,
        transform: mat4,
    ) -> tuple[vec3, vec3] | None:
        if not fastmath.available() or self.mdx_size <= 0:
            return None
        vertex_count = len(self.vertex_data) // self.mdx_size
        if vertex_count == 0:
            return None
        mv = memoryview(self.vertex_data)
        matrix_values = [value_ptr(transform)[i] for i in range(16)]
        bounds_min, bounds_max = fastmath.transform_bounds(
            mv, vertex_count, self.mdx_size, self.mdx_vertex, matrix_values
        )
        return vec3(*bounds_min), vec3(*bounds_max)

    def bounds(
        self,
        transform: mat4,
    ) -> tuple[vec3, vec3]:
        fast = self._fast_bounds(transform)
        if fast is not None:
            return fast

        min_point = vec3(100000, 100000, 100000)
        max_point = vec3(-100000, -100000, -100000)
        vertex_count = len(self.vertex_data) // self.mdx_size
        if vertex_count == 0:
            return min_point, max_point

        import struct

        for idx in range(vertex_count):
            offset = idx * self.mdx_size + self.mdx_vertex
            x, y, z = struct.unpack_from("<3f", self.vertex_data, offset)
            world = transform * vec4(x, y, z, 1.0)
            min_point.x = min(min_point.x, world.x)
            min_point.y = min(min_point.y, world.y)
            min_point.z = min(min_point.z, world.z)
            max_point.x = max(max_point.x, world.x)
            max_point.y = max(max_point.y, world.y)
            max_point.z = max(max_point.z, world.z)
        return min_point, max_point

    def vertex_blob(self) -> bytes:
        if self._vertex_blob_cache is not None:
            return self._vertex_blob_cache

        import numpy as np

        vertex_count = len(self.vertex_data) // self.mdx_size
        if vertex_count == 0:
            self._vertex_blob_cache = np.zeros((1, 7), dtype=np.float32).tobytes()
            return self._vertex_blob_cache

        blob = np.zeros((vertex_count, 7), dtype=np.float32)
        positions = np.frombuffer(
            self.vertex_data,
            dtype="<f4",
            count=vertex_count * 3,
            offset=self.mdx_vertex,
        ).reshape(vertex_count, 3)
        blob[:, 0:3] = positions

        if self.mdx_texture >= 0:
            diffuse = np.frombuffer(
                self.vertex_data,
                dtype="<f4",
                count=vertex_count * 2,
                offset=self.mdx_texture,
            ).reshape(vertex_count, 2)
            blob[:, 3:5] = diffuse

        if self.mdx_lightmap >= 0:
            lightmap = np.frombuffer(
                self.vertex_data,
                dtype="<f4",
                count=vertex_count * 2,
                offset=self.mdx_lightmap,
            ).reshape(vertex_count, 2)
            blob[:, 5:7] = lightmap

        self._vertex_blob_cache = blob.tobytes()
        return self._vertex_blob_cache

    @property
    def index_data(self) -> bytes:
        return self._index_data
