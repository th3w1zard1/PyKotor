"""Reference node data structure for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pykotor.resource.formats.mdl.data.nodes.node import MDLNode
from utility.common.geometry import Vector3


@dataclass
class MDLReferenceNode(MDLNode):
    """Reference node in MDL format.

    Reference nodes are used to include other models or parts of models. They can
    reference external model files or specific nodes within the same model. This
    allows for model reuse and hierarchical model composition.
    """

    # Reference target
    ref_model: Optional[str] = None  # Name of referenced model file
    ref_node: Optional[str] = None  # Name of referenced node

    # Transform
    position: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))  # Position offset
    orientation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])  # Rotation quaternion [x,y,z,w]
    scale: Vector3 = field(default_factory=lambda: Vector3(1.0, 1.0, 1.0))  # Scale factors

    # Reattach flags
    reattach_mesh: bool = False  # Whether to reattach mesh data
    reattach_anim: bool = False  # Whether to reattach animation data
    reattach_walkmesh: bool = False  # Whether to reattach walkmesh data
    reattach_dangly: bool = False  # Whether to reattach dangly mesh data
    reattach_skin: bool = False  # Whether to reattach skin data
    reattach_aabb: bool = False  # Whether to reattach AABB data

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def get_transform_matrix(self) -> List[List[float]]:
        """Get 4x4 transformation matrix.

        Returns:
            List[List[float]]: 4x4 transformation matrix in row-major order
        """
        # Extract quaternion components
        qx, qy, qz, qw = self.orientation

        # Compute rotation matrix elements
        xx = qx * qx
        xy = qx * qy
        xz = qx * qz
        xw = qx * qw
        yy = qy * qy
        yz = qy * qz
        yw = qy * qw
        zz = qz * qz
        zw = qz * qw

        # Build 4x4 matrix (row-major)
        return [
            # Row 1
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - zw), 2.0 * (xz + yw), self.position.x],
            # Row 2
            [2.0 * (xy + zw), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - xw), self.position.y],
            # Row 3
            [2.0 * (xz - yw), 2.0 * (yz + xw), 1.0 - 2.0 * (xx + yy), self.position.z],
            # Row 4
            [0.0, 0.0, 0.0, 1.0],
        ]

    def transform_point(self, point: Vector3) -> Vector3:
        """Transform point by reference node's transform.

        Args:
            point: Point to transform

        Returns:
            Vector3: Transformed point
        """
        # Extract quaternion components
        qx, qy, qz, qw = self.orientation

        # Rotate point by quaternion
        ix = qw * point.x + qy * point.z - qz * point.y
        iy = qw * point.y + qz * point.x - qx * point.z
        iz = qw * point.z + qx * point.y - qy * point.x
        iw = -qx * point.x - qy * point.y - qz * point.z

        # Final rotation
        x = ix * qw + iw * -qx + iy * -qz - iz * -qy
        y = iy * qw + iw * -qy + iz * -qx - ix * -qz
        z = iz * qw + iw * -qz + ix * -qy - iy * -qx

        # Apply scale and translation
        return Vector3(x * self.scale.x + self.position.x, y * self.scale.y + self.position.y, z * self.scale.z + self.position.z)
