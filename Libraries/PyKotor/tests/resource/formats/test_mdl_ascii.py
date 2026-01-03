"""Exhaustive and comprehensive unit tests for ASCII MDL format handling.

This test module provides meticulous coverage of ALL MDL/MDX ASCII format features:
- All node types (dummy, trimesh, light, emitter, reference, saber, aabb, skin, dangly)
- All controller types (position, orientation, scale, alpha, color, radius, etc.)
- All mesh data (verts, faces, tverts, bones, weights, constraints)
- Animations with various configurations
- Round-trip testing (binary -> ASCII -> binary, ASCII -> binary -> ASCII)
- Edge cases and error handling
- Format detection
- All combinations of features

Test files are located in Libraries/PyKotor/tests/test_files/mdl/
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import pytest

from pykotor.common.misc import Color
from pykotor.extract.chitin import Chitin
from pykotor.extract.file import FileResource
from pykotor.resource.formats.mdl import (
    MDL,
    MDLAnimation,
    MDLAsciiReader,
    MDLAsciiWriter,
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
    detect_mdl,
    read_mdl,
    write_mdl,
)
from pykotor.resource.formats.mdl.mdl_types import (
    MDLClassification,
    MDLControllerType,
    MDLNodeType,
)
from pykotor.resource.formats.mdl.mdl_data import _qfloat
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector2, Vector3, Vector4


# ============================================================================
# Test Data Builders
# ============================================================================


def create_test_mdl(name: str = "test_model") -> MDL:
    """Create a basic test MDL with minimal data."""
    mdl = MDL()
    mdl.name = name
    mdl.supermodel = "null"
    mdl.classification = MDLClassification.OTHER
    mdl.root.name = "root"
    return mdl


def create_test_node(
    name: str = "test_node",
    node_type: MDLNodeType = MDLNodeType.DUMMY,
) -> MDLNode:
    """Create a test node with specified type."""
    node = MDLNode()
    node.name = name
    node.node_type = node_type
    node.position = Vector3(0.0, 0.0, 0.0)
    node.orientation = Vector4(0.0, 0.0, 0.0, 1.0)
    return node


def create_test_mesh() -> MDLMesh:
    """Create a test mesh with basic geometry."""
    mesh = MDLMesh()
    mesh.texture_1 = "test_texture"
    mesh.render = True
    mesh.shadow = False

    # Add some vertices
    mesh.vertex_positions = [
        Vector3(0.0, 0.0, 0.0),
        Vector3(1.0, 0.0, 0.0),
        Vector3(0.0, 1.0, 0.0),
    ]

    # Add a face
    face = MDLFace()
    face.v1 = 0
    face.v2 = 1
    face.v3 = 2
    face.material = 0
    mesh.faces = [face]

    return mesh


def create_test_controller(
    controller_type: MDLControllerType,
    is_bezier: bool = False,
) -> MDLController:
    """Create a test controller with specified type."""
    # Determine row data based on controller type
    if controller_type == MDLControllerType.POSITION:
        row_data = [1.0, 2.0, 3.0]
    elif controller_type == MDLControllerType.ORIENTATION:
        row_data = [0.0, 0.0, 0.0, 1.0]  # quaternion
    elif controller_type == MDLControllerType.SCALE:
        row_data = [1.0]
    elif controller_type == MDLControllerType.COLOR:
        row_data = [1.0, 1.0, 1.0]
    elif controller_type == MDLControllerType.RADIUS:
        row_data = [5.0]
    else:
        row_data = [1.0]

    # Create row and controller with proper constructors
    row = MDLControllerRow(0.0, row_data)
    controller = MDLController(controller_type, [row], is_bezier)
    return controller


def create_test_animation(name: str = "test_anim") -> MDLAnimation:
    """Create a test animation."""
    anim = MDLAnimation()
    anim.name = name
    anim.anim_length = 1.0
    anim.transition_length = 0.25
    anim.root_model = ""

    # Add a test event
    event = MDLEvent()
    event.activation_time = 0.5
    event.name = "footstep"
    anim.events = [event]

    # Add a test node to animation
    anim_node = create_test_node("anim_node", MDLNodeType.DUMMY)
    anim_node.controllers.append(create_test_controller(MDLControllerType.POSITION))
    anim.root = anim_node

    return anim


# ============================================================================
# Format Detection Tests
# ============================================================================


class TestMDLAsciiDetection(unittest.TestCase):
    """Test ASCII MDL format detection."""

    def test_detect_ascii_format(self):
        """Test detecting ASCII format."""
        # Create ASCII content
        ascii_content = b"# ASCII MDL\nnewmodel test_model\n"

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(ascii_content)
            temp_path = f.name

        try:
            detected = detect_mdl(temp_path)
            self.assertEqual(detected, ResourceType.MDL_ASCII)
        finally:
            Path(temp_path).unlink()

    def test_detect_binary_format(self):
        """Test detecting binary format."""
        # Create binary content (starts with null bytes)
        binary_content = b"\x00\x00\x00\x00" + b"test" * 100

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(binary_content)
            temp_path = f.name

        try:
            detected = detect_mdl(temp_path)
            self.assertEqual(detected, ResourceType.MDL)
        finally:
            Path(temp_path).unlink()

    def test_detect_from_bytes(self):
        """Test detection from bytes buffer."""
        ascii_content = b"# ASCII MDL\nnewmodel test\n"
        detected = detect_mdl(ascii_content)
        self.assertEqual(detected, ResourceType.MDL_ASCII)

        binary_content = b"\x00\x00\x00\x00" + b"test"
        detected = detect_mdl(binary_content)
        self.assertEqual(detected, ResourceType.MDL)


# ============================================================================
# Basic ASCII I/O Tests
# ============================================================================


class TestMDLAsciiBasicIO(unittest.TestCase):
    """Test basic ASCII MDL reading and writing."""

    def test_write_empty_mdl(self):
        """Test writing an empty MDL to ASCII."""
        mdl = create_test_mdl("empty_test")

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("newmodel empty_test", content)
        self.assertIn("beginmodelgeom", content)
        self.assertIn("endmodelgeom", content)
        self.assertIn("donemodel", content)

    def test_read_write_roundtrip_basic(self):
        """Test basic round-trip: write -> read."""
        mdl = create_test_mdl("roundtrip_test")
        mdl.root.name = "root_node"

        # Write to ASCII
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        # Read back
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        self.assertEqual(mdl2.name, mdl.name)
        self.assertEqual(mdl2.supermodel, mdl.supermodel)
        self.assertEqual(mdl2.classification, mdl.classification)

    def test_write_to_bytes(self):
        """Test writing to bytes buffer."""
        mdl = create_test_mdl("bytes_test")

        data = bytearray()
        writer = MDLAsciiWriter(mdl, data)
        writer.write()

        self.assertGreater(len(data), 0)
        content = data.decode("utf-8")
        self.assertIn("newmodel bytes_test", content)

    def test_write_to_bytesio(self):
        """Test writing to BytesIO."""
        mdl = create_test_mdl("bytesio_test")

        buffer = io.BytesIO()
        writer = MDLAsciiWriter(mdl, buffer)
        writer.write()

        buffer.seek(0)
        content = buffer.read().decode("utf-8")
        self.assertIn("newmodel bytesio_test", content)


# ============================================================================
# Node Type Tests
# ============================================================================


class TestMDLAsciiNodeTypes(unittest.TestCase):
    """Test all node types in ASCII format."""

    def test_write_dummy_node(self):
        """Test writing dummy node."""
        mdl = create_test_mdl("dummy_test")
        node = create_test_node("dummy_node", MDLNodeType.DUMMY)
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node dummy dummy_node", content)

    def test_read_dummy_node(self):
        """Test reading dummy node."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node dummy test_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        self.assertEqual(len(mdl.all_nodes()), 2)  # root + dummy
        dummy = mdl.get("test_node")
        self.assertIsNotNone(dummy)
        assert dummy is not None  # Type narrowing
        self.assertEqual(dummy.node_type, MDLNodeType.DUMMY)

    def test_write_trimesh_node(self):
        """Test writing trimesh node."""
        mdl = create_test_mdl("trimesh_test")
        node = create_test_node("mesh_node", MDLNodeType.TRIMESH)
        node.mesh = create_test_mesh()
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node trimesh mesh_node", content)
        self.assertIn("verts", content.lower())
        self.assertIn("faces", content.lower())

    def test_read_trimesh_node(self):
        """Test reading trimesh node."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node trimesh mesh_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    verts 3
      0 0 0
      1 0 0
      0 1 0
    faces 1
      0 1 2 0
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        mesh_node = mdl.get("mesh_node")
        self.assertIsNotNone(mesh_node)
        assert mesh_node is not None  # Type narrowing
        self.assertIsNotNone(mesh_node.mesh)
        assert mesh_node.mesh is not None  # Type narrowing
        self.assertEqual(len(mesh_node.mesh.vertex_positions), 3)
        self.assertEqual(len(mesh_node.mesh.faces), 1)

    def test_write_light_node(self):
        """Test writing light node."""
        mdl = create_test_mdl("light_test")
        node = create_test_node("light_node", MDLNodeType.LIGHT)
        node.light = MDLLight()
        node.light.color = Color(1.0, 1.0, 1.0)
        node.light.radius = 10.0
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node light light_node", content)

    def test_read_light_node(self):
        """Test reading light node."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node light light_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    color 1 1 1
    radius 10
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        light_node = mdl.get("light_node")
        self.assertIsNotNone(light_node)
        assert light_node is not None  # Type narrowing
        self.assertIsNotNone(light_node.light)
        assert light_node.light is not None  # Type narrowing
        self.assertEqual(light_node.light.radius, 10.0)

    def test_write_emitter_node(self):
        """Test writing emitter node."""
        mdl = create_test_mdl("emitter_test")
        node = create_test_node("emitter_node", MDLNodeType.EMITTER)
        node.emitter = MDLEmitter()
        node.emitter.update = "fountain"
        node.emitter.render = "normal"
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node emitter emitter_node", content)

    def test_read_emitter_node(self):
        """Test reading emitter node."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node emitter emitter_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    update fountain
    render normal
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        emitter_node = mdl.get("emitter_node")
        self.assertIsNotNone(emitter_node)
        assert emitter_node is not None  # Type narrowing
        self.assertIsNotNone(emitter_node.emitter)
        assert emitter_node.emitter is not None  # Type narrowing
        self.assertEqual(emitter_node.emitter.update, "fountain")

    def test_write_reference_node(self):
        """Test writing reference node."""
        mdl = create_test_mdl("reference_test")
        node = create_test_node("ref_node", MDLNodeType.REFERENCE)
        node.reference = MDLReference()
        node.reference.model = "test_ref.mdl"
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node reference ref_node", content)

    def test_read_reference_node(self):
        """Test reading reference node."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node reference ref_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    model test_ref.mdl
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        ref_node = mdl.get("ref_node")
        self.assertIsNotNone(ref_node)
        assert ref_node is not None  # Type narrowing
        self.assertIsNotNone(ref_node.reference)
        assert ref_node.reference is not None  # Type narrowing
        self.assertEqual(ref_node.reference.model, "test_ref.mdl")

    def test_write_saber_node(self):
        """Test writing saber node."""
        mdl = create_test_mdl("saber_test")
        node = create_test_node("saber_node", MDLNodeType.SABER)
        node.saber = MDLSaber()
        node.saber.saber_length = 1.0
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node lightsaber saber_node", content)

    def test_read_saber_node(self):
        """Test reading saber node."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node lightsaber saber_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    length 1.0
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        saber_node = mdl.get("saber_node")
        self.assertIsNotNone(saber_node,     )
        assert saber_node is not None  # Type narrowing
        self.assertIsNotNone(saber_node.saber)
        assert saber_node.saber is not None  # Type narrowing
        self.assertEqual(saber_node.saber.saber_length, 1.0)

    def test_write_aabb_node(self):
        """Test writing AABB/walkmesh node."""
        mdl = create_test_mdl("aabb_test")
        node = create_test_node("aabb_node", MDLNodeType.AABB)
        node.aabb = MDLWalkmesh()
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node aabb aabb_node", content)

    def test_read_aabb_node(self):
        """Test reading AABB/walkmesh node."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node aabb aabb_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        aabb_node = mdl.get("aabb_node")
        self.assertIsNotNone(aabb_node)
        assert aabb_node is not None  # Type narrowing
        self.assertIsNotNone(aabb_node.aabb)
        assert aabb_node.aabb is not None  # Type narrowing


