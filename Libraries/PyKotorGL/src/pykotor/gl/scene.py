from __future__ import annotations

import math

from copy import copy
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

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
    GL_TEXTURE_2D,
    glBlendFunc,
    glClear,
    glClearColor,
    glCullFace,
    glDisable,
    glEnable,
)
from OpenGL.raw.GL.VERSION.GL_1_2 import GL_BGRA, GL_UNSIGNED_INT_8_8_8_8

from pykotor.common.geometry import Vector3, Vector4, euler_from_quaternion
from pykotor.common.misc import CaseInsensitiveDict
from pykotor.common.stream import BinaryReader
from pykotor.extract.installation import SearchLocation
from pykotor.gl.models.mdl import Boundary, Cube, Empty
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
from pykotor.gl.shader import (
    KOTOR_FSHADER,
    KOTOR_VSHADER,
    PICKER_FSHADER,
    PICKER_VSHADER,
    PLAIN_FSHADER,
    PLAIN_VSHADER,
    Shader,
    Texture,
)
from pykotor.resource.formats.lyt import LYTRoom
from pykotor.resource.formats.tpc import TPC
from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.generics.git import (
    GITCamera,
    GITCreature,
    GITDoor,
    GITEncounter,
    GITInstance,
    GITPlaceable,
    GITSound,
    GITStore,
    GITTrigger,
    GITWaypoint,
)
from pykotor.resource.generics.uts import UTS
from pykotor.resource.type import ResourceType
from pykotor.tools import creature
from utility.error_handling import format_exception_with_variables

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Literal

    from pykotor.common.module import Module
    from pykotor.extract.capsule import Capsule
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.gl.models.mdl import Model
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.generics.git import GIT
    from pykotor.resource.generics.utc import UTC
    from pykotor.resource.generics.utd import UTD
    from pykotor.resource.generics.utp import UTP

SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER: list[SearchLocation] = [SearchLocation.CUSTOM_MODULES, SearchLocation.OVERRIDE, SearchLocation.CHITIN]


