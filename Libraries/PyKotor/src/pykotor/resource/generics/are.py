from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, GFFStruct, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector2

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

from pykotor.resource.generics.base import GenericBase


class ARE(GenericBase):
    """Stores static area data.
    
    ARE files are GFF-based format files that store static area information including
    lighting, fog, grass, weather, script hooks, and map data. ARE files use the GFF
    binary format with a specific structure defined by the ARE content type.
    
    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x00508c50 - CSWSArea::LoadAreaHeader (5246 bytes, 624 lines)
                - Main ARE GFF parser entry point
                - Loads area header information from GFF structure
                - Function signature: LoadAreaHeader(CSWSArea* this, CResStruct* param_1)
                - Called from LoadArea (0x0050e190)
            - Reads area header fields:
                - ID (INT) - area ID
                - Creator_ID (INT) - creator ID
                - Version (DWORD) - area version
                - Comments (CExoString) - area comments
                - Expansion_List (GFFList) - expansion list:
                    - Expansion_Name (CExoLocString) - expansion name
                    - Expansion_ID (INT) - expansion ID
                - OnHeartbeat (CResRef) - heartbeat script
                - OnUserDefined (CResRef) - user-defined script
                - OnEnter (CResRef) - enter script
                - OnExit (CResRef) - exit script
                - Name (CExoLocString) - localized area name
                - Tag (CExoString) - area tag (lowercased)
                - Flags (DWORD) - area flags
                - CameraStyle (INT) - camera style
                - DefaultEnvMap (CResRef) - default environment map
                - And many more fields for lighting, fog, grass, weather, etc.
        KotOR II / TSL (swkotor2.exe):
            - Functionally identical to K1 implementation
            - Same GFF structure and parsing logic

    Attributes:
    ----------
        tag: "Tag" field.
        name: "Name" field.
        alpha_test: "AlphaTest" field.
        camera_style: "CameraStyle" field.
        default_envmap: "DefaultEnvMap" field.
        grass_texture: "Grass_TexName" field.
        grass_density: "Grass_Density" field.
        grass_size: "Grass_QuadSize" field.
        grass_prob_ll: "Grass_Prob_LL" field.
        grass_prob_lr: "Grass_Prob_LR" field.
        grass_prob_ul: "Grass_Prob_UL" field.
        grass_prob_ur: "Grass_Prob_UR" field.
        fog_enabled: "SunFogOn" field.
        fog_near: "SunFogNear" field.
        fog_far: "SunFogFar" field.
        shadows: "SunShadows" field.
        shadow_opacity: "ShadowOpacity" field.
        wind_power: "WindPower" field.
        unescapable: "Unescapable" field.
        disable_transit: "DisableTransit" field.
        stealth_xp: "StealthXPEnabled" field.
        stealth_xp_loss: "StealthXPLoss" field.
        stealth_xp_max: "StealthXPMax" field.
        on_enter: "OnEnter" field.
        on_exit: "OnExit" field.
        on_heartbeat: "OnHeartbeat" field.
        on_user_defined: "OnUserDefined" field.
        sun_ambient: "SunAmbientColor" field.
        sun_diffuse: "SunDiffuseColor" field.
        dynamic_light: "DynAmbientColor" field.
        fog_color: "SunFogColor" field.
        grass_ambient: "Grass_Ambient" field.
        grass_diffuse: "Grass_Diffuse" field.

        dirty_argb_1: "DirtyARGBOne" field. KotOR 2 Only.
        dirty_argb_2: "DirtyARGBTwo" field. KotOR 2 Only.
        dirty_argb_3: "DirtyARGBThree" field. KotOR 2 Only.
        grass_emissive: "Grass_Emissive" field. KotOR 2 Only.
        chance_rain: "ChanceRain" field. KotOR 2 Only.
        chance_snow: "ChanceSnow" field. KotOR 2 Only.
        chance_lightning: "ChanceLightning" field. KotOR 2 Only.
        dirty_size_1: "DirtySizeOne" field. KotOR 2 Only.
        dirty_formula_1: "DirtyFormulaOne" field. KotOR 2 Only.
        dirty_func_1: "DirtyFuncOne" field. KotOR 2 Only.
        dirty_size_2: "DirtySizeTwo" field. KotOR 2 Only.
        dirty_formula_2: "DirtyFormulaTwo" field. KotOR 2 Only.
        dirty_func_2: "DirtyFuncTwo" field. KotOR 2 Only.
        dirty_size_3: "DirtySizeThree" field. KotOR 2 Only.
        dirty_formula_3: "DirtyFormulaThre" field. KotOR 2 Only.
        dirty_func_3: "DirtyFuncThree" field. KotOR 2 Only.

        comment: "Comments" field. Used in toolset only.

        unused_id: "ID" field. Not used by the game engine.
        creator_id: "Creator_ID" field. Not used by the game engine.
        flags: "Flags" field. Not used by the game engine.
        mod_spot_check: "ModSpotCheck" field. Not used by the game engine.
        mod_listen_check: "ModListenCheck" field. Not used by the game engine.
        moon_ambient: "MoonAmbientColor" field. Not used by the game engine.
        moon_diffuse: "MoonDiffuseColor" field. Not used by the game engine.
        moon_fog: "MoonFogOn" field. Not used by the game engine.
        moon_fog_near: "MoonFogNear" field. Not used by the game engine.
        moon_fog_far: "MoonFogFar" field. Not used by the game engine.
        moon_fog_color: "MoonFogColor" field. Not used by the game engine.
        moon_shadows: "MoonShadows" field. Not used by the game engine.
        is_night: "IsNight" field. Not used by the game engine.
        lighting_scheme: "LightingScheme" field. Not used by the game engine.
        day_night: "DayNightCycle" field. Not used by the game engine.
        loadscreen_id: "LoadScreenID" field. Not used by the game engine.
        no_rest: "NoRest" field. Not used by the game engine.
        no_hang_back: "NoHangBack" field. Not used by the game engine.
        player_only: "PlayerOnly" field. Not used by the game engine.
        player_vs_player: "PlayerVsPlayer" field. Not used by the game engine.

        NOTE on engine usage claims:
        We do not claim a field is "unused by the engine" unless verified against engine implementations.

        Verified by ` + `
        - Moon lighting/fog fields are read from ARE and used by the day/night codepath.
        - `IsNight` / `DayNightCycle` affect whether/when the engine updates day/night state.
        - `SunAmbientColor`, `SunDiffuseColor`, `DynAmbientColor` are used for lighting setup.

        See also:
        - ` (`CSW*Area` load from ARE + area scene setup)
        - ` (`CSWArea` struct fields: `moon_*`, `sun_*`, `day_night_cycle`, `is_night`, `dynamic_ambient_color`)
    """

    BINARY_TYPE = ResourceType.ARE

    def __init__(self):
        super().__init__()
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:13
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:140
        # Alpha test threshold for transparency rendering (default 0.2)
        self.alpha_test: float = 0.0
        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:14
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:145
        # Index into camerastyle.2da for camera behavior
        self.camera_style: int = 0

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:15-17
        # Weather effect probabilities (KotOR 2 only, 0-100)
        self.chance_lightning: int = 0
        self.chance_snow: int = 0
        self.chance_rain: int = 0

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:18
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:150
        # Module designer comments (toolset only, not used by engine)
        self.comment: str = ""

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:21
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:166
        # ResRef of default environment map texture (cube map)
        self.default_envmap: ResRef = ResRef.from_blank()

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:34
        # Disable area transitions flag
        self.disable_transit: bool = False

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:35,73-75
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:171,244-246
        # Lighting colors (RGB integers)
        self.dynamic_light: Color = Color.BLACK
        self.sun_ambient: Color = Color.BLACK
        self.sun_diffuse: Color = Color.BLACK
        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:69,79
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:251,281
        # Shadow rendering properties
        self.shadow_opacity: int = 0
        self.shadows: bool = False

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:75-78
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:246-250
        # Fog rendering properties
        self.fog_color: Color = Color.BLACK
        self.fog_near: float = 0
        self.fog_far: float = 0
        self.fog_enabled: bool = False

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:22,25,28,31
        # First dirty/weather effect parameters (KotOR 2 only)
        self.dirty_argb_1: Color = Color.BLACK
        self.dirty_func_1: int = 0
        self.dirty_size_1: int = 0
        self.dirty_formula_1: int = 0

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:24,27,30,32
        # Second dirty/weather effect parameters (KotOR 2 only)
        self.dirty_argb_2: Color = Color.BLACK
        self.dirty_func_2: int = 0
        self.dirty_size_2: int = 0
        self.dirty_formula_2: int = 0

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:23,26,29,33
        # Third dirty/weather effect parameters (KotOR 2 only)
        self.dirty_argb_3: Color = Color.BLACK
        self.dirty_func_3: int = 0
        self.dirty_size_3: int = 0
        self.dirty_formula_3: int = 0

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:37-46
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:188-200
        # Grass rendering properties
        self.grass_ambient: Color = Color.BLACK
        self.grass_diffuse: Color = Color.BLACK
        self.grass_emissive: Color = Color.BLACK
        self.grass_density: float = 0.0
        self.grass_size: float = 0.0
        self.grass_prob_ll: float = 0.0
        self.grass_prob_lr: float = 0.0
        self.grass_prob_ul: float = 0.0
        self.grass_prob_ur: float = 0.0
        self.grass_texture: ResRef = ResRef.from_blank()

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:83
        # Wind strength for area (Still=0, Weak=1, Strong=2)
        self.wind_power: AREWindPower = AREWindPower.Still

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:63-66
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:122
        # Area script hooks (ResRefs)
        self.on_enter: ResRef = ResRef.from_blank()
        self.on_exit: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:70-72
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:286-297
        # Stealth XP mechanics
        self.stealth_xp: bool = False
        self.stealth_xp_loss: int = 0
        self.stealth_xp_max: int = 0

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:60,80
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:258
        # Area identification
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.tag: str = ""
        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:81
        # Area cannot be escaped from (no transitions)
        self.unescapable: bool = False

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:84-94
        # Area map data (coordinate mapping)
        self.map_original_struct_id: int = 0
        self.map_point_1: Vector2 = Vector2.from_null()
        self.map_point_2: Vector2 = Vector2.from_null()
        self.world_point_1: Vector2 = Vector2.from_null()
        self.world_point_2: Vector2 = Vector2.from_null()
        self.map_res_x: int = 0
        self.map_zoom: int = 0
        self.north_axis: ARENorthAxis = ARENorthAxis.PositiveX

        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:96
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:120
        # List of room definitions (audio, weather, force rating)
        self.rooms: list[ARERoom] = []

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:82
        # ARE file format version
        self.version: int = 0

        # Deprecated fields (not used by KotOR engine, from NWN):
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:19-20,36,47-68
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:155-276 (various deprecated flags)
        self.unused_id: int = 0
        self.creator_id: int = 0
        self.flags: int = 0
        self.mod_spot_check: int = 0
        self.mod_listen_check: int = 0
        self.moon_ambient: int = 0
        self.moon_diffuse: int = 0
        self.moon_fog: int = 0
        self.moon_fog_near: float = 0.0
        self.moon_fog_far: float = 0.0
        self.moon_fog_color: int = 0
        self.moon_shadows: int = 0
        self.is_night: int = 0
        self.lighting_scheme: int = 0
        self.day_night: int = 0
        self.loadscreen_id: int = 0
        self.no_rest: int = 0
        self.no_hang_back: int = 0
        self.player_only: int = 0
        self.player_vs_player: int = 0


