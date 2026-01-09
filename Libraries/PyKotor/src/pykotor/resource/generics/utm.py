from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, InventoryItem, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTM:
    """Stores merchant data.
    
    UTM (User Template Merchant) files define merchant/store blueprints. Stored as GFF format
    with inventory, pricing, and script references. Merchants use UTM templates to define
    their inventory, buy/sell capabilities, and markup/down rates.

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x005c7180 - CSWSStore::LoadStore (1116 bytes, 189 lines)
                - Main UTM GFF parser entry point
                - Reads Tag, LocName, MarkDown, MarkUp, OnOpenStore, BuySellFlag, ItemList fields
                - Function signature: LoadStore(CSWSStore* this, CResGFF* param_1, CResStruct* param_2, int param_3)
                - Called from LoadFromTemplate (0x005c7760) and LoadStores (0x005057a0)
            - 0x005c6cd0 - CSWSStore::SaveStore
                - UTM GFF writer function
                - Writes all UTM fields to GFF structure
            - 0x0074bea4 - "BuySellFlag" string reference
            - 0x0074beb0 - "OnOpenStore" string reference
            - 0x0074bebc - "MarkUp" string reference
            - 0x0074bec4 - "MarkDown" string reference
            - 0x00747210 - "ItemList" string reference
            - 0x0074dcc8 - "utm" extension string (used in resource extension table)
        
        KotOR II / TSL (swkotor2.exe):
            - Functionally equivalent UTM parsing logic
            - Same GFF field structure and parsing behavior
            - String references at different addresses due to binary layout differences
        
        GFF Field Structure (from LoadStore analysis):
            - Root struct fields:
                - "Tag" (CExoString) - Merchant tag identifier
                - "LocName" (CExoLocString) - Localized merchant name
                - "MarkDown" (INT32) - Markdown percentage for buying from player
                - "MarkUp" (INT32) - Markup percentage for selling to player
                - "OnOpenStore" (CResRef) - Script ResRef executed when store opens
                - "BuySellFlag" (BYTE) - Bit flags: bit 0 = can buy, bit 1 = can sell
                - "ItemList" (GFFList) - List of inventory items
            - ItemList element struct fields:
                - "ObjectId" (DWORD) - Object ID for existing items (0x7f000000 if not set)
                - "InventoryRes" (CResRef) - Item template ResRef (used when loading from template)
                - "Infinite" (BYTE) - Flag indicating infinite stock (bit 2 of item bit_flags)
                - "Dropable" (BYTE) - Flag indicating item can be dropped (not directly in LoadStore, inferred from SaveStore)
        
        Note: UTM files are GFF format files with specific structure definitions (GFFContent.UTM)

    Derivations and Other Implementations:
    ----------
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTM/UTM.cs (UTM structure)
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTM/UTMDecompiler.cs (UTM parsing)
        https://github.com/th3w1zard1/KotOR-Bioware-Libs/tree/master/GFF.pm (GFF format implementation)


    Attributes:
    ----------
        resref: "ResRef" field. Merchant template ResRef.
            Unique identifier for this merchant template.
        
        name: "LocName" field. Localized merchant name.
            Display name shown in merchant interface.
        
        tag: "Tag" field. Merchant tag identifier.
            Used for script references and identification.
        
        mark_up: "MarkUp" field. Markup percentage for selling to player.
            Percentage added to base item price when player buys.
            Reference: merchants.2da for predefined markup values.
        
        mark_down: "MarkDown" field. Markdown percentage for buying from player.
            Percentage subtracted from base item price when player sells.
            Reference: merchants.2da for predefined markdown values.
        
        on_open: "OnOpenStore" field. Script executed when store opens.
            Script ResRef called when merchant interface is opened.
        
        comment: "Comment" field. Developer comment string.
            Not used by game engine.
        
        can_buy: Derived from "BuySellFlag" bit 0. Whether merchant can buy items.
            Bit 0: 1 = can buy, 0 = cannot buy.
        
        can_sell: Derived from "BuySellFlag" bit 1. Whether merchant can sell items.
            Bit 1: 1 = can sell, 0 = cannot sell.
        
        inventory: "ItemList" field. List of items in merchant inventory.
            Items available for purchase from this merchant.
            Each item has InventoryRes (ResRef), Infinite flag, and position.

        id: "ID" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.UTM

    def __init__(
        self,
        *,
        resref: ResRef = ResRef.from_blank(),
        name: LocalizedString = LocalizedString.from_invalid(),
        tag: str = "",
        mark_up: int = 0,
        mark_down: int = 0,
        on_open: ResRef = ResRef.from_blank(),
        comment: str = "",
        id: int = 5,
        can_buy: bool = False,
        can_sell: bool = False,
        inventory: list[InventoryItem] | None = None,
    ):
        self.resref: ResRef = resref
        self.comment: str = comment
        self.tag: str = tag

        self.name: LocalizedString = name

        self.can_buy: bool = can_buy
        self.can_sell: bool = can_sell

        self.mark_up: int = mark_up
        self.mark_down: int = mark_down

        self.on_open: ResRef = on_open

        self.inventory: list[InventoryItem] = list(inventory) if inventory is not None else []

        # Deprecated:
        self.id: int = id


def construct_utm(
    gff: GFF,
) -> UTM:
    utm = UTM()

    root: GFFStruct = gff.root
    utm.resref = root.acquire("ResRef", ResRef.from_blank())
    utm.name = root.acquire("LocName", LocalizedString.from_invalid())
    utm.tag = root.acquire("Tag", "")
    utm.mark_up = root.acquire("MarkUp", 0)
    utm.mark_down = root.acquire("MarkDown", 0)
    utm.on_open = root.acquire("OnOpenStore", ResRef.from_blank())
    utm.comment = root.acquire("Comment", "")
    utm.id = root.acquire("ID", 0)
    utm.can_buy = root.acquire("BuySellFlag", 0) & 1 != 0
    utm.can_sell = root.acquire("BuySellFlag", 0) & 2 != 0

    item_list: GFFList = root.acquire("ItemList", GFFList())
    for item_struct in item_list:
        item = InventoryItem(ResRef.from_blank())
        utm.inventory.append(item)
        item.droppable = bool(item_struct.acquire("Dropable", 0))
        item.resref = item_struct.acquire("InventoryRes", ResRef.from_blank())
        item.infinite = bool(item_struct.acquire("Infinite", 0))

    return utm


def dismantle_utm(
    utm: UTM,
    game: Game = Game.K2,  # noqa: ARG001
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTM)

    root: GFFStruct = gff.root
    root.set_resref("ResRef", utm.resref)
    root.set_locstring("LocName", utm.name)
    root.set_string("Tag", utm.tag)
    root.set_int32("MarkUp", utm.mark_up)
    root.set_int32("MarkDown", utm.mark_down)
    root.set_resref("OnOpenStore", utm.on_open)
    root.set_string("Comment", utm.comment)
    root.set_uint8("BuySellFlag", utm.can_buy + utm.can_sell * 2)

    item_list: GFFList = root.set_list("ItemList", GFFList())
    for i, item in enumerate(utm.inventory):
        item_struct: GFFStruct = item_list.add(i)
        item_struct.set_resref("InventoryRes", item.resref)
        item_struct.set_uint16("Repos_PosX", i)
        item_struct.set_uint16("Repos_PosY", 0)
        if item.droppable:
            item_struct.set_uint8("Dropable", int(item.droppable))
        if item.infinite:
            item_struct.set_uint8("Infinite", value=True)

    if use_deprecated:
        root.set_uint8("ID", utm.id)

    return gff


def read_utm(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTM:
    gff: GFF = read_gff(source, offset, size)
    return construct_utm(gff)


def write_utm(
    utm: UTM,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_utm(utm, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utm(
    utm: UTM,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_utm(utm, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
