from __future__ import annotations

import base64
import itertools
import json
import math

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any, NamedTuple

from loggerplus import RobustLogger
from pykotor.common.indoorkit import Kit, KitComponent, KitComponentHook, KitDoor
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.common.modulekit import ModuleKit, ModuleKitManager
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.bwm import BWM, bytes_bwm, read_bwm
from pykotor.resource.formats.erf import ERF, ERFType, write_erf
from pykotor.resource.formats.lyt import LYT, LYTRoom, bytes_lyt
from pykotor.resource.formats.tpc import TPCTextureFormat, bytes_tpc
from pykotor.resource.formats.vis import VIS, bytes_vis
from pykotor.resource.generics.are import ARE, ARENorthAxis, bytes_are
from pykotor.resource.generics.git import GIT, GITDoor, GITModuleLink, bytes_git
from pykotor.resource.generics.ifo import IFO, bytes_ifo
from pykotor.resource.generics.utd import bytes_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import model
from utility.common.geometry import Vector2, Vector3

if TYPE_CHECKING:
    import os


INDOOR_EMBED_RESREF = "indoormap"
INDOOR_EMBED_RESTYPE = ResourceType.TXT


class DoorInsertion(NamedTuple):
    door: KitDoor
    room: "IndoorMapRoom"
    room2: "IndoorMapRoom | None"
    static: bool
    position: Vector3
    rotation: float
    hook1: KitComponentHook
    hook2: KitComponentHook | None


class MinimapData(NamedTuple):
    imagePointMin: Vector2
    imagePointMax: Vector2
    worldPointMin: Vector2
    worldPointMax: Vector2


class MissingRoomInfo(NamedTuple):
    kit_name: str
    component_name: str | None
    reason: str  # "kit_missing" or "component_missing"