class ARERoom:
    """Represents a room definition within an area.
    
    Rooms define audio properties, weather behavior, and force rating for specific
    regions within an area. Rooms are referenced by VIS (visibility) files and
    used for audio occlusion and weather control.
    
    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x00508c50 - CSWSArea::LoadAreaHeader (5246 bytes, 624 lines)
                - Loads Rooms list from ARE GFF structure
                - Function signature: LoadAreaHeader(CSWSArea* this, CResStruct* param_1)
                - Called from LoadArea (0x0050e190)
            - Reads Rooms (GFFList) at line 349:
                - RoomName (CExoString) - room name identifier
                - EnvAudio (INT) - environment audio ID
                - AmbientScale (FLOAT) - ambient sound scale
                - PartSounds (GFFList) - particle sounds list:
                    - Looping (BYTE) - looping flag
        KotOR II / TSL (swkotor2.exe):
            - Functionally identical to K1 implementation
            - Same GFF structure and parsing logic

        
    Attributes:
    ----------
        name: Room name identifier
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/ARE.cs:105 (RoomName String property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleRoom.ts (room name)
            Unique identifier for this room (referenced by VIS files)
            
        weather: Disable weather flag for this room
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/ARE.cs:102 (DisableWeather Byte property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleArea.ts:463 (room_struct.set_uint8("DisableWeather", room.weather)) (room_struct.set_uint8("DisableWeather", room.weather)
            If True, weather effects are disabled in this room (KotOR 2 only)
            
        env_audio: Environment audio index
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/ARE.cs:103 (EnvAudio Int32 property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleArea.ts:138 (audio.environmentAudio = 0)
            Index into environment audio system for room acoustics
            
        force_rating: Force rating modifier for this room
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/ARE.cs:104 (ForceRating Int32 property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleArea.ts:464 (room_struct.set_int32("ForceRating", room.force_rating)) (room_struct.set_int32("ForceRating", room.force_rating)
            Force rating modifier applied in this room (KotOR 2 only)
            
        ambient_scale: Ambient audio scaling factor
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/ARE.cs:101 (AmbientScale Single property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleArea.ts:459 (room_struct.set_single("AmbientScale", room.ambient_scale)) (room_struct.set_single("AmbientScale", room.ambient_scale)
            Scaling factor for ambient audio volume in this room
    """
    def __init__(
        self,
        name: str,
        weather: bool,
        env_audio: int,
        force_rating: int,
        ambient_scale: float,
    ):
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:105
        # Room name identifier (referenced by VIS files)
        self.name: str = name
        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:102
        # Disable weather flag (KotOR 2 only)
        self.weather: bool = weather
        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:103
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleArea.ts:138
        # Environment audio index
        self.env_audio: int = env_audio
        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:104
        # Force rating modifier (KotOR 2 only)
        self.force_rating: int = force_rating
        
        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorARE/ARE.cs:101
        # Ambient audio scaling factor
        self.ambient_scale: float = ambient_scale


