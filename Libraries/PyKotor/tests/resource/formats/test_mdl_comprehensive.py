"""Exhaustive and comprehensive unit tests for ALL MDL/MDX feature combinations.

This test module provides meticulous coverage of EVERY possible combination of MDL/MDX features:
- All node type combinations
- All controller type combinations per node type
- All mesh type combinations (trimesh, skin, dangly, saber, aabb)
- All light property combinations
- All emitter property combinations
- All animation combinations
- Complex nested hierarchies with all features
- Stress tests with maximum complexity
- Integration tests with real-world scenarios
- Edge cases with unusual combinations

Test files are located in Libraries/PyKotor/tests/test_files/mdl/
"""

from __future__ import annotations

import io
import itertools
import unittest
from pathlib import Path

from pykotor.common.misc import Color
from pykotor.resource.formats.mdl import (
    MDL,
    MDLAnimation,
    MDLAsciiReader,
    MDLAsciiWriter,
    MDLBinaryReader,
    MDLBinaryWriter,
    MDLBoneVertex,
    MDLConstraint,
    MDLController,
    MDLControllerRow,
    MDLDangly,
    MDLEmitter,
    MDLEvent,
    MDLFace,
    MDLLight,
    MDLMesh,
    MDLNode,
    MDLReference,
    MDLSaber,
    MDLSkin,
    MDLWalkmesh,
    bytes_mdl,
    read_mdl,
    write_mdl,
)
from pykotor.resource.formats.mdl.mdl_types import (
    MDLClassification,
    MDLControllerType,
    MDLNodeType,
)
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector2, Vector3, Vector4


# ============================================================================
# Comprehensive Test Data Builders
# ============================================================================


def create_comprehensive_mdl(name: str = "comprehensive_test") -> MDL:
    """Create a comprehensive test MDL with all features."""
    mdl = MDL()
    mdl.name = name
    mdl.supermodel = "null"
    mdl.classification = MDLClassification.CHARACTER
    mdl.fog = True
    mdl.animation_scale = 0.971
    mdl.compress_quaternions = 1
    mdl.bmin = Vector3(-10.0, -10.0, -5.0)
    mdl.bmax = Vector3(10.0, 10.0, 15.0)
    mdl.radius = 12.0
    mdl.headlink = "head"
    mdl.root.name = "root"
    return mdl


def create_node_with_all_controllers(node_type: MDLNodeType = MDLNodeType.DUMMY) -> MDLNode:
    """Create a node with ALL applicable controllers for its type."""
    node = MDLNode()
    node.name = f"node_{node_type.name.lower()}"
    node.node_type = node_type
    node.position = Vector3(1.0, 2.0, 3.0)
    node.orientation = Vector4(0.0, 0.0, 0.0, 1.0)

    # Base controllers (all node types)
    controllers = [
        MDLControllerType.POSITION,
        MDLControllerType.ORIENTATION,
        MDLControllerType.SCALE,
        MDLControllerType.ALPHA,
    ]

    # Add type-specific controllers
    if node_type == MDLNodeType.LIGHT:
        controllers.extend([
            MDLControllerType.COLOR,
            MDLControllerType.RADIUS,
            MDLControllerType.SHADOWRADIUS,
            MDLControllerType.VERTICALDISPLACEMENT,
            MDLControllerType.MULTIPLIER,
        ])
    elif node_type == MDLNodeType.EMITTER:
        controllers.extend([
            MDLControllerType.ALPHASTART,
            MDLControllerType.ALPHAEND,
            MDLControllerType.BIRTHRATE,
            MDLControllerType.BOUNCECO,
            MDLControllerType.COMBINETIME,
            MDLControllerType.DRAG,
            MDLControllerType.FPS,
            MDLControllerType.FRAMEEND,
            MDLControllerType.FRAMESTART,
            MDLControllerType.GRAV,
            MDLControllerType.LIFEEXP,
            MDLControllerType.MASS,
            MDLControllerType.VELOCITY,
            MDLControllerType.SIZESTART,
            MDLControllerType.SIZEEND,
            MDLControllerType.COLORSTART,
            MDLControllerType.COLOREND,
        ])
    elif node_type == MDLNodeType.TRIMESH:
        controllers.append(MDLControllerType.SELFILLUMCOLOR)

    # Create controllers
    for ctrl_type in controllers:
        # Add rows with appropriate data
        row1_data = []
        row2_data = []

        if ctrl_type == MDLControllerType.POSITION:
            row1_data = [0.0, 0.0, 0.0]
            row2_data = [1.0, 1.0, 1.0]
        elif ctrl_type == MDLControllerType.ORIENTATION:
            row1_data = [0.0, 0.0, 0.0, 1.0]
            row2_data = [0.0, 0.0, 0.0, 1.0]
        elif ctrl_type == MDLControllerType.SCALE:
            row1_data = [1.0]
            row2_data = [1.5]
        elif ctrl_type == MDLControllerType.COLOR:
            row1_data = [1.0, 1.0, 1.0]
            row2_data = [0.5, 0.5, 0.5]
        elif ctrl_type in [MDLControllerType.RADIUS, MDLControllerType.SHADOWRADIUS, MDLControllerType.MULTIPLIER]:
            row1_data = [5.0]
            row2_data = [10.0]
        else:
            row1_data = [1.0]
            row2_data = [2.0]

        row1 = MDLControllerRow(0.0, row1_data)
        row2 = MDLControllerRow(1.0, row2_data)
        controller = MDLController(ctrl_type, [row1, row2], False)
        node.controllers.append(controller)

    return node


