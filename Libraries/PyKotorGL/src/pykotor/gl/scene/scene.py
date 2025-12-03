from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import glm

from OpenGL.GL import glReadPixels
from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_BLEND, GL_COLOR_BUFFER_BIT, GL_CULL_FACE, GL_DEPTH_BUFFER_BIT, GL_DEPTH_COMPONENT, glClear, glClearColor, glDisable, glEnable
from OpenGL.raw.GL.VERSION.GL_1_2 import GL_BGRA, GL_UNSIGNED_INT_8_8_8_8
from glm import mat4, vec3, vec4

from pykotor.extract.installation import SearchLocation
from pykotor.gl.models.mdl import Model
from pykotor.gl.scene.frustum import CullingStats, Frustum
from pykotor.gl.scene.scene_base import SceneBase
from pykotor.gl.scene.scene_cache import SceneCache
from pykotor.gl.shader import KOTOR_FSHADER, KOTOR_VSHADER, PICKER_FSHADER, PICKER_VSHADER, PLAIN_FSHADER, PLAIN_VSHADER, Shader
from pykotor.resource.formats.lyt.lyt_data import LYTRoom
from pykotor.resource.generics.git import GITCamera, GITCreature, GITDoor, GITEncounter, GITInstance, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.gl.models.mdl import Model
    from pykotor.gl.scene import RenderObject