class AREWindPower(IntEnum):
    Still = 0
    Weak = 1
    Strong = 2


class ARENorthAxis(IntEnum):
    PositiveY = 0
    NegativeY = 1
    PositiveX = 2
    NegativeX = 3


def construct_are(
    gff: GFF,
) -> ARE:
    """Constructs an ARE object from a GFF file.

    Args:
    ----
        gff: GFF - The GFF file object

    Returns:
    -------
        ARE - The constructed ARE object

    Processing Logic:
    ----------------
        - Acquires values from the GFF root node and assigns them to ARE properties
        - Handles color values as special case, converting to Color objects
        - All other values assigned directly from GFF.
    """
    are = ARE()

    root = gff.root
    map_struct = root.acquire("Map", GFFStruct())
    are.map_original_struct_id = map_struct.struct_id

    are.north_axis = ARENorthAxis(
        map_struct.acquire("NorthAxis", 0),
    )
    are.map_zoom = map_struct.acquire("MapZoom", 0)
    are.map_res_x = map_struct.acquire("MapResX", 0)
    are.map_point_1 = Vector2(
        map_struct.acquire("MapPt1X", 0.0),
        map_struct.acquire("MapPt1Y", 0.0),
    )
    are.map_point_2 = Vector2(
        map_struct.acquire("MapPt2X", 0.0),
        map_struct.acquire("MapPt2Y", 0.0),
    )
    are.world_point_1 = Vector2(
        map_struct.acquire("WorldPt1X", 0.0),
        map_struct.acquire("WorldPt1Y", 0.0),
    )
    are.world_point_2 = Vector2(
        map_struct.acquire("WorldPt2X", 0.0),
        map_struct.acquire("WorldPt2Y", 0.0),
    )
    are.version = root.acquire("Version", 0)
    are.tag = root.acquire("Tag", "")
    are.name = root.acquire("Name", LocalizedString.from_invalid())
    are.comment = root.acquire("Comments", "")
    are.alpha_test = root.acquire("AlphaTest", 0.0)
    are.camera_style = root.acquire("CameraStyle", 0)
    are.default_envmap = root.acquire("DefaultEnvMap", ResRef.from_blank())
    are.grass_texture = root.acquire("Grass_TexName", ResRef.from_blank())
    are.grass_density = root.acquire("Grass_Density", 0.0)
    are.grass_size = root.acquire("Grass_QuadSize", 0.0)
    are.grass_prob_ll = root.acquire("Grass_Prob_LL", 0.0)
    are.grass_prob_lr = root.acquire("Grass_Prob_LR", 0.0)
    are.grass_prob_ul = root.acquire("Grass_Prob_UL", 0.0)
    are.grass_prob_ur = root.acquire("Grass_Prob_UR", 0.0)
    are.fog_enabled = bool(root.acquire("SunFogOn", 0))
    are.fog_near = root.acquire("SunFogNear", 0.0)
    are.fog_far = root.acquire("SunFogFar", 0.0)
    are.shadows = bool(root.acquire("SunShadows", 0))
    are.shadow_opacity = root.acquire("ShadowOpacity", 0)
    are.wind_power = AREWindPower(root.acquire("WindPower", 0))
    are.unescapable = bool(root.acquire("Unescapable", 0))
    are.disable_transit = bool(root.acquire("DisableTransit", 0))
    are.stealth_xp = bool(root.acquire("StealthXPEnabled", 0))
    are.stealth_xp_loss = root.acquire("StealthXPLoss", 0)
    are.stealth_xp_max = root.acquire("StealthXPMax", 0)
    are.on_enter = root.acquire("OnEnter", ResRef.from_blank())
    are.on_exit = root.acquire("OnExit", ResRef.from_blank())
    are.on_heartbeat = root.acquire("OnHeartbeat", ResRef.from_blank())
    are.on_user_defined = root.acquire("OnUserDefined", ResRef.from_blank())
    are.chance_rain = root.acquire("ChanceRain", 0)
    are.chance_snow = root.acquire("ChanceSnow", 0)
    are.chance_lightning = root.acquire("ChanceLightning", 0)
    are.dirty_size_1 = root.acquire("DirtySizeOne", 0)
    are.dirty_formula_1 = root.acquire("DirtyFormulaOne", 0)
    are.dirty_func_1 = root.acquire("DirtyFuncOne", 0)
    are.dirty_size_2 = root.acquire("DirtySizeTwo", 0)
    are.dirty_formula_2 = root.acquire("DirtyFormulaTwo", 0)
    are.dirty_func_2 = root.acquire("DirtyFuncTwo", 0)
    are.dirty_size_3 = root.acquire("DirtySizeThree", 0)
    are.dirty_formula_3 = root.acquire("DirtyFormulaThre", 0)
    are.dirty_func_3 = root.acquire("DirtyFuncThree", 0)
    are.unused_id = root.acquire("ID", 0)
    are.creator_id = root.acquire("Creator_ID", 0)
    are.flags = root.acquire("Flags", 0)
    are.mod_spot_check = root.acquire("ModSpotCheck", 0)
    are.mod_listen_check = root.acquire("ModListenCheck", 0)
    are.moon_ambient = root.acquire("MoonAmbientColor", 0)
    are.moon_diffuse = root.acquire("MoonDiffuseColor", 0)
    are.moon_fog = root.acquire("MoonFogOn", 0)
    are.moon_fog_near = root.acquire("MoonFogNear", 0.0)
    are.moon_fog_far = root.acquire("MoonFogFar", 0.0)
    are.moon_fog_color = root.acquire("MoonFogColor", 0)
    are.moon_shadows = root.acquire("MoonShadows", 0)
    are.is_night = root.acquire("IsNight", 0)
    are.lighting_scheme = root.acquire("LightingScheme", 0)
    are.day_night = root.acquire("DayNightCycle", 0)
    are.loadscreen_id = root.acquire("LoadScreenID", 0)
    are.no_rest = root.acquire("NoRest", 0)
    are.no_hang_back = root.acquire("NoHangBack", 0)
    are.player_only = root.acquire("PlayerOnly", 0)
    are.player_vs_player = root.acquire("PlayerVsPlayer", 0)

    are.sun_ambient = Color.from_rgb_integer(root.acquire("SunAmbientColor", 0))
    are.sun_diffuse = Color.from_rgb_integer(root.acquire("SunDiffuseColor", 0))
    are.dynamic_light = Color.from_rgb_integer(root.acquire("DynAmbientColor", 0))
    are.fog_color = Color.from_rgb_integer(root.acquire("SunFogColor", 0))
    are.grass_ambient = Color.from_rgb_integer(root.acquire("Grass_Ambient", 0))
    are.grass_diffuse = Color.from_rgb_integer(root.acquire("Grass_Diffuse", 0))

    are.grass_emissive = Color.from_rgb_integer(root.acquire("Grass_Emissive", 0))
    are.dirty_argb_1 = Color.from_rgb_integer(root.acquire("DirtyARGBOne", 0))
    are.dirty_argb_2 = Color.from_rgb_integer(root.acquire("DirtyARGBTwo", 0))
    are.dirty_argb_3 = Color.from_rgb_integer(root.acquire("DirtyARGBThree", 0))

    rooms_list = root.acquire("Rooms", GFFList())
    for room_struct in rooms_list:
        ambient_scale = room_struct.acquire("AmbientScale", 0.0)
        env_audio = room_struct.acquire("EnvAudio", 0)
        room_name = room_struct.acquire("RoomName", "")
        disable_weather = bool(room_struct.acquire("DisableWeather", 0))
        force_rating = room_struct.acquire("ForceRating", 0)
        are.rooms.append(ARERoom(room_name, disable_weather, env_audio, force_rating, ambient_scale))

    # Preserve original values for fields not in UI
    are.preserve_original()
    # Store all field values as original
    are._store_original('version', are.version)
    are._store_original('player_vs_player', are.player_vs_player)
    are._store_original('moon_fog', are.moon_fog)
    are._store_original('moon_fog_near', are.moon_fog_near)
    are._store_original('moon_fog_far', are.moon_fog_far)
    are._store_original('moon_fog_color', are.moon_fog_color)
    are._store_original('map_point_1', are.map_point_1)
    are._store_original('map_point_2', are.map_point_2)

    return are