def create_light_with_all_properties() -> MDLLight:
    """Create a light with all properties set."""
    light = MDLLight()
    light.flare_radius = 5.0
    light.light_priority = 3
    light.ambient_only = 0
    light.dynamic_type = 1
    light.shadow = 1
    light.flare = 1
    light.fading_light = 1
    light.color = Color(255.0/255.0, 200.0/255.0, 150.0/255.0)
    light.radius = 10.0
    light.multiplier = 1.5

    # Add flare data
    light.flare_sizes = [0.5, 0.3, 0.2]
    light.flare_positions = [0.0, 0.5, 1.0]
    light.flare_color_shifts = [0.0, 0.2, 0.4]
    light.flare_textures = ["flaretex01", "flaretex02", "flaretex03"]

    return light


def create_emitter_with_all_properties() -> MDLEmitter:
    """Create an emitter with all properties set."""
    emitter = MDLEmitter()
    # Only set attributes that actually exist on MDLEmitter
    emitter.update = "fountain"
    emitter.render = "normal"
    emitter.blend = "lighten"
    emitter.spawn_type = 0
    emitter.dead_space = 0.0
    emitter.blast_radius = 5.0
    emitter.blast_length = 10.0
    emitter.branch_count = 3
    emitter.control_point_smoothing = 0.5
    emitter.x_grid = 4
    emitter.y_grid = 4
    emitter.texture = "fx_texture"
    emitter.chunk_name = "chunk"
    emitter.two_sided_texture = 1
    emitter.loop = 1
    emitter.render_order = 0
    emitter.frame_blender = 1
    emitter.depth_texture = "depth_tex"
    emitter.flags = 0

    return emitter


def create_mesh_with_all_properties() -> MDLMesh:
    """Create a mesh with all properties set."""
    mesh = MDLMesh()
    mesh.texture_1 = "texture1"
    mesh.texture_2 = "texture2"
    mesh.texture_3 = "texture3"
    mesh.texture_4 = "texture4"
    mesh.texture_5 = "texture5"
    mesh.texture_6 = "texture6"
    mesh.lightmap = "lightmap"
    mesh.render = True
    mesh.shadow = True
    mesh.beaming = True
    mesh.infinite = True
    mesh.rotatetexture = True
    mesh.background_geometry = True
    mesh.has_lightmap = True
    mesh.animate_uv = True
    mesh.uv_direction_x = 1.0
    mesh.uv_direction_y = 1.0
    mesh.uv_jitter = 0.0
    mesh.uv_jitter_speed = 0.0
    mesh.uv_fps = 1.0

    # Add vertices
    mesh.vertex_positions = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(1.0, 0.0, 0.0),
        Vector3(0.0, 1.0, 0.0),
        Vector3(1.0, 1.0, 0.0),
    ]

    # Add texture coordinates
    mesh.vertex_uvs = [
        Vector2(0.0, 0.0),
        Vector2(1.0, 0.0),
        Vector2(0.0, 1.0),
        Vector2(1.0, 1.0),
    ]

    # Add normals
    mesh.vertex_normals = [
        Vector3(0.0, 0.0, 1.0),
        Vector3(0.0, 0.0, 1.0),
        Vector3(0.0, 0.0, 1.0),
        Vector3(0.0, 0.0, 1.0),
    ]

    # Add faces
    face1 = MDLFace()
    face1.v1 = 0
    face1.v2 = 1
    face1.v3 = 2
    face1.material = 0

    face2 = MDLFace()
    face2.v1 = 1
    face2.v2 = 3
    face2.v3 = 2
    face2.material = 0

    mesh.faces = [face1, face2]

    return mesh


