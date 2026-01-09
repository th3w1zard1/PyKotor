from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTS:
    """Stores sound data.

    UTS files are GFF-based format files that store sound object definitions including
    audio settings, positioning, looping, and volume controls.

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x00505560 - CSWSArea::LoadSounds (575 bytes, 93 lines)
                - Loads sound objects from area GIT file
                - Calls CSWSSoundObject::Load or CSWSSoundObject::LoadFromTemplate
                - Function signature: LoadSounds(CSWSArea* this, CResGFF* param_1, CResStruct* param_2, int param_3, int param_4)
            - 0x005c94e0 - CSWSSoundObject::LoadFromTemplate (likely)
                - Loads sound template from ResRef
                - Pattern consistent with other LoadFromTemplate functions
            - CSWSSoundObject::Load (called from LoadSounds at line 51)
                - Loads sound object from GFF struct
                - Reads TemplateResRef, ObjectId, GeneratedType, position fields
        
        KotOR II / TSL (swkotor2.exe):
            - Functionally equivalent UTS parsing logic
            - Same GFF field structure and parsing behavior
            - String references at different addresses due to binary layout differences
        
        GFF Field Structure (from LoadSounds and inferred patterns):
            - Root struct fields:
                - "TemplateResRef" (CResRef) - Template resource reference
                - "ObjectId" (DWORD) - Object ID (default 0x7f000000)
                - "GeneratedType" (DWORD) - Generated type identifier
                - "XPosition" (FLOAT) - X coordinate position
                - "YPosition" (FLOAT) - Y coordinate position
                - "ZPosition" (FLOAT) - Z coordinate position
                - "Tag" (CExoString) - Sound object tag identifier
                - "Active" (BYTE) - Whether sound is active
                - "Continuous" (BYTE) - Whether sound plays continuously
                - "Looping" (BYTE) - Whether sound loops
                - "Positional" (BYTE) - Whether sound is positional (3D)
                - "RandomPosition" (BYTE) - Whether sound position is randomized
                - "RandomRange" (FLOAT) - Random position range
                - "Elevation" (FLOAT) - Sound elevation
                - "Volume" (BYTE) - Sound volume (0-255)
                - "PitchVariation" (FLOAT) - Pitch variation range
                - "VolumeVariation" (FLOAT) - Volume variation range
                - "Sound" (CResRef) - Sound resource reference
        
        Note: UTS files are GFF format files with specific structure definitions (GFFContent.UTS)

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this sound template.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:15 (TemplateResRef property)

        tag: "Tag" field. Tag identifier for this sound.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:13 (Tag property)

        active: "Active" field. Whether sound is active.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:16 (Active property)

        continuous: "Continuous" field. Whether sound plays continuously.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:17 (Continuous property)

        looping: "Looping" field. Whether sound loops.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:18 (Looping property)

        positional: "Positional" field. Whether sound is positional (3D).
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:19 (Positional property)

        random_position: "RandomPosition" field. Whether sound position is randomized.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:20 (RandomPosition property)

        random_pick: "Random" field. Whether sound is randomly selected from list.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:21 (Random property)

        elevation: "Elevation" field. Elevation offset for positional sounds.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:22 (Elevation property)

        max_distance: "MaxDistance" field. Maximum distance for positional sounds.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:23 (MaxDistance property)

        min_distance: "MinDistance" field. Minimum distance for positional sounds.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:24 (MinDistance property)

        random_range_x: "RandomRangeX" field. X-axis range for random positioning.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:25 (RandomRangeX property)

        random_range_y: "RandomRangeY" field. Y-axis range for random positioning.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:26 (RandomRangeY property)

        interval: "Interval" field. Time interval between sound plays (in seconds).
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:27 (Interval property)

        interval_variation: "IntervalVrtn" field. Variation in interval timing.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:28 (IntervalVrtn property)

        pitch_variation: "PitchVariation" field. Pitch variation amount.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:29 (PitchVariation property)

        priority: "Priority" field. Sound priority level.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:30 (Priority property)

        volume: "Volume" field. Volume level (0-255).
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:33 (Volume property)

        volume_variation: "VolumeVrtn" field. Volume variation amount.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:34 (VolumeVrtn property)

        sounds: List of ResRef objects representing sound files to play.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:35 (Sounds property)

        comment: "Comment" field. Developer comment.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:37 (Comment property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:36 (PaletteID property)

        name: "LocName" field. Localized name. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:14 (LocName property)

        hours: "Hours" field. Hour restriction. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:31 (Hours property)

        times: "Times" field. Time restriction. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTS.cs:32 (Times property)
            Note: PyKotor comment notes some files have this as uint8, others as uint32
    """

    BINARY_TYPE = ResourceType.UTS

    def __init__(self):
        self.resref: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.comment: str = ""

        self.active: bool = False
        self.continuous: bool = False
        self.looping: bool = False
        self.positional: bool = False
        self.random_pick: bool = False

        self.random_position: bool = False
        self.random_range_x: float = 0.0
        self.random_range_y: float = 0.0

        self.elevation: float = 0.0
        self.max_distance: float = 0.0
        self.min_distance: float = 0.0

        self.priority: int = 0

        self.interval: int = 0
        self.interval_variation: int = 0
        self.pitch_variation: float = 0.0
        self.volume: int = 0
        self.volume_variation: int = 0

        self.sounds: list[ResRef] = []

        # Deprecated:
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.times: int = 0
        self.hours: int = 0
        self.palette_id: int = 0


