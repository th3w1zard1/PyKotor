"""Binary reader for MDL mesh nodes.

This reader handles the common mesh data found in MDL files, including:
- Geometry (vertices, faces, normals, UVs)
- Materials (textures, colors, transparency)
- Render properties (shadows, beaming, etc)
- Animation properties (UV animation)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional

from pykotor.common.misc import Color
from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.mesh import MDLMeshNode
from pykotor.resource.formats.mdl.io.binary.nodes.base_node_reader import MDLBinaryNodeReader
from utility.common.geometry import Vector2, Vector3

if TYPE_CHECKING:
    from pykotor.common.stream import BinaryReader
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode

# MDX data flags
MDX_FLAG_VERTICES = 0x0001
MDX_FLAG_TEX0_VERTICES = 0x0002
MDX_FLAG_TEX1_VERTICES = 0x0004
MDX_FLAG_TEX2_VERTICES = 0x0008
MDX_FLAG_TEX3_VERTICES = 0x0010
MDX_FLAG_VERTEX_NORMALS = 0x0020
MDX_FLAG_VERTEX_COLORS = 0x0040
MDX_FLAG_TANGENT_SPACE = 0x0080
MDX_FLAG_BONE_WEIGHTS = 0x0800
MDX_FLAG_BONE_INDICES = 0x1000


class BinaryMeshReader(MDLBinaryNodeReader):
    """Reader for binary MDL mesh nodes."""

    def __init__(
        self,
        mdl_reader: BinaryReader,
        mdx_reader: BinaryReader,
        names: List[str],
        node_by_number: Dict[int, MDLNode],
    ):
        """Initialize the mesh reader.

        Args:
            mdl_reader: Reader for MDL data
            mdx_reader: Reader for MDX data
            names: List of names from the MDL file
            node_by_number: Dictionary mapping node numbers to nodes
        """
        super().__init__(mdl_reader, mdx_reader, names, node_by_number)

    def _read_face(self) -> List[int]:
        """Read triangle face indices.

        Returns:
            List[int]: The three vertex indices
        """
        return [self._mdl_reader.read_uint16() for _ in range(3)]

    def _read_mdx_vertex(self, mdx_offset: int, vertex_index: int, vertex_size: int, vertex_offset: int) -> Vector3:
        """Read a vertex position from MDX data.

        Args:
            mdx_offset: Base offset into MDX data
            vertex_index: Index of vertex to read
            vertex_size: Size of each vertex in bytes
            vertex_offset: Offset to vertex position within vertex

        Returns:
            Vector3: The vertex position
        """
        self._mdx_reader.seek(mdx_offset + vertex_index * vertex_size + vertex_offset)
        x = self._mdx_reader.read_single()
        y = self._mdx_reader.read_single()
        z = self._mdx_reader.read_single()
        return Vector3(x, y, z)

    def _read_mdx_normal(self, mdx_offset: int, vertex_index: int, vertex_size: int, normal_offset: int) -> Vector3:
        """Read a vertex normal from MDX data.

        Args:
            mdx_offset: Base offset into MDX data
            vertex_index: Index of vertex to read
            vertex_size: Size of each vertex in bytes
            normal_offset: Offset to normal within vertex

        Returns:
            Vector3: The vertex normal
        """
        self._mdx_reader.seek(mdx_offset + vertex_index * vertex_size + normal_offset)
        x = self._mdx_reader.read_single()
        y = self._mdx_reader.read_single()
        z = self._mdx_reader.read_single()
        return Vector3(x, y, z)

    def _read_mdx_uv(self, mdx_offset: int, vertex_index: int, vertex_size: int, uv_offset: int) -> Vector2:
        """Read UV coordinates from MDX data.

        Args:
            mdx_offset: Base offset into MDX data
            vertex_index: Index of vertex to read
            vertex_size: Size of each vertex in bytes
            uv_offset: Offset to UV coordinates within vertex

        Returns:
            Vector2: The UV coordinates
        """
        self._mdx_reader.seek(mdx_offset + vertex_index * vertex_size + uv_offset)
        u = self._mdx_reader.read_single()
        v = self._mdx_reader.read_single()
        return Vector2(u, v)

    def _read_mdx_color(self, mdx_offset: int, vertex_index: int, vertex_size: int, color_offset: int) -> Color:
        """Read vertex color from MDX data.

        Args:
            mdx_offset: Base offset into MDX data
            vertex_index: Index of vertex to read
            vertex_size: Size of each vertex in bytes
            color_offset: Offset to color within vertex

        Returns:
            Color: The vertex color
        """
        self._mdx_reader.seek(mdx_offset + vertex_index * vertex_size + color_offset)
        r = self._mdx_reader.read_single()
        g = self._mdx_reader.read_single()
        b = self._mdx_reader.read_single()
        a = self._mdx_reader.read_single()
        return Color(r, g, b, a)

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read a mesh node from the file.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded mesh node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create mesh node
            name = self._names[name_index]
            node = MDLMeshNode(name)
            node.node_number = node_number

            if parent:
                node.parent = parent

            # Read geometry arrays
            vertices_arr = self._read_array_definition()
            normals_arr = self._read_array_definition()
            uv1_arr = self._read_array_definition()
            uv2_arr = self._read_array_definition()
            colors_arr = self._read_array_definition()

            # Read face arrays
            faces_arr = self._read_array_definition()
            face_materials_arr = self._read_array_definition()
            face_normals_arr = self._read_array_definition()
            face_distances_arr = self._read_array_definition()

            # Read material properties
            node.diffuse = [self._mdl_reader.read_single() for _ in range(3)]
            node.ambient = [self._mdl_reader.read_single() for _ in range(3)]
            node.self_illumination = [self._mdl_reader.read_single() for _ in range(3)]
            node.transparency = self._mdl_reader.read_single()

            # Read texture names
            texture_name_index = self._mdl_reader.read_uint32()
            texture2_name_index = self._mdl_reader.read_uint32()

            if texture_name_index < len(self._names):
                node.texture = self._names[texture_name_index]
            if texture2_name_index < len(self._names):
                node.texture2 = self._names[texture2_name_index]

            # Read render flags
            render_flags = self._mdl_reader.read_uint32()
            node.render = bool(render_flags & 0x0001)
            node.shadow = bool(render_flags & 0x0002)
            node.beaming = bool(render_flags & 0x0004)
            node.render_environment_map = bool(render_flags & 0x0008)
            node.background_geometry = bool(render_flags & 0x0010)

            # Read animation properties
            anim_flags = self._mdl_reader.read_uint32()
            node.animate_uv = bool(anim_flags & 0x0001)
            node.rotate_texture = bool(anim_flags & 0x0002)

            # Read UV direction as Vector2
            x = self._mdl_reader.read_single()
            y = self._mdl_reader.read_single()
            node.uv_direction = Vector2(x, y)

            node.uv_jitter = self._mdl_reader.read_single()
            node.uv_jitter_speed = self._mdl_reader.read_single()

            # Read MDX data info
            mdx_vertex_size = self._mdl_reader.read_uint32()
            mdx_data_flags = self._mdl_reader.read_uint32()
            off_mdx_vertices = self._mdl_reader.read_int32()
            off_mdx_normals = self._mdl_reader.read_int32()
            off_mdx_colors = self._mdl_reader.read_int32()
            off_mdx_uv1 = self._mdl_reader.read_int32()
            off_mdx_uv2 = self._mdl_reader.read_int32()

            # Skip unused UV sets and tangent space
            self._mdl_reader.skip(5 * 4)

            # Read vertex counts and flags
            num_vertices = self._mdl_reader.read_uint16()
            num_textures = self._mdl_reader.read_uint16()
            node.lightmapped = bool(self._mdl_reader.read_uint8())
            node.rotate_texture = bool(self._mdl_reader.read_uint8())
            node.background_geometry = bool(self._mdl_reader.read_uint8())
            node.shadow = bool(self._mdl_reader.read_uint8())
            node.beaming = bool(self._mdl_reader.read_uint8())
            node.render = bool(self._mdl_reader.read_uint8())

            # Skip padding and unused fields
            self._mdl_reader.skip(6)

            # Read MDX data offset
            mdx_offset = self._mdl_reader.read_uint32()

            # Read vertex data from MDX
            if mdx_vertex_size > 0:
                for i in range(num_vertices):
                    # Read vertex position
                    if mdx_data_flags & MDX_FLAG_VERTICES:
                        node.vertices.append(self._read_mdx_vertex(mdx_offset, i, mdx_vertex_size, off_mdx_vertices))

                    # Read vertex normal
                    if mdx_data_flags & MDX_FLAG_VERTEX_NORMALS:
                        node.normals.append(self._read_mdx_normal(mdx_offset, i, mdx_vertex_size, off_mdx_normals))

                    # Read vertex color
                    if mdx_data_flags & MDX_FLAG_VERTEX_COLORS:
                        node.colors.append(self._read_mdx_color(mdx_offset, i, mdx_vertex_size, off_mdx_colors))

                    # Read UV1 coordinates
                    if mdx_data_flags & MDX_FLAG_TEX0_VERTICES:
                        node.uv1.append(self._read_mdx_uv(mdx_offset, i, mdx_vertex_size, off_mdx_uv1))

                    # Read UV2 coordinates
                    if mdx_data_flags & MDX_FLAG_TEX1_VERTICES:
                        node.uv2.append(self._read_mdx_uv(mdx_offset, i, mdx_vertex_size, off_mdx_uv2))

            # Read face data
            if faces_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + faces_arr.offset)
                for _ in range(faces_arr.count):
                    node.faces.append(self._read_face())

            # Read face material data
            if face_materials_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + face_materials_arr.offset)
                for _ in range(face_materials_arr.count):
                    material = self._mdl_reader.read_uint16()
                    node.face_materials.append(material)

            # Read face normal data
            if face_normals_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + face_normals_arr.offset)
                for i in range(face_normals_arr.count):
                    node.face_normals.append(self._read_mdx_vertex(mdx_offset, i, mdx_vertex_size, off_mdx_vertices))

            # Read face distance data
            if face_distances_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + face_distances_arr.offset)
                for _ in range(face_distances_arr.count):
                    distance = self._mdl_reader.read_single()
                    node.face_distances.append(distance)

            # Read child nodes
            self._read_children(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading mesh node: {str(e)}")
