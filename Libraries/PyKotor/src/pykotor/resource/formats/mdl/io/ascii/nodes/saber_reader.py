"""ASCII MDL saber node reader."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import Color, ResRef
from pykotor.resource.formats.mdl.data.enums import MDLSaberFlags, MDLSaberType
from pykotor.resource.formats.mdl.data.exceptions import MDLReadError
from pykotor.resource.formats.mdl.data.nodes.anim import MDLPositionKeyframe, MDLRotationKeyframe
from pykotor.resource.formats.mdl.data.nodes.saber import MDLSaber, MDLSaberNode
from pykotor.resource.formats.mdl.io.ascii.nodes.base_node_reader import MDLASCIINodeReader

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


class MDLASCIISaberReader(MDLASCIINodeReader):
    """Reader for ASCII MDL saber nodes.

    In ASCII format, saber nodes are actually trimesh nodes marked with a "2081__" prefix.
    They get converted to saber nodes during loading.
    """

    def read_node(self, parent: MDLNode | None = None) -> MDLNode:
        """Read a saber node from the file.

        Args:
            parent: Parent node if any

        Returns:
            MDLNode: The loaded node

        Raises:
            MDLReadError: If there is an error reading the node
        """
        try:
            # Read node header
            line = self.read_line()
            if not line.startswith("node"):
                raise MDLReadError(f"Expected node, got {line}")

            parts = line.split()
            if len(parts) < 3:
                raise MDLReadError("Invalid node line, expected 'node type name'")

            # Remove 2081__ prefix if present
            name = parts[2]
            if name.startswith("2081__"):
                name = name[6:]

            node = MDLSaberNode(name)
            node.parent = parent

            # Initialize saber properties
            node.saber = MDLSaber()

            # Read node sections
            while True:
                line = self.read_line()
                if line.startswith("endnode"):
                    break

                if line.startswith("beginproperties"):
                    self.read_properties(node)
                elif line.startswith("beginmodelgeom"):
                    self.read_geometry(node)
                elif line.startswith("beginanimation"):
                    self.read_animation(node)
                elif line.startswith("beginchildren"):
                    self.read_children(node)
                elif line.startswith("beginsaber"):
                    self.read_saber_properties(node)

            return node

        except Exception as e:
            raise MDLReadError(f"Error reading saber node: {str(e)}")

    def read_saber_properties(self, node: MDLNode) -> None:
        """Read saber-specific properties.

        Args:
            node: Node to read properties for

        Raises:
            MDLReadError: If there is an error reading properties
        """
        try:
            if not isinstance(node, MDLSaberNode):
                return

            while True:
                line = self.read_line()
                if line.startswith("endsaber"):
                    break

                parts = line.split()
                if not parts:
                    continue

                if line.startswith("type"):
                    node.saber.saber_type = MDLSaberType(int(parts[1]))
                elif line.startswith("color"):
                    node.saber.saber_color = Color.from_rgb_integer(int(parts[1]))
                elif line.startswith("length"):
                    node.saber.saber_length = float(parts[1])
                elif line.startswith("width"):
                    node.saber.saber_width = float(parts[1])
                elif line.startswith("flarecolor"):
                    node.saber.saber_flare_color = Color.from_rgb_integer(int(parts[1]))
                elif line.startswith("flareradius"):
                    node.saber.saber_flare_radius = float(parts[1])
                elif line.startswith("flags"):
                    node.saber.saber_flags = MDLSaberFlags(int(parts[1]))
                elif line.startswith("blurlength"):
                    node.saber.blur_length = float(parts[1])
                elif line.startswith("blurwidth"):
                    node.saber.blur_width = float(parts[1])
                elif line.startswith("glowsize"):
                    node.saber.glow_size = float(parts[1])
                elif line.startswith("glowintensity"):
                    node.saber.glow_intensity = float(parts[1])
                elif line.startswith("bladetexture"):
                    node.saber.blade_texture = ResRef(parts[1].strip('"'))
                elif line.startswith("hittexture"):
                    node.saber.hit_texture = ResRef(parts[1].strip('"'))
                elif line.startswith("flaretexture"):
                    node.saber.flare_texture = ResRef(parts[1].strip('"'))

        except Exception as e:
            raise MDLReadError(f"Error reading saber properties: {str(e)}")

    def read_properties(self, node: MDLNode) -> None:
        """Read node properties.

        Args:
            node: Node to read properties for

        Raises:
            MDLReadError: If there is an error reading properties
        """
        try:
            if not isinstance(node, MDLSaberNode):
                return

            while True:
                line = self.read_line()
                if line.startswith("endproperties"):
                    break

                if line.startswith("position"):
                    vec = self._parse_vector3(line)
                    node.position = [vec.x, vec.y, vec.z]
                elif line.startswith("orientation"):
                    vec = self._parse_vector4(line)
                    node.orientation = [vec.x, vec.y, vec.z, vec.w]
                elif line.startswith("bitmap"):
                    node.bitmap = line.split('"')[1]  # Extract quoted string
                elif line.startswith("renderhint"):
                    node.render_hint = int(line.split()[1])
                elif line.startswith("beaming"):
                    node.beaming = bool(int(line.split()[1]))
                elif line.startswith("rotatewithtarget"):
                    node.rotate_with_target = bool(int(line.split()[1]))

        except Exception as e:
            raise MDLReadError(f"Error reading saber properties: {str(e)}")

    def read_geometry(self, node: MDLNode) -> None:
        """Read node geometry data.

        Args:
            node: Node to read geometry for

        Raises:
            MDLReadError: If there is an error reading geometry
        """
        try:
            if not isinstance(node, MDLSaberNode):
                return

            while True:
                line = self.read_line()
                if line.startswith("endmodelgeom"):
                    break

                if line.startswith("verts"):
                    # Read base mesh vertices
                    count = int(line.split()[1])
                    line = self.read_line()
                    if not line.startswith("{"):
                        raise MDLReadError("Expected { after verts count")

                    for _ in range(count):
                        line = self.read_line()
                        node.vertices.append(self._parse_vector3(line))

                    line = self.read_line()
                    if not line.startswith("}"):
                        raise MDLReadError("Expected } after verts")

                elif line.startswith("faces"):
                    # Read face indices
                    count = int(line.split()[1])
                    line = self.read_line()
                    if not line.startswith("{"):
                        raise MDLReadError("Expected { after faces count")

                    for _ in range(count):
                        line = self.read_line()
                        parts = line.split()
                        face = [int(parts[0]), int(parts[1]), int(parts[2])]
                        node.faces.append(face)

                    line = self.read_line()
                    if not line.startswith("}"):
                        raise MDLReadError("Expected } after faces")

                elif line.startswith("tverts"):
                    # Read texture coordinates
                    count = int(line.split()[1])
                    line = self.read_line()
                    if not line.startswith("{"):
                        raise MDLReadError("Expected { after tverts count")

                    for _ in range(count):
                        line = self.read_line()
                        parts = line.split()
                        uv = (float(parts[0]), float(parts[1]))
                        node.uvs.append(uv)

                    line = self.read_line()
                    if not line.startswith("}"):
                        raise MDLReadError("Expected } after tverts")

                elif line.startswith("saber_verts"):
                    # Read saber blade vertices
                    count = int(line.split()[1])
                    line = self.read_line()
                    if not line.startswith("{"):
                        raise MDLReadError("Expected { after saber_verts count")

                    for _ in range(count):
                        line = self.read_line()
                        node.saber_vertices.append(self._parse_vector3(line))

                    line = self.read_line()
                    if not line.startswith("}"):
                        raise MDLReadError("Expected } after saber_verts")

                elif line.startswith("saber_norms"):
                    # Read saber blade normals
                    count = int(line.split()[1])
                    line = self.read_line()
                    if not line.startswith("{"):
                        raise MDLReadError("Expected { after saber_norms count")

                    for _ in range(count):
                        line = self.read_line()
                        node.normals.append(self._parse_vector3(line))

                    line = self.read_line()
                    if not line.startswith("}"):
                        raise MDLReadError("Expected } after saber_norms")

        except Exception as e:
            raise MDLReadError(f"Error reading saber geometry: {str(e)}")

    def read_animation(self, node: MDLNode) -> None:
        """Read node animation data.

        Args:
            node: Node to read animation for

        Raises:
            MDLReadError: If there is an error reading animation
        """
        try:
            if not isinstance(node, MDLSaberNode):
                return

            while True:
                line = self.read_line()
                if line.startswith("endanimation"):
                    break

                if line.startswith("positionkey"):
                    parts = line.split()
                    time = float(parts[1])
                    pos = self._parse_vector3(" ".join(parts[2:]))
                    keyframe = MDLPositionKeyframe(time=time, position=pos)
                    node.position_keyframes.append(keyframe)
                elif line.startswith("orientationkey"):
                    parts = line.split()
                    time = float(parts[1])
                    rot = self._parse_vector4(" ".join(parts[2:]))
                    keyframe = MDLRotationKeyframe(time=time, rotation=rot)
                    node.rotation_keyframes.append(keyframe)

        except Exception as e:
            raise MDLReadError(f"Error reading saber animation: {str(e)}")

    def read_children(self, node: MDLNode) -> None:
        """Read child nodes.

        Args:
            node: Parent node to add children to

        Raises:
            MDLReadError: If there is an error reading child nodes
        """
        try:
            while True:
                # Peek at next line
                pos = self._reader.tell()
                line = self.read_line()
                if not line.startswith("node "):
                    self._reader.seek(pos)
                    break

                # Read child node
                child = self.read_node(node)
                node.add_child(child)

        except Exception as e:
            raise MDLReadError(f"Error reading child nodes: {str(e)}")

    def read_header(self, node: MDLNode) -> None:
        """Read the header of a node.

        Args:
            node: Node to read header for

        Raises:
            MDLReadError: If there is an error reading the header
        """
        pass  # ASCII does not have a binary header to read

    def read_subheader(self, node: MDLNode) -> None:
        """Read the subheader of a node.

        Args:
            node: Node to read subheader for

        Raises:
            MDLReadError: If there is an error reading the subheader
        """
        pass  # ASCII does not have a binary subheader to read

    def read_controllers(self, node: MDLNode) -> None:
        """Read the controllers of a node.

        Args:
            node: Node to read controllers for

        Raises:
            MDLReadError: If there is an error reading controllers
        """
        pass  # ASCII does not have binary controllers to read

    def read_controller_data(self, node: MDLNode) -> None:
        """Read the controller data of a node.

        Args:
            node: Node to read controller data for

        Raises:
            MDLReadError: If there is an error reading controller data
        """
        pass  # ASCII does not have binary controller data to read

    def read_vertex_coordinates(self, node: MDLNode) -> None:
        """Read the vertex coordinates of a node.

        Args:
            node: Node to read vertex coordinates for

        Raises:
            MDLReadError: If there is an error reading vertex coordinates
        """
        pass  # Vertex coordinates are read in read_geometry

    def read_faces(self, node: MDLNode) -> None:
        """Read the faces of a node.

        Args:
            node: Node to read faces for

        Raises:
            MDLReadError: If there is an error reading faces
        """
        pass  # Faces are read in read_geometry

    def read_aabb(self, node: MDLNode) -> None:
        """Read the AABB (Axis-Aligned Bounding Box) of a node.

        Args:
            node: Node to read AABB for

        Raises:
            MDLReadError: If there is an error reading AABB
        """
        pass  # ASCII does not have binary AABB data to read