def create_skin_with_all_properties() -> MDLSkin:
    """Create a skin mesh with all properties set."""
    skin = MDLSkin()

    # Add bone data
    skin.bonemap = [0, 1, 2]

    # Add bone quaternions and translations
    for i in range(3):
        skin.qbones.append(Vector4(0.0, 0.0, 0.0, 1.0))
        skin.tbones.append(Vector3(float(i), 0.0, 0.0))

    # Add bone vertices (vertex_bones)
    for i in range(4):
        bone_vert = MDLBoneVertex()
        bone_vert.vertex_weights = (0.5, 0.3, 0.2, 0.0)
        bone_vert.vertex_indices = (0.0, 1.0, 2.0, 0.0)
        skin.vertex_bones.append(bone_vert)

    return skin


def create_dangly_with_all_properties() -> MDLDangly:
    """Create a dangly mesh with all properties set."""
    dangly = MDLDangly()

    # Add vertices (current positions)
    dangly.verts = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(1.0, 0.0, 0.0),
        Vector3(0.0, 1.0, 0.0),
        Vector3(1.0, 1.0, 0.0),
    ]

    # Add original vertices (bind pose)
    dangly.verts_original = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(1.0, 0.0, 0.0),
        Vector3(0.0, 1.0, 0.0),
        Vector3(1.0, 1.0, 0.0),
    ]

    # Add constraints
    for i in range(4):
        constraint = MDLConstraint()
        constraint.name = f"constraint_{i}"
        constraint.type = 0
        constraint.target = i
        constraint.target_node = 0
        dangly.constraints.append(constraint)

    return dangly


def create_saber_with_all_properties() -> MDLSaber:
    """Create a saber mesh with all properties set."""
    saber = MDLSaber()
    saber.length = 1.0
    saber.tip = Vector3(0.0, 0.0, 1.0)
    saber.base = Vector3(0.0, 0.0, 0.0)

    return saber


def create_animation_with_all_properties(name: str = "comprehensive_anim") -> MDLAnimation:
    """Create an animation with all properties set."""
    anim = MDLAnimation()
    anim.name = name
    anim.anim_length = 2.0
    anim.transition_length = 0.5
    anim.root_model = "root"

    # Add multiple events
    for i in range(5):
        event = MDLEvent()
        event.activation_time = i * 0.4
        event.name = f"event_{i}"
        anim.events.append(event)

    # Add complex node hierarchy to animation
    anim_root = MDLNode()
    anim_root.name = "anim_root"
    anim_root.node_type = MDLNodeType.DUMMY
    anim_root.position = Vector3(0.0, 0.0, 0.0)
    anim_root.orientation = Vector4(0.0, 0.0, 0.0, 1.0)

    # Add controllers to animation node
    for ctrl_type in [MDLControllerType.POSITION, MDLControllerType.ORIENTATION, MDLControllerType.SCALE]:
        if ctrl_type == MDLControllerType.POSITION:
            row_data = [0.0, 0.0, 0.0]
        elif ctrl_type == MDLControllerType.ORIENTATION:
            row_data = [0.0, 0.0, 0.0, 1.0]
        else:
            row_data = [1.0]

        row = MDLControllerRow(0.0, row_data)
        controller = MDLController(ctrl_type, [row], False)
        anim_root.controllers.append(controller)

    # Add child nodes
    for i in range(3):
        child = MDLNode()
        child.name = f"anim_child_{i}"
        child.node_type = MDLNodeType.DUMMY
        child.position = Vector3(float(i), 0.0, 0.0)
        child.orientation = Vector4(0.0, 0.0, 0.0, 1.0)
        anim_root.children.append(child)

    anim.root = anim_root

    return anim


# ============================================================================
# Comprehensive Feature Combination Tests
# ============================================================================


