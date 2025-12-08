from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from OpenGL.raw.GL.VERSION.GL_1_0 import GL_BACK, GL_DEPTH_TEST, GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA, glBlendFunc, glCullFace, glEnable
from loggerplus import RobustLogger

from pykotor.common.module import Module, ModuleResource
from pykotor.common.stream import BinaryReader
from pykotor.extract.file import ResourceResult
from pykotor.extract.installation import SearchLocation
from pykotor.gl.models.mdl import Model, Node
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
from pykotor.gl.scene.async_loader import AsyncResourceLoader, create_model_from_intermediate, create_texture_from_intermediate
from pykotor.gl.shader import Texture
from pykotor.resource.formats.lyt.lyt_data import LYT
from pykotor.resource.formats.tpc.tpc_data import TPC
from pykotor.resource.formats.twoda.twoda_auto import read_2da
from pykotor.resource.formats.twoda.twoda_data import TwoDA
from pykotor.resource.generics.git import GIT, GITCreature, GITInstance
from pykotor.resource.generics.ifo import IFO
from pykotor.resource.type import ResourceType
from pykotor.tools import creature
from utility.common.geometry import Vector3
from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:

    from collections.abc import Callable
    from concurrent.futures import Future

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.module import Module, ModulePieceResource, ModuleResource
    from pykotor.extract.capsule import Capsule
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.gl.models.mdl import Model, Node
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.generics.git import GITCreature, GITInstance
    from pykotor.resource.generics.utc import UTC
    from utility.common.geometry import Vector3

T = TypeVar("T")
SEARCH_ORDER_2DA: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
SEARCH_ORDER: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]


# DO NOT USE INSTALLATION IN CHILD PROCESSES
# Both IO AND parsing should be in child process(es). ONE PROCESS PER FILE!!


