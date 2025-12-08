from __future__ import annotations

import math

from copy import copy
from typing import TYPE_CHECKING, Any, Callable, Union

import glm

from glm import mat4, quat, vec3, vec4

from pykotor.gl.models.mdl import Cube, Empty

if TYPE_CHECKING:
    from pykotor.gl.models.mdl import Boundary
    from pykotor.gl.scene.scene import Scene


class RenderObject:
    """Render object with cached bounding sphere for efficient frustum culling.
    
    Performance optimization: Bounding sphere radius and center are cached to avoid
    expensive recalculation during frustum culling. The cache is invalidated when
    position changes or cube is reset.
    
    Reference: Standard game engine practice (Unity BoundingSphere, UE4 FBoundingSphere)
    """
    
    __slots__ = (
        "model", "children", "_transform", "_position", "_rotation",
        "_cube", "_boundary", "gen_boundary", "data", "override_texture",
        "_cached_radius", "_cached_center", "_bounds_dirty"
    )
    
    def __init__(
        self,
        model: str,
        position: vec3 | None = None,
        rotation: vec3 | None = None,
        *,
        data: Any = None,
        gen_boundary: Callable[[], Boundary] | None = None,
        override_texture: str | None = None,
    ):
        self.model: str = model
        self.children: list[RenderObject] = []
        self._transform: mat4 = mat4()
        self._position: vec3 = vec3() if position is None else position
        self._rotation: vec3 = vec3() if rotation is None else rotation
        self._cube: Cube | None = None
        self._boundary: Boundary | Empty | None = None
        self.gen_boundary: Callable[[], Boundary] | None = gen_boundary
        self.data: Any = data
        self.override_texture: str | None = override_texture
        
        # Cached bounding sphere for frustum culling
        self._cached_radius: float = -1.0  # -1 means not computed
        self._cached_center: vec3 | None = None
        self._bounds_dirty: bool = True

        self._recalc_transform()

    def transform(self) -> mat4:
        return self._transform

    def set_transform(
        self,
        transform: mat4,
    ):
        self._transform = transform
        rotation = quat()
        scale = vec3()
        skew = vec3()
        perspective = vec4()
        glm.decompose(transform, scale, rotation, self._position, skew, perspective)  # pyright: ignore[reportArgumentType, reportCallIssue]
        self._rotation = glm.eulerAngles(rotation)
        self._bounds_dirty = True

    def _recalc_transform(self):
        self._transform = mat4() * glm.translate(self._position)
        self._transform = self._transform * glm.mat4_cast(quat(self._rotation))

    def position(self) -> vec3:
        return copy(self._position)

    def set_position(
        self,
        x: float,
        y: float,
        z: float,
    ):
        if self._position.x == x and self._position.y == y and self._position.z == z:
            return

        self._position = vec3(x, y, z)
        self._recalc_transform()
        self._bounds_dirty = True

    def rotation(self) -> vec3:
        return copy(self._rotation)

    def set_rotation(
        self,
        x: float,
        y: float,
        z: float,
    ):
        if self._rotation.x == x and self._rotation.y == y and self._rotation.z == z:
            return

        self._rotation = vec3(x, y, z)
        self._recalc_transform()
        self._bounds_dirty = True

    def reset_cube(self):
        self._cube = None
        self._bounds_dirty = True
        self._cached_radius = -1.0
        self._cached_center = None

    def cube(
        self,
        scene: Scene,
    ) -> Cube:
        if not self._cube:
            min_point = vec3(10000, 10000, 10000)
            max_point = vec3(-10000, -10000, -10000)
            self._cube_rec(scene, mat4(), self, min_point, max_point)
            self._cube = Cube(scene, min_point, max_point)
            self._bounds_dirty = True
        return self._cube

    def radius(
        self,
        scene: Scene,
    ) -> float:
        cube = self.cube(scene)
        return max(
            abs(cube.min_point.x),
            abs(cube.min_point.y),
            abs(cube.min_point.z),
            abs(cube.max_point.x),
            abs(cube.max_point.y),
            abs(cube.max_point.z),
        )

    def bounding_sphere(
        self,
        scene: Scene,
        default_radius: float = 5.0,
    ) -> tuple[vec3, float]:
        """Get cached bounding sphere center and radius for frustum culling.
        
        This is optimized for fast access during rendering - values are cached
        and only recomputed when the object's bounds change.
        
        Args:
            scene: The scene for model lookups.
            default_radius: Default radius if bounds cannot be computed.
            
        Returns:
            Tuple of (center, radius) for the bounding sphere.
        """
        # Fast path: return cached values if valid
        if not self._bounds_dirty and self._cached_radius >= 0 and self._cached_center is not None:
            # Update center position (cheap operation)
            pos = self._position
            return vec3(
                pos.x + self._cached_center.x,
                pos.y + self._cached_center.y,
                pos.z + self._cached_center.z,
            ), self._cached_radius
        
        # Slow path: compute bounding sphere
        try:
            cube = self.cube(scene)
            min_pt = cube.min_point
            max_pt = cube.max_point
            
            # Calculate bounding sphere from AABB
            dx = max_pt.x - min_pt.x
            dy = max_pt.y - min_pt.y
            dz = max_pt.z - min_pt.z
            
            # Radius is half the diagonal of the AABB
            self._cached_radius = math.sqrt(dx * dx + dy * dy + dz * dz) / 2.0
            
            # Center offset relative to object position
            self._cached_center = vec3(
                (min_pt.x + max_pt.x) / 2.0,
                (min_pt.y + max_pt.y) / 2.0,
                (min_pt.z + max_pt.z) / 2.0,
            )
            self._bounds_dirty = False
            
            # Return world-space center
            pos = self._position
            return vec3(
                pos.x + self._cached_center.x,
                pos.y + self._cached_center.y,
                pos.z + self._cached_center.z,
            ), self._cached_radius
            
        except Exception:  # noqa: BLE001
            # Fallback to default values
            self._cached_radius = default_radius
            self._cached_center = vec3(0, 0, 0)
            self._bounds_dirty = False
            return self._position, default_radius

    def _cube_rec(
        self,
        scene: Scene,
        transform: mat4,
        obj: RenderObject,
        min_point: vec3,
        max_point: vec3,
    ):
        obj_min, obj_max = scene.model(obj.model).bounds(transform)
        min_point.x = min(min_point.x, obj_min.x, obj_max.x)
        min_point.y = min(min_point.y, obj_min.y, obj_max.y)
        min_point.z = min(min_point.z, obj_min.z, obj_max.z)
        max_point.x = max(max_point.x, obj_min.x, obj_max.x)
        max_point.y = max(max_point.y, obj_min.y, obj_max.y)
        max_point.z = max(max_point.z, obj_min.z, obj_max.z)
        for child in obj.children:
            self._cube_rec(scene, transform * child.transform(), child, min_point, max_point)

    def reset_boundary(self):
        self._boundary = None

    def boundary(
        self,
        scene: Scene,
    ) -> Union[Boundary, Empty]:
        if self._boundary is None:
            self._boundary = Empty(scene) if self.gen_boundary is None else self.gen_boundary()
        return self._boundary
