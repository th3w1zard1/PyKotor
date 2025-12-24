from __future__ import annotations

import copy

from typing import TYPE_CHECKING, Any

from utility.common.more_collections import CaseInsensitiveDict

if TYPE_CHECKING:
    from pathlib import Path

    from qtpy.QtGui import QImage

    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.generics.utd import UTD
    from utility.common.geometry import Vector3


class Kit:
    def __init__(
        self,
        name: str,
    ):
        self.name: str = name
        self.always: dict[Path, bytes] = {}
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.skyboxes: CaseInsensitiveDict[MDLMDXTuple] = CaseInsensitiveDict()
        self.doors: list[KitDoor] = []
        self.components: list[KitComponent] = []
        self.name: str = name
        self.components: list[KitComponent] = []
        self.doors: list[KitDoor] = []
        self.textures: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.lightmaps: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.txis: CaseInsensitiveDict[bytes] = CaseInsensitiveDict()
        self.always: dict[Path, bytes] = {}
        self.side_padding: dict[int, dict[int, MDLMDXTuple]] = {}
        self.top_padding: dict[int, dict[int, MDLMDXTuple]] = {}


class KitComponentHook:
    def __init__(
        self,
        position: Vector3,
        rotation: float,
        edge: str,
        door: KitDoor,
    ):
        self.position: Vector3 = position
        self.rotation: float = rotation
        self.edge: str = edge
        self.door: KitDoor = door


class KitDoor:
    def __init__(
        self,
        utd_k1: UTD,
        utd_k2: UTD,
        width: float,
        height: float,
    ):
        self.utd_k1: UTD = utd_k1
        self.utd_k2: UTD = utd_k2
        self.width: float = width
        self.height: float = height

        # Primary door blueprint alias.
        # Some existing tooling assumes a single ``utd`` attribute; expose
        # ``utd`` as the K1-side blueprint for compatibility.
        # This class is specific to Holocron Toolset and does not mirror any
        # external engine implementation directly, but the shape is similar to
        # the door handling used in ``vendor/reone/src/door.*`` where a
        # dominant blueprint is treated as the canonical one.
        self.utd: UTD = utd_k1


class MDLMDXTuple:
    def __init__(
        self,
        mdl: bytes,
        mdx: bytes,
    ):
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx


class KitComponent:
    def __init__(
        self,
        kit: Kit,
        name: str,
        image: QImage,
        bwm: BWM,
        mdl: bytes,
        mdx: bytes,
    ):
        self.kit: Kit = kit
        self.image: QImage = image
        self.name: str = name
        self.hooks: list[KitComponentHook] = []

        self.bwm: BWM = bwm
        self.mdl: bytes = mdl
        self.mdx: bytes = mdx
    
    def __deepcopy__(self, memo: dict[int, Any]) -> KitComponent:
        """Custom deep copy implementation that handles QImage properly.
        
        QImage objects cannot be pickled, so we need to manually copy them
        using QImage.copy() instead of relying on the default deepcopy behavior.
        """
        # Create a new KitComponent with copied attributes
        # Copy the QImage using its copy() method (QImage is not pickleable)
        image_copy = self.image.copy() if self.image is not None else None
        
        # Deep copy other attributes
        bwm_copy = copy.deepcopy(self.bwm, memo)
        hooks_copy = copy.deepcopy(self.hooks, memo)
        
        # Create new instance
        new_component = KitComponent(
            self.kit,  # Keep reference to same kit (don't deep copy)
            self.name,  # String is immutable, can share
            image_copy if image_copy is not None else QImage(),
            bwm_copy,
            self.mdl,  # bytes are immutable, can share
            self.mdx,  # bytes are immutable, can share
        )
        new_component.hooks = hooks_copy
        
        return new_component
