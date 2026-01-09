"""MDL to Panda3D Geom converter.

This module converts PyKotor MDL/MDX models into Panda3D GeomNode structures
with full support for vertex data, tangent space, and face topology.

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Libraries/PyKotor/src/pykotor/resource/formats/mdl - MDL data structures
        /panda3d/panda3d-docs/programming/internal-structures/procedural-generation - Geom creation
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts


"""

from __future__ import annotations

import sys

from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add PyKotor to path
pykotor_path = Path(__file__).parents[5] / "Libraries" / "PyKotor" / "src"
if str(pykotor_path) not in sys.path:
    sys.path.insert(0, str(pykotor_path))

from panda3d.core import (  # type: ignore[import-not-found, note]  # pyright: ignore[reportMissingImports]
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexArrayFormat,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    InternalName,
    NodePath,
)
from pykotor.common.geometry_utils import compute_per_vertex_tangent_space  # pyright: ignore[reportMissingImports]
from pykotor.gl.models.mdl_converter import get_node_converter_type  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.mdl import read_mdl  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.engine.materials.base import IMaterialManager  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.mdl.mdl_data import (  # pyright: ignore[reportMissingImports]
        MDL,
        MDLMesh,
        MDLNode,
        MDLReference,
    )


class MDLLoader:
    """Loads KotOR MDL/MDX files and converts them to Panda3D geometry.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs - GeomVertexData and Geom creation
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:150-400


    """
    
    def __init__(
        self,
        material_manager: IMaterialManager | None = None,
        resource_loader: Any | None = None,
        texture_base_path: Path | None = None,
    ):
        """Initialize the MDL loader."""
        self._mdl: MDL | None = None
        self._mdx_path: str | None = None
        self._material_manager = material_manager
        self._resource_loader = resource_loader
        self._texture_base_path = texture_base_path
        self._active_texture_base: Path | None = None
    
    def load(self, mdl_path: str, mdx_path: str | None = None) -> NodePath:
        """Load an MDL/MDX file and convert to Panda3D scene graph.
        
        Args:
        ----
            mdl_path: Path to the MDL file
            mdx_path: Path to the MDX file (auto-detected if None)
        
        Returns:
        -------
            NodePath containing the loaded model geometry
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py - MDL reader

        """
        # Auto-detect MDX path
        if mdx_path is None:
            mdx_path = mdl_path.replace(".mdl", ".mdx")
        
        self._mdx_path = mdx_path
        
        # Read MDL file
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/io_mdl.py:2085-2130
        self._mdl = read_mdl(mdl_path)

        # Track texture base directory for materials
        mdl_dir = Path(mdl_path).parent
        self._active_texture_base = self._texture_base_path or mdl_dir
        
        # Prepare skin meshes
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:150-175
        self._mdl.prepare_skin_meshes()
        
        # Convert root node
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:46
        root_np = NodePath("root")
        self._convert_node_hierarchy(self._mdl.root, root_np)
        
        return root_np
    
    def _convert_node_hierarchy(self, mdl_node: MDLNode, parent_np: NodePath) -> None:
        """Recursively convert MDL node hierarchy to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node to convert
            parent_np: Parent NodePath
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:938-1134


        """
        # Convert this node based on type
        #
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:987-1004
        node_np: NodePath | None = None
        
        # Determine node type using abstract converter
        # Reference: Libraries/PyKotorGL/src/pykotor/gl/models/mdl_converter.py
        converter_type = get_node_converter_type(mdl_node)
        
        # Convert based on type
        #
        if converter_type == "aabb":
            node_np = self._convert_aabb_node(mdl_node)
        elif converter_type == "saber":
            node_np = self._convert_saber_node(mdl_node)
        elif converter_type == "dangly":
            node_np = self._convert_dangly_node(mdl_node)
        elif converter_type == "skin":
            node_np = self._convert_skin_node(mdl_node)
        elif converter_type == "mesh":
            node_np = self._convert_mesh_node(mdl_node)
        elif converter_type == "light":
            node_np = self._convert_light_node(mdl_node)
        elif converter_type == "emitter":
            node_np = self._convert_emitter_node(mdl_node)
        elif converter_type == "reference":
            node_np = self._convert_reference_node(mdl_node)
        else:
            # Dummy node (empty hierarchy node)
            node_np = NodePath(mdl_node.name)
        
        # Set local transform
        #
        # Reference: /panda3d/panda3d-docs - NodePath.setPos(), setHpr()
        node_np.setPos(
            mdl_node.position.x,
            mdl_node.position.y,
            mdl_node.position.z
        )
        
        # Convert quaternion to HPR
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:970-971
        from panda3d.core import Quat
        quat = Quat(
            mdl_node.orientation.w,
            mdl_node.orientation.x,
            mdl_node.orientation.y,
            mdl_node.orientation.z
        )
        hpr = quat.getHpr()
        node_np.setHpr(hpr)
        
        # Handle skin mesh reparenting (reone:72-76)
        # Skin meshes need special transform handling to prevent double animation
        #
        # Skin meshes are reparented directly to model root to prevent animation
        # being applied twice (once to bone, once to mesh)
        if converter_type == "skin" and mdl_node.skin:
            # Store skin data for skeletal animation
            node_np.setPythonTag("skin_data", mdl_node.skin)
            node_np.setPythonTag("is_skin_mesh", True)
        
        # Attach to parent
        #
        node_np.reparentTo(parent_np)
        
        # Handle reference nodes (load child models)
        #
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1006-1027
        if mdl_node.reference and self._resource_loader:
            self._load_reference_model(mdl_node.reference, node_np)
        
        # Recursively convert children
        #
        for child in mdl_node.children:
            self._convert_node_hierarchy(child, node_np)
    
    def _convert_mesh_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert an MDL mesh node to Panda3D GeomNode.
        
        Args:
        ----
            mdl_node: MDL node containing mesh data
        
        Returns:
        -------
            NodePath containing the GeomNode
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs - Geom creation
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1136-1372


        """
        mesh = mdl_node.mesh
        if not mesh:
            return NodePath(mdl_node.name)
        
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1146
        # Only create geometry if mesh has faces
        if not mesh.faces:
            return NodePath(mdl_node.name)
        
        # Create vertex format
        vertex_format = self._create_vertex_format(mesh)
        
        # Create vertex data
        # Reference: /panda3d/panda3d-docs - GeomVertexData(name, format, Geom.UHStatic)
        vdata = GeomVertexData(mdl_node.name, vertex_format, Geom.UHStatic)
        vdata.setNumRows(len(mesh.vertex_positions))
        
        # Write vertex data
        self._write_vertex_data(vdata, mesh)
        
        # Create geometry primitive
        geom = self._create_geometry(vdata, mesh)
        
        # Create GeomNode
        geom_node = GeomNode(mdl_node.name)
        geom_node.addGeom(geom)
        
        node = NodePath(geom_node)

        if self._material_manager:
            material = self._material_manager.create_material_from_mesh(mesh)
            if self._resource_loader and self._active_texture_base:
                material.load_resources(self._resource_loader, self._active_texture_base)
            self._material_manager.apply_material(node, material)

        return node
    
    def _convert_skin_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert a skinned mesh node to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node containing skin mesh data
        
        Returns:
        -------
            NodePath containing the skinned mesh
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1259-1263


        """
        # Skin nodes have both mesh (geometry) and skin (bone weights)
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1228
        if not mdl_node.skin or not mdl_node.mesh:
            return NodePath(mdl_node.name)
        
        mesh = mdl_node.mesh
        skin = mdl_node.skin
        
        if not mesh.vertex_positions:
            return NodePath(mdl_node.name)
        
        # Create vertex format (includes bone weights from skin)
        vertex_format = self._create_vertex_format(mesh)
        
        # Create vertex data
        vdata = GeomVertexData(mdl_node.name, vertex_format, Geom.UHStatic)
        vdata.setNumRows(len(mesh.vertex_positions))
        
        # Write vertex data (includes bone weights from skin)
        self._write_vertex_data(vdata, mesh)
        
        # Create geometry primitive
        geom = self._create_geometry(vdata, mesh)
        
        # Create GeomNode
        geom_node = GeomNode(mdl_node.name)
        geom_node.addGeom(geom)
        
        node = NodePath(geom_node)

        # Store skin/bone data for skeletal animation
        #
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1228-1342
        node.setPythonTag("skin_type", "skinned")
        node.setPythonTag("skin_data", skin)
        node.setPythonTag("bone_indices", skin.bone_indices)
        node.setPythonTag("bonemap", skin.bonemap)
        node.setPythonTag("bone_serial", skin.bone_serial)
        node.setPythonTag("bone_node_number", skin.bone_node_number)
        node.setPythonTag("qbones", skin.qbones)  # Bind pose quaternions
        node.setPythonTag("tbones", skin.tbones)  # Bind pose translations
        node.setPythonTag("vertex_bones", skin.vertex_bones)  # Per-vertex bone weights
        
        # Store reference to the full model for bone hierarchy access
        # This will be used to find bone nodes for animation
        if self._mdl:
            node.setPythonTag("model_root", self._mdl.root)

        if self._material_manager:
            material = self._material_manager.create_material_from_mesh(mesh)
            if self._resource_loader and self._active_texture_base:
                material.load_resources(self._resource_loader, self._active_texture_base)
            self._material_manager.apply_material(node, material)

        return node
    
    def _convert_dangly_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert a dangly (cloth/physics) mesh node to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node containing dangly mesh data
        
        Returns:
        -------
            NodePath containing the dangly mesh
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1202-1205


        """
        # Dangly nodes have both mesh (geometry) and dangly (physics constraints)
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1356
        if not mdl_node.dangly or not mdl_node.mesh:
            return NodePath(mdl_node.name)
        
        mesh = mdl_node.mesh
        dangly = mdl_node.dangly
        
        if not mesh.vertex_positions:
            return NodePath(mdl_node.name)
        
        # Create vertex format with dangly constraints
        vertex_format = self._create_vertex_format(mesh)
        
        # Create vertex data
        vdata = GeomVertexData(mdl_node.name, vertex_format, Geom.UHStatic)
        vdata.setNumRows(len(mesh.vertex_positions))
        
        # Write vertex data
        self._write_vertex_data(vdata, mesh)
        
        # Create geometry primitive
        geom = self._create_geometry(vdata, mesh)
        
        # Create GeomNode
        geom_node = GeomNode(mdl_node.name)
        geom_node.addGeom(geom)
        
        node = NodePath(geom_node)
        
        # Store dangly properties for physics simulation and shader uniforms
        #
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1491-1497
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1356-1399
        node.setPythonTag("dangly_type", "cloth")
        node.setPythonTag("dangly_data", dangly)
        node.setPythonTag("dangly_constraints", dangly.constraints)
        node.setPythonTag("dangly_verts_original", dangly.verts_original)
        
        # Apply material
        if self._material_manager:
            material = self._material_manager.create_material_from_mesh(mesh)
            if self._resource_loader and self._active_texture_base:
                material.load_resources(self._resource_loader, self._active_texture_base)
            self._material_manager.apply_material(node, material)
            # Dangly properties (displacement, tightness, period) will be set in material
            # when physics system is implemented
        
        return node
    
    def _convert_saber_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert a lightsaber blade mesh node to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node containing saber mesh data
        
        Returns:
        -------
            NodePath containing the saber mesh with saber properties stored
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1476-1479
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1447-1505 - MDLSaber structure

        """
        # Saber meshes have mesh data
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1447
        if not mdl_node.saber or not mdl_node.mesh:
            return NodePath(mdl_node.name)
        
        saber = mdl_node.saber
        
        # Convert as regular mesh but with saber material flags
        node_np = self._convert_mesh_node(mdl_node)
        
        # Store saber properties for special rendering
        #
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1447-1505
        node_np.setPythonTag("saber_type", "blade")
        node_np.setPythonTag("saber_data", saber)
        node_np.setPythonTag("saber_type_id", saber.saber_type)
        node_np.setPythonTag("saber_color", saber.saber_color)
        node_np.setPythonTag("saber_length", saber.saber_length)
        node_np.setPythonTag("saber_width", saber.saber_width)
        node_np.setPythonTag("saber_flare_color", saber.saber_flare_color)
        node_np.setPythonTag("saber_flare_radius", saber.saber_flare_radius)
        
        # Saber meshes need special material flags
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1476-1479
        # Material should have SABER and IGNORE_LIGHTING flags
        # This is handled in material manager
        
        return node_np
    
    def _convert_aabb_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert an AABB (walkmesh/collision) node to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node containing AABB data
        
        Returns:
        -------
            NodePath containing the AABB mesh (typically invisible)
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1212-1243


        """
        # AABB nodes are typically not rendered, used for collision
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1212-1243
        if not mdl_node.walkmesh:
            return NodePath(mdl_node.name)
        
        walkmesh = mdl_node.walkmesh
        
        # Create NodePath for collision detection
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:1403-1445
        aabb_np = NodePath(mdl_node.name)
        
        # Store walkmesh/AABB data for collision detection
        #
        aabb_np.setPythonTag("aabb_type", "collision")
        aabb_np.setPythonTag("walkmesh_data", walkmesh)
        aabb_np.setPythonTag("aabb_tree", walkmesh.aabbs)
        
        # AABB meshes are typically invisible (no rendering)
        # They're used for collision detection and pathfinding
        #
        return node_np
    
    def _convert_light_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert a light node to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node containing light data
        
        Returns:
        -------
            NodePath containing the light
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs - PointLight, DirectionalLight, SpotLight
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1544-1639


        """
        from panda3d.core import PointLight, DirectionalLight, Vec3, Vec4
        
        if not mdl_node.light:
            return NodePath(mdl_node.name)
        
        light_data = mdl_node.light
        
        # Determine light type based on radius
        #
        # Large radius (>100) = directional, otherwise point light
        is_directional = light_data.radius >= 100.0
        
        if is_directional:
            # Directional light (sun)
            #
            light = DirectionalLight(mdl_node.name)
        else:
            # Point light
            #
            light = PointLight(mdl_node.name)
            light.setAttenuation(Vec3(1, 0, 1.0 / light_data.radius))
            light.setMaxDistance(light_data.radius)
        
        # Set light color
        #
        # MDL light color is RGB (0-1 range)
        color = Vec4(
            light_data.color[0] if len(light_data.color) > 0 else 1.0,
            light_data.color[1] if len(light_data.color) > 1 else 1.0,
            light_data.color[2] if len(light_data.color) > 2 else 1.0,
            1.0
        )
        light.setColor(color)
        
        # Create NodePath for the light
        light_np = NodePath(light)
        
        # Store light data for animation controllers
        #
        light_np.setPythonTag("light_data", light_data)
        light_np.setPythonTag("light_active", light_data.active)
        
        return light_np
    
    def _convert_emitter_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert an emitter (particle system) node to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node containing emitter data
        
        Returns:
        -------
            NodePath containing the emitter (properties stored in tags for particle system)
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:998-1004
        Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:842-1051 - MDLEmitter structure

        """
        if not mdl_node.emitter:
            return NodePath(mdl_node.name)
        
        emitter = mdl_node.emitter
        
        # Create a placeholder node for the emitter
        # The actual particle system will be implemented later
        #
        emitter_np = NodePath(mdl_node.name)
        
        # Store emitter properties in NodePath tags for particle system integration
        # Reference: Libraries/PyKotor/src/pykotor/resource/formats/mdl/mdl_data.py:842-1051
        emitter_np.setPythonTag("emitter_type", "particle")
        emitter_np.setPythonTag("emitter_update", emitter.update)
        emitter_np.setPythonTag("emitter_render", emitter.render)
        emitter_np.setPythonTag("emitter_blend", emitter.blend)
        emitter_np.setPythonTag("emitter_texture", emitter.texture)
        emitter_np.setPythonTag("emitter_chunk_name", emitter.chunk_name)
        emitter_np.setPythonTag("emitter_depth_texture", emitter.depth_texture)
        emitter_np.setPythonTag("emitter_spawn_type", emitter.spawn_type)
        emitter_np.setPythonTag("emitter_loop", emitter.loop)
        emitter_np.setPythonTag("emitter_two_sided", emitter.two_sided_texture)
        emitter_np.setPythonTag("emitter_frame_blender", emitter.frame_blender)
        emitter_np.setPythonTag("emitter_render_order", emitter.render_order)
        emitter_np.setPythonTag("emitter_dead_space", emitter.dead_space)
        emitter_np.setPythonTag("emitter_blast_radius", emitter.blast_radius)
        emitter_np.setPythonTag("emitter_blast_length", emitter.blast_length)
        emitter_np.setPythonTag("emitter_branch_count", emitter.branch_count)
        emitter_np.setPythonTag("emitter_control_point_smoothing", emitter.control_point_smoothing)
        emitter_np.setPythonTag("emitter_x_grid", emitter.x_grid)
        emitter_np.setPythonTag("emitter_y_grid", emitter.y_grid)
        emitter_np.setPythonTag("emitter_flags", emitter.flags)
        
        # Store emitter data object for animation controllers
        # Controllers will animate: birthrate, lifeExp, xSize, ySize, spread, velocity, etc.
        emitter_np.setPythonTag("emitter_data", emitter)
        
        return emitter_np
    
    def _convert_reference_node(self, mdl_node: MDLNode) -> NodePath:
        """Convert a reference node (external model link) to Panda3D.
        
        Args:
        ----
            mdl_node: MDL node containing reference data
        
        Returns:
        -------
            NodePath for the reference (child model loaded separately)
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1006-1027


        """
        # Reference nodes create a placeholder - actual model loaded in _load_reference_model
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1006-1027
        return NodePath(mdl_node.name)
    
    def _load_reference_model(self, reference: MDLReference, parent_np: NodePath) -> None:
        """Load a referenced external model.
        
        Args:
        ----
            reference: MDL reference data
            parent_np: Parent NodePath to attach loaded model to
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1012-1026


        """
        #
        # Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/src/three/odyssey/OdysseyModel3D.ts:1012-1026
        if not self._resource_loader or not reference.model_name:
            return
        
        # Load the referenced model using Installation resource resolution
        #
        # The model name is stored in reference.model_name (without extension)
        model_name = reference.model_name
        
        # Resolve MDL and MDX resources from installation
        # Reference: Engines/PyKotorEngine/src/pykotor/engine/panda3d/module_loader.py:231-256
        from pykotor.extract.installation import SearchLocation  # pyright: ignore[reportMissingImports]
        from pykotor.resource.type import ResourceType  # pyright: ignore[reportMissingImports]
        
        SEARCH_ORDER = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
        
        mdl_resource = self._resource_loader.resource(model_name, ResourceType.MDL, SEARCH_ORDER)
        mdx_resource = self._resource_loader.resource(model_name, ResourceType.MDX, SEARCH_ORDER)
        
        if not mdl_resource or not mdx_resource:
            return
        
        # Get file paths from resources
        mdl_path = None
        mdx_path = None
        
        # Try to get filepath from resource
        if hasattr(mdl_resource, 'filepath') and mdl_resource.filepath():
            mdl_path = str(mdl_resource.filepath())
        elif hasattr(mdl_resource, 'path'):
            mdl_path = str(mdl_resource.path)
        else:
            # Fallback: construct path from resource identifier
            mdl_path = model_name + ".mdl"
        
        if hasattr(mdx_resource, 'filepath') and mdx_resource.filepath():
            mdx_path = str(mdx_resource.filepath())
        elif hasattr(mdx_resource, 'path'):
            mdx_path = str(mdx_resource.path)
        else:
            mdx_path = model_name + ".mdx"
        
        # Create a new MDLLoader instance to load the referenced model
        #
        # Use the same material manager and resource loader
        child_loader = MDLLoader(
            material_manager=self._material_manager,
            resource_loader=self._resource_loader,
            texture_base_path=self._texture_base_path,
        )
        
        # Load the child model
        child_np = child_loader.load(mdl_path, mdx_path)
        
        # Attach to parent at the reference node's position
        #
        if child_np:
            child_np.reparentTo(parent_np)
    
    def _create_vertex_format(self, mesh: MDLMesh) -> GeomVertexFormat:
        """Create vertex format for the mesh.
        
        Args:
        ----
            mesh: MDL mesh to create format for
        
        Returns:
        -------
            GeomVertexFormat with appropriate vertex attributes
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Libraries/PyKotorGL/src/pykotor/gl/models/mdl_converter.py - Format requirements
        /panda3d/panda3d-docs - GeomVertexArrayFormat.addColumn()

        """
        # Determine format requirements using abstract utility
        # Reference: Libraries/PyKotorGL/src/pykotor/gl/models/mdl_converter.py
        from pykotor.gl.models.mdl_converter import VertexFormatRequirements
        reqs = VertexFormatRequirements.from_mesh(mesh)
        
        # Create array format
        # Reference: /panda3d/panda3d-docs - GeomVertexArrayFormat()
        array = GeomVertexArrayFormat()
        
        # Position, normal, UV (required)
        # Reference: /panda3d/panda3d-docs - addColumn(name, num_components, numeric_type, contents)
        array.addColumn(InternalName.getVertex(), 3, Geom.NTFloat32, Geom.CPoint)
        array.addColumn(InternalName.getNormal(), 3, Geom.NTFloat32, Geom.CVector)
        array.addColumn(InternalName.getTexcoord(), 2, Geom.NTFloat32, Geom.CTexcoord)
        
        # Tangent space for normal mapping
        # Reference: https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:5470-5596 - Tangent space
        if reqs.has_tangent_space:
            array.addColumn(InternalName.getTangent(), 3, Geom.NTFloat32, Geom.CVector)
            array.addColumn(InternalName.getBinormal(), 3, Geom.NTFloat32, Geom.CVector)
        
        # Lightmap UV
        if reqs.has_lightmap:
            array.addColumn(InternalName.getTexcoord().getIndex(1), 2, Geom.NTFloat32, Geom.CTexcoord)
        
        # Bone weights for skinning
        #
        if reqs.has_skinning:
            array.addColumn(InternalName.make("bone_indices"), 4, Geom.NTUint16, Geom.CIndex)
            array.addColumn(InternalName.make("bone_weights"), 4, Geom.NTFloat32, Geom.CVector)
        
        # Register format
        # Reference: /panda3d/panda3d-docs - GeomVertexFormat.registerFormat()
        format = GeomVertexFormat()
        format.addArray(array)
        return GeomVertexFormat.registerFormat(format)
    
    def _write_vertex_data(self, vdata: GeomVertexData, mesh: MDLMesh) -> None:
        """Write vertex data from MDL mesh to Panda3D GeomVertexData.
        
        Args:
        ----
            vdata: Panda3D vertex data to write to
            mesh: MDL mesh source data
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs - GeomVertexWriter


        """
        # Determine format requirements first to ensure writer creation matches column existence
        # Reference: Libraries/PyKotorGL/src/pykotor/gl/models/mdl_converter.py
        from pykotor.gl.models.mdl_converter import VertexFormatRequirements
        reqs = VertexFormatRequirements.from_mesh(mesh)
        
        # Create writers
        # Reference: /panda3d/panda3d-docs - GeomVertexWriter(vdata, 'column_name')
        vertex_writer = GeomVertexWriter(vdata, InternalName.getVertex())
        normal_writer = GeomVertexWriter(vdata, InternalName.getNormal())
        uv_writer = GeomVertexWriter(vdata, InternalName.getTexcoord())
        
        # Optional writers - must match conditions used in _create_vertex_format
        # Tangent/binormal writers only if has_tangent_space (normals AND faces AND UVs)
        # Reference: https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:5470-5596 - Tangent space
        tangent_writer = None
        binormal_writer = None
        if reqs.has_tangent_space:
            tangent_writer = GeomVertexWriter(vdata, InternalName.getTangent())
            binormal_writer = GeomVertexWriter(vdata, InternalName.getBinormal())
        
        uv2_writer = None
        if reqs.has_lightmap:
            uv2_writer = GeomVertexWriter(vdata, InternalName.getTexcoord().getIndex(1))
        
        bone_indices_writer = None
        bone_weights_writer = None
        if reqs.has_skinning:
            bone_indices_writer = GeomVertexWriter(vdata, InternalName.make("bone_indices"))
            bone_weights_writer = GeomVertexWriter(vdata, InternalName.make("bone_weights"))
        
        # Compute tangent space if needed
        # Reference: Libraries/PyKotor/src/pykotor/common/geometry_utils.py
        tangent_data = None
        if reqs.has_tangent_space:
            tangent_data = compute_per_vertex_tangent_space(mesh)
        
        # Write vertex data
        # Reference: /panda3d/panda3d-docs - writer.addData3(x, y, z)
        for i, pos in enumerate(mesh.vertex_positions):
            # Position
            vertex_writer.addData3(pos.x, pos.y, pos.z)
            
            # Normal
            if i < len(mesh.vertex_normals):
                normal = mesh.vertex_normals[i]
                normal_writer.addData3(normal.x, normal.y, normal.z)
            else:
                normal_writer.addData3(0, 0, 1)
            
            # UV
            if i < len(mesh.vertex_uv):
                uv = mesh.vertex_uv[i]
                uv_writer.addData2(uv[0], uv[1])
            else:
                uv_writer.addData2(0, 0)
            
            # Tangent space
            if tangent_writer and tangent_data and i in tangent_data:
                tangent, binormal = tangent_data[i]
                tangent_writer.addData3(tangent.x, tangent.y, tangent.z)
                binormal_writer.addData3(binormal.x, binormal.y, binormal.z)
            elif tangent_writer:
                tangent_writer.addData3(1, 0, 0)
                binormal_writer.addData3(0, 1, 0)
            
            # Lightmap UV
            if uv2_writer and i < len(mesh.vertex_uv2):
                uv2 = mesh.vertex_uv2[i]
                uv2_writer.addData2(uv2[0], uv2[1])
            
            # Bone weights
            if bone_indices_writer and mesh.skin and i < len(mesh.skin.vertex_bones):
                bone_vertex = mesh.skin.vertex_bones[i]
                bone_indices_writer.addData4i(
                    int(bone_vertex.bone_indices[0]) if len(bone_vertex.bone_indices) > 0 else 0,
                    int(bone_vertex.bone_indices[1]) if len(bone_vertex.bone_indices) > 1 else 0,
                    int(bone_vertex.bone_indices[2]) if len(bone_vertex.bone_indices) > 2 else 0,
                    int(bone_vertex.bone_indices[3]) if len(bone_vertex.bone_indices) > 3 else 0,
                )
                bone_weights_writer.addData4(
                    bone_vertex.bone_weights[0] if len(bone_vertex.bone_weights) > 0 else 0.0,
                    bone_vertex.bone_weights[1] if len(bone_vertex.bone_weights) > 1 else 0.0,
                    bone_vertex.bone_weights[2] if len(bone_vertex.bone_weights) > 2 else 0.0,
                    bone_vertex.bone_weights[3] if len(bone_vertex.bone_weights) > 3 else 0.0,
                )
            elif bone_indices_writer:
                bone_indices_writer.addData4i(0, 0, 0, 0)
                bone_weights_writer.addData4(1.0, 0.0, 0.0, 0.0)
    
    
    def _create_geometry(self, vdata: GeomVertexData, mesh: MDLMesh) -> Geom:
        """Create Panda3D geometry from vertex data and face topology.
        
        Args:
        ----
            vdata: Vertex data
            mesh: MDL mesh with face data
        
        Returns:
        -------
            Geom object containing the mesh geometry
        
        References:
        ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        /panda3d/panda3d-docs - GeomTriangles


        """
        # Create triangle primitive
        prim = GeomTriangles(Geom.UHStatic)
        
        # Add face indices
        # Reference: Libraries/PyKotorGL/src/pykotor/gl/models/mdl_converter.py
        from pykotor.gl.models.mdl_converter import should_reverse_winding_order
        reverse_winding = should_reverse_winding_order("panda3d")
        
        for face in mesh.faces:
            # KotOR uses clockwise winding, Panda3D uses counter-clockwise
            #
            if reverse_winding:
                # Reverse winding order: v1, v2, v3 -> v1, v3, v2
                prim.addVertices(face.v1, face.v3, face.v2)
            else:
                prim.addVertices(face.v1, face.v2, face.v3)
        
        prim.closePrimitive()
        
        # Create Geom
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        
        return geom

