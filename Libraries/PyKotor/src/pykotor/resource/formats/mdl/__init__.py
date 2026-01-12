"""MDL (Model) format for KotOR.

This module provides support for reading, writing, and manipulating MDL/MDX model files
used in Knights of the Old Republic (K1) and The Sith Lords (TSL).

MDL Format Overview:
-------------------
MDL files store 3D model geometry, animations, materials, and node hierarchies for
characters, creatures, placeables, and area geometry. MDL files contain hierarchical
node structures with:

- Geometry nodes (Trimesh, Skin, Danglymesh)
- Animation nodes (controllers for position, orientation, scale)
- Light nodes (point lights, spot lights, ambient)
- Emitter nodes (particle effects)
- Reference nodes (model references, placeables)
- Camera nodes (viewpoint definitions)

Each node can have:
- Position, orientation (quaternion), scale
- Controllers (keyframe animations)
- Children nodes (hierarchical structure)
- Node-specific data (geometry, lights, etc.)

The MDL file contains node hierarchy, animations, and metadata, while the MDX file
contains vertex data, faces, and geometry payload.

String References (GFF Field Names and Resource Identifiers):
-------------------------------------------------------------
All strings located via cross-reference search and verified in both executables.
These are used by the game engine for GFF field access and model resource identification.
For file extension strings used in I/O operations, see io_mdl.py documentation.

- "ModelName" @ (K1: 0x00749814, TSL: 0x007c1c8c)
  * GFF field name for storing/retrieving model resource references
  * K1: Referenced in 7 locations:
    - LoadDoor() @ (K1: 0x0058b23e, TSL: TODO: Find this address) (GFF field access for door models)
    - AddToArea() @ (K1: 0x00587276, TSL: TODO: Find this address) (area object model name)
    - AddPlaceableObjectStatic() @ (K1: 0x0060739b, TSL: TODO: Find this address), (K1: 0x006073d5, TSL: TODO: Find this address) (placeable model names)
    - HandleServerToPlayerDoorUpdate_Add() @ (K1: 0x0064d12a, TSL: TODO: Find this address) (network door updates)
    - HandleServerToPlayerPlaceableUpdate_Add() @ (K1: 0x0064d685, TSL: TODO: Find this address), (K1: 0x0064d6b4, TSL: TODO: Find this address) (network placeable updates)
  * TSL: Referenced in 7 locations (equivalent functions):
    - Door loading equivalent @ (K1: TODO: Find this address, TSL: 0x006532aa), (K1: TODO: Find this address, TSL: 0x006532e4)
    - Area addition equivalent @ (K1: TODO: Find this address, TSL: 0x00589de0)
    - Placeable static equivalent @ (K1: TODO: Find this address, TSL: 0x006a1eb6), (K1: TODO: Find this address, TSL: 0x006a1eda)
    - Creature loading equivalent @ (K1: TODO: Find this address, TSL: 0x006a187f)
    - Placeable related @ (K1: TODO: Find this address, TSL: 0x00582027)

- "ModelPart" @ (K1: 0x0074778c, TSL: 0x007bd42c)
  * GFF field for model part references in area files
  * LoadAreaHeader() @ (K1: 0x00509a0d, TSL: 0x004e4e3d) (area header GFF field)

- "MODELTYPE" @ (K1: 0x00747c2c, TSL: 0x007c036c)
  * Model type identifier

- "refModel" @ (K1: 0x00742a2c, TSL: 0x007babe8)
  * Reference model identifier

- "ModelVariation" @ (K1: 0x00748fac, TSL: 0x007c0990)
  * Model variation identifier

- "ModelPart1" @ (K1: 0x00749054, TSL: 0x007c0acc)
  * GFF field name for first model part in multi-part models

- "VisibleModel" @ (K1: 0x00749990, TSL: 0x007c1c98)
  * GFF field name for visible model flag/override

- "Model" @ (K1: 0x007499a0, TSL: 0x007c1ca8)
  * Generic model field name

Additional String References (verified in both K1 and TSL):
------------------------------------------------------------
- "c_FocusGobDummyModel%d" @ (K1: 0x007416e4, TSL: 0x007b985c)
  * Format string for dummy model names in focus object system

- "Model%d" @ (K1: 0x00751d5c, TSL: 0x007cae00)
  * Format string for numbered model references

- "modelhook" @ (K1: 0x0075244c, TSL: 0x007cb3b4)
  * Model hook identifier string

- "Bullet_Model" @ (K1: 0x007526d4, TSL: 0x007cb664)
  * Bullet/projectile model field name

- "Gun_Model" @ (K1: 0x007526ec, TSL: 0x007cb67c)
  * Gun model field name

- "RotatingModel" @ (K1: 0x0075297c, TSL: 0x007cb928)
  * Rotating model field name

- "Models" @ (K1: 0x0075298c, TSL: 0x007cb938)
  * Plural model identifier

- "headconjure" @ (K1: TODO: Find this address, TSL: 0x007c82f0)
  * Dummy node name for spell visual positioning
  * Referenced in LoadModel_Internal @ (K1: TODO: Find this address, TSL: 0x0066a1a5) via anim_base->vtable[0xa0]() call
  * Also referenced in 7 other functions for finding headconjure dummy node in model hierarchy

- "_head_hit" @ (K1: TODO: Find this address, TSL: 0x007ccaf8)
  * Hit detection node suffix
  * Referenced in 3 functions related to model hit detection setup
  * Hardcoded in CSWCPlaceable::LoadModel @ (K1: 0x006823f0, TSL: TODO: Find this address) (not in string table)

- "snd_Footstep" @ (K1: TODO: Find this address, TSL: 0x007c82d0)
  * Footstep sound callback name
  * Used to register footstep sound callback for creature animations
  * Referenced in RegisterCallbacks for headconjure @ (K1: TODO: Find this address, TSL: 0x00669570)

- "snd_hitground" @ (K1: TODO: Find this address, TSL: 0x007c82bc)
  * Hit ground sound callback name
  * Used to register hit ground sound callback for creature animations
  * Referenced in RegisterCallbacks for headconjure @ (K1: TODO: Find this address, TSL: 0x00669570)

Supermodel System String References:
-------------------------------------
These strings are used for the supermodel system. The supermodel directory path and resource
reference formats are present in TSL but may not exist in K1.

- "SUPERMODELS" @ (K1: TODO: Find this address, TSL: 0x007c69b0)
  * Supermodel system identifier

- ".\\supermodels" @ (K1: TODO: Find this address, TSL: 0x007c69bc)
  * Supermodel directory path (relative)

- "d:\\supermodels" @ (K1: TODO: Find this address, TSL: 0x007c69cc)
  * Supermodel directory path (absolute, likely debug/hardcoded)

- "SUPERMODELS:smseta" @ (K1: TODO: Find this address, TSL: 0x007c7380)
  * Supermodel resource reference format

- "SUPERMODELS:smsetb" @ (K1: TODO: Find this address, TSL: 0x007c73a8)
  * Supermodel resource reference variant

- "SUPERMODELS:smsetc" @ (K1: TODO: Find this address, TSL: 0x007c73a8)
  * Supermodel resource reference variant

- "ModelA" @ (K1: TODO: Find this address, TSL: 0x007bf4bc)
  * Model variant identifier

Error Messages:
---------------
- "CSWCCreature::LoadModel(): Failed to load creature model '%s'." @ (K1: 0x0074f85c, TSL: 0x007c82fc)
  * Referenced in CSWCCreature::LoadModel() @ (K1: 0x0061b5cf, TSL: 0x0066a0f0) (call site within LoadModel)
    - Used in sprintf() call when anim_base->vtable[3] returns 0
    - param_1 is resource name from CResRef::GetResRefStr()
  * Referenced in CSWCCreature::LoadModel error handler @ (K1: TODO: Find this address, TSL: 0x0066a0f0)
    - Used in sprintf equivalent @ (K1: TODO: Find this address, TSL: 0x0076dac2)
    - Resource name obtained via resource name cache/getter @ (K1: TODO: Find this address, TSL: 0x00406050)

- "Model %s nor the default model %s could be loaded." @ (K1: 0x00751c70, TSL: 0x007cad14)
  * Generic model loading failure message
  * Format: Takes two model names (requested and default fallback)
"""

