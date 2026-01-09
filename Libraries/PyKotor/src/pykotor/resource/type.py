"""Resource type definitions for BioWare game engines.

This module contains comprehensive resource type definitions for all known BioWare game engines,
including Infinity, Aurora, Odyssey, and Eclipse engines. Resource types are identified by
numeric IDs and file extensions, with engine support tracking via the BiowareEngine enum.

The ResourceType enum includes all resource types from:
- Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
- Based on swkotor.exe resource type system:
  * CExoResRef - Resource reference structure used throughout engine
  * CResRef::GetResRef - Gets resource reference string
  * Resource type IDs defined in engine's resource system
- Derivations and other implementations (see References sections below)

Each resource type includes:
- type_id: Numeric identifier used by game engines
- extension: File extension (lowercase, no leading dot)
- category: Descriptive category (e.g., "Models", "Textures", "Scripts")
- contents: Data format ("binary", "plaintext", "gff", "erf", "lips", "video", "xml")
- supported_engines: Tuple of BiowareEngine values indicating which engines support this type

References:
----------
    Original BioWare engine binaries (resource type IDs from swkotor.exe, swkotor2.exe, etc.)
    Based on swkotor.exe resource type system:
    - GetResTypeFromFile @ 0x00406650 - Gets resource type from file extension
    - GetResTypeFromExtension @ 0x005e6670, @ 0x005e7a40 - Gets resource type from extension string
    wiki/Bioware-Aurora-KeyBIF.md (Aurora engine resource type documentation)
"""

from __future__ import annotations

import io
import mmap
import os
import struct
import uuid

from enum import Enum
from functools import lru_cache
from io import BytesIO
from typing import TYPE_CHECKING, NamedTuple, TypeVar, Union, cast
from xml.etree.ElementTree import ParseError

from pykotor.common.stream import BinaryReader, BinaryWriter
from utility.common.misc_string.mutable_str import WrappedStr

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Literal, Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.stream import BinaryWriterBytearray, BinaryWriterFile


class BiowareEngine(Enum):
    """BioWare game engine identifiers.

    Represents the different BioWare game engines that use resource type systems.
    Used to track which engines support which resource types.

    Members:
    --------
        Infinity: Engine for Baldur's Gate, Baldur's Gate II, Icewind Dale, Planescape: Torment
        Aurora: Engine for Neverwinter Nights, Neverwinter Nights 2, Neverwinter Nights: Enhanced Edition
        Odyssey: Engine for Knights of the Old Republic and Knights of the Old Republic II: The Sith Lords
        Eclipse: Engine for Dragon Age: Origins and Dragon Age II

    References:
    -----------
        Original BioWare engine binaries (engine type information from swkotor.exe, swkotor2.exe, etc.)
        Based on swkotor.exe resource type system:
    - GetResTypeFromFile @ 0x00406650 - Gets resource type from file extension
    - GetResTypeFromExtension @ 0x005e6670, @ 0x005e7a40 - Gets resource type from extension string
    """

    Infinity = "infinity"  # Baldur's Gate, Icewind Dale, Planescape: Torment
    Aurora = "aurora"  # Neverwinter Nights series
    Odyssey = "odyssey"  # KotOR I & II
    Eclipse = "eclipse"  # Dragon Age: Origins, Dragon Age II


STREAM_TYPES = Union[io.BufferedIOBase, io.RawIOBase, mmap.mmap]
BASE_SOURCE_TYPES = Union[os.PathLike, str, bytes, bytearray, memoryview]
SOURCE_TYPES = Union[BASE_SOURCE_TYPES, STREAM_TYPES, BytesIO, io.StringIO, BinaryReader]
TARGET_TYPES = Union[os.PathLike, str, bytearray, BytesIO, io.StringIO, BinaryWriter]


R = TypeVar("R")


def autoclose(func: Callable[..., R]) -> Callable[..., R]:
    def _autoclose(self: ResourceReader | ResourceWriter, auto_close: bool = True) -> R:  # noqa: FBT002, FBT001
        try:
            resource: R = func(self, auto_close=auto_close)
        except (OSError, ParseError, ValueError, IndexError, StopIteration, struct.error) as e:
            msg = "Tried to save or load an unsupported or corrupted file."
            raise ValueError(msg) from e
        finally:
            if auto_close:
                self.close()
        return resource

    return _autoclose


class ResourceReader:
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int | None = None,
        *,
        use_binary_reader: bool = True,
    ):
        if use_binary_reader:
            self._reader: BinaryReader = BinaryReader.from_auto(source, offset)
            self._size: int = size or self._reader.remaining()
        else:
            if isinstance(source, memoryview):
                loaded_src: bytearray = bytearray(source)
            elif isinstance(source, (bytes, bytearray)):
                loaded_src = source if isinstance(source, bytearray) else bytearray(source)
            elif isinstance(source, (os.PathLike, str)):
                with open(  # noqa: PTH123
                    os.path.normpath(source) if isinstance(source, str) else os.fspath(source),
                    "rb",
                ) as f:
                    loaded_src = bytearray(f.read())
            elif isinstance(source, io.BufferedIOBase):
                loaded_src = bytearray(source.read())
            elif isinstance(source, mmap.mmap):
                loaded_src = bytearray(source)
            else:
                assert isinstance(source, BinaryReader)
                loaded_src = bytearray(source.read_all())

            self._offset: int = offset
            self._size: int = len(loaded_src)
            self._source: bytearray = loaded_src[offset : self._size]

    def close(self):
        self._reader.close()


class ResourceWriter:
    def __init__(
        self,
        target: TARGET_TYPES,
    ):
        self._writer: BinaryWriter = BinaryWriter.to_auto(target)

    def close(self):
        self._writer.close()


