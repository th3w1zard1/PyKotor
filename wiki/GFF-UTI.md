# UTI (Item)

Part of the [GFF File Format Documentation](GFF-File-Format).

UTI [files](GFF-File-Format) define [item templates](GFF-File-Format#uti-item) for all objects in creature inventories, containers, and stores. Items range from weapons and armor to quest items, upgrades, and consumables.

**Official Bioware Documentation:** For the authoritative Bioware Aurora Engine Item [format](GFF-File-Format) specification, see [Bioware Aurora Item Format](Bioware-Aurora-Item).

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/uti.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uti.py)

## Core Identity [fields](GFF-File-Format#file-structure)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | [ResRef](GFF-File-Format#resref) | Template identifier for this item |
| `Tag` | [CExoString](GFF-File-Format#cexostring) | Unique tag for script references |
| `LocalizedName` | [CExoLocString](GFF-File-Format#localizedstring) | Item name (localized) |
| `Description` | [CExoLocString](GFF-File-Format#localizedstring) | Generic description |
| `DescIdentified` | [CExoLocString](GFF-File-Format#localizedstring) | Description when identified |
| `Comment` | [CExoString](GFF-File-Format#cexostring) | Developer comment/notes |

## Base Item Configuration

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `BaseItem` | Int | [index](2DA-File-Format#row-labels) into [`baseitems.2da`](2DA-baseitems) (defines item [type](GFF-File-Format#data-types)) |
| `Cost` | DWord | Base [value](GFF-File-Format#data-types) in credits |
| `AddCost` | DWord | Additional cost from properties |
| `Plot` | Byte | Plot-critical item (cannot be sold/destroyed) |
| `Charges` | Byte | Number of uses remaining |
| `StackSize` | Word | Current stack quantity |
| `ModelVariation` | Byte | [model](MDL-MDX-File-Format) variation index (1-99) |
| `BodyVariation` | Byte | Body variation for armor (1-9) |
| `TextureVar` | Byte | [texture](TPC-File-Format) variation for armor (1-9) |

**BaseItem [types](GFF-File-Format#data-types)** (from [`baseitems.2da`](2DA-baseitems)):

- **0-10**: Various weapon types (shortsword, longsword, blaster, etc.)
- **11-30**: Armor [types](GFF-File-Format#data-types) and shields
- **31-50**: Quest items, grenades, medical supplies
- **51-70**: Upgrades, armbands, belts
- **71-90**: Droid equipment, special items
- **91+**: KotOR2-specific items

## Item Properties

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `PropertiesList` | List | Item properties and enchantments |
| `Upgradable` | Byte | Can accept upgrades (KotOR1 only) |
| `UpgradeLevel` | Byte | Current upgrade tier (KotOR2 only) |

**PropertiesList Struct [fields](GFF-File-Format#file-structure):**

- `PropertyName` (Word): [index](2DA-File-Format#row-labels) into [`itempropdef.2da`](2DA-itempropdef)
- `Subtype` (Word): Property subtype/category
- `CostTable` (Byte): Cost table [index](2DA-File-Format#row-labels)
- `CostValue` (Word): Cost [value](GFF-File-Format#data-types)
- `Param1` (Byte): First parameter
- `Param1Value` (Byte): First parameter [value](GFF-File-Format#data-types)
- `ChanceAppear` (Byte): Percentage chance to appear (random loot)
- `UsesPerDay` (Byte): Daily usage limit (0 = unlimited)
- `UsesLeft` (Byte): Remaining uses for today

**Common Item Properties:**

- **Attack Bonus**: +1 to +12 attack rolls
- **Damage Bonus**: Additional damage dice
- **Ability Bonus**: +1 to +12 to ability scores
- **Damage Resistance**: Reduce damage by amount/percentage
- **Saving Throw Bonus**: +1 to +20 to saves
- **Skill Bonus**: +1 to +50 to skills
- **Immunity**: Immunity to damage [type](GFF-File-Format#data-types) or condition
- **On Hit**: Cast spell/effect on successful hit
- **Keen**: Expanded critical threat range
- **Massive Criticals**: Bonus damage on critical hit

## Weapon-Specific [fields](GFF-File-Format#file-structure)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `WeaponColor` (KotOR2) | [byte](GFF-File-Format#byte) | Blade [color](GFF-File-Format#color) for lightsabers |
| `WeaponWhoosh` (KotOR2) | [byte](GFF-File-Format#byte) | Whoosh sound [type](GFF-File-Format#data-types) |

**Lightsaber [colors](GFF-File-Format#color)** (KotOR2 `WeaponColor`):

- 0: Blue, 1: Yellow, 2: Green, 3: Red
- 4: Violet, 5: Orange, 6: Cyan, 7: Silver
- 8: White, 9: Viridian, 10: Bronze

## Armor-Specific [fields](GFF-File-Format#file-structure)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `BodyVariation` | Byte | Body [model](MDL-MDX-File-Format) variation (1-9) |
| `TextureVar` | Byte | [texture](TPC-File-Format) variation (1-9) |
| `ModelVariation` | Byte | [model](MDL-MDX-File-Format) type (typically 1-3) |
| `ArmorRulesType` (KotOR2) | [byte](GFF-File-Format#byte) | Armor class category |

**Armor [model](MDL-MDX-File-Format) Variations:**

- **Body + [texture](TPC-File-Format) Variation**: Creates visual diversity
- Armor adapts to wearer's body [type](GFF-File-Format#data-types) and gender
- `appearance.2da` defines valid combinations

## Quest & Special Items

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Cannot be sold or destroyed |
| `Stolen` | Byte | Marked as stolen |
| `Cursed` | Byte | Cannot be unequipped |
| `Identified` | Byte | Player has identified the item |

**Plot Item Behavior:**

- Immune to destruction/selling
- Often required for quest completion
- Can have special script interactions

## Upgrade System (KotOR1)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `Upgradable` | Byte | Item accepts upgrade items |

**Upgrade Mechanism:**

- Weapon/armor can have upgrade slots
- Player applies upgrade items to base item
- Properties from upgrade merge into base
- Referenced in `upgradetypes.2da`

## Upgrade System (KotOR2 Enhanced)

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `UpgradeLevel` | Byte | Current upgrade tier (0-2) |
| `WeaponColor` | Byte | Lightsaber blade [color](GFF-File-Format#color) |
| `WeaponWhoosh` | Byte | Swing sound [type](GFF-File-Format#data-types) |
| `ArmorRulesType` | Byte | Armor restriction category |

**KotOR2 Upgrade Slots:**

- Weapons can have multiple upgrade slots
- Each slot has specific [type](GFF-File-Format#data-types) restrictions
- Lightsabers get [color](GFF-File-Format#color) customization
- Armor upgrades affect appearance

## Visual & Audio

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `ModelVariation` | Byte | Base [model](MDL-MDX-File-Format) [index](2DA-File-Format#row-labels) |
| `BodyVariation` | Byte | Body [model](MDL-MDX-File-Format) for armor |
| `TextureVar` | Byte | [texture](TPC-File-Format) variant |

**[model](MDL-MDX-File-Format) Resolution:**

1. Engine looks up `BaseItem` in [`baseitems.2da`](2DA-baseitems)
2. Retrieves [model](MDL-MDX-File-Format) prefix (e.g., `w_lghtsbr`)
3. Appends variations: `w_lghtsbr_001.mdl`
4. [textures](TPC-File-Format) follow similar pattern

## Palette & Editor

| [field](GFF-File-Format#file-structure) | [type](GFF-File-Format#data-types) | Description |
| ----- | ---- | ----------- |
| `PaletteID` | Byte | Toolset palette category |
| `Comment` | [CExoString](GFF-File-Format#cexostring) | Designer notes/documentation |

**Toolset Integration:**

- `PaletteID` organizes items in editor
- Does not affect gameplay
- Used for content creation workflow

## Implementation Notes

**Item Instantiation:**

1. **Template Loading**: [GFF](GFF-File-Format) [structure](GFF-File-Format#file-structure) parsed from [UTI](GFF-File-Format#uti-item)
2. **Property Application**: PropertiesList merged into item
3. **Cost Calculation**: Base cost + AddCost + property costs
4. **Visual Setup**: [model](MDL-MDX-File-Format)/[texture](TPC-File-Format) variants resolved
5. **Stack Handling**: StackSize determines inventory behavior

**Property System:**

- Properties defined in [`itempropdef.2da`](2DA-itempropdef)
- Each property has cost formula
- Properties stack or override based on [type](GFF-File-Format#data-types)
- Engine recalculates effects when equipped

**Performance Optimization:**

- Simple items (no properties) load fastest
- Complex property lists increase spawn time
- Stack-based items share template [data](GFF-File-Format#file-structure)
- Unique items (non-stackable) require instance [data](GFF-File-Format#file-structure)

**Common Item Categories:**

**Weapons:**

- Melee: lightsabers, swords, vibroblades
- Ranged: blasters, rifles, heavy weapons
- Properties: damage, attack bonus, critical

**Armor:**

- Light, Medium, Heavy classes
- Robes (Force user specific)
- Properties: AC bonus, resistance, ability boosts

**Upgrades:**

- Weapon: Power crystals, energy cells, lens
- Armor: Overlays, underlays, plates
- Applied via crafting interface

**Consumables:**

- Medpacs: Restore health
- Stimulants: Temporary bonuses
- Grenades: Area damage/effects
- Single-use or limited charges

**Quest Items:**

- Plot-flagged, cannot be lost
- Often no combat [value](GFF-File-Format#data-types)
- Trigger scripted events

**Droid Equipment:**

- Special items for droid party members
- Sensors, shields, weapons
- Different slot [types](GFF-File-Format#data-types) than organic characters