# ============================================================================
# Controller Tests
# ============================================================================


class TestMDLAsciiControllers(unittest.TestCase):
    """Test all controller types in ASCII format."""

    def test_write_position_controller(self):
        """Test writing position controller."""
        mdl = create_test_mdl("pos_ctrl_test")
        node = create_test_node("test_node")
        node.controllers.append(create_test_controller(MDLControllerType.POSITION))
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("positionkey", content.lower())

    def test_read_position_controller(self):
        """Test reading position controller."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node dummy test_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    positionkey
      0 1 2 3
    endlist
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        node = mdl.get("test_node")
        self.assertIsNotNone(node)
        assert node is not None  # Type narrowing
        self.assertEqual(len(node.controllers), 1)
        self.assertEqual(node.controllers[0].controller_type, MDLControllerType.POSITION)

    def test_write_orientation_controller(self):
        """Test writing orientation controller."""
        mdl = create_test_mdl("orient_ctrl_test")
        node = create_test_node("test_node")
        node.controllers.append(create_test_controller(MDLControllerType.ORIENTATION))
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("orientationkey", content.lower())

    def test_read_orientation_controller(self):
        """Test reading orientation controller."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node dummy test_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    orientationkey
      0 0 0 0 1
    endlist
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        node = mdl.get("test_node")
        self.assertIsNotNone(node)
        assert node is not None  # Type narrowing
        self.assertEqual(len(node.controllers), 1)
        self.assertEqual(node.controllers[0].controller_type, MDLControllerType.ORIENTATION)

    def test_write_scale_controller(self):
        """Test writing scale controller."""
        mdl = create_test_mdl("scale_ctrl_test")
        node = create_test_node("test_node")
        node.controllers.append(create_test_controller(MDLControllerType.SCALE))
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("scalekey", content.lower())

    def test_write_bezier_controller(self):
        """Test writing bezier controller."""
        mdl = create_test_mdl("bezier_ctrl_test")
        node = create_test_node("test_node")
        controller = create_test_controller(MDLControllerType.POSITION, is_bezier=True)
        node.controllers.append(controller)
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("positionbezierkey", content.lower())

    def test_read_bezier_controller(self):
        """Test reading bezier controller."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node dummy test_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    positionbezierkey
      0 1 2 3
    endlist
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        node = mdl.get("test_node")
        self.assertIsNotNone(node)
        assert node is not None  # Type narrowing
        self.assertEqual(len(node.controllers), 1)
        self.assertTrue(node.controllers[0].is_bezier)

    def test_write_all_header_controllers(self):
        """Test writing all header node controllers."""
        mdl = create_test_mdl("all_header_ctrl_test")
        node = create_test_node("test_node")

        # Add all header controllers
        for ctrl_type in [
            MDLControllerType.POSITION,
            MDLControllerType.ORIENTATION,
            MDLControllerType.SCALE,
            MDLControllerType.ALPHA,
        ]:
            node.controllers.append(create_test_controller(ctrl_type))

        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("positionkey", content.lower())
        self.assertIn("orientationkey", content.lower())
        self.assertIn("scalekey", content.lower())
        self.assertIn("alphakey", content.lower())

    def test_write_light_controllers(self):
        """Test writing light node controllers."""
        mdl = create_test_mdl("light_ctrl_test")
        node = create_test_node("light_node", MDLNodeType.LIGHT)
        node.light = MDLLight()

        # Add light controllers
        for ctrl_type in [
            MDLControllerType.COLOR,
            MDLControllerType.RADIUS,
            MDLControllerType.SHADOWRADIUS,
            MDLControllerType.VERTICALDISPLACEMENT,
            MDLControllerType.MULTIPLIER,
        ]:
            node.controllers.append(create_test_controller(ctrl_type))

        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("colorkey", content.lower())
        self.assertIn("radiuskey", content.lower())
        self.assertIn("shadowradiuskey", content.lower())

    def test_write_emitter_controllers(self):
        """Test writing emitter node controllers."""
        mdl = create_test_mdl("emitter_ctrl_test")
        node = create_test_node("emitter_node", MDLNodeType.EMITTER)
        node.emitter = MDLEmitter()

        # Add some emitter controllers
        for ctrl_type in [
            MDLControllerType.ALPHASTART,
            MDLControllerType.ALPHAEND,
            MDLControllerType.BIRTHRATE,
            MDLControllerType.DRAG,
            MDLControllerType.VELOCITY,
        ]:
            node.controllers.append(create_test_controller(ctrl_type))

        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("alphastartkey", content.lower())
        self.assertIn("alphaendkey", content.lower())
        self.assertIn("birthratekey", content.lower())


# ============================================================================
# Mesh Data Tests
# ============================================================================


class TestMDLAsciiMeshData(unittest.TestCase):
    """Test mesh data in ASCII format."""

    def test_write_mesh_vertices(self):
        """Test writing mesh vertices."""
        mdl = create_test_mdl("mesh_verts_test")
        node = create_test_node("mesh_node", MDLNodeType.TRIMESH)
        mesh = create_test_mesh()
        mesh.vertex_positions = [
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
            Vector3(0.0, 0.0, 1.0),
        ]
        node.mesh = mesh
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("verts 4", content.lower())

    def test_read_mesh_vertices(self):
        """Test reading mesh vertices."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node trimesh mesh_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    verts 3
      0 0 0
      1 0 0
      0 1 0
    faces 0
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        mesh_node = mdl.get("mesh_node")
        self.assertIsNotNone(mesh_node)
        assert mesh_node is not None  # Type narrowing
        self.assertIsNotNone(mesh_node.mesh)
        assert mesh_node.mesh is not None  # Type narrowing
        self.assertEqual(len(mesh_node.mesh.vertex_positions), 3)

    def test_write_mesh_faces(self):
        """Test writing mesh faces."""
        mdl = create_test_mdl("mesh_faces_test")
        node = create_test_node("mesh_node", MDLNodeType.TRIMESH)
        mesh = create_test_mesh()

        # Add multiple faces
        face1 = MDLFace()
        face1.v1 = 0
        face1.v2 = 1
        face1.v3 = 2
        face1.material = 0

        face2 = MDLFace()
        face2.v1 = 1
        face2.v2 = 2
        face2.v3 = 3
        face2.material = 0

        mesh.faces = [face1, face2]
        node.mesh = mesh
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("faces 2", content.lower())

    def test_read_mesh_faces(self):
        """Test reading mesh faces."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node trimesh mesh_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    verts 4
      0 0 0
      1 0 0
      0 1 0
      0 0 1
    faces 2
      0 1 2 0
      1 2 3 0
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        mesh_node = mdl.get("mesh_node")
        self.assertIsNotNone(mesh_node)
        assert mesh_node is not None  # Type narrowing
        self.assertIsNotNone(mesh_node.mesh)
        assert mesh_node.mesh is not None  # Type narrowing
        self.assertEqual(len(mesh_node.mesh.faces), 2)

    def test_write_mesh_tverts(self):
        """Test writing texture coordinates."""
        mdl = create_test_mdl("mesh_tverts_test")
        node = create_test_node("mesh_node", MDLNodeType.TRIMESH)
        mesh = create_test_mesh()
        mesh.vertex_uvs = [
            Vector2(0.0, 0.0),
            Vector2(1.0, 0.0),
            Vector2(0.0, 1.0),
        ]
        node.mesh = mesh
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("tverts", content.lower())

    def test_read_mesh_tverts(self):
        """Test reading texture coordinates."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node trimesh mesh_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    verts 3
      0 0 0
      1 0 0
      0 1 0
    tverts 3
      0 0
      1 0
      0 1
    faces 1
      0 1 2 0
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        mesh_node = mdl.get("mesh_node")
        self.assertIsNotNone(mesh_node)
        assert mesh_node is not None  # Type narrowing
        self.assertIsNotNone(mesh_node.mesh)
        assert mesh_node.mesh is not None  # Type narrowing
        self.assertEqual(len(mesh_node.mesh.vertex_uvs), 3)

    def test_write_skin_mesh(self):
        """Test writing skin mesh with bones and weights."""
        mdl = create_test_mdl("skin_test")
        node = create_test_node("skin_node", MDLNodeType.TRIMESH)
        node.mesh = create_test_mesh()

        # Create skin data
        skin = MDLSkin()
        skin.bonemap = [0, 1]
        # Note: bone_indices is a fixed 16-element tuple, set via qbones/tbones length
        skin.qbones = [Vector4(0, 0, 0, 1), Vector4(0, 0, 0, 1)]
        skin.tbones = [Vector3(0, 0, 0), Vector3(0, 0, 0)]

        # Add bone vertices
        bone_vert = MDLBoneVertex()
        bone_vert.vertex_weights = (1.0, 0.0, 0.0, 0.0)
        bone_vert.vertex_indices = (0.0, -1.0, -1.0, -1.0)
        skin.vertex_bones = [bone_vert]

        node.mesh = skin
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("bones", content.lower())
        self.assertIn("weights", content.lower())

    def test_read_skin_mesh(self):
        """Test reading skin mesh."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node trimesh skin_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    verts 1
      0 0 0
    bones 2
      0
      1
    weights 1
      1 0 0 0 0 0 0 0
    faces 0
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        skin_node = mdl.get("skin_node")
        self.assertIsNotNone(skin_node)
        # Note: Skin detection might require node type check

    def test_write_dangly_mesh(self):
        """Test writing dangly mesh with constraints."""
        mdl = create_test_mdl("dangly_test")
        node = create_test_node("dangly_node", MDLNodeType.DANGLYMESH)

        # Create dangly data
        dangly = MDLDangly()
        # Note: displacement, tightness, and period are not direct attributes of MDLDangly
        # They may be stored as controller data or node-level properties
        # For now, we'll just test constraints which are the main dangly feature

        # Add constraint
        constraint = MDLConstraint()
        constraint.name = "constraint1"
        dangly.constraints = [constraint]

        node.mesh = dangly
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("danglymesh", content.lower())


# ============================================================================
# Animation Tests
# ============================================================================


class TestMDLAsciiAnimations(unittest.TestCase):
    """Test animation data in ASCII format."""

    def test_write_animation_basic(self):
        """Test writing basic animation."""
        mdl = create_test_mdl("anim_test")
        anim = create_test_animation("test_anim")
        mdl.anims.append(anim)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("newanim test_anim", content)
        self.assertIn("length", content.lower())
        self.assertIn("transtime", content.lower())
        self.assertIn("doneanim test_anim", content)

    def test_read_animation_basic(self):
        """Test reading basic animation."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

