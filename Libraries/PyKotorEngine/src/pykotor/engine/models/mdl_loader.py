from __future__ import annotations

import struct

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from loggerplus import RobustLogger
from ursina import Entity, Ursina, Vec3
from ursina.shaders import lit_with_shadows_shader

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.gl.models.mdl import Mesh
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pathlib import Path

    from direct.showbase.Loader import Loader
    from direct.showbase.ShowBase import ShowBase
    from ursina import NodePath

    from pykotor.common.module import ModuleResource
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.git import GITInstance
    from pykotor.resource.generics.utc import UTC

    base: ShowBase = ShowBase()
    render: NodePath = NodePath("render")  # idek. somehow this is always defined.
    loader: Loader = Loader(base)  # pyright: ignore[reportUnknownParameterType]


T = TypeVar("T")


# Empty model data for fallbacks
EMPTY_MDL_DATA = bytes([0] * 1024)  # Minimal valid MDL structure
EMPTY_MDX_DATA = bytes([0] * 1024)  # Minimal valid MDX structure

class UrsinaRenderObject:
    """Ursina equivalent of RenderObject."""
    def __init__(
        self,
        model_name: str,
        data: Any = None,
        override_texture: str | None = None
    ):
        self.entity = Entity(
            model=model_name,
            texture=override_texture if override_texture else "white_cube",
            shader=lit_with_shadows_shader
        )
        self.data = data
        self.children: list[UrsinaRenderObject] = []

    def set_transform(self, transform: tuple[Vec3, Vec3, Vec3]):
        """Set position, rotation and scale."""
        position, rotation, scale = transform
        self.entity.position = Vec3(*position)
        self.entity.rotation = Vec3(*rotation)
        self.entity.scale = Vec3(*scale)

    def set_rotation(self, x: float, y: float, z: float):
        """Set rotation in Euler angles."""
        self.entity.rotation = Vec3(x, y, z)

    def rotation(self) -> Vec3:
        """Get current rotation."""
        return self.entity.rotation

    def destroy(self):
        """Clean up the entity and its children."""
        for child in self.children:
            child.destroy()
        destroy(self.entity)


class UrsinaModel:
    """Ursina equivalent of the OpenGL Model class."""
    def __init__(self, root_entity: Entity):
        self.root = root_entity
        self.children: list[Entity] = []

    def find(self, node_name: str) -> Entity | None:
        """Find a child node by name."""
        def search_entity(entity: Entity) -> Entity | None:
            if entity.name.lower() == node_name.lower():
                return entity
            for child in entity.children:
                result = search_entity(child)
                if result:
                    return result
            return None

        return search_entity(self.root)

    def all(self) -> list[Entity]:
        """Get all nodes in the model hierarchy."""
        all_entities = []
        def collect_entities(entity: Entity):
            all_entities.append(entity)
            for child in entity.children:
                collect_entities(child)

        collect_entities(self.root)
        return all_entities

    def box(self) -> tuple[Vec3, Vec3]:
        """Get bounding box of model."""
        min_point = Vec3(float("inf"), float("inf"), float("inf"))
        max_point = Vec3(float("-inf"), float("-inf"), float("-inf"))

        for entity in self.all():
            if hasattr(entity, "model") and entity.model:
                # Get vertices from model
                for vertex in entity.model.vertices:
                    # Transform vertex to world space
                    world_pos = entity.world_position + vertex

                    # Update bounds
                    min_point.x = min(min_point.x, world_pos.x)
                    min_point.y = min(min_point.y, world_pos.y)
                    min_point.z = min(min_point.z, world_pos.z)
                    max_point.x = max(max_point.x, world_pos.x)
                    max_point.y = max(max_point.y, world_pos.y)
                    max_point.z = max(max_point.z, world_pos.z)

        # Add padding
        min_point -= Vec3(0.1, 0.1, 0.1)
        max_point += Vec3(0.1, 0.1, 0.1)

        return min_point, max_point  # pyright: ignore[reportReturnType]


