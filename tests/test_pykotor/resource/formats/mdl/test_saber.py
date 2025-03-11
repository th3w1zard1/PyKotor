"""Tests for MDL saber node functionality."""

import io
import unittest
from typing import BinaryIO

from pykotor.common.misc import Color, ResRef
from pykotor.common.stream import BinaryReader, BinaryWriterBytearray
from pykotor.resource.formats.mdl.data.enums import MDLNodeFlags, MDLSaberFlags, MDLSaberType
from pykotor.resource.formats.mdl.data.nodes.saber import MDLSaber, MDLSaberNode
from pykotor.resource.formats.mdl.io.ascii.nodes.saber_reader import MDLASCIISaberReader
from pykotor.resource.formats.mdl.io.binary.nodes.saber_reader import MDLBinarySaberReader
from utility.common.geometry import Vector3


class TestMDLSaber(unittest.TestCase):
    """Test MDL saber node functionality."""

    def test_binary_saber_node(self) -> None:
        """Test reading a binary saber node."""
        # Create test data
        data = bytearray()
        with BinaryWriterBytearray(data) as writer:
            # Node header
            writer.write_bytes(b"\x00" * 8)  # Function pointers
            writer.write_uint16(0x0400)  # Node flags (SABER)
            writer.write_uint16(1)  # Node number
            writer.write_uint16(0)  # Name index
            writer.write_bytes(b"\x00" * 2)  # Padding
            writer.write_uint32(0)  # Root offset
            writer.write_uint32(0)  # Parent offset

            # Saber properties
            writer.write_uint32(int(MDLSaberType.STANDARD))  # Type
            writer.write_uint32(int(0xFF0000))  # Color
            writer.write_single(1.5)  # Length
            writer.write_single(0.5)  # Width
            writer.write_uint32(int(0x00FF00))  # Flare color
            writer.write_single(0.75)  # Flare radius
            writer.write_uint32(int(MDLSaberFlags.FLARE))  # Flags

            # Textures
            writer.write_string("blade.tga")  # Blade texture
            writer.write_string("hit.tga")  # Hit texture
            writer.write_string("flare.tga")  # Flare texture

            # Vertex data
            writer.write_uint32(4)  # Vertex count
            writer.write_uint32(100)  # Vertex offset

            # Add vertex data at offset 100
            while len(data) < 100:
                writer.write_bytes(b"\x00")

            # Vertices
            for i in range(4):
                writer.write_single(i)  # x
                writer.write_single(i)  # y
                writer.write_single(i)  # z

        # Create reader and read node
        reader = MDLBinarySaberReader(BinaryReader.from_bytes(data), BinaryReader.from_bytes(b""), ["test"], {})
        node = reader.read_node()

        # Verify node properties
        self.assertIsInstance(node, MDLSaberNode)
        self.assertEqual(node.node_flags, MDLNodeFlags(0x0400))
        self.assertEqual(node.name, "test")

        # Verify saber properties
        self.assertEqual(node.saber.saber_type, MDLSaberType.STANDARD)
        self.assertEqual(node.saber.saber_color, Color.from_rgb_integer(0xFF0000))
        self.assertEqual(node.saber.saber_length, 1.5)
        self.assertEqual(node.saber.saber_width, 0.5)
        self.assertEqual(node.saber.saber_flare_color, Color.from_rgb_integer(0x00FF00))
        self.assertEqual(node.saber.saber_flare_radius, 0.75)
        self.assertEqual(node.saber.saber_flags, MDLSaberFlags.FLARE)

        # Verify textures
        self.assertEqual(node.saber.blade_texture, ResRef("blade.tga"))
        self.assertEqual(node.saber.hit_texture, ResRef("hit.tga"))
        self.assertEqual(node.saber.flare_texture, ResRef("flare.tga"))

        # Verify vertices
        self.assertEqual(len(node.vertices), 4)
        for i, vertex in enumerate(node.vertices):
            self.assertEqual(vertex, Vector3(i, i, i))

    def test_ascii_saber_node(self) -> None:
        """Test reading an ASCII saber node."""
        # Create test data
        data = """node trimesh 2081__test
beginproperties
position 1.0 2.0 3.0
orientation 0.0 0.0 0.0 1.0
bitmap "blade.tga"
renderhint 1
beaming 1
rotatewithtarget 0
endproperties
beginsaber
type 0
color 16711680
length 1.5
width 0.5
flarecolor 65280
flareradius 0.75
flags 1
bladetexture "blade.tga"
hittexture "hit.tga"
flaretexture "flare.tga"
endsaber
beginmodelgeom
verts 4
{
0.0 0.0 0.0
1.0 1.0 1.0
2.0 2.0 2.0
3.0 3.0 3.0
}
faces 2
{
0 1 2 1 0 1 2 0
1 2 3 1 1 2 3 0
}
tverts 4
{
0.0 0.0
0.0 1.0
1.0 0.0
1.0 1.0
}
saber_verts 4
{
0.0 0.0 0.0
1.0 1.0 1.0
2.0 2.0 2.0
3.0 3.0 3.0
}
saber_norms 4
{
0.0 0.0 1.0
0.0 0.0 1.0
0.0 0.0 1.0
0.0 0.0 1.0
}
endmodelgeom
endnode"""

        # Create reader and read node
        reader = MDLASCIISaberReader(BinaryReader.from_bytes(data.encode()), ["test"], {})
        node = reader.read_node()

        # Verify node properties
        self.assertIsInstance(node, MDLSaberNode)
        self.assertEqual(node.name, "test")
        self.assertEqual(node.position, [1.0, 2.0, 3.0])
        self.assertEqual(node.orientation, [0.0, 0.0, 0.0, 1.0])
        self.assertEqual(node.bitmap, "blade.tga")
        self.assertEqual(node.render_hint, 1)
        self.assertTrue(node.beaming)
        self.assertFalse(node.rotate_with_target)

        # Verify saber properties
        self.assertEqual(node.saber.saber_type, MDLSaberType.STANDARD)
        self.assertEqual(node.saber.saber_color, Color.from_rgb_integer(0xFF0000))
        self.assertEqual(node.saber.saber_length, 1.5)
        self.assertEqual(node.saber.saber_width, 0.5)
        self.assertEqual(node.saber.saber_flare_color, Color.from_rgb_integer(0x00FF00))
        self.assertEqual(node.saber.saber_flare_radius, 0.75)
        self.assertEqual(node.saber.saber_flags, MDLSaberFlags.FLARE)

        # Verify textures
        self.assertEqual(node.saber.blade_texture, ResRef("blade.tga"))
        self.assertEqual(node.saber.hit_texture, ResRef("hit.tga"))
        self.assertEqual(node.saber.flare_texture, ResRef("flare.tga"))

        # Verify geometry
        self.assertEqual(len(node.vertices), 4)
        self.assertEqual(len(node.faces), 2)
        self.assertEqual(len(node.uvs), 4)
        self.assertEqual(len(node.saber_vertices), 4)
        self.assertEqual(len(node.normals), 4)

        # Verify vertices
        for i, vertex in enumerate(node.vertices):
            self.assertEqual(vertex, Vector3(i, i, i))

        # Verify faces
        self.assertEqual(node.faces[0], [0, 1, 2])
        self.assertEqual(node.faces[1], [1, 2, 3])

        # Verify UVs
        self.assertEqual(node.uvs[0], (0.0, 0.0))
        self.assertEqual(node.uvs[1], (0.0, 1.0))
        self.assertEqual(node.uvs[2], (1.0, 0.0))
        self.assertEqual(node.uvs[3], (1.0, 1.0))

        # Verify saber vertices
        for i, vertex in enumerate(node.saber_vertices):
            self.assertEqual(vertex, Vector3(i, i, i))

        # Verify normals
        for normal in node.normals:
            self.assertEqual(normal, Vector3(0.0, 0.0, 1.0))

    def test_invalid_binary_saber(self) -> None:
        """Test reading an invalid binary saber node."""
        # Create invalid test data
        data = bytearray()
        # Invalid node header
        data.extend(b"\x00" * 8)  # Function pointers
        data.extend(int(0x0400).to_bytes(2, "little"))  # Node flags (SABER)
        data.extend(int(1).to_bytes(2, "little"))  # Node number
        data.extend(int(99).to_bytes(2, "little"))  # Invalid name index
        data.extend(b"\x00" * 2)  # Padding
        data.extend(int(0).to_bytes(4, "little"))  # Root offset
        data.extend(int(0).to_bytes(4, "little"))  # Parent offset

        # Create reader
        reader = MDLBinarySaberReader(BinaryReader.from_bytes(data), BinaryReader.from_bytes(b""), ["test"], {})

        # Verify error is raised
        with self.assertRaises(Exception):
            reader.read_node()

    def test_invalid_ascii_saber(self) -> None:
        """Test reading an invalid ASCII saber node."""
        # Create invalid test data
        data = """node trimesh 2081__test
beginproperties
invalid_property
endproperties
endnode"""

        # Create reader
        reader = MDLASCIISaberReader(BinaryReader.from_bytes(data.encode()), ["test"], {})

        # Verify error is raised
        with self.assertRaises(Exception):
            reader.read_node()


if __name__ == "__main__":
    unittest.main()
