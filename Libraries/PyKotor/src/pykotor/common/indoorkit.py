from __future__ import annotations

"""Indoor-kit data model (headless).

This module contains the *classes* for the Holocron indoor-kit format.

Design rule (repo convention):
- `pykotor.common.*` contains **classes / data models**
- `pykotor.tools.*` contains **functions / workflows**

Toolset/Qt-specific behavior (e.g. QImage previews) must live outside this module.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from utility.common.more_collections import CaseInsensitiveDict
from utility.common.geometry import Vector3

if TYPE_CHECKING:
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.utd import UTD
    from utility.common.geometry import Vector3


class Kit:
    """Indoor kit container.

    Note: kits on disk are deprecated for many workflows, but the data model remains
    useful for roundtrips and for Toolset interoperability.
    """

    def __init__(self, name: str, kit_id: str):
        self.name: str = name
        self.id: str = kit_id

        self.components: list[KitComponent] = []
        self.doors: list[KitDoor] = []

        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()

        self.always: dict[Path, bytes] = {}
        self.side_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.top_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.skyboxes: dict[str, MDLMDXTuple] = {}


class KitComponent:
    def __init__(self, kit: Kit, name: str, component_id: str, bwm: "BWM", mdl: bytes, mdx: bytes):
        self.kit: Kit = kit
        self.id: str = component_id
        self.name: str = name
        self.hooks: list[KitComponentHook] = []

        self.bwm: "BWM" = bwm
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx

        # ---- Indoor pipeline metadata ----
        # For ModuleKit components, we persist the original room placement from the module's LYT.
        # Keeping this as a real attribute (not dynamic) ensures typecheckers catch misuse.
        self.default_position: Vector3 = Vector3.from_null()

        # ---- Toolset UI metadata ----
        # Toolset attaches a Qt QImage preview for display. We deliberately type this as `object | None`
        # to keep `pykotor.common` free of Qt dependencies, while still making the attribute explicit.
        self.image: object | None = None


class KitComponentHook:
    def __init__(self, position: "Vector3", rotation: float, edge: int, door: "KitDoor"):
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.edge: int = edge
        self.door: KitDoor = door


@dataclass
class KitDoor:
    """Door blueprint reference for kit doorhooks.

    Compatibility note:
    - Toolset historically used snake_case (`utd_k1`, `utd_k2`) and sometimes a single `utd` alias.
    - PyKotor library code historically used camelCase (`utdK1`, `utdK2`).

    We provide both attribute spellings and a stable `utd` alias for K1 to keep old
    call sites working while we migrate imports.
    """

    utdK1: UTD
    utdK2: UTD
    width: float
    height: float

    # ---- compatibility aliases (no additional storage) ----
    @property
    def utd_k1(self) -> "UTD":  # noqa: D401
        """Alias for `utdK1`."""

        return self.utdK1

    @property
    def utd_k2(self) -> "UTD":  # noqa: D401
        """Alias for `utdK2`."""

        return self.utdK2

    @property
    def utd(self) -> "UTD":  # noqa: D401
        """Canonical single-blueprint alias (Toolset compatibility)."""

        return self.utdK1


class MDLMDXTuple(NamedTuple):
    mdl: bytes
    mdx: bytes