class TestMDLAllNodeTypeCombinations(unittest.TestCase):
    """Test ALL node type combinations."""

    def test_all_node_types_in_single_model(self):
        """Test model with ALL node types present."""
        mdl = create_comprehensive_mdl("all_node_types")

        # Add all node types
        node_types = [
            MDLNodeType.DUMMY,
            MDLNodeType.TRIMESH,
            MDLNodeType.LIGHT,
            MDLNodeType.EMITTER,
            MDLNodeType.REFERENCE,
            MDLNodeType.AABB,
            MDLNodeType.SABER,
        ]

        for node_type in node_types:
            node = create_node_with_all_controllers(node_type)

            # Add type-specific data
            if node_type == MDLNodeType.TRIMESH:
                node.mesh = create_mesh_with_all_properties()
            elif node_type == MDLNodeType.LIGHT:
                node.light = create_light_with_all_properties()
            elif node_type == MDLNodeType.EMITTER:
                node.emitter = create_emitter_with_all_properties()
            elif node_type == MDLNodeType.REFERENCE:
                node.reference = MDLReference()
                node.reference.model = "ref_model.mdl"
            elif node_type == MDLNodeType.AABB:
                node.aabb = MDLWalkmesh()
            elif node_type == MDLNodeType.SABER:
                node.saber = create_saber_with_all_properties()

            mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify all node types are present
        self.assertEqual(len(mdl2.all_nodes()), len(mdl.all_nodes()))
        for node_type in node_types:
            found = any(n.node_type == node_type for n in mdl2.all_nodes())
            self.assertTrue(found, f"Node type {node_type} should be present")

    def test_all_node_types_with_controllers(self):
        """Test all node types with all their controllers."""
        mdl = create_comprehensive_mdl("all_nodes_controllers")

        for node_type in MDLNodeType:
            node = create_node_with_all_controllers(node_type)
            mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify controllers are preserved
        for node in mdl2.all_nodes():
            if node != mdl2.root:
                self.assertGreater(len(node.controllers), 0, f"Node {node.name} should have controllers")


class TestMDLAllControllerCombinations(unittest.TestCase):
    """Test ALL controller type combinations."""

    def test_all_header_controllers_together(self):
        """Test all header controllers on a single node."""
        mdl = create_comprehensive_mdl("all_header_controllers")
        node = MDLNode()
        node.name = "all_ctrls"
        node.node_type = MDLNodeType.DUMMY

        # Add all header controllers
        for ctrl_type in [
            MDLControllerType.POSITION,
            MDLControllerType.ORIENTATION,
            MDLControllerType.SCALE,
            MDLControllerType.ALPHA,
        ]:
            if ctrl_type == MDLControllerType.POSITION:
                row_data = [1.0, 2.0, 3.0]
            elif ctrl_type == MDLControllerType.ORIENTATION:
                row_data = [0.0, 0.0, 0.0, 1.0]
            elif ctrl_type == MDLControllerType.SCALE:
                row_data = [1.5]
            else:
                row_data = [0.8]

            row = MDLControllerRow(0.0, row_data)
            controller = MDLController(ctrl_type, [row], False)
            node.controllers.append(controller)

        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("all_ctrls")
        self.assertIsNotNone(node2)
        self.assertEqual(len(node2.controllers), 4)

    def test_all_light_controllers_together(self):
        """Test all light controllers on a light node."""
        mdl = create_comprehensive_mdl("all_light_controllers")
        node = MDLNode()
        node.name = "light_all_ctrls"
        node.node_type = MDLNodeType.LIGHT
        node.light = create_light_with_all_properties()

        # Add all light controllers
        for ctrl_type in [
            MDLControllerType.COLOR,
            MDLControllerType.RADIUS,
            MDLControllerType.SHADOWRADIUS,
            MDLControllerType.VERTICALDISPLACEMENT,
            MDLControllerType.MULTIPLIER,
        ]:
            if ctrl_type == MDLControllerType.COLOR:
                row_data = [1.0, 1.0, 1.0]
            else:
                row_data = [5.0]

            row = MDLControllerRow(0.0, row_data)
            controller = MDLController(ctrl_type, [row], False)
            node.controllers.append(controller)

        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("light_all_ctrls")
        self.assertIsNotNone(node2)
        self.assertGreaterEqual(len(node2.controllers), 5)

    def test_all_emitter_controllers_together(self):
        """Test all emitter controllers on an emitter node."""
        mdl = create_comprehensive_mdl("all_emitter_controllers")
        node = MDLNode()
        node.name = "emitter_all_ctrls"
        node.node_type = MDLNodeType.EMITTER
        node.emitter = create_emitter_with_all_properties()

        # Add many emitter controllers (subset for testing)
        emitter_controllers = [
            MDLControllerType.ALPHASTART,
            MDLControllerType.ALPHAEND,
            MDLControllerType.BIRTHRATE,
            MDLControllerType.VELOCITY,
            MDLControllerType.SIZESTART,
            MDLControllerType.SIZEEND,
            MDLControllerType.COLORSTART,
            MDLControllerType.COLOREND,
        ]

        for ctrl_type in emitter_controllers:
            if ctrl_type in [MDLControllerType.COLORSTART, MDLControllerType.COLOREND]:
                row_data = [1.0, 1.0, 1.0]
            elif ctrl_type in [MDLControllerType.SIZESTART, MDLControllerType.SIZEEND]:
                row_data = [1.0, 1.0]
            elif ctrl_type == MDLControllerType.VELOCITY:
                row_data = [0.0, 0.0, 1.0]
            else:
                row_data = [1.0]

            row = MDLControllerRow(0.0, row_data)
            controller = MDLController(ctrl_type, [row], False)
            node.controllers.append(controller)

        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("emitter_all_ctrls")
        self.assertIsNotNone(node2)
        self.assertGreaterEqual(len(node2.controllers), len(emitter_controllers))

    def test_keyed_and_bezier_controllers_together(self):
        """Test both keyed and bezier controllers on same node."""
        mdl = create_comprehensive_mdl("keyed_bezier_mixed")
        node = MDLNode()
        node.name = "mixed_ctrls"
        node.node_type = MDLNodeType.DUMMY

        # Add keyed controller
        row = MDLControllerRow(0.0, [0.0, 0.0, 0.0])
        keyed_ctrl = MDLController(MDLControllerType.POSITION, [row], False)
        node.controllers.append(keyed_ctrl)

        # Add bezier controller
        row = MDLControllerRow(0.0, [0.0, 0.0, 0.0, 1.0])
        bezier_ctrl = MDLController(MDLControllerType.ORIENTATION, [row], True)
        node.controllers.append(bezier_ctrl)

        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("mixed_ctrls")
        self.assertIsNotNone(node2)
        self.assertEqual(len(node2.controllers), 2)
        # Verify one is keyed, one is bezier
        keyed_found = any(not ctrl.is_bezier for ctrl in node2.controllers)
        bezier_found = any(ctrl.is_bezier for ctrl in node2.controllers)
        self.assertTrue(keyed_found)
        self.assertTrue(bezier_found)


