"""Dangly mesh node data structure for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from pykotor.resource.formats.mdl.data.nodes.trimesh import MDLTrimeshNode
from utility.common.geometry import Vector3


@dataclass
class MDLDanglyNode(MDLTrimeshNode):
    """Dangly mesh node in MDL format.

    Dangly meshes are used for cloth-like animations. They extend the trimesh with
    displacement constraints and physics properties that control how vertices move
    in response to forces like gravity and wind.
    """

    # Displacement limits
    displacement_max: float = 1.0  # Maximum vertex displacement
    displacement_min: float = 0.0  # Minimum vertex displacement
    period: float = 1.0  # Time for one complete oscillation
    tightness: float = 1.0  # Spring force coefficient

    # Force properties
    force_point: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))  # Force origin point
    force_radius: float = 0.0  # Radius of force effect
    force_type: int = 0  # Type of force (0=directional, 1=point)

    # Constraint flags
    constrain_x: bool = False  # Constrain motion in X axis
    constrain_y: bool = False  # Constrain motion in Y axis
    constrain_z: bool = False  # Constrain motion in Z axis

    # Per-vertex data
    displacement: List[float] = field(default_factory=list)  # Per-vertex displacement values
    constraints: List[Vector3] = field(default_factory=list)  # Per-vertex displacement constraints
    displacement_map: List[float] = field(default_factory=list)  # Per-vertex displacement multipliers

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def get_vertex_displacement(self, vertex_index: int, time: float) -> Vector3:
        """Get vertex displacement at given time.

        Args:
            vertex_index: Index of vertex
            time: Time in seconds

        Returns:
            Vector3: Displacement vector
        """
        if not self.constraints or vertex_index >= len(self.constraints):
            return Vector3(0.0, 0.0, 0.0)

        # Get base constraint and multiplier
        constraint = self.constraints[vertex_index]
        multiplier = self.displacement_map[vertex_index] if vertex_index < len(self.displacement_map) else 1.0
        displacement = self.displacement[vertex_index] if vertex_index < len(self.displacement) else self.displacement_max

        # Calculate oscillation
        t = (time % self.period) / self.period
        factor = ((1.0 - self.tightness) * (1.0 + self.tightness)) ** 0.5
        oscillation = factor * (1.0 - abs(2.0 * t - 1.0))

        # Apply displacement with constraints
        disp = Vector3(
            constraint.x * multiplier * oscillation * displacement if not self.constrain_x else 0.0,
            constraint.y * multiplier * oscillation * displacement if not self.constrain_y else 0.0,
            constraint.z * multiplier * oscillation * displacement if not self.constrain_z else 0.0,
        )

        # Clamp displacement magnitude
        mag_sq = disp.x * disp.x + disp.y * disp.y + disp.z * disp.z
        if mag_sq > 0:
            mag = mag_sq**0.5
            if mag > self.displacement_max:
                scale = self.displacement_max / mag
                disp = Vector3(disp.x * scale, disp.y * scale, disp.z * scale)
            elif mag < self.displacement_min:
                scale = self.displacement_min / mag
                disp = Vector3(disp.x * scale, disp.y * scale, disp.z * scale)

        return disp
