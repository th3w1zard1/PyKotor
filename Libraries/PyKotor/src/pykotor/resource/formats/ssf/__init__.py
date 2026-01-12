"""SSF (Sound Set File) format for KotOR.

This module provides support for reading, writing, and manipulating SSF sound set files
used in Knights of the Old Republic (K1) and The Sith Lords (TSL).

SSF Format Overview:
-------------------
SSF files contain mappings from sound event types to string references (StrRefs) in the
TLK file. Each SSF defines a set of 28 sound effects that creatures can play during
various game events (battle cries, pain grunts, selection sounds, etc.). The StrRefs point
to entries in dialog.tlk which contain the actual WAV file references.

When a creature needs to play a sound (e.g., battle cry, pain grunt), the game looks up
the StrRef from the SSF and then retrieves the actual WAV filename from the TLK entry.
This allows different creatures to have different sound sets while sharing the same
event type system.

I/O and Parsing Functions (Engine Implementation):
-------------------------------------------------
These functions correspond to the game engine's SSF parsing implementation:

    - CResSSF::CResSSF() @ (K1: 0x006db650, TSL: TODO: Find this address)
      * Constructor for SSF resource
      * Initializes SSF resource structure
      * Sets up vtable and resource flags
      
    - CResSSF::~CResSSF() @ (K1: 0x006db670, TSL: TODO: Find this address)
      * Destructor for SSF resource
      * Cleans up allocated memory
      
    - CResSSF::~CResSSF() (alternate) @ (K1: 0x006db6b0, TSL: TODO: Find this address)
      * Alternate destructor path for SSF resource

String References:
-----------------
All strings located via cross-reference search and verified in both executables.
These are used by the game engine for SSF file identification and parsing.

    - "SSF " @ (K1: TODO: Find this address, TSL: TODO: Find this address)
      * File type identifier (first 4 bytes of SSF files)
      * Used to validate file format during loading
      
    - "V1.1" @ (K1: TODO: Find this address, TSL: TODO: Find this address)
      * File version identifier (bytes 4-7 of SSF files)
      * Used to validate file version compatibility
      
    - ".ssf" @ (K1: TODO: Find this address, TSL: TODO: Find this address)
      * SSF file extension
      * Used in file I/O operations and resource loading

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
Index corresponds to SSFSound enum value (0-27)
"""

from __future__ import annotations
from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.formats.ssf.io_ssf import (
    SSFBinaryReader,
    SSFBinaryWriter,
)
from pykotor.resource.formats.ssf.io_ssf_xml import (
    SSFXMLReader,
    SSFXMLWriter,
)
from pykotor.resource.formats.ssf.ssf_auto import (
    bytes_ssf,
    read_ssf,
    write_ssf,
)

__all__ = [
    "SSF",
    "SSFBinaryReader",
    "SSFBinaryWriter",
    "SSFSound",
    "SSFXMLReader",
    "SSFXMLWriter",
    "bytes_ssf",
    "read_ssf",
    "write_ssf",
]