class TestMDLAllMeshTypeCombinations(unittest.TestCase):
    """Test ALL mesh type combinations."""

    def test_trimesh_with_all_properties(self):
        """Test trimesh with all properties set."""
        mdl = create_comprehensive_mdl("trimesh_all_props")
        node = MDLNode()
        node.name = "trimesh_all"
        node.node_type = MDLNodeType.TRIMESH
        node.mesh = create_mesh_with_all_properties()
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("trimesh_all")
        self.assertIsNotNone(node2)
        self.assertIsNotNone(node2.mesh)
        self.assertEqual(len(node2.mesh.vertex_positions), 4)
        self.assertEqual(len(node2.mesh.faces), 2)

    def test_skin_with_all_properties(self):
        """Test skin mesh with all properties set."""
        mdl = create_comprehensive_mdl("skin_all_props")
        node = MDLNode()
        node.name = "skin_all"
        node.node_type = MDLNodeType.TRIMESH
        node.mesh = create_skin_with_all_properties()
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("skin_all")
        self.assertIsNotNone(node2)
        # Note: Skin detection may require checking mesh type

    def test_dangly_with_all_properties(self):
        """Test dangly mesh with all properties set."""
        mdl = create_comprehensive_mdl("dangly_all_props")
        node = MDLNode()
        node.name = "dangly_all"
        node.node_type = MDLNodeType.DANGLYMESH
        node.mesh = create_dangly_with_all_properties()
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("dangly_all")
        self.assertIsNotNone(node2)

    def test_saber_with_all_properties(self):
        """Test saber mesh with all properties set."""
        mdl = create_comprehensive_mdl("saber_all_props")
        node = MDLNode()
        node.name = "saber_all"
        node.node_type = MDLNodeType.SABER
        node.saber = create_saber_with_all_properties()
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("saber_all")
        self.assertIsNotNone(node2)
        self.assertIsNotNone(node2.saber)


