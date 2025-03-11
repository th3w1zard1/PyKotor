"""Functions for reading and writing MDL format."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import Color, Game, ResRef
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.mdl.data.animation import MDLAnimation
from pykotor.resource.formats.mdl.data.controller import MDLController, MDLControllerRow
from pykotor.resource.formats.mdl.data.emitter import MDLEmitter
from pykotor.resource.formats.mdl.data.enums import (
    MDLBlendType,
    MDLClassification,
    MDLControllerConstants,
    MDLControllerType,
    MDLEmitterFlags,
    MDLEmitterType,
    MDLModelType,
    MDLNodeFlags,
    MDLRenderType,
    MDLUpdateType,
    MDXDataFlags,
)
from pykotor.resource.formats.mdl.data.geometry import MDLDangly, MDLFace, MDLMesh, MDLSkin
from pykotor.resource.formats.mdl.data.light import MDLLight
from pykotor.resource.formats.mdl.data.model import MDL
from pykotor.resource.formats.mdl.data.node import MDLNode
from pykotor.resource.formats.mdl.data.reference import MDLReference
from pykotor.resource.formats.mdl.data.saber import MDLSaber
from pykotor.resource.formats.mdl.io.model_header import _ModelHeader
from utility.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from utility.common.misc_string.case_insens_str import CaseInsensImmutableStr

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.data.walkmesh import MDLAABBNode, MDLWalkmesh
    from pykotor.resource.type import SOURCE_TYPES


class MDLBinaryReader:
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
        source_mdx: SOURCE_TYPES | None = None,
        offset_mdx: int = 0,
        size_mdx: int = 0,
        *,
        use_high_level_reader: bool = True,
    ):
        self._mdl_reader: BinaryReader = BinaryReader.from_auto(source, offset, size)
        self._mdx_reader: BinaryReader | None = None if source_mdx is None else BinaryReader.from_auto(source_mdx, offset_mdx, size_mdx)
        self._game: Game = Game.K1

    def load(self) -> MDL:
        """Load MDL/MDX data into a model structure.

        Returns:
            MDL: The loaded model data.
        """
        self._mdl: MDL = MDL()
        self._names: list[str] = []
        self._node_by_number: dict[int, MDLNode] = {}

        # Read file header (first 12 bytes)
        if self._mdl_reader.read_uint32() != 0:
            raise ValueError("Invalid MDL signature")
        mdl_size = self._mdl_reader.read_uint32()
        mdx_size = self._mdl_reader.read_uint32()

        # Read model header
        model_header: _ModelHeader = _ModelHeader().read(self._mdl_reader)

        # Set basic model properties
        self._mdl.name = model_header.geometry.model_name
        self._mdl.affected_by_fog = model_header.affected_by_fog
        self._mdl.supermodel = model_header.supermodel
        self._mdl.animscale = model_header.anim_scale
        # Map MDLModelType to MDLClassification
        model_type_map = {
            MDLModelType.OTHER: MDLClassification.OTHER,
            MDLModelType.EFFECT: MDLClassification.EFFECT,
            MDLModelType.TILE: MDLClassification.TILE,
            MDLModelType.CHARACTER: MDLClassification.CHARACTER,
            MDLModelType.DOOR: MDLClassification.DOOR,
            MDLModelType.LIGHTSABER: MDLClassification.LIGHTSABER,
            MDLModelType.PLACEABLE: MDLClassification.PLACEABLE,
            MDLModelType.GUI: MDLClassification.GUI,
            MDLModelType.ITEM: MDLClassification.WEAPON,
            MDLModelType.WAYPOINT: MDLClassification.WAYPOINT,
            MDLModelType.WEAPON: MDLClassification.WEAPON,
            MDLModelType.FURNITURE: MDLClassification.FURNITURE,
            MDLModelType.CREATURE: MDLClassification.CHARACTER,
            MDLModelType.PROJECTILE: MDLClassification.EFFECT,
            MDLModelType.AREA_EFFECT: MDLClassification.EFFECT,
            MDLModelType.TRIGGER: MDLClassification.OTHER,
            MDLModelType.SOUND: MDLClassification.OTHER,
        }
        self._mdl.classification = model_type_map.get(model_header.model_type, MDLClassification.OTHER)
        self._mdl.subclassification = model_header.model_flags.value

        # Load names array
        self._load_names(model_header.offset_to_name_offsets, model_header.name_offsets_count)

        # Peek nodes to build name list
        self._peek_nodes(model_header.geometry.root_node_offset)

        # Load node hierarchy
        self._mdl.root = self._load_nodes(model_header.geometry.root_node_offset, 0)

        # Load animations if present
        if model_header.animation_count > 0:
            self._load_animations(model_header.offset_to_animations, model_header.animation_count)

        self._mdl_reader.close()
        if self._mdx_reader is not None:
            self._mdx_reader.close()

        return self._mdl

    def _load_names(self, offset: int, count: int) -> None:
        """Load the array of node names.

        Args:
            offset: Offset to name array
            count: Number of names
        """
        self._mdl_reader.seek(12 + offset)  # 12 byte header
        offsets = [self._mdl_reader.read_uint32() for _ in range(count)]
        for off in offsets:
            self._mdl_reader.seek(12 + off)
            self._names.append(self._mdl_reader.read_terminated_string("\0"))

    def _peek_nodes(self, offset: int) -> None:
        """Pre-scan nodes to build name list.

        Args:
            offset: Offset to node
        """
        self._mdl_reader.seek(12 + offset)
        type_flags = self._mdl_reader.read_uint16()
        name_index = self._mdl_reader.read_uint16()
        self._mdl_reader.skip(38)  # Skip to children array
        children_count = self._mdl_reader.read_uint32()
        children_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Process children recursively
        if children_count > 0:
            self._mdl_reader.seek(12 + children_offset)
            child_offsets = [self._mdl_reader.read_uint32() for _ in range(children_count)]
            for child_offset in child_offsets:
                self._peek_nodes(child_offset)

    def _load_nodes(self, offset: int, export_order: int, parent: MDLNode | None = None) -> MDLNode:
        """Load a node and its children recursively.

        Args:
            offset: Offset to node data
            export_order: Order for export
            parent: Parent node if any

        Returns:
            MDLNode: The loaded node
        """
        self._mdl_reader.seek(12 + offset)

        # Read node header
        type_flags = self._mdl_reader.read_uint16()
        node_number = self._mdl_reader.read_uint16()
        name_index = self._mdl_reader.read_uint16()
        self._mdl_reader.skip(2)  # padding
        root_offset = self._mdl_reader.read_uint32()
        parent_offset = self._mdl_reader.read_uint32()

        # Read position and orientation
        position = Vector3(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )
        orientation = Vector4(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )

        # Read array definitions
        children_count = self._mdl_reader.read_uint32()
        children_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2
        controller_count = self._mdl_reader.read_uint32()
        controller_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2
        controller_data_count = self._mdl_reader.read_uint32()
        controller_data_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Create node
        node = MDLNode()
        node.name = CaseInsensImmutableStr(self._names[name_index])
        node.node_id = node_number
        node.position = position
        node.orientation = orientation
        node.parent_id = -1 if parent is None else parent.node_id

        # Store for animation lookup
        self._node_by_number[node_number] = node

        # Load node-specific data based on type flags
        if type_flags & MDLNodeFlags.HAS_LIGHT:
            node.light = self._load_light_data()

        if type_flags & MDLNodeFlags.HAS_EMITTER:
            node.emitter = self._load_emitter_data()

        if type_flags & MDLNodeFlags.HAS_REFERENCE:
            node.reference = self._load_reference_data()

        if type_flags & MDLNodeFlags.HAS_MESH:
            node.mesh = self._load_mesh_data()

        if type_flags & MDLNodeFlags.HAS_SKIN:
            node.skin = self._load_skin_data()

        if type_flags & MDLNodeFlags.HAS_DANGLY:
            node.dangly = self._load_dangly_data()

        if type_flags & MDLNodeFlags.HAS_AABB:
            node.aabb = self._load_aabb_data()

        if type_flags & MDLNodeFlags.HAS_SABER:
            node.saber = self._load_saber_data()

        # Load controllers if present
        if controller_count > 0:
            node.controllers = self._load_controllers(
                controller_offset,
                controller_count,
                controller_data_offset,
                controller_data_count
            )

        # Load children recursively
        if children_count > 0:
            self._mdl_reader.seek(12 + children_offset)
            child_offsets = [self._mdl_reader.read_uint32() for _ in range(children_count)]
            for i, child_offset in enumerate(child_offsets):
                child = self._load_nodes(child_offset, i, node)
                node.children.append(child)

        return node

    def _load_light_data(self) -> MDLLight:
        """Load light node data.

        Returns:
            MDLLight: The loaded light data
        """
        light = MDLLight()

        # Read flare radius
        light.flare_radius = self._mdl_reader.read_single()

        # Skip unknown array
        _ = self._mdl_reader.read_uint32()  # count
        _ = self._mdl_reader.read_uint32()  # offset
        _ = self._mdl_reader.read_uint32()  # count2

        # Read flare arrays
        flare_sizes_count = self._mdl_reader.read_uint32()
        flare_sizes_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        flare_positions_count = self._mdl_reader.read_uint32()
        flare_positions_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        flare_color_shifts_count = self._mdl_reader.read_uint32()
        flare_color_shifts_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        flare_textures_count = self._mdl_reader.read_uint32()
        flare_textures_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Read light properties
        light.light_priority = self._mdl_reader.read_int32()
        light.ambient_only = bool(self._mdl_reader.read_uint32())
        light.dynamic_type = self._mdl_reader.read_uint32()
        light.affect_dynamic = bool(self._mdl_reader.read_uint32())
        light.shadow = bool(self._mdl_reader.read_uint32())
        light.flare = bool(self._mdl_reader.read_uint32())
        light.fading_light = bool(self._mdl_reader.read_uint32())

        # Load flare data if present
        if flare_sizes_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + flare_sizes_offset)
            light.flare_sizes = [self._mdl_reader.read_single() for _ in range(flare_sizes_count)]
            self._mdl_reader.seek(old_pos)

        if flare_positions_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + flare_positions_offset)
            light.flare_positions = [self._mdl_reader.read_single() for _ in range(flare_positions_count)]
            self._mdl_reader.seek(old_pos)

        if flare_color_shifts_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + flare_color_shifts_offset)
            for _ in range(flare_color_shifts_count):
                color = Color(
                    self._mdl_reader.read_single(),
                    self._mdl_reader.read_single(),
                    self._mdl_reader.read_single()
                )
                light.flare_color_shifts.append(color)
            self._mdl_reader.seek(old_pos)

        if flare_textures_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + flare_textures_offset)
            texture_offsets = [self._mdl_reader.read_uint32() for _ in range(flare_textures_count)]
            for offset in texture_offsets:
                self._mdl_reader.seek(12 + offset)
                light.flare_textures.append(ResRef(self._mdl_reader.read_terminated_string("\0")))
            self._mdl_reader.seek(old_pos)

        return light

    def _load_emitter_data(self) -> MDLEmitter:
        """Load emitter node data.

        Returns:
            MDLEmitter: The loaded emitter data
        """
        emitter = MDLEmitter()

        # Read basic properties
        emitter.dead_space = self._mdl_reader.read_single()
        emitter.blast_radius = self._mdl_reader.read_single()
        emitter.blast_length = self._mdl_reader.read_single()
        emitter.branch_count = self._mdl_reader.read_uint32()
        emitter.control_point_smoothing = self._mdl_reader.read_single()
        emitter.x_grid = self._mdl_reader.read_uint32()
        emitter.y_grid = self._mdl_reader.read_uint32()

        # Read behavior types
        emitter.spawn_type = MDLEmitterType(self._mdl_reader.read_uint32())
        emitter.update_type = MDLUpdateType(self._mdl_reader.read_terminated_string("\0"))
        emitter.render_type = MDLRenderType(self._mdl_reader.read_terminated_string("\0"))
        emitter.blend_type = MDLBlendType(self._mdl_reader.read_terminated_string("\0"))

        # Read textures and names
        emitter.texture = ResRef(self._mdl_reader.read_terminated_string("\0"))
        emitter.chunk_name = ResRef(self._mdl_reader.read_terminated_string("\0", 16))

        # Read flags and properties
        emitter.twosided = bool(self._mdl_reader.read_uint32())
        emitter.loop = bool(self._mdl_reader.read_uint32())
        emitter.render_order = self._mdl_reader.read_uint16()
        emitter.frame_blend = bool(self._mdl_reader.read_uint8())
        emitter.depth_texture = ResRef(self._mdl_reader.read_terminated_string("\0"))

        self._mdl_reader.skip(1)  # padding

        # Read emitter flags
        flags = self._mdl_reader.read_uint32()
        emitter.emitter_flags = MDLEmitterFlags(flags)

        return emitter

    def _load_reference_data(self) -> MDLReference:
        """Load reference node data.

        Returns:
            MDLReference: The loaded reference data
        """
        reference = MDLReference()

        # Read model name
        reference.model = ResRef(self._mdl_reader.read_terminated_string("\0"))

        # Read reattachable flag
        reference.reattachable = bool(self._mdl_reader.read_uint32())

        return reference

    def _load_mesh_data(self) -> MDLMesh:
        """Load mesh data.

        Returns:
            MDLMesh: The loaded mesh data
        """
        mesh = MDLMesh()

        # Read function pointers
        _ = self._mdl_reader.read_uint32()  # fn_ptr1
        _ = self._mdl_reader.read_uint32()  # fn_ptr2

        # Read face array info
        face_count = self._mdl_reader.read_uint32()
        face_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Read bounding box and properties
        bounding_box_min = Vector3(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )
        bounding_box_max = Vector3(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )
        radius = self._mdl_reader.read_single()
        average = Vector3(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )
        diffuse = Color(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )
        ambient = Color(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )

        # Read transparency and textures
        transparency_hint = self._mdl_reader.read_uint32()
        texture = ResRef(self._mdl_reader.read_terminated_string("\0", 32))
        texture2 = ResRef(self._mdl_reader.read_terminated_string("\0", 32))
        _ = self._mdl_reader.read_terminated_string("\0", 12)  # bitmap3
        _ = self._mdl_reader.read_terminated_string("\0", 12)  # bitmap4

        # Read index arrays
        index_count_count = self._mdl_reader.read_uint32()
        index_count_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        index_offset_count = self._mdl_reader.read_uint32()
        index_offset_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Skip unknown arrays
        self._mdl_reader.skip(3 * 4)  # unknown
        self._mdl_reader.skip(8)  # saber unknown

        # Read UV animation properties
        animate_uv = bool(self._mdl_reader.read_uint32())
        uv_direction_x = self._mdl_reader.read_single()
        uv_direction_y = self._mdl_reader.read_single()
        uv_jitter = self._mdl_reader.read_single()
        uv_jitter_speed = self._mdl_reader.read_single()

        # Read MDX data info
        mdx_data_size = self._mdl_reader.read_uint32()
        mdx_data_bitmap = self._mdl_reader.read_uint32()
        mdx_vertices_offset = self._mdl_reader.read_uint32()
        mdx_normals_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # mdx_colors_offset
        mdx_tex1_offset = self._mdl_reader.read_uint32()
        mdx_tex2_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # mdx_tex3_offset
        _ = self._mdl_reader.read_uint32()  # mdx_tex4_offset
        _ = self._mdl_reader.read_uint32()  # mdx_tan1_offset
        _ = self._mdl_reader.read_uint32()  # mdx_tan2_offset
        _ = self._mdl_reader.read_uint32()  # mdx_tan3_offset
        _ = self._mdl_reader.read_uint32()  # mdx_tan4_offset

        # Read mesh properties
        vertex_count = self._mdl_reader.read_uint16()
        _ = self._mdl_reader.read_uint16()  # texture_count
        has_lightmap = bool(self._mdl_reader.read_uint8())
        rotate_texture = bool(self._mdl_reader.read_uint8())
        background_geometry = bool(self._mdl_reader.read_uint8())
        shadow = bool(self._mdl_reader.read_uint8())
        beaming = bool(self._mdl_reader.read_uint8())
        render = bool(self._mdl_reader.read_uint8())

        # Read TSL-specific properties
        if self._is_tsl():
            dirt_enabled = bool(self._mdl_reader.read_uint8())
            self._mdl_reader.skip(1)  # padding
            dirt_texture = self._mdl_reader.read_uint16()
            dirt_coord_space = self._mdl_reader.read_uint16()
            hide_in_holograms = bool(self._mdl_reader.read_uint8())
            self._mdl_reader.skip(1)  # padding

        # Skip padding and read final offsets
        self._mdl_reader.skip(2)  # padding
        _ = self._mdl_reader.read_single()  # total_area
        self._mdl_reader.skip(4)  # padding
        mdx_offset = self._mdl_reader.read_uint32()
        if not self._is_xbox():
            _ = self._mdl_reader.read_uint32()  # vertex_array_offset

        # Set mesh properties
        mesh.render = render
        mesh.shadow = shadow
        mesh.lightmapped = has_lightmap
        mesh.beaming = beaming
        mesh.tangent_space = bool(mdx_data_bitmap & MDXDataFlags.TANGENT1)
        mesh.rotate_texture = rotate_texture
        mesh.background_geometry = background_geometry
        mesh.animate_uv = animate_uv
        mesh.uv_direction_x = uv_direction_x
        mesh.uv_direction_y = uv_direction_y
        mesh.uv_jitter = uv_jitter
        mesh.uv_jitter_speed = uv_jitter_speed
        mesh.transparency_hint = transparency_hint
        mesh.ambient = ambient
        mesh.diffuse = diffuse
        mesh.center = average
        mesh.bounding_box_min = bounding_box_min
        mesh.bounding_box_max = bounding_box_max
        mesh.radius = radius

        # Set textures if present
        if texture and texture.get_value().lower() != "null":
            mesh.texture = texture
        if texture2 and texture2.get_value().lower() != "null":
            mesh.texture2 = texture2

        # Set TSL-specific properties
        if self._is_tsl():
            mesh.dirt_enabled = dirt_enabled
            mesh.dirt_texture = dirt_texture
            mesh.dirt_coord_space = dirt_coord_space
            mesh.hide_in_holograms = hide_in_holograms

        # Load faces if present
        if face_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + face_offset)

            for _ in range(face_count):
                # Read face normal and plane distance
                normal = Vector3(
                    self._mdl_reader.read_single(),
                    self._mdl_reader.read_single(),
                    self._mdl_reader.read_single()
                )
                plane_distance = self._mdl_reader.read_single()

                # Read material and adjacency
                material = self._mdl_reader.read_uint32()
                adjacent = [self._mdl_reader.read_uint16() for _ in range(3)]

                # Read vertex indices
                indices = [self._mdl_reader.read_uint16() for _ in range(3)]

                # Create face
                face = MDLFace()
                face.material = SurfaceMaterial(material)
                face.vertex_indices = indices
                face.plane_normal = normal
                face.plane_distance = plane_distance
                face.adjacent_faces = adjacent

                mesh.faces.append(face)

            self._mdl_reader.seek(old_pos)

        # Load vertex data from MDX if present
        if mdx_data_size > 0 and self._mdx_reader is not None:
            for i in range(vertex_count):
                # Read vertex position
                self._mdx_reader.seek(mdx_offset + i * mdx_data_size + mdx_vertices_offset)
                vertex = Vector3(
                    self._mdx_reader.read_single(),
                    self._mdx_reader.read_single(),
                    self._mdx_reader.read_single()
                )
                mesh.vertices.append(vertex)

                # Read normal if present
                if mdx_data_bitmap & MDXDataFlags.NORMAL:
                    self._mdx_reader.seek(mdx_offset + i * mdx_data_size + mdx_normals_offset)
                    if self._is_xbox():
                        normal = self._decompress_vector_xbox(self._mdx_reader.read_uint32())
                    else:
                        normal = Vector3(
                            self._mdx_reader.read_single(),
                            self._mdx_reader.read_single(),
                            self._mdx_reader.read_single()
                        )
                    mesh.normals.append(normal)

                # Read UV coordinates if present
                if mdx_data_bitmap & MDXDataFlags.UV1:
                    self._mdx_reader.seek(mdx_offset + i * mdx_data_size + mdx_tex1_offset)
                    uv1 = Vector2(
                        self._mdx_reader.read_single(),
                        self._mdx_reader.read_single()
                    )
                    mesh.uvs.append(uv1)

                if mdx_data_bitmap & MDXDataFlags.UV2:
                    self._mdx_reader.seek(mdx_offset + i * mdx_data_size + mdx_tex2_offset)
                    uv2 = Vector2(
                        self._mdx_reader.read_single(),
                        self._mdx_reader.read_single()
                    )
                    mesh.lightmap_uvs.append(uv2)

        return mesh

    def _load_animations(self, offset: int, count: int) -> None:
        """Load animation data.

        Args:
            offset: Offset to animation array
            count: Number of animations
        """
        if count == 0:
            return

        # Read animation offsets
        self._mdl_reader.seek(12 + offset)
        animation_offsets = [self._mdl_reader.read_uint32() for _ in range(count)]

        # Load each animation
        for anim_offset in animation_offsets:
            self._load_animation(anim_offset)

    def _load_animation(self, offset: int) -> None:
        """Load a single animation.

        Args:
            offset: Offset to animation data
        """
        self._mdl_reader.seek(12 + offset)

        # Skip function pointers
        _ = self._mdl_reader.read_uint32()  # fn_ptr1
        _ = self._mdl_reader.read_uint32()  # fn_ptr2

        # Read animation properties
        name = self._mdl_reader.read_terminated_string("\0", 32)
        root_node_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # total_node_count

        # Skip runtime arrays
        _ = self._mdl_reader.read_uint32()  # runtime_arr1_offset
        _ = self._mdl_reader.read_uint32()  # runtime_arr1_count
        _ = self._mdl_reader.read_uint32()  # runtime_arr1_count2
        _ = self._mdl_reader.read_uint32()  # runtime_arr2_offset
        _ = self._mdl_reader.read_uint32()  # runtime_arr2_count
        _ = self._mdl_reader.read_uint32()  # runtime_arr2_count2

        # Skip reference count and model type
        _ = self._mdl_reader.read_uint32()  # ref_count
        _ = self._mdl_reader.read_uint8()   # model_type
        self._mdl_reader.skip(3)  # padding

        # Read animation timing
        length = self._mdl_reader.read_single()
        transition_time = self._mdl_reader.read_single()
        anim_root = self._mdl_reader.read_terminated_string("\0", 32)

        # Read events array info
        events_count = self._mdl_reader.read_uint32()
        events_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # events_count2

        self._mdl_reader.skip(4)  # padding

        # Create animation
        animation = MDLAnimation()
        animation.name = name
        animation.length = length
        animation.transition_time = transition_time
        animation.root_node = anim_root

        # Load events if present
        if events_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + events_offset)

            for _ in range(events_count):
                time = self._mdl_reader.read_single()
                event_name = self._mdl_reader.read_terminated_string("\0", 32)
                animation.events.append((time, event_name))

            self._mdl_reader.seek(old_pos)

        # Load animation nodes
        animation.root = self._load_animation_node(root_node_offset, animation)
        self._mdl.animations.append(animation)

    def _load_skin_data(self) -> MDLSkin:
        """Load skin mesh data.

        Returns:
            MDLSkin: The loaded skin data
        """
        skin = MDLSkin()

        # Skip unknown array
        count = self._mdl_reader.read_uint32()
        offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Read MDX offsets
        skin.mdx_bone_weights_offset = self._mdl_reader.read_uint32()
        skin.mdx_bone_indices_offset = self._mdl_reader.read_uint32()

        # Read bone map
        bone_map_offset = self._mdl_reader.read_uint32()
        bone_map_count = self._mdl_reader.read_uint32()

        # Skip bone arrays
        for _ in range(3):  # qbone, tbone, garbage arrays
            count = self._mdl_reader.read_uint32()
            offset = self._mdl_reader.read_uint32()
            _ = self._mdl_reader.read_uint32()  # count2

        # Read bone indices
        skin.bone_indices = [self._mdl_reader.read_uint16() for _ in range(16)]
        self._mdl_reader.skip(4)  # padding

        # Load bone map if present
        if bone_map_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + bone_map_offset)

            if self._is_xbox():
                skin.bone_map = [self._mdl_reader.read_uint16() for _ in range(bone_map_count)]
            else:
                skin.bone_map = [int(self._mdl_reader.read_single()) for _ in range(bone_map_count)]

            self._mdl_reader.seek(old_pos)

        return skin

    def _load_dangly_data(self) -> MDLDangly:
        """Load dangly mesh data.

        Returns:
            MDLDangly: The loaded dangly data
        """
        dangly = MDLDangly()

        # Read constraints array info
        constraints_count = self._mdl_reader.read_uint32()
        constraints_offset = self._mdl_reader.read_uint32()
        _ = self._mdl_reader.read_uint32()  # count2

        # Read properties
        dangly.displacement = self._mdl_reader.read_single()
        dangly.tightness = self._mdl_reader.read_single()
        dangly.period = self._mdl_reader.read_single()

        # Skip vertex data offset
        self._mdl_reader.skip(4)

        # Load constraints if present
        if constraints_count > 0:
            old_pos = self._mdl_reader.tell()
            self._mdl_reader.seek(12 + constraints_offset)
            dangly.constraints = [self._mdl_reader.read_single() for _ in range(constraints_count)]
            self._mdl_reader.seek(old_pos)

        return dangly

    def _load_aabb_data(self) -> MDLWalkmesh:
        """Load AABB walkmesh data.

        Returns:
            MDLWalkmesh: The loaded AABB data
        """
        from pykotor.resource.formats.mdl.data.walkmesh import MDLWalkmesh

        walkmesh = MDLWalkmesh()

        # Read root AABB node offset
        root_offset = self._mdl_reader.read_uint32()

        # Load AABB tree recursively
        walkmesh.root = self._load_aabb_node(root_offset)

        return walkmesh

    def _load_aabb_node(self, offset: int) -> MDLAABBNode:
        """Load an AABB tree node recursively.

        Args:
            offset: Offset to node data

        Returns:
            MDLAABBNode: The loaded AABB node
        """
        from pykotor.resource.formats.mdl.data.walkmesh import MDLAABBNode

        old_pos = self._mdl_reader.tell()
        self._mdl_reader.seek(12 + offset)

        node = MDLAABBNode()

        # Read bounding box
        node.bounding_box_min = Vector3(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )
        node.bounding_box_max = Vector3(
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single(),
            self._mdl_reader.read_single()
        )

        # Read child offsets
        child1_offset = self._mdl_reader.read_uint32()
        child2_offset = self._mdl_reader.read_uint32()

        # Read face index and plane
        node.face_index = self._mdl_reader.read_int32()
        node.plane = self._mdl_reader.read_uint32()

        # Load children recursively
        if child1_offset > 0:
            node.left = self._load_aabb_node(child1_offset)
        if child2_offset > 0:
            node.right = self._load_aabb_node(child2_offset)

        self._mdl_reader.seek(old_pos)
        return node

    def _load_saber_data(self) -> MDLSaber:
        """Load lightsaber data.

        Returns:
            MDLSaber: The loaded saber data
        """
        saber = MDLSaber()

        # Read vertex data offsets
        saber.vertex_offset = self._mdl_reader.read_uint32()
        saber.uv_offset = self._mdl_reader.read_uint32()
        saber.normal_offset = self._mdl_reader.read_uint32()

        # Skip unknown values
        self._mdl_reader.skip(8)

        return saber

    def _load_controllers(self, offset: int, count: int, data_offset: int, data_count: int) -> list[MDLController]:
        """Load controller data.

        Args:
            offset: Offset to controller array
            count: Number of controllers
            data_offset: Offset to controller data
            data_count: Amount of controller data

        Returns:
            list[MDLController]: The loaded controllers
        """

        # TODO: dont' store binary information like offsets into MDLController, create a underscore-prefixed class. Whole point of mdl_data and MDLController is to provide a high-level abstraction to the complicated format that the MDL produces. e.g. it doesn't make sense to save the counts of the rows, when we have to load the row lists anyway.

        controllers: list[MDLController] = []

        # Read controller headers
        self._mdl_reader.seek(12 + offset)
        controllers: list[MDLController] = []
        for _ in range(count):
            controller_type = self._mdl_reader.read_uint32()
            self._mdl_reader.skip(2)  # unknown
            rows = self._mdl_reader.read_uint16()
            timekeys_offset = self._mdl_reader.read_uint16()
            data_offset = self._mdl_reader.read_uint16()
            columns = self._mdl_reader.read_uint8()
            self._mdl_reader.skip(3)  # padding

            # Read timekeys
            old_pos = self._mdl_reader.position()
            self._mdl_reader.seek(12 + data_offset + 4 * timekeys_offset)
            timekeys = [self._mdl_reader.read_single() for _ in range(rows)]

            # Read data values
            self._mdl_reader.seek(12 + data_offset + 4 * data_offset)

            # Handle special case for orientation controllers
            is_integral = False
            if controller_type == MDLControllerType.ORIENTATION and columns == 2:
                is_integral = True
                columns = 1
            else:
                columns &= 0xF  # Remove bezier flag
                if columns & MDLControllerConstants.CTRL_FLAG_BEZIER:
                    columns *= 3

            # Read data rows
            rows_data: list[MDLControllerRow] = []
            for _ in range(rows):
                row = MDLControllerRow()
                if is_integral:
                    row.values = [self._mdl_reader.read_uint32()]
                else:
                    row.values = [self._mdl_reader.read_single() for _ in range(columns)]
                rows_data.append(row)

            self._mdl_reader.seek(old_pos)
            controllers.append(MDLController(controller_type, rows_data, timekeys, is_integral))

        return controllers

    def _is_tsl(self) -> bool:
        """Check if this is a TSL model.

        Returns:
            bool: True if TSL, False if K1
        """
        return self._game == Game.K2

    def _is_xbox(self) -> bool:
        """Check if this is an Xbox model.

        Returns:
            bool: True if Xbox, False if PC
        """
        return False  # TODO: Implement Xbox detection