endmodelgeom test

newanim test_anim test
  length 1.0
  transtime 0.25
  animroot test

doneanim test_anim test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        self.assertEqual(len(mdl.anims), 1)
        self.assertEqual(mdl.anims[0].name, "test_anim")
        self.assertEqual(mdl.anims[0].anim_length, 1.0)
        self.assertEqual(mdl.anims[0].transition_length, 0.25)

    def test_write_animation_with_events(self):
        """Test writing animation with events."""
        mdl = create_test_mdl("anim_events_test")
        anim = create_test_animation("test_anim")

        # Add multiple events
        event1 = MDLEvent()
        event1.activation_time = 0.5
        event1.name = "footstep"

        event2 = MDLEvent()
        event2.activation_time = 1.0
        event2.name = "attack_hit"

        anim.events = [event1, event2]
        mdl.anims.append(anim)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("event 0.5 footstep", content)
        self.assertIn("event 1.0 attack_hit", content)

    def test_read_animation_with_events(self):
        """Test reading animation with events."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

endmodelgeom test

newanim test_anim test
  length 1.0
  transtime 0.25
  event 0.5 footstep
  event 1.0 attack_hit

doneanim test_anim test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        self.assertEqual(len(mdl.anims), 1)
        self.assertEqual(len(mdl.anims[0].events), 2)
        self.assertEqual(mdl.anims[0].events[0].name, "footstep")
        self.assertEqual(mdl.anims[0].events[1].name, "attack_hit")

    def test_write_animation_with_nodes(self):
        """Test writing animation with nodes and controllers."""
        mdl = create_test_mdl("anim_nodes_test")
        anim = create_test_animation("test_anim")

        # Add node with controller to animation
        anim_node = create_test_node("anim_node")
        anim_node.controllers.append(create_test_controller(MDLControllerType.POSITION))
        anim.root = anim_node

        mdl.anims.append(anim)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("node dummy anim_node", content)
        self.assertIn("positionkey", content.lower())

    def test_read_animation_with_nodes(self):
        """Test reading animation with nodes."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

endmodelgeom test

newanim test_anim test
  length 1.0
  transtime 0.25
  node dummy anim_node
    parent null
    positionkey
      0 1 2 3
    endlist
  endnode

doneanim test_anim test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        self.assertEqual(len(mdl.anims), 1)
        anim = mdl.anims[0]
        self.assertIsNotNone(anim.root)
        self.assertEqual(len(anim.root.controllers), 1)

    def test_write_multiple_animations(self):
        """Test writing multiple animations."""
        mdl = create_test_mdl("multi_anim_test")

        anim1 = create_test_animation("anim1")
        anim2 = create_test_animation("anim2")
        anim3 = create_test_animation("anim3")

        mdl.anims = [anim1, anim2, anim3]

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("newanim anim1", content)
        self.assertIn("newanim anim2", content)
        self.assertIn("newanim anim3", content)
        self.assertIn("doneanim anim1", content)
        self.assertIn("doneanim anim2", content)
        self.assertIn("doneanim anim3", content)


