# Welcome to the PyKotor Wiki

## Documentation

### For End Users

- [Installing Mods with HoloPatcher](Installing-Mods-with-HoloPatcher)

### For Mod Developers

- [HoloPatcher README for Mod Developers](HoloPatcher-README-for-mod-developers.)
- [TSLPatcher's Official Readme](TSLPatcher's-Official-Readme)
- [TSLPatcher Thread Complete Archive](TSLPatcher_Thread_Complete)
- [HoloPatcher Feature Coverage Overview](Explanations-on-HoloPatcher-Internal-Logic#feature-support-summary)
- **[TSLPatcher InstallList Syntax Guide](TSLPatcher-InstallList-Syntax)** ← Complete reference for [file](GFF-File-Format) installation
- **[TSLPatcher TLKList Syntax Guide](TSLPatcher-TLKList-Syntax)** ← Complete reference for TLK ([TalkTable](TLK-File-Format)) modifications
- **[TSLPatcher 2DAList Syntax Guide](TSLPatcher-2DAList-Syntax)** ← Complete reference for 2DA (Two-Dimensional [array](2DA-File-Format)) patches
- **[TSLPatcher GFFList Syntax Guide](TSLPatcher-GFFList-Syntax)** ← Complete reference for [GFF](GFF-File-Format) modifications
- **[TSLPatcher SSFList Syntax Guide](TSLPatcher-SSFList-Syntax)** ← Complete reference for SSF ([sound set files](SSF-File-Format)) modifications
- [Mod Creation Best Practices](Mod-Creation-Best-Practices)
- [KotorDiff Integration in KotorCLI](KotorDiff-Integration)

### Official Bioware Aurora Documentation

The following documents [ARE](GFF-File-Format#are-area) official Bioware Aurora Engine [file](GFF-File-Format) [format](GFF-File-Format) specifications. These [ARE](GFF-File-Format#are-area) authoritative references for the underlying [file](GFF-File-Format) [formats](GFF-File-Format) used by KotOR:

- **[2DA File Format](Bioware-Aurora-2DA)** - Official 2DA (Two-Dimensional [array](2DA-File-Format)) [format](GFF-File-Format) specification
- **[GFF File Format](Bioware-Aurora-GFF)** - Official Generic [file](GFF-File-Format) [format](GFF-File-Format) specification
- **[Common GFF Structs](Bioware-Aurora-CommonGFFStructs)** - Common [GFF](GFF-File-Format) [structure](GFF-File-Format#file-structure) definitions
- **[Area File Format](Bioware-Aurora-AreaFile)** - Official ARE (Area) [file](GFF-File-Format) [format](GFF-File-Format)
- **[Creature Format](Bioware-Aurora-Creature)** - Official UTC (Creature) [format](GFF-File-Format)
- **[Item Format](Bioware-Aurora-Item)** - Official UTI (Item) [format](GFF-File-Format)
- **[Door/Placeable Format](Bioware-Aurora-DoorPlaceableGFF)** - Official [UTD](GFF-File-Format#utd-door)/[UTP](GFF-File-Format#utp-placeable) [formats](GFF-File-Format)
- **[Encounter Format](Bioware-Aurora-Encounter)** - Official UTE (Encounter) [format](GFF-File-Format)
- **[Trigger Format](Bioware-Aurora-Trigger)** - Official UTT (Trigger) [format](GFF-File-Format)
- **[Waypoint Format](Bioware-Aurora-Waypoint)** - Official UTW (Waypoint) [format](GFF-File-Format)
- **[Store Format](Bioware-Aurora-Store)** - Official UTM (Store) [format](GFF-File-Format)
- **[Sound Object Format](Bioware-Aurora-SoundObject)** - Official UTS (Sound) [format](GFF-File-Format)
- **[Journal Format](Bioware-Aurora-Journal)** - Official JRL (Journal) [format](GFF-File-Format)
- **[Conversation Format](Bioware-Aurora-Conversation)** - Official DLG (Dialogue) [format](GFF-File-Format)
- **[IFO Format](Bioware-Aurora-IFO)** - Official [module info](GFF-File-Format#ifo-module-info) [format](GFF-File-Format)
- **[ERF Format](Bioware-Aurora-ERF)** - Official Encapsulated Resource [format](GFF-File-Format)
- **[Key/BIF Format](Bioware-Aurora-KeyBIF)** - Official [KEY](KEY-File-Format) and [BIF file](BIF-File-Format) [formats](GFF-File-Format)
- **[TalkTable Format](Bioware-Aurora-TalkTable)** - Official TLK ([Talk Table](TLK-File-Format)) [format](GFF-File-Format)
- **[SSF Format](Bioware-Aurora-SSF)** - Official [sound set files](SSF-File-Format) [format](GFF-File-Format)
- **[Localized Strings Format](Bioware-Aurora-LocalizedStrings)** - Official localized [strings](GFF-File-Format#cexostring) [format](GFF-File-Format)
- **[Faction Format](Bioware-Aurora-Faction)** - Official faction [data](GFF-File-Format#file-structure) [format](GFF-File-Format)
- **[Palette/ITP Format](Bioware-Aurora-PaletteITP)** - Official palette and ITP [formats](GFF-File-Format)

### Aurora Engine Basics

The BioWare Aurora Engine (used by KotOR, TSL, and Neverwinter Nights) uses a standardized resource system:

**[KEY](KEY-File-Format) [files](GFF-File-Format):**

- **[`chitin.key`](KEY-File-Format)**: Master [index](2DA-File-Format#row-labels) [file](GFF-File-Format) that maps resource names to [BIF archives](BIF-File-Format) locations
- **[`dialog.tlk`](TLK-File-Format)**: Text resource [file](GFF-File-Format) containing localized [strings](GFF-File-Format#cexostring) referenced by [StrRef](TLK-File-Format#string-references-strref) IDs
- **`kotor.ini` / `nwn.ini`**: Configuration [file](GFF-File-Format) with `[Alias]` section mapping logical directory names to physical paths

**Resource Resolution Order:**

1. Override folder (`override/`)
2. Currently loaded MOD/[ERF files](ERF-File-Format)
3. Currently loaded SAV file (if in-game)
4. [BIF files](BIF-File-Format) via [KEY](KEY-File-Format) lookup
5. Hardcoded defaults

**Resource [types](GFF-File-Format#data-types):**

The Aurora engine uses hexadecimal resource [type](GFF-File-Format#data-types) identifiers. Common [types](GFF-File-Format#data-types) include:

| Resource Name | [type](GFF-File-Format#data-types) ID | Description                                    |
| ------------- | ------- | ---------------------------------------------- |
| [MDL](MDL-MDX-File-Format)           | 0x07D2  | 3D [model](MDL-MDX-File-Format) [file](GFF-File-Format)                                   |
| [NCS](NCS-File-Format)           | 0x07DA  | Compiled NWScript bytecode                     |
| [NSS](NSS-File-Format)           | 0x07D9  | NWScript source code                            |
| [ARE](GFF-File-Format#are-area)           | 0x07DC  | Area definition                                 |
| [IFO](GFF-File-Format#ifo-module-info)           | 0x07DE  | Module information                              |
| [2DA](2DA-File-Format)           | 0x07E1  | Two-dimensional [array](2DA-File-Format) [data](GFF-File-Format#file-structure)                      |
| [TLK](TLK-File-Format)           | 0x07E2  | Talk table (localized [strings](GFF-File-Format#cexostring))                 |
| [TXI](TXI-File-Format)           | 0x07E6  | [texture](TPC-File-Format) information                             |
| [GIT](GFF-File-Format#git-game-instance-template)           | 0x07E7  | [game instance template](GFF-File-Format#git-game-instance-template)                          |
| [UTI](GFF-File-Format#uti-item)           | 0x07E9  | [item templates](GFF-File-Format#uti-item)                                   |
| [UTC](GFF-File-Format#utc-creature)           | 0x07EB  | [creature templates](GFF-File-Format#utc-creature)                               |
| [DLG](GFF-File-Format#dlg-dialogue)           | 0x07ED  | Dialogue/conversation                           |
| [GFF](GFF-File-Format)           | 0x07F5  | Generic [file](GFF-File-Format) format (container)                 |
| [UTE](GFF-File-Format#ute-encounter)           | 0x07F8  | [encounter template](GFF-File-Format#ute-encounter)                              |
| [UTD](GFF-File-Format#utd-door)           | 0x07FA  | [door templates](GFF-File-Format#utd-door)                                   |
| [UTP](GFF-File-Format#utp-placeable)           | 0x07FC  | [placeable templates](GFF-File-Format#utp-placeable)                              |
| [GUI](GFF-File-Format#gui-graphical-user-interface)           | 0x07FF  | User interface definition                       |
| [UTM](GFF-File-Format#utm-merchant)           | 0x0803  | Merchant/store template                         |
| [JRL](GFF-File-Format#jrl-journal)           | 0x0808  | Journal/quest log                               |
| SAV           | 0x0809  | [save game archives](ERF-File-Format)                               |
| [UTW](GFF-File-Format#utw-waypoint)           | 0x080A  | [waypoint template](GFF-File-Format#utw-waypoint)                               |
| [SSF](SSF-File-Format)           | 0x080C  | [sound set files](SSF-File-Format)                                  |
| HAK           | 0x080D  | Hak pak archive                                 |
| [ERF](ERF-File-Format)           | 0x270D  | Encapsulated resource [file](GFF-File-Format)                      |
| [BIF](BIF-File-Format)           | 0x270E  | BioWare [index](2DA-File-Format#row-labels) file (archive)                    |
| [KEY](KEY-File-Format)           | 0x270F  | [KEY](KEY-File-Format) table ([BIF](BIF-File-Format) [index](2DA-File-Format#row-labels))                          |

**Language IDs:**

Localized [strings](GFF-File-Format#cexostring) use language identifiers:

| Language        | ID |
| --------------- | -- |
| English         | 0  |
| French (Male)   | 2  |
| French (Female) | 3  |
| German (Male)   | 4  |
| German (Female) | 5  |
| Italian (Male)  | 6  |
| Italian (Female)| 7  |
| Spanish (Male)  | 8  |
| Spanish (Female)| 9  |

**Reference**: [`vendor/xoreos-docs/specs/torlack/basics.html`](vendor/xoreos-docs/specs/torlack/basics.html) - Tim Smith (Torlack)'s NWN [data](GFF-File-Format#file-structure) [file](GFF-File-Format) Basics documentation (Aurora engine fundamentals)

### [file](GFF-File-Format) Formats

- **[MDL/MDX File Format](MDL-MDX-File-Format)** ← Complete reference for 3D [model](MDL-MDX-File-Format) files
  - **[2DA File Format](2DA-File-Format)** ← Complete reference for Two-Dimensional [array](2DA-File-Format) format (see also [Official Bioware 2DA Documentation](Bioware-Aurora-2DA))
  - [acbonus.2da](2DA-acbonus)
  - [actions.2da](2DA-actions)
  - [ai_styles.2da](2DA-ai_styles)
  - [aiscripts.2da](2DA-aiscripts)
  - [aliensound.2da](2DA-aliensound)
  - [alienvo.2da](2DA-alienvo)
  - [ambientmusic.2da](2DA-ambientmusic)
  - [ambientsound.2da](2DA-ambientsound)
  - [ammunitiontypes.2da](2DA-ammunitiontypes)
  - [animations.2da](2DA-animations)
  - [appearance.2da](2DA-appearance)
  - [appearancesndset.2da](2DA-appearancesndset)
  - [areaeffects.2da](2DA-areaeffects)
  - [baseitems.2da](2DA-baseitems)
  - [bindablekeys.2da](2DA-bindablekeys)
  - [bodybag.2da](2DA-bodybag)
  - [bodyvariation.2da](2DA-bodyvariation)
  - [camerastyle.2da](2DA-camerastyle)
  - [chargenclothes.2da](2DA-chargenclothes)
  - [classes.2da](2DA-classes)
  - [classpowergain.2da](2DA-classpowergain)
  - [cls_atk_*.2da](2DA-cls_atk__pattern)
  - [cls_savthr_*.2da](2DA-cls_savthr__pattern)
  - [combatanimations.2da](2DA-combatanimations)
  - [creaturesize.2da](2DA-creaturesize)
  - [creaturespeed.2da](2DA-creaturespeed)
  - [credits.2da](2DA-credits)
  - [crtemplates.2da](2DA-crtemplates)
  - [cursors.2da](2DA-cursors)
  - [dialoganimations.2da](2DA-dialoganimations)
  - [difficultyopt.2da](2DA-difficultyopt)
  - [disease.2da](2DA-disease)
  - [doortypes.2da](2DA-doortypes)
  - [droiddischarge.2da](2DA-droiddischarge)
  - [effecticon.2da](2DA-effecticon)
  - [emotion.2da](2DA-emotion)
  - [encdifficulty.2da](2DA-encdifficulty)
  - [environment.2da](2DA-environment)
  - [exptable.2da](2DA-exptable)
  - [facialanim.2da](2DA-facialanim)
  - [feat.2da](2DA-feat)
  - [featgain.2da](2DA-featgain)
  - [feedbacktext.2da](2DA-feedbacktext)
  - [footstepsounds.2da](2DA-footstepsounds)
  - [forceshields.2da](2DA-forceshields)
  - [fractionalcr.2da](2DA-fractionalcr)
  - [gamespyrooms.2da](2DA-gamespyrooms)
  - [gender.2da](2DA-gender)
  - [genericdoors.2da](2DA-genericdoors)
  - [globalcat.2da](2DA-globalcat)
  - [grenadesnd.2da](2DA-grenadesnd)
  - [guisounds.2da](2DA-guisounds)
  - [heads.2da](2DA-heads)
  - [hen_companion.2da](2DA-hen_companion)
  - [hen_familiar.2da](2DA-hen_familiar)
  - [humanfirst.2da](2DA-humanfirst)
  - [humanlast.2da](2DA-humanlast)
  - [inventorysnds.2da](2DA-inventorysnds)
  - [iprp_abilities.2da](2DA-iprp_abilities)
  - [iprp_acmodtype.2da](2DA-iprp_acmodtype)
  - [iprp_aligngrp.2da](2DA-iprp_aligngrp)
  - [iprp_ammocost.2da](2DA-iprp_ammocost)
  - [iprp_ammotype.2da](2DA-iprp_ammotype)
  - [iprp_attackmod.2da](2DA-iprp_attackmod)
  - [iprp_bonusfeat.2da](2DA-iprp_bonusfeat)
  - [iprp_combatdam.2da](2DA-iprp_combatdam)
  - [iprp_costtable.2da](2DA-iprp_costtable)
  - [iprp_damagecost.2da](2DA-iprp_damagecost)
  - [iprp_damagered.2da](2DA-iprp_damagered)
  - [iprp_damagetype.2da](2DA-iprp_damagetype)
  - [iprp_damagevs.2da](2DA-iprp_damagevs)
  - [iprp_feats.2da](2DA-iprp_feats)
  - [iprp_immunity.2da](2DA-iprp_immunity)
  - [iprp_lightcol.2da](2DA-iprp_lightcol)
  - [iprp_monstdam.2da](2DA-iprp_monstdam)
  - [iprp_mosterhit.2da](2DA-iprp_mosterhit)
  - [iprp_onhit.2da](2DA-iprp_onhit)
  - [iprp_paramtable.2da](2DA-iprp_paramtable)
  - [iprp_protection.2da](2DA-iprp_protection)
  - [iprp_saveelement.2da](2DA-iprp_saveelement)
  - [iprp_savingthrow.2da](2DA-iprp_savingthrow)
  - [iprp_skillcost.2da](2DA-iprp_skillcost)
  - [iprp_spellres.2da](2DA-iprp_spellres)
  - [iprp_spells.2da](2DA-iprp_spells)
  - [iprp_traptype.2da](2DA-iprp_traptype)
  - [iprp_walk.2da](2DA-iprp_walk)
  - [iprp_weightinc.2da](2DA-iprp_weightinc)
  - [itempropdef.2da](2DA-itempropdef)
  - [itemprops.2da](2DA-itemprops)
  - [itempropsdef.2da](2DA-itempropsdef)
  - [keymap.2da](2DA-keymap)
  - [loadscreenhints.2da](2DA-loadscreenhints)
  - [loadscreens.2da](2DA-loadscreens)
  - [masterfeats.2da](2DA-masterfeats)
  - [merchants.2da](2DA-merchants)
  - [minglobalrim.2da](2DA-minglobalrim)
  - [modulesave.2da](2DA-modulesave)
  - [movies.2da](2DA-movies)
  - [musictable.2da](2DA-musictable)
  - [palette.2da](2DA-palette)
  - [pazaakdecks.2da](2DA-pazaakdecks)
  - [phenotype.2da](2DA-phenotype)
  - [placeableobjsnds.2da](2DA-placeableobjsnds)
  - [placeables.2da](2DA-placeables)
  - [planetary.2da](2DA-planetary)
  - [plot.2da](2DA-plot)
  - [poison.2da](2DA-poison)
  - [portraits.2da](2DA-portraits)
  - [prioritygroups.2da](2DA-prioritygroups)
  - [racialtypes.2da](2DA-racialtypes)
  - [ranges.2da](2DA-ranges)
  - [regeneration.2da](2DA-regeneration)
  - [repute.2da](2DA-repute)
  - [rumble.2da](2DA-rumble)
  - [skills.2da](2DA-skills)
  - [soundeax.2da](2DA-soundeax)
  - [soundset.2da](2DA-soundset)
  - [spells.2da](2DA-spells)
  - [stringtokens.2da](2DA-stringtokens)
  - [subrace.2da](2DA-subrace)
  - [surfacemat.2da](2DA-surfacemat)
  - [texpacks.2da](2DA-texpacks)
  - [textures.2da](2DA-textures)
  - [tilecolor.2da](2DA-tilecolor)
  - [traps.2da](2DA-traps)
  - [tutorial.2da](2DA-tutorial)
  - [tutorial_old.2da](2DA-tutorial_old)
  - [upcrystals.2da](2DA-upcrystals)
  - [upgrade.2da](2DA-upgrade)
  - [videoeffects.2da](2DA-videoeffects)
  - [videoquality.2da](2DA-videoquality)
  - [visualeffects.2da](2DA-visualeffects)
  - [weaponsounds.2da](2DA-weaponsounds)
  - [xptable.2da](2DA-xptable)
- **[TLK File Format](TLK-File-Format)** ← Complete reference for [Talk Table](TLK-File-Format) format
- [BIF File Format](BIF-File-Format) ← BioWare Infinity Format
- **[BWM File Format](BWM-File-Format)** ← Complete reference for Binary [walkmesh](BWM-File-Format) format
- **[GUI File Format](GUI-File-Format)** ← Complete reference for Graphical User Interface format
- [ERF File Format](ERF-File-Format) ← Encapsulated Resource [format](GFF-File-Format)
- **[Kit Structure Documentation](Kit-Structure-Documentation)** ← Complete reference for indoor kit [structure](GFF-File-Format#file-structure) and generation
- [GFF File Format](GFF-File-Format) ← Generic [file](GFF-File-Format) Format (see also [Official Bioware GFF Documentation](Bioware-Aurora-GFF))
  - [ARE (Area)](GFF-ARE)
  - [DLG (Dialogue)](GFF-DLG)
  - [GIT (Game Instance Template)](GFF-GIT)
  - [GUI (Graphical User Interface)](GFF-GUI)
  - [IFO (Module Info)](GFF-IFO)
  - [JRL (Journal)](GFF-JRL)
  - [PTH (Path)](GFF-PTH)
  - [UTC (Creature)](GFF-UTC)
  - [UTD (Door)](GFF-UTD)
  - [UTE (Encounter)](GFF-UTE)
  - [UTI (Item)](GFF-UTI)
  - [UTM (Merchant)](GFF-UTM)
  - [UTP (Placeable)](GFF-UTP)
  - [UTS (Sound)](GFF-UTS)
  - [UTT (Trigger)](GFF-UTT)
  - [UTW (Waypoint)](GFF-UTW)
- [KEY File Format](KEY-File-Format) ← [KEY](KEY-File-Format) file format
- [LIP File Format](LIP-File-Format) ← [LIP](LIP-File-Format) sync format
- [LTR File Format](LTR-File-Format) ← Letter format
- [LYT File Format](LYT-File-Format) ← Layout format
- [NCS File Format](NCS-File-Format) ← NwScript Compiled Script format
- [NSS File Format](NSS-File-Format) ← NwScript Source format (nwscript.nss, function/constant definitions)
- [RIM File Format](RIM-File-Format) ← Resource [index](2DA-File-Format#row-labels) Manifest format
- [SSF File Format](SSF-File-Format) ← [sound set files](SSF-File-Format) format
- [TLK File Format](TLK-File-Format) ← [Talk Table](TLK-File-Format) format
- [TPC File Format](TPC-File-Format) ← [texture](TPC-File-Format) Pack Container format
- [TXI File Format](TXI-File-Format) ← [texture](TPC-File-Format) Info format
- [VIS File Format](VIS-File-Format) ← Visibility format
- [WAV File Format](WAV-File-Format) ← Wave audio [format](GFF-File-Format)

### Internal Documentation

- [HoloPatcher](HoloPatcher)
- [Explanations on HoloPatcher Internal Logic](Explanations-on-HoloPatcher-Internal-Logic)

## Vendor Implementations

PyKotor includes many vendor submodules that provide alternative implementations of KotOR tools and engines. These serve as reference implementations and enable comparison of different approaches to the same problems.

### Engine Reimplementations

Complete game engine rewrites that can load and play KotOR:

- **[xoreos](https://github.com/xoreos/xoreos)** - C++ reimplementation of BioWare's Aurora engine, supports multiple Aurora games including KotOR. Focus on accuracy and cross-platform compatibility. ([Mirror: th3w1zard1/xoreos](https://github.com/th3w1zard1/xoreos))
- **[reone](https://github.com/seedhartha/reone)** - Modern C++ KotOR engine with OpenGL rendering. Focus on performance and clean architecture. ([Mirror: th3w1zard1/reone](https://github.com/th3w1zard1/reone))
- **[KotOR.js](https://github.com/KobaltBlu/KotOR.js)** - TypeScript/JavaScript engine running in browsers via WebGL. Enables playing KotOR directly in web browsers. ([Mirror: th3w1zard1/KotOR.js](https://github.com/th3w1zard1/KotOR.js))
- **[NorthernLights](https://github.com/lachjames/NorthernLights)** - .NET/C# engine implementation with Unity integration capabilities (based on KotOR-Unity project with further improvements) ([Mirror: th3w1zard1/NorthernLights](https://github.com/th3w1zard1/NorthernLights))
- **[KotOR-Unity](https://github.com/reubenduncan/KotOR-Unity)** - Unity-based KotOR engine rewrite. Leverages Unity's rendering and physics. ([Mirror: th3w1zard1/KotOR-Unity](https://github.com/th3w1zard1/KotOR-Unity))

### [file](GFF-File-Format) [format](GFF-File-Format) Libraries

Libraries focused on reading/writing KotOR [file](GFF-File-Format) [formats](GFF-File-Format):

- **[xoreos-tools](https://github.com/xoreos/xoreos-tools)** - Command-line tools for extracting and converting Aurora [file](GFF-File-Format) formats ([Mirror: th3w1zard1/xoreos-tools](https://github.com/th3w1zard1/xoreos-tools))
- **[Kotor.NET](https://github.com/NickHugi/Kotor.NET)** - .NET library for KotOR [file](GFF-File-Format) [formats](GFF-File-Format) with builder APIs

### 3D Modeling Tools

Tools for working with KotOR 3D [models](MDL-MDX-File-Format) and [textures](TPC-File-Format):

- **[kotorblender](https://github.com/ndixUR/kotorblender)** - Blender add-on for importing/exporting KotOR [MDL files](MDL-MDX-File-Format) with full [animation](MDL-MDX-File-Format#animation-header) support ([Mirror: th3w1zard1/kotorblender](https://github.com/th3w1zard1/kotorblender))
- **[mdlops](https://github.com/ndixUR/mdlops)** - Legacy Python [MDL](MDL-MDX-File-Format) toolkit for [model](MDL-MDX-File-Format) conversions ([Mirror: th3w1zard1/mdlops](https://github.com/th3w1zard1/mdlops))
- **[tga2tpc](https://github.com/ndixUR/tga2tpc)** - Standalone TGA to [TPC](TPC-File-Format) [texture](TPC-File-Format) converter ([Mirror: th3w1zard1/tga2tpc](https://github.com/th3w1zard1/tga2tpc))
- **[DLZ-Tool](https://github.com/LaneDibello/DLZ-Tool)** - DLZ [file](GFF-File-Format) decompression tool ([Mirror: th3w1zard1/DLZ-Tool](https://github.com/th3w1zard1/DLZ-Tool))
- **[WalkmeshVisualizer](https://github.com/glasnonck/WalkmeshVisualizer)** - [walkmesh](BWM-File-Format) viewing and debugging tool ([Mirror: th3w1zard1/WalkmeshVisualizer](https://github.com/th3w1zard1/WalkmeshVisualizer))

### Script Development

Tools for writing and editing NWScript:

- **[HoloLSP](https://github.com/th3w1zard1/HoloLSP)** - Language Server Protocol implementation for NWScript
(enables IDE integration)
- **[nwscript-mode.el](https://github.com/implicit-image/nwscript-mode.el)** - Emacs major mode for NWScript editing ([Mirror: th3w1zard1/nwscript-mode.el](https://github.com/th3w1zard1/nwscript-mode.el))
- **[Vanilla_KOTOR_Script_Source](https://github.com/KOTORCommunityPatches/Vanilla_KOTOR_Script_Source)** - Decompiled vanilla KotOR scripts for reference ([Mirror: th3w1zard1/Vanilla_KOTOR_Script_Source](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source))

### Modding Tools

Tools for creating and installing mods:

- **KotorCLI (PyKotor)** - CLI-first toolset for packing, conversion, Holocron kit generation, and [GUI](GFF-File-Format#gui-graphical-user-interface) layout scaling. `python -m kotorcli kit-generate --installation <path> --module <module> --output <dir>` runs headless; launching with no arguments opens the Tkinter kit generator [GUI](GFF-File-Format#gui-graphical-user-interface) for interactive use. `python -m kotorcli gui-convert --input <gui_or_folder> --output <dir> --resolution ALL` runs headless for [GUI](GFF-File-Format#gui-graphical-user-interface) resizing; omitting args opens the converter [GUI](GFF-File-Format#gui-graphical-user-interface). (Implementations: `Tools/KotorCLI/src/kotorcli/kit_generator.py` wraps `Libraries/PyKotor/src/pykotor/tools/kit.py`; `Tools/KotorCLI/src/kotorcli/gui_converter.py` delegates to `pykotor.resource.formats.gff`.)
- **[TSLPatcher](https://github.com/Fair-Strides/TSLPatcher)** - Original Perl mod installer (reference implementation) ([Mirror: th3w1zard1/TSLPatcher](https://github.com/th3w1zard1/TSLPatcher))
- **[HoloPatcher.NET](https://github.com/th3w1zard1/HoloPatcher.NET)** - .NET reimplementation of TSLPatcher
- **[Kotor-Patch-Manager](https://github.com/LaneDibello/Kotor-Patch-Manager)** - Alternative mod manager ([Mirror: th3w1zard1/Kotor-Patch-Manager](https://github.com/th3w1zard1/Kotor-Patch-Manager))
- **[KotORModSync](https://github.com/th3w1zard1/KotORModSync)** - Mod synchronization and installation
- **[StarForge](https://github.com/th3w1zard1/StarForge)** - Module editor and modding toolkit
- **[KotorModTools](https://github.com/Box65535/KotorModTools)** - Collection of modding utilities ([Mirror: th3w1zard1/KotorModTools](https://github.com/th3w1zard1/KotorModTools))

### Save Editors

Tools for editing KotOR save games:

- **[sotor](https://github.com/StarfishXeno/sotor)** - Terminal-based save editor ([Mirror: th3w1zard1/sotor](https://github.com/th3w1zard1/sotor))
- **[KSELinux](https://github.com/Bolche/KSELinux)** - KotOR Save Editor for Linux ([Mirror: th3w1zard1/KSELinux](https://github.com/th3w1zard1/KSELinux))
- **[KotOR-Save-Editor](https://github.com/Fair-Strides/KotOR-Save-Editor)** - [GUI](GFF-File-Format#gui-graphical-user-interface) save editor ([Mirror: th3w1zard1/KotOR-Save-Editor](https://github.com/th3w1zard1/KotOR-Save-Editor))
- **[kotor-savegame-editor](https://github.com/th3w1zard1/kotor-savegame-editor)** - Web-based save editor

### Audio Tools

Tools for working with KotOR audio:

- **[SithCodec](https://github.com/BBBrassil/SithCodec)** - KotOR audio codec implementation ([Mirror: th3w1zard1/SithCodec](https://github.com/th3w1zard1/SithCodec))
- **[SWKotOR-Audio-Encoder](https://github.com/LoranRendel/SWKotOR-Audio-Encoder)** - Audio encoding tool for KotOR ([Mirror: th3w1zard1/SWKotOR-Audio-Encoder](https://github.com/th3w1zard1/SWKotOR-Audio-Encoder))

### Community Resources

Guides, patches, and community-maintained resources:

- **[K1_Community_Patch](https://github.com/KOTORCommunityPatches/K1_Community_Patch)** - Community bug fix patch for KotOR 1 ([Mirror: th3w1zard1/K1_Community_Patch](https://github.com/th3w1zard1/K1_Community_Patch))
- **[TSL_Community_Patch](https://github.com/KOTORCommunityPatches/TSL_Community_Patch)** - Community bug fix patch for KotOR 2 ([Mirror: th3w1zard1/TSL_Community_Patch](https://github.com/th3w1zard1/TSL_Community_Patch))
- **[KOTOR-utils](https://github.com/JCarter426/KOTOR-utils)** - JCarter426's utility scripts and tools ([Mirror: th3w1zard1/KOTOR-utils](https://github.com/th3w1zard1/KOTOR-utils))
- **[KotOR-Bioware-Libs](https://github.com/Fair-Strides/KotOR-Bioware-Libs)** - BioWare library references ([Mirror: th3w1zard1/KotOR-Bioware-Libs](https://github.com/th3w1zard1/KotOR-Bioware-Libs))
- **[kotor_combat_faq](https://github.com/statsjedi/kotor_combat_faq)** - Combat mechanics documentation ([Mirror: th3w1zard1/kotor_combat_faq](https://github.com/th3w1zard1/kotor_combat_faq))
- **[ds-kotor-modding-wiki](https://github.com/DeadlyStream/ds-kotor-modding-wiki)** - DeadlyStream modding wiki archive ([Mirror: th3w1zard1/ds-kotor-modding-wiki](https://github.com/th3w1zard1/ds-kotor-modding-wiki))

### External Documentation

Reference documentation from related projects (external sources):

- **[xoreos-docs](https://github.com/xoreos/xoreos-docs)** - Aurora engine [format](GFF-File-Format) documentation (xoreos project)
- **[nwn-docs](https://github.com/kucik/nwn-docs)** - Neverwinter Nights documentation (shares Aurora [formats](GFF-File-Format))