class ResourceTuple(NamedTuple):
    """Tuple representing a resource type definition.

    Attributes:
    -----------
        type_id: Integer ID of the resource type as recognized by the game engines.
        extension: File extension associated with the resource type (lowercase, no leading dot).
        category: Short description of what kind of data the resource type stores.
        contents: How the resource type stores data: "binary", "plaintext", "gff", "erf", "lips", "video", or "xml".
        is_invalid: Whether this resource type is invalid/undefined.
        target_member: For toolset-only types, the name of the target ResourceType member this maps to.
        supported_engines: Set of BiowareEngine values indicating which engines support this resource type.
            Defaults to empty set if not specified (unknown support).

    References:
    -----------
        Based on swkotor.exe resource type system:
        - GetResTypeFromFile @ 0x00406650 - Gets resource type from file extension
        - GetResTypeFromExtension @ 0x005e6670, @ 0x005e7a40 - Gets resource type from extension string
        - ".mdl" string @ 0x00740ca8 - MDL file extension
        - ".wav" string @ 0x0074d308 - WAV file extension
        - "_s.rim" string @ 0x00752ff0 - RIM file extension pattern
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
    """

    type_id: int
    extension: str
    category: Literal["Save Data", "Images", "Video", "Audio", "Text Files", "Other", "Models", "Textures", "Scripts", "Modules", "Module Data", "Creatures", "2D Arrays", "Talk Tables", "Dialogs", "Palettes", "Triggers", "Sounds", "Factions", "Encounters", "Doors", "Placeables", "Defaults", "GUIs", "Unused"]
    contents: Literal["binary", "plaintext", "gff", "erf", "lips", "video", "xml"]
    is_invalid: bool = False
    target_member: Literal["RES", "BMP", "MVE", "TGA", "WAV", "PLT", "INI", "BMU", "MPG", "TXT", "WMA", "WMV", "XMV", "PLH", "TEX", "MDL", "THG", "FNT", "LUA", "SLT", "NSS", "NCS", "MOD", "ARE", "SET", "BIP", "JPG2", "PWC"] | None = None
    supported_engines: tuple[BiowareEngine, ...] = ()  # Empty tuple as default, use tuple for immutability