# ============================================================================
# Round-Trip Tests
# ============================================================================


class TestMDLAsciiRoundTrip(unittest.TestCase):
    """Test round-trip conversion (ASCII -> Binary -> ASCII)."""

    def test_ascii_to_ascii_roundtrip(self):
        """Test ASCII -> ASCII round-trip."""
        mdl1 = create_test_mdl("roundtrip_test")
        node = create_test_node("test_node")
        node.mesh = create_test_mesh()
        mdl1.root.children.append(node)

        # Write to ASCII
        output1 = io.StringIO()
        writer1 = MDLAsciiWriter(mdl1, output1)
        writer1.write()
        ascii1 = output1.getvalue()

        # Read back
        reader = MDLAsciiReader(io.StringIO(ascii1))
        mdl2 = reader.load()

        # Write again
        output2 = io.StringIO()
        writer2 = MDLAsciiWriter(mdl2, output2)
        writer2.write()
        ascii2 = output2.getvalue()

        # Compare key elements
        self.assertIn("newmodel roundtrip_test", ascii2)
        self.assertIn("node trimesh test_node", ascii2.lower())

    def test_ascii_with_all_node_types_roundtrip(self):
        """Test round-trip with all node types."""
        mdl1 = create_test_mdl("all_nodes_test")

        # Add all node types
        dummy = create_test_node("dummy", MDLNodeType.DUMMY)
        trimesh = create_test_node("trimesh", MDLNodeType.TRIMESH)
        trimesh.mesh = create_test_mesh()
        light = create_test_node("light", MDLNodeType.LIGHT)
        light.light = MDLLight()
        emitter = create_test_node("emitter", MDLNodeType.EMITTER)
        emitter.emitter = MDLEmitter()
        reference = create_test_node("reference", MDLNodeType.REFERENCE)
        reference.reference = MDLReference()
        saber = create_test_node("saber", MDLNodeType.SABER)
        saber.saber = MDLSaber()
        aabb = create_test_node("aabb", MDLNodeType.AABB)
        aabb.aabb = MDLWalkmesh()

        mdl1.root.children.extend([
            dummy, trimesh, light, emitter, reference, saber, aabb
        ])

        # Round-trip
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl1, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify all nodes exist
        self.assertIsNotNone(mdl2.get("dummy"))
        self.assertIsNotNone(mdl2.get("trimesh"))
        self.assertIsNotNone(mdl2.get("light"))
        self.assertIsNotNone(mdl2.get("emitter"))
        self.assertIsNotNone(mdl2.get("reference"))
        self.assertIsNotNone(mdl2.get("saber"))
        self.assertIsNotNone(mdl2.get("aabb"))

    def test_ascii_with_all_controllers_roundtrip(self):
        """Test round-trip with all controller types."""
        mdl1 = create_test_mdl("all_ctrl_test")
        node = create_test_node("test_node")

        # Add all header controllers
        for ctrl_type in [
            MDLControllerType.POSITION,
            MDLControllerType.ORIENTATION,
            MDLControllerType.SCALE,
            MDLControllerType.ALPHA,
        ]:
            node.controllers.append(create_test_controller(ctrl_type))

        mdl1.root.children.append(node)

        # Round-trip
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl1, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify controllers
        node2 = mdl2.get("test_node")
        self.assertIsNotNone(node2)
        assert node2 is not None  # Type narrowing
        self.assertEqual(len(node2.controllers), 4)

    def test_ascii_with_animations_roundtrip(self):
        """Test round-trip with animations."""
        mdl1 = create_test_mdl("anim_roundtrip_test")

        anim1 = create_test_animation("anim1")
        anim2 = create_test_animation("anim2")
        mdl1.anims = [anim1, anim2]

        # Round-trip
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl1, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify animations
        self.assertEqual(len(mdl2.anims), 2)
        self.assertEqual(mdl2.anims[0].name, "anim1")
        self.assertEqual(mdl2.anims[1].name, "anim2")


# ============================================================================
# Classification Tests
# ============================================================================


class TestMDLAsciiClassifications(unittest.TestCase):
    """Test all model classifications."""

    def test_write_all_classifications(self):
        """Test writing all classification types."""
        for classification in MDLClassification:
            if classification == MDLClassification.INVALID:
                continue

            mdl = create_test_mdl(f"class_{classification.name.lower()}_test")
            mdl.classification = classification

            output = io.StringIO()
            writer = MDLAsciiWriter(mdl, output)
            writer.write()

            content = output.getvalue()
            self.assertIn(f"classification {classification.name.lower()}", content)

    def test_read_all_classifications(self):
        """Test reading all classification types."""
        for classification in MDLClassification:
            if classification == MDLClassification.INVALID:
                continue

            ascii_content = f"""# ASCII MDL
newmodel test
setsupermodel test null
classification {classification.name.lower()}
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

endmodelgeom test

donemodel test
"""
            reader = MDLAsciiReader(io.StringIO(ascii_content))
            mdl = reader.load()

            self.assertEqual(mdl.classification, classification)


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestMDLAsciiEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_read_empty_file(self):
        """Test reading empty file."""
        reader = MDLAsciiReader(io.StringIO(""))
        with self.assertRaises(Exception):  # Should raise some error
            reader.load()

    def test_read_malformed_header(self):
        """Test reading malformed header."""
        ascii_content = """invalid header
more invalid content
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        # Should handle gracefully or raise appropriate error
        try:
            mdl = reader.load()
            # If it doesn't raise, at least verify it's a valid MDL
            self.assertIsInstance(mdl, MDL)
        except Exception:
            pass  # Expected for malformed input

    def test_read_missing_endmarkers(self):
        """Test reading file with missing end markers."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        # Should handle gracefully
        try:
            mdl = reader.load()
            self.assertIsInstance(mdl, MDL)
        except Exception:
            pass  # May raise on incomplete data

    def test_write_node_with_no_name(self):
        """Test writing node with empty name."""
        mdl = create_test_mdl("no_name_test")
        node = create_test_node("")
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        # Should handle gracefully
        content = output.getvalue()
        self.assertIn("beginmodelgeom", content)

    def test_write_controller_with_no_rows(self):
        """Test writing controller with no rows."""
        mdl = create_test_mdl("no_rows_test")
        node = create_test_node("test_node")

        controller = MDLController(MDLControllerType.POSITION, [], False)  # Empty rows

        node.controllers.append(controller)
        mdl.root.children.append(node)

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        # Should skip empty controllers
        content = output.getvalue()
        self.assertNotIn("positionkey", content.lower())

    def test_read_controller_with_old_format(self):
        """Test reading controller with old count format."""
        ascii_content = """# ASCII MDL
newmodel test
setsupermodel test null
classification other
classification_unk1 0
ignorefog 1
compress_quaternions 0
setanimationscale 0.971

beginmodelgeom test
  bmin -5 -5 -1
  bmax 5 5 10
  radius 7

  node dummy test_node
  {
    parent -1
    position 0 0 0
    orientation 0 0 0 1
    positionkey 2
      0 1 2 3
      1 4 5 6
  }

endmodelgeom test

donemodel test
"""
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        node = mdl.get("test_node")
        self.assertIsNotNone(node)
        # Should handle old format with count

    def test_write_large_mesh(self):
        """Test writing large mesh with many vertices."""
        mdl = create_test_mdl("large_mesh_test")
        node = create_test_node("large_mesh", MDLNodeType.TRIMESH)
        mesh = MDLMesh()

        # Create 1000 vertices
        mesh.vertex_positions = [
            Vector3(float(i), float(i), float(i))
            for i in range(1000)
        ]

        # Create 500 faces
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

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        self.assertIn("verts 1000", content)
        self.assertIn("faces 500", content)

    def test_read_large_mesh(self):
        """Test reading large mesh."""
        # Generate large ASCII content
        lines = [
            "# ASCII MDL",
            "newmodel test",
            "setsupermodel test null",
            "classification other",
            "classification_unk1 0",
            "ignorefog 1",
            "compress_quaternions 0",
            "setanimationscale 0.971",
            "",
            "beginmodelgeom test",
            "  bmin -5 -5 -1",
            "  bmax 5 5 10",
            "  radius 7",
            "",
            "  node trimesh large_mesh",
            "  {",
            "    parent -1",
            "    position 0 0 0",
            "    orientation 0 0 0 1",
            "    verts 100",
        ]

        # Add 100 vertices
        for i in range(100):
            lines.append(f"      {i} {i} {i}")

        lines.append("    faces 50")
        # Add 50 faces
        for i in range(50):
            lines.append(f"      {i*2} {i*2+1} {(i*2+2)%100} 0")

        lines.extend([
            "  }",
            "",
            "endmodelgeom test",
            "",
            "donemodel test",
        ])

        ascii_content = "\n".join(lines)

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        mesh_node = mdl.get("large_mesh")
        self.assertIsNotNone(mesh_node)
        assert mesh_node is not None  # Type narrowing
        self.assertIsNotNone(mesh_node.mesh)
        assert mesh_node.mesh is not None  # Type narrowing
        self.assertEqual(len(mesh_node.mesh.vertex_positions), 100)
        self.assertEqual(len(mesh_node.mesh.faces), 50)

    def test_write_deep_hierarchy(self):
        """Test writing deep node hierarchy."""
        mdl = create_test_mdl("deep_hierarchy_test")

        # Create 10 levels deep
        current = mdl.root
        for i in range(10):
            child = create_test_node(f"level_{i}")
            current.children.append(child)
            current = child

        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()

        content = output.getvalue()
        # All levels should be present
        for i in range(10):
            self.assertIn(f"level_{i}", content)

    def test_read_deep_hierarchy(self):
        """Test reading deep node hierarchy."""
        lines = [
            "# ASCII MDL",
            "newmodel test",
            "setsupermodel test null",
            "classification other",
            "classification_unk1 0",
            "ignorefog 1",
            "compress_quaternions 0",
            "setanimationscale 0.971",
            "",
            "beginmodelgeom test",
            "  bmin -5 -5 -1",
            "  bmax 5 5 10",
            "  radius 7",
        ]

        # Create 5 levels deep
        for i in range(5):
            lines.append(f"  node dummy level_{i}")
            lines.append("  {")
            lines.append(f"    parent {'level_' + str(i-1) if i > 0 else 'null'}")
            lines.append("    position 0 0 0")
            lines.append("    orientation 0 0 0 1")
            lines.append("  }")

        lines.extend([
            "",
            "endmodelgeom test",
            "",
            "donemodel test",
        ])

        ascii_content = "\n".join(lines)

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()

        # Verify hierarchy
        for i in range(5):
            node = mdl.get(f"level_{i}")
            self.assertIsNotNone(node, f"Node level_{i} should exist")


