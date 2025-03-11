"""Trimesh node data structure for MDL format."""

from __future__ import annotations

from dataclasses import dataclass

from pykotor.resource.formats.mdl.data.nodes.mesh import MDLMeshNode


@dataclass
class MDLTrimeshNode(MDLMeshNode):
    """Trimesh (triangle mesh) node in MDL format.

    This is the base mesh type that represents static geometry made up of triangles.
    Other mesh types like skinned meshes and dangly meshes extend from this.
    All geometry and material properties are inherited from MDLMeshNode.
    """

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)