class ResourceType(Enum):
    """Represents a resource type used across BioWare game engines.

    This enum contains comprehensive resource type definitions based on swkotor.exe resource type system
    REVA analysis, representing all known resource types across BioWare's Infinity, Aurora,
    Odyssey, and Eclipse engines.

    Each enum member is a ResourceTuple containing:
    - type_id: Integer ID recognized by game engines (consistent across implementations)
    - extension: File extension (lowercase, no leading dot)
    - category: Descriptive category grouping
    - contents: Data storage format
    - is_invalid: Whether this type is invalid/undefined
    - target_member: For toolset-only types, the target ResourceType this maps to
    - supported_engines: Tuple of BiowareEngine values indicating engine support

    Resource type IDs are consistent across all vendor implementations and match the
    original BioWare engine binaries. Types marked as "Unused" are reserved IDs that
    are not currently used by any known engine.

    Engine Support:
    --------------
        Infinity: Baldur's Gate, Icewind Dale, Planescape: Torment
        Aurora: Neverwinter Nights series
        Odyssey: Knights of the Old Republic I & II
        Eclipse: Dragon Age: Origins, Dragon Age II

    Toolset-only types (supported_engines=()) are used by modding tools but not by
    game engines directly. These typically provide human-readable formats (XML, JSON)
    for editing game resources.

    References:
    ----------
        Based on swkotor.exe resource type system:
        - GetResTypeFromFile @ 0x00406650 - Gets resource type from file extension
        - GetResTypeFromExtension @ 0x005e6670, @ 0x005e7a40 - Gets resource type from extension string
        - CExoResRef - Resource reference structure used throughout engine
        - Resource type IDs defined in engine's resource system
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        wiki/Bioware-Aurora-KeyBIF.md (Aurora engine documentation)
    """

    INVALID = ResourceTuple(-1, "", "Undefined", "binary", is_invalid=True)
    RES = ResourceTuple(0, "res", "Save Data", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse))  # Generic GFF
    BMP = ResourceTuple(  # Image, Windows bitmap
        1, "bmp", "Images", "binary", supported_engines=(BiowareEngine.Infinity, BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    MVE = ResourceTuple(  # Video, Infinity Engine
        2, "mve", "Video", "video", supported_engines=(BiowareEngine.Infinity,)
    )
    TGA = ResourceTuple(  # Image, Truevision TARGA image
        3, "tga", "Textures", "binary", supported_engines=(BiowareEngine.Infinity, BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    WAV = ResourceTuple(  # Audio, Waveform
        4, "wav", "Audio", "binary", supported_engines=(BiowareEngine.Infinity, BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    # Type ID 5 is reserved/unused in all BioWare engines
    PLT = ResourceTuple(  # Packed layer texture
        6, "plt", "Other", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))
    INI = ResourceTuple(  # Configuration, Windows INI
        7, "ini", "Text Files", "plaintext", supported_engines=(BiowareEngine.Infinity, BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    BMU = ResourceTuple(8, "bmu", "Audio", "binary", supported_engines=(BiowareEngine.Odyssey,))  # Audio, MP3 with extra header (TSL uses MP3 extension with this type ID)
    MPG = ResourceTuple(9, "mpg", "Video", "binary", supported_engines=(BiowareEngine.Odyssey,))  # Video, MPEG
    TXT = ResourceTuple(  # Text, raw
        10, "txt", "Text Files", "plaintext", supported_engines=(BiowareEngine.Infinity, BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    WMA = ResourceTuple(11, "wma", "Audio", "binary", supported_engines=(BiowareEngine.Odyssey,))  # Audio, Windows media (K1 only, not in TSL)
    WMV = ResourceTuple(12, "wmv", "Audio", "binary", supported_engines=(BiowareEngine.Odyssey,))  # Video, Windows media
    XMV = ResourceTuple(13, "xmv", "Audio", "binary", supported_engines=(BiowareEngine.Odyssey,))  # Video, Xbox
    PLH = ResourceTuple(2000, "plh", "Models", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))
    TEX = ResourceTuple(2001, "tex", "Textures", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Texture
    MDL = ResourceTuple(2002, "mdl", "Models", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse))  # Geometry, BioWare model
    THG = ResourceTuple(2003, "thg", "Unused", "binary", supported_engines=(BiowareEngine.Odyssey,))
    # Type ID 2004 is reserved/unused
    FNT = ResourceTuple(2005, "fnt", "Font", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Font
    # Type ID 2006 is reserved/unused
    LUA = ResourceTuple(2007, "lua", "Scripts", "plaintext", supported_engines=(BiowareEngine.Odyssey, BiowareEngine.Eclipse))  # Script, LUA source
    SLT = ResourceTuple(2008, "slt", "Unused", "binary", supported_engines=(BiowareEngine.Odyssey,))
    NSS = ResourceTuple(2009, "nss", "Scripts", "plaintext", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Script, NWScript source
    NCS = ResourceTuple(2010, "ncs", "Scripts", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Script, NWScript bytecode
    MOD = ResourceTuple(2011, "mod", "Modules", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Module, ERF
    ARE = ResourceTuple(2012, "are", "Module Data", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Static area data, GFF
    SET = ResourceTuple(2013, "set", "Unused", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Tileset
    IFO = ResourceTuple(2014, "ifo", "Module Data", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Module information, GFF
    BIC = ResourceTuple(2015, "bic", "Creatures", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Character data, GFF
    WOK = ResourceTuple(2016, "wok", "Walkmeshes", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Walk mesh
    TwoDA = ResourceTuple(
        2017, "2da", "2D Arrays", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )  # Table data, 2-dimensional text array
    TLK = ResourceTuple(2018, "tlk", "Talk Tables", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse))  # Talk table
    # Type IDs 2019-2021 are reserved/unused
    TXI = ResourceTuple(2022, "txi", "Textures", "plaintext", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Texture information
    GIT = ResourceTuple(2023, "git", "Module Data", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Dynamic area data, GFF
    BTI = ResourceTuple(2024, "bti", "Items", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Item template (BioWare), GFF
    UTI = ResourceTuple(2025, "uti", "Items", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Item template (user), GFF
    BTC = ResourceTuple(2026, "btc", "Creatures", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Creature template (BioWare), GFF
    UTC = ResourceTuple(2027, "utc", "Creatures", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Creature template (user), GFF
    # Type ID 2028 is reserved/unused
    DLG = ResourceTuple(2029, "dlg", "Dialogs", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse))  # Dialog tree, GFF
    ITP = ResourceTuple(
        2030, "itp", "Palettes", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey)
    )  # Toolset "palette" (tree of tiles or object templates), GFF
    BTT = ResourceTuple(2031, "btt", "Triggers", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Trigger template (BioWare), GFF
    UTT = ResourceTuple(2032, "utt", "Triggers", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Trigger template (user), GFF
    DDS = ResourceTuple(  # Texture, DirectDraw Surface
        2033, "dds", "Textures", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    BTS = ResourceTuple(2034, "bts", "Sounds", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Sound template (BioWare), GFF
    UTS = ResourceTuple(2035, "uts", "Sounds", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Sound template (user), GFF
    LTR = ResourceTuple(2036, "ltr", "Other", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Letter combo probability information
    GFF = ResourceTuple(2037, "gff", "Other", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse))  # Generic GFF
    FAC = ResourceTuple(2038, "fac", "Factions", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Faction information, GFF
    BTE = ResourceTuple(2039, "bte", "Encounters", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Encounter template (BioWare), GFF
    UTE = ResourceTuple(2040, "ute", "Encounters", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Encounter template (user), GFF
    BTD = ResourceTuple(2041, "btd", "Doors", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Door template (BioWare), GFF
    UTD = ResourceTuple(2042, "utd", "Doors", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Door template (user), GFF
    BTP = ResourceTuple(2043, "btp", "Placeables", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Placeable template (BioWare), GFF
    UTP = ResourceTuple(2044, "utp", "Placeables", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Placeable template (user), GFF
    DFT = ResourceTuple(2045, "dft", "Defaults", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Default values
    DTF = ResourceTuple(2045, "dft", "Defaults", "plaintext", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Default value file, INI
    GIC = ResourceTuple(2046, "gic", "Module Data", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Game instance comments, GFF
    GUI = ResourceTuple(2047, "gui", "GUIs", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse))  # GUI definition, GFF
    CSS = ResourceTuple(2048, "css", "Scripts", "plaintext", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Script, conditional source script
    CCS = ResourceTuple(2049, "ccs", "Scripts", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Script, conditional compiled script
    BTM = ResourceTuple(2050, "btm", "Merchants", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Store template (BioWare), GFF
    UTM = ResourceTuple(2051, "utm", "Merchants", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Store template (user), GFF
    DWK = ResourceTuple(2052, "dwk", "Walkmeshes", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Door walk mesh
    PWK = ResourceTuple(2053, "pwk", "Walkmeshes", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Placeable walk mesh
    BTG = ResourceTuple(2054, "btg", "Items", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Random item generator template (BioWare), GFF
    UTG = ResourceTuple(2055, "utg", "Items", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Random item generator template (user), GFF
    JRL = ResourceTuple(2056, "jrl", "Journals", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Journal data, GFF
    SAV = ResourceTuple(2057, "sav", "Save Data", "erf", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Game save, ERF
    UTW = ResourceTuple(2058, "utw", "Waypoints", "gff", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Waypoint template, GFF
    FourPC = ResourceTuple(2059, "4pc", "Textures", "binary", supported_engines=(BiowareEngine.Odyssey,))  # Texture, custom 16-bit RGBA
    SSF = ResourceTuple(2060, "ssf", "Soundsets", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Sound Set File
    HAK = ResourceTuple(2061, "hak", "Modules", "erf", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Resource hak pak, ERF (K1 only, not in TSL)
    NWM = ResourceTuple(  # Neverwinter Nights original campaign module, ERF (K1 only, not in TSL)
        2062, "nwm", "Modules", "erf", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey)
    )
    BIK = ResourceTuple(2063, "bik", "Videos", "binary", supported_engines=(BiowareEngine.Odyssey,))  # Video, RAD Game Tools Bink
    NDB = ResourceTuple(2064, "ndb", "Other", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Script debugger file
    PTM = ResourceTuple(2065, "ptm", "Other", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Plot instance/manager, GFF
    PTT = ResourceTuple(2066, "ptt", "Other", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey))  # Plot wizard template, GFF
    NCM = ResourceTuple(2067, "ncm", "Unused", "binary")
    MFX = ResourceTuple(2068, "mfx", "Unused", "binary")
    MAT = ResourceTuple(2069, "mat", "Materials", "binary", supported_engines=())  # Material
    MDB = ResourceTuple(2070, "mdb", "Models", "binary", supported_engines=())  # Geometry, BioWare model
    SAY = ResourceTuple(2071, "say", "Unused", "binary")
    TTF = ResourceTuple(2072, "ttf", "Fonts", "binary", supported_engines=())  # Font, True Type
    TTC = ResourceTuple(2073, "ttc", "Unused", "binary")
    CUT = ResourceTuple(2074, "cut", "Cutscenes", "gff", supported_engines=())  # Cutscene, GFF
    KA = ResourceTuple(  # Unused type, reserved  # noqa: E221
        2075, "ka", "Unused", "xml"
    )
    JPG = ResourceTuple(  # Image, JPEG
        2076, "jpg", "Images", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    ICO = ResourceTuple(  # Icon, Windows ICO
        2077, "ico", "Images", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    OGG = ResourceTuple(2078, "ogg", "Audio", "binary", supported_engines=(BiowareEngine.Eclipse,))  # Audio, Ogg Vorbis
    SPT = ResourceTuple(  # Unused type, reserved
        2079, "spt", "Unused", "binary"
    )
    SPW = ResourceTuple(  # Unused type, reserved
        2080, "spw", "Unused", "binary"
    )
    WFX = ResourceTuple(  # Unused type, reserved
        2081, "wfx", "Unused", "xml"
    )
    UGM = ResourceTuple(  # Unused type, reserved
        2082, "ugm", "Unused", "binary"
    )
    QDB = ResourceTuple(  # Unused type, reserved
        2083, "qdb", "Unused", "gff"
    )
    QST = ResourceTuple(  # Unused type, reserved
        2084, "qst", "Unused", "gff"
    )
    NPC = ResourceTuple(  # Unused type, reserved
        2085, "npc", "Unused", "binary"
    )
    SPN = ResourceTuple(  # Unused type, reserved
        2086, "spn", "Unused", "binary"
    )
    UTX = ResourceTuple(  # Unused type, reserved
        2087, "utx", "Unused", "binary"
    )
    MMD = ResourceTuple(  # Unused type, reserved
        2088, "mmd", "Unused", "binary"
    )
    SMM = ResourceTuple(  # Unused type, reserved
        2089, "smm", "Unused", "binary"
    )
    UTA = ResourceTuple(  # Unused type, reserved
        2090, "uta", "Unused", "binary"
    )
    MDE = ResourceTuple(  # Unused type, reserved
        2091, "mde", "Unused", "binary"
    )
    MDV = ResourceTuple(  # Unused type, reserved
        2092, "mdv", "Unused", "binary"
    )
    MDA = ResourceTuple(  # Unused type, reserved
        2093, "mda", "Unused", "binary"
    )
    MBA = ResourceTuple(  # Unused type, reserved
        2094, "mba", "Unused", "binary"
    )
    OCT = ResourceTuple(  # Unused type, reserved
        2095, "oct", "Unused", "binary"
    )
    BFX = ResourceTuple(  # Unused type, reserved
        2096, "bfx", "Unused", "binary"
    )
    PDB = ResourceTuple(2097, "pdb", "Unused", "binary")  # Unused type, reserved
    THEWITCHERSAVE = ResourceTuple(2098, "thewitchersave", "Save Data", "binary")  # The Witcher save file, not BioWare engine
    PVS = ResourceTuple(2099, "pvs", "Unused", "binary")  # Unused type, reserved
    CFX = ResourceTuple(2100, "cfx", "Unused", "binary")  # Unused type, reserved
    LUC = ResourceTuple(2101, "luc", "Scripts", "binary", supported_engines=(BiowareEngine.Eclipse,))  # Compiled Lua script, Eclipse only
    # Type ID 2102 is reserved/unused
    PRB = ResourceTuple(2103, "prb", "Unused", "binary")  # Unused type, reserved
    CAM = ResourceTuple(  # Campaign information, Aurora only
        2104, "cam", "Module Data", "binary", supported_engines=(BiowareEngine.Aurora,)
    )
    VDS = ResourceTuple(  # Unused type, reserved
        2105, "vds", "Unused", "binary"
    )
    BIN = ResourceTuple(  # Unused type, reserved
        2106, "bin", "Unused", "binary"
    )
    WOB = ResourceTuple(  # Unused type, reserved
        2107, "wob", "Unused", "binary"
    )
    API = ResourceTuple(  # Unused type, reserved
        2108, "api", "Unused", "binary"
    )
    Properties = ResourceTuple(  # Unused type, reserved
        2109, "properties", "Unused", "binary"
    )
    PNG = ResourceTuple(  # PNG image format
        2110, "png", "Images", "binary", supported_engines=(BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    LYT = ResourceTuple(  # Layout file, defines area layout
        3000, "lyt", "Module Data", "plaintext", supported_engines=(BiowareEngine.Odyssey,)
    )
    VIS = ResourceTuple(  # Visibility file, area visibility data
        3001, "vis", "Module Data", "plaintext", supported_engines=(BiowareEngine.Odyssey,)
    )
    RIM = ResourceTuple(  # RIM archive file, Odyssey module format
        3002, "rim", "Modules", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    PTH = ResourceTuple(  # Path file, creature pathfinding data
        3003, "pth", "Paths", "gff", supported_engines=(BiowareEngine.Odyssey,)
    )
    LIP = ResourceTuple(  # Lip sync file, facial animation data
        3004, "lip", "Lips", "lips", supported_engines=(BiowareEngine.Odyssey,)
    )
    BWM = ResourceTuple(  # Walkmesh file
        3005, "bwm", "Walkmeshes", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    TXB = ResourceTuple(  # Texture file
        3006, "txb", "Textures", "binary"
    )
    TPC = ResourceTuple(  # Texture file
        3007, "tpc", "Textures", "binary"
    )
    MDX = ResourceTuple(  # Geometry, model mesh data
        3008, "mdx", "Models", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    RSV = ResourceTuple(  # Unused type, reserved
        3009, "rsv", "Unused", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    SIG = ResourceTuple(  # Unused type, reserved
        3010, "sig", "Unused", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    MAB = ResourceTuple(  # Material, binary
        3011, "mab", "Materials", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    QST2 = ResourceTuple(  # Quest, GFF
        3012, "qst2", "Quests", "gff", supported_engines=(BiowareEngine.Odyssey,)
    )
    STO = ResourceTuple(  # GFF
        3013, "sto", "Other", "gff", supported_engines=(BiowareEngine.Odyssey,)
    )
    # Type ID 3014 is reserved/unused
    HEX = ResourceTuple(  # Hex grid file
        3015, "hex", "Other", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    MDX2 = ResourceTuple(  # Geometry, model mesh data
        3016, "mdx2", "Models", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    TXB2 = ResourceTuple(  # Texture
        3017, "txb2", "Textures", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    # Type IDs 3018-3021 are reserved/unused
    FSM = ResourceTuple(  # Finite State Machine data
        3022, "fsm", "Other", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    ART = ResourceTuple(  # Area environment settings, INI
        3023, "art", "Module Data", "plaintext", supported_engines=(BiowareEngine.Odyssey,)
    )
    AMP = ResourceTuple(  # Brightening control
        3024, "amp", "Other", "binary", supported_engines=(BiowareEngine.Odyssey,)
    )
    CWA = ResourceTuple(  # Crowd attributes, GFF
        3025, "cwa", "Crowd Attributes", "gff", supported_engines=(BiowareEngine.Odyssey,)
    )
    # Type IDs 3026-3027 are reserved/unused
    BIP = ResourceTuple(  # Lipsync data, binary LIP
        3028, "bip", "Lips", "lips", supported_engines=(BiowareEngine.Odyssey,)
    )
    MDB2 = ResourceTuple(  # Model database v2, Eclipse only
        4000, "mdb2", "Models", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    MDA2 = ResourceTuple(  # Model animation v2, Eclipse only
        4001, "mda2", "Models", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    SPT2 = ResourceTuple(  # Unused type, reserved
        4002, "spt2", "Unused", "binary"
    )
    GR2 = ResourceTuple(  # GR2 file, Eclipse only
        4003, "gr2", "Other", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    FXA = ResourceTuple(  # FXA file, Eclipse only
        4004, "fxa", "Other", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    FXE = ResourceTuple(  # FXE file, Eclipse only
        4005, "fxe", "Other", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    # Type ID 4006 is reserved/unused
    JPG2 = ResourceTuple(  # JPEG v2, Eclipse only
        4007, "jpg2", "Images", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    PWC = ResourceTuple(  # PWC file, Eclipse only
        4008, "pwc", "Other", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    EXE = ResourceTuple(  # Windows executable
        19000, "exe", "Other", "binary"
    )
    DBF = ResourceTuple(  # Database file
        19001, "dbf", "Other", "binary"
    )
    CDX = ResourceTuple(  # CDX file
        19002, "cdx", "Other", "binary"
    )
    FPT = ResourceTuple(  # FPT file
        19003, "fpt", "Other", "binary"
    )
    ZIP = ResourceTuple(  # ZIP archive
        20000, "zip", "Archives", "binary"
    )
    FXM = ResourceTuple(  # FXM file
        20001, "fxm", "Other", "binary"
    )
    FXS = ResourceTuple(  # FXS file
        20002, "fxs", "Other", "binary"
    )
    XML = ResourceTuple(  # XML file
        20003, "xml", "Other", "plaintext"
    )
    WLK = ResourceTuple(  # WLK file
        20004, "wlk", "Walkmeshes", "binary"
    )
    UTR = ResourceTuple(  # UTR file
        20005, "utr", "Unused", "binary"
    )
    SEF = ResourceTuple(  # SEF file
        20006, "sef", "Other", "binary"
    )
    PFX = ResourceTuple(  # PFX file
        20007, "pfx", "Other", "binary"
    )
    TFX = ResourceTuple(  # TFX file
        20008, "tfx", "Other", "binary"
    )
    IFX = ResourceTuple(  # IFX file
        20009, "ifx", "Other", "binary"
    )
    LFX = ResourceTuple(  # LFX file
        20010, "lfx", "Other", "binary"
    )
    BBX = ResourceTuple(  # BBX file
        20011, "bbx", "Other", "binary"
    )
    PFB = ResourceTuple(  # PFB file
        20012, "pfb", "Other", "binary"
    )
    UPE = ResourceTuple(  # UPE file
        20013, "upe", "Unused", "binary"
    )
    USC = ResourceTuple(  # USC file
        20014, "usc", "Unused", "binary"
    )
    ULT = ResourceTuple(  # ULT file
        20015, "ult", "Unused", "binary"
    )
    FX = ResourceTuple(  # FX file
        20016, "fx", "Other", "binary"
    )
    MAX = ResourceTuple(  # 3ds Max file
        20017, "max", "Other", "binary"
    )
    DOC = ResourceTuple(  # DOC file
        20018, "doc", "Other", "binary"
    )
    SCC = ResourceTuple(  # SCC file
        20019, "scc", "Other", "binary"
    )
    WMP = ResourceTuple(  # WMP file
        20020, "wmp", "Other", "binary"
    )
    OSC = ResourceTuple(  # OSC file
        20021, "osc", "Other", "binary"
    )
    TRN = ResourceTuple(  # TRN file
        20022, "trn", "Other", "binary"
    )
    UEN = ResourceTuple(  # UEN file
        20023, "uen", "Unused", "binary"
    )
    ROS = ResourceTuple(  # ROS file
        20024, "ros", "Other", "binary"
    )
    RST = ResourceTuple(  # RST file
        20025, "rst", "Other", "binary"
    )
    PTX = ResourceTuple(  # PTX file
        20026, "ptx", "Other", "binary"
    )
    LTX = ResourceTuple(  # LTX file
        20027, "ltx", "Other", "binary"
    )
    TRX = ResourceTuple(  # TRX file
        20028, "trx", "Other", "binary"
    )
    NDS = ResourceTuple(21000, "nds", "Other", "binary")
    HERF = ResourceTuple(  # HERF file
        21001, "herf", "Other", "binary"
    )
    DICT = ResourceTuple(  # Dictionary file
        21002, "dict", "Other", "binary"
    )
    SMALL = ResourceTuple(21003, "small", "Other", "binary")
    CBGT = ResourceTuple(21004, "cbgt", "Other", "binary")
    CDPTH = ResourceTuple(21005, "cdpth", "Other", "binary")
    EMIT = ResourceTuple(21006, "emit", "Other", "binary")
    ITM = ResourceTuple(21007, "itm", "Other", "binary")
    NANR = ResourceTuple(21008, "nanr", "Other", "binary")
    NBFP = ResourceTuple(21009, "nbfp", "Other", "binary")
    NBFS = ResourceTuple(21010, "nbfs", "Other", "binary")
    NCER = ResourceTuple(21011, "ncer", "Other", "binary")
    NCGR = ResourceTuple(21012, "ncgr", "Other", "binary")
    NCLR = ResourceTuple(21013, "nclr", "Other", "binary")
    NFTR = ResourceTuple(21014, "nftr", "Other", "binary")
    NSBCA = ResourceTuple(21015, "nsbca", "Other", "binary")
    NSBMD = ResourceTuple(21016, "nsbmd", "Other", "binary")
    NSBTA = ResourceTuple(21017, "nsbta", "Other", "binary")
    NSBTP = ResourceTuple(21018, "nsbtp", "Other", "binary")
    NSBTX = ResourceTuple(21019, "nsbtx", "Other", "binary")
    PAL = ResourceTuple(  # Palette file
        21020, "pal", "Palettes", "binary"
    )
    RAW = ResourceTuple(  # Raw data file
        21021, "raw", "Other", "binary"
    )
    SADL = ResourceTuple(21022, "sadl", "Other", "binary")
    SDAT = ResourceTuple(21023, "sdat", "Other", "binary")
    SMP = ResourceTuple(21024, "smp", "Other", "binary")
    SPL = ResourceTuple(21025, "spl", "Other", "binary")
    VX = ResourceTuple(21026, "vx", "Other", "binary")
    ANB = ResourceTuple(22000, "anb", "Other", "binary")
    ANI = ResourceTuple(22001, "ani", "Other", "binary")
    CNS = ResourceTuple(22002, "cns", "Other", "binary")
    CUR = ResourceTuple(  # Cursor file
        22003, "cur", "Other", "binary"
    )
    EVT = ResourceTuple(  # Event file
        22004, "evt", "Other", "binary"
    )
    FDL = ResourceTuple(22005, "fdl", "Other", "binary")
    FXO = ResourceTuple(22006, "fxo", "Other", "binary")
    GAD = ResourceTuple(22007, "gad", "Other", "binary")
    GDA = ResourceTuple(  # Game data archive, Eclipse only
        22008, "gda", "Other", "binary", supported_engines=(BiowareEngine.Eclipse,)
    )
    GFX = ResourceTuple(  # Graphics file
        22009, "gfx", "Other", "binary"
    )
    LDF = ResourceTuple(22010, "ldf", "Other", "binary")
    LST = ResourceTuple(  # List file
        22011, "lst", "Other", "plaintext"
    )
    MAL = ResourceTuple(22012, "mal", "Other", "binary")
    MAO = ResourceTuple(22013, "mao", "Other", "binary")
    MMH = ResourceTuple(22014, "mmh", "Other", "binary")
    MOP = ResourceTuple(22015, "mop", "Other", "binary")
    MOR = ResourceTuple(22016, "mor", "Other", "binary")
    MSH = ResourceTuple(  # Mesh file
        22017, "msh", "Models", "binary"
    )
    MTX = ResourceTuple(22018, "mtx", "Other", "binary")
    NCC = ResourceTuple(22019, "ncc", "Other", "binary")
    PHY = ResourceTuple(  # Physics file
        22020, "phy", "Other", "binary"
    )
    PLO = ResourceTuple(22021, "plo", "Other", "binary")
    STG = ResourceTuple(22022, "stg", "Other", "binary")
    TBI = ResourceTuple(22023, "tbi", "Other", "binary")
    TNT = ResourceTuple(22024, "tnt", "Other", "binary")
    ARL = ResourceTuple(22025, "arl", "Other", "binary")
    FEV = ResourceTuple(22026, "fev", "Other", "binary")
    FSB = ResourceTuple(  # FMOD Sound Bank
        22027, "fsb", "Audio", "binary"
    )
    OPF = ResourceTuple(22028, "opf", "Other", "binary")
    CRF = ResourceTuple(22029, "crf", "Other", "binary")
    RIMP = ResourceTuple(22030, "rimp", "Other", "binary")
    MET = ResourceTuple(22031, "met", "Other", "binary")
    META = ResourceTuple(  # Metadata file
        22032, "meta", "Other", "binary"
    )
    FXR = ResourceTuple(22033, "fxr", "Other", "binary")
    FXT = ResourceTuple(22033, "fxt", "Other", "binary")
    CIF = ResourceTuple(22034, "cif", "Other", "binary")
    CUB = ResourceTuple(22035, "cub", "Other", "binary")
    DLB = ResourceTuple(22036, "dlb", "Other", "binary")
    NSC = ResourceTuple(22037, "nsc", "Other", "binary")
    MOV = ResourceTuple(  # QuickTime movie
        23000, "mov", "Video", "binary"
    )
    CURS = ResourceTuple(  # Cursor resource
        23001, "curs", "Other", "binary"
    )
    PICT = ResourceTuple(  # PICT image
        23002, "pict", "Images", "binary"
    )
    RSRC = ResourceTuple(  # Resource file
        23003, "rsrc", "Other", "binary"
    )
    PLIST = ResourceTuple(  # Property list
        23004, "plist", "Other", "plaintext"
    )
    CRE = ResourceTuple(  # Creature file
        24000, "cre", "Creatures", "binary"
    )
    PSO = ResourceTuple(24001, "pso", "Other", "binary")
    VSO = ResourceTuple(24002, "vso", "Other", "binary")
    ABC = ResourceTuple(24003, "abc", "Other", "binary")
    SBM = ResourceTuple(24004, "sbm", "Other", "binary")
    PVD = ResourceTuple(24005, "pvd", "Other", "binary")
    PLA = ResourceTuple(24006, "pla", "Other", "binary")
    TRG = ResourceTuple(24007, "trg", "Other", "binary")
    PK = ResourceTuple(24008, "pk", "Other", "binary")
    ALS = ResourceTuple(25000, "als", "Other", "binary")
    APL = ResourceTuple(25001, "apl", "Other", "binary")
    ASSEMBLY = ResourceTuple(  # Assembly file
        25002, "assembly", "Other", "binary"
    )
    BAK = ResourceTuple(  # Backup file
        25003, "bak", "Other", "binary"
    )
    BNK = ResourceTuple(  # Audio bank
        25004, "bnk", "Audio", "binary"
    )
    CL = ResourceTuple(25005, "cl", "Other", "binary")
    CNV = ResourceTuple(25006, "cnv", "Other", "binary")
    CON = ResourceTuple(25007, "con", "Other", "binary")
    DAT = ResourceTuple(  # Data file
        25008, "dat", "Other", "binary"
    )
    DX11 = ResourceTuple(  # DirectX 11 file
        25009, "dx11", "Other", "binary"
    )
    IDS = ResourceTuple(  # IDS file
        25010, "ids", "Other", "plaintext"
    )
    LOG = ResourceTuple(25011, "log", "Other", "plaintext", supported_engines=(BiowareEngine.Odyssey,))
    MAP = ResourceTuple(  # Map file
        25012, "map", "Other", "binary"
    )
    MML = ResourceTuple(25013, "mml", "Other", "binary")
    PCK = ResourceTuple(  # Audio package
        25015, "pck", "Audio", "binary"
    )
    RML = ResourceTuple(25016, "rml", "Other", "binary")
    S = ResourceTuple(25017, "s", "Other", "binary")
    STA = ResourceTuple(25018, "sta", "Other", "binary")
    SVR = ResourceTuple(25019, "svr", "Other", "binary")
    VLM = ResourceTuple(25020, "vlm", "Other", "binary")
    WBD = ResourceTuple(25021, "wbd", "Other", "binary")
    XBX = ResourceTuple(25022, "xbx", "Other", "binary", supported_engines=(BiowareEngine.Odyssey,))
    XLS = ResourceTuple(  # Excel file
        25023, "xls", "Other", "binary"
    )
    BZF = ResourceTuple(26000, "bzf", "Other", "binary")
    ADV = ResourceTuple(  # Adventure file
        27000, "adv", "Other", "binary"
    )
    JSON = ResourceTuple(  # JSON file
        28000, "json", "Other", "plaintext"
    )
    TLK_EXPERT = ResourceTuple(  # Expert talk table
        28001, "tlk_expert", "Talk Tables", "binary"
    )
    TLK_MOBILE = ResourceTuple(  # Mobile talk table
        28002, "tlk_mobile", "Talk Tables", "binary"
    )
    TLK_TOUCH = ResourceTuple(  # Touch talk table
        28003, "tlk_touch", "Talk Tables", "binary"
    )
    OTF = ResourceTuple(  # OpenType font
        28004, "otf", "Fonts", "binary"
    )
    PAR = ResourceTuple(28005, "par", "Other", "binary")
    XWB = ResourceTuple(  # Xbox Wave Bank
        29000, "xwb", "Audio", "binary"
    )
    XSB = ResourceTuple(  # Xbox Sound Bank
        29001, "xsb", "Audio", "binary"
    )
    XDS = ResourceTuple(30000, "xds", "Other", "binary")
    WND = ResourceTuple(  # Window file
        30001, "wnd", "Other", "binary"
    )
    XEOSITEX = ResourceTuple(  # Xeositex texture
        40000, "xeositex", "Textures", "binary"
    )
    WBM = ResourceTuple(41000, "wbm", "Other", "binary")
    OneDA = ResourceTuple(  # Table data, 1-dimensional text array
        9996, "1da", "2D Arrays", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    ERF = ResourceTuple(  # Module resources
        9997, "erf", "Modules", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    BIF = ResourceTuple(  # Game resource data
        9998, "bif", "Archives", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )
    KEY = ResourceTuple(  # Game resource index
        9999, "key", "Chitin", "binary", supported_engines=(BiowareEngine.Aurora, BiowareEngine.Odyssey, BiowareEngine.Eclipse)
    )

    # Toolset/Editor-specific types (not used by game engine)
    # Define these here to ensure we don't reuse these numbers.
    GLSL = ResourceTuple(  # OpenGL Shading Language, toolset only
        0x1001, "glsl", "Scripts", "plaintext", supported_engines=()
    )
    CURSOR = ResourceTuple(  # Windows cursor, toolset only
        0x2000, "cursor", "Other", "binary", supported_engines=()
    )
    CURSORGROUP = ResourceTuple(  # Windows cursor group, toolset only
        0x2001, "cursorgroup", "Other", "binary", supported_engines=()
    )

    # For Toolset Use:
    # Note: MP3 is actually used by Odyssey engine (K1 has separate MP3 type, TSL uses type ID 8/BMU for MP3 extension)
    # This toolset-only entry is kept for compatibility but MP3 files in-game use BMU type ID 8 in TSL
    MP3 = ResourceTuple(  # MP3 audio, toolset only (BMU type ID 8 is used in-game for MP3 in TSL)
        25014, "mp3", "Audio", "binary", supported_engines=()
    )
    WAV_DEOB = ResourceTuple(  # Deobfuscated WAV (type_id 4 is obfuscated), toolset only
        50000, "wav", "Audio", "binary"
    )
    TLK_XML = ResourceTuple(  # TLK as XML, toolset only
        50001, "tlk.xml", "Talk Tables", "plaintext", supported_engines=(), target_member="TLK"
    )
    MDL_ASCII = ResourceTuple(  # MDL as ASCII text, toolset only
        50002, "mdl.ascii", "Models", "plaintext", supported_engines=(), target_member="MDL"
    )
    TwoDA_CSV = ResourceTuple(  # 2DA as CSV, toolset only
        50003, "2da.csv", "2D Arrays", "plaintext", supported_engines=(), target_member="TwoDA"
    )
    GFF_XML = ResourceTuple(  # GFF as XML, toolset only
        50004, "gff.xml", "Other", "plaintext", supported_engines=(), target_member="GFF"
    )
    GFF_JSON = ResourceTuple(  # GFF as JSON, toolset only
        50005, "gff.json", "Other", "plaintext", supported_engines=(), target_member="GFF"
    )
    IFO_XML = ResourceTuple(  # IFO as XML, toolset only
        50006, "ifo.xml", "Module Data", "plaintext", supported_engines=(), target_member="IFO"
    )
    GIT_XML = ResourceTuple(  # GIT as XML, toolset only
        50007, "git.xml", "Module Data", "plaintext", supported_engines=(), target_member="GIT"
    )
    UTI_XML = ResourceTuple(  # UTI as XML, toolset only
        50008, "uti.xml", "Items", "plaintext", supported_engines=(), target_member="UTI"
    )
    UTC_XML = ResourceTuple(  # UTC as XML, toolset only
        50009, "utc.xml", "Creatures", "plaintext", supported_engines=(), target_member="UTC"
    )
    DLG_XML = ResourceTuple(  # DLG as XML, toolset only
        50010, "dlg.xml", "Dialogs", "plaintext", supported_engines=(), target_member="DLG"
    )
    # Type ID 50011 is reserved/unused
    UTT_XML = ResourceTuple(  # UTT as XML, toolset only
        50012, "utt.xml", "Triggers", "plaintext", supported_engines=(), target_member="UTT"
    )
    UTS_XML = ResourceTuple(  # UTS as XML, toolset only
        50013, "uts.xml", "Sounds", "plaintext", supported_engines=(), target_member="UTS"
    )
    FAC_XML = ResourceTuple(  # FAC as XML, toolset only
        50014, "fac.xml", "Factions", "plaintext", supported_engines=(), target_member="FAC"
    )
    UTE_XML = ResourceTuple(  # UTE as XML, toolset only
        50015, "ute.xml", "Encounters", "plaintext", supported_engines=(), target_member="UTE"
    )
    UTD_XML = ResourceTuple(  # UTD as XML, toolset only
        50016, "utd.xml", "Doors", "plaintext", supported_engines=(), target_member="UTD"
    )
    UTP_XML = ResourceTuple(  # UTP as XML, toolset only
        50017, "utp.xml", "Placeables", "plaintext", supported_engines=(), target_member="UTP"
    )
    GUI_XML = ResourceTuple(  # GUI as XML, toolset only
        50018, "gui.xml", "GUIs", "plaintext", supported_engines=(), target_member="GUI"
    )
    UTM_XML = ResourceTuple(  # UTM as XML, toolset only
        50019, "utm.xml", "Merchants", "plaintext", supported_engines=(), target_member="UTM"
    )
    JRL_XML = ResourceTuple(  # JRL as XML, toolset only
        50020, "jrl.xml", "Journals", "plaintext", supported_engines=(), target_member="JRL"
    )
    UTW_XML = ResourceTuple(  # UTW as XML, toolset only
        50021, "utw.xml", "Waypoints", "plaintext", supported_engines=(), target_member="UTW"
    )
    PTH_XML = ResourceTuple(  # PTH as XML, toolset only
        50022, "pth.xml", "Paths", "plaintext", supported_engines=(), target_member="PTH"
    )
    LIP_XML = ResourceTuple(  # LIP as XML, toolset only
        50023, "lip.xml", "Lips", "plaintext", supported_engines=(), target_member="LIP"
    )
    SSF_XML = ResourceTuple(  # SSF as XML, toolset only
        50024, "ssf.xml", "Soundsets", "plaintext", supported_engines=(), target_member="SSF"
    )
    ARE_XML = ResourceTuple(  # ARE as XML, toolset only
        50025, "are.xml", "Module Data", "plaintext", supported_engines=(), target_member="ARE"
    )
    TwoDA_JSON = ResourceTuple(  # 2DA as JSON, toolset only
        50026, "2da.json", "2D Arrays", "plaintext", supported_engines=(), target_member="TwoDA"
    )
    TLK_JSON = ResourceTuple(  # TLK as JSON, toolset only
        50027, "tlk.json", "Talk Tables", "plaintext", supported_engines=(), target_member="TLK"
    )
    LIP_JSON = ResourceTuple(  # LIP as JSON, toolset only
        50028, "lip.json", "Lips", "plaintext", supported_engines=(), target_member="LIP"
    )
    RES_XML = ResourceTuple(  # RES as XML, toolset only
        50029, "res.xml", "Save Data", "plaintext", supported_engines=(), target_member="RES"
    )

    def __init__(  # noqa: PLR0913
        self,
        type_id: int,
        extension: str,
        category: str,
        contents: str,
        is_invalid: bool = False,  # noqa: FBT001, FBT002
        target_member: str | None = None,
        supported_engines: tuple[BiowareEngine, ...] = (),
    ):
        self.type_id: int = type_id
        self.extension: str = extension.strip().lower()
        self.category: str = category
        self.contents: str = contents
        self.is_invalid: bool = is_invalid
        self.target_member: str | None = target_member
        self.supported_engines: tuple[BiowareEngine, ...] = supported_engines

    def is_gff(self) -> bool:
        """Returns True if this resourcetype is a gff, excluding the xml/json abstractions, False otherwise."""
        return self.contents == "gff"

    def target_type(self) -> Self:
        return self if self.target_member is None else self.__class__.__members__[self.target_member]

    @classmethod
    @lru_cache(maxsize=0xFFFF)
    def from_id(
        cls,
        type_id: int | str,
    ) -> ResourceType:
        """Returns the ResourceType for the specified id.

        Args:
        ----
            type_id: The resource id.

        Returns:
        -------
            The corresponding ResourceType object.
        """
        if isinstance(type_id, str):
            type_id = int(type_id)

        return next(
            (restype for restype in ResourceType.__members__.values() if type_id == restype),
            ResourceType.from_invalid(type_id=type_id),
        )

    @classmethod
    def from_extension(
        cls,
        extension: str,
    ) -> ResourceType:
        """Returns the ResourceType for the specified extension.

        This will slice off the leading dot in the extension, if it exists.

        Args:
        ----
            extension: The resource's extension. This is case-insensitive

        Returns:
        -------
            The corresponding ResourceType object.
        """
        lower_ext: str = extension.lower()
        if lower_ext.startswith("."):
            lower_ext = lower_ext[1:]
        return next(
            (restype for restype in ResourceType.__members__.values() if lower_ext == restype.extension),
            ResourceType.from_invalid(extension=lower_ext),
        )

    @classmethod
    def from_invalid(
        cls,
        **kwargs,
    ):
        if not kwargs:
            return cls.INVALID
        instance = object.__new__(cls)
        name = f"INVALID_{kwargs.get('extension', kwargs.get('type_id', cls.INVALID.extension)) or uuid.uuid4().hex}"
        while name in cls.__members__:
            name = f"INVALID_{kwargs.get('extension', kwargs.get('type_id', cls.INVALID.extension))}{uuid.uuid4().hex}"
        instance._name_ = name
        instance._value_ = ResourceTuple(
            type_id=kwargs.get("type_id", cls.INVALID.type_id),
            extension=kwargs.get("extension", cls.INVALID.extension),
            category=kwargs.get("category", cls.INVALID.category),
            contents=kwargs.get("contents", cls.INVALID.contents),
            is_invalid=kwargs.get("is_invalid", cls.INVALID.is_invalid),
            target_member=kwargs.get("target_member", cls.INVALID.target_member),
            supported_engines=kwargs.get("supported_engines", cls.INVALID.supported_engines),
        )
        instance.__init__(
            type_id=kwargs.get("type_id", cls.INVALID.type_id),
            extension=kwargs.get("extension", cls.INVALID.extension),
            category=kwargs.get("category", cls.INVALID.category),
            contents=kwargs.get("contents", cls.INVALID.contents),
            is_invalid=kwargs.get("is_invalid", cls.INVALID.is_invalid),
            target_member=kwargs.get("target_member", cls.INVALID.target_member),
            supported_engines=kwargs.get("supported_engines", cls.INVALID.supported_engines),
        )
        return super().__new__(cls, instance)

    def validate(self):
        if not self:
            msg = f"Invalid ResourceType: '{self!r}'"
            raise ValueError(msg)
        return self

    def __bool__(self) -> bool:
        return not self.is_invalid

    def __repr__(self) -> str:  # sourcery skip: simplify-fstring-formatting
        if self.name == "INVALID" or not self.is_invalid:
            return f"{self.__class__.__name__}.{self.name}"

        return (  # For dynamically constructed invalid members
            f"{self.__class__.__name__}.from_invalid("
            f"{f'type_id={self.type_id}, '}"
            f"{f'extension={self.extension}, ' if self.extension else ''}"
            f"{f'category={self.category}, ' if self.category else ''}"
            f"contents={self.contents})"
        )

    def __str__(self) -> str:
        """Returns the extension in all caps."""
        return str(self.extension.upper())

    def __int__(self):
        """Returns the type_id."""
        return self.type_id

    def __eq__(
        self,
        other: ResourceType | str | int | object,
    ):
        """Two ResourceTypes are equal if they are the same.

        A ResourceType and a str are equal if the extension is case-sensitively equal to the string.
        A ResourceType and a int are equal if the type_id is equal to the integer.
        """
        # sourcery skip: assign-if-exp, merge-duplicate-blocks, reintroduce-else, remove-redundant-if, split-or-ifs
        if self is other:
            return True
        if isinstance(other, ResourceType):
            if self.is_invalid or other.is_invalid:
                return self.is_invalid and other.is_invalid
            return self.name == other.name
        if isinstance(other, (str, WrappedStr)):
            return self.extension == other.lower()
        if isinstance(other, int):
            return self.type_id == other
        return NotImplemented

    def __hash__(self):
        return hash(self.extension)

    def is_valid(self) -> bool:
        return not self.is_invalid
