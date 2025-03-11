"""MDL format handling for KotOR games."""
from __future__ import annotations

from resource.formats.mdl.mdl_auto import read_mdl, write_mdl, bytes_mdl
from resource.formats.mdl.io_mdl import MDLBinaryReader, MDLBinaryWriter
from resource.formats.mdl.mdl_data import MDL, MDLNode, MDLLight, MDLEmitter, MDLReference, MDLNodeFlags, MDLSkin, MDLDangly, MDLConstraint, MDLAnimation

__all__ = [
    "read_mdl",
    "write_mdl",
    "bytes_mdl",
    "MDLBinaryReader",
    "MDLBinaryWriter",
    "MDL",
    "MDLNode",
    "MDLLight",
    "MDLEmitter",
    "MDLReference",
    "MDLNodeFlags",
    "MDLSkin",
    "MDLDangly",
    "MDLConstraint",
    "MDLAnimation",
]
