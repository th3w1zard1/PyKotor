from __future__ import annotations

import ctypes
import logging
import math
import struct

from copy import copy
from typing import TYPE_CHECKING

import numpy as np

from pykotor.gl.compat import has_pyopengl, missing_constant, missing_gl_func, safe_gl_error_module

HAS_PYOPENGL = has_pyopengl()
gl_error = safe_gl_error_module()

if HAS_PYOPENGL:
    from OpenGL import error as gl_error  # pyright: ignore[reportMissingImports]
    from OpenGL.GL import glGenBuffers, glGenVertexArrays, glVertexAttribPointer
    from OpenGL.GL.shaders import GL_FALSE  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.ARB.tessellation_shader import GL_TRIANGLES  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_1_0 import GL_UNSIGNED_SHORT  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_1_1 import glDrawElements  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_1_3 import GL_TEXTURE0, GL_TEXTURE1, glActiveTexture  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_1_5 import GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, glBindBuffer, glBufferData  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_2_0 import glEnableVertexAttribArray  # pyright: ignore[reportMissingImports]
    from OpenGL.raw.GL.VERSION.GL_3_0 import glBindVertexArray  # pyright: ignore[reportMissingImports]
    from pykotor.gl.compat import GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, GL_SRC_COLOR, glBlendFunc, glDepthMask  # noqa: E501
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
    GL_ONE = missing_constant("GL_ONE")
    GL_ONE_MINUS_SRC_ALPHA = missing_constant("GL_ONE_MINUS_SRC_ALPHA")
    GL_SRC_ALPHA = missing_constant("GL_SRC_ALPHA")
    GL_SRC_COLOR = missing_constant("GL_SRC_COLOR")
    glBlendFunc = missing_gl_func("glBlendFunc")
    glDepthMask = missing_gl_func("glDepthMask")

from pykotor.gl import glm, mat4, quat, vec3, vec4
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.gl.scene import Scene
    from pykotor.gl.shader import Shader


logger = logging.getLogger(__name__)


class Model:
    def __init__(self, scene: Scene, root: Node):
        self._scene: Scene = scene
        self.root: Node = root

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        *,
        override_texture: str | None = None,
    ):
        self.root.draw(shader, transform, override_texture)

    def find(self, name: str) -> Node | None:
        nodes: list[Node] = [self.root]
        while nodes:
            node: Node = nodes.pop()
            if node.name.lower() == name.lower():
                return node
            nodes.extend(node.children)
        return None

    def all(self) -> list[Node]:
        all_nodes: list[Node] = []
        search: list[Node] = [self.root]
        while search:
            node: Node = search.pop()
            search.extend(node.children)
            all_nodes.append(node)
        return all_nodes

    def box(self) -> tuple[vec3, vec3]:
        return self.bounds(mat4())

    def bounds(self, transform: mat4) -> tuple[vec3, vec3]:
        """Calculate the bounding box of the model with the given transform."""
        min_point = vec3(100000, 100000, 100000)
        max_point = vec3(-100000, -100000, -100000)
        self._box_rec(self.root, transform, min_point, max_point)

        min_point.x -= 0.1
        min_point.y -= 0.1
        min_point.z -= 0.1
        max_point.x += 0.1
        max_point.y += 0.1
        max_point.z += 0.1

        return min_point, max_point

    def _box_rec(
        self,
        node: Node,
        transform: mat4,
        min_point: vec3,
        max_point: vec3,
    ):
        """Calculates bounding box of node and its children recursively.

        Call the 'box' function to get started here, don't call this directly.

        Args:
        ----
            node: {Node object whose bounding box is calculated}
            transform: {Transformation matrix to apply on node}
            min_point: {vec3 to store minimum point of bounding box}
            max_point: {vec3 to store maximum point of bounding box}.

        Processing Logic:
        ----------------
            - Apply transformation on node position and rotation
            - Iterate through vertices of node mesh if present
            - Transform vertices and update bounding box points
            - Recursively call function for each child node.
        """
        transform = transform * glm.translate(node._position)  # noqa: SLF001
        transform = transform * glm.mat4_cast(node._rotation)  # noqa: SLF001

        if node.mesh and node.render:
            vertex_count = len(node.mesh.vertex_data) // node.mesh.mdx_size
            for i in range(vertex_count):
                index = i * node.mesh.mdx_size + node.mesh.mdx_vertex
                data = node.mesh.vertex_data[index : index + 12]
                x, y, z = struct.unpack("fff", data)
                position = transform * vec3(x, y, z)
                min_point.x = min(min_point.x, position.x)
                min_point.y = min(min_point.y, position.y)
                min_point.z = min(min_point.z, position.z)
                max_point.x = max(max_point.x, position.x)
                max_point.y = max(max_point.y, position.y)
                max_point.z = max(max_point.z, position.z)

        for child in node.children:
            self._box_rec(child, transform, min_point, max_point)


