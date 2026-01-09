"""This module handles classes relating to editing SSF files.

SSF (Sound Set File) files contain mappings from sound event types to string references (StrRefs)
in the TLK file. Each SSF defines a set of 28 sound effects that creatures can play during
various game events (battle cries, pain grunts, selection sounds, etc.). The StrRefs point
to entries in dialog.tlk which contain the actual WAV file references.

References:
----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
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

from enum import IntEnum

from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType


class SSF(ComparableMixin):
    """Represents a SSF (Sound Set File) containing creature sound event mappings.
    
    SSF files map 28 predefined sound event types to string references (StrRefs) in the
    TLK file. When a creature needs to play a sound (e.g., battle cry, pain grunt), the
    game looks up the StrRef from the SSF and then retrieves the actual WAV filename from
    the TLK entry. This allows different creatures to have different sound sets while
    sharing the same event type system.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        SSF file format specification


        
    Attributes:
    ----------
        _sounds: Array of 28 StrRef values, one for each sound event type
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/SSFBinaryStructure.cs:67 (SoundStringRefs[40] array, but only 28 used)
            Reference: https://github.com/th3w1zard1/KotOR_IO/tree/master/SSF.cs:51-54 (28 entries read)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFObject.ts:17,42-44 (sound_refs array, 28 entries)
            Index corresponds to SSFSound enum value
            Each value is a StrRef (int32) into dialog.tlk
            Value -1 indicates no sound for that event type
            Array length fixed at 28 for KotOR (some implementations use 40 for NWN compatibility)
    """

    BINARY_TYPE = ResourceType.SSF
    COMPARABLE_SEQUENCE_FIELDS = ("_sounds",)

    def __init__(self):
        # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Formats/KotorSSF/SSFBinaryStructure.cs:67
        # https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File Formats/SSF.cs:51-54
        # https://github.com/th3w1zard1/KotOR.js/tree/master/src/resource/SSFObject.ts:17,42-44
        # Array of 28 StrRef values (one per sound event type)
        # Index maps to SSFSound enum, value is StrRef into dialog.tlk
        # -1 indicates no sound for that event type
        self._sounds: list[int] = [-1] * 28

    def __eq__(self, other):
        if not isinstance(other, SSF):
            return NotImplemented
        return self._sounds == other._sounds

    def __hash__(self):
        return hash(tuple(self._sounds))

    def __getitem__(
        self,
        item,
    ):
        """Returns the stringref for the specified sound."""
        if not isinstance(item, SSFSound):
            return NotImplemented
        return self._sounds[item]

    def reset(self):
        """Sets all the sound stringrefs to -1."""
        for i in range(28):
            self._sounds[i] = -1

    def set_data(
        self,
        sound: SSFSound,
        stringref: int,
    ):
        """Set the stringref for the specified sound.

        Args:
        ----
            sound: The sound.
            stringref: The new stringref for the sound.
        """
        self._sounds[sound] = stringref

    def get(
        self,
        sound: SSFSound,
    ) -> int | None:
        """Returns the stringref for the specified sound.

        Args:
        ----
            sound: The sound.

        Returns:
        -------
            The corresponding stringref.
        """
        return self._sounds[sound]


class SSFSound(IntEnum):
    """Enumeration of sound event types used in SSF files.
    
    Each value represents a specific game event that can trigger a sound effect.
    The SSF file maps these event types to StrRefs in dialog.tlk, which in turn
    reference the actual WAV files to play. This system allows different creatures
    to have different sound sets while sharing the same event type definitions.
    
    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/KotOR_IO/tree/master/KotOR_IO/File (Reference_Tables.SSFields)
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/enums/resource/SSFType.ts:11-40
        https://github.com/th3w1zard1/KotOR-Bioware-Libs/tree/master/SSF.pm:15-42
        Sound Event Types:
        ------------------
        BATTLE_CRY_1-6 (0-5): Battle cry sounds played during combat

            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:12-17
            Used when creature enters combat or performs combat actions
            
        SELECT_1-3 (6-8): Selection sounds when creature is clicked/selected
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:18-20
            Played when player clicks on creature
            
        ATTACK_GRUNT_1-3 (9-11): Grunts during attack animations
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:21-23
            Used during melee/ranged attack animations
            
        PAIN_GRUNT_1-2 (12-13): Pain sounds when taking damage
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:24-25
            Played when creature receives damage
            
        LOW_HEALTH (14): Sound when health drops below threshold
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:26
            Typically played at ~25% health
            
        DEAD (15): Death sound when creature dies
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:27
            Played on creature death
            
        CRITICAL_HIT (16): Sound when creature scores critical hit
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:28
            Played when creature lands critical attack
            
        TARGET_IMMUNE (17): Sound when target is immune to attack
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:29
            Played when attack has no effect
            
        LAY_MINE (18): Sound when laying a mine
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:30
            
        DISARM_MINE (19): Sound when disarming a mine
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:31
            
        BEGIN_STEALTH (20): Sound when entering stealth mode
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:32
            
        BEGIN_SEARCH (21): Sound when starting search mode
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:33
            
        BEGIN_UNLOCK (22): Sound when starting lockpicking
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:34
            
        UNLOCK_FAILED (23): Sound when lockpicking fails
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:35
            
        UNLOCK_SUCCESS (24): Sound when lockpicking succeeds
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:36
            
        SEPARATED_FROM_PARTY (25): Sound when leaving party
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:37
            
        REJOINED_PARTY (26): Sound when rejoining party
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:38
            
        POISONED (27): Sound when creature is poisoned
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/SSFType.ts:39
    """
    
    BATTLE_CRY_1 = 0
    BATTLE_CRY_2 = 1
    BATTLE_CRY_3 = 2
    BATTLE_CRY_4 = 3
    BATTLE_CRY_5 = 4
    BATTLE_CRY_6 = 5
    SELECT_1 = 6
    SELECT_2 = 7
    SELECT_3 = 8
    ATTACK_GRUNT_1 = 9
    ATTACK_GRUNT_2 = 10
    ATTACK_GRUNT_3 = 11
    PAIN_GRUNT_1 = 12
    PAIN_GRUNT_2 = 13
    LOW_HEALTH = 14
    DEAD = 15
    CRITICAL_HIT = 16
    TARGET_IMMUNE = 17
    LAY_MINE = 18
    DISARM_MINE = 19
    BEGIN_STEALTH = 20
    BEGIN_SEARCH = 21
    BEGIN_UNLOCK = 22
    UNLOCK_FAILED = 23
    UNLOCK_SUCCESS = 24
    SEPARATED_FROM_PARTY = 25
    REJOINED_PARTY = 26
    POISONED = 27