from __future__ import annotations
from pykotor.resource.formats.mdl.mdl_data import (
    MDL,
    MDLNode,
    MDLMesh,
    MDLSkin,
    MDLConstraint,
    MDLDangly,
    MDLAnimation,
    MDLController,
    MDLControllerRow,
    MDLBoneVertex,
    MDLEmitter,
    MDLEvent,
    MDLLight,
    MDLFace,
    MDLReference,
    MDLSaber,
    MDLWalkmesh,
)
from pykotor.resource.formats.mdl.mdl_types import (
    MDLClassification,
    MDLControllerType,
    MDLNodeFlags,
    MDLNodeType,
    MDLGeometryType,
)
from pykotor.resource.formats.mdl.io_mdl import MDLBinaryReader, MDLBinaryWriter
from pykotor.resource.formats.mdl.io_mdl_ascii import MDLAsciiReader, MDLAsciiWriter
from pykotor.resource.formats.mdl.mdl_auto import bytes_mdl, write_mdl, read_mdl, read_mdl_fast, detect_mdl

__all__ = [
    "MDLClassification",
    "MDLController",
    "MDLControllerType",
    "MDLWalkmesh",
    "MDLReference",
    "MDLAnimation",
    "MDLSaber",
    "MDLControllerRow",
    "MDLConstraint",
    "MDLDangly",
    "MDLEmitter",
    "MDLEvent",
    "MDLFace",
    "MDL",
    "MDLLight",
    "MDLMesh",
    "MDLNode",
    "MDLSkin",
    "MDLBoneVertex",
    "MDLAsciiReader",
    "MDLAsciiWriter",
    "MDLBinaryReader",
    "MDLBinaryWriter",
    "MDLNodeFlags",
    "bytes_mdl",
    "read_mdl",
    "read_mdl_fast",
    "write_mdl",
    "detect_mdl",
]