class Node:
    def __init__(
        self,
        scene: Scene,
        parent: Node | None,
        name: str,
    ):
        self._scene: Scene = scene
        self._parent: Node | None = parent
        self.name: str = name
        self._transform: mat4 = mat4()
        self._position: vec3 = glm.vec3()
        self._rotation: quat = glm.quat()
        self.children: list[Node] = []
        self.render: bool = True
        self.mesh: Mesh | None = None

        self._recalc_transform()

    def root(self) -> Node | None:
        ancestor: Node | None = self._parent
        while ancestor:
            ancestor = ancestor._parent  # noqa: SLF001
        return ancestor

    def ancestors(self) -> list[Node]:
        ancestors: list[Node] = []
        ancestor: Node | None = self._parent
        while ancestor:
            ancestors.append(ancestor)
            ancestor = ancestor._parent  # noqa: SLF001
        return list(reversed(ancestors))

    def global_position(self) -> vec3:  # sourcery skip: class-extract-method
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)  # noqa: SLF001
            transform = transform * glm.mat4_cast(ancestor._rotation)  # noqa: SLF001
        position = vec3()
        glm.decompose(transform, vec3(), quat(), position, vec3(), vec4())  # pyright: ignore[reportCallIssue, reportArgumentType]
        return position

    def global_rotation(self) -> quat:
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)  # noqa: SLF001
            transform = transform * glm.mat4_cast(ancestor._rotation)  # noqa: SLF001
        rotation = quat()
        glm.decompose(transform, vec3(), rotation, vec3(), vec3(), vec4())  # pyright: ignore[reportCallIssue, reportArgumentType]
        return rotation

    def global_transform(self) -> mat4:
        ancestors: list[Node] = [*self.ancestors(), self]
        transform = mat4()
        for ancestor in ancestors:
            transform = transform * glm.translate(ancestor._position)  # noqa: SLF001
            transform = transform * glm.mat4_cast(ancestor._rotation)  # noqa: SLF001
        return transform

    def transform(self) -> mat4:
        return copy(self._transform)

    def _recalc_transform(self):
        self._transform = glm.translate(self._position) * glm.mat4_cast(quat(self._rotation))

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(self, x: float, y: float, z: float):
        self._position = vec3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> quat:
        return copy(self._rotation)

    def set_rotation(
        self,
        pitch: float,
        yaw: float,
        roll: float,
    ):
        self._rotation = quat(vec3(pitch, yaw, roll))
        self._recalc_transform()

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        override_texture: str | None = None,
    ):
        transform = transform * self._transform

        if self.mesh and self.render:
            self.mesh.draw(shader, transform, override_texture)

        for child in self.children:
            child.draw(shader, transform, override_texture=override_texture)


