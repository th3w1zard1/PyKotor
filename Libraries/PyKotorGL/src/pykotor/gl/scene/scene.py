from __future__ import annotations

import math

from copy import copy
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

import glm

from OpenGL.GL import glReadPixels
from OpenGL.raw.GL.ARB.vertex_shader import GL_FLOAT
from OpenGL.raw.GL.VERSION.GL_1_0 import (
    GL_BACK,
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_TEST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    glBlendFunc,
    glClear,
    glClearColor,
    glCullFace,
    glDisable,
    glEnable,
)
from OpenGL.raw.GL.VERSION.GL_1_2 import GL_BGRA, GL_UNSIGNED_INT_8_8_8_8
from glm import mat4, quat, vec3, vec4
from loggerplus import RobustLogger

from pykotor.common.geometry import Vector3
from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.gl.models.mdl import Boundary, Model
from pykotor.gl.models.predefined_mdl import (
    CAMERA_MDL_DATA,
    CAMERA_MDX_DATA,
    CURSOR_MDL_DATA,
    CURSOR_MDX_DATA,
    EMPTY_MDL_DATA,
    EMPTY_MDX_DATA,
    ENCOUNTER_MDL_DATA,
    ENCOUNTER_MDX_DATA,
    ENTRY_MDL_DATA,
    ENTRY_MDX_DATA,
    SOUND_MDL_DATA,
    SOUND_MDX_DATA,
    STORE_MDL_DATA,
    STORE_MDX_DATA,
    TRIGGER_MDL_DATA,
    TRIGGER_MDX_DATA,
    UNKNOWN_MDL_DATA,
    UNKNOWN_MDX_DATA,
    WAYPOINT_MDL_DATA,
    WAYPOINT_MDX_DATA,
)
from pykotor.gl.models.read_mdl import gl_load_stitched_model
from pykotor.gl.scene import Camera, RenderObject
from pykotor.gl.shader import KOTOR_FSHADER, KOTOR_VSHADER, PICKER_FSHADER, PICKER_VSHADER, PLAIN_FSHADER, PLAIN_VSHADER, Shader, Texture
from pykotor.resource.formats.lyt.lyt_data import LYT, LYTRoom
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.generics.git import GIT, GITCamera, GITCreature, GITDoor, GITEncounter, GITInstance, GITPlaceable, GITSound, GITStore, GITTrigger, GITWaypoint
from pykotor.resource.generics.utd import UTD
from pykotor.resource.generics.utp import UTP
from pykotor.resource.generics.uts import UTS
from pykotor.resource.type import ResourceType
from pykotor.tools import creature
from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.module import Module, ModulePieceResource, ModuleResource
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.gl.models.mdl import Model, Node
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.generics.utc import UTC

from typing import TYPE_CHECKING

from pykotor.resource.generics.ifo import IFO