@dataclass
class MeshData:
    vertices: list[Vec3]
    triangles: list[int]
    uvs: list[tuple[float, float]]
    texture_name: str
    lightmap_name: str
    mdx_size: int
    mdx_data_bitflags: int
    mdx_vertex_offset: int
    mdx_normal_offset: int
    mdx_texture_offset: int
    mdx_lightmap_offset: int


class ModelLoader:
    @staticmethod
    def load_model(
        mdl_data: bytes,
        mdx_data: bytes,
        texture_name: str | None = None
    ) -> Entity:
        """Load a KotOR MDL/MDX model pair and convert to Ursina Entity."""
        mdl = BinaryReader.from_bytes(mdl_data, 12)
        mdx = BinaryReader.from_bytes(mdx_data)

        # Read MDL header
        mdl.seek(40)
        offset = mdl.read_uint32()

        # Read name table
        mdl.seek(184)
        offset_to_name_offsets = mdl.read_uint32()
        name_count = mdl.read_uint32()

        mdl.seek(offset_to_name_offsets)
        name_offsets = [mdl.read_uint32() for _ in range(name_count)]
        names = []
        for name_offset in name_offsets:
            mdl.seek(name_offset)
            names.append(mdl.read_terminated_string("\0"))

        # Create root entity
        root_entity = Entity(shader=lit_with_shadows_shader)

        # Read node data
        mdl.seek(offset)
        node_type = mdl.read_uint16()
        mdl.read_uint16()  # supernode id
        _name_id = mdl.read_uint16()

        mdl.seek(offset + 16)
        position = Vec3(mdl.read_single(), mdl.read_single(), mdl.read_single())
        rotation = Vec3(mdl.read_single(), mdl.read_single(), mdl.read_single(), mdl.read_single())
        child_offsets = mdl.read_uint32()
        child_count = mdl.read_uint32()

        # Process mesh data if this is a mesh node
        if node_type & 0x100000:
            mdl.seek(offset + 80)
            is_tsl_model = mdl.read_uint32() in {4216880, 4216816, 4216864}

            mdl.seek(offset + 80 + 8)
            mdl.read_uint32()  # offset_to_faces
            face_count = mdl.read_uint32()

            mdl.seek(offset + 80 + 88)
            texture = mdl.read_terminated_string("\0", 32)
            _lightmap = mdl.read_terminated_string("\0", 32)

            mdl.seek(offset + 80 + 313)
            _render = bool(mdl.read_uint8())

            mdl.seek(offset + 80 + 304)
            vertex_count = mdl.read_uint16()

            mdl.seek(offset + 80 + (332 if is_tsl_model else 324))

            mdx_offset = mdl.read_uint32()

            # Read element data
            mdl.seek(offset + 80 + 184)
            element_offsets_count = mdl.read_uint32()
            offset_to_element_offsets = mdl.read_int32()

            triangles = []
            if offset_to_element_offsets != -1 and element_offsets_count > 0:
                mdl.seek(offset_to_element_offsets)
                offset_to_elements = mdl.read_uint32()
                mdl.seek(offset_to_elements)
                element_data = mdl.read_bytes(face_count * 2 * 3)
                for i in range(0, len(element_data), 2):
                    triangles.append(struct.unpack("H", element_data[i:i+2])[0])

            # Read vertex data
            mdl.seek(offset + 80 + 252)
            mdx_block_size = mdl.read_uint32()
            _mdx_data_bitflags = mdl.read_uint32()
            mdx_vertex_offset = mdl.read_int32()
            _mdx_normal_offset = mdl.read_int32()
            mdl.skip(4)
            mdx_texture_offset = mdl.read_int32()
            _mdx_lightmap_offset = mdl.read_int32()

            vertices = []
            uvs = []
            for i in range(vertex_count):
                mdx.seek(mdx_offset + i * mdx_block_size + mdx_vertex_offset)
                vertices.append(Vec3(struct.unpack("fff", mdx.read_bytes(12))))

                if mdx_texture_offset != -1:
                    mdx.seek(mdx_offset + i * mdx_block_size + mdx_texture_offset)
                    uvs.append((struct.unpack("ff", mdx.read_bytes(8))))

            # Create mesh
            mesh = Mesh(
                vertices=vertices,
                triangles=triangles,
                uvs=uvs if uvs else None,
                mode="triangle"
            )
            root_entity.model = mesh

            # Apply texture
            if texture_name:
                root_entity.texture = texture_name
            elif texture and texture != "NULL":
                root_entity.texture = texture

        # Process child nodes
        for i in range(child_count):
            mdl.seek(child_offsets + i * 4)
            _offset_to_child = mdl.read_uint32()
            child_entity: Entity = ModelLoader.load_model(mdl_data, mdx_data)
            child_entity.parent = root_entity

        # Set transform
        root_entity.position = position
        root_entity.rotation = rotation

        return root_entity

    @staticmethod
    def create_basic_shapes() -> dict[str, Entity]:
        """Create basic primitive shapes for debug/placeholder use."""
        return {
            "cube": Entity(model="cube"),
            "sphere": Entity(model="sphere"),
            "plane": Entity(model="plane"),
            "quad": Entity(model="quad")
        }

    def _resource_from_gitinstance(
        self,
        instance: GITInstance,
        lookup_func: Callable[..., ModuleResource[T] | None],
    ) -> T | None:
        resource: ModuleResource[T] | None = lookup_func(str(instance.resref))
        if resource is None:
            RobustLogger().error(f"The module '{self.module.root()}' does not store '{instance.identifier()}' needed to render a Scene.")
            return None
        resource_data: T | None = resource.resource()
        if resource_data is None:
            RobustLogger().error(f"No locations found for '{resource.identifier()}' needed by module '{self.module.root()}'")
            return None
        return resource_data

    def model(  # noqa: C901, PLR0912
        self,
        name: str,
    ) -> UrsinaModel:
        mdl_data = EMPTY_MDL_DATA
        mdx_data = EMPTY_MDX_DATA
        try:
            mdl_reader: BinaryReader = BinaryReader.from_bytes(mdl_data, 12)
            mdx_reader: BinaryReader = BinaryReader.from_bytes(mdx_data)
            model: UrsinaModel = gl_load_stitched_model(self, mdl_reader, mdx_reader)
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Could not load model '{name}'.")
            model = gl_load_stitched_model(
                self,
                BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                BinaryReader.from_bytes(EMPTY_MDX_DATA),
            )

            self.models[name] = model
        return self.models[name]


    def get_creature_render_object(  # noqa: C901
        self,
        instance: GITCreature,
        installation: Installation,
        appearance_2da: TwoDA,
        heads_2da: TwoDA,
        baseitems_2da: TwoDA,
        utc: UTC | None = None,
    ) -> UrsinaRenderObject:
        assert installation is not None
        try:
            if utc is None:
                utc = self._resource_from_gitinstance(instance, self.module.creature)
            if utc is None:
                RobustLogger().warning(f"Could not get UTC for GITCreature instance '{instance.identifier()}', not found in mod/override.")
                return UrsinaRenderObject("unknown", data=instance)

            head_obj: UrsinaRenderObject | None = None
            mask_hook = None

            body_model, body_texture = creature.get_body_model(
                utc,
                installation,
                appearance=appearance_2da,
                baseitems=baseitems_2da,
            )
            if not body_model or not body_model.strip():
                raise ValueError("creature.get_body_model failed to return a valid body_model resref str.")  # noqa: TRY301
            head_model, head_texture = creature.get_head_model(
                utc,
                installation,
                appearance=appearance_2da,
                heads=heads_2da,
            )
            rhand_model, lhand_model = creature.get_weapon_models(
                utc,
                installation,
                appearance=appearance_2da,
                baseitems=baseitems_2da,
            )
            mask_model = creature.get_mask_model(utc, installation)

            obj = UrsinaRenderObject(body_model, data=instance, override_texture=body_texture)

            head_hook: UrsinaModel | None = self.model(body_model).find("headhook")
            if head_model and head_hook:
                head_obj = UrsinaRenderObject(head_model, override_texture=head_texture)
                head_obj.set_transform(head_hook.global_transform())
                obj.children.append(head_obj)

            rhand_hook: UrsinaModel | None = self.model(body_model).find("rhand")
            if rhand_model and rhand_hook:
                rhand_obj = UrsinaRenderObject(rhand_model)
                rhand_obj.set_transform(rhand_hook.global_transform())
                obj.children.append(rhand_obj)
            lhand_hook: UrsinaModel | None = self.model(body_model).find("lhand")
            if lhand_model and lhand_hook:
                lhand_obj = UrsinaRenderObject(lhand_model)
                lhand_obj.set_transform(lhand_hook.global_transform())
                obj.children.append(lhand_obj)
            if head_hook is None:
                mask_hook: UrsinaModel | None = self.model(body_model).find("gogglehook")
            elif head_model:
                mask_hook = self.model(head_model).find("gogglehook")
            if mask_model and mask_hook:
                mask_obj = UrsinaRenderObject(mask_model)
                mask_obj.set_transform(mask_hook.global_transform())
                if head_hook is None:
                    obj.children.append(mask_obj)
                elif head_obj is not None:
                    head_obj.children.append(mask_obj)

        except Exception:  # noqa: BLE001
            RobustLogger().exception("Exception occurred getting the creature render object.")
            # If failed to load creature models, use the unknown model instead
            obj = UrsinaRenderObject("unknown", data=instance)

        return obj