class Mesh:
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
        else:
            self._vao = 0
            self._vbo = 0
            self._ebo = 0

        self._face_count: int = len(element_data) // 2

    def draw(
        self,
        shader: Shader,
        transform: mat4,
        override_texture: str | None = None,
    ):
        # Defensive: ensure the shader program is bound before setting uniforms.
        # In some Qt/OpenGL driver combinations, the current program can be lost between calls.
        shader.use()
        shader.set_matrix4("model", transform)

        glActiveTexture(GL_TEXTURE0)
        diffuse_tex = self._scene.texture(override_texture or self.texture)
        diffuse_tex.use()

        # Material hints (TXI blending) influence how we draw “effect” meshes (e.g. light shafts).
        blend_mode = int(getattr(diffuse_tex, "blend_mode", 0))
        alpha_cutoff = float(getattr(diffuse_tex, "alpha_cutoff", 0.0))
        has_alpha = bool(getattr(diffuse_tex, "has_alpha", True))

        # Blend + depth-write selection:
        # - additive: no depth writes + additive blend (prevents “solid sheets” / incorrect occlusion)
        # - punchthrough: depth writes + alpha cutout
        # - default: depth writes + standard alpha blend
        if blend_mode == 1:
            glDepthMask(False)
            glBlendFunc(GL_SRC_ALPHA if has_alpha else GL_SRC_COLOR, GL_ONE)
            shader.set_float("alphaCutoff", 0.0)
        else:
            glDepthMask(True)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            shader.set_float("alphaCutoff", alpha_cutoff)

        glActiveTexture(GL_TEXTURE1)
        self._scene.texture(self.lightmap, lightmap=True).use()

        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)

        # Restore conservative defaults for the next draw.
        glDepthMask(True)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        shader.set_float("alphaCutoff", 0.0)

    def vertex_blob(self) -> bytes:
        """Generate an interleaved vertex blob for rendering.
        
        Returns a bytes object containing interleaved vertex data:
        - 3 floats for position (x, y, z)
        - 2 floats for diffuse UV (u, v)
        - 2 floats for lightmap UV (u, v)
        """
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
        """Return the index data for the mesh."""
        return self._index_data


class Cube:
    def __init__(
        self,
        scene: Scene,
        min_point: vec3 | None = None,
        max_point: vec3 | None = None,
    ):
        self._scene = scene

        min_point = vec3(-1.0, -1.0, -1.0) if min_point is None else min_point
        max_point = vec3(1.0, 1.0, 1.0) if max_point is None else max_point

        vertices = np.array(
            [
                min_point.x,
                min_point.y,
                max_point.z,
                max_point.x,
                min_point.y,
                max_point.z,
                max_point.x,
                max_point.y,
                max_point.z,
                min_point.x,
                max_point.y,
                max_point.z,
                min_point.x,
                min_point.y,
                min_point.z,
                max_point.x,
                min_point.y,
                min_point.z,
                max_point.x,
                max_point.y,
                min_point.z,
                min_point.x,
                max_point.y,
                min_point.z,
            ],
            dtype="float32",
        )

        elements = np.array(
            [0, 1, 2, 2, 3, 0, 1, 5, 6, 6, 2, 1, 7, 6, 5, 5, 4, 7, 4, 0, 3, 3, 7, 4, 4, 5, 1, 1, 0, 4, 3, 2, 6, 6, 7, 3],
            dtype="int16",
        )

        self.min_point: vec3 = min_point
        self.max_point: vec3 = max_point
        self._vertex_data = vertices
        self._index_data = elements
        self._face_count: int = len(elements)
        self._buffers_supported = False

        if HAS_PYOPENGL:
            try:
                self._vao: int = glGenVertexArrays(1)
                self._vbo: int = glGenBuffers(1)
                self._ebo: int = glGenBuffers(1)
                glBindVertexArray(self._vao)

                glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
                glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW)

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
                glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(elements) * 4, elements, GL_STATIC_DRAW)

                glEnableVertexAttribArray(1)
                glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glBindVertexArray(0)
                self._buffers_supported = True
            except gl_error.NullFunctionError:
                logger.warning(
                    "OpenGL buffer objects are unavailable; falling back to CPU-only cube bounds."
                )
                self._face_count = 0
                self._vao = 0
                self._vbo = 0
                self._ebo = 0
        else:
            self._vao = 0
            self._vbo = 0
            self._ebo = 0


    def draw(self, shader: Shader, transform: mat4):
        if not self._buffers_supported:
            return
        if not HAS_PYOPENGL:
            raise gl_error.NullFunctionError("PyOpenGL is unavailable.")

        shader.set_matrix4("model", transform)
        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)
    
    def vertex_blob(self) -> bytes:
        """Interleaved vertex data (position only)."""
        vertex_count = len(self._vertex_data) // 3
        blob = np.zeros((vertex_count, 7), dtype=np.float32)
        blob[:, 0:3] = self._vertex_data.reshape(vertex_count, 3)
        return blob.tobytes()

    @property
    def index_data(self) -> bytes:
        return self._index_data.tobytes()