class IndoorMap:
    """Headless indoor map model + builder.

    This is a migrated version of HolocronToolset `toolset.data.indoormap.IndoorMap`,
    refactored to remove UI (`qtpy`) dependencies so it can be used by library code and KotorCLI.
    """

    def __init__(
        self,
        rooms: list["IndoorMapRoom"] | None = None,
        module_id: str | None = None,
        name: LocalizedString | None = None,
        lighting: Color | None = None,
        skybox: str | None = None,
        warp_point: Vector3 | None = None,
        target_game_type: bool | None = None,
    ):
        self.rooms: list[IndoorMapRoom] = rooms if rooms is not None else []
        self.module_id: str = module_id if module_id is not None else "test01"
        self.name: LocalizedString = name if name is not None else LocalizedString.from_english("New Module")
        self.lighting: Color = lighting if lighting is not None else Color(0.5, 0.5, 0.5)
        self.skybox: str = skybox if skybox is not None else ""
        self.warp_point: Vector3 = warp_point if warp_point is not None else Vector3.from_null()
        # target_game_type: None = use installation.game(), True = K2, False = K1
        self.target_game_type: bool | None = target_game_type

        # Build-time fields
        self.mod: ERF | None = None
        self.lyt: LYT | None = None
        self.vis: VIS | None = None
        self.are: ARE | None = None
        self.ifo: IFO | None = None
        self.git: GIT | None = None

        self.room_names: dict[IndoorMapRoom, str] = {}
        self.tex_renames: dict[str, str] = {}
        self.total_lm: int = 0
        self.used_rooms: set[KitComponent] = set()
        self.used_kits: set[Kit] = set()
        self.scan_mdls: set[bytes] = set()

    def rebuild_room_connections(self):
        for room in self.rooms:
            room.rebuild_connections(self.rooms)

    def door_insertions(self) -> list[DoorInsertion]:
        points: list[Vector3] = []
        insertions: list[DoorInsertion] = []

        for room in self.rooms:
            for hook_index, connection in enumerate(room.hooks):
                room1: IndoorMapRoom = room
                room2: IndoorMapRoom | None = None
                hook1: KitComponentHook = room1.component.hooks[hook_index]
                hook2: KitComponentHook | None = None
                door: KitDoor = hook1.door
                position: Vector3 = room1.hook_position(hook1)
                rotation: float = hook1.rotation + room1.rotation
                if connection is not None:
                    for other_hook_index, other_room in enumerate(connection.hooks):
                        if other_room == room1:
                            other_hook: KitComponentHook = connection.component.hooks[other_hook_index]
                            if hook1.door.width < other_hook.door.width:
                                door = other_hook.door
                                hook2 = hook1
                                hook1 = other_hook
                                room2 = room1
                                room1 = connection
                            else:
                                hook2 = connection.component.hooks[other_hook_index]
                                room2 = connection
                                rotation = hook2.rotation + room2.rotation

                if position not in points:
                    points.append(position)
                    static: bool = connection is None
                    door_insertion = DoorInsertion(
                        door,
                        room1,
                        room2,
                        static,
                        position,
                        rotation,
                        hook1,
                        hook2,
                    )
                    insertions.append(door_insertion)

        return insertions

    def _target_is_k2(
        self,
        installation: Installation,
        game_override: Game | None,
    ) -> bool:
        if self.target_game_type is not None:
            return bool(self.target_game_type)
        if game_override is not None:
            return game_override == Game.K2
        try:
            return installation.game() == Game.K2
        except Exception:
            return False

    def add_rooms(self):
        assert self.vis is not None
        for i in range(len(self.rooms)):
            modelname = f"{self.module_id}_room{i}"
            self.vis.add_room(modelname)

    def process_room_components(self):
        for room in self.rooms:
            self.used_rooms.add(room.component)
        for kit_room in self.used_rooms:
            self.scan_mdls.add(kit_room.mdl)
            self.used_kits.add(kit_room.kit)
            for door_padding_dict in list(kit_room.kit.top_padding.values()) + list(kit_room.kit.side_padding.values()):
                for padding_model in door_padding_dict.values():
                    self.scan_mdls.add(padding_model.mdl)

    def handle_textures(self):
        assert self.mod is not None
        # Deterministic iteration: sets are unordered and can change rename indices across runs.
        for mdl in sorted(self.scan_mdls):
            # Deterministic rename order is required for stable `.indoor -> .mod` rebuilds.
            for texture in (t for t in sorted(model.iterate_textures(mdl)) if t not in self.tex_renames):
                renamed = f"{self.module_id}_tex{len(self.tex_renames.keys())}"
                self.tex_renames[texture] = renamed
                for kit in sorted(self.used_kits, key=lambda k: k.id):
                    if texture not in kit.textures:
                        continue
                    self.mod.set_data(renamed, ResourceType.TGA, kit.textures[texture])
                    self.mod.set_data(renamed, ResourceType.TXI, kit.txis.get(texture, b""))

    def handle_lightmaps(
        self,
        installation: Installation,
    ):
        assert self.mod is not None
        # The toolset tries kit lightmaps first, then installation. We keep the same behavior.
        for kit in sorted(self.used_kits, key=lambda k: k.id):
            for lightmap_name in sorted(kit.lightmaps.keys()):
                lightmap_data = kit.lightmaps[lightmap_name]
                # Ensure TXI for lightmaps is also placed
                self.mod.set_data(lightmap_name, ResourceType.TGA, lightmap_data)
                self.mod.set_data(lightmap_name, ResourceType.TXI, kit.txis.get(lightmap_name, b""))

        # Additionally, later `process_lightmaps` will pull missing lightmaps from installation if needed.

    def add_static_resources(self, room: IndoorMapRoom):
        assert self.mod is not None
        from pykotor.extract.file import ResourceIdentifier  # noqa: PLC0415

        for filename, data in room.component.kit.always.items():
            resname, restype = ResourceIdentifier.from_path(filename).unpack()
            if restype == ResourceType.INVALID:
                continue
            self.mod.set_data(resname, restype, data)

    def process_model(
        self,
        room: IndoorMapRoom,
        installation: Installation,
        target_tsl: bool,
    ) -> tuple[bytes | bytearray, bytes | bytearray]:
        mdl, mdx = model.flip(room.component.mdl, room.component.mdx, flip_x=room.flip_x, flip_y=room.flip_y)
        mdl_transformed: bytes | bytearray = model.transform(mdl, Vector3.from_null(), room.rotation)
        mdl_converted: bytes | bytearray = model.convert_to_k2(mdl_transformed) if target_tsl else model.convert_to_k1(mdl_transformed)
        return mdl_converted, mdx

    def process_lightmaps(
        self,
        mdl_data: bytes | bytearray,
        installation: Installation,
    ) -> bytes | bytearray:
        assert self.mod is not None
        lm_renames: dict[str, str] = {}
        # Deterministic rename order is required for stable `.indoor -> .mod` rebuilds.
        for lightmap in sorted(model.iterate_lightmaps(mdl_data)):
            renamed = f"{self.module_id}_lm{self.total_lm}"
            self.total_lm += 1
            lm_renames[lightmap.lower()] = renamed

            # Prefer kit-copied lightmaps already in mod; else try installation for texture + txi.
            tga_in_mod = self.mod.get(renamed, ResourceType.TGA) if self.mod.has(renamed, ResourceType.TGA) else None
            if tga_in_mod is None:
                tex = installation.texture(
                    lightmap,
                    [
                        SearchLocation.CHITIN,
                        SearchLocation.OVERRIDE,
                        SearchLocation.TEXTURES_TPA,
                        SearchLocation.TEXTURES_GUI,
                    ],
                )
                if tex is not None:
                    # Convert to RGBA and store as TGA
                    tex = tex.copy()
                    fmt = tex.format()
                    if fmt in (TPCTextureFormat.BGR, TPCTextureFormat.DXT1, TPCTextureFormat.Greyscale):
                        tex.convert(TPCTextureFormat.RGB)
                    elif fmt in (TPCTextureFormat.BGRA, TPCTextureFormat.DXT3, TPCTextureFormat.DXT5):
                        tex.convert(TPCTextureFormat.RGBA)
                    self.mod.set_data(renamed, ResourceType.TGA, bytes_tpc(tex, ResourceType.TGA))
        return model.change_lightmaps(mdl_data, lm_renames)

    def process_bwm(self, room: IndoorMapRoom) -> BWM:
        bwm: BWM = deepcopy(room.base_walkmesh())
        bwm.flip(room.flip_x, room.flip_y)
        bwm.rotate(room.rotation)
        bwm.translate(room.position.x, room.position.y, room.position.z)
        return bwm

    def add_model_resources(
        self,
        modelname: str,
        mdl: bytes | bytearray,
        mdx: bytes | bytearray,
    ) -> None:
        assert self.mod is not None
        mdl = model.change_textures(mdl, self.tex_renames)
        self.mod.set_data(modelname, ResourceType.MDL, bytes(mdl))
        self.mod.set_data(modelname, ResourceType.MDX, bytes(mdx))

    def add_bwm_resource(self, modelname: str, bwm: BWM):
        assert self.mod is not None
        self.mod.set_data(modelname, ResourceType.WOK, bytes_bwm(bwm))

    def process_skybox(self, kits: list[Kit]):
        if not self.skybox:
            return
        assert self.mod is not None and self.lyt is not None and self.vis is not None
        for kit in kits:
            if self.skybox not in kit.skyboxes:
                continue
            mdl, mdx = kit.skyboxes[self.skybox].mdl, kit.skyboxes[self.skybox].mdx
            model_name = f"{self.module_id}_sky"
            mdl_converted = model.change_textures(mdl, self.tex_renames)
            self.mod.set_data(model_name, ResourceType.MDL, bytes(mdl_converted))
            self.mod.set_data(model_name, ResourceType.MDX, mdx)
            self.lyt.rooms.append(LYTRoom(model_name, Vector3.from_null()))
            self.vis.add_room(model_name)

    def _compute_bounds(self) -> tuple[Vector2, Vector2]:
        walkmeshes: list[BWM] = []
        for room in self.rooms:
            bwm = deepcopy(room.base_walkmesh())
            bwm.flip(room.flip_x, room.flip_y)
            bwm.rotate(room.rotation)
            bwm.translate(room.position.x, room.position.y, room.position.z)
            walkmeshes.append(bwm)

        bbmin = Vector3(1000000, 1000000, 1000000)
        bbmax = Vector3(-1000000, -1000000, -1000000)
        for bwm in walkmeshes:
            for vertex in bwm.vertices():
                bbmin.x = min(bbmin.x, vertex.x)
                bbmin.y = min(bbmin.y, vertex.y)
                bbmax.x = max(bbmax.x, vertex.x)
                bbmax.y = max(bbmax.y, vertex.y)

        bbmin.x -= 5
        bbmin.y -= 5
        bbmax.x += 5
        bbmax.y += 5
        return Vector2(bbmin.x, bbmin.y), Vector2(bbmax.x, bbmax.y)

    def generate_and_set_minimap(self):
        """Headless minimap generation.

        We generate a blank 512x256 RGBA minimap. Bounds are still computed from walkmeshes
        and written into ARE so the in-game map framing remains consistent.
        """
        assert self.mod is not None
        from pykotor.resource.formats.tpc import TPC  # noqa: PLC0415

        data = bytearray()
        for _y, _x in itertools.product(range(256), range(512)):
            data.extend([0, 0, 0, 255])
        minimap_tpc = TPC()
        minimap_tpc.set_single(data, TPCTextureFormat.RGBA, 512, 256)
        self.mod.set_data(f"lbl_map{self.module_id}", ResourceType.TGA, bytes_tpc(minimap_tpc, ResourceType.TGA))

    def set_area_attributes(self, bounds: tuple[Vector2, Vector2]):
        assert self.are is not None
        world_min, world_max = bounds
        self.are.tag = self.module_id
        self.are.dynamic_light = self.lighting
        self.are.name = self.name
        # Image points are pixels in the minimap image; use full image.
        self.are.map_point_1 = Vector2(0, 0)
        self.are.map_point_2 = Vector2(512, 256)
        self.are.world_point_1 = world_min
        self.are.world_point_2 = world_max
        self.are.map_zoom = 1
        self.are.map_res_x = 1
        self.are.north_axis = ARENorthAxis.NegativeY

    def set_ifo_attributes(self):
        assert self.ifo is not None and self.vis is not None
        self.ifo.tag = self.module_id
        self.ifo.area_name = ResRef(self.module_id)
        self.ifo.resref = ResRef(self.module_id)
        self.vis.set_all_visible()
        self.ifo.entry_position = self.warp_point

    def handle_door_insertions(self, target_tsl: bool):
        assert self.mod is not None and self.git is not None
        insertions = self.door_insertions()
        for i, insertion in enumerate(insertions):
            door_resname = f"{self.module_id}_dor{i}"
            door: GITDoor = GITDoor()
            door.resref = ResRef(door_resname)
            door.tag = door_resname
            door.position = insertion.position
            door.bearing = math.radians(insertion.rotation)
            if insertion.room2 is not None:
                # Linked door
                door.linked_to_module = ResRef(self.module_id)
                door.linked_to = door_resname
                door.linked_to_flags = GITModuleLink.ToDoor
            else:
                door.linked_to_flags = GITModuleLink.NoLink
            self.git.doors.append(door)

            utd = insertion.door.utdK2 if target_tsl else insertion.door.utdK1
            self.mod.set_data(door_resname, ResourceType.UTD, bytes_utd(utd))

    def finalize_module_data(self):
        assert self.mod is not None and self.lyt is not None and self.vis is not None and self.are is not None and self.git is not None and self.ifo is not None
        self.mod.set_data(self.module_id, ResourceType.LYT, bytes_lyt(self.lyt))
        self.mod.set_data(self.module_id, ResourceType.VIS, bytes_vis(self.vis))
        self.mod.set_data(self.module_id, ResourceType.ARE, bytes_are(self.are))
        self.mod.set_data(self.module_id, ResourceType.GIT, bytes_git(self.git))
        self.mod.set_data("module", ResourceType.IFO, bytes_ifo(self.ifo))

        # Embed the .indoor JSON so it can be recovered from composite modules later.
        self.mod.set_data(INDOOR_EMBED_RESREF, INDOOR_EMBED_RESTYPE, self.write())

    def build(
        self,
        installation: Installation,
        kits: list[Kit],
        output_path: os.PathLike | str,
        *,
        game_override: Game | None = None,
        loadscreen_path: os.PathLike | str | None = None,
    ):
        self.mod = ERF(ERFType.MOD)
        self.lyt = LYT()
        self.vis = VIS()
        self.are = ARE()
        self.ifo = IFO()
        self.git = GIT()
        self.room_names.clear()
        self.tex_renames.clear()
        self.total_lm = 0
        self.used_rooms.clear()
        self.used_kits.clear()
        self.scan_mdls.clear()

        target_tsl: bool = self._target_is_k2(installation, game_override)

        self.add_rooms()
        self.process_room_components()
        self.handle_textures()
        self.handle_lightmaps(installation)

        # Process each room
        for i, room in enumerate(self.rooms):
            modelname = f"{self.module_id}_room{i}"
            self.room_names[room] = modelname
            self.lyt.rooms.append(LYTRoom(modelname, room.position))
            self.add_static_resources(room)

            mdl, mdx = self.process_model(room, installation, target_tsl)
            mdl = model.change_textures(mdl, self.tex_renames)
            mdl = self.process_lightmaps(mdl, installation)
            self.add_model_resources(modelname, mdl, mdx)

            bwm = self.process_bwm(room)
            self.add_bwm_resource(modelname, bwm)

        self.process_skybox(kits)
        self.generate_and_set_minimap()

        # Loadscreen override
        if loadscreen_path is not None:
            from pathlib import Path  # noqa: PLC0415

            load_path = Path(loadscreen_path)
            if load_path.is_file():
                data = load_path.read_bytes()
                restype = ResourceType.TGA if load_path.suffix.lower() == ".tga" else ResourceType.TPC
                self.mod.set_data(f"load_{self.module_id}", restype, data)

        self.handle_door_insertions(target_tsl)
        bounds: tuple[Vector2, Vector2] = self._compute_bounds()
        self.set_area_attributes(bounds)
        self.set_ifo_attributes()
        self.finalize_module_data()

        write_erf(self.mod, output_path)

    def write(self) -> bytes:
        data: dict[str, Any] = {"module_id": self.module_id, "name": {}}

        data["name"]["stringref"] = self.name.stringref
        for language, gender, text in self.name:
            stringid = LocalizedString.substring_id(language, gender)
            data["name"][stringid] = text

        data["lighting"] = [self.lighting.r, self.lighting.g, self.lighting.b]
        data["skybox"] = self.skybox
        data["warp"] = self.module_id
        if self.target_game_type is not None:
            data["target_game_type"] = self.target_game_type

        data["rooms"] = []
        for room in self.rooms:
            room_data: dict[str, Any] = {
                "position": [*room.position],
                "rotation": room.rotation,
                "flip_x": room.flip_x,
                "flip_y": room.flip_y,
                "kit": room.component.kit.id,
                "component": room.component.id,
            }
            # Implicit ModuleKit support: persist the module root used to resolve the kit.
            if isinstance(room.component.kit, ModuleKit):
                room_data["module_root"] = room.component.kit.module_root
            if room.walkmesh_override is not None:
                room_data["walkmesh_override"] = base64.b64encode(bytes_bwm(room.walkmesh_override)).decode("ascii")
            data["rooms"].append(room_data)

        return json.dumps(data).encode("utf-8")

    def load(
        self,
        raw: bytes,
        kits: list[Kit],
        module_kit_manager: ModuleKitManager | None = None,
    ) -> list[MissingRoomInfo]:
        self.reset()
        data: dict[str, Any] = json.loads(raw)
        try:
            return self._load_data(data, kits, module_kit_manager)
        except KeyError as e:
            msg = "Map file is corrupted."
            raise ValueError(msg) from e

    def _load_data(
        self,
        data: dict[str, Any],
        kits: list[Kit],
        module_kit_manager: ModuleKitManager | None = None,
    ) -> list[MissingRoomInfo]:
        missing_rooms: list[MissingRoomInfo] = []

        self.name = LocalizedString(data["name"]["stringref"])
        for substring_id in (key for key in data["name"] if str(key).isnumeric()):
            language, gender = LocalizedString.substring_pair(int(substring_id))
            self.name.set_data(language, gender, data["name"][substring_id])

        self.lighting.r = data["lighting"][0]
        self.lighting.g = data["lighting"][1]
        self.lighting.b = data["lighting"][2]

        self.module_id = data.get("warp", data.get("module_id", "test01"))
        self.skybox = data.get("skybox", "")
        self.target_game_type = data.get("target_game_type", None)

        for room_data in data.get("rooms", []):
            kit_id = room_data["kit"]
            comp_id = room_data["component"]
            s_kit: Kit | None = next((k for k in kits if k.id == kit_id), None)
            if s_kit is None:
                if module_kit_manager is not None:
                    module_root = str(room_data.get("module_root") or kit_id)
                    mk = module_kit_manager.get_module_kit(module_root)
                    if mk.ensure_loaded():
                        s_kit = mk
                if s_kit is None:
                    RobustLogger().warning("Kit '%s' is missing, skipping room.", kit_id)
                    missing_rooms.append(MissingRoomInfo(kit_name=kit_id, component_name=comp_id, reason="kit_missing"))
                    continue
            s_component: KitComponent | None = next((c for c in s_kit.components if c.id == comp_id), None)
            if s_component is None:
                RobustLogger().warning("Component '%s' is missing in kit '%s', skipping room.", comp_id, s_kit.id)
                missing_rooms.append(MissingRoomInfo(kit_name=kit_id, component_name=comp_id, reason="component_missing"))
                continue

            room = IndoorMapRoom(
                s_component,
                Vector3(room_data["position"][0], room_data["position"][1], room_data["position"][2]),
                room_data["rotation"],
                flip_x=bool(room_data.get("flip_x", False)),
                flip_y=bool(room_data.get("flip_y", False)),
            )
            if "walkmesh_override" in room_data:
                try:
                    raw_bwm = base64.b64decode(room_data["walkmesh_override"])
                    room.walkmesh_override = read_bwm(raw_bwm)
                except Exception as exc:  # noqa: BLE001
                    RobustLogger().warning("Failed to read walkmesh override for room '%s': %s", room.component.id, exc)
            self.rooms.append(room)

        return missing_rooms

    def reset(self):
        self.rooms.clear()
        self.module_id = "test01"
        self.name = LocalizedString.from_english("New Module")
        self.lighting = Color(0.5, 0.5, 0.5)
        self.target_game_type = None


