from __future__ import annotations

import math

from typing import TYPE_CHECKING, Literal, Union

import glm

from glm import mat4, vec3

if TYPE_CHECKING:
    from utility.common.geometry import Vector3


class Camera:
    """Camera with cached view/projection matrices.
    
    Performance optimization: view() and projection() matrix calculations are
    cached and only recomputed when camera parameters change. This provides
    significant speedup when matrices are accessed multiple times per frame.
    
    All position/orientation attributes (x, y, z, pitch, yaw, distance) use
    properties that automatically invalidate the view cache when modified.
    Similarly, width/height/fov invalidate the projection cache.
    
    Reference: Standard game engine practice (Unity, Unreal use similar caching)
    """
    
    __slots__ = (
        "_x", "_y", "_z", "_width", "_height", "_pitch", "_yaw", "_distance", "_fov",
        "_cached_view", "_cached_projection", "_view_dirty", "_projection_dirty"
    )
    
    def __init__(self):
        # Initialize internal attributes directly to avoid property setters
        # triggering invalidation during construction
        self._x: float = 40.0
        self._y: float = 130.0
        self._z: float = 0.5
        self._width: int = 1920
        self._height: int = 1080
        self._pitch: float = math.pi / 2
        self._yaw: float = 0.0
        self._distance: float = 10.0
        self._fov: float = 90.0
        
        # Cached matrices
        self._cached_view: mat4 | None = None
        self._cached_projection: mat4 | None = None
        self._view_dirty: bool = True
        self._projection_dirty: bool = True
    
    # Position properties - invalidate view cache on change
    @property
    def x(self) -> float:
        return self._x
    
    @x.setter
    def x(self, value: float) -> None:
        if self._x != value:
            self._x = value
            self._view_dirty = True
    
    @property
    def y(self) -> float:
        return self._y
    
    @y.setter
    def y(self, value: float) -> None:
        if self._y != value:
            self._y = value
            self._view_dirty = True
    
    @property
    def z(self) -> float:
        return self._z
    
    @z.setter
    def z(self, value: float) -> None:
        if self._z != value:
            self._z = value
            self._view_dirty = True
    
    # Orientation properties - invalidate view cache on change
    @property
    def pitch(self) -> float:
        return self._pitch
    
    @pitch.setter
    def pitch(self, value: float) -> None:
        if self._pitch != value:
            self._pitch = value
            self._view_dirty = True
    
    @property
    def yaw(self) -> float:
        return self._yaw
    
    @yaw.setter
    def yaw(self, value: float) -> None:
        if self._yaw != value:
            self._yaw = value
            self._view_dirty = True
    
    @property
    def distance(self) -> float:
        return self._distance
    
    @distance.setter
    def distance(self, value: float) -> None:
        if self._distance != value:
            self._distance = value
            self._view_dirty = True
    
    # Viewport/projection properties - invalidate projection cache on change
    @property
    def width(self) -> int:
        return self._width
    
    @width.setter
    def width(self, value: int) -> None:
        if self._width != value:
            self._width = value
            self._projection_dirty = True
    
    @property
    def height(self) -> int:
        return self._height
    
    @height.setter
    def height(self, value: int) -> None:
        if self._height != value:
            self._height = value
            self._projection_dirty = True
    
    @property
    def fov(self) -> float:
        return self._fov
    
    @fov.setter
    def fov(self, value: float) -> None:
        if self._fov != value:
            self._fov = value
            self._projection_dirty = True

    def _invalidate_view(self):
        """Mark view matrix as needing recalculation.
        
        Note: This is now called automatically by property setters for
        x, y, z, pitch, yaw, and distance. Manual calls are only needed
        for bulk updates or special cases.
        """
        self._view_dirty = True
    
    def _invalidate_projection(self):
        """Mark projection matrix as needing recalculation.
        
        Note: This is now called automatically by property setters for
        width, height, and fov. Manual calls are only needed for bulk
        updates or special cases.
        """
        self._projection_dirty = True

    def set_resolution(
        self,
        width: int,
        height: int,
    ):
        # Properties handle cache invalidation automatically
        self.width = width
        self.height = height

    def set_position(
        self,
        position: Union[Vector3, vec3],
    ):
        # Properties handle cache invalidation automatically
            self.x = position.x
            self.y = position.y
            self.z = position.z

    def view(self) -> mat4:
        """Get view matrix with caching.
        
        Matrix is recalculated only when camera position/orientation changes.
        """
        if not self._view_dirty and self._cached_view is not None:
            return self._cached_view
        
        up: vec3 = vec3(0, 0, 1)
        pitch_axis: vec3 = glm.vec3(1, 0, 0)

        x, y, z = self.x, self.y, self.z
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        pitch_offset = self.pitch - math.pi / 2
        cos_pitch = math.cos(pitch_offset)
        sin_pitch = math.sin(pitch_offset)
        
        x += cos_yaw * cos_pitch * self.distance
        y += sin_yaw * cos_pitch * self.distance
        z += sin_pitch * self.distance

        camera: mat4 = mat4() * glm.translate(vec3(x, y, z))
        camera = glm.rotate(camera, self.yaw + math.pi / 2, up)
        camera = glm.rotate(camera, math.pi - self.pitch, pitch_axis)
        
        self._cached_view = glm.inverse(camera)
        self._view_dirty = False
        return self._cached_view

    def projection(self) -> mat4:
        """Get projection matrix with caching.
        
        Matrix is recalculated only when FOV or aspect ratio changes.
        """
        if not self._projection_dirty and self._cached_projection is not None:
            return self._cached_projection
        
        self._cached_projection = glm.perspective(
            self.fov,
            self.width / self.height,
            0.1,
            5000,
        )
        self._projection_dirty = False
        return self._cached_projection

    def translate(
        self,
        translation: vec3,
    ):
        # Properties handle cache invalidation automatically
        self.x += translation.x
        self.y += translation.y
        self.z += translation.z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        *,
        clamp: bool = False,
        lower_limit: float = 0,
        upper_limit: float = math.pi,
    ):
        # Update pitch and yaw (properties handle cache invalidation)
        self.pitch = self.pitch + pitch
        self.yaw = self.yaw + yaw

        # ensure yaw doesn't get too large.
        if self.yaw > 2 * math.pi:
            self.yaw -= 4 * math.pi
        elif self.yaw < -2 * math.pi:
            self.yaw += 4 * math.pi

        if pitch == 0:
            return

        # ensure pitch doesn't get too large.
        if self.pitch > 2 * math.pi:
            self.pitch -= 4 * math.pi
        elif self.pitch < -2 * math.pi:
            self.pitch += 4 * math.pi

        if clamp:
            if self.pitch < lower_limit:
                self.pitch = lower_limit
            elif self.pitch > upper_limit:
                self.pitch = upper_limit

        # Add a small value to pitch to jump to the other side if near the limits
        gimbal_lock_range = .05
        pitch_limit = math.pi / 2
        if pitch_limit - gimbal_lock_range < self.pitch < pitch_limit + gimbal_lock_range:
            small_value = .02 if pitch > 0 else -.02
            self.pitch += small_value

    def forward(
        self,
        *,
        ignore_z: bool = True,
    ) -> vec3:
        eye_x: float = math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_y: float = math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_z: Union[float, Literal[0]] = 0 if ignore_z else math.sin(self.pitch - math.pi / 2)
        return glm.normalize(-vec3(eye_x, eye_y, eye_z))

    def sideward(
        self,
        *,
        ignore_z: bool = True,
    ) -> vec3:
        return glm.normalize(glm.cross(self.forward(ignore_z=ignore_z), vec3(0.0, 0.0, 1.0)))

    def upward(
        self,
        *,
        ignore_xy: bool = True,
    ) -> vec3:
        if ignore_xy:
            return glm.normalize(vec3(0, 0, 1))
        forward: vec3 = self.forward(ignore_z=False)
        sideward: vec3 = self.sideward(ignore_z=False)
        cross: vec3 = glm.cross(forward, sideward)
        return glm.normalize(cross)

    def true_position(self) -> vec3:
        cos_yaw: float = math.cos(self.yaw)
        cos_pitch: float = math.cos(self.pitch - math.pi / 2)
        sin_yaw: float = math.sin(self.yaw)
        sin_pitch: float = math.sin(self.pitch - math.pi / 2)
        return vec3(
            self.x + cos_yaw * cos_pitch * self.distance,
            self.y + sin_yaw * cos_pitch * self.distance,
            self.z + sin_pitch * self.distance,
        )
