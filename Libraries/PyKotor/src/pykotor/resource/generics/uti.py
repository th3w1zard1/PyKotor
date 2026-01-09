from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, read_gff, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

ARMOR_BASE_ITEMS: set[int] = {35, 36, 37, 38, 39, 40, 41, 42, 43, 53, 58, 63, 64, 65, 69, 71, 85, 89, 98, 100, 102, 103}
""" Base Item IDs that are considered armor as per the 2DA files. """


class UTI:
    """Stores item data.

    UTI files are GFF-based format files that store item definitions including
    properties, costs, charges, and upgrade information.

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x0055fcd0 - CSWSItem::LoadDataFromGff (2927 bytes, 448 lines)
                - Main UTI GFF parser entry point
                - Loads all UTI template fields from GFF structure
                - Function signature: LoadDataFromGff(CSWSItem* this, CResGFF* param_1, CResStruct* param_2)
                - Called from LoadFromTemplate (0x005608b0) and LoadItem (0x00560970)
            - 0x00560970 - CSWSItem::LoadItem (445 bytes, 48 lines)
                - Loads item from GFF (used in containers/stores)
                - Reads EquippedRes, InventoryRes, Dropable, Pickpocketable
                - Calls LoadDataFromGff when no EquippedRes/InventoryRes present
            - 0x005608b0 - CSWSItem::LoadFromTemplate
                - Loads UTI template from ResRef
                - Calls LoadDataFromGff after loading GFF
            - 0x00747494 - "TemplateResRef" string reference
            - 0x00749018 - "BaseItem" string reference
            - 0x00748fec - "LocalizedName" string reference
            - 0x00748ffc - "DescIdentified" string reference
            - 0x00748f88 - "Charges" string reference
            - 0x00748f7c - "MaxCharges" string reference
            - 0x00748fe0 - "StackSize" string reference
        
        KotOR II / TSL (swkotor2.exe):
            - Functionally equivalent UTI parsing logic
            - Same GFF field structure and parsing behavior
            - String references at different addresses due to binary layout differences
        
        GFF Field Structure (from LoadDataFromGff analysis):
            - Root struct fields:
                - "BaseItem" (INT32) - Base item type identifier
                - "Tag" (CExoString) - Item tag identifier
                - "Identified" (BYTE) - Whether item is identified (bit 0 of bit_flags)
                - "Description" (CExoLocString) - Description when not identified
                - "DescIdentified" (CExoLocString) - Description when identified
                - "LocalizedName" (CExoLocString) - Localized item name
                - "StackSize" (WORD) - Maximum stack size
                - "Stolen" (BYTE) - Whether item is stolen (bit 5 of bit_flags)
                - "Upgrades" (DWORD) - Upgrade level/bitfield
                - "Dropable" (BYTE) - Whether item can be dropped (bit 3 of bit_flags)
                - "Pickpocketable" (BYTE) - Whether item can be pickpocketed (bit 4 of bit_flags)
                - "NonEquippable" (BYTE) - Whether item cannot be equipped (bit 6 of bit_flags)
                - "ModelVariation" (BYTE) - Model variation index
                - "ModelPart1" (BYTE) - Model part 1 index (fallback if ModelVariation is 0)
                - "TextureVar" (BYTE) - Texture variation (for armor items)
                - "Charges" (BYTE) - Current charges (default 0x32 = 50)
                - "MaxCharges" (BYTE) - Maximum charges
                - "NewItem" (BYTE) - New item flag (bit 7 of bit_flags)
                - "DELETING" (BYTE) - Deletion flag (bit 8 of bit_flags)
                - "AddCost" (DWORD) - Additional cost modifier
                - "Plot" (BYTE) - Whether item is plot-critical
                - "PropertiesList" (GFFList) - List of item properties
            - PropertiesList element struct fields:
                - "PropertyName" (WORD) - Property type identifier
                - "Subtype" (WORD) - Property subtype
                - "CostTable" (BYTE) - Cost table index
                - "CostValue" (WORD) - Cost value
                - "Param1" (BYTE) - Parameter 1
                - "Param1Value" (BYTE) - Parameter 1 value
                - "ChanceAppear" (BYTE) - Chance to appear (0-100)
                - "Useable" (BYTE) - Whether property is usable (default 1)
                - "UsesPerDay" (BYTE) - Uses per day limit (default 0xff = unlimited)
                - "UpgradeType" (BYTE) - Upgrade type (default 0xff)
        
        Note: UTI files are GFF format files with specific structure definitions (GFFContent.UTI)

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this item template.
        base_item: "BaseItem" field. Base item type identifier.
        name: "LocalizedName" field. Localized name of the item.
        description: "DescIdentified" field. Localized description when identified.
        description2: "Description" field. Localized description.
        tag: "Tag" field. Tag identifier for this item.
        charges: "Charges" field. Number of charges remaining.
        cost: "Cost" field. Base cost of the item.
        stack_size: "StackSize" field. Maximum stack size.
        plot: "Plot" field. Whether item is plot-critical.
        add_cost: "AddCost" field. Additional cost modifier.
        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
        comment: "Comment" field. Developer comment.
        upgrade_level: "UpgradeLevel" field. Upgrade level of the item.
        properties: List of UTIProperty objects representing item properties.
        body_variation: "BodyVariation" field. Body variation index. Armor items only.
        model_variation: "ModelVariation" field. Model variation index. Armor items only.
        texture_variation: "TextureVar" field. Texture variation index. Armor items only.
        stolen: "Stolen" field. Whether item is stolen. Deprecated.
        identified: "Identified" field. Whether item is identified. Deprecated.
    """

    BINARY_TYPE = ResourceType.UTI

    def __init__(self):
        self.resref: ResRef = ResRef.from_blank()
        self.base_item: int = 0
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.description2: LocalizedString = LocalizedString.from_invalid()
        self.tag: str = ""
        self.charges: int = 0
        self.cost: int = 0
        self.stack_size: int = 0
        self.plot: int = 0
        self.add_cost: int = 0
        self.palette_id: int = 0
        self.comment: str = ""

        self.upgrade_level: int = 0

        self.properties: list[UTIProperty] = []

        # Armor Items Only:
        self.body_variation: int = 0
        self.model_variation: int = 0
        self.texture_variation: int = 0

        # Deprecated:
        self.stolen: int = 0
        self.identified: int = 0

    def is_armor(self) -> bool:
        return self.base_item in ARMOR_BASE_ITEMS