T = TypeVar("T")
SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class Scene(SceneBase):
    """Optimized scene renderer with caching and batched operations.
    
    Performance optimizations:
    - Cached object categorization (avoids list comprehensions every frame)
    - Cached view/projection matrices (set once per frame, not per object)
    - Cached bounding spheres for frustum culling
    - Incremental cache building (only rebuilds when dirty)
    - Lazy cursor position calculation
    
    Reference implementations:
    - reone: src/graphics/renderpipeline.cpp
    - kotor.js: src/engine/renderer.ts
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.picker_shader: Shader = Shader(PICKER_VSHADER, PICKER_FSHADER)
        self.plain_shader: Shader = Shader(PLAIN_VSHADER, PLAIN_FSHADER)
        self.shader: Shader = Shader(KOTOR_VSHADER, KOTOR_FSHADER)
        
        # Frustum culling
        self.frustum: Frustum = Frustum()
        self.culling_stats: CullingStats = CullingStats()
        self.enable_frustum_culling: bool = True
        # Default bounding sphere radius for objects without computed bounds
        self.default_cull_radius: float = 5.0
        
        # Cached object lists for render batching (rebuilt when objects change)
        self._cached_regular_objects: list[RenderObject] | None = None
        self._cached_special_objects: list[RenderObject] | None = None
        self._cached_sound_objects: list[RenderObject] | None = None
        self._cached_encounter_objects: list[RenderObject] | None = None
        self._cached_trigger_objects: list[RenderObject] | None = None
        self._objects_dirty: bool = True
        self._last_objects_count: int = 0
        
        # Cached camera matrices (set once per frame, used by multiple shaders)
        self._cached_view: mat4 | None = None
        self._cached_projection: mat4 | None = None
    
    def _invalidate_object_cache(self):
        """Mark object caches as dirty. Call when objects are added/removed."""
        self._objects_dirty = True
        self._cached_regular_objects = None
        self._cached_special_objects = None
        self._cached_sound_objects = None
        self._cached_encounter_objects = None
        self._cached_trigger_objects = None
    
    def _rebuild_object_caches(self):
        """Rebuild cached object lists for efficient iteration."""
        if not self._objects_dirty and len(self.objects) == self._last_objects_count:
            return
        
        special_models = frozenset(self.SPECIAL_MODELS)
        
        regular = []
        special = []
        sounds = []
        encounters = []
        triggers = []
        
        for obj in self.objects.values():
            model = obj.model
            if model in special_models:
                special.append(obj)
                if model == "sound":
                    sounds.append(obj)
                elif model == "encounter":
                    encounters.append(obj)
                elif model == "trigger":
                    triggers.append(obj)
            else:
                regular.append(obj)
        
        self._cached_regular_objects = regular
        self._cached_special_objects = special
        self._cached_sound_objects = sounds
        self._cached_encounter_objects = encounters
        self._cached_trigger_objects = triggers
        self._objects_dirty = False
        self._last_objects_count = len(self.objects)
    
    def _update_camera_matrices(self):
        """Update cached camera matrices.
        
        Camera.view() and Camera.projection() already have internal caching
        that only recomputes when dirty. We just store the results for use
        in multiple shaders per frame.
        """
        # Camera has internal dirty tracking, so these calls are cheap when unchanged
        self._cached_view = self.camera.view()
        self._cached_projection = self.camera.projection()

    def render(self):
        # Poll for completed async resources (non-blocking) - MAIN PROCESS ONLY
        self.poll_async_resources()
        
        # ALWAYS build cache - it updates object positions for existing objects!
        # SceneCache.build_cache updates positions (set_position/set_rotation) 
        # even for objects already in scene.objects. Skipping this causes:
        # 1. Objects not moving when dragged
        # 2. Camera snapping not working until rotation
        SceneCache.build_cache(self)
        
        # Rebuild object lists if objects changed (cheap check)
        if self._objects_dirty or len(self.objects) != self._last_objects_count:
            self._rebuild_object_caches()
        
        # Update camera matrices once per frame
        self._update_camera_matrices()
        
        # Update frustum for culling
        if self.enable_frustum_culling:
            self.frustum.update_from_camera(self.camera)
        
        if self.enable_frustum_culling:
            self.culling_stats.reset()

        # Prepare GL state and main shader
        self._prepare_gl_and_shader_optimized()
        self.shader.set_bool("enableLightmap", self.use_lightmap)
        
        # Render regular objects (models)
        assert self._cached_regular_objects is not None
        identity = mat4()  # Create once, reuse
        for obj in self._cached_regular_objects:
            if self.enable_frustum_culling and not self._is_object_visible(obj):
                self.culling_stats.record_object(visible=False)
                continue
            self.culling_stats.record_object(visible=True)
            self._render_object(self.shader, obj, identity)

        # Setup plain shader for special objects (once)
        glEnable(GL_BLEND)
        self.plain_shader.use()
        assert self._cached_view is not None and self._cached_projection is not None
        self.plain_shader.set_matrix4("view", self._cached_view)
        self.plain_shader.set_matrix4("projection", self._cached_projection)
        self.plain_shader.set_vector4("color", vec4(0.0, 0.0, 1.0, 0.4))
        
        # Render special objects (icons)
        assert self._cached_special_objects is not None
        for obj in self._cached_special_objects:
            if self.enable_frustum_culling and not self._is_object_visible(obj):
                self.culling_stats.record_object(visible=False)
                continue
            self.culling_stats.record_object(visible=True)
            self._render_object(self.plain_shader, obj, identity)

        # Draw bounding box for selected objects
        self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
        for obj in self.selection:
            obj.cube(self).draw(self.plain_shader, obj.transform())

        # Draw boundary for selected objects
        glDisable(GL_CULL_FACE)
        self.plain_shader.set_vector4("color", vec4(0.0, 1.0, 0.0, 0.8))
        for obj in self.selection:
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        # Draw non-selected boundaries (only if visible and enabled)
        if not self.hide_sound_boundaries:
            assert self._cached_sound_objects is not None
            for obj in self._cached_sound_objects:
                if not self.enable_frustum_culling or self._is_object_visible(obj):
                    obj.boundary(self).draw(self.plain_shader, obj.transform())
        
        if not self.hide_encounter_boundaries:
            assert self._cached_encounter_objects is not None
            for obj in self._cached_encounter_objects:
                if not self.enable_frustum_culling or self._is_object_visible(obj):
                    obj.boundary(self).draw(self.plain_shader, obj.transform())
        
        if not self.hide_trigger_boundaries:
            assert self._cached_trigger_objects is not None
            for obj in self._cached_trigger_objects:
                if not self.enable_frustum_culling or self._is_object_visible(obj):
                    obj.boundary(self).draw(self.plain_shader, obj.transform())

        if self.show_cursor:
            self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
            self._render_object(self.plain_shader, self.cursor, identity)
        
        # End frame statistics
        if self.enable_frustum_culling:
            self.culling_stats.end_frame()
    
    def _prepare_gl_and_shader_optimized(self):
        """Optimized GL state preparation using cached matrices."""
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # type: ignore[]
        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        self.shader.use()
        
        # Use cached matrices instead of recalculating
        assert self._cached_view is not None and self._cached_projection is not None
        self.shader.set_matrix4("view", self._cached_view)
        self.shader.set_matrix4("projection", self._cached_projection)
    
    def _is_object_visible(self, obj: RenderObject) -> bool:
        """Check if an object is visible within the frustum.
        
        Uses cached bounding sphere from RenderObject for efficiency.
        
        Args:
            obj: The render object to test.
            
        Returns:
            True if the object should be rendered.
        """
        # Use cached bounding sphere from RenderObject
        center, radius = obj.bounding_sphere(self, self.default_cull_radius)
        return self.frustum.sphere_in_frustum(center, radius)

    def should_hide_obj(
        self,
        obj: RenderObject,
    ) -> bool:
        result = False
        if isinstance(obj.data, GITCreature) and self.hide_creatures:
            result = True
        elif isinstance(obj.data, GITPlaceable) and self.hide_placeables:
            result = True
        elif isinstance(obj.data, GITDoor) and self.hide_doors:
            result = True
        elif isinstance(obj.data, GITTrigger) and self.hide_triggers:
            result = True
        elif isinstance(obj.data, GITEncounter) and self.hide_encounters:
            result = True
        elif isinstance(obj.data, GITWaypoint) and self.hide_waypoints:
            result = True
        elif isinstance(obj.data, GITSound) and self.hide_sounds:
            result = True
        elif isinstance(obj.data, GITStore) and self.hide_sounds:
            result = True
        elif isinstance(obj.data, GITCamera) and self.hide_cameras:
            result = True
        return result

    def _render_object(
        self,
        shader: Shader,
        obj: RenderObject,
        transform: mat4,
    ):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        transform = transform * obj.transform()
        model.draw(shader, transform, override_texture=obj.override_texture)

        for child in obj.children:
            self._render_object(shader, child, transform)

    def picker_render(self):
        """Render scene for object picking with unique colors per object.
        
        Optimized to use cached matrices and enumerate for O(1) index access.
        """
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # pyright: ignore[reportOperatorIssue]

        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)

        self.picker_shader.use()
        
        # Use cached matrices if available, otherwise compute
        if self._cached_view is not None and self._cached_projection is not None:
            self.picker_shader.set_matrix4("view", self._cached_view)
            self.picker_shader.set_matrix4("projection", self._cached_projection)
        else:
            self.picker_shader.set_matrix4("view", self.camera.view())
            self.picker_shader.set_matrix4("projection", self.camera.projection())
        
        # Use enumerate instead of list.index() which is O(n) per call
        identity = mat4()
        instances: list[RenderObject] = list(self.objects.values())
        for idx, obj in enumerate(instances):
            r: int = idx & 0xFF
            g: int = (idx >> 8) & 0xFF
            b: int = (idx >> 16) & 0xFF
            color = vec3(r / 0xFF, g / 0xFF, b / 0xFF)
            self.picker_shader.set_vector3("colorId", color)
            self._picker_render_object(obj, identity)

    def _picker_render_object(self, obj: RenderObject, transform: mat4):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        model.draw(self.picker_shader, transform * obj.transform())
        for child in obj.children:
            self._picker_render_object(child, obj.transform())

    def pick(
        self,
        x: float,
        y: float,
    ) -> RenderObject | None:
        self.picker_render()
        pixel: int = glReadPixels(x, y, 1, 1, GL_BGRA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8  # type: ignore[]
        instances: list[RenderObject] = list(self.objects.values())
        return instances[pixel] if pixel != 0xFFFFFF else None  # noqa: PLR2004

    def select(
        self,
        target: RenderObject | GITInstance,
        *,
        clear_existing: bool = True,
    ):
        if clear_existing:
            self.selection.clear()

        SceneCache.build_cache(self)
        actual_target: RenderObject | None = None
        if isinstance(target, GITInstance):
            for obj in self.objects.values():
                if obj.data is target:
                    actual_target = obj
                    break
        else:
            actual_target = target

        if actual_target is not None:
            self.selection.append(actual_target)

    def screen_to_world(
        self,
        x: int,
        y: int,
    ) -> Vector3:
        """Convert screen coordinates to world coordinates.
        
        Optimized to:
        - Use cached room objects list
        - Use cached view/projection matrices
        - Minimize GL state changes
        """
        # Prepare GL state efficiently
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # type: ignore[]
        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        self.shader.use()
        
        # Use cached matrices if available
        if self._cached_view is not None and self._cached_projection is not None:
            view = self._cached_view
            projection = self._cached_projection
        else:
            view = self.camera.view()
            projection = self.camera.projection()
        
        self.shader.set_matrix4("view", view)
        self.shader.set_matrix4("projection", projection)
        
        # Only render room geometry for depth calculation
        identity = mat4()
        for obj in self.objects.values():
            if isinstance(obj.data, LYTRoom):
                self._render_object(self.shader, obj, identity)

        zpos = glReadPixels(
            x,
            self.camera.height - y,
            1,
            1,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
        )[0][0]  # type: ignore[]
        
        cursor: vec3 = glm.unProject(
            vec3(x, self.camera.height - y, zpos),
            view,
            projection,
            vec4(0, 0, self.camera.width, self.camera.height),
        )
        return Vector3(cursor.x, cursor.y, cursor.z)

    def _prepare_gl_and_shader(self):
        """Legacy method for backward compatibility."""
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # type: ignore[]
        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())

