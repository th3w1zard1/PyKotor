from __future__ import annotations

from dataclasses import dataclass

import glm
import moderngl  # type: ignore[import]
import numpy as np

from glm import mat4

from pykotor.gl.scene import Scene
from pykotor.gl.scene.render_object import RenderObject
from pykotor.gl.shader.texture import Texture


MODERN_VS = """
#version 330 core
layout (location = 0) in vec3 in_position;
layout (location = 1) in vec2 in_diffuse_uv;
layout (location = 2) in vec2 in_lightmap_uv;

out vec2 v_diffuse;
out vec2 v_lightmap;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    gl_Position = projection * view * model * vec4(in_position, 1.0);
    v_diffuse = in_diffuse_uv;
    v_lightmap = in_lightmap_uv;
}
"""

MODERN_FS = """
#version 330 core
in vec2 v_diffuse;
in vec2 v_lightmap;

uniform sampler2D diffuse;
uniform sampler2D lightmap;
uniform int enableLightmap;

out vec4 FragColor;

void main() {
    vec4 diffuseColor = texture(diffuse, v_diffuse);
    vec4 lightmapColor = texture(lightmap, v_lightmap);
    if (enableLightmap == 1) {
        FragColor = mix(diffuseColor, lightmapColor, 0.5);
    } else {
        FragColor = diffuseColor;
    }
}
"""

PLAIN_VS = """
#version 330 core
layout (location = 0) in vec3 in_position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    gl_Position = projection * view * model * vec4(in_position, 1.0);
}
"""

PLAIN_FS = """
#version 330 core
uniform vec4 color;
out vec4 FragColor;
void main() {
    FragColor = color;
}
"""


def _mat4_bytes(matrix: mat4) -> bytes:
    ptr = glm.value_ptr(matrix)
    return np.ctypeslib.as_array(ptr, shape=(16,)).astype(np.float32).tobytes()


@dataclass
class ModernGLMesh:
    ctx: moderngl.Context
    mesh_id: int
    vbo: moderngl.Buffer
    ibo: moderngl.Buffer
    vao_cache: dict[int, moderngl.VertexArray]

    @classmethod
    def from_mesh(cls, ctx: moderngl.Context, mesh) -> ModernGLMesh:
        vertex_blob = mesh.vertex_blob()
        if not vertex_blob:
            vertex_blob = np.zeros((1, 7), dtype=np.float32).tobytes()
        vbo = ctx.buffer(vertex_blob)
        ibo = ctx.buffer(mesh.index_data)
        return cls(ctx=ctx, mesh_id=id(mesh), vbo=vbo, ibo=ibo, vao_cache={})

    def vao(self, program: moderngl.Program) -> moderngl.VertexArray:
        key = id(program)
        vao = self.vao_cache.get(key)
        if vao is None:
            vao = self.ctx.vertex_array(
                program,
                [(self.vbo, "3f 2f 2f", "in_position", "in_diffuse_uv", "in_lightmap_uv")],
                index_buffer=self.ibo,
                index_element_size=2,
            )
            self.vao_cache[key] = vao
        return vao


class ModernTextureCache:
    def __init__(self, ctx: moderngl.Context, scene: Scene):
        self.ctx = ctx
        self.scene = scene
        self._cache: dict[int, moderngl.Texture] = {}

    def _key(self, tex: Texture) -> int:
        return id(tex)

    def get(self, name: str, *, lightmap: bool = False) -> moderngl.Texture:
        tex = self.scene.texture(name, lightmap=lightmap)
        key = self._key(tex)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        modern = tex.ensure_modern(self.ctx)
        self._cache[key] = modern
        return modern