class IndoorMapRoom:
    def __init__(
        self,
        component: KitComponent,
        position: Vector3,
        rotation: float,
        *,
        flip_x: bool,
        flip_y: bool,
    ):
        self.component: KitComponent = component
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.hooks: list[IndoorMapRoom | None] = [None] * len(component.hooks)
        self.flip_x: bool = flip_x
        self.flip_y: bool = flip_y
        self.walkmesh_override: BWM | None = None

    def hook_position(self, hook: KitComponentHook, *, world_offset: bool = True) -> Vector3:
        pos: Vector3 = copy(hook.position)
        pos.x = -pos.x if self.flip_x else pos.x
        pos.y = -pos.y if self.flip_y else pos.y
        temp: Vector3 = copy(pos)

        cos = math.cos(math.radians(self.rotation))
        sin = math.sin(math.radians(self.rotation))
        pos.x = temp.x * cos - temp.y * sin
        pos.y = temp.x * sin + temp.y * cos

        if world_offset:
            pos = pos + self.position
        return pos

    def rebuild_connections(self, rooms: list["IndoorMapRoom"]):
        self.hooks = [None] * len(self.component.hooks)
        for hook in self.component.hooks:
            hook_index = self.component.hooks.index(hook)
            hook_pos = self.hook_position(hook)
            for other_room in (r for r in rooms if r is not self):
                for other_hook in other_room.component.hooks:
                    other_hook_pos = other_room.hook_position(other_hook)
                    if hook_pos.distance(other_hook_pos) < 0.001:
                        self.hooks[hook_index] = other_room

    def base_walkmesh(self) -> BWM:
        return self.walkmesh_override if self.walkmesh_override is not None else self.component.bwm


class _RoomTransformMatch(NamedTuple):
    component: KitComponent
    flip_x: bool
    flip_y: bool
    rotation_deg: float
    translation: Vector3
    rms_error: float