def construct_uts(
    gff: GFF,
) -> UTS:
    uts = UTS()

    root: GFFStruct = gff.root
    uts.tag = root.acquire("Tag", "")
    uts.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    uts.active = bool(root.acquire("Active", 0))
    uts.continuous = bool(root.acquire("Continuous", 0))
    uts.looping = bool(root.acquire("Looping", 0))
    uts.positional = bool(root.acquire("Positional", 0))
    uts.random_position = bool(root.acquire("RandomPosition", 0))
    uts.random_pick = bool(root.acquire("Random", 0))
    uts.elevation = root.acquire("Elevation", 0.0)
    uts.max_distance = root.acquire("MaxDistance", 0.0)
    uts.min_distance = root.acquire("MinDistance", 0.0)
    uts.random_range_x = root.acquire("RandomRangeX", 0.0)
    uts.random_range_y = root.acquire("RandomRangeY", 0.0)
    uts.interval = root.acquire("Interval", 0)
    uts.interval_variation = root.acquire("IntervalVrtn", 0)
    uts.pitch_variation = root.acquire("PitchVariation", 0.0)
    uts.priority = root.acquire("Priority", 0)
    uts.volume = root.acquire("Volume", 0)
    uts.volume_variation = root.acquire("VolumeVrtn", 0)
    uts.comment = root.acquire("Comment", "")
    uts.name = root.acquire("LocName", LocalizedString.from_invalid())
    uts.hours = root.acquire("Hours", 0)
    uts.times = root.acquire("Times", 0)
    uts.palette_id = root.acquire("PaletteID", 0)

    for sound_struct in root.acquire("Sounds", GFFList()):
        sound = sound_struct.acquire("Sound", ResRef.from_blank())
        uts.sounds.append(sound)

    return uts


def dismantle_uts(
    uts: UTS,
    game: Game = Game.K2,  # noqa: ARG001
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTS)

    root: GFFStruct = gff.root
    root.set_string("Tag", uts.tag)
    root.set_resref("TemplateResRef", uts.resref)
    root.set_uint8("Active", uts.active)
    root.set_uint8("Continuous", uts.continuous)
    root.set_uint8("Looping", uts.looping)
    root.set_uint8("Positional", uts.positional)
    root.set_uint8("RandomPosition", uts.random_position)
    root.set_uint8("Random", uts.random_pick)
    root.set_single("Elevation", uts.elevation)
    root.set_single("MaxDistance", uts.max_distance)
    root.set_single("MinDistance", uts.min_distance)
    root.set_single("RandomRangeX", uts.random_range_x)
    root.set_single("RandomRangeY", uts.random_range_y)
    root.set_uint32("Interval", uts.interval)
    root.set_uint32("IntervalVrtn", uts.interval_variation)
    root.set_single("PitchVariation", uts.pitch_variation)
    root.set_uint8("Priority", uts.priority)
    root.set_uint8("Volume", uts.volume)
    root.set_uint8("VolumeVrtn", uts.volume_variation)
    root.set_string("Comment", uts.comment)

    sound_list = root.set_list("Sounds", GFFList())
    for sound in uts.sounds:
        sound_list.add(0).set_resref("Sound", sound)

    root.set_uint8("PaletteID", uts.palette_id)

    if use_deprecated:
        root.set_locstring("LocName", uts.name)
        root.set_uint32("Hours", uts.hours)
        root.set_uint8("Times", uts.times)  # TODO(th3w1zard1): double check this. Some files have this field as uint8 others as uint32?

    return gff


def read_uts(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTS:
    gff: GFF = read_gff(source, offset, size)
    return construct_uts(gff)


def write_uts(
    uts: UTS,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_uts(uts, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_uts(
    uts: UTS,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_uts(uts, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
