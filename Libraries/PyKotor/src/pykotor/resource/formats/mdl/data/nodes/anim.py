"""Animation node data structures for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from utility.common.geometry import Vector3, Vector4


@dataclass
class MDLAnimationEvent:
    """Animation event data.

    Events are markers in an animation sequence that trigger effects or
    actions at specific times, like footstep sounds or particle effects.

    Attributes:
        time: Time in seconds when event triggers
        name: Name/identifier of the event
    """

    time: float
    name: str


@dataclass
class MDLPositionKeyframe:
    """Position keyframe data for animation."""
    time: float
    position: Vector3


@dataclass
class MDLRotationKeyframe:
    """Rotation keyframe data for animation."""
    time: float
    rotation: Vector4  # Quaternion


@dataclass
class MDLScaleKeyframe:
    """Scale keyframe data for animation."""
    time: float
    scale: Vector3


@dataclass
class MDLAnimation:
    """High-level animation sequence in an MDL model.

    Attributes:
        name: Name of the animation
        length: Duration in seconds
        transtime: Transition time in seconds
        animroot: Name of the root node for this animation
        events: List of animation events
        root_node: Root animation node
    """

    name: str
    length: float = 0.0
    transtime: float = 0.0
    animroot: str = ""
    events: List[MDLAnimationEvent] = field(default_factory=list)
    root_node: Optional[MDLNode] = None


@dataclass
class MDLNodeAnimation(MDLNode):
    """A node in an animation hierarchy.

    Contains keyframe data for various properties that can be animated.

    Attributes:
        name: Name of the node
        node_number: Node number in the model
        nodetype: Type of the node (e.g. "DUMMY", "TRIMESH", etc)
        parent: Parent animation node if any
        children: List of child animation nodes
        length: Duration in seconds
        transtime: Transition time in seconds
        animroot: Name of the root node for this animation
        events: List of (time, event_name) tuples
    """

    nodetype: str = "DUMMY"
    parent: Optional[MDLNode] = None
    children: List[MDLNode] = field(default_factory=list)

    # Animation data
    length: float = 0.0
    transtime: float = 0.0
    root_node: Optional[MDLNode] = None
    events: List[MDLAnimationEvent] = field(default_factory=list)

    # Keyframe data
    position_keyframes: List[MDLPositionKeyframe] = field(default_factory=list)
    rotation_keyframes: List[MDLRotationKeyframe] = field(default_factory=list)
    scale_keyframes: List[MDLScaleKeyframe] = field(default_factory=list)

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def get_position_at_time(self, time: float) -> Vector3:
        """Get interpolated position at given time.

        Args:
            time: Time in seconds

        Returns:
            Vector3: Interpolated position
        """
        if not self.position_keyframes:
            return Vector3(0.0, 0.0, 0.0)

        # Find surrounding keyframes
        if time <= self.position_keyframes[0].time:
            return self.position_keyframes[0].position
        if time >= self.position_keyframes[-1].time:
            return self.position_keyframes[-1].position

        for i in range(len(self.position_keyframes) - 1):
            if self.position_keyframes[i].time <= time <= self.position_keyframes[i + 1].time:
                # Linear interpolation
                t = (time - self.position_keyframes[i].time) / (self.position_keyframes[i + 1].time - self.position_keyframes[i].time)
                pos1 = self.position_keyframes[i].position
                pos2 = self.position_keyframes[i + 1].position
                return Vector3(pos1.x + (pos2.x - pos1.x) * t, pos1.y + (pos2.y - pos1.y) * t, pos1.z + (pos2.z - pos1.z) * t)

        return Vector3(0.0, 0.0, 0.0)

    def get_rotation_at_time(self, time: float) -> Vector4:
        """Get interpolated rotation at given time.

        Args:
            time: Time in seconds

        Returns:
            Vector4: Interpolated rotation quaternion [x,y,z,w]
        """
        if not self.rotation_keyframes:
            return Vector4(0.0, 0.0, 0.0, 1.0)

        # Find surrounding keyframes
        if time <= self.rotation_keyframes[0].time:
            return self.rotation_keyframes[0].rotation
        if time >= self.rotation_keyframes[-1].time:
            return self.rotation_keyframes[-1].rotation

        for i in range(len(self.rotation_keyframes) - 1):
            if self.rotation_keyframes[i].time <= time <= self.rotation_keyframes[i + 1].time:
                # Spherical linear interpolation (SLERP)
                t = (time - self.rotation_keyframes[i].time) / (self.rotation_keyframes[i + 1].time - self.rotation_keyframes[i].time)
                q1 = self.rotation_keyframes[i].rotation
                q2 = self.rotation_keyframes[i + 1].rotation

                # Calculate dot product
                dot = q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w

                # If negative dot product, negate one quaternion to take shorter path
                if dot < 0:
                    q2 = Vector4(-q2.x, -q2.y, -q2.z, -q2.w)
                    dot = -dot

                # Use linear interpolation if quaternions are very close
                if dot > 0.9995:
                    return Vector4(q1.x + (q2.x - q1.x) * t, q1.y + (q2.y - q1.y) * t, q1.z + (q2.z - q1.z) * t, q1.w + (q2.w - q1.w) * t)

                # Calculate SLERP
                theta_0 = dot
                theta = theta_0 * t
                sin_theta = (1 - theta_0 * theta_0) ** 0.5
                sin_theta_0 = (1 - theta * theta) ** 0.5

                s0 = sin_theta_0 / sin_theta
                s1 = theta / sin_theta

                return Vector4(s0 * q1.x + s1 * q2.x, s0 * q1.y + s1 * q2.y, s0 * q1.z + s1 * q2.z, s0 * q1.w + s1 * q2.w)

        return Vector4(0.0, 0.0, 0.0, 1.0)

    def get_scale_at_time(self, time: float) -> Vector3:
        """Get interpolated scale at given time.

        Args:
            time: Time in seconds

        Returns:
            Vector3: Interpolated scale
        """
        if not self.scale_keyframes:
            return Vector3(1.0, 1.0, 1.0)

        # Find surrounding keyframes
        if time <= self.scale_keyframes[0].time:
            return self.scale_keyframes[0].scale
        if time >= self.scale_keyframes[-1].time:
            return self.scale_keyframes[-1].scale

        for i in range(len(self.scale_keyframes) - 1):
            if self.scale_keyframes[i].time <= time <= self.scale_keyframes[i + 1].time:
                # Linear interpolation
                t = (time - self.scale_keyframes[i].time) / (self.scale_keyframes[i + 1].time - self.scale_keyframes[i].time)
                scale1 = self.scale_keyframes[i].scale
                scale2 = self.scale_keyframes[i + 1].scale
                return Vector3(scale1.x + (scale2.x - scale1.x) * t, scale1.y + (scale2.y - scale1.y) * t, scale1.z + (scale2.z - scale1.z) * t)

        return Vector3(1.0, 1.0, 1.0)
