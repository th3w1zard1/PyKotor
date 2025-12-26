from __future__ import annotations

"""Toolset indoor-kit package (Qt shim).

All **core** indoor-kit logic lives in PyKotor:
- Data model: `pykotor.common.indoorkit`
- Loaders/workflows: `pykotor.tools.indoorkit`

Toolset keeps only Qt preview helpers and thin compatibility wrappers here.
"""

from pykotor.common.indoorkit import Kit, KitComponent, KitComponentHook, KitDoor, MDLMDXTuple  # noqa: TID252
from pykotor.common.modulekit import ModuleKit, ModuleKitManager  # noqa: TID252
from .indoorkit_loader import load_kits  # noqa: TID252
from .qt_preview import ensure_component_image  # noqa: TID252


__all__ = [
    "Kit",
    "KitComponent",
    "KitComponentHook",
    "KitDoor",
    "MDLMDXTuple",
    "ModuleKit",
    "ModuleKitManager",
    "load_kits",
    "ensure_component_image",
]