class UTIProperty:
    """Represents an item property (enchantment, upgrade, etc.).

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x0055fcd0 - CSWSItem::LoadDataFromGff (2927 bytes, 448 lines)
                - Loads PropertiesList from UTI GFF structure
                - Function signature: LoadDataFromGff(CSWSItem* this, CResGFF* param_1, CResStruct* param_2)
                - Called from LoadFromTemplate (0x005608b0) and LoadItem (0x00560970)
            - Reads PropertiesList (GFFList) at line 150:
                - PropertyName (WORD) - property name identifier
                - Subtype (WORD) - property subtype identifier
                - CostTable (BYTE) - cost table identifier
                - CostValue (WORD) - cost value
                - Param1 (BYTE) - first parameter
                - Param1Value (BYTE) - first parameter value
                - ChanceAppear (BYTE) - chance this property appears (0-100)
                - Useable (BYTE) - usable flag (default: 1)
                - UsesPerDay (BYTE) - uses per day (default: 0xFF)
                - UpgradeType (BYTE) - upgrade type identifier (default: 0xFF)
        KotOR II / TSL (swkotor2.exe):
            - Functionally identical to K1 implementation
            - Same GFF structure and parsing logic

    Attributes:
    ----------
        cost_table: "CostTable" field. Cost table identifier.
        cost_value: "CostValue" field. Cost value.
        param1: "Param1" field. First parameter.
        param1_value: "Param1Value" field. First parameter value.
        property_name: "PropertyName" field. Property name identifier.
        subtype: "Subtype" field. Property subtype identifier.
        chance_appear: "ChanceAppear" field. Chance this property appears (0-100).
        upgrade_type: "UpgradeType" field. Upgrade type identifier.
    """
    def __init__(self):
        self.cost_table: int = 0
        self.cost_value: int = 0
        self.param1: int = 0
        self.param1_value: int = 0
        self.property_name: int = 0
        self.subtype: int = 0
        self.chance_appear: int = 100
        self.upgrade_type: int | None = None


def construct_uti_from_struct(struct: GFFStruct) -> UTI:
    new_gff = GFF(GFFContent.UTI)
    new_gff.root = deepcopy(struct)
    return construct_uti(new_gff)