class SceneBase:
    SPECIAL_MODELS: ClassVar[list[str]] = ["waypoint", "store", "sound", "camera", "trigger", "encounter", "unknown"]

    def __init__(
        self,
        *,
        installation: Installation | None = None,
        module: Module | None = None,
    ):

        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCullFace(GL_BACK)

        self.installation: Installation | None = installation
        if installation is not None:
            self.set_installation(installation)

        self._missing_texture = Texture.from_color(255, 0, 255)
        self._missing_lightmap = Texture.from_color(0, 0, 0)
        self._loading_texture = Texture.from_color(128, 128, 128)

        self.textures: CaseInsensitiveDict[Texture] = CaseInsensitiveDict()
        self.textures["NULL"] = Texture.from_color()
        self.models: CaseInsensitiveDict[Model] = CaseInsensitiveDict()
        # Store texture lookup results from existing lookups for reuse (no additional lookups)
        # CRITICAL: Every texture in self.textures MUST have an entry in texture_lookup_info
        self.texture_lookup_info: CaseInsensitiveDict[dict[str, Any]] = CaseInsensitiveDict()
        # Track texture names that are requested during rendering (populated by scene.texture() calls)
        self.requested_texture_names: set[str] = set()

        self.cursor: RenderObject = RenderObject("cursor")
        self.objects: dict[Any, RenderObject] = {}

        self.selection: list[RenderObject] = []
        self._module: Module | None = module
        self.camera: Camera = Camera()

        self.git: GIT | None = None
        self.layout: LYT | None = None
        self.clear_cache_buffer: list[ResourceIdentifier] = []
        
        # Async resource loading
        # Main thread: Use Installation to RESOLVE file locations ONLY (no Installation in child!)
        # Child process: Do raw file IO + parsing (one process per file)
        
        # Pre-compute search location lists to avoid creating new lists on every call
        texture_search_locs = [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_TPA, SearchLocation.CHITIN]
        model_search_locs = [SearchLocation.OVERRIDE, SearchLocation.CHITIN]
        # Cache capsules list for model loading (computed once per scene, not per model)
        _cached_capsules: list[Capsule] | None = None
        
        def _resolve_texture_location(name: str) -> tuple[str, int, int, dict[str, Any]] | None:
            """Resolve texture file location in main thread using Installation ONLY.
            
            Returns (filepath, offset, size, context) or None.
            Context contains the exact lookup information that MUST be stored when texture loads.
            """
            RobustLogger().debug(f"_resolve_texture_location called for '{name}'")
            if self.installation is None:
                RobustLogger().debug(f"_resolve_texture_location: No installation available for '{name}'")
                return None
            
            # Installation.location() returns LocationResult which has offset/size as fields
            locations = self.installation.location(name, ResourceType.TPC, texture_search_locs)
            if locations:
                loc = locations[0]
                # Create context with EXACT lookup information - this MUST be stored when texture loads
                context = {
                    "filepath": loc.filepath,
                    "restype": ResourceType.TPC,
                    "found": True,
                    "search_order": texture_search_locs.copy(),
                }
                RobustLogger().debug(f"_resolve_texture_location: Found '{name}' at {loc.filepath}, context prepared")
                # LocationResult has: filepath (Path field), offset (int field), size (int field)
                return (str(loc.filepath), loc.offset, loc.size, context)
            # Create context for "not found" case - MUST return context even when not found
            context = {
                "filepath": None,
                "found": False,
                "restype": ResourceType.TPC,
                "search_order": texture_search_locs.copy(),
            }
            # Store lookup info immediately for "not found" case
            self.texture_lookup_info[name] = context.copy()
            RobustLogger().debug(f"_resolve_texture_location: '{name}' not found, context prepared and stored")
            # Return None to indicate not found, but context is already stored in texture_lookup_info
            # The async_loader will need to retrieve it from there
            return None
        
        def _resolve_model_location(name: str) -> tuple[tuple[str, int, int] | None, tuple[str, int, int] | None]:
            """Resolve model file locations in main thread using Installation ONLY.
            
            Returns ((mdl_path, offset, size), (mdx_path, offset, size)) or (None, None).
            """
            nonlocal _cached_capsules
            if self.installation is None:
                return (None, None)
            
            # Cache capsules list for this scene (avoids repeated calls to capsules())
            if _cached_capsules is None and self._module is not None:
                module_capsules = self._module.capsules()
                _cached_capsules = list(module_capsules) if module_capsules else []
            
            capsules = _cached_capsules or []
            
            # Installation.location() returns list[LocationResult] with offset/size fields
            mdl_locs = self.installation.location(name, ResourceType.MDL, model_search_locs, capsules=capsules)
            mdx_locs = self.installation.location(name, ResourceType.MDX, model_search_locs, capsules=capsules)
            
            mdl_loc = None
            mdx_loc = None
            
            if mdl_locs:
                loc = mdl_locs[0]
                mdl_loc = (str(loc.filepath), loc.offset, loc.size)
            
            if mdx_locs:
                loc = mdx_locs[0]
                mdx_loc = (str(loc.filepath), loc.offset, loc.size)
            
            return (mdl_loc, mdx_loc)
        
        self.async_loader: AsyncResourceLoader = AsyncResourceLoader(
            texture_location_resolver=_resolve_texture_location,
            model_location_resolver=_resolve_model_location,
        )
        self.async_loader.start()
        self._pending_texture_futures: dict[str, Any] = {}  # name -> Future
        self._pending_model_futures: dict[str, Any] = {}  # name -> Future

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
    
    def __del__(self):
        """Cleanup async resources when scene is destroyed."""
        try:
            if hasattr(self, "async_loader") and self.async_loader is not None:
                self.async_loader.shutdown(wait=False)
                RobustLogger().debug("Scene cleanup: shutdown async loader")
        except Exception:  # noqa: BLE001, S110
            pass  # Don't raise exceptions in __del__

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
        instance: GITCreature | None = None,
        utc: UTC | None = None,
        *,
        sync: bool = False,
    ) -> RenderObject:
        """Get a RenderObject for a creature.
        
        Args:
            instance: Optional GITCreature instance to get the UTC from.
            utc: Optional UTC object to use directly.
            sync: If True, force synchronous model loading (required for hook finding).
        """
        assert self.installation is not None
        try:
            if instance is not None and utc is None:
                utc = self._resource_from_gitinstance(instance, self.module.creature)
            if utc is None:
                if instance is not None:
                    RobustLogger().warning(f"Could not get UTC for GITCreature instance '{instance.identifier()}', not found in mod/override.")
                else:
                    RobustLogger().warning("Could not get UTC for GITCreature, no instance provided.")
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

            # Use synchronous model loading for hook finding to ensure model is loaded
            body_model_obj: Model = self.model_sync(body_model) if sync else self.model(body_model)
            head_hook: Node | None = body_model_obj.find("headhook")
            if head_model and head_hook:
                head_obj = RenderObject(head_model, override_texture=head_texture)
                head_obj.set_transform(head_hook.global_transform())
                obj.children.append(head_obj)

            rhand_hook: Node | None = body_model_obj.find("rhand")
            if rhand_model and rhand_hook:
                rhand_obj = RenderObject(rhand_model)
                rhand_obj.set_transform(rhand_hook.global_transform())
                obj.children.append(rhand_obj)
            lhand_hook: Node | None = body_model_obj.find("lhand")
            if lhand_model and lhand_hook:
                lhand_obj = RenderObject(lhand_model)
                lhand_obj.set_transform(lhand_hook.global_transform())
                obj.children.append(lhand_obj)
            if head_hook is None:
                mask_hook = body_model_obj.find("gogglehook")
            elif head_model:
                head_model_obj: Model = self.model_sync(head_model) if sync else self.model(head_model)
                mask_hook = head_model_obj.find("gogglehook")
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

    def jump_to_entry_location(self):
        if self._module is None:
            self.camera.x = 0
            self.camera.y = 0
            self.camera.z = 0
        else:
            point: Vector3 = self._get_ifo().entry_position
            self.camera.x = point.x
            self.camera.y = point.y
            self.camera.z = point.z + 1.8
    
    def invalidate_cache(self):
        """Invalidate resource caches and cancel pending async operations."""
        RobustLogger().debug("invalidate_cache: Starting cache invalidation...")
        # Cancel pending operations
        for future in self._pending_texture_futures.values():
            future.cancel()
        for future in self._pending_model_futures.values():
            future.cancel()
        
        self._pending_texture_futures.clear()
        self._pending_model_futures.clear()
        
        # Clear caches (but keep predefined models/textures)
        predefined_models: set[str] = {"waypoint", "sound", "store", "entry", "encounter", "trigger", "camera", "empty", "cursor", "unknown"}
        self.models = CaseInsensitiveDict({k: v for k, v in self.models.items() if k in predefined_models})
        
        # Log textures before clearing
        keys = list(self.textures.keys())
        RobustLogger().debug(f"invalidate_cache: Clearing {len(keys)} textures: {keys[:10]}...")
        
        self.textures = CaseInsensitiveDict({"NULL": self.textures.get("NULL", Texture.from_color())})
        
        # Clear texture tracking (will be repopulated as new model renders)
        self.requested_texture_names.clear()
        self.texture_lookup_info.clear()
        RobustLogger().debug("invalidate_cache: Invalidated resource cache and cleared texture tracking")
    
    def poll_async_resources(
        self,
        *,
        max_textures_per_frame: int = 8,
        max_models_per_frame: int = 4,
    ):
        """Poll for completed async resource loading and create OpenGL objects.
        
        MUST be called from main thread with active OpenGL context.
        This is non-blocking and processes only completed futures.
        
        Args:
            max_textures_per_frame: Max textures to upload to GPU per frame (prevents frame spikes)
            max_models_per_frame: Max models to upload to GPU per frame (prevents frame spikes)
        """
        # Fast path: nothing to poll
        if not self._pending_texture_futures and not self._pending_model_futures:
            return
        
        # Check completed texture futures (limited per frame to prevent stuttering)
        completed_textures: list[str] = []
        textures_processed = 0
        RobustLogger().debug(f"Polling for completed texture futures: {len(self._pending_texture_futures)} pending")
        future: Future[Any]
        name: str
        resource_name: str
        intermediate: Any
        error: str
        context: dict[str, Any] | None
        for name, future in self._pending_texture_futures.items():
            if textures_processed >= max_textures_per_frame:
                break  # Process more next frame
            if future.done():
                try:
                    resource_name, intermediate, error, context = future.result()
                    # ASSERT: Context MUST exist - it contains the exact lookup information
                    assert context is not None, f"Texture '{resource_name}' (key '{name}') finished loading but context is None! This is a bug - context must be provided by _resolve_texture_location."
                    
                    # If context is incomplete (empty search_order), use stored lookup_info from resolver
                    # This happens when resolver returned None (not found) - it stored lookup_info but async_loader created minimal context
                    if not context.get("search_order") and name in self.texture_lookup_info:
                        # Use the EXACT lookup info stored by resolver
                        stored_info = self.texture_lookup_info[name]
                        context = stored_info.copy()
                        RobustLogger().debug(f"Texture '{resource_name}': Using stored lookup_info from resolver (context was incomplete)")
                    
                    if error:
                        # Only log at debug level for missing textures (very common)
                        if "not found" in error:
                            RobustLogger().debug(f"Texture not found: '{resource_name}'")
                        else:
                            RobustLogger().warning(f"Async texture load failed for '{resource_name}': {error}")
                        self.textures[resource_name] = self._missing_texture  # Magenta placeholder
                        # Store EXACT lookup info from context (contains search_order and filepath=None for not found)
                        self.texture_lookup_info[resource_name] = context.copy()
                        if name != resource_name:
                            self.texture_lookup_info[name] = context.copy()
                    elif intermediate:
                        self.textures[resource_name] = create_texture_from_intermediate(intermediate)
                        RobustLogger().debug(f"Async texture '{resource_name}' finished loading and uploaded to GPU. textures keys now: {list(self.textures.keys())[:10]}...")
                        # Store EXACT lookup info from context (contains filepath, search_order, restype)
                        self.texture_lookup_info[resource_name] = context.copy()
                        if name != resource_name:
                            self.texture_lookup_info[name] = context.copy()
                        RobustLogger().debug(f"Texture '{resource_name}' lookup info stored: found={context.get('found')}, filepath={context.get('filepath')}")
                    completed_textures.append(name)
                    textures_processed += 1
                except Exception:  # noqa: BLE001
                    RobustLogger().exception(f"Error processing completed texture future for '{name}'")
                    self.textures[name] = self._missing_texture
                    # For exception case, we can't recover context - this should never happen if resolver works correctly
                    # But we must store something to satisfy the requirement that texture_lookup_info always exists
                    # This is a last resort - the resolver should have provided context
                    if name not in self.texture_lookup_info:
                        RobustLogger().error(f"Texture '{name}' exception but no context available - resolver should have provided context. This indicates a bug in _resolve_texture_location.")
                        # Fast fail: raise assertion error since we can't satisfy the requirement
                        raise AssertionError(f"Texture '{name}' has no lookup info after exception - resolver must provide context. This is a critical bug.")
                    completed_textures.append(name)
                    textures_processed += 1
        
        for name in completed_textures:
            del self._pending_texture_futures[name]
        
        # Check completed model futures (limited per frame)
        completed_models: list[str] = []
        models_processed = 0
        for name, future in self._pending_model_futures.items():
            if models_processed >= max_models_per_frame:
                break  # Process more next frame
            if future.done():
                try:
                    resource_name, intermediate, error = future.result()
                    if error:
                        # Only log at debug level for missing models
                        if "not found" in error:
                            RobustLogger().debug(f"Model not found: '{resource_name}'")
                        else:
                            RobustLogger().warning(f"Async model load failed for '{resource_name}': {error}")
                        # Load empty model as fallback
                        self.models[resource_name] = gl_load_stitched_model(
                            self,  # pyright: ignore[reportArgumentType]
                            BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                            BinaryReader.from_bytes(EMPTY_MDX_DATA),
                        )
                    elif intermediate:
                        self.models[resource_name] = create_model_from_intermediate(self, intermediate)
                    completed_models.append(name)
                    models_processed += 1
                except Exception:  # noqa: BLE001
                    RobustLogger().exception(f"Error processing completed model future for '{name}'")
                    self.models[name] = gl_load_stitched_model(
                        self,  # pyright: ignore[reportArgumentType]
                        BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                        BinaryReader.from_bytes(EMPTY_MDX_DATA),
                    )
                    completed_models.append(name)
                    models_processed += 1
        
        for name in completed_models:
            del self._pending_model_futures[name]

    def texture(
        self,
        name: str,
        *,
        lightmap: bool = False,
    ) -> Texture:
        type_name: Literal["lightmap", "texture"] = "lightmap" if lightmap else "texture"
        RobustLogger().debug(f"scene.texture() called for {type_name} '{name}' - this is where texture is requested for rendering")
        
        # Track this texture name as requested (happens during rendering, no additional traversal)
        # Track BOTH regular textures and lightmaps (but not NULL)
        if name and name != "NULL":
            self.requested_texture_names.add(name)
            RobustLogger().debug(f"Tracked texture name '{name}' as requested for rendering (requested_texture_names now has {len(self.requested_texture_names)} textures)")
        
        # Already cached?
        if name in self.textures:
            tex = self.textures[name]
            if tex is self._missing_texture and lightmap:
                return self._missing_lightmap
            # ASSERT: Lookup info MUST exist for cached texture - it was stored when texture was loaded
            assert name in self.texture_lookup_info, (
                f"Texture '{name}' is cached in self.textures but has NO lookup info in texture_lookup_info! "
                f"This is a critical bug - lookup info MUST be stored when texture is loaded. "
                f"Available texture keys: {list(self.textures.keys())[:10]}, "
                f"Available lookup keys: {list(self.texture_lookup_info.keys())[:10]}"
            )
            lookup_info = self.texture_lookup_info[name]
            RobustLogger().debug(f"Texture '{name}' returned from cache (already loaded), lookup_info: found={lookup_info.get('found')}, filepath={lookup_info.get('filepath')}")
            return tex
        
        # Already loading?
        if name in self._pending_texture_futures:
            # Return placeholder while loading
            RobustLogger().debug(f"Texture '{name}' already pending async load, returning placeholder")
            return self._loading_texture
        
        # Start async loading if location resolver available
        if self.async_loader.texture_location_resolver is not None:
            RobustLogger().debug(f"Starting async load for {type_name} '{name}'")
            future = self.async_loader.load_texture_async(name)
            self._pending_texture_futures[name] = future
            # Return gray placeholder immediately
            return self._loading_texture
        
        # Fallback to synchronous loading (e.g., if process pools unavailable)
        type_name = "lightmap" if lightmap else "texture"
        tpc: TPC | None = None
        try:
            # Check the textures linked to the module first
            if self._module is not None:
                RobustLogger().debug(f"Locating {type_name} '{name}' in module '{self.module.root()}'")
                module_tex: ModuleResource[TPC] | None = self.module.texture(name)
                if module_tex is not None:
                    RobustLogger().debug(f"Loading {type_name} '{name}' from module '{self.module.root()}'")
                    tpc = module_tex.resource()
                    # Store EXACT lookup info for module textures
                    module_filepath = module_tex.active()  # Returns Path | None
                    self.texture_lookup_info[name] = {
                        "filepath": module_filepath,
                        "restype": ResourceType.TPC,
                        "found": True,
                        "search_order": [SearchLocation.MODULES],  # Module textures come from modules
                    }
                    RobustLogger().debug(f"Sync module texture load: Found '{name}' in module at {module_filepath}, stored in texture_lookup_info")

            # Otherwise just search through all relevant game files
            # Use resource() instead of texture() - same single lookup but returns filepath too
            if tpc is None and self.installation is not None:
                RobustLogger().debug(f"Locating and loading {type_name} '{name}' from override/bifs/texturepacks...")
                search_order: list[SearchLocation] = [  # DO NOT MODIFY THIS ORDER
                    SearchLocation.OVERRIDE,
                    SearchLocation.CUSTOM_MODULES,
                    SearchLocation.MODULES,
                    SearchLocation.TEXTURES_GUI,
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.CHITIN,
                ]
                result = self.installation.resource(name, ResourceType.TPC, search_order)
                if result is not None:
                    from pykotor.resource.formats.tpc import read_tpc
                    tpc = read_tpc(result.data)
                    # Store EXACT lookup info
                    self.texture_lookup_info[name] = {
                        "filepath": result.filepath,
                        "restype": ResourceType.TPC,
                        "found": True,
                        "search_order": search_order.copy(),  # Store search order used
                    }
                    RobustLogger().debug(f"Sync texture load: Found '{name}' at {result.filepath}, stored in texture_lookup_info")
                else:
                    # Store EXACT lookup info for "not found" case
                    self.texture_lookup_info[name] = {
                        "filepath": None,
                        "found": False,
                        "restype": ResourceType.TPC,
                        "search_order": search_order.copy(),  # Store search order used even when not found
                    }
                    RobustLogger().debug(f"Sync texture load: '{name}' not found, stored in texture_lookup_info")
            if tpc is None:
                RobustLogger().warning(f"MISSING {type_name.upper()}: '{name}'")
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Could not load {type_name} '{name}'.")
            # Store "not found" lookup info for error case (if not already stored)
            if name not in self.texture_lookup_info:
                self.texture_lookup_info[name] = {
                    "filepath": None,
                    "found": False,
                    "restype": ResourceType.TPC,
                    "search_order": [],  # Unknown search order for error case
                }

        if tpc is None:
            self.textures[name] = self._missing_texture
            return self._missing_lightmap if lightmap else self._missing_texture
        
        self.textures[name] = Texture.from_tpc(tpc)
        return self.textures[name]

    def model_sync(
        self,
        name: str,
    ) -> Model:
        """Load a model synchronously, bypassing async loading.
        
        This is useful when you need the model immediately (e.g., for finding hooks).
        The model will be cached for future use.
        
        Args:
            name: The model name to load.
            
        Returns:
            The loaded Model object.
        """
        # Already cached?
        if name in self.models:
            return self.models[name]
        
        # Cancel any pending async load for this model
        if name in self._pending_model_futures:
            self._pending_model_futures[name].cancel()
            del self._pending_model_futures[name]
        
        # Handle predefined models
        predefined_models = {
            "waypoint": (WAYPOINT_MDL_DATA, WAYPOINT_MDX_DATA),
            "sound": (SOUND_MDL_DATA, SOUND_MDX_DATA),
            "store": (STORE_MDL_DATA, STORE_MDX_DATA),
            "entry": (ENTRY_MDL_DATA, ENTRY_MDX_DATA),
            "encounter": (ENCOUNTER_MDL_DATA, ENCOUNTER_MDX_DATA),
            "trigger": (TRIGGER_MDL_DATA, TRIGGER_MDX_DATA),
            "camera": (CAMERA_MDL_DATA, CAMERA_MDX_DATA),
            "empty": (EMPTY_MDL_DATA, EMPTY_MDX_DATA),
            "cursor": (CURSOR_MDL_DATA, CURSOR_MDX_DATA),
            "unknown": (UNKNOWN_MDL_DATA, UNKNOWN_MDX_DATA),
        }
        
        if name in predefined_models:
            mdl_data, mdx_data = predefined_models[name]
            try:
                mdl_reader: BinaryReader = BinaryReader.from_bytes(mdl_data, 12)
                mdx_reader: BinaryReader = BinaryReader.from_bytes(mdx_data)
                model: Model = gl_load_stitched_model(self, mdl_reader, mdx_reader)  # pyright: ignore[reportArgumentType]
                self.models[name] = model
                return model
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Could not load predefined model '{name}'.")
        
        # Synchronous loading from installation
        fallback_mdl_data: bytes = EMPTY_MDL_DATA
        fallback_mdx_data: bytes = EMPTY_MDX_DATA
        
        if self.installation is not None:
            capsules: list[ModulePieceResource] = [] if self._module is None else self.module.capsules()
            mdl_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=capsules)
            mdx_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=capsules)
            if mdl_search is not None and mdx_search is not None:
                fallback_mdl_data = mdl_search.data
                fallback_mdx_data = mdx_search.data
            else:
                RobustLogger().warning(f"Model '{name}' not found in installation (MDL: {mdl_search is not None}, MDX: {mdx_search is not None})")

        try:
            mdl_reader = BinaryReader.from_bytes(fallback_mdl_data, 12)
            mdx_reader = BinaryReader.from_bytes(fallback_mdx_data)
            model = gl_load_stitched_model(self, mdl_reader, mdx_reader)  # pyright: ignore[reportArgumentType]
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Could not load model '{name}'.")
            model = gl_load_stitched_model(
                self,  # pyright: ignore[reportArgumentType]
                BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                BinaryReader.from_bytes(EMPTY_MDX_DATA),
            )

        self.models[name] = model
        return model

    def model(  # noqa: C901, PLR0912
        self,
        name: str,
    ) -> Model:
        # Already cached?
        if name in self.models:
            return self.models[name]
        
        # Special/predefined models - load synchronously
        predefined_models = {
            "waypoint": (WAYPOINT_MDL_DATA, WAYPOINT_MDX_DATA),
            "sound": (SOUND_MDL_DATA, SOUND_MDX_DATA),
            "store": (STORE_MDL_DATA, STORE_MDX_DATA),
            "entry": (ENTRY_MDL_DATA, ENTRY_MDX_DATA),
            "encounter": (ENCOUNTER_MDL_DATA, ENCOUNTER_MDX_DATA),
            "trigger": (TRIGGER_MDL_DATA, TRIGGER_MDX_DATA),
            "camera": (CAMERA_MDL_DATA, CAMERA_MDX_DATA),
            "empty": (EMPTY_MDL_DATA, EMPTY_MDX_DATA),
            "cursor": (CURSOR_MDL_DATA, CURSOR_MDX_DATA),
            "unknown": (UNKNOWN_MDL_DATA, UNKNOWN_MDX_DATA),
        }
        
        if name in predefined_models:
            mdl_data, mdx_data = predefined_models[name]
            try:
                mdl_reader: BinaryReader = BinaryReader.from_bytes(mdl_data, 12)
                mdx_reader: BinaryReader = BinaryReader.from_bytes(mdx_data)
                model: Model = gl_load_stitched_model(self, mdl_reader, mdx_reader)  # pyright: ignore[reportArgumentType]
                self.models[name] = model
                return model
            except Exception:  # noqa: BLE001
                RobustLogger().exception(f"Could not load predefined model '{name}'.")
                # Fall through to empty model
        
        # Already loading?
        if name in self._pending_model_futures:
            # Return empty model placeholder while loading
            if "empty" not in self.models:
                empty_model = gl_load_stitched_model(
                    self,  # pyright: ignore[reportArgumentType]
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )
                self.models["empty"] = empty_model
            return self.models["empty"]
        
        # Start async loading if location resolver available
        if self.async_loader.model_location_resolver is not None:
            future = self.async_loader.load_model_async(name)
            self._pending_model_futures[name] = future
            # Return empty model immediately as placeholder
            if "empty" not in self.models:
                empty_model = gl_load_stitched_model(
                    self,  # pyright: ignore[reportArgumentType]
                    BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                    BinaryReader.from_bytes(EMPTY_MDX_DATA),
                )
                self.models["empty"] = empty_model
            return self.models["empty"]
        
        # Fallback to synchronous loading
        fallback_mdl_data: bytes = EMPTY_MDL_DATA
        fallback_mdx_data: bytes = EMPTY_MDX_DATA
        
        if self.installation is not None:
            capsules: list[ModulePieceResource] = [] if self._module is None else self.module.capsules()
            mdl_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDL, SEARCH_ORDER, capsules=capsules)
            mdx_search: ResourceResult | None = self.installation.resource(name, ResourceType.MDX, SEARCH_ORDER, capsules=capsules)
            if mdl_search is not None and mdx_search is not None:
                fallback_mdl_data = mdl_search.data
                fallback_mdx_data = mdx_search.data

        try:
            mdl_reader = BinaryReader.from_bytes(fallback_mdl_data, 12)
            mdx_reader = BinaryReader.from_bytes(fallback_mdx_data)
            model = gl_load_stitched_model(self, mdl_reader, mdx_reader)
        except Exception:  # noqa: BLE001
            RobustLogger().warning(f"Could not load model '{name}'.")
            model = gl_load_stitched_model(
                self,
                BinaryReader.from_bytes(EMPTY_MDL_DATA, 12),
                BinaryReader.from_bytes(EMPTY_MDX_DATA),
            )

        self.models[name] = model
        return model