def dismantle_are(
    are: ARE,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    """Converts an ARE structure to a GFF structure.

    Args:
    ----
        are: ARE - The ARE structure to convert
        game: Game - The game type (K1, K2, etc)
        use_deprecated: bool - Whether to include deprecated fields

    Returns:
    -------
        gff: GFF - The converted GFF structure

    Processing Logic:
    ----------------
        - Creates a new GFF structure
        - Maps ARE fields to GFF fields
        - Includes additional K2-specific fields if game is K2
        - Includes deprecated fields if use_deprecated is True
        - Returns the populated GFF structure.
    """
    gff = GFF(GFFContent.ARE)

    root = gff.root

    map_struct = root.set_struct("Map", GFFStruct(are.map_original_struct_id))
    map_struct.set_int32("MapZoom", are.map_zoom)
    map_struct.set_int32("MapResX", are.map_res_x)
    map_struct.set_int32("NorthAxis", are.north_axis.value)
    # Use original values for map points if current values are at default
    default_map_point = Vector2.from_null()
    map_pt1 = are.get_original_or_current('map_point_1', are.map_point_1, default_map_point)
    map_pt2 = are.get_original_or_current('map_point_2', are.map_point_2, default_map_point)
    map_struct.set_single("MapPt1X", map_pt1.x)
    map_struct.set_single("MapPt1Y", map_pt1.y)
    map_struct.set_single("MapPt2X", map_pt2.x)
    map_struct.set_single("MapPt2Y", map_pt2.y)
    map_struct.set_single("WorldPt1X", are.world_point_1.x)
    map_struct.set_single("WorldPt1Y", are.world_point_1.y)
    map_struct.set_single("WorldPt2X", are.world_point_2.x)
    map_struct.set_single("WorldPt2Y", are.world_point_2.y)

    # Use original value for version if current is at default (0)
    version = are.get_original_or_current('version', are.version, 0)
    root.set_uint32("Version", version)

    root.set_uint32("SunAmbientColor", are.sun_ambient.rgb_integer())
    root.set_uint32("SunDiffuseColor", are.sun_diffuse.rgb_integer())
    root.set_uint32("DynAmbientColor", are.dynamic_light.rgb_integer())
    root.set_uint32("SunFogColor", are.fog_color.rgb_integer())
    root.set_uint32("Grass_Ambient", are.grass_ambient.rgb_integer())
    root.set_uint32("Grass_Diffuse", are.grass_diffuse.rgb_integer())

    root.set_string("Tag", are.tag)
    root.set_locstring("Name", are.name)
    root.set_string("Comments", are.comment)
    root.set_single("AlphaTest", are.alpha_test)
    root.set_int32("CameraStyle", are.camera_style)
    root.set_resref("DefaultEnvMap", are.default_envmap)
    root.set_resref("Grass_TexName", are.grass_texture)
    root.set_single("Grass_Density", are.grass_density)
    root.set_single("Grass_QuadSize", are.grass_size)
    root.set_single("Grass_Prob_LL", are.grass_prob_ll)
    root.set_single("Grass_Prob_LR", are.grass_prob_lr)
    root.set_single("Grass_Prob_UL", are.grass_prob_ul)
    root.set_single("Grass_Prob_UR", are.grass_prob_ur)
    root.set_uint8("SunFogOn", are.fog_enabled)
    root.set_single("SunFogNear", are.fog_near)
    root.set_single("SunFogFar", are.fog_far)
    root.set_uint8("SunShadows", are.shadows)
    root.set_uint8("ShadowOpacity", are.shadow_opacity)
    root.set_int32("WindPower", are.wind_power.value)
    root.set_uint8("Unescapable", are.unescapable)
    root.set_uint8("DisableTransit", are.disable_transit)
    root.set_uint8("StealthXPEnabled", are.stealth_xp)
    root.set_uint32("StealthXPLoss", are.stealth_xp_loss)
    root.set_uint32("StealthXPMax", are.stealth_xp_max)
    root.set_resref("OnEnter", are.on_enter)
    root.set_resref("OnExit", are.on_exit)
    root.set_resref("OnHeartbeat", are.on_heartbeat)
    root.set_resref("OnUserDefined", are.on_user_defined)

    rooms_list = root.set_list("Rooms", GFFList())
    for room in are.rooms:
        room_struct = rooms_list.add(0)
        room_struct.set_single("AmbientScale", room.ambient_scale)
        room_struct.set_int32("EnvAudio", room.env_audio)
        room_struct.set_string("RoomName", room.name)
        if game.is_k2():
            room_struct.set_uint8("DisableWeather", room.weather)
            room_struct.set_int32("ForceRating", room.force_rating)

    if game.is_k2():
        root.set_int32("DirtyARGBOne", are.dirty_argb_1.rgb_integer())
        root.set_int32("DirtyARGBTwo", are.dirty_argb_2.rgb_integer())
        root.set_int32("DirtyARGBThree", are.dirty_argb_3.rgb_integer())
        root.set_uint32("Grass_Emissive", are.grass_emissive.rgb_integer())

        root.set_int32("ChanceRain", are.chance_rain)
        root.set_int32("ChanceSnow", are.chance_snow)
        root.set_int32("ChanceLightning", are.chance_lightning)
        root.set_int32("DirtySizeOne", are.dirty_size_1)
        root.set_int32("DirtyFormulaOne", are.dirty_formula_1)
        root.set_int32("DirtyFuncOne", are.dirty_func_1)
        root.set_int32("DirtySizeTwo", are.dirty_size_2)
        root.set_int32("DirtyFormulaTwo", are.dirty_formula_2)
        root.set_int32("DirtyFuncTwo", are.dirty_func_2)
        root.set_int32("DirtySizeThree", are.dirty_size_3)
        root.set_int32("DirtyFormulaThre", are.dirty_formula_3)
        root.set_int32("DirtyFuncThree", are.dirty_func_3)

    if use_deprecated:
        root.set_int32("ID", are.unused_id)
        root.set_int32("Creator_ID", are.creator_id)
        root.set_uint32("Flags", are.flags)
        root.set_int32("ModSpotCheck", are.mod_spot_check)
        root.set_int32("ModListenCheck", are.mod_listen_check)
        root.set_uint32("MoonAmbientColor", are.moon_ambient)
        root.set_uint32("MoonDiffuseColor", are.moon_diffuse)
        root.set_uint8("MoonFogOn", are.moon_fog)
        # Use original values for moon fog if current values are at default (0.0)
        moon_fog_near = are.get_original_or_current('moon_fog_near', are.moon_fog_near, 0.0)
        moon_fog_far = are.get_original_or_current('moon_fog_far', are.moon_fog_far, 0.0)
        root.set_single("MoonFogNear", moon_fog_near)
        root.set_single("MoonFogFar", moon_fog_far)
        root.set_uint32("MoonFogColor", are.moon_fog_color)
        root.set_uint8("MoonShadows", are.moon_shadows)
        root.set_uint8("IsNight", are.is_night)
        root.set_uint8("LightingScheme", are.lighting_scheme)
        root.set_uint8("DayNightCycle", are.day_night)
        root.set_uint16("LoadScreenID", are.loadscreen_id)
        root.set_uint8("NoRest", are.no_rest)
        root.set_uint8("NoHangBack", are.no_hang_back)
        root.set_uint8("PlayerOnly", are.player_only)
        # Use original value for PlayerVsPlayer if current is at default (0)
        player_vs_player = are.get_original_or_current('player_vs_player', are.player_vs_player, 0)
        root.set_uint8("PlayerVsPlayer", player_vs_player)
        root.set_list("Expansion_List", GFFList())

    return gff


def read_are(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> ARE:
    """Returns an ARE instance from the source.

    Args:
    ----
        source: The source to read from
        offset: The byte offset to start reading from
        size: The maximum number of bytes to read

    Returns:
    -------
        ARE: The constructed annotation regions

    Processing Logic:
    ----------------
        - Read GFF from source starting at offset with max size
        - Construct ARE object from parsed GFF
    """
    gff = read_gff(source, offset, size)
    return construct_are(gff)


def write_are(
    are: ARE,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    """Writes an ARE resource to a target file format.

    Args:
    ----
        are: ARE - The ARE resource to write
        target: TARGET_TYPES - The target file path or object to write to
        game: Game - The game type of the ARE (default K2)
        file_format: ResourceType - The file format to write as (default GFF)
        use_deprecated: bool - Whether to include deprecated fields (default True)

    Returns:
    -------
        None: Writes the ARE as GFF to the target without returning anything

    Processing Logic:
    ----------------
        - Dismantles the ARE into a GFF structure
        - Writes the GFF structure to the target using the specified file format
    """
    gff = dismantle_are(are, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_are(
    are: ARE,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    """Converts ARE to bytes in specified file format.

    Args:
    ----
        are: ARE: area object
        game: Game: Game type are is for
        file_format: ResourceType: File format to convert to
        use_deprecated: bool: Use deprecated ARE fields if true

    Returns:
    -------
        bytes: Converted ARE bytes

    Processing Logic:
    ----------------
        - Dismantle ARE to GFF format
        - Convert GFF to specified file format bytes
    """
    gff = dismantle_are(are, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
