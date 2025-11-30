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
    
    Reference: Standard game engine practice (Unity, Unreal use similar caching)
    """
    
    __slots__ = (
        "x", "y", "z", "width", "height", "pitch", "yaw", "distance", "fov",
        "_cached_view", "_cached_projection", "_view_dirty", "_projection_dirty"
    )
    
    def __init__(self):
        self.x: float = 40.0
        self.y: float = 130.0
        self.z: float = 0.5
        self.width: int = 1920
        self.height: int = 1080
        self.pitch: float = math.pi / 2
        self.yaw: float = 0.0
        self.distance: float = 10.0
        self.fov: float = 90.0
        
        # Cached matrices
        self._cached_view: mat4 | None = None
        self._cached_projection: mat4 | None = None
        self._view_dirty: bool = True
        self._projection_dirty: bool = True

    def _invalidate_view(self):
        """Mark view matrix as needing recalculation."""
        self._view_dirty = True
    
    def _invalidate_projection(self):
        """Mark projection matrix as needing recalculation."""
        self._projection_dirty = True

    def set_resolution(
        self,
        width: int,
        height: int,
    ):
        if self.width != width or self.height != height:
            self.width, self.height = width, height
            self._invalidate_projection()

    def set_position(
        self,
        position: Union[Vector3, vec3],
    ):
        if self.x != position.x or self.y != position.y or self.z != position.z:
            self.x = position.x
            self.y = position.y
            self.z = position.z
            self._invalidate_view()

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
        self.x += translation.x
        self.y += translation.y
        self.z += translation.z
        self._invalidate_view()

    def rotate(
        self,
        yaw: float,
        pitch: float,
        *,
        clamp: bool = False,
        lower_limit: float = 0,
        upper_limit: float = math.pi,
    ):
        # Update pitch and yaw
        self.pitch = self.pitch + pitch
        self.yaw = self.yaw + yaw
        self._invalidate_view()

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