T = TypeVar("T")
SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class Scene:
    SPECIAL_MODELS: ClassVar[list[str]] = ["waypoint", "store", "sound", "camera", "trigger", "encounter", "unknown"]

    def __init__(
        self,
        *,
        installation: Installation | None = None,
        module: Module | None = None,
    ):
        module_id_part: str = "" if module is None else f" from module '{module.root()}'"
        RobustLogger().info(f"Start initialize Scene{module_id_part}")

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_BACK)

        self.installation: Installation | None = installation
        self.textures: CaseInsensitiveDict[Texture] = CaseInsensitiveDict()
        self.textures["NULL"] = Texture.from_color()
        self.models: CaseInsensitiveDict[Model] = CaseInsensitiveDict()

        self.cursor: RenderObject = RenderObject("cursor")
        self.objects: dict[Any, RenderObject] = {}

        self.installation: Installation | None = installation
        self.selection: list[RenderObject] = []
        self._module: Module | None = module
        self.camera: Camera = Camera()
        self.cursor: RenderObject = RenderObject("cursor")

        self.git: GIT | None = None
        self.layout: LYT | None = None
        self.clear_cache_buffer: list[ResourceIdentifier] = []

        self.picker_shader: Shader = Shader(PICKER_VSHADER, PICKER_FSHADER)
        self.plain_shader: Shader = Shader(PLAIN_VSHADER, PLAIN_FSHADER)
        self.shader: Shader = Shader(KOTOR_VSHADER, KOTOR_FSHADER)

        self.jump_to_entry_location()

        self.table_doors: TwoDA = TwoDA()
        self.table_placeables: TwoDA = TwoDA()
        self.table_creatures: TwoDA = TwoDA()
        self.table_heads: TwoDA = TwoDA()
        self.table_baseitems: TwoDA = TwoDA()
        if installation is not None:
            self.set_installation(installation)

        self.hide_creatures: bool = False
        self.hide_placeables: bool = False
        self.hide_doors: bool = False
        self.hide_triggers: bool = False
        self.hide_encounters: bool = False
        self.hide_waypoints: bool = False
        self.hide_sounds: bool = False
        self.hide_stores: bool = False
        self.hide_cameras: bool = False
        self.hide_sound_boundaries: bool = True
        self.hide_trigger_boundaries: bool = True
        self.hide_encounter_boundaries: bool = True
        self.backface_culling: bool = True
        self.use_lightmap: bool = True
        self.show_cursor: bool = True
        module_id_part = "" if module is None else f" from module '{module.root()}'"
        RobustLogger().debug(f"Completed pre-initialize Scene{module_id_part}")

    def set_lyt(self, lyt: LYT):
        self.layout = lyt

    def set_installation(
        self,
        installation: Installation,
    ):
        def load_2da(name: str) -> TwoDA:
            resource: ResourceResult | None = installation.resource(name, ResourceType.TwoDA, SEARCH_ORDER_2DA)
            if resource is None:
                RobustLogger().warning(f"Could not load {name}.2da, this means its models will not be rendered")
                return TwoDA()
            return read_2da(resource.data)

        self.table_doors = load_2da("genericdoors")
        self.table_placeables = load_2da("placeables")
        self.table_creatures = load_2da("appearance")
        self.table_heads = load_2da("heads")
        self.table_baseitems = load_2da("baseitems")

    def get_creature_render_object(  # noqa: C901
        self,
        instance: GITCreature,
        utc: UTC | None = None,
    ) -> RenderObject:
        assert self.installation is not None
        try:
            if utc is None:
                utc = self._resource_from_gitinstance(instance, self.module.creature)
            if utc is None:
                RobustLogger().warning(f"Could not get UTC for GITCreature instance '{instance.identifier()}', not found in mod/override.")
                return RenderObject("unknown", data=instance)

            head_obj: RenderObject | None = None
            mask_hook = None

            body_model, body_texture = creature.get_body_model(
                utc,
                self.installation,
                appearance=self.table_creatures,
                baseitems=self.table_baseitems,
            )
            if not body_model or not body_model.strip():
                raise ValueError("creature.get_body_model failed to return a valid body_model resref str.")  # noqa: TRY301
            head_model, head_texture = creature.get_head_model(
                utc,
                self.installation,
                appearance=self.table_creatures,
                heads=self.table_heads,
            )
            rhand_model, lhand_model = creature.get_weapon_models(
                utc,
                self.installation,
                appearance=self.table_creatures,
                baseitems=self.table_baseitems,
            )
            mask_model = creature.get_mask_model(
                utc,
                self.installation,
            )

            obj = RenderObject(body_model, data=instance, override_texture=body_texture)

            head_hook: Node | None = self.model(body_model).find("headhook")
            if head_model and head_hook:
                head_obj = RenderObject(head_model, override_texture=head_texture)
                head_obj.set_transform(head_hook.global_transform())
                obj.children.append(head_obj)

            rhand_hook: Node | None = self.model(body_model).find("rhand")
            if rhand_model and rhand_hook:
                rhand_obj = RenderObject(rhand_model)
                rhand_obj.set_transform(rhand_hook.global_transform())
                obj.children.append(rhand_obj)
            lhand_hook: Node | None = self.model(body_model).find("lhand")
            if lhand_model and lhand_hook:
                lhand_obj = RenderObject(lhand_model)
                lhand_obj.set_transform(lhand_hook.global_transform())
                obj.children.append(lhand_obj)
            if head_hook is None:
                mask_hook: Node | None = self.model(body_model).find("gogglehook")
            elif head_model:
                mask_hook = self.model(head_model).find("gogglehook")
            if mask_model and mask_hook:
                mask_obj = RenderObject(mask_model)
                mask_obj.set_transform(mask_hook.global_transform())
                if head_hook is None:
                    obj.children.append(mask_obj)
                elif head_obj is not None:
                    head_obj.children.append(mask_obj)

        except Exception:  # noqa: BLE001
            RobustLogger().exception("Exception occurred getting the creature render object.")
            # If failed to load creature models, use the unknown model instead
            obj = RenderObject("unknown", data=instance)

        return obj

    @property
    def module(self) -> Module:
        if not self._module:
            raise RuntimeError("Module must be defined before a Scene can be rendered.")
        return self._module

    @module.setter
    def module(self, value: Module):
        self._module = value

    def _get_git(self) -> GIT:
        module_resource_git: ModuleResource[GIT] | None = self.module.git()
        result: GIT | None = self._resource_from_module(module_resource_git, "' is missing a GIT.")
        if result is None:
            RobustLogger().warning(f"Module '{self.module.root()}' is missing a GIT.")
            return GIT()
        return result

    def _get_lyt(self) -> LYT:
        layout_module_resource: ModuleResource[LYT] | None = self.module.layout()
        result: LYT | None = self._resource_from_module(layout_module_resource, "' is missing a LYT.")
        if result is None:
            RobustLogger().warning(f"Module '{self.module.root()}' is missing a LYT.")
            return LYT()
        return result

    def _get_ifo(self) -> IFO:
        info_module_resource: ModuleResource[IFO] | None = self.module.info()
        result: IFO | None = self._resource_from_module(info_module_resource, "' is missing an IFO.")
        if result is None:
            RobustLogger().warning(f"Module '{self.module.root()}' is missing an IFO.")
            return IFO()
        return result

    def _resource_from_module(
        self,
        module_res: ModuleResource[T] | None,
        errpart: str,
    ) -> T | None:
        if module_res is None:
            RobustLogger().error(f"Cannot render a frame in Scene when this module '{self.module.root()}{errpart}")
            return None
        resource: T | None = module_res.resource()
        if resource is None:
            RobustLogger().error(f"No locations found for '{module_res.identifier()}', needed to render a Scene for module '{self.module.root()}'")
            return None
        return resource

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

    def build_cache(  # noqa: C901, PLR0912, PLR0915
        self,
        *,
        clear_cache: bool = False,
    ):
        if self._module is None:
            return

        if clear_cache:
            self.objects.clear()

        if self.git is None:
            self.git = self._get_git()

        if self.layout is None:
            self.layout = self._get_lyt()

        for identifier in self.clear_cache_buffer:
            for git_creature in self.git.creatures.copy():
                if identifier.resname == git_creature.resref and identifier.restype is ResourceType.UTC:
                    del self.objects[git_creature]
            for placeable in self.git.placeables.copy():
                if identifier.resname == placeable.resref and identifier.restype is ResourceType.UTP:
                    del self.objects[placeable]
            for door in self.git.doors.copy():
                if door.resref == identifier.resname and identifier.restype is ResourceType.UTD:
                    del self.objects[door]
            if identifier.restype in {ResourceType.TPC, ResourceType.TGA}:
                del self.textures[identifier.resname]
            if identifier.restype in {ResourceType.MDL, ResourceType.MDX}:
                del self.models[identifier.resname]
            if identifier.restype is ResourceType.GIT:
                for instance in self.git.instances():
                    del self.objects[instance]
                self.git = self._get_git()
            if identifier.restype is ResourceType.LYT:
                for room in self.layout.rooms:
                    del self.objects[room]
                self.layout = self._get_lyt()
        self.clear_cache_buffer = []

        for room in self.layout.rooms:
            if room not in self.objects:
                position = vec3(room.position.x, room.position.y, room.position.z)
                self.objects[room] = RenderObject(
                    room.model,
                    position,
                    data=room,
                )

        for door in self.git.doors:
            if door not in self.objects:
                model_name = "unknown"  # If failed to load door models, use an empty model instead
                utd = None
                try:
                    utd: UTD | None = self._resource_from_gitinstance(door, self._module.door)
                    if utd is not None:
                        model_name: str = self.table_doors.get_row(utd.appearance_id).get_string("modelname")
                except Exception:  # noqa: BLE001
                    RobustLogger().exception(f"Could not get the model name from the UTD '{door.resref}.utd' and/or the appearance.2da")
                if utd is None:
                    utd = UTD()

                self.objects[door] = RenderObject(
                    model_name,
                    vec3(),
                    vec3(),
                    data=door,
                )

            self.objects[door].set_position(door.position.x, door.position.y, door.position.z)
            self.objects[door].set_rotation(0, 0, door.bearing)

        for placeable in self.git.placeables:
            if placeable not in self.objects:
                model_name = "unknown"  # If failed to load a placeable models, use an empty model instead
                utp = None
                try:
                    utp: UTP | None = self._resource_from_gitinstance(placeable, self._module.placeable)
                    if utp is not None:
                        model_name: str = self.table_placeables.get_row(utp.appearance_id).get_string("modelname")
                except Exception:  # noqa: BLE001
                    RobustLogger().exception(f"Could not get the model name from the UTP '{placeable.resref}.utp' and/or the appearance.2da")
                if utp is None:
                    utp = UTP()

                self.objects[placeable] = RenderObject(
                    model_name,
                    vec3(),
                    vec3(),
                    data=placeable,
                )

            self.objects[placeable].set_position(placeable.position.x, placeable.position.y, placeable.position.z)
            self.objects[placeable].set_rotation(0, 0, placeable.bearing)

        for git_creature in self.git.creatures:
            if git_creature in self.objects:
                continue
            self.objects[git_creature] = self.get_creature_render_object(git_creature)

            self.objects[git_creature].set_position(git_creature.position.x, git_creature.position.y, git_creature.position.z)
            self.objects[git_creature].set_rotation(0, 0, git_creature.bearing)

        for waypoint in self.git.waypoints:
            if waypoint in self.objects:
                continue
            obj = RenderObject(
                "waypoint",
                vec3(),
                vec3(),
                data=waypoint,
            )
            self.objects[waypoint] = obj

            self.objects[waypoint].set_position(waypoint.position.x, waypoint.position.y, waypoint.position.z)
            self.objects[waypoint].set_rotation(0, 0, waypoint.bearing)

        for store in self.git.stores:
            if store not in self.objects:
                obj = RenderObject(
                    "store",
                    vec3(),
                    vec3(),
                    data=store,
                )
                self.objects[store] = obj

            self.objects[store].set_position(store.position.x, store.position.y, store.position.z)
            self.objects[store].set_rotation(0, 0, store.bearing)

        for sound in self.git.sounds:
            if sound in self.objects:
                continue
            uts = None
            try:
                uts: UTS | None = self._resource_from_gitinstance(sound, self._module.sound)
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Could not get the sound resource '{sound.resref}.uts' and/or the appearance.2da")
            if uts is None:
                uts = UTS()

            obj = RenderObject(
                "sound",
                vec3(),
                vec3(),
                data=sound,
                gen_boundary=lambda uts=uts: Boundary.from_circle(self, uts.max_distance),
            )
            self.objects[sound] = obj

            self.objects[sound].set_position(sound.position.x, sound.position.y, sound.position.z)
            self.objects[sound].set_rotation(0, 0, 0)

        for encounter in self.git.encounters:
            if encounter in self.objects:
                continue
            obj = RenderObject(
                "encounter",
                vec3(),
                vec3(),
                data=encounter,
                gen_boundary=lambda encounter=encounter: Boundary(self, encounter.geometry.points),
            )
            self.objects[encounter] = obj

            self.objects[encounter].set_position(
                encounter.position.x,
                encounter.position.y,
                encounter.position.z,
            )
            self.objects[encounter].set_rotation(0, 0, 0)

        for trigger in self.git.triggers:
            if trigger not in self.objects:
                obj = RenderObject(
                    "trigger",
                    vec3(),
                    vec3(),
                    data=trigger,
                    gen_boundary=lambda trigger=trigger: Boundary(self, trigger.geometry.points),
                )
                self.objects[trigger] = obj

            self.objects[trigger].set_position(
                trigger.position.x,
                trigger.position.y,
                trigger.position.z,
            )
            self.objects[trigger].set_rotation(0, 0, 0)

        for camera in self.git.cameras:
            if camera not in self.objects:
                obj = RenderObject(
                    "camera",
                    vec3(),
                    vec3(),
                    data=camera,
                )
                self.objects[camera] = obj

            self.objects[camera].set_position(camera.position.x, camera.position.y, camera.position.z + camera.height)
            euler: vec3 = glm.eulerAngles(quat(camera.orientation.w, camera.orientation.x, camera.orientation.y, camera.orientation.z))
            self.objects[camera].set_rotation(
                euler.y,
                euler.z - math.pi / 2 + math.radians(camera.pitch),
                -euler.x + math.pi / 2,
            )

        # Detect if GIT objects still exist; if they do not then remove them from the render list
        for obj in copy(self.objects):
            self._del_git_objects(obj, self.git, self.objects)

    @staticmethod
    def _del_git_objects(
        obj: GITInstance | LYTRoom,
        git: GIT,
        objects: dict[GITInstance | LYTRoom, RenderObject],
    ):
        if isinstance(obj, GITCreature) and obj not in git.creatures:
            del objects[obj]
        if isinstance(obj, GITPlaceable) and obj not in git.placeables:
            del objects[obj]
        if isinstance(obj, GITDoor) and obj not in git.doors:
            del objects[obj]
        if isinstance(obj, GITTrigger) and obj not in git.triggers:
            del objects[obj]
        if isinstance(obj, GITStore) and obj not in git.stores:
            del objects[obj]
        if isinstance(obj, GITCamera) and obj not in git.cameras:
            del objects[obj]
        if isinstance(obj, GITWaypoint) and obj not in git.waypoints:
            del objects[obj]
        if isinstance(obj, GITEncounter) and obj not in git.encounters:
            del objects[obj]
        if isinstance(obj, GITSound) and obj not in git.sounds:
            del objects[obj]

    def render(self):
        self.build_cache()

        self._prepare_gl_and_shader()
        self.shader.set_bool("enableLightmap", self.use_lightmap)
        group1: list[RenderObject] = [obj for obj in self.objects.values() if obj.model not in self.SPECIAL_MODELS]
        for obj in group1:
            self._render_object(self.shader, obj, mat4())

        # Draw all instance types that lack a proper model
        glEnable(GL_BLEND)
        self.plain_shader.use()
        self.plain_shader.set_matrix4("view", self.camera.view())
        self.plain_shader.set_matrix4("projection", self.camera.projection())
        self.plain_shader.set_vector4("color", vec4(0.0, 0.0, 1.0, 0.4))
        group2: list[RenderObject] = [obj for obj in self.objects.values() if obj.model in self.SPECIAL_MODELS]
        for obj in group2:
            self._render_object(self.plain_shader, obj, mat4())

        # Draw bounding box for selected objects
        self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
        for obj in self.selection:
            obj.cube(self).draw(self.plain_shader, obj.transform())

        # Draw boundary for selected objects
        glDisable(GL_CULL_FACE)
        self.plain_shader.set_vector4("color", vec4(0.0, 1.0, 0.0, 0.8))
        for obj in self.selection:
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        # Draw non-selected boundaries
        for obj in (obj for obj in self.objects.values() if obj.model == "sound" and not self.hide_sound_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in (obj for obj in self.objects.values() if obj.model == "encounter" and not self.hide_encounter_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())
        for obj in (obj for obj in self.objects.values() if obj.model == "trigger" and not self.hide_trigger_boundaries):
            obj.boundary(self).draw(self.plain_shader, obj.transform())

        if self.show_cursor:
            self.plain_shader.set_vector4("color", vec4(1.0, 0.0, 0.0, 0.4))
            self._render_object(self.plain_shader, self.cursor, mat4())

    def should_hide_obj(
        self,
        obj: RenderObject,
    ) -> bool:
        result = False
        if isinstance(obj.data, GITCreature) and self.hide_creatures:
            result = True
        elif isinstance(obj.data, GITPlaceable) and self.hide_placeables:
            result = True
        elif isinstance(obj.data, GITDoor) and self.hide_doors:
            result = True
        elif isinstance(obj.data, GITTrigger) and self.hide_triggers:
            result = True
        elif isinstance(obj.data, GITEncounter) and self.hide_encounters:
            result = True
        elif isinstance(obj.data, GITWaypoint) and self.hide_waypoints:
            result = True
        elif isinstance(obj.data, GITSound) and self.hide_sounds:
            result = True
        elif isinstance(obj.data, GITStore) and self.hide_sounds:
            result = True
        elif isinstance(obj.data, GITCamera) and self.hide_cameras:
            result = True
        return result

    def _render_object(
        self,
        shader: Shader,
        obj: RenderObject,
        transform: mat4,
    ):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        transform = transform * obj.transform()
        model.draw(shader, transform, override_texture=obj.override_texture)

        for child in obj.children:
            self._render_object(shader, child, transform)

    def picker_render(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)  # Sets the clear color for the OpenGL color buffer to pure white
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clears the color and depth buffers. Clean slate for rendering.  # pyright: ignore[reportOperatorIssue]

        if self.backface_culling:
            glEnable(GL_CULL_FACE)  # Enables backface culling to improve rendering performance by ignoring back faces of polygons.
        else:
            glDisable(GL_CULL_FACE)  # Disables backface culling.

        self.picker_shader.use()  # Activates the shader program for rendering.
        self.picker_shader.set_matrix4("view", self.camera.view())  # Sets the view matrix for the shader.
        self.picker_shader.set_matrix4("projection", self.camera.projection())  # Sets the projection matrix for the shader.
        instances: list[RenderObject] = list(self.objects.values())
        for obj in instances:
            int_rgb: int = instances.index(obj)  # Gets the index of the object in the list and converts it to an integer.
            r: int = int_rgb & 0xFF
            g: int = (int_rgb >> 8) & 0xFF
            b: int = (int_rgb >> 16) & 0xFF
            color = vec3(r / 0xFF, g / 0xFF, b / 0xFF)
            self.picker_shader.set_vector3("colorId", color)

            self._picker_render_object(obj, mat4())

    def _picker_render_object(self, obj: RenderObject, transform: mat4):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        model.draw(self.picker_shader, transform * obj.transform())
        for child in obj.children:
            self._picker_render_object(child, obj.transform())

    def pick(
        self,
        x: float,
        y: float,
    ) -> RenderObject | None:
        self.picker_render()
        pixel: int = glReadPixels(x, y, 1, 1, GL_BGRA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8  # type: ignore[]
        instances: list[RenderObject] = list(self.objects.values())
        return instances[pixel] if pixel != 0xFFFFFF else None  # noqa: PLR2004

    def select(
        self,
        target: RenderObject | GITInstance,
        *,
        clear_existing: bool = True,
    ):
        if clear_existing:
            self.selection.clear()

        self.build_cache()
        actual_target: RenderObject
        if isinstance(target, GITInstance):
            for obj in self.objects.values():
                if obj.data is not target:
                    continue
                actual_target = obj
                break
        else:
            actual_target = target

        self.selection.append(actual_target)

    def screen_to_world(
        self,
        x: int,
        y: int,
    ) -> Vector3:
        self._prepare_gl_and_shader()
        group1: list[RenderObject] = [obj for obj in self.objects.values() if isinstance(obj.data, LYTRoom)]
        for obj in group1:
            self._render_object(self.shader, obj, mat4())

        zpos = glReadPixels(
            x,
            self.camera.height - y,
            1,
            1,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
        )[0][0]  # type: ignore[]
        cursor: vec3 = glm.unProject(
            vec3(x, self.camera.height - y, zpos),
            self.camera.view(),
            self.camera.projection(),
            vec4(0, 0, self.camera.width, self.camera.height),
        )
        return Vector3(cursor.x, cursor.y, cursor.z)

    def _prepare_gl_and_shader(self):
        glClearColor(0.5, 0.5, 1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # type: ignore[]
        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())

    def texture(
        self,
        name: str,
        *,
        lightmap: bool = False,
    ) -> Texture:
        if name in self.textures:
            return self.textures[name]
        type_name: Literal["lightmap", "texture"] = "lightmap" if lightmap else "texture"
        tpc: TPC | None = None
        try:
            # Check the textures linked to the module first
            if self._module is not None:
                RobustLogger().debug(f"Locating {type_name} '{name}' in module '{self.module.root()}'")
                module_tex: ModuleResource[TPC] | None = self.module.texture(name)
                if module_tex is not None:
                    RobustLogger().debug(f"Loading {type_name} '{name}' from module '{self.module.root()}'")
                    tpc = module_tex.resource()

            # Otherwise just search through all relevant game files
            if tpc is None and self.installation is not None:
                RobustLogger().debug(f"Locating and loading {type_name} '{name}' from override/bifs/texturepacks...")
                tpc = self.installation.texture(name, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN])
            if tpc is None:
                RobustLogger().warning(f"MISSING {type_name.upper()}: '{name}'")
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Could not load {type_name} '{name}'.")

        blank: Texture = Texture.from_color(0, 0, 0) if lightmap else Texture.from_color(255, 0, 255)
        self.textures[name] = blank if tpc is None else Texture.from_tpc(tpc)
        return self.textures[name]

    def model(  # noqa: C901, PLR0912
        self,
        name: str,
    ) -> Model:
        mdl_data: bytes = EMPTY_MDL_DATA
        mdx_data: bytes = EMPTY_MDX_DATA

        if name not in self.models:
            if name == "waypoint":
                mdl_data = WAYPOINT_MDL_DATA
                mdx_data = WAYPOINT_MDX_DATA
            elif name == "sound":
                mdl_data = SOUND_MDL_DATA
                mdx_data = SOUND_MDX_DATA
            elif name == "store":
                mdl_data = STORE_MDL_DATA
                mdx_data = STORE_MDX_DATA
            elif name == "entry":
                mdl_data = ENTRY_MDL_DATA
                mdx_data = ENTRY_MDX_DATA
            elif name == "encounter":
                mdl_data = ENCOUNTER_MDL_DATA
                mdx_data = ENCOUNTER_MDX_DATA
            elif name == "trigger":
                mdl_data = TRIGGER_MDL_DATA
                mdx_data = TRIGGER_MDX_DATA
            elif name == "camera":
                mdl_data = CAMERA_MDL_DATA
                mdx_data = CAMERA_MDX_DATA
            elif name == "empty":
                mdl_data = EMPTY_MDL_DATA
                mdx_data = EMPTY_MDX_DATA
            elif name == "cursor":
                mdl_data = CURSOR_MDL_DATA
                mdx_data = CURSOR_MDX_DATA
            elif name == "unknown":
                mdl_data = UNKNOWN_MDL_DATA
                mdx_data = UNKNOWN_MDX_DATA
            elif self.installation is not None:
                capsules: list[ModulePieceResource] = [] if self._module is None else self.module.capsules()
                mdl_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=capsules)
                mdx_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=capsules)
                if mdl_search is not None and mdx_search is not None:
                    mdl_data = mdl_search.data
                    mdx_data = mdx_search.data

            try:
                mdl_reader: BinaryReader = BinaryReader.from_bytes(mdl_data, 12)
                mdx_reader: BinaryReader = BinaryReader.from_bytes(mdx_data)
                model: Model = gl_load_stitched_model(self, mdl_reader, mdx_reader)
            except Exception:  # noqa: BLE001
                RobustLogger().warning(f"Could not load model '{name}'.")
                model = gl_load_stitched_model(
                    self,
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )

            self.models[name] = model
        return self.models[name]

    def jump_to_entry_location(self):
        if self._module is None:
            self.camera.x = 0
            self.camera.y = 0
            self.camera.z = 0
        else:
            point: Vector3 = self.module.info().resource().entry_position
            self.camera.x = point.x
            self.camera.y = point.y
            self.camera.z = point.z + 1.8