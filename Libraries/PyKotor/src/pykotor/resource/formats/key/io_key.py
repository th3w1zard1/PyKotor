"""This module handles reading and writing KEY files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.misc import ResRef
from pykotor.resource.formats.key.key_data import KEY, BifEntry, KeyEntry
from pykotor.resource.type import ResourceReader, ResourceType, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class KEYBinaryReader(ResourceReader):
    """Reads KEY files.
    
    KEY files index game resources stored in BIF files. They contain references to BIF files
    and resource entries that map ResRefs to locations within those BIF files.
    
    References:
    ----------
        Based on swkotor.exe KEY structure:
        - CExoKeyTable::CExoKeyTable @ 0x0040d030 - Key table constructor (157 bytes, 2 callees)
          * Initializes key table structure
          * Sets up BIF file list and resource entry table
        - CExoKeyTable::AddKeyTable @ 0x00406e20 - Adds key table (478 bytes, 14 callees)
          * Loads KEY file and adds to resource manager
          * Parses KEY file header, BIF entries, and key entries
        - CExoKeyTable::AddKeyTableContents @ 0x0040fb80 - Adds key table contents (1529 bytes, 24 callees)
          * Loads BIF files referenced in KEY table
          * Registers resources from BIF files in key table
          * Handles BIF file location and validation
        - CExoKeyTable::LocateBifFile @ 0x0040d200 - Locates BIF file (194 bytes)
          * Searches for BIF file in resource directories
          * Validates BIF file exists and is accessible
        - CExoKeyTable::GetKeyEntryFromTable @ 0x004071a0 - Gets key entry from table (143 bytes, 3 callees)
        - CExoKeyTable::DestroyTable @ 0x0040d2e0 - Destroys key table (418 bytes, 7 callees)
        - "BIF" string @ 0x0073d8dc - BIF file type identifier
        - "CExoKeyTable::DestroyTable: Resource %s still in demand during table deletion" @ 0x0073e0d8 - Error message
        - "CExoKeyTable::AddKey: Duplicate Resource " @ 0x0073e184 - Duplicate resource error
        - KEY file format: "KEY " type, "V1.0" version, BIF count, key count, file table offset, key table offset
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Missing Features:
        ----------------
        - ResRef lowercasing (reone lowercases resrefs)
        - Resource ID decomposition (reone decomposes resource_id into bif_index/resource_index)

    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self.key: KEY = KEY()

    @autoclose
    def load(self, *, auto_close: bool = True) -> KEY:  # noqa: FBT001, FBT002, ARG002
        """Load KEY data from source."""
        
        # Read signature
        self.key.file_type = self._reader.read_string(4)
        self.key.file_version = self._reader.read_string(4)

        if self.key.file_type != KEY.FILE_TYPE:
            msg = f"Invalid KEY file type: {self.key.file_type}"
            raise ValueError(msg)

        if self.key.file_version != KEY.FILE_VERSION:
            msg = f"Unsupported KEY version: {self.key.file_version}"
            raise ValueError(msg)

        # Read counts and offsets
        bif_count: int = self._reader.read_uint32()
        key_count: int = self._reader.read_uint32()
        file_table_offset: int = self._reader.read_uint32()
        key_table_offset: int = self._reader.read_uint32()

        # Read build info
        self.key.build_year = self._reader.read_uint32()
        self.key.build_day = self._reader.read_uint32()

        # there's 32 bytes of reserved bytes here.

        # Read file table
        self._reader.seek(file_table_offset)
        for _ in range(bif_count):
            bif: BifEntry = BifEntry()
            bif.filesize = self._reader.read_uint32()
            filename_offset: int = self._reader.read_uint32()
            filename_size: int = self._reader.read_uint16()
            bif.drives = self._reader.read_uint16()

            # Save current position
            current_pos: int = self._reader.position()

            # Read filename
            self._reader.seek(filename_offset)
            bif.filename = self._reader.read_string(filename_size).rstrip("\0").replace("\\", "/").lstrip("/")

            # Restore position
            self._reader.seek(current_pos)
            self.key.bif_entries.append(bif)

        # Read key table
        self._reader.seek(key_table_offset)
        for _ in range(key_count):
            entry: KeyEntry = KeyEntry()
            
            # reone lowercases resref at line 46
            resref_str = self._reader.read_string(16).rstrip("\0").lower()
            entry.resref = ResRef(resref_str)
            entry.restype = ResourceType.from_id(self._reader.read_uint16())
            
            # NOTE: reone decomposes resource_id into bif_index/resource_index, PyKotor stores as-is
            entry.resource_id = self._reader.read_uint32()
            self.key.key_entries.append(entry)

        self.key.build_lookup_tables()

        return self.key


class KEYBinaryWriter(ResourceWriter):
    """Writes KEY files."""

    def __init__(
        self,
        key: KEY,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.key: KEY = key

    @autoclose
    def write(self, *, auto_close: bool = True) -> None:  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        """Write KEY data to target."""
        self._write_header()
        self._write_file_table()
        self._write_key_table()

    def _write_header(self) -> None:
        """Write KEY file header."""
        # Write signature
        self._writer.write_string(self.key.file_type)
        self._writer.write_string(self.key.file_version)

        # Write counts
        self._writer.write_uint32(len(self.key.bif_entries))
        self._writer.write_uint32(len(self.key.key_entries))

        # Write table offsets
        self._writer.write_uint32(self.key.calculate_file_table_offset())
        self._writer.write_uint32(self.key.calculate_key_table_offset())

        # Write build info
        self._writer.write_uint32(self.key.build_year)
        self._writer.write_uint32(self.key.build_day)

        # Write reserved bytes
        self._writer.write_bytes(b"\0" * 32)

    def _write_file_table(self) -> None:
        """Write BIF file table."""
        # Write file entries
        for i, bif in enumerate(self.key.bif_entries):
            self._writer.write_uint32(bif.filesize)
            self._writer.write_uint32(self.key.calculate_filename_offset(i))
            self._writer.write_uint16(len(bif.filename) + 1)  # +1 for null terminator
            self._writer.write_uint16(bif.drives)

        # Write filenames
        for bif in self.key.bif_entries:
            self._writer.write_string(bif.filename)
            self._writer.write_uint8(0)  # Null terminator

    def _write_key_table(self) -> None:
        """Write resource key table."""
        for entry in self.key.key_entries:
            # Write ResRef (padded with nulls to 16 bytes)
            resref: str = str(entry.resref)
            self._writer.write_string(resref)
            self._writer.write_bytes(b"\0" * (16 - len(resref)))

            # Write type and ID
            self._writer.write_uint16(entry.restype.type_id)
            self._writer.write_uint32(entry.resource_id)