class Scene:
    SPECIAL_MODELS: ClassVar[list[str]] = ["waypoint", "store", "sound", "camera", "trigger", "encounter", "unknown"]

    def __init__(self, *, installation: Installation | None = None, module: Module | None = None):
        """Initializes the renderer.

        Args:
        ----
            installation: Installation: The installation to load resources from
            module: Module: The active module

        Processing Logic:
        ----------------
            - Initializes OpenGL settings
            - Sets up default textures, shaders, camera
            - Loads 2DA tables from installation
            - Hides certain object types by default
            - Sets other renderer options.
        """
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_BACK)

        self.installation: Installation | None = installation
        self.textures: CaseInsensitiveDict[Texture] = CaseInsensitiveDict()
        self.models: CaseInsensitiveDict[Model] = CaseInsensitiveDict()
        self.objects: dict[Any, RenderObject] = {}
        self.selection: list[RenderObject] = []
        self.module: Module | None = module
        self.camera: Camera = Camera()
        self.cursor: RenderObject = RenderObject("cursor")

        self.textures["NULL"] = Texture.from_color()

        self.git: GIT | None = None
        self.layout: LYT | None = None
        self.clearCacheBuffer: list[ResourceIdentifier] = []

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
            self.setInstallation(installation)

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

    def setInstallation(self, installation: Installation):
        self.table_doors = read_2da(installation.resource("genericdoors", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_placeables = read_2da(installation.resource("placeables", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_creatures = read_2da(installation.resource("appearance", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_heads = read_2da(installation.resource("heads", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)
        self.table_baseitems = read_2da(installation.resource("baseitems", ResourceType.TwoDA, SEARCH_ORDER_2DA).data)

    def getCreatureRenderObject(self, instance: GITCreature, utc: UTC | None = None) -> RenderObject:
        """Generates a render object for a creature instance.

        Args:
        ----
            instance: {Creature instance}: Creature instance to generate render object for
            utc: {Optional timestamp}: Timestamp to use for generation or current time if None

        Returns:
        -------
            RenderObject: Render object representing the creature

        Processing Logic:
        ----------------
            - Gets body, head, weapon and mask models/textures based on creature appearance
            - Creates base render object and attaches head, hands and mask sub-objects
            - Catches exceptions and returns default "unknown" render object if model loading fails.
        """
        try:
            if utc is None:
                utc = self.module.creature(str(instance.resref)).resource()

            head_obj: RenderObject | None = None
            mask_hook = None

            body_model, body_texture = creature.get_body_model(
                utc,
                self.installation,
                appearance=self.table_creatures,
                baseitems=self.table_baseitems,
            )
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

            head_hook = self.model(body_model).find("headhook")
            if head_model and head_hook:
                head_obj = RenderObject(head_model, override_texture=head_texture)
                head_obj.set_transform(head_hook.global_transform())
                obj.children.append(head_obj)

            rhand_hook = self.model(body_model).find("rhand")
            if rhand_model and rhand_hook:
                self._transform_hand(rhand_model, rhand_hook, obj)
            lhand_hook = self.model(body_model).find("lhand")
            if lhand_model and lhand_hook:
                self._transform_hand(lhand_model, lhand_hook, obj)
            if head_hook is None:
                mask_hook = self.model(body_model).find("gogglehook")
            elif head_model:
                mask_hook = self.model(head_model).find("gogglehook")
            if mask_model and mask_hook:
                mask_obj = RenderObject(mask_model)
                mask_obj.set_transform(mask_hook.global_transform())
                if head_hook is None:
                    obj.children.append(mask_obj)
                elif head_obj is not None:
                    head_obj.children.append(mask_obj)

        except Exception as e:
            print(format_exception_with_variables(e))
            # If failed to load creature models, use the unknown model instead
            obj = RenderObject("unknown", data=instance)

        return obj

    def _transform_hand(self, arg0, arg1, obj):
        rhand_obj = RenderObject(arg0)
        rhand_obj.set_transform(arg1.global_transform())
        obj.children.append(rhand_obj)

    def buildCache(self, clear_cache: bool = False):
        """Builds and caches game objects from the module.

        Args:
        ----
            clear_cache (bool): Whether to clear the existing cache

        Processing Logic:
        ----------------
            - Clear existing cache if clear_cache is True
            - Delete objects matching identifiers in clearCacheBuffer
            - Retrieve/update game objects from module
            - Add/update objects in cache..
        """
        if self.module is None:
            return

        if clear_cache:
            self.objects = {}

        for identifier in self.clearCacheBuffer:
            for git_creature in copy(self.git.creatures):
                if identifier.resname == git_creature.resref and identifier.restype == ResourceType.UTC:
                    del self.objects[git_creature]
            for placeable in copy(self.git.placeables):
                if identifier.resname == placeable.resref and identifier.restype == ResourceType.UTP:
                    del self.objects[placeable]
            for door in copy(self.git.doors):
                if door.resref == identifier.resname and identifier.restype == ResourceType.UTD:
                    del self.objects[door]
            if identifier.restype in {ResourceType.TPC, ResourceType.TGA}:
                del self.textures[identifier.resname]
            if identifier.restype in {ResourceType.MDL, ResourceType.MDX}:
                del self.models[identifier.resname]
            if identifier.restype == ResourceType.GIT:
                for instance in self.git.instances():
                    del self.objects[instance]
                self.git = self.module.git().resource()
            if identifier.restype == ResourceType.LYT:
                for room in self.layout.rooms:
                    del self.objects[room]
                self.layout = self.module.layout().resource()
        self.clearCacheBuffer = []

        if self.git is None:
            self.git = self.module.git().resource()

        if self.layout is None:
            self.layout = self.module.layout().resource()

        for room in self.layout.rooms:
            if room not in self.objects:
                position = Vector3(room.position.x, room.position.y, room.position.z)
                self.objects[room] = RenderObject(room.model, position, data=room)

        for door in self.git.doors:
            if door not in self.objects:
                try:
                    utd: UTD | None = self.module.door(str(door.resref)).resource()
                    model_name = self.table_doors.get_row(utd.appearance_id).get_string("modelname")
                except Exception as e:
                    print(format_exception_with_variables(e))
                    # If failed to load creature models, use an empty model instead
                    model_name = "unknown"

                self.objects[door] = RenderObject(model_name, Vector3.from_null(), Vector3.from_null(), data=door)

            self.objects[door].set_position(door.position.x, door.position.y, door.position.z)
            self.objects[door].set_rotation(0, 0, door.bearing)

        for placeable in self.git.placeables:
            if placeable not in self.objects:
                try:
                    utp: UTP | None = self.module.placeable(str(placeable.resref)).resource()
                    model_name: str = self.table_placeables.get_row(utp.appearance_id).get_string("modelname")
                except Exception as e:
                    print(format_exception_with_variables(e))
                    # If failed to load creature models, use an empty model instead
                    model_name = "unknown"

                self.objects[placeable] = RenderObject(model_name, Vector3.from_null(), Vector3.from_null(), data=placeable)

            self.objects[placeable].set_position(placeable.position.x, placeable.position.y, placeable.position.z)
            self.objects[placeable].set_rotation(0, 0, placeable.bearing)

        for git_creature in self.git.creatures:
            if git_creature not in self.objects:
                self.objects[git_creature] = self.getCreatureRenderObject(git_creature)

            self.objects[git_creature].set_position(git_creature.position.x, git_creature.position.y, git_creature.position.z)
            self.objects[git_creature].set_rotation(0, 0, git_creature.bearing)

        for waypoint in self.git.waypoints:
            if waypoint not in self.objects:
                obj = RenderObject("waypoint", Vector3.from_null(), Vector3.from_null(), data=waypoint)
                self.objects[waypoint] = obj

            self.objects[waypoint].set_position(waypoint.position.x, waypoint.position.y, waypoint.position.z)
            self.objects[waypoint].set_rotation(0, 0, waypoint.bearing)

        for store in self.git.stores:
            if store not in self.objects:
                obj = RenderObject("store", Vector3.from_null(), Vector3.from_null(), data=store)
                self.objects[store] = obj

            self.objects[store].set_position(store.position.x, store.position.y, store.position.z)
            self.objects[store].set_rotation(0, 0, store.bearing)

        for sound in self.git.sounds:
            if sound not in self.objects:
                try:
                    uts: UTS = self.module.sound(str(sound.resref)).resource() or UTS()
                except Exception as e:
                    print(format_exception_with_variables(e))
                    uts = UTS()

                obj = RenderObject(
                    "sound",
                    Vector3.from_null(),
                    Vector3.from_null(),
                    data=sound,
                    gen_boundary=lambda uts=uts: Boundary.from_circle(self, uts.max_distance),
                )
                self.objects[sound] = obj

            self.objects[sound].set_position(sound.position.x, sound.position.y, sound.position.z)
            self.objects[sound].set_rotation(0, 0, 0)

        for encounter in self.git.encounters:
            if encounter not in self.objects:
                obj = RenderObject(
                    "encounter",
                    Vector3.from_null(),
                    Vector3.from_null(),
                    data=encounter,
                    gen_boundary=lambda encounter=encounter: Boundary(self, encounter.geometry.points),
                )
                self.objects[encounter] = obj

            self.objects[encounter].set_position(encounter.position.x, encounter.position.y, encounter.position.z)
            self.objects[encounter].set_rotation(0, 0, 0)

        for trigger in self.git.triggers:
            if trigger not in self.objects:
                obj = RenderObject(
                    "trigger",
                    Vector3.from_null(),
                    Vector3.from_null(),
                    data=trigger,
                    gen_boundary=lambda trigger=trigger: Boundary(self, trigger.geometry.points),
                )
                self.objects[trigger] = obj

            self.objects[trigger].set_position(trigger.position.x, trigger.position.y, trigger.position.z)
            self.objects[trigger].set_rotation(0, 0, 0)

        for camera in self.git.cameras:
            if camera not in self.objects:
                obj = RenderObject("camera", Vector3.from_null(), Vector3.from_null(), data=camera)
                self.objects[camera] = obj

            self.objects[camera].set_position(camera.position.x, camera.position.y, camera.position.z + camera.height)
            euler: Vector3 = Vector3(*euler_from_quaternion(camera.orientation.w, camera.orientation.x, camera.orientation.y, camera.orientation.z))
            self.objects[camera].set_rotation(
                euler.y,
                euler.z - math.pi / 2 + math.radians(camera.pitch),
                -euler.x + math.pi / 2,
            )

        # Detect if GIT still exists; if they do not then remove them from the render list
        for obj in copy(self.objects):
            self._del_git_objects(obj)

    def _del_git_objects(self, obj):
        if isinstance(obj, GITCreature) and obj not in self.git.creatures:
            del self.objects[obj]
        if isinstance(obj, GITPlaceable) and obj not in self.git.placeables:
            del self.objects[obj]
        if isinstance(obj, GITDoor) and obj not in self.git.doors:
            del self.objects[obj]
        if isinstance(obj, GITTrigger) and obj not in self.git.triggers:
            del self.objects[obj]
        if isinstance(obj, GITStore) and obj not in self.git.stores:
            del self.objects[obj]
        if isinstance(obj, GITCamera) and obj not in self.git.cameras:
            del self.objects[obj]
        if isinstance(obj, GITWaypoint) and obj not in self.git.waypoints:
            del self.objects[obj]
        if isinstance(obj, GITEncounter) and obj not in self.git.encounters:
            del self.objects[obj]
        if isinstance(obj, GITSound) and obj not in self.git.sounds:
            del self.objects[obj]

    def render(self):
        """Renders the scene.

        Args:
        ----
            self: Renderer object containing scene data

        Returns:
        -------
            None: Does not return anything, renders directly to the framebuffer

        Processing Logic:
        ----------------
            - Clear color and depth buffers
            - Enable/disable backface culling
            - Set view and projection matrices
            - Render opaque geometry with lighting
            - Render instanced objects without lighting
            - Render selection bounding boxes
            - Render selection boundaries
            - Render non-selected boundaries
            - Render cursor if shown.
        """
        self.buildCache()

        self._prepareGL(0.5, 1)
        glDisable(GL_BLEND)
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view())
        self.shader.set_matrix4("projection", self.camera.projection())
        self.shader.set_bool("enableLightmap", self.use_lightmap)
        group1: list[RenderObject] = [obj for obj in self.objects.values() if obj.model not in self.SPECIAL_MODELS]
        for obj in group1:
            self._render_object(self.shader, obj, np.eye(4))

        # Draw all instance types that lack a proper model
        glEnable(GL_BLEND)
        self.plain_shader.use()
        self.plain_shader.set_matrix4("view", self.camera.view())
        self.plain_shader.set_matrix4("projection", self.camera.projection())
        self.plain_shader.set_vector4("color", Vector4(0.0, 0.0, 1.0, 0.4))
        group2: list[RenderObject] = [obj for obj in self.objects.values() if obj.model in self.SPECIAL_MODELS]
        for obj in group2:
            self._render_object(self.plain_shader, obj, np.eye(4))

        # Draw bounding box for selected objects
        self.plain_shader.set_vector4("color", Vector4(1.0, 0.0, 0.0, 0.4))
        for obj in self.selection:
            obj.cube(self).draw(self.plain_shader, obj.transform())

        # Draw boundary for selected objects
        glDisable(GL_CULL_FACE)
        self.plain_shader.set_vector4("color", Vector4(0.0, 1.0, 0.0, 0.8))
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
            self.plain_shader.set_vector4("color", Vector4(1.0, 0.0, 0.0, 0.4))
            self._render_object(self.plain_shader, self.cursor, np.eye(4))

    def should_hide_obj(self, obj: RenderObject) -> bool:
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

    def _render_object(self, shader: Shader, obj: RenderObject, transform):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        transform = transform * obj.transform()
        model.draw(shader, transform, override_texture=obj.override_texture)

        for child in obj.children:
            self._render_object(shader, child, transform)

    def picker_render(self):
        self._prepareGL(1.0, 1.0)
        self.picker_shader.use()
        self.picker_shader.set_matrix4("view", self.camera.view())
        self.picker_shader.set_matrix4("projection", self.camera.projection())
        instances = list(self.objects.values())
        for obj in instances:
            int_rgb: int = instances.index(obj)
            r: int = int_rgb & 0xFF
            g: int = (int_rgb >> 8) & 0xFF
            b: int = (int_rgb >> 16) & 0xFF
            color = Vector3(r / 0xFF, g / 0xFF, b / 0xFF)
            self.picker_shader.set_vector3("colorId", color)

            self._picker_render_object(obj, np.eye(4))

    def _picker_render_object(self, obj: RenderObject, transform):
        if self.should_hide_obj(obj):
            return

        model: Model = self.model(obj.model)
        model.draw(self.picker_shader, transform * obj.transform())
        for child in obj.children:
            self._picker_render_object(child, obj.transform())

    def pick(self, x: float, y: float) -> RenderObject:
        self.picker_render()
        pixel = glReadPixels(x, y, 1, 1, GL_BGRA, GL_UNSIGNED_INT_8_8_8_8)[0][0] >> 8  # type: ignore[]
        instances = list(self.objects.values())
        return instances[pixel] if pixel != 0xFFFFFF else None  # type: ignore[reportReturnType]  # noqa: PLR2004

    def select(self, target: RenderObject | GITInstance, clear_existing: bool = True):
        if clear_existing:
            self.selection.clear()

        self.buildCache()
        actual_target: RenderObject
        if isinstance(target, GITInstance):
            for obj in self.objects.values():
                if obj.data is target:
                    actual_target = obj
                    break
        else:
            actual_target = target

        self.selection.append(actual_target)

    def screenToWorld(self, x: int, y: int) -> Vector3:
        self._prepareGL(0.5, 1)
        glDisable(GL_BLEND)

        # Use the shader and set matrices
        self.shader.use()
        self.shader.set_matrix4("view", self.camera.view().tolist())  # Assuming set_matrix4 can take a list
        self.shader.set_matrix4("projection", self.camera.projection().tolist())

        # Render specific objects in the scene
        group1 = [obj for obj in self.objects.values() if isinstance(obj.data, LYTRoom)]
        for obj in group1:
            self._render_object(self.shader, obj, np.eye(4))  # Using np.eye(4) as the identity matrix

        # Read the depth from the pixel
        zpos = glReadPixels(x, self.camera.height - y, 1, 1, GL_DEPTH_BUFFER_BIT, GL_FLOAT)[0][0]  # type: ignore[reportIndexIssue]

        # Assuming the following functions/methods are correctly adapted to no longer use GLM:
        view_matrix = self.camera.view()
        projection_matrix = self.camera.projection()
        _viewport = np.array([0, 0, self.camera.width, self.camera.height])

        # Convert screen coordinates to normalized device coordinates (NDC)
        ndc_x = (2.0 * x) / self.camera.width - 1.0
        ndc_y = 1.0 - (2.0 * y) / self.camera.height
        ndc_z = 2.0 * zpos - 1.0
        ndc = np.array([ndc_x, ndc_y, ndc_z, 1.0])

        # Unproject NDC to world coordinates
        inv_vp = np.linalg.inv(np.dot(projection_matrix, view_matrix))
        world_coords = np.dot(inv_vp, ndc)
        world_coords /= world_coords[3]  # Homogenize

        # Convert numpy array to Vector3 and return
        return Vector3(world_coords[0], world_coords[1], world_coords[2])

    # TODO Rename this here and in `render`, `picker_render` and `screenToWorld`
    def _prepareGL(self, arg0, arg1):
        glClearColor(arg0, arg0, arg1, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.backface_culling:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)

    def texture(self, name: str) -> Texture:
        if name in self.textures:
            return self.textures[name]
        try:
            tpc: TPC | None = None
            # Check the textures linked to the module first
            if self.module is not None:
                print(f"Loading texture '{name}' from {self.module._root}")
                module_tex = self.module.texture(name)
                tpc = module_tex.resource() if module_tex is not None else None

            # Otherwise just search through all relevant game files
            if tpc is None and self.installation:
                print(f"Locating texture '{name}' from override/bifs...")
                tpc = self.installation.texture(name, [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN])
                print(f"Finished checking installation for texture '{name}'")
            if tpc is None:
                print(f"NOT FOUND ANYWHERE: Texture '{name}'")
        except Exception as e:  # noqa: BLE001
            print(format_exception_with_variables(e))
            # If an error occurs during the loading process, just use a blank image.
            tpc = TPC()

        self.textures[name] = Texture.from_color(0xFF, 0, 0xFF) if tpc is None else Texture.from_tpc(tpc)
        return self.textures[name]

    def model(self, name: str) -> Model:
        mdl_data = EMPTY_MDL_DATA
        mdx_data = EMPTY_MDX_DATA

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
                capsules: list[Capsule] = [] if self.module is None else self.module.capsules()
                mdl_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=capsules)
                mdx_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=capsules)
                if mdl_search is not None and mdx_search is not None:
                    mdl_data: bytes = mdl_search.data
                    mdx_data: bytes = mdx_search.data

            try:
                model = gl_load_stitched_model(self, BinaryReader.from_bytes(mdl_data, 12), BinaryReader.from_bytes(mdx_data))
            except Exception as e:
                print(format_exception_with_variables(e))
                model = gl_load_stitched_model(
                    self,
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )

            self.models[name] = model
        return self.models[name]

    def jump_to_entry_location(self):
        if self.module is None:
            self.camera.x = 0
            self.camera.y = 0
            self.camera.z = 0
        else:
            point: Vector3 = self.module.info().resource().entry_position
            self.camera.x = point.x
            self.camera.y = point.y
            self.camera.z = point.z + 1.8

class TransformHandler:
    def __init__(self):
        self._position = np.array([0, 0, 0])
        self._rotation = np.array([0, 0, 0])  # Euler angles (roll, pitch, yaw)

def create_translation_matrix(translation):
    """Create a 4x4 translation matrix."""
    matrix = np.eye(4)
    matrix[:3, 3] = translation
    return matrix

def matrix_to_quaternion(self, matrix):
    m = matrix
    tr = np.trace(matrix)
    if tr > 0:
        S = np.sqrt(tr + 1.0) * 2  # S=4*qw
        qw = 0.25 * S
        qx = (m[2, 1] - m[1, 2]) / S
        qy = (m[0, 2] - m[2, 0]) / S
        qz = (m[1, 0] - m[0, 1]) / S
    elif (m[0, 0] > m[1, 1]) and (m[0, 0] > m[2, 2]):
        S = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2  # S=4*qx
        qw = (m[2, 1] - m[1, 2]) / S
        qx = 0.25 * S
        qy = (m[0, 1] + m[1, 0]) / S
        qz = (m[0, 2] + m[2, 0]) / S
    elif m[1, 1] > m[2, 2]:
        S = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2  # S=4*qy
        qw = (m[0, 2] - m[2, 0]) / S
        qx = (m[0, 1] + m[1, 0]) / S
        qy = 0.25 * S
        qz = (m[1, 2] + m[2, 1]) / S
    else:
        S = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2  # S=4*qz
        qw = (m[1, 0] - m[0, 1]) / S
        qx = (m[0, 2] + m[2, 0]) / S
        qy = (m[1, 2] + m[2, 1]) / S
        qz = 0.25 * S
    return np.array([qx, qy, qz, qw])

def create_rotation_matrix(rotation):
    roll, pitch, yaw = rotation

    # Create individual matrices
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])

    Ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    # Combine rotations
    R = np.dot(Rz, np.dot(Ry, Rx))
    rotation_matrix = np.eye(4)
    rotation_matrix[:3, :3] = R
    return rotation_matrix

class RenderObject:
    def __init__(
        self,
        model: str,
        position: Vector3 | None = None,
        rotation: Vector3 | None = None,
        *,
        data: Any = None,
        gen_boundary: Callable[[], Boundary] | None = None,
        override_texture: str | None = None,
    ):
        self.model: str = model
        self.children: list[RenderObject] = []
        self._transform = np.eye(4)
        self._position: Vector3 = position if position is not None else Vector3.from_null()
        self._rotation: Vector3 = rotation if rotation is not None else Vector3.from_null()
        self._cube: Cube | None = None
        self._boundary: Boundary | Empty | None = None
        self.genBoundary: Callable[[], Boundary] | None = gen_boundary
        self.data: Any = data
        self.override_texture: str | None = override_texture

        self._recalc_transform()

    def transform(self):
        return self._transform

    def set_transform(self, transform):
        self._transform = transform
        self._position = transform[:3, 3]  # Extract position from the last column

        # Extract rotation matrix from the top-left 3x3 submatrix
        rotation_matrix = transform[:3, :3]
        quaternion = matrix_to_quaternion(rotation_matrix)
        self._rotation = euler_from_quaternion(quaternion)  # Convert to Euler angles

    def _recalc_transform(self):
        translation_matrix = create_translation_matrix(self._position)
        rotation_matrix = create_rotation_matrix(self._rotation)
        self._transform = np.dot(translation_matrix, rotation_matrix)

    def position(self) -> Vector3:
        return copy(self._position)

    def set_position(self, x: float, y: float, z: float):
        if self._position.x == x and self._position.y == y and self._position.z == z:
            return

        self._position = Vector3(x, y, z)
        self._recalc_transform()

    def rotation(self) -> Vector3:
        return copy(self._rotation)

    def set_rotation(self, x: float, y: float, z: float):
        if self._rotation.x == x and self._rotation.y == y and self._rotation.z == z:
            return

        self._rotation = Vector3(x, y, z)
        self._recalc_transform()

    def reset_cube(self):
        self._cube = None

    def cube(self, scene: Scene) -> Cube:
        if not self._cube:
            min_point = Vector3(10000, 10000, 10000)
            max_point = Vector3(-10000, -10000, -10000)
            identity_matrix = np.eye(4)  # Replacing mat4() with an identity matrix
            self._cube_rec(scene, identity_matrix, self, min_point, max_point)
            self._cube = Cube(scene, min_point, max_point)
        return self._cube

    def radius(self, scene: Scene) -> float:
        cube = self.cube(scene)
        return max(
            abs(cube.min_point.x),
            abs(cube.min_point.y),
            abs(cube.min_point.z),
            abs(cube.max_point.x),
            abs(cube.max_point.y),
            abs(cube.max_point.z),
        )

    def _cube_rec(self, scene: Scene, transform: np.ndarray, obj: RenderObject, min_point: Vector3, max_point: Vector3):
        obj_min, obj_max = scene.model(obj.model).box()

        # Convert Vector3 to numpy array for matrix multiplication, append 1 for homogeneous coordinates
        obj_min_np = np.dot(transform, np.append(np.array([*obj_min]), 1))[:3]
        obj_max_np = np.dot(transform, np.append(np.array([*obj_max]), 1))[:3]

        # Update the bounding box corners
        min_point.x = min(min_point.x, obj_min_np[0], obj_max_np[0])
        min_point.y = min(min_point.y, obj_min_np[1], obj_max_np[1])
        min_point.z = min(min_point.z, obj_min_np[2], obj_max_np[2])
        max_point.x = max(max_point.x, obj_min_np[0], obj_max_np[0])
        max_point.y = max(max_point.y, obj_min_np[1], obj_max_np[1])
        max_point.z = max(max_point.z, obj_min_np[2], obj_max_np[2])

        for child in obj.children:
            # Calculate the child's transform matrix by multiplying the parent's transform matrix with the child's
            child_transform = np.dot(transform, np.array([*child.transform()]))
            self._cube_rec(scene, child_transform, child, min_point, max_point)

    def reset_boundary(self):
        self._boundary = None

    def boundary(self, scene: Scene) -> Boundary | Empty:
        if not self._boundary:
            if self.genBoundary is None:
                self._boundary = Empty(scene)
            else:
                self._boundary = self.genBoundary()
        return self._boundary


class Camera:
    def __init__(self):
        self.x: float = 40.0
        self.y: float = 130.0
        self.z: float = 0.5
        self.width: int = 1920
        self.height: int = 1080
        self.pitch: float = math.pi / 2
        self.yaw: float = 0.0
        self.distance: float = 10.0
        self.fov: float = 90.0

    def view(self):
        """Calculate and return the view matrix."""
        # Camera direction calculations
        direction = np.array([
            math.cos(self.yaw) * math.cos(self.pitch),
            math.sin(self.yaw) * math.cos(self.pitch),
            math.sin(self.pitch)
        ])
        # Normalize direction
        direction = direction / np.linalg.norm(direction)

        # Define up vector
        up = np.array([0, 0, 1])

        # Calculate right vector
        right = np.cross(up, direction)
        # Normalize right vector
        right = right / np.linalg.norm(right)

        # Recalculate up vector as cross product of direction and right vectors
        up = np.cross(direction, right)

        # Camera position
        position = np.array([self.x, self.y, self.z])

        # View matrix construction
        view = np.eye(4)
        view[0, :3] = right
        view[1, :3] = up
        view[2, :3] = -direction
        view[:3, 3] = -np.dot(view[:3, :3], position)

        return view

    def projection(self):
        """Calculate and return the perspective projection matrix."""
        aspect_ratio = self.width / self.height
        fov_rad = math.radians(self.fov)  # Convert fov to radians
        f = 1 / math.tan(fov_rad / 2)

        near = 0.1
        far = 5000.0
        projection = np.zeros((4, 4))
        projection[0, 0] = f / aspect_ratio
        projection[1, 1] = f
        projection[2, 2] = (far + near) / (near - far)
        projection[2, 3] = (2 * far * near) / (near - far)
        projection[3, 2] = -1

        return projection

    def translate(self, translation: Vector3):
        self.x += translation.x
        self.y += translation.y
        self.z += translation.z

    def rotate(self, yaw: float, pitch: float):
        """Rotates the object by yaw and pitch angles.

        Args:
        ----
            yaw: float - Yaw angle in radians
            pitch: float - Pitch angle in radians

        Returns:
        -------
            None - Rotates object in place

        Processes rotation:
        ------------------
            - Increments pitch by pitch argument
            - Increments yaw by yaw argument
            - Clips pitch to valid range between 0 and pi radians to avoid gimbal lock
        """
        self.pitch += pitch
        self.yaw += yaw

        if self.pitch > math.pi - 0.001:
            self.pitch = math.pi - 0.001
        elif self.pitch < 0.001:
            self.pitch = 0.001

    def forward(self, ignore_z: bool = True) -> Vector3:
        """Calculates the forward vector from the camera's rotation.

        Args:
        ----
            ignore_z: Whether to ignore z component of vector {True by default}.

        Returns:
        -------
            Vector3: Normalized forward vector from camera rotation

        Processing Logic:
        ----------------
            - Calculate x component of eye vector from yaw and pitch
            - Calculate y component of eye vector from yaw and pitch
            - Set z component to 0 if ignore_z is True, else calculate from pitch
            - Return normalized negative of eye vector as forward vector.
        """
        eye_x: float = math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_y: float = math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2)
        eye_z: float | Literal[0] = 0 if ignore_z else math.sin(self.pitch - math.pi / 2)
        norm = np.linalg.norm([eye_x, eye_y, eye_z])
        if norm == 0:
            return Vector3.from_null()
        return Vector3(eye_x / norm, eye_y / norm, eye_z / norm)

    def sideward(self, ignore_z: bool = True) -> Vector3:
        """Returns a normalized vector perpendicular to the forward direction.

        Args:
        ----
            ignore_z: Ignore z-component of forward vector.

        Returns:
        -------
            Vector3: Normalized sideward vector.

        Processing Logic:
        ----------------
            - Calculate cross product of forward vector and (0,0,1) to get sideward vector
            - Normalize sideward vector to get unit sideward vector
            - Return normalized sideward vector
        """
        cross_product = np.cross(self.forward(ignore_z), np.array([0.0, 0.0, 1.0]))
        normalized_vector = cross_product / np.linalg.norm(cross_product)
        return Vector3(normalized_vector[0], normalized_vector[1], normalized_vector[2])

    def upward(self, ignore_xy: bool = True) -> Vector3:
        """Returns the upward vector of the entity.

        Args:
        ----
            ignore_xy (bool): Ignore x and y components of the vector if True.

        Returns:
        -------
            Vector3: The normalized upward vector.

        Processing Logic:
        ----------------
            - Calculate forward vector ignoring z component
            - Calculate sideward vector ignoring z component
            - Take cross product of forward and sideward vectors
            - Return normalized cross product vector
        """
        if ignore_xy:
            retVect = Vector3(0, 0, 1)
            retVect.normalize()
            return retVect

        forward = self.forward(ignore_z=False)
        sideward = self.sideward(ignore_z=False)
        cross = forward.cross(sideward)  # Utilize the cross product method of Vector3
        cross.normalize()
        return cross  # Normalize the result using the Vector3 normalize method

    def true_position(self) -> Vector3:
        """Calculates the true position of an object based on its orientation and distance from origin.

        Args:
        ----
            self: {Object with x, y, z, yaw, pitch, and distance attributes}

        Returns:
        -------
            Vector3: {Calculated true position as a 3D vector}

        Processing Logic:
        ----------------
            - Calculate x, y, z offsets based on orientation and distance
            - Add offsets to base x, y, z to get true position
            - Return true position as a 3D vector
        """
        x, y, z = self.x, self.y, self.z
        x += math.cos(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        y += math.sin(self.yaw) * math.cos(self.pitch - math.pi / 2) * self.distance
        z += math.sin(self.pitch - math.pi / 2) * self.distance
        return Vector3(x, y, z)