class Boundary:
    def __init__(
        self,
        scene: Scene,
        vertices: list[Vector3],
    ):
        self._scene: Scene = scene

        vertices_np, elements_np = self._build_nd(vertices)
        self._vertex_data: np.ndarray = vertices_np
        self._index_data: np.ndarray = elements_np
        self._face_count: int = len(elements_np)
        self._buffers_supported = False

        if HAS_PYOPENGL:
            try:
                self._vao = glGenVertexArrays(1)
                self._vbo = glGenBuffers(1)
                self._ebo = glGenBuffers(1)
                glBindVertexArray(self._vao)

                glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
                glBufferData(GL_ARRAY_BUFFER, len(vertices_np) * 4, vertices_np, GL_STATIC_DRAW)

                glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
                glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(elements_np) * 4, elements_np, GL_STATIC_DRAW)

                glEnableVertexAttribArray(1)
                glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glBindVertexArray(0)
                self._buffers_supported = True
            except gl_error.NullFunctionError:
                logger.warning(
                    "OpenGL buffer objects are unavailable; boundary rendering disabled."
                )
                self._face_count = 0
                self._vao = 0
                self._vbo = 0
                self._ebo = 0
        else:
            self._vao = 0
            self._vbo = 0
            self._ebo = 0

    @classmethod
    def from_circle(
        cls,
        scene: Scene,
        radius: float,
        smoothness: int = 10,
    ) -> Boundary:
        vertices: list[Vector3] = []
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2)
            y = math.sin(i / smoothness * math.pi / 2)
            vertices.append(Vector3(x, y, 0) * radius)
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2 + math.pi / 2)
            y = math.sin(i / smoothness * math.pi / 2 + math.pi / 2)
            vertices.append(Vector3(x, y, 0) * radius)
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2 + math.pi / 2 * 2)
            y = math.sin(i / smoothness * math.pi / 2 + math.pi / 2 * 2)
            vertices.append(Vector3(x, y, 0) * radius)
        for i in range(smoothness):
            x = math.cos(i / smoothness * math.pi / 2 + math.pi / 2 * 3)
            y = math.sin(i / smoothness * math.pi / 2 + math.pi / 2 * 3)
            vertices.append(Vector3(x, y, 0) * radius)
        return Boundary(scene, vertices)

    def draw(self, shader: Shader, transform: mat4):
        if not self._buffers_supported:
            return
        if not HAS_PYOPENGL:
            raise gl_error.NullFunctionError("PyOpenGL is unavailable.")

        shader.set_matrix4("model", transform)
        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, self._face_count, GL_UNSIGNED_SHORT, None)
    
    def vertex_blob(self) -> bytes:
        """Interleaved vertex data (position only)."""
        vertex_count = len(self._vertex_data) // 3
        blob = np.zeros((vertex_count, 7), dtype=np.float32)
        blob[:, 0:3] = self._vertex_data.reshape(vertex_count, 3)
        return blob.tobytes()

    @property
    def index_data(self) -> bytes:
        return self._index_data.tobytes()

    def _build_nd(self, vertices: list[Vector3]) -> tuple[np.ndarray, np.ndarray]:
        vertices_np: list[float] = []
        for vertex in vertices:
            vertices_np.extend([*vertex, *Vector3(vertex.x, vertex.y, vertex.z + 2)])

        faces_np: list[int] = []
        count = len(vertices) * 2
        for i, _vertex in enumerate(vertices):
            index1 = i * 2
            index2 = i * 2 + 2 if i * 2 + 2 < count else 0
            index3 = i * 2 + 1
            index4 = (i * 2 + 2) + 1 if (i * 2 + 2) + 1 < count else 1
            faces_np.extend([index1, index2, index3, index2, index4, index3])
        return np.array(vertices_np, dtype="float32"), np.array(faces_np, dtype="int16")


class Empty:
    def __init__(self, scene: Scene):
        self._scene: Scene = scene

    def draw(self, shader: Shader, transform: mat4):
        ...