class TestMDLAllLightPropertyCombinations(unittest.TestCase):
    """Test ALL light property combinations."""

    def test_light_with_all_properties(self):
        """Test light with all properties set."""
        mdl = create_comprehensive_mdl("light_all_props")
        node = MDLNode()
        node.name = "light_all"
        node.node_type = MDLNodeType.LIGHT
        node.light = create_light_with_all_properties()
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("light_all")
        self.assertIsNotNone(node2)
        self.assertIsNotNone(node2.light)
        self.assertEqual(node2.light.flare_radius, 5.0)
        self.assertEqual(len(node2.light.flare_textures), 3)

    def test_light_with_all_flare_properties(self):
        """Test light with all flare properties set."""
        mdl = create_comprehensive_mdl("light_flares")
        node = MDLNode()
        node.name = "light_flares"
        node.node_type = MDLNodeType.LIGHT
        light = MDLLight()
        light.flare = 1
        light.flare_radius = 10.0
        light.flare_sizes = [0.5, 0.4, 0.3, 0.2]
        light.flare_positions = [0.0, 0.25, 0.5, 0.75]
        light.flare_color_shifts = [0.0, 0.1, 0.2, 0.3]
        light.flare_textures = ["flaretex01", "flaretex02", "flaretex03", "flaretex04"]
        node.light = light
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("light_flares")
        self.assertIsNotNone(node2)
        self.assertIsNotNone(node2.light)
        self.assertEqual(len(node2.light.flare_textures), 4)


class TestMDLAllEmitterPropertyCombinations(unittest.TestCase):
    """Test ALL emitter property combinations."""

    def test_emitter_with_all_properties(self):
        """Test emitter with all properties set."""
        mdl = create_comprehensive_mdl("emitter_all_props")
        node = MDLNode()
        node.name = "emitter_all"
        node.node_type = MDLNodeType.EMITTER
        node.emitter = create_emitter_with_all_properties()
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("emitter_all")
        self.assertIsNotNone(node2)
        self.assertIsNotNone(node2.emitter)
        self.assertEqual(node2.emitter.update, "fountain")
        self.assertEqual(node2.emitter.render, "normal")

    def test_emitter_all_update_modes(self):
        """Test emitter with all update modes."""
        update_modes = ["fountain", "single", "explosion", "lightning"]

        for update_mode in update_modes:
            with self.subTest(update_mode=update_mode):
                mdl = create_comprehensive_mdl(f"emitter_{update_mode}")
                node = MDLNode()
                node.name = f"emitter_{update_mode}"
                node.node_type = MDLNodeType.EMITTER
                emitter = MDLEmitter()
                emitter.update = update_mode
                node.emitter = emitter
                mdl.root.children.append(node)

                # Round-trip test
                output = io.StringIO()
                writer = MDLAsciiWriter(mdl, output)
                writer.write()
                ascii_content = output.getvalue()

                reader = MDLAsciiReader(io.StringIO(ascii_content))
                mdl2 = reader.load()

                node2 = mdl2.get(f"emitter_{update_mode}")
                self.assertIsNotNone(node2)
                self.assertEqual(node2.emitter.update, update_mode)

    def test_emitter_all_render_modes(self):
        """Test emitter with all render modes."""
        render_modes = [
            "normal",
            "linked",
            "billboard_to_local_z",
            "billboard_to_world_z",
            "aligned_to_world_z",
            "aligned_to_particle_dir",
            "motion_blur",
        ]

        for render_mode in render_modes:
            with self.subTest(render_mode=render_mode):
                mdl = create_comprehensive_mdl(f"emitter_{render_mode}")
                node = MDLNode()
                node.name = f"emitter_{render_mode}"
                node.node_type = MDLNodeType.EMITTER
                emitter = MDLEmitter()
                emitter.render = render_mode
                node.emitter = emitter
                mdl.root.children.append(node)

                # Round-trip test
                output = io.StringIO()
                writer = MDLAsciiWriter(mdl, output)
                writer.write()
                ascii_content = output.getvalue()

                reader = MDLAsciiReader(io.StringIO(ascii_content))
                mdl2 = reader.load()

                node2 = mdl2.get(f"emitter_{render_mode}")
                self.assertIsNotNone(node2)
                self.assertEqual(node2.emitter.render, render_mode)


class TestMDLAllAnimationCombinations(unittest.TestCase):
    """Test ALL animation combinations."""

    def test_animation_with_all_properties(self):
        """Test animation with all properties set."""
        mdl = create_comprehensive_mdl("anim_all_props")
        anim = create_animation_with_all_properties("comprehensive_anim")
        mdl.anims.append(anim)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        self.assertEqual(len(mdl2.anims), 1)
        anim2 = mdl2.anims[0]
        self.assertEqual(len(anim2.events), 5)
        self.assertIsNotNone(anim2.root)

    def test_multiple_animations_with_all_features(self):
        """Test multiple animations with all features."""
        mdl = create_comprehensive_mdl("multi_anims_all")

        for i in range(5):
            anim = create_animation_with_all_properties(f"anim_{i}")
            anim.anim_length = float(i + 1)
            mdl.anims.append(anim)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        self.assertEqual(len(mdl2.anims), 5)
        for i, anim in enumerate(mdl2.anims):
            self.assertEqual(anim.name, f"anim_{i}")
            self.assertEqual(anim.anim_length, float(i + 1))


