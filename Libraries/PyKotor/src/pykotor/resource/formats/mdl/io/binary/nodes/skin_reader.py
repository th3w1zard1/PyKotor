"""Binary reader for MDL skin mesh nodes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.skin import MDLSkinNode
from pykotor.resource.formats.mdl.io.binary.nodes.mesh_reader import MDX_FLAG_COLOR, MDX_FLAG_NORMAL, MDX_FLAG_UV1, MDX_FLAG_UV2, MDX_FLAG_VERTEX
from pykotor.resource.formats.mdl.io.binary.nodes.trimesh_reader import MDLBinaryTrimeshReader
from utility.common.geometry import Vector2, Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode

# Additional MDX flags for skin meshes
MDX_FLAG_BONE_WEIGHTS = 0x0800
MDX_FLAG_BONE_INDICES = 0x1000


class MDLBinarySkinReader(MDLBinaryTrimeshReader):
    """Reader for binary MDL skin mesh nodes."""

    def read_node(self, offset: int, parent: Optional[MDLNode] = None) -> MDLNode:
        """Read a skin mesh node from the file.

        Args:
            offset: Offset to node data
            parent: Parent node if any

        Returns:
            MDLNode: The loaded skin mesh node

        Raises:
            MDLReadError: If there is an error reading the node data
        """
        try:
            self._mdl_reader.seek(self.MDL_OFFSET + offset)

            # Read common node header
            type_flags, node_number, name_index, root_offset, parent_offset = self._read_node_header()

            # Create skin mesh node
            name = self._names[name_index]
            node = MDLSkinNode(name)
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

            # Read UV direction
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
            off_mdx_bone_weights = self._mdl_reader.read_int32()
            off_mdx_bone_indices = self._mdl_reader.read_int32()

            # Skip unused UV sets and tangent space
            self._mdl_reader.skip(3 * 4)

            # Read vertex counts and flags
            num_vertices = self._mdl_reader.read_uint16()
            num_textures = self._mdl_reader.read_uint16()  # FIXME: why is this unused?
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

            # Read bone data
            num_bones = self._mdl_reader.read_uint32()
            bone_map_arr = self._read_array_definition()
            qbone_arr = self._read_array_definition()
            tbone_arr = self._read_array_definition()

            # Read bone indices
            node.bone_indices = [self._mdl_reader.read_uint16() for _ in range(16)]
            self._mdl_reader.skip(4)  # padding

            # Read bone map
            if bone_map_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + bone_map_arr.offset)
                node.bone_map = [self._mdl_reader.read_single() for _ in range(bone_map_arr.count)]

            # Read quaternion bones
            if qbone_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + qbone_arr.offset)
                for _ in range(qbone_arr.count):
                    quat = [self._mdl_reader.read_single() for _ in range(4)]
                    node.qbones.append(quat)

            # Read translation bones
            if tbone_arr.count > 0:
                self._mdl_reader.seek(self.MDL_OFFSET + tbone_arr.offset)
                for _ in range(tbone_arr.count):
                    trans = [self._mdl_reader.read_single() for _ in range(3)]
                    node.tbones.append(trans)

            # Read vertex data from MDX
            if mdx_vertex_size > 0:
                for i in range(num_vertices):
                    # Read vertex position
                    if mdx_data_flags & MDX_FLAG_VERTEX:
                        node.vertices.append(self._read_mdx_vertex(mdx_offset, i, mdx_vertex_size, off_mdx_vertices))

                    # Read vertex normal
                    if mdx_data_flags & MDX_FLAG_NORMAL:
                        node.normals.append(self._read_mdx_normal(mdx_offset, i, mdx_vertex_size, off_mdx_normals))

                    # Read vertex color
                    if mdx_data_flags & MDX_FLAG_COLOR:
                        node.colors.append(self._read_mdx_color(mdx_offset, i, mdx_vertex_size, off_mdx_colors))

                    # Read UV1 coordinates
                    if mdx_data_flags & MDX_FLAG_UV1:
                        node.uv1.append(self._read_mdx_uv(mdx_offset, i, mdx_vertex_size, off_mdx_uv1))

                    # Read UV2 coordinates
                    if mdx_data_flags & MDX_FLAG_UV2:
                        node.uv2.append(self._read_mdx_uv(mdx_offset, i, mdx_vertex_size, off_mdx_uv2))

                    # Read bone weights
                    if mdx_data_flags & MDX_FLAG_BONE_WEIGHTS:
                        self._mdx_reader.seek(mdx_offset + i * mdx_vertex_size + off_mdx_bone_weights)
                        weights = [self._mdx_reader.read_single() for _ in range(4)]
                        node.bone_weights.append(weights)

                    # Read bone indices
                    if mdx_data_flags & MDX_FLAG_BONE_INDICES:
                        self._mdx_reader.seek(mdx_offset + i * mdx_vertex_size + off_mdx_bone_indices)
                        indices = [self._mdx_reader.read_single() for _ in range(4)]
                        node.bone_vertex_indices.append([int(i) for i in indices])

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
                for _ in range(face_normals_arr.count):
                    x = self._mdl_reader.read_single()
                    y = self._mdl_reader.read_single()
                    z = self._mdl_reader.read_single()
                    node.face_normals.append(Vector3(x, y, z))

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
            raise MDLReadError(f"Error reading skin mesh node: {str(e)}") from e