def construct_uti(gff: GFF) -> UTI:
    """Constructs a UTI object from a GFF structure.
    
    Parses UTI (item template) data from a GFF file, reading all fields
    including properties, costs, charges, and upgrade information.
    
    References:
    ----------
        Based on swkotor.exe UTI structure:
        - CSWSItem::LoadDataFromGff @ 0x0055fcd0 - Loads item data from GFF
        - CSWSItem::LoadItem @ 0x00560970 - Loads item template
        - CResGFF::CreateGFFFile @ 0x00411260 - Creates GFF file structure
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
    """
    uti = UTI()

    root = gff.root
    uti.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    uti.base_item = root.acquire("BaseItem", 0)
    uti.name = root.acquire("LocalizedName", LocalizedString.from_invalid())
    uti.description = root.acquire("DescIdentified", LocalizedString.from_invalid())
    uti.description2 = root.acquire("Description", LocalizedString.from_invalid())
    uti.tag = root.acquire("Tag", "")
    uti.charges = root.acquire("Charges", 0)
    uti.cost = root.acquire("Cost", 0)
    uti.stack_size = root.acquire("StackSize", 0)
    uti.plot = root.acquire("Plot", 0)
    uti.add_cost = root.acquire("AddCost", 0)
    uti.palette_id = root.acquire("PaletteID", 0)
    uti.comment = root.acquire("Comment", "")
    uti.model_variation = root.acquire("ModelVariation", 0)
    uti.body_variation = root.acquire("BodyVariation", 0)
    uti.texture_variation = root.acquire("TextureVar", 0)
    uti.upgrade_level = root.acquire("UpgradeLevel", 0)
    uti.stolen = root.acquire("Stolen", 0)
    uti.identified = root.acquire("Identified", 0)

    # PropertiesList contains item properties (enchantments, upgrades, etc.)
    for property_struct in root.acquire("PropertiesList", GFFList()):
        prop = UTIProperty()
        uti.properties.append(prop)
        prop.cost_table = property_struct.acquire("CostTable", 0)
        prop.cost_value = property_struct.acquire("CostValue", 0)
        prop.param1 = property_struct.acquire("Param1", 0)
        prop.param1_value = property_struct.acquire("Param1Value", 0)
        prop.property_name = property_struct.acquire("PropertyName", 0)
        prop.subtype = property_struct.acquire("Subtype", 0)
        prop.chance_appear = property_struct.acquire("ChanceAppear", 100)

        if property_struct.exists("UpgradeType"):
            prop.upgrade_type = property_struct.acquire("UpgradeType", 0)

    return uti


def dismantle_uti(
    uti: UTI,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTI)

    root = gff.root
    root.set_resref("TemplateResRef", uti.resref)
    root.set_int32("BaseItem", uti.base_item)
    root.set_locstring("LocalizedName", uti.name)
    root.set_locstring("Description", uti.description2)
    root.set_locstring("DescIdentified", uti.description)
    root.set_string("Tag", uti.tag)
    root.set_uint8("Charges", uti.charges)
    root.set_uint32("Cost", uti.cost)
    root.set_uint16("StackSize", uti.stack_size)
    root.set_uint8("Plot", uti.plot)
    root.set_uint32("AddCost", uti.add_cost)
    root.set_uint8("PaletteID", uti.palette_id)
    root.set_string("Comment", uti.comment)

    properties_list: GFFList = root.set_list("PropertiesList", GFFList())
    for prop in uti.properties:
        properties_struct = properties_list.add(0)
        properties_struct.set_uint8("CostTable", prop.cost_table)
        properties_struct.set_uint16("CostValue", prop.cost_value)
        properties_struct.set_uint8("Param1", prop.param1)
        properties_struct.set_uint8("Param1Value", prop.param1_value)
        properties_struct.set_uint16("PropertyName", prop.property_name)
        properties_struct.set_uint16("Subtype", prop.subtype)
        properties_struct.set_uint8("ChanceAppear", prop.chance_appear)
        if prop.upgrade_type is not None:
            properties_struct.set_uint8("UpgradeType", prop.upgrade_type)

    root.set_uint8("ModelVariation", uti.model_variation)
    root.set_uint8("BodyVariation", uti.body_variation)
    root.set_uint8("TextureVar", uti.texture_variation)

    if game.is_k2():
        root.set_uint8("UpgradeLevel", uti.upgrade_level)

    if use_deprecated:
        root.set_uint8("Stolen", uti.stolen)
        root.set_uint8("Identified", uti.identified)

    return gff


def read_uti(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTI:
    gff = read_gff(source, offset, size)
    return construct_uti(gff)


def write_uti(
    uti: UTI,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff = dismantle_uti(uti, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_uti(
    uti: UTI,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_uti(uti, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