if __name__ == "__main__":
    from ursina import Button, Text, camera, color, destroy

    from pykotor.extract.installation import Installation
    from pykotor.resource.generics.git import GITCreature
    from pykotor.resource.generics.utc import read_utc
    from pykotor.resource.type import ResourceType
    from pykotor.tools import creature
    from pykotor.tools.path import find_kotor_paths_from_default

    # Find KotOR installation and create Installation object
    paths: dict[Game, list[Path]] = find_kotor_paths_from_default()
    if not paths:
        print("Could not find KotOR installation")
        exit(1)

    installation = Installation(paths[Game.K1][0])

    # Load all UTCs from installation
    print("Loading UTCs from installation...")
    all_utcs: list[UTC] = [read_utc(res.data) for res in installation if res.restype == ResourceType.UTC]
    print(f"Found {len(all_utcs)} UTCs")

    # Current model entity reference
    current_model = None

    def load_creature(utc_index: int):
        global current_model

        # Clear previous model if it exists
        if current_model:
            destroy(current_model)

        # Get the selected UTC
        utc = all_utcs[utc_index]

        # Create a test creature instance
        creature_instance = GITCreature()
        creature_instance.position.x = 0
        creature_instance.position.y = 0
        creature_instance.position.z = 0

        try:
            # Load and render the creature model
            render_obj = ModelLoader.get_creature_render_object(creature_instance, utc)
            current_model = render_obj

            # Update camera
            camera.position = (0, -5, 2)
            camera.look_at(current_model)

        except Exception as e:
            print(f"Error loading creature: {e}")

    # Create UI elements
    title = Text("KotOR Creature Viewer", y=0.45)

    # Create buttons for UTC selection
    button_height = 0.35
    buttons_per_column = 10
    column = 0

    for i, utc in enumerate(all_utcs):
        # Get creature name
        name = str(utc.first_name)
        if not name:
            name = f"Creature {i}"

        # Create button
        Button(
            text=name,
            scale=(0.2, 0.05),
            position=(-0.6 + (column * 0.25), button_height),
            color=color.azure,
            on_click=lambda i=i: load_creature(i)
        )

        button_height -= 0.06
        if button_height < -0.35:
            button_height = 0.35
            column += 1

    # Set up initial camera
    camera.position = (0, -5, 2)
    camera.rotation_x = 0

    print("Starting demo...")
    Ursina().run()
    print("Demo finished.")