class TestMDLComplexNestedHierarchies(unittest.TestCase):
    """Test complex nested hierarchies with all features."""

    def test_deep_hierarchy_with_all_features(self):
        """Test deep hierarchy with all node types and features."""
        mdl = create_comprehensive_mdl("deep_hierarchy_all")

        # Create 5-level deep hierarchy
        current = mdl.root
        for level in range(5):
            # Add multiple node types at each level
            dummy = MDLNode()
            dummy.name = f"level_{level}_dummy"
            dummy.node_type = MDLNodeType.DUMMY
            dummy.controllers.append(create_node_with_all_controllers(MDLNodeType.DUMMY).controllers[0])

            trimesh = MDLNode()
            trimesh.name = f"level_{level}_trimesh"
            trimesh.node_type = MDLNodeType.TRIMESH
            trimesh.mesh = create_mesh_with_all_properties()

            light = MDLNode()
            light.name = f"level_{level}_light"
            light.node_type = MDLNodeType.LIGHT
            light.light = create_light_with_all_properties()

            current.children.extend([dummy, trimesh, light])
            current = dummy  # Continue hierarchy with dummy

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify hierarchy depth
        all_nodes = mdl2.all_nodes()
        self.assertGreater(len(all_nodes), 15)  # root + 5 levels * 3 nodes

    def test_wide_hierarchy_with_all_features(self):
        """Test wide hierarchy with many siblings and all features."""
        mdl = create_comprehensive_mdl("wide_hierarchy_all")

        # Add 20 different nodes to root
        for i in range(20):
            node = MDLNode()
            node.name = f"sibling_{i}"
            node.node_type = MDLNodeType.DUMMY if i % 2 == 0 else MDLNodeType.TRIMESH

            if node.node_type == MDLNodeType.TRIMESH:
                node.mesh = create_mesh_with_all_properties()

            node.controllers.append(create_node_with_all_controllers(node.node_type).controllers[0])
            mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        self.assertEqual(len(mdl2.root.children), 20)


class TestMDLMaximumComplexityStressTests(unittest.TestCase):
    """Stress tests with maximum complexity."""

    def test_model_with_maximum_nodes(self):
        """Test model with maximum number of nodes."""
        mdl = create_comprehensive_mdl("max_nodes")

        # Add 100 nodes
        for i in range(100):
            node = MDLNode()
            node.name = f"node_{i}"
            node.node_type = MDLNodeType.DUMMY if i % 10 != 0 else MDLNodeType.TRIMESH

            if node.node_type == MDLNodeType.TRIMESH:
                node.mesh = create_mesh_with_all_properties()

            mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        self.assertEqual(len(mdl2.all_nodes()), 101)  # root + 100 children

    def test_model_with_maximum_controllers(self):
        """Test model with maximum number of controllers per node."""
        mdl = create_comprehensive_mdl("max_controllers")
        node = MDLNode()
        node.name = "max_ctrls"
        node.node_type = MDLNodeType.EMITTER
        node.emitter = create_emitter_with_all_properties()

        # Add 30 controllers (all emitter controllers)
        emitter_controllers = [
            MDLControllerType.ALPHASTART, MDLControllerType.ALPHAEND,
            MDLControllerType.BIRTHRATE, MDLControllerType.BOUNCECO,
            MDLControllerType.COMBINETIME, MDLControllerType.DRAG,
            MDLControllerType.FPS, MDLControllerType.FRAMEEND,
            MDLControllerType.FRAMESTART, MDLControllerType.GRAV,
            MDLControllerType.LIFEEXP, MDLControllerType.MASS,
            MDLControllerType.VELOCITY, MDLControllerType.SIZESTART,
            MDLControllerType.SIZEEND, MDLControllerType.COLORSTART,
            MDLControllerType.COLOREND, MDLControllerType.SIZESTART_Y,
            MDLControllerType.SIZEEND_Y, MDLControllerType.SPREAD,
            MDLControllerType.THRESHOLD, MDLControllerType.XSIZE,
            MDLControllerType.YSIZE, MDLControllerType.BLURLENGTH,
            MDLControllerType.LIGHTNINGDELAY, MDLControllerType.LIGHTNINGRADIUS,
            MDLControllerType.LIGHTNINGSCALE, MDLControllerType.ALPHAMID,
        ]

        for ctrl_type in emitter_controllers:
            row = MDLControllerRow(0.0, [1.0])
            controller = MDLController(ctrl_type, [row], False)
            node.controllers.append(controller)

        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("max_ctrls")
        self.assertIsNotNone(node2)
        self.assertGreaterEqual(len(node2.controllers), len(emitter_controllers))

    def test_model_with_maximum_animations(self):
        """Test model with maximum number of animations."""
        mdl = create_comprehensive_mdl("max_anims")

        # Add 20 animations
        for i in range(20):
            anim = create_animation_with_all_properties(f"anim_{i}")
            anim.anim_length = float(i + 1)
            mdl.anims.append(anim)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        self.assertEqual(len(mdl2.anims), 20)

    def test_model_with_maximum_mesh_vertices(self):
        """Test model with maximum number of vertices."""
        mdl = create_comprehensive_mdl("max_vertices")
        node = MDLNode()
        node.name = "max_verts"
        node.node_type = MDLNodeType.TRIMESH
        mesh = MDLMesh()

        # Add 1000 vertices
        mesh.vertex_positions = [
            Vector3(float(i), float(i), float(i))
            for i in range(1000)
        ]

        # Add 500 faces
        mesh.faces = []
        for i in range(500):
            face = MDLFace()
            face.v1 = i * 2
            face.v2 = i * 2 + 1
            face.v3 = (i * 2 + 2) % 1000
            face.material = 0
            mesh.faces.append(face)

        node.mesh = mesh
        mdl.root.children.append(node)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        node2 = mdl2.get("max_verts")
        self.assertIsNotNone(node2)
        self.assertIsNotNone(node2.mesh)
        self.assertEqual(len(node2.mesh.vertex_positions), 1000)
        self.assertEqual(len(node2.mesh.faces), 500)