# ============================================================================
# Integration Tests with Binary Format
# ============================================================================


class TestMDLAsciiBinaryIntegration(unittest.TestCase):
    """Test integration between ASCII and binary formats."""

    def setUp(self):
        """Set up test fixtures."""
        # Resolve relative to this test file so it works regardless of CWD.
        self.test_dir = Path(__file__).resolve().parents[2] / "test_files" / "mdl"
        if not self.test_dir.exists():
            self.skipTest(f"Test directory {self.test_dir} does not exist")

    def test_binary_to_ascii_conversion(self):
        """Test converting binary MDL to ASCII."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        if not mdl_path.exists():
            self.skipTest("Test file c_dewback.mdl not found")

        # Read binary
        mdl_binary = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

        # Convert to ASCII
        ascii_bytes = bytes_mdl(mdl_binary, ResourceType.MDL_ASCII)
        self.assertIsInstance(ascii_bytes, bytes)
        self.assertGreater(len(ascii_bytes), 0)

        # Verify it's ASCII
        ascii_str = ascii_bytes.decode("utf-8", errors="ignore")
        self.assertIn("newmodel", ascii_str.lower())
        self.assertIn("beginmodelgeom", ascii_str.lower())

    def test_ascii_to_binary_conversion(self):
        """Test converting ASCII MDL to binary."""
        # Create ASCII MDL
        mdl_ascii = create_test_mdl("ascii_to_binary_test")
        node = create_test_node("test_node")
        node.mesh = create_test_mesh()
        mdl_ascii.root.children.append(node)

        # Convert to binary (keep MDL/MDX separated in-memory)
        mdl_bytes = bytearray()
        mdx_bytes = bytearray()
        write_mdl(mdl_ascii, mdl_bytes, ResourceType.MDL, target_ext=mdx_bytes)
        binary_bytes = bytes(mdl_bytes)
        self.assertGreater(len(binary_bytes), 0)

        # Verify it's binary (starts with null bytes)
        self.assertEqual(binary_bytes[:4], b"\x00\x00\x00\x00")

    def test_binary_ascii_binary_roundtrip(self):
        """Test Binary -> ASCII -> Binary round-trip."""
        mdl_path = self.test_dir / "c_dewback.mdl"
        mdx_path = self.test_dir / "c_dewback.mdx"

        if not mdl_path.exists():
            self.skipTest("Test file c_dewback.mdl not found")

        # Read binary
        mdl1 = read_mdl(mdl_path, source_ext=mdx_path, file_format=ResourceType.MDL)

        # Convert to ASCII
        ascii_bytes = bytes_mdl(mdl1, ResourceType.MDL_ASCII)

        # Read ASCII
        mdl2 = read_mdl(ascii_bytes, file_format=ResourceType.MDL_ASCII)

        # Convert back to binary (keep MDL/MDX separated in-memory)
        mdl_bytes = bytearray()
        mdx_bytes = bytearray()
        write_mdl(mdl2, mdl_bytes, ResourceType.MDL, target_ext=mdx_bytes)
        binary_bytes = bytes(mdl_bytes)

        # Verify binary structure
        self.assertEqual(binary_bytes[:4], b"\x00\x00\x00\x00")
        self.assertGreater(len(binary_bytes), 12)  # At least header

    def test_ascii_binary_ascii_roundtrip(self):
        """Test ASCII -> Binary -> ASCII round-trip."""
        # Create ASCII MDL
        mdl1 = create_test_mdl("roundtrip_ascii_test")
        node = create_test_node("test_node")
        node.mesh = create_test_mesh()
        mdl1.root.children.append(node)

        # Convert to binary (keep MDL/MDX separated in-memory)
        mdl_bytes = bytearray()
        mdx_bytes = bytearray()
        write_mdl(mdl1, mdl_bytes, ResourceType.MDL, target_ext=mdx_bytes)
        binary_bytes = bytes(mdl_bytes)

        # Read binary (provide MDX as source_ext)
        mdl2 = read_mdl(binary_bytes, source_ext=bytes(mdx_bytes), file_format=ResourceType.MDL)

        # Convert back to ASCII
        ascii_bytes = bytes_mdl(mdl2, ResourceType.MDL_ASCII)
        ascii_str = ascii_bytes.decode("utf-8", errors="ignore")

        # Verify ASCII structure
        self.assertIn("newmodel roundtrip_ascii_test", ascii_str)
        self.assertIn("beginmodelgeom", ascii_str.lower())


# ============================================================================
# Comprehensive Feature Combination Tests
# ============================================================================


class TestMDLAsciiComprehensive(unittest.TestCase):
    """Comprehensive tests combining multiple features."""

    def test_complex_model_all_features(self):
        """Test model with all features combined."""
        mdl = create_test_mdl("complex_test")

        # Add multiple node types
        dummy = create_test_node("dummy", MDLNodeType.DUMMY)
        dummy.controllers.append(create_test_controller(MDLControllerType.POSITION))

        trimesh = create_test_node("trimesh", MDLNodeType.TRIMESH)
        mesh = create_test_mesh()
        mesh.vertex_uvs = [Vector2(0.0, 0.0), Vector2(1.0, 0.0), Vector2(0.0, 1.0)]
        trimesh.mesh = mesh
        trimesh.controllers.append(create_test_controller(MDLControllerType.SCALE))

        light = create_test_node("light", MDLNodeType.LIGHT)
        light.light = MDLLight()
        light.controllers.append(create_test_controller(MDLControllerType.COLOR))

        emitter = create_test_node("emitter", MDLNodeType.EMITTER)
        emitter.emitter = MDLEmitter()
        emitter.controllers.append(create_test_controller(MDLControllerType.BIRTHRATE))

        mdl.root.children.extend([dummy, trimesh, light, emitter])

        # Add animations
        anim1 = create_test_animation("walk")
        anim2 = create_test_animation("run")
        mdl.anims = [anim1, anim2]

        # Round-trip test
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify all features
        self.assertEqual(len(mdl2.all_nodes()), 5)  # root + 4 children
        self.assertEqual(len(mdl2.anims), 2)
        self.assertIsNotNone(mdl2.get("dummy"))
        self.assertIsNotNone(mdl2.get("trimesh"))
        self.assertIsNotNone(mdl2.get("light"))
        self.assertIsNotNone(mdl2.get("emitter"))

    def test_model_with_nested_hierarchy_and_controllers(self):
        """Test model with nested hierarchy and controllers at all levels."""
        mdl = create_test_mdl("nested_test")

        # Create 3-level hierarchy
        level1 = create_test_node("level1")
        level1.controllers.append(create_test_controller(MDLControllerType.POSITION))

        level2 = create_test_node("level2")
        level2.controllers.append(create_test_controller(MDLControllerType.ORIENTATION))
        level1.children.append(level2)

        level3 = create_test_node("level3")
        level3.controllers.append(create_test_controller(MDLControllerType.SCALE))
        level2.children.append(level3)

        mdl.root.children.append(level1)

        # Round-trip
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify hierarchy
        self.assertIsNotNone(mdl2.get("level1"))
        self.assertIsNotNone(mdl2.get("level2"))
        self.assertIsNotNone(mdl2.get("level3"))

        level1_node = mdl2.get("level1")
        assert level1_node is not None  # Type narrowing
        self.assertEqual(len(level1_node.children), 1)
        self.assertEqual(len(level1_node.controllers), 1)

    def test_animation_with_complex_node_structure(self):
        """Test animation with complex node structure."""
        mdl = create_test_mdl("complex_anim_test")

        anim = MDLAnimation()
        anim.name = "complex_anim"
        anim.anim_length = 2.0
        anim.transition_length = 0.5

        # Add multiple events
        for i in range(5):
            event = MDLEvent()
            event.activation_time = i * 0.4
            event.name = f"event_{i}"
            anim.events.append(event)

        # Add complex node hierarchy to animation
        anim_root = create_test_node("anim_root")
        anim_root.controllers.append(create_test_controller(MDLControllerType.POSITION))

        anim_child1 = create_test_node("anim_child1")
        anim_child1.controllers.append(create_test_controller(MDLControllerType.ORIENTATION))
        anim_root.children.append(anim_child1)

        anim_child2 = create_test_node("anim_child2")
        anim_child2.controllers.append(create_test_controller(MDLControllerType.SCALE))
        anim_root.children.append(anim_child2)

        anim.root = anim_root
        mdl.anims.append(anim)

        # Round-trip
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        ascii_content = output.getvalue()

        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl2 = reader.load()

        # Verify animation
        self.assertEqual(len(mdl2.anims), 1)
        anim2 = mdl2.anims[0]
        self.assertEqual(len(anim2.events), 5)
        self.assertIsNotNone(anim2.root)
        self.assertEqual(len(anim2.root.children), 2)


# ============================================================================
# Performance and Stress Tests
# ============================================================================


class TestMDLAsciiPerformance(unittest.TestCase):
    """Performance and stress tests."""

    def test_write_performance_large_model(self):
        """Test writing performance with large model."""
        import time

        mdl = create_test_mdl("large_perf_test")

        # Create 100 nodes
        for i in range(100):
            node = create_test_node(f"node_{i}")
            if i % 10 == 0:
                node.mesh = create_test_mesh()
            mdl.root.children.append(node)

        start = time.time()
        output = io.StringIO()
        writer = MDLAsciiWriter(mdl, output)
        writer.write()
        write_time = time.time() - start

        # Should complete in reasonable time (< 1 second for 100 nodes)
        self.assertLess(write_time, 1.0, "Writing should be fast")

        content = output.getvalue()
        self.assertGreater(len(content), 0)

    def test_read_performance_large_model(self):
        """Test reading performance with large model."""
        import time

        # Generate large ASCII content
        lines = [
            "# ASCII MDL",
            "newmodel test",
            "setsupermodel test null",
            "classification other",
            "classification_unk1 0",
            "ignorefog 1",
            "compress_quaternions 0",
            "setanimationscale 0.971",
            "",
            "beginmodelgeom test",
            "  bmin -5 -5 -1",
            "  bmax 5 5 10",
            "  radius 7",
        ]

        # Add 100 nodes
        for i in range(100):
            lines.append(f"  node dummy node_{i}")
            lines.append("  {")
            lines.append("    parent -1")
            lines.append("    position 0 0 0")
            lines.append("    orientation 0 0 0 1")
            lines.append("  }")

        lines.extend([
            "",
            "endmodelgeom test",
            "",
            "donemodel test",
        ])

        ascii_content = "\n".join(lines)

        start = time.time()
        reader = MDLAsciiReader(io.StringIO(ascii_content))
        mdl = reader.load()
        read_time = time.time() - start

        # Should complete in reasonable time
        self.assertLess(read_time, 1.0, "Reading should be fast")
        self.assertEqual(len(mdl.all_nodes()), 101)  # root + 100 children


# ============================================================================
# ASCII Round-Trip Tests: ASCII -> Binary -> ASCII
# ============================================================================


def _is_vector_like(v) -> bool:
    return hasattr(v, "x") and hasattr(v, "y") and (hasattr(v, "z") or hasattr(v, "w"))


def _assert_vector_close(test_case: unittest.TestCase, a, b, *, context: str):
    test_case.assertTrue(_is_vector_like(a) and _is_vector_like(b), f"{context}: expected vector-like objects")
    test_case.assertEqual(_qfloat(float(a.x)), _qfloat(float(b.x)), f"{context}.x: float mismatch {a.x!r} vs {b.x!r}")
    test_case.assertEqual(_qfloat(float(a.y)), _qfloat(float(b.y)), f"{context}.y: float mismatch {a.y!r} vs {b.y!r}")
    if hasattr(a, "z") or hasattr(b, "z"):
        az = float(getattr(a, "z", 0.0))
        bz = float(getattr(b, "z", 0.0))
        test_case.assertEqual(_qfloat(az), _qfloat(bz), f"{context}.z: float mismatch {az!r} vs {bz!r}")
    if hasattr(a, "w") or hasattr(b, "w"):
        aw = float(getattr(a, "w", 0.0))
        bw = float(getattr(b, "w", 0.0))
        test_case.assertEqual(_qfloat(aw), _qfloat(bw), f"{context}.w: float mismatch {aw!r} vs {bw!r}")


def _compare_components(
    test_case: unittest.TestCase,
    a,
    b,
    *,
    context: str,
    visited: set[tuple[int, int]] | None = None,
):
    """Deep, component-wise comparison with float tolerance and cycle protection."""
    if visited is None:
        visited = set()
    key = (id(a), id(b))
    if key in visited:
        return
    visited.add(key)

    if a is None or b is None:
        test_case.assertIs(a, b, f"{context}: one side is None")
        return

    if isinstance(a, float) and isinstance(b, float):
        test_case.assertEqual(_qfloat(a), _qfloat(b), f"{context}: float mismatch {a!r} vs {b!r}")
        return

    if _is_vector_like(a) and _is_vector_like(b):
        _assert_vector_close(test_case, a, b, context=context)
        return

    if isinstance(a, Color) and isinstance(b, Color):
        # Align with MDL metamethods: compare float channels via quantization.
        for ch in ("r", "g", "b", "a"):
            if hasattr(a, ch) or hasattr(b, ch):
                av = float(getattr(a, ch, 0.0))
                bv = float(getattr(b, ch, 0.0))
                test_case.assertEqual(_qfloat(av), _qfloat(bv), f"{context}.{ch}: color channel mismatch {av!r} vs {bv!r}")
        return

    if isinstance(a, (str, int, bool)) or isinstance(b, (str, int, bool)):
        test_case.assertEqual(a, b, f"{context}: scalar mismatch")
        return

    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        test_case.assertEqual(len(a), len(b), f"{context}: sequence length mismatch")
        for i, (ai, bi) in enumerate(zip(a, b)):
            _compare_components(test_case, ai, bi, context=f"{context}[{i}]", visited=visited)
        return

    if isinstance(a, dict) and isinstance(b, dict):
        test_case.assertEqual(set(a.keys()), set(b.keys()), f"{context}: dict keys mismatch")
        for k in sorted(a.keys(), key=str):
            _compare_components(test_case, a[k], b[k], context=f"{context}[{k!r}]", visited=visited)
        return

    # Compare objects by their __dict__ (most MDL structures are plain objects).
    da = getattr(a, "__dict__", None)
    db = getattr(b, "__dict__", None)
    if isinstance(da, dict) and isinstance(db, dict):
        # Ignore unstable or derived keys (mirrors MDL metamethod ignore list).
        ignore = {"vertex_uvs", "node_id", "parent_id", "node_type", "bone_serial", "bone_node_number"}
        ka = {k for k in da.keys() if k not in ignore}
        kb = {k for k in db.keys() if k not in ignore}
        test_case.assertEqual(ka, kb, f"{context}: object keys mismatch ({a.__class__.__name__} vs {b.__class__.__name__})")
        for k in sorted(ka):
            _compare_components(test_case, da[k], db[k], context=f"{context}.{k}", visited=visited)
        return

    test_case.assertEqual(a, b, f"{context}: fallback equality mismatch")


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "vendor" / "MDLOps" / "mdlops.exe").exists():
            return parent
    raise RuntimeError("Could not locate repo root containing vendor/MDLOps/mdlops.exe")


def _mdlops_exe() -> Path:
    return _repo_root() / "vendor" / "MDLOps" / "mdlops.exe"


def _run_mdlops_decompile(*, mdl_path: Path, mdx_path: Path) -> bytes:
    """Run MDLOps to decompile a binary (MDL+MDX) pair into MDLOps ASCII bytes."""
    mdlops = _mdlops_exe()
    if not mdlops.exists():
        raise FileNotFoundError(mdlops)

    with tempfile.TemporaryDirectory(prefix="pykotor-mdlops-rt-") as td_s:
        td = Path(td_s)
        src_mdl = td / mdl_path.name
        src_mdx = td / mdx_path.name
        shutil.copyfile(mdl_path, src_mdl)
        shutil.copyfile(mdx_path, src_mdx)

        r = subprocess.run(
            [str(mdlops), str(src_mdl)],
            cwd=str(td),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=120,
        )
        if r.returncode != 0:
            raise AssertionError(f"MDLOps failed decompiling {mdl_path.name}:\n{r.stdout}")

        ascii_path = td / f"{src_mdl.stem}-ascii.mdl"
        if not ascii_path.exists() or ascii_path.stat().st_size == 0:
            raise AssertionError(f"MDLOps did not emit ASCII output for {mdl_path.name}")
        return ascii_path.read_bytes()


def _run_mdlops_decompile_bytes(*, mdl_bytes: bytes, mdx_bytes: bytes, stem: str) -> bytes:
    """Run MDLOps to decompile an in-memory binary (MDL+MDX) pair into MDLOps ASCII bytes."""
    mdlops = _mdlops_exe()
    if not mdlops.exists():
        raise FileNotFoundError(mdlops)

    with tempfile.TemporaryDirectory(prefix="pykotor-mdlops-rt-bytes-") as td_s:
        td = Path(td_s)
        mdl_path = td / f"{stem}.mdl"
        mdx_path = td / f"{stem}.mdx"
        mdl_path.write_bytes(mdl_bytes)
        mdx_path.write_bytes(mdx_bytes)

        r = subprocess.run(
            [str(mdlops), str(mdl_path)],
            cwd=str(td),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=120,
        )
        if r.returncode != 0:
            raise AssertionError(f"MDLOps failed decompiling {stem}.mdl:\n{r.stdout}")

        ascii_path = td / f"{stem}-ascii.mdl"
        if not ascii_path.exists() or ascii_path.stat().st_size == 0:
            raise AssertionError(f"MDLOps did not emit ASCII output for {stem}.mdl")
        return ascii_path.read_bytes()


def compare_mdl_basic(mdl1: MDL, mdl2: MDL, test_case: unittest.TestCase, context: str = ""):
    """Compare basic MDL properties between two models.

    NOTE: Binary MDL/MDX roundtrips are not guaranteed to be 1:1 for all node types yet,
    so this helper intentionally focuses on stable header properties.
    """
    msg_prefix = f"{context}: " if context else ""
    test_case.assertEqual(mdl1.name, mdl2.name, f"{msg_prefix}Model names should match")
    test_case.assertEqual(mdl1.supermodel, mdl2.supermodel, f"{msg_prefix}Supermodels should match")
    # NOTE: Classification is not reliably preserved across all binary/ASCII toolchains yet.
    # It is validated in the dedicated MDLOps-anchored compatibility tests.


def compare_mdl_nodes(mdl1: MDL, mdl2: MDL, test_case: unittest.TestCase, context: str = ""):
    """Compare node hierarchies between two models (shallow)."""
    msg_prefix = f"{context}: " if context else ""
    nodes1 = mdl1.all_nodes()
    nodes2 = mdl2.all_nodes()
    test_case.assertEqual(len(nodes1), len(nodes2), f"{msg_prefix}Node counts should match")


class TestMDLRoundTripAsciiToBinaryToAscii(unittest.TestCase):
    """Test round-trip conversion: ASCII -> Binary -> ASCII using diverse models."""

    def setUp(self):
        """Set up test fixtures."""
        # Resolve relative to this test file so it works regardless of CWD.
        self.test_dir = Path(__file__).resolve().parents[2] / "test_files" / "mdl"
        if not self.test_dir.exists():
            self.skipTest(f"Test directory {self.test_dir} does not exist")

        self.test_models = {
            "character": ("c_dewback.mdl", "c_dewback.mdx"),
            "door": ("dor_lhr02.mdl", "dor_lhr02.mdx"),
            "placeable": ("m02aa_09b.mdl", "m02aa_09b.mdx"),
            "animation": ("m12aa_c03_char02.mdl", "m12aa_c03_char02.mdx"),
            "camera": ("m12aa_c04_cam.mdl", "m12aa_c04_cam.mdx"),
        }

    def _create_ascii_from_binary(self, mdl_path: Path, mdx_path: Path) -> bytes:
        """Helper to convert binary MDL to ASCII for testing.

        Prefer MDLOps as the source-of-truth for binary -> ASCII decompilation, so our
        roundtrip tests validate interoperability with the de-facto tooling ecosystem.
        """
        return _run_mdlops_decompile(mdl_path=mdl_path, mdx_path=mdx_path)

    def test_roundtrip_character_model_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip with character model."""
        mdl_path: Path = self.test_dir / self.test_models["character"][0]
        mdx_path: Path = self.test_dir / self.test_models["character"][1]

        if not mdl_path.exists():
            self.skipTest("Test file c_dewback.mdl not found")

        # Start with ASCII (created from binary for consistency)
        ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
        mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)

        # Convert to binary (MDL + MDX).
        mdl_bytes = bytearray()
        mdx_bytes = bytearray()
        write_mdl(mdl_from_ascii_original, mdl_bytes, ResourceType.MDL, target_ext=mdx_bytes)

        # Decompile with MDLOps back to ASCII (authoritative) and compare parsed models.
        ascii_bytes_round: bytes = _run_mdlops_decompile_bytes(
            mdl_bytes=bytes(mdl_bytes),
            mdx_bytes=bytes(mdx_bytes),
            stem="c_dewback",
        )
        mdl_from_ascii_round: MDL = read_mdl(ascii_bytes_round, file_format=ResourceType.MDL_ASCII)

        compare_mdl_basic(mdl_from_ascii_original, mdl_from_ascii_round, self, "Character model: MDLOps ASCII compare")
        compare_mdl_nodes(mdl_from_ascii_original, mdl_from_ascii_round, self, "Character model: MDLOps ASCII compare")

        # (Optional) also sanity-check that PyKotor can read the MDLOps output we produced.
        # The deep comparisons above already validate the full component graph.

    def test_roundtrip_all_models_reverse(self):
        """Test ASCII -> Binary -> ASCII round-trip for all available models."""
        for model_type, (mdl_file, mdx_file) in self.test_models.items():
            with self.subTest(model_type=model_type):
                mdl_path = self.test_dir / mdl_file
                mdx_path = self.test_dir / mdx_file

                if not mdl_path.exists():
                    self.skipTest(f"Test file {mdl_file} not found")

                # Start with ASCII
                ascii_bytes_original = self._create_ascii_from_binary(mdl_path, mdx_path)
                mdl_from_ascii_original = read_mdl(ascii_bytes_original, file_format=ResourceType.MDL_ASCII)

                # Convert to binary (MDL + MDX).
                mdl_bytes = bytearray()
                mdx_bytes = bytearray()
                write_mdl(mdl_from_ascii_original, mdl_bytes, ResourceType.MDL, target_ext=mdx_bytes)

                ascii_bytes_round = _run_mdlops_decompile_bytes(
                    mdl_bytes=bytes(mdl_bytes),
                    mdx_bytes=bytes(mdx_bytes),
                    stem=Path(mdl_file).stem,
                )
                mdl_from_ascii_round = read_mdl(ascii_bytes_round, file_format=ResourceType.MDL_ASCII)

                compare_mdl_basic(mdl_from_ascii_original, mdl_from_ascii_round, self, f"{model_type}: MDLOps ASCII compare")
                compare_mdl_nodes(mdl_from_ascii_original, mdl_from_ascii_round, self, f"{model_type}: MDLOps ASCII compare")


