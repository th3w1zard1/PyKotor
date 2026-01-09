"""This module handles classes relating to editing ERF files.

ERF (Encapsulated Resource File) files are self-contained archives used for modules, save games,
texture packs, and hak paks. Unlike BIF files which require a KEY file for filename lookups,
ERF files store both resource names (ResRefs) and data in the same file. They also support
localized strings for descriptions in multiple languages.

References:
----------
        Based on swkotor.exe ERF structure:
        - CExoEncapsulatedFile::CExoEncapsulatedFile @ 0x0040ef90 - Constructor for encapsulated file
        - CExoKeyTable::AddEncapsulatedContents @ 0x0040f3c0 - Adds ERF/MOD/SAV contents to key table
          * Tries resource types in order: NWM, MOD, SAV, ERF
          * Opens file with "rb" mode
          * Reads header and resource entries
        - "MOD V1.0" string @ 0x0074539c - MOD file version identifier
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        ERF file format specification
        Binary Format:
        -------------
        Header (160 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("ERF ", "MOD ", "SAV ", "HAK ")
        0x04   | 4    | char[] | File Version ("V1.0")
        0x08   | 4    | uint32 | Language Count
        0x0C   | 4    | uint32 | Localized String Size (total bytes)
        0x10   | 4    | uint32 | Entry Count (number of resources)
        0x14   | 4    | uint32 | Offset to Localized String List
        0x18   | 4    | uint32 | Offset to Key List
        0x1C   | 4    | uint32 | Offset to Resource List
        0x20   | 4    | uint32 | Build Year (years since 1900)
        0x24   | 4    | uint32 | Build Day (days since Jan 1)
        0x28   | 4    | uint32 | Description StrRef (TLK reference)
        0x2C   | 116  | byte[] | Reserved (padding, usually zeros)
        Localized String Entry (variable length per language):
        - 4 bytes: Language ID (see Language enum)
        - 4 bytes: String Size (length in bytes)
        - N bytes: String Data (UTF-8 encoded text)
        Key Entry (24 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 16   | char[] | ResRef (filename, null-padded, max 16 chars)
        0x10   | 4    | uint32 | Resource ID (index into resource list)
        0x14   | 2    | uint16 | Resource Type
        0x16   | 2    | uint16 | Unused (padding)
        Resource Entry (8 bytes each):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | uint32 | Offset to Resource Data
        0x04   | 4    | uint32 | Resource Size
        Resource Data:
        Raw binary data for each resource at specified offsets


    Reference: Original BioWare engine binaries (ERF format from swkotor.exe, swkotor2.exe)
        - CExoEncapsulatedFile::CExoEncapsulatedFile @ 0x0040ef90
        - CExoKeyTable::AddEncapsulatedContents @ 0x0040f3c0
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.resource.bioware_archive import ArchiveResource, BiowareArchive
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_erf_file, is_mod_file, is_sav_file

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import ResRef


class ERFResource(ArchiveResource):
    """A single resource stored in an ERF/MOD/SAV file.

    Unlike BIF resources, ERF resources include their ResRef (filename) directly in the
    archive. Each resource is identified by a unique ResRef and ResourceType combination.

    References:
    ----------
        Based on swkotor.exe ERF structure:
        - CExoEncapsulatedFile::CExoEncapsulatedFile @ 0x0040ef90 - Constructor for encapsulated file
        - CExoKeyTable::AddEncapsulatedContents @ 0x0040f3c0 - Adds ERF/MOD/SAV contents to key table
        - "MOD V1.0" string @ 0x0074539c - MOD file version identifier
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs - Key and Resource entries
        https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File Formats/ERF.cs - Key and Resource classes
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/interface/resource/IERFKeyEntry.ts - Key entry interface
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/interface/resource/IERFResource.ts - Resource entry interface


    Attributes:
    ----------
        All attributes inherited from ArchiveResource (resref, restype, data, size)
        ERF resources have no additional attributes beyond the base ArchiveResource
    """

    def __init__(self, resref: ResRef, restype: ResourceType, data: bytes):
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:119-120
        # https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File Formats/ERF.cs:197-198
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/ERFObject.ts:103-107
        # ResRef stored in Key Entry (16 bytes, null-padded)
        # ResourceType stored in Key Entry (2 bytes, uint16)
        # Resource data referenced via Resource Entry (offset + size)
        super().__init__(resref=resref, restype=restype, data=data)


class ERFType(Enum):
    """The type of ERF file based on file header signature.

    ERF files can have different type signatures depending on their purpose:
    - ERF: Generic encapsulated resource file (texture packs, etc.)
    - MOD: Module file (game areas/levels)
    - SAV: Save game file
    - HAK: Hak pak file (custom content, unused in KotOR)

    References:
    ----------
        Based on swkotor.exe ERF structure:
        - CExoEncapsulatedFile::CExoEncapsulatedFile @ 0x0040ef90 - Constructor for encapsulated file
        - CExoKeyTable::AddEncapsulatedContents @ 0x0040f3c0 - Adds ERF/MOD/SAV contents to key table
        - "MOD V1.0" string @ 0x0074539c - MOD file version identifier
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs - FileType field
        https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File Formats/ERF.cs - FileType reading
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/ERFObject.ts - File type default

    """

    ERF = "ERF "  # Generic ERF archive (texture packs, etc.)
    MOD = "MOD "  # Module file (game levels/areas)

    @classmethod
    def from_extension(cls, ext_or_filepath: os.PathLike | str) -> ERFType:
        if is_erf_file(ext_or_filepath):
            return cls.ERF
        if is_mod_file(ext_or_filepath):
            return cls.MOD
        if is_sav_file(ext_or_filepath):  # .SAV files still use the 'MOD ' signature in its first 4 bytes of the file header
            return cls.MOD
        msg = f"Invalid ERF extension in filepath '{ext_or_filepath}'."
        raise ValueError(msg)


class ERF(BiowareArchive):
    """Represents an ERF/MOD/SAV file.

    ERF (Encapsulated Resource File) is a self-contained archive format used for game modules,
    save games, and resource packs. Unlike BIF+KEY pairs, ERF files contain both resource names
    and data in a single file, making them ideal for distributable content like mods.

    References:
    ----------
        Based on swkotor.exe ERF structure:
        - CExoEncapsulatedFile::CExoEncapsulatedFile @ 0x0040ef90 - Constructor for encapsulated file
        - CExoKeyTable::AddEncapsulatedContents @ 0x0040f3c0 - Adds ERF/MOD/SAV contents to key table
        - "MOD V1.0" string @ 0x0074539c - MOD file version identifier
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs - FileRoot class
        https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File Formats/ERF.cs - Complete ERF implementation
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/ERFObject.ts - ERFObject class


    Attributes:
    ----------
        erf_type: File type signature (ERF, MOD, SAV, HAK)
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/ERFBinaryStructure.cs:73 (FileType property)
            Reference: https://github.com/th3w1zard1/KotOR_IO/tree/master/ERF.cs:46 (FileType field)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ERFObject.ts:45 (fileType default)
            Determines intended use of the archive
            ERF = texture packs, MOD = game modules, SAV = save games

        is_save: Flag indicating if this is a save game ERF
            Reference: https://github.com/th3w1zard1/KotOR_IO/tree/master/ERF.cs:15-16 (save game comment)
            Save games use MOD signature but have different structure
            Affects how certain fields are interpreted (e.g., build date)
            PyKotor-specific flag for save game handling
    """

    BINARY_TYPE = ResourceType.ERF
    ARCHIVE_TYPE: type[ArchiveResource] = ERFResource
    COMPARABLE_FIELDS = ("erf_type", "is_save_erf")
    COMPARABLE_SET_FIELDS = ("_resources",)

    def __init__(
        self,
        erf_type: ERFType = ERFType.ERF,
        *,
        is_save: bool = False,
    ):
        super().__init__()

        
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorERF/ERFBinaryStructure.cs:73
        # https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File Formats/ERF.cs:46
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/ERFObject.ts:45
        # File type signature (ERF, MOD, SAV, HAK)
        self.erf_type: ERFType = erf_type

        # PyKotor-specific flag for save game handling
        # Save games use MOD signature but have different behavior
        self.is_save: bool = is_save

    @property
    def is_save_erf(self) -> bool:
        """Alias for ComparableMixin compatibility."""
        return self.is_save

    @is_save_erf.setter
    def is_save_erf(self, value: bool) -> None:
        self.is_save = value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.erf_type!r}, is_save={self.is_save})"

    def __eq__(self, other: object):
        from pykotor.resource.formats.rim import RIM  # Prevent circular imports  # noqa: PLC0415

        if not isinstance(other, (ERF, RIM)):
            return NotImplemented
        return set(self._resources) == set(other._resources)

    def __hash__(self) -> int:
        return hash((self.erf_type, tuple(self._resources), self.is_save))

    def get_resource_offset(self, resource: ArchiveResource) -> int:
        from pykotor.resource.formats.erf.io_erf import ERFBinaryWriter

        entry_count = len(self._resources)
        offset_to_keys = ERFBinaryWriter.FILE_HEADER_SIZE
        data_start = offset_to_keys + ERFBinaryWriter.KEY_ELEMENT_SIZE * entry_count

        resource_index = self._resources.index(resource)
        offset = data_start + sum(len(res.data) for res in self._resources[:resource_index])

        return offset