class ModernGLRenderer:
    """Drop-in renderer replacement using moderngl for drastically lower CPU overhead."""

    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.program = self.ctx.program(vertex_shader=MODERN_VS, fragment_shader=MODERN_FS)
        self.plain_program = self.ctx.program(vertex_shader=PLAIN_VS, fragment_shader=PLAIN_FS)
        self._mesh_cache: dict[int, ModernGLMesh] = {}
        self._texture_cache: ModernTextureCache | None = None

    def _textures(self, scene: Scene) -> ModernTextureCache:
        if self._texture_cache is None:
            self._texture_cache = ModernTextureCache(self.ctx, scene)
        return self._texture_cache

    def _mesh(self, mesh) -> ModernGLMesh:
        key = id(mesh)
        cached = self._mesh_cache.get(key)
        if cached is None:
            cached = ModernGLMesh.from_mesh(self.ctx, mesh)
            self._mesh_cache[key] = cached
        return cached

    def _set_transforms(self, program: moderngl.Program, view: mat4, projection: mat4) -> None:
        program["view"].write(_mat4_bytes(view))
        program["projection"].write(_mat4_bytes(projection))

    def render(self, scene: Scene) -> None:
        from pykotor.gl.scene.scene_cache import SceneCache  # local import to avoid cycle

        SceneCache.build_cache(scene)
        if scene._objects_dirty or scene._cached_regular_objects is None:
            scene._rebuild_object_caches()

        self.ctx.clear(0.5, 0.5, 1.0, 1.0)
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)

        view = scene.camera.view()
        projection = scene.camera.projection()
        texture_cache = self._textures(scene)

        # Render regular objects (models)
        self.program["enableLightmap"].value = 1 if scene.use_lightmap else 0
        self._set_transforms(self.program, view, projection)

        if scene._cached_regular_objects:
            for obj in scene._cached_regular_objects:
                if scene.enable_frustum_culling and not scene._is_object_visible(obj):
                    continue
                self._draw_render_object(scene, obj, texture_cache)

        # Render special objects (icons) with plain shader
        self.ctx.enable(moderngl.BLEND)
        self._set_transforms(self.plain_program, view, projection)
        self.plain_program["color"].write(np.array([0.0, 0.0, 1.0, 0.4], dtype=np.float32).tobytes())

        if scene._cached_special_objects:
            for obj in scene._cached_special_objects:
                if scene.enable_frustum_culling and not scene._is_object_visible(obj):
                    continue
                self._draw_render_object_plain(scene, obj)

        # Draw selection bounding boxes (red)
        self.plain_program["color"].write(np.array([1.0, 0.0, 0.0, 0.4], dtype=np.float32).tobytes())
        for obj in scene.selection:
            cube = obj.cube(scene)
            if cube:
                self._draw_cube(cube, obj.transform())

        # Draw selection boundaries (green)
        self.ctx.disable(moderngl.CULL_FACE)
        self.plain_program["color"].write(np.array([0.0, 1.0, 0.0, 0.8], dtype=np.float32).tobytes())
        for obj in scene.selection:
            boundary = obj.boundary(scene)
            if boundary:
                self._draw_boundary(boundary, obj.transform())

        # Draw sound/encounter/trigger boundaries if not hidden
        if not scene.hide_sound_boundaries and scene._cached_sound_objects:
            for obj in scene._cached_sound_objects:
                if not scene.enable_frustum_culling or scene._is_object_visible(obj):
                    boundary = obj.boundary(scene)
                    if boundary:
                        self._draw_boundary(boundary, obj.transform())

        if not scene.hide_encounter_boundaries and scene._cached_encounter_objects:
            for obj in scene._cached_encounter_objects:
                if not scene.enable_frustum_culling or scene._is_object_visible(obj):
                    boundary = obj.boundary(scene)
                    if boundary:
                        self._draw_boundary(boundary, obj.transform())

        if not scene.hide_trigger_boundaries and scene._cached_trigger_objects:
            for obj in scene._cached_trigger_objects:
                if not scene.enable_frustum_culling or scene._is_object_visible(obj):
                    boundary = obj.boundary(scene)
                    if boundary:
                        self._draw_boundary(boundary, obj.transform())

        # Draw cursor if enabled
        if scene.show_cursor:
            self.plain_program["color"].write(np.array([1.0, 0.0, 0.0, 0.4], dtype=np.float32).tobytes())
            self._draw_render_object_plain(scene, scene.cursor)

    def _draw_render_object(
        self,
        scene: Scene,
        render_object: RenderObject,
        texture_cache: ModernTextureCache,
    ) -> None:
        model = scene.model(render_object.model)
        transform = render_object.transform()
        override_texture = render_object.override_texture
        self._draw_node(model.root, transform, override_texture, texture_cache)  # type: ignore[arg-type]

    def _draw_node(
        self,
        node,
        parent_transform: mat4,
        override_texture: str | None,
        texture_cache: ModernTextureCache,
    ) -> None:
        local_transform = parent_transform * node._transform
        if node.mesh and node.render:
            mesh = node.mesh
            vao = self._mesh(mesh).vao(self.program)
            self.program["model"].write(_mat4_bytes(local_transform))

            diffuse_name = override_texture if override_texture else mesh.texture
            diffuse_tex = texture_cache.get(diffuse_name)
            lightmap_tex = texture_cache.get(mesh.lightmap, lightmap=True)

            diffuse_tex.use(location=0)
            lightmap_tex.use(location=1)
            self.program["enableLightmap"].value = 1 if mesh.lightmap != "NULL" else 0
            vao.render()

        for child in node.children:
            self._draw_node(child, local_transform, override_texture, texture_cache)

    def _draw_render_object_plain(
        self,
        scene: Scene,
        render_object: RenderObject,
    ) -> None:
        """Draw a render object using the plain shader (for icons, cursor, etc.)."""
        model = scene.model(render_object.model)
        transform = render_object.transform()
        self._draw_node_plain(model.root, transform)  # type: ignore[arg-type]

    def _draw_node_plain(
        self,
        node,
        parent_transform: mat4,
    ) -> None:
        """Draw a node using the plain shader."""
        local_transform = parent_transform * node._transform
        if node.mesh and node.render:
            mesh = node.mesh
            vao = self._mesh(mesh).vao(self.plain_program)
            self.plain_program["model"].write(_mat4_bytes(local_transform))
            vao.render()

        for child in node.children:
            self._draw_node_plain(child, local_transform)

    def _draw_cube(self, cube, transform: mat4) -> None:
        """Draw a cube using the plain shader."""
        # Cubes are typically simple geometry - for now, skip if not implemented
        # This would require implementing cube rendering in ModernGL
        pass

    def _draw_boundary(self, boundary, transform: mat4) -> None:
        """Draw a boundary using the plain shader."""
        # Boundaries are typically simple geometry - for now, skip if not implemented
        # This would require implementing boundary rendering in ModernGL
        pass