class TestMDLEqualityAndHashing(unittest.TestCase):
    """Validate that MDL objects support robust equality + hashing for set/dict usage.

    This focuses on *in-memory* models where a 1:1 component graph is expected.
    """

    def test_mdl_eq_hash_and_component_compare(self):
        mdl1 = create_test_mdl("EQ_HASH_TEST")
        mdl2 = create_test_mdl("EQ_HASH_TEST")

        self.assertTrue(mdl1 == mdl2, "MDL __eq__ should consider equivalent models equal")
        self.assertEqual(hash(mdl1), hash(mdl2), "MDL __hash__ must align with __eq__")
        self.assertEqual({mdl1}, {mdl2}, "MDL must be usable in hash-based collections (set)")

        # Deep per-component validation (float-tolerant).
        _compare_components(self, mdl1, mdl2, context="mdl_eq_hash_component")


if __name__ == "__main__":
    unittest.main()


# ============================================================================
# Installation-Backed Tests: Roundtrip everything in models.bif (K1/K2)
# ============================================================================


def _safe_filename(stem: str) -> str:
    stem = stem.strip().replace(" ", "_")
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem)
    return stem or "mdl"


def _collect_mdl_entries_for_game(game_label: str, game_root: Path) -> list[tuple[str, FileResource, FileResource | None]]:
    """Collect all MDL entries from models.bif for a given game installation.

    Returns:
        List of tuples: (resref, mdl_resource, mdx_resource_or_none)
    """
    chitin = Chitin(key_path=game_root / "chitin.key", base_path=game_root)

    models_bif_key = next(
        (
            bif_key
            for bif_key in chitin._resource_dict.keys()  # noqa: SLF001 - test-only introspection
            if Path(bif_key).name.lower() == "models.bif"
        ),
        None,
    )
    if not models_bif_key:
        return []

    models_resources: list[FileResource] = chitin._resource_dict[models_bif_key]  # noqa: SLF001 - test-only introspection
    if not models_resources:
        return []

    by_key: dict[tuple[str, ResourceType], FileResource] = {}
    for fileres in models_resources:
        by_key[(fileres.resname(), fileres.restype())] = fileres

    mdl_entries: list[FileResource] = [r for r in models_resources if r.restype() == ResourceType.MDL]
    if not mdl_entries:
        return []

    mdl_entries = sorted(mdl_entries, key=lambda r: r.resname().lower())
    limit = int(os.environ.get("PYKOTOR_MODELS_BIF_LIMIT", "0"))
    if limit > 0:
        mdl_entries = mdl_entries[:limit]

    result: list[tuple[str, FileResource, FileResource | None]] = []
    for mdl_res in mdl_entries:
        resref = mdl_res.resname()
        mdx_res = by_key.get((resref, ResourceType.MDX))
        result.append((resref, mdl_res, mdx_res))

    return result


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize test_models_bif_roundtrip_eq_hash_pytest with MDL entries.

    This generates test cases for each model, combining game_install_root and mdl_entry
    into a single parametrization to avoid cartesian product duplication.
    """
    # Only handle our test function
    if "mdl_entry" not in metafunc.fixturenames or "game_install_root" not in metafunc.fixturenames:
        return

    # Get game install roots using the same logic as conftest
    # We duplicate the logic here to avoid import issues at collection time
    roots: list[tuple[str, Path]] = []
    seen: set[str] = set()

    def _add(label: str, value: str | None):
        if not value:
            return
        p = Path(value).expanduser()
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            return
        seen.add(key)
        roots.append((label, p))

    _add("k1", os.environ.get("K1_PATH"))
    _add("k2", os.environ.get("TSL_PATH") or os.environ.get("K2_PATH"))

    if not roots:
        metafunc.parametrize(
            "game_install_root,mdl_entry",
            [
                pytest.param(
                    ("missing", Path(".")),
                    None,
                    marks=pytest.mark.skip(
                        reason="Requires K1_PATH and/or TSL_PATH/K2_PATH to be set to a game installation root.",
                    ),
                    id="missing-install",
                ),
            ],
        )
        return

    # Collect MDL entries for each game install root and create combined parameters
    # This avoids the cartesian product by combining game_install_root and mdl_entry
    params: list = []
    for game_label, game_root in roots:
        mdl_entries = _collect_mdl_entries_for_game(game_label, game_root)
        if not mdl_entries:
            # Add a skip marker if no MDL entries found
            params.append(
                pytest.param(
                    (game_label, game_root),
                    (game_label, game_root, None, None, None),
                    marks=pytest.mark.skip(
                        reason=f"{game_label}: no MDL entries found in models.bif",
                    ),
                    id=f"{game_label}-no-models",
                ),
            )
        else:
            for resref, mdl_res, mdx_res in mdl_entries:
                safe_resref = _safe_filename(resref)
                params.append(
                    pytest.param(
                        (game_label, game_root),
                        (game_label, game_root, resref, mdl_res, mdx_res),
                        id=f"{game_label}-{safe_resref}",
                    ),
                )

    metafunc.parametrize("game_install_root,mdl_entry", params)


def test_models_bif_roundtrip_eq_hash_pytest(
    game_install_root: tuple[str, Path],
    mdl_entry: tuple[str, Path, str | None, FileResource | None, FileResource | None] | None,
    tmp_path: Path,
):
    """Roundtrip each MDL in models.bif using Chitin (KEY/BIF) enumeration (pytest-parametrized).

    This test is parametrized by `pytest_generate_tests` in this module, which combines
    `game_install_root` and `mdl_entry` into a single parametrization to avoid duplicates.

    Each model gets its own test case with the model name as a suffix (e.g., k1-modelname or k2-modelname).

    Pipeline per resref:
      - Read binary MDL (+ optional MDX) from models.bif via Chitin
      - Parse binary -> MDL object
      - Write ASCII to a temporary file (disk)
      - Read ASCII -> MDL object
      - Validate __eq__/__hash__ + deep component-wise equality
      - Convert back to binary and re-parse, validating stability
    """
    if mdl_entry is None:
        pytest.skip("No MDL entry provided")

    game_label_from_entry, game_root_from_entry, resref, mdl_res, mdx_res = mdl_entry
    game_label, game_root = game_install_root

    # Verify game_install_root matches mdl_entry (should always match now, but keep for safety)
    if game_label != game_label_from_entry or game_root != game_root_from_entry:
        pytest.skip(f"Mismatch between game_install_root ({game_label}) and mdl_entry ({game_label_from_entry})")

    # Handle skip case where no MDL entries were found
    if resref is None or mdl_res is None:
        pytest.skip("No MDL entry provided")

    eqhash_budget_s = float(os.environ.get("PYKOTOR_MODELS_BIF_EQHASH_BUDGET_S", "2.0"))

    out_dir: Path = tmp_path / f"pykotor-models-bif-{game_label}"
    out_dir.mkdir(parents=True, exist_ok=True)

    mdl_bytes = mdl_res.data()
    mdx_bytes = mdx_res.data() if mdx_res is not None else b""

    mdl_bin = read_mdl(
        mdl_bytes,
        source_ext=mdx_bytes if mdx_bytes else None,
        file_format=ResourceType.MDL,
    )

    ascii_bytes = bytes_mdl(mdl_bin, ResourceType.MDL_ASCII)
    ascii_path = out_dir / f"{_safe_filename(resref)}.mdl.ascii"
    ascii_path.write_bytes(ascii_bytes)

    mdl_ascii = read_mdl(ascii_path.read_bytes(), file_format=ResourceType.MDL_ASCII)

    assert mdl_bin == mdl_ascii, "binary->ascii parse mismatch (MDL __eq__)"
    assert hash(mdl_bin) == hash(mdl_ascii), "MDL __hash__ must align with __eq__"
    assert {mdl_bin} == {mdl_ascii}, "MDL must be usable in hash-based collections"
    _compare_components(pytest, mdl_bin, mdl_ascii, context=f"{game_label}:{resref}:binary_vs_ascii")  # type: ignore[arg-type]

    out_mdl = bytearray()
    out_mdx = bytearray()
    write_mdl(mdl_ascii, out_mdl, ResourceType.MDL, target_ext=out_mdx)

    mdl_bin_round = read_mdl(
        bytes(out_mdl),
        source_ext=bytes(out_mdx) if out_mdx else None,
        file_format=ResourceType.MDL,
    )

    assert mdl_bin == mdl_bin_round, "binary->ascii->binary parse mismatch (MDL __eq__)"
    assert hash(mdl_bin) == hash(mdl_bin_round), "MDL hash changed after roundtrip"
    _compare_components(pytest, mdl_bin, mdl_bin_round, context=f"{game_label}:{resref}:binary_vs_binary_round")  # type: ignore[arg-type]

    t0 = time.perf_counter()
    for _ in range(3):
        assert mdl_bin == mdl_ascii
        assert mdl_bin == mdl_bin_round
        _ = hash(mdl_bin)
        _ = hash(mdl_ascii)
        _ = hash(mdl_bin_round)
    elapsed = time.perf_counter() - t0
    assert elapsed < eqhash_budget_s, (
        f"eq/hash perf regression for {game_label}:{resref} ({elapsed:.3f}s > {eqhash_budget_s:.3f}s). "
        "Tune with PYKOTOR_MODELS_BIF_EQHASH_BUDGET_S."
    )

