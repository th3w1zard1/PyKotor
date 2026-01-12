"""
SSF (Sound Set File) files contain mappings from sound event types to string references (StrRefs)
in the TLK file. Each SSF defines a set of 28 sound effects that creatures can play during
various game events (battle cries, pain grunts, selection sounds, etc.). The StrRefs point
to entries in dialog.tlk which contain the actual WAV file references.

References:
----------
    Based on swkotor.exe SSF structure:
    - LoadSSF - Loads SSF file for creature sound sets
      * Parses binary SSF format with "SSF V1.1" header
      * Reads offset to sound table (typically 12)
      * Reads 28 StrRef entries (4 bytes each, int32)
      * Maps sound event types to TLK string references
    - "SSF " file type identifier - First 4 bytes of SSF files
    - "V1.1" version identifier - Bytes 4-7 of SSF files
    - Offset to Sound Table field at offset 0x08 (4 bytes, uint32, typically 12)
    - Sound Table starts at offset 0x0C (112 bytes: 28 entries * 4 bytes)
      * Each entry is a StrRef (int32) into dialog.tlk
      * Value -1 indicates no sound for that event type
      * Index corresponds to SSFSound enum value (0-27)
    - ".ssf" extension - SSF file extension
    - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
    SSF file format specification
        Binary Format:
        -------------
        Header (12 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | char[] | File Type ("SSF ")
        0x04   | 4    | char[] | File Version ("V1.1")
        0x08   | 4    | uint32 | Offset to Sound Table (typically 12)
        Sound Table (112 bytes = 28 entries * 4 bytes):
        Offset | Size | Type   | Description
        -------|------|--------|-------------
        0x00   | 4    | int32  | StrRef for BATTLE_CRY_1
        0x04   | 4    | int32  | StrRef for BATTLE_CRY_2
        ...    | ...  | ...    | ...
        0x6C   | 4    | int32  | StrRef for POISONED
        Each entry is a StrRef (string reference) into dialog.tlk
        Value -1 indicates no sound for that event type
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class SSFBinaryReader(ResourceReader):
    """Reads SSF (Sound Set File) files.
    
    SSF files map sound event types to sound resource IDs. Used for creature sound sets
    that define battle cries, grunts, pain sounds, and other audio events.
    
    References:
    ----------
        Based on swkotor.exe SSF structure:
        - CResSSF::CResSSF @ 0x006db650 - Constructor for SSF resource
        - CResSSF::~CResSSF @ 0x006db670, @ 0x006db6b0 - Destructors for SSF resource
        - SSF file format: "SSF " type, "V1.1" version
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Note: SSF files map sound event types (BattleCry, Attack, Pain, etc.) to sound
        resource IDs. Used for creature sound sets that define battle cries, grunts,
        pain sounds, and other audio events.

    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._ssf: SSF | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> SSF:  # noqa: FBT001, FBT002, ARG002
        self._ssf = SSF()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "SSF ":
            msg = "Attempted to load an invalid SSF was loaded."
            raise ValueError(msg)

        if file_version != "V1.1":
            msg = "The supplied SSF file version is not supported."
            raise ValueError(msg)

        sounds_offset = self._reader.read_uint32()
        self._reader.seek(sounds_offset)

        
        # Read sound set entries (uint32 array, -1 indicates no sound)
        self._ssf.set_data(SSFSound.BATTLE_CRY_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_3, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_4, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_5, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_6, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.SELECT_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.SELECT_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.SELECT_3, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.ATTACK_GRUNT_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.ATTACK_GRUNT_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.ATTACK_GRUNT_3, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.PAIN_GRUNT_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.PAIN_GRUNT_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.LOW_HEALTH, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.DEAD, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.CRITICAL_HIT, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.TARGET_IMMUNE, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.LAY_MINE, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.DISARM_MINE, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BEGIN_STEALTH, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BEGIN_SEARCH, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BEGIN_UNLOCK, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.UNLOCK_FAILED, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.UNLOCK_SUCCESS, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(
            SSFSound.SEPARATED_FROM_PARTY,
            self._reader.read_uint32(max_neg1=True),
        )
        self._ssf.set_data(SSFSound.REJOINED_PARTY, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.POISONED, self._reader.read_uint32(max_neg1=True))

        return self._ssf


class SSFBinaryWriter(ResourceWriter):
    def __init__(
        self,
        ssf: SSF,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._ssf: SSF = ssf

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        self._writer.write_string("SSF ")
        self._writer.write_string("V1.1")
        self._writer.write_uint32(12)

        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_3) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_4) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_5) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_6) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_3) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_3) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.PAIN_GRUNT_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.PAIN_GRUNT_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.LOW_HEALTH) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.DEAD) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.CRITICAL_HIT) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.TARGET_IMMUNE) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.LAY_MINE) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.DISARM_MINE) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_STEALTH) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_SEARCH) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_UNLOCK) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.UNLOCK_FAILED) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.UNLOCK_SUCCESS) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SEPARATED_FROM_PARTY) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.REJOINED_PARTY) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.POISONED) or 0, max_neg1=True)

        for _ in range(12):
            self._writer.write_uint32(0xFFFFFFFF)