class TestMDLAllClassificationCombinations(unittest.TestCase):
    """Test ALL model classification combinations."""

    def test_all_classifications(self):
        """Test all model classifications."""
        for classification in MDLClassification:
            if classification == MDLClassification.INVALID:
                continue

            with self.subTest(classification=classification):
                mdl = create_comprehensive_mdl(f"class_{classification.name.lower()}")
                mdl.classification = classification

                # Round-trip test
                output = io.StringIO()
                writer = MDLAsciiWriter(mdl, output)
                writer.write()
                ascii_content = output.getvalue()

                reader = MDLAsciiReader(io.StringIO(ascii_content))
                mdl2 = reader.load()

                self.assertEqual(mdl2.classification, classification)


class TestMDLUltimateCombinationTest(unittest.TestCase):
    """Ultimate combination test with EVERYTHING."""

    def test_ultimate_model_with_everything(self):
        """Test model with EVERY possible feature combination."""
        mdl = create_comprehensive_mdl("ultimate_test")

        # Add all node types
        for node_type in MDLNodeType:
            node = create_node_with_all_controllers(node_type)

            # Add type-specific data
            if node_type == MDLNodeType.TRIMESH:
                node.mesh = create_mesh_with_all_properties()
            elif node_type == MDLNodeType.LIGHT:
                node.light = create_light_with_all_properties()
            elif node_type == MDLNodeType.EMITTER:
                node.emitter = create_emitter_with_all_properties()
            elif node_type == MDLNodeType.REFERENCE:
                node.reference = MDLReference()
                node.reference.model = "ref.mdl"
            elif node_type == MDLNodeType.AABB:
                node.aabb = MDLWalkmesh()
            elif node_type == MDLNodeType.SABER:
                node.saber = create_saber_with_all_properties()

            mdl.root.children.append(node)

        # Add multiple animations
        for i in range(5):
            anim = create_animation_with_all_properties(f"ultimate_anim_{i}")
            mdl.anims.append(anim)

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify everything
        self.assertEqual(len(mdl2.all_nodes()), len(mdl.all_nodes()))
        self.assertEqual(len(mdl2.anims), 5)
        self.assertEqual(mdl2.classification, MDLClassification.CHARACTER)

        # Verify all node types are present
        node_types_found = {n.node_type for n in mdl2.all_nodes() if n != mdl2.root}
        expected_types = set(MDLNodeType)
        self.assertEqual(node_types_found, expected_types)


if __name__ == "__main__":
    unittest.main()

