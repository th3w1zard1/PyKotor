from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, NamedTuple

# Import for runtime usage
from pykotor.extract.file import ResourceIdentifier  # pyright: ignore[reportMissingImports]
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.twoda.twoda_data import TwoDARow
    from pykotor.tools.path import CaseAwarePath


class LookupResult2DA(NamedTuple):
    filepath: CaseAwarePath
    row_index: int
    column_name: str
    contents: str
    entire_row: TwoDARow


@dataclass(frozen=True, init=False, repr=False)
class K1ResRef2DAColumns:
    ...


class ABSColumns2DA:

    @classmethod
    def as_dict(cls) -> dict[str, set[str]]:
        # HACK(th3w1zard1): Include only attributes that are defined in the current class and are not methods or private
        parent_attrs: set[str] = set(dir(cls.__base__))
        current_attrs: set[str] = set(dir(cls)) - parent_attrs
        this_dict: dict[str, set[str]] = {}
        for k in current_attrs:
            v = cls.__dict__[k]
            if k.startswith("__") or callable(v):
                continue
            if isinstance(v, ABSColumns2DA):
                this_dict.update(v.as_dict())
            else:
                this_dict[f"{k}.2da"] = v
        return this_dict

    @classmethod
    def all_files(cls) -> set[str]:
        # HACK(th3w1zard): Include only attributes that are defined in the current class and are not methods or private
        parent_attrs: set[str] = set(dir(cls.__base__))
        current_attrs: set[str] = set(dir(cls)) - parent_attrs
        filenames: set[str] = set()
        for k in current_attrs:
            v = cls.__dict__[k]
            if k.startswith("__") or callable(v):
                continue
            if isinstance(v, ABSColumns2DA):
                filenames.update(v.all_files())
            else:
                filenames.add(f"{k}.2da")
        return filenames


class K1Columns2DA:
    @dataclass(frozen=True, init=False, repr=False)
    class StrRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a stringref in the TalkTable used by the first game."""
        actions: ClassVar[set[str]] = {"string_ref"}
        aiscripts: ClassVar[set[str]] = {"name_strref", "description_strref"}  # k1 only
        ambientsound: ClassVar[set[str]] = {"description"}
        appearance: ClassVar[set[str]] = {"string_ref"}
        bindablekeys: ClassVar[set[str]] = {"keynamestrref"}
        classes: ClassVar[set[str]] = {"name", "description"}
        crtemplates: ClassVar[set[str]] = {"strref"}
        creaturesize: ClassVar[set[str]] = {"strref"}
        doortypes: ClassVar[set[str]] = {"stringrefgame"}
        effecticons: ClassVar[set[str]] = {"strref"}
        encdifficulty: ClassVar[set[str]] = {"strref"}
        environment: ClassVar[set[str]] = {"strref"}
        feat: ClassVar[set[str]] = {"name", "description"}
        feedbacktext: ClassVar[set[str]] = {"strref"}
        fractionalcr: ClassVar[set[str]] = {"displaystrref"}
        gamespyrooms: ClassVar[set[str]] = {"str_ref"}
        genericdoors: ClassVar[set[str]] = {"strref"}
        hen_companion: ClassVar[set[str]] = {"strref"}
        iprp_abilities: ClassVar[set[str]] = {"name"}
        iprp_acmodtype: ClassVar[set[str]] = {"name"}
        iprp_aligngrp: ClassVar[set[str]] = {"name"}
        iprp_alignment: ClassVar[set[str]] = {"name"}
        iprp_ammocost: ClassVar[set[str]] = {"name"}
        iprp_ammotype: ClassVar[set[str]] = {"name"}
        iprp_amount: ClassVar[set[str]] = {"name"}  # ...
        iprp_bonuscost: ClassVar[set[str]] = {"name"}
        iprp_chargecost: ClassVar[set[str]] = {"name"}
        iprp_color: ClassVar[set[str]] = {"name"}
        iprp_combatdam: ClassVar[set[str]] = {"name"}
        iprp_damagecost: ClassVar[set[str]] = {"name"}
        iprp_damagetype: ClassVar[set[str]] = {"name"}
        iprp_damvulcost: ClassVar[set[str]] = {"name"}
        iprp_feats: ClassVar[set[str]] = {"name"}
        iprp_immuncost: ClassVar[set[str]] = {"name"}
        iprp_immunity: ClassVar[set[str]] = {"name"}
        iprp_lightcost: ClassVar[set[str]] = {"name"}
        iprp_meleecost: ClassVar[set[str]] = {"name"}
        iprp_monstcost: ClassVar[set[str]] = {"name"}
        iprp_monsterhit: ClassVar[set[str]] = {"name"}
        iprp_neg10cost: ClassVar[set[str]] = {"name"}
        iprp_neg5cost: ClassVar[set[str]] = {"name"}
        iprp_onhit: ClassVar[set[str]] = {"name"}
        iprp_onhitcost: ClassVar[set[str]] = {"name"}
        iprp_onhitdc: ClassVar[set[str]] = {"name"}
        iprp_onhitdur: ClassVar[set[str]] = {"name"}
        iprp_paramtable: ClassVar[set[str]] = {"name"}
        iprp_poison: ClassVar[set[str]] = {"name"}
        iprp_protection: ClassVar[set[str]] = {"name"}
        iprp_redcost: ClassVar[set[str]] = {"name"}
        iprp_resistcost: ClassVar[set[str]] = {"name"}
        iprp_saveelement: ClassVar[set[str]] = {"name"}
        iprp_savingthrow: ClassVar[set[str]] = {"name"}
        iprp_soakcost: ClassVar[set[str]] = {"name"}
        iprp_spellcost: ClassVar[set[str]] = {"name"}
        iprp_spellvcost: ClassVar[set[str]] = {"name"}
        iprp_spellvlimm: ClassVar[set[str]] = {"name"}
        iprp_spells: ClassVar[set[str]] = {"name"}
        iprp_spellshl: ClassVar[set[str]] = {"name"}
        iprp_srcost: ClassVar[set[str]] = {"name"}
        iprp_trapcost: ClassVar[set[str]] = {"name"}
        iprp_traps: ClassVar[set[str]] = {"name"}
        iprp_walk: ClassVar[set[str]] = {"name"}
        iprp_weightcost: ClassVar[set[str]] = {"name"}
        iprp_weightinc: ClassVar[set[str]] = {"name"}
        itempropdef: ClassVar[set[str]] = {"name"}
        itemprops: ClassVar[set[str]] = {"stringref"}
        keymap: ClassVar[set[str]] = {"actionstrref"}
        loadscreenhints: ClassVar[set[str]] = {"gameplayhint", "storyhint"}
        masterfeats: ClassVar[set[str]] = {"strref"}
        modulesave: ClassVar[set[str]] = {"areaname"}
        movies: ClassVar[set[str]] = {"strrefname", "strrefdesc"}
        placeables: ClassVar[set[str]] = {"strref"}
        planetary: ClassVar[set[str]] = {"name", "description"}
        soundset: ClassVar[set[str]] = {"strref"}
        stringtokens: ClassVar[set[str]] = {"strref1", "strref2", "strref3", "strref4"}
        texpacks: ClassVar[set[str]] = {"strrefname"}
        tutorial: ClassVar[set[str]] = {"message0", "message1", "message2"}
        tutorial_old: ClassVar[set[str]] = {"message0", "message1", "message2"}
        skills: ClassVar[set[str]] = {"name", "description"}
        spells: ClassVar[set[str]] = {"name", "spelldesc"}
        traps: ClassVar[set[str]] = {"trapname", "name"}

    @dataclass(frozen=True, init=False, repr=False)
    class ResRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a filestem used by the first game."""
        appearance: ClassVar[set[str]] = {"race"}
        droiddischarge: ClassVar[set[str]] = {">>##HEADER##<<"}
        hen_companion: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        hen_familiar: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        iprp_paramtable: ClassVar[set[str]] = {"tableresref"}
        itempropdef: ClassVar[set[str]] = {"subtyperesref", "param1resref", "gamestrref", "description"}
        minglobalrim: ClassVar[set[str]] = {"moduleresref"}
        modulesave: ClassVar[set[str]] = {"modulename"}

        @dataclass(frozen=True, init=False, repr=False)
        class Models(ABSColumns2DA):
            """All 2DA columns that reference model resrefs in the first game."""
            ammunitiontypes: ClassVar[set[str]] = {"model", "model0", "model1", "muzzleflash"}
            appearance: ClassVar[set[str]] = {"modela", "modelb", "modelc", "modeld", "modele", "modelf", "modelg", "modelh", "modeli", "modelj"}
            baseitems: ClassVar[set[str]] = {"defaultmodel"}
            placeables: ClassVar[set[str]] = {"modelname"}
            planetary: ClassVar[set[str]] = {"model"}
            upcrystals: ClassVar[set[str]] = {"shortmdlvar", "longmdlvar", "doublemdlvar"}

            @dataclass(frozen=True, init=False, repr=False)
            class Doors(ABSColumns2DA):
                """All 2DA columns that reference door model resrefs."""
                doortypes: ClassVar[set[str]] = {"model"}
                genericdoors: ClassVar[set[str]] = {"modelname"}

        @dataclass(frozen=True, init=False, repr=False)
        class Sounds(ABSColumns2DA):
            """All 2DA columns that reference sound resrefs."""
            aliensound: ClassVar[set[str]] = {"filename"}
            ambientsound: ClassVar[set[str]] = {"resource"}
            ammunitiontypes: ClassVar[set[str]] = {"shotsound0", "shotsound1", "impactsound0", "impactsound1"}
            appearancesndset: ClassVar[set[str]] = {"falldirt", "fallhard", "fallmetal", "fallwater"}
            baseitems: ClassVar[set[str]] = {"powerupsnd", "powerdownsnd", "poweredsnd"}
            footstepsounds: ClassVar[set[str]] = {"rolling",
                                                  "dirt0", "dirt1", "dirt2",
                                                  "grass0", "grass1", "grass2",
                                                  "stone0", "stone1", "stone2",
                                                  "wood0", "wood1", "wood2"
                                                  "water0", "water1", "water2"
                                                  "carpet0", "carpet1", "carpet2",
                                                  "metal0", "metal1", "metal2",
                                                  "puddles0", "puddles1", "puddles2",
                                                  "leaves0", "leaves1", "leaves2",
                                                  "force1", "force2", "force3"}  # TODO: Why are these the only ones different?
            grenadesnd: ClassVar[set[str]] = {"sound"}
            guisounds: ClassVar[set[str]] = {"soundresref"}
            inventorysnds: ClassVar[set[str]] = {"inventorysound"}

        @dataclass(frozen=True, init=False, repr=False)
        class Music(ABSColumns2DA):
            """All 2DA columns that reference music resrefs."""
            ambientmusic: ClassVar[set[str]] = {"resource", "stinger1", "stinger2", "stinger3"}
            loadscreens: ClassVar[set[str]] = {"musicresref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Textures(ABSColumns2DA):
            """All 2DA columns that reference texture resrefs."""
            actions: ClassVar[set[str]] = {"iconresref"}
            appearance: ClassVar[set[str]] = {"racetex", "texa", "texb", "texc", "texd", "texe", "texf", "texg", "texh", "texi", "texj",
                                              "headtexve", "headtexe", "headtexvg", "headtexg"}
            baseitems: ClassVar[set[str]] = {"defaulticon"}
            effecticon: ClassVar[set[str]] = {"iconresref"}
            heads: ClassVar[set[str]] = {"head", "headtexvvve", "headtexvve", "headtexve", "headtexe", "headtexg", "headtexvg"}
            iprp_spells: ClassVar[set[str]] = {"icon"}
            loadscreens: ClassVar[set[str]] = {"bmpresref"}
            planetary: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class Items(ABSColumns2DA):
            """All 2DA columns that reference item resrefs."""
            baseitems: ClassVar[set[str]] = {"itemclass", "baseitemstatref"}
            chargenclothes: ClassVar[set[str]] = {"itemresref"}
            feat: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class GUIs(ABSColumns2DA):
            """All 2DA columns that reference GUI resrefs."""
            cursors: ClassVar[set[str]] = {"resref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Scripts(ABSColumns2DA):
            """All 2DA columns that reference script resrefs."""
            areaeffects: ClassVar[set[str]] = {"onenter", "heartbeat", "onexit"}
            disease: ClassVar[set[str]] = {"end_incu_script", "24_hour_script"}
            spells: ClassVar[set[str]] = {"impactscript"}


class K2Columns2DA:
    @dataclass(frozen=True, init=False, repr=False)
    class StrRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a stringref in the TalkTable used by the second game."""
        aiscripts: ClassVar[set[str]] = {"name_strref"}
        ambientsound: ClassVar[set[str]] = {"description"}
        appearance: ClassVar[set[str]] = {"string_ref"}
        bindablekeys: ClassVar[set[str]] = {"keynamestrref"}
        classes: ClassVar[set[str]] = {"name", "description"}
        credits: ClassVar[set[str]] = {"name"}
        crtemplates: ClassVar[set[str]] = {"strref"}
        creaturesize: ClassVar[set[str]] = {"strref"}
        difficultyop: ClassVar[set[str]] = {"name"}
        disease: ClassVar[set[str]] = {"name"}
        doortypes: ClassVar[set[str]] = {"stringrefgame"}
        effecticons: ClassVar[set[str]] = {"strref"}
        encdifficulty: ClassVar[set[str]] = {"strref"}
        environment: ClassVar[set[str]] = {"strref"}
        feat: ClassVar[set[str]] = {"name", "description"}
        feedbacktext: ClassVar[set[str]] = {"strref"}
        fractionalcr: ClassVar[set[str]] = {"displaystrref"}
        gamespyrooms: ClassVar[set[str]] = {"str_ref"}
        genericdoors: ClassVar[set[str]] = {"strref"}
        hen_companion: ClassVar[set[str]] = {"strref"}
        iprp_abilities: ClassVar[set[str]] = {"name"}
        iprp_acmodtype: ClassVar[set[str]] = {"name"}
        iprp_aligngrp: ClassVar[set[str]] = {"name"}
        iprp_alignment: ClassVar[set[str]] = {"name"}
        iprp_ammocost: ClassVar[set[str]] = {"name"}
        iprp_ammotype: ClassVar[set[str]] = {"name"}
        iprp_amount: ClassVar[set[str]] = {"name"}  # ...
        iprp_bonuscost: ClassVar[set[str]] = {"name"}
        iprp_chargecost: ClassVar[set[str]] = {"name"}
        iprp_color: ClassVar[set[str]] = {"name"}
        iprp_combatdam: ClassVar[set[str]] = {"name"}
        iprp_damagecost: ClassVar[set[str]] = {"name"}
        iprp_damagetype: ClassVar[set[str]] = {"name"}
        iprp_damvulcost: ClassVar[set[str]] = {"name"}
        iprp_feats: ClassVar[set[str]] = {"name"}
        iprp_immuncost: ClassVar[set[str]] = {"name"}
        iprp_immunity: ClassVar[set[str]] = {"name"}
        iprp_lightcost: ClassVar[set[str]] = {"name"}
        iprp_meleecost: ClassVar[set[str]] = {"name"}
        iprp_monstcost: ClassVar[set[str]] = {"name"}
        iprp_monsterhit: ClassVar[set[str]] = {"name"}
        iprp_neg10cost: ClassVar[set[str]] = {"name"}
        iprp_neg5cost: ClassVar[set[str]] = {"name"}
        iprp_onhit: ClassVar[set[str]] = {"name"}
        iprp_onhitcost: ClassVar[set[str]] = {"name"}
        iprp_onhitdc: ClassVar[set[str]] = {"name"}
        iprp_onhitdur: ClassVar[set[str]] = {"name"}
        iprp_paramtable: ClassVar[set[str]] = {"name"}
        iprp_poison: ClassVar[set[str]] = {"name"}
        iprp_protection: ClassVar[set[str]] = {"name"}
        iprp_redcost: ClassVar[set[str]] = {"name"}
        iprp_resistcost: ClassVar[set[str]] = {"name"}
        iprp_saveelement: ClassVar[set[str]] = {"name"}
        iprp_savingthrow: ClassVar[set[str]] = {"name"}
        iprp_soakcost: ClassVar[set[str]] = {"name"}
        iprp_spellcost: ClassVar[set[str]] = {"name"}
        iprp_spellvcost: ClassVar[set[str]] = {"name"}
        iprp_spellvlimm: ClassVar[set[str]] = {"name"}
        iprp_spells: ClassVar[set[str]] = {"name"}
        iprp_spellshl: ClassVar[set[str]] = {"name"}
        iprp_srcost: ClassVar[set[str]] = {"name"}
        iprp_trapcost: ClassVar[set[str]] = {"name"}
        iprp_traps: ClassVar[set[str]] = {"name"}
        iprp_walk: ClassVar[set[str]] = {"name"}
        iprp_weightcost: ClassVar[set[str]] = {"name"}
        iprp_weightinc: ClassVar[set[str]] = {"name"}
        itempropdef: ClassVar[set[str]] = {"name"}
        itemprops: ClassVar[set[str]] = {"stringref"}
        keymap: ClassVar[set[str]] = {"actionstrref"}
        loadscreenhints: ClassVar[set[str]] = {"gameplayhint", "storyhint"}
        masterfeats: ClassVar[set[str]] = {"strref"}
        modulesave: ClassVar[set[str]] = {"areaname"}
        movies: ClassVar[set[str]] = {"strrefname", "strrefdesc"}
        placeables: ClassVar[set[str]] = {"strref"}
        planetary: ClassVar[set[str]] = {"name", "description"}
        soundset: ClassVar[set[str]] = {"strref"}
        stringtokens: ClassVar[set[str]] = {"strref1", "strref2", "strref3", "strref4"}
        texpacks: ClassVar[set[str]] = {"strrefname"}
        tutorial: ClassVar[set[str]] = {"message0", "message1", "message2"}
        tutorial_old: ClassVar[set[str]] = {"message0", "message1", "message2"}
        skills: ClassVar[set[str]] = {"name", "description"}
        spells: ClassVar[set[str]] = {"name", "spelldesc"}
        traps: ClassVar[set[str]] = {"trapname", "name"}

    @dataclass(frozen=True, init=False, repr=False)
    class ResRefs(ABSColumns2DA):
        """All 2DA's that contain columns referencing a filestem."""
        ammunitiontypes: ClassVar[set[str]] = {"muzzleflash"}
        appearance: ClassVar[set[str]] = {"race"}
        droiddischarge: ClassVar[set[str]] = {">>##HEADER##<<"}
        hen_companion: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        hen_familiar: ClassVar[set[str]] = {"baseresref"}  # Not used in the game engine.
        iprp_paramtable: ClassVar[set[str]] = {"tableresref"}
        itempropdef: ClassVar[set[str]] = {"subtyperesref", "param1resref", "gamestrref", "description"}
        minglobalrim: ClassVar[set[str]] = {"moduleresref"}
        modulesave: ClassVar[set[str]] = {"modulename"}

        @dataclass(frozen=True, init=False, repr=False)
        class Models(ABSColumns2DA):
            """All 2DA columns that reference model resrefs."""
            ammunitiontypes: ClassVar[set[str]] = {"model", "model0", "model1"}
            appearance: ClassVar[set[str]] = {"modela", "modelb", "modelc", "modeld", "modele", "modelf", "modelg", "modelh", "modeli", "modelj"}
            baseitems: ClassVar[set[str]] = {"defaultmodel"}
            placeables: ClassVar[set[str]] = {"modelname"}
            planetary: ClassVar[set[str]] = {"model"}
            upcrystals: ClassVar[set[str]] = {"shortmdlvar", "longmdlvar", "doublemdlvar"}

            @dataclass(frozen=True, init=False, repr=False)
            class Doors(ABSColumns2DA):
                """All 2DA columns that reference door model resrefs."""
                doortypes: ClassVar[set[str]] = {"model"}
                genericdoors: ClassVar[set[str]] = {"modelname"}

        @dataclass(frozen=True, init=False, repr=False)
        class Sounds(ABSColumns2DA):
            """All 2DA columns that reference sound resrefs."""
            aliensound: ClassVar[set[str]] = {"filename"}
            alienvo: ClassVar[set[str]] = {"angry_long", "angry_medium", "angry_short",
                                           "comment_generic_long", "comment_generic_medium", "comment_generic_short",
                                           "greeting_medium", "greeting_short",
                                           "happy_thankful_long", "happy_thankful_medium", "happy_thankful_short",
                                           "laughter_normal", "laughter_mocking_medium", "laughter_mocking_short", "laughter_long", "laughter_short"
                                           "pleading_medium", "pleading_short",
                                           "question_long", "question_medium", "question_short",
                                           "sad_long", "sad_medium", "sad_short",
                                           "scared_long", "scared_medium", "scared_short",
                                           "seductive_long", "seductive_medium", "seductive_short",
                                           "silence",
                                           "wounded_medium", "wounded_small",
                                           "screaming_medium", "screaming_small"}
            ambientsound: ClassVar[set[str]] = {"resource"}
            ammunitiontypes: ClassVar[set[str]] = {"shotsound0", "shotsound1", "impactsound0", "impactsound1"}
            appearancesndset: ClassVar[set[str]] = {"falldirt", "fallhard", "fallmetal", "fallwater"}
            baseitems: ClassVar[set[str]] = {"powerupsnd", "powerdownsnd", "poweredsnd"}
            footstepsounds: ClassVar[set[str]] = {"rolling",
                                                  "dirt0", "dirt1", "dirt2",
                                                  "grass0", "grass1", "grass2",
                                                  "stone0", "stone1", "stone2",
                                                  "wood0", "wood1", "wood2"
                                                  "water0", "water1", "water2"
                                                  "carpet0", "carpet1", "carpet2",
                                                  "metal0", "metal1", "metal2",
                                                  "puddles0", "puddles1", "puddles2",
                                                  "leaves0", "leaves1", "leaves2",
                                                  "force1", "force2", "force3"}  # TODO: Why are these the only ones different?
            grenadesnd: ClassVar[set[str]] = {"sound"}
            guisounds: ClassVar[set[str]] = {"soundresref"}
            inventorysnds: ClassVar[set[str]] = {"inventorysound"}

            @dataclass(frozen=True, init=False, repr=False)
            class Music(ABSColumns2DA):
                """All 2DA columns that reference music resref sounds."""
                ambientmusic: ClassVar[set[str]] = {"resource", "stinger1", "stinger2", "stinger3"}
                loadscreens: ClassVar[set[str]] = {"musicresref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Textures(ABSColumns2DA):
            """All 2DA columns that reference texture resrefs."""
            actions: ClassVar[set[str]] = {"iconresref"}
            appearance: ClassVar[set[str]] = {"racetex", "texa", "texb", "texc", "texd", "texe", "texf", "texg", "texh", "texi", "texj",
                                              "headtexve", "headtexe", "headtexvg", "headtexg"}
            cursors: ClassVar[set[str]] = {"resref"}
            baseitems: ClassVar[set[str]] = {"defaulticon"}
            effecticon: ClassVar[set[str]] = {"iconresref"}
            heads: ClassVar[set[str]] = {"head", "headtexvvve", "headtexvve", "headtexve", "headtexe", "headtexg", "headtexvg"}
            iprp_spells: ClassVar[set[str]] = {"icon"}
            loadscreens: ClassVar[set[str]] = {"bmpresref"}
            planetary: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class Items(ABSColumns2DA):
            """All 2DA columns that reference item resrefs."""
            baseitems: ClassVar[set[str]] = {"itemclass", "baseitemstatref"}
            chargenclothes: ClassVar[set[str]] = {"itemresref"}
            feat: ClassVar[set[str]] = {"icon"}

        @dataclass(frozen=True, init=False, repr=False)
        class GUIs(ABSColumns2DA):
            """All 2DA columns that reference GUI resrefs."""
            cursors: ClassVar[set[str]] = {"resref"}

        @dataclass(frozen=True, init=False, repr=False)
        class Scripts(ABSColumns2DA):
            """All 2DA columns that reference script resrefs."""
            areaeffects: ClassVar[set[str]] = {"onenter", "heartbeat", "onexit"}
            disease: ClassVar[set[str]] = {"end_incu_script", "24_hour_script"}
            spells: ClassVar[set[str]] = {"impactscript"}



class TwoDARegistry:
    """Central registry for 2DA metadata, GFF mappings, and helpers.
    
    This registry provides metadata about 2DA files, including which columns contain
    string references (StrRefs) or resource references (ResRefs). It also maps GFF fields
    to their corresponding 2DA lookup tables.
    
    Game Engine Usage:
    ----------------
    The following 2DA files are confirmed to be loaded and used by the game engine,
    as verified through reverse engineering analysis of swkotor.exe and swkotor2.exe
    using Ghidra (via Reva MCP server):
    
    **swkotor.exe (KotOR 1) - Loaded via Load2DArrays() and related functions:**
    - ambientmusic.2da: Load2DArrays_AmbientMusic() - CResRef("AmbientMusic")
    - ambientsound.2da: Load2DArrays_AmbientSound() - CResRef("AmbientSound")
    - ammunitiontypes.2da: Load2DArrays_AmmunitionTypes() - CResRef("AmmunitionTypes")
    - appearance.2da: Load2DArrays_Appearance() - CResRef("Appearance")
    - appearancesndset.2da: Load2DArrays_AppearanceSounds() - CResRef("AppearanceSounds")
    - baseitems.2da: CSWBaseItemArray::Load() - CResRef("BASEITEMS")
    - bindablekeys.2da: Load2DArrays_BindableKey() - CResRef("BindableKey")
    - camerastyle.2da: Load2DArrays_CameraStyle() - CResRef("CameraStyle")
    - classes.2da: LoadClassInfo() - CResRef("Classes")
    - creaturespeed.2da: Load2DArrays_CreatureSpeed() - CResRef("CreatureSpeed")
    - cursors.2da: Load2DArrays_Cursor() - CResRef("cursors")
    - dialoganimations.2da: Load2DArrays_DialogAnimations() - CResRef("DialogAnimations")
    - difficultyopt.2da: Load2DArrays_DifficultyOptions() - CResRef("DifficultyOptions")
    - disease.2da: Load2DArrays_Disease() - CResRef("Disease")
    - doortypes.2da: Load2DArrays_DoorTypes() - CResRef("DoorTypes")
    - encdifficulty.2da: Load2DArrays_EncDifficulty() - CResRef("EncDifficulty")
    - exptable.2da: CSWRules::CSWRules() - CResRef("EXPTABLE")
    - feat.2da: LoadFeatInfo() - CResRef("Feat")
    - featgain.2da: CSWClass::LoadFeatGain() - CResRef("featgain")
    - footstepsounds.2da: Load2DArrays_FootstepSounds() - CResRef("FootstepSounds")
    - fractionalcr.2da: Load2DArrays_FractionalCR() - CResRef("FractionalCR")
    - gamma.2da: Load2DArrays_Gamma() - CResRef("Gamma")
    - gender.2da: Load2DArrays_Gender() - CResRef("GENDER")
    - genericdoors.2da: Load2DArrays_GenericDoors() - CResRef("GenericDoors")
    - globalcat.2da: CSWGlobalVariableTable::ReadCatalogue() - CResRef("globalcat")
    - heads.2da: Load2DArrays_Heads() - CResRef("Heads")
    - iprp_abilities.2da: Load2DArrays_IPRPAbilities() - CResRef("IPRP_ABILITIES")
    - iprp_acmodtype.2da: LoadIPRPCostTables() - CResRef("IPRP_ACMODTYPE")
    - iprp_aligngrp.2da: LoadIPRPCostTables() - CResRef("IPRP_ALIGNGRP")
    - iprp_ammotype.2da: LoadIPRPCostTables() - CResRef("IPRP_AMMOTYPE")
    - iprp_combatdam.2da: LoadIPRPCostTables() - CResRef("IPRP_COMBATDAM")
    - iprp_costtable.2da: LoadIPRPCostTables() - CResRef("IPRP_COSTTABLE")
    - iprp_damagecost.2da: Load2DArrays_IPRPDamage() - CResRef("IPRP_DAMAGECOST")
    - iprp_damagetype.2da: LoadIPRPCostTables() - CResRef("IPRP_DAMAGETYPE")
    - iprp_immunity.2da: LoadIPRPCostTables() - CResRef("IPRP_IMMUNITY")
    - iprp_lightcol.2da: Load2DArrays_LightColor() - CResRef("LightColor")
    - iprp_meleecost.2da: Load2DArrays_IPRPMelee() - CResRef("IPRP_MeleeCost")
    - iprp_onhit.2da: Load2DArrays_OnHit() - CResRef("IPRP_ONHIT")
    - iprp_paramtable.2da: LoadIPRPParamTables() - CResRef("IPRP_PARAMTABLE")
    - iprp_protection.2da: LoadIPRPCostTables() - CResRef("IPRP_PROTECTION")
    - iprp_saveelement.2da: LoadIPRPCostTables() - CResRef("IPRP_SAVEELEMENT")
    - iprp_savingthrow.2da: LoadIPRPCostTables() - CResRef("IPRP_SAVINGTHROW")
    - iprp_walk.2da: LoadIPRPCostTables() - CResRef("IPRP_WALK")
    - itempropdef.2da: Load2DArrays_ItemPropDef() - CResRef("ItemPropDef")
    - itemprops.2da: HandleServerToPlayerDebugInfo_Item() - CResRef("ITEMPROPS")
    - keymap.2da: Load2DArrays_Keymap() - CResRef("Keymap")
    - loadscreenhints.2da: CClientExoAppInternal::GetNextLoadScreenHintSTRREF() - CResRef("loadscreenhints")
    - loadscreens.2da: Load2DArrays_AreaTransition() - CResRef("Loadscreens")
    - modulesave.2da: StartNewModule() - CResRef("modulesave")
    - movies.2da: Load2DArrays_Movies() - CResRef("Movies")
    - placeables.2da: Load2DArrays_Placeables() - CResRef("Placeables")
    - placeablesounds.2da: Load2DArrays_PlaceableSounds() - CResRef("PlaceableSounds")
    - planetary.2da: Load2DArrays_Planetary() - CResRef("Planetary")
    - plot.2da: Load2DArrays_PlotXP() - CResRef("Plot")
    - poison.2da: Load2DArrays_Poison() - CResRef("Poison")
    - portraits.2da: Load2DArrays_Portrait() - CResRef("Portraits")
    - racialtypes.2da: LoadRaceInfo() - CResRef("RacialTypes")
    - ranges.2da: CSWRules::CSWRules() - CResRef("Ranges")
    - regeneration.2da: Load2DArrays_Regeneration() - CResRef("Regeneration")
    - repadjustments.2da: Load2DArrays_RepAdjustments() - CResRef("RepAdjustments")
    - repute.2da: Load2DArrays_Repute() - CResRef("Repute")
    - skills.2da: LoadSkillInfo() - CResRef("Skills")
    - spells.2da: Load2DArrays_Spells() - CResRef("Spells")
    - statescripts.2da: Load2DArrays_StateScripts() - CResRef("StateScripts")
    - surfacemat.2da: Load2DArrays_SurfaceMaterial() - CResRef("SurfaceMaterial")
    - traps.2da: Load2DArrays_Traps() - CResRef("Traps")
    - tutorial.2da: Load2DArrays_Tutorial() - CResRef("Tutorial")
    - upgrade.2da: CSWGuiUpgrade() - CResRef("upgrade")
    - videoeffects.2da: Load2DArrays_VideoEffects() - CResRef("VideoEffects")
    - visualeffects.2da: Load2DArrays_VisualEffect() - CResRef("VisualEffect")
    - weaponsounds.2da: Load2DArrays_WeaponSounds() - CResRef("WeaponSounds")
    - xptable.2da: Load2DArrays_XpBase() - CResRef("XPTable")
    
    **swkotor2.exe (KotOR 2/TSL) - Additional files loaded:**
    - emotion.2da: FUN_00612fb0() - CResRef("Emotion")
    - facialanim.2da: FUN_005e6ac0() - CResRef("FacialAnim")
    - iprp_bonuscost.2da: FUN_006111c0() - CResRef("IPRP_BONUSCOST")
    - iprp_monstcost.2da: FUN_00611120() - CResRef("IPRP_MONSTCOST")
    - iprp_neg5cost.2da: FUN_00611300() - CResRef("IPRP_NEG5COST")
    - iprp_onhitdur.2da: FUN_006114e0() - CResRef("IPRP_ONHITDUR")
    - iprp_pc.2da: FUN_00612b50() - CResRef("IPRP_PC")
    - iprp_srcost.2da: FUN_00611260() - CResRef("IPRP_SRCOST")
    - pazaakdecks.2da: FUN_00754f60() - CResRef("PazaakDecks")
    - soundset.2da: FUN_006ce0c0() - CResRef("SoundSet")
    - subrace.2da: FUN_00612ab0() - CResRef("Subrace")
    - upcrystals.2da: FUN_00730970() - CResRef("upcrystals")
    - upgrade.2da: FUN_00730970() - CResRef("upgrade")
    
    All files listed above were verified through decompilation analysis of the game executables.
    The canonical file names in this registry match those used by the game engine.
    
    References:
    ----------
        Note: This registry is PyKotor-specific for tooling and modding purposes.
        Game engine analysis performed via Ghidra reverse engineering (Reva MCP server).
    """

    # Canonical 2DA file names (single source of truth)
    # All file names below are verified to be loaded by the game engine via reverse engineering
    # analysis of swkotor.exe and swkotor2.exe using Ghidra (Reva MCP server).
    # See class docstring for detailed function references.
    APPEARANCES: ClassVar[str] = "appearance"  # swkotor.exe: Load2DArrays_Appearance()
    BASEITEMS: ClassVar[str] = "baseitems"  # swkotor.exe: CSWBaseItemArray::Load()
    CAMERAS: ClassVar[str] = "camerastyle"  # swkotor.exe: Load2DArrays_CameraStyle()
    CLASSES: ClassVar[str] = "classes"  # swkotor.exe: LoadClassInfo()
    CLASSPOWERGAIN: ClassVar[str] = "classpowergain"
    COMBATANIMATIONS: ClassVar[str] = "combatanimations"
    CREATURESPEED: ClassVar[str] = "creaturespeed"
    CURSORS: ClassVar[str] = "cursors"  # swkotor.exe: Load2DArrays_Cursor()
    DIALOG_ANIMS: ClassVar[str] = "dialoganimations"  # swkotor.exe: Load2DArrays_DialogAnimations()
    DOORS: ClassVar[str] = "genericdoors"  # swkotor.exe: Load2DArrays_GenericDoors()
    EMOTIONS: ClassVar[str] = "emotion"  # swkotor2.exe: FUN_00612fb0()
    ENC_DIFFICULTIES: ClassVar[str] = "encdifficulty"  # swkotor.exe: Load2DArrays_EncDifficulty()
    EXPRESSIONS: ClassVar[str] = "facialanim"  # swkotor2.exe: FUN_005e6ac0()
    FACTIONS: ClassVar[str] = "repute"  # swkotor.exe: Load2DArrays_Repute()
    FEATS: ClassVar[str] = "feat"  # swkotor.exe: LoadFeatInfo()
    GENDERS: ClassVar[str] = "gender"  # swkotor.exe: Load2DArrays_Gender()
    IPRP_ABILITIES: ClassVar[str] = "iprp_abilities"  # swkotor.exe: Load2DArrays_IPRPAbilities()
    IPRP_ACMODTYPE: ClassVar[str] = "iprp_acmodtype"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_ALIGNGRP: ClassVar[str] = "iprp_aligngrp"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_AMMOTYPE: ClassVar[str] = "iprp_ammotype"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_COMBATDAM: ClassVar[str] = "iprp_combatdam"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_COSTTABLE: ClassVar[str] = "iprp_costtable"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_DAMAGETYPE: ClassVar[str] = "iprp_damagetype"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_IMMUNITY: ClassVar[str] = "iprp_immunity"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_MONSTERHIT: ClassVar[str] = "iprp_mosterhit"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_ONHIT: ClassVar[str] = "iprp_onhit"  # swkotor.exe: Load2DArrays_OnHit()
    IPRP_PARAMTABLE: ClassVar[str] = "iprp_paramtable"  # swkotor.exe: LoadIPRPParamTables()
    IPRP_PROTECTION: ClassVar[str] = "iprp_protection"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_SAVEELEMENT: ClassVar[str] = "iprp_saveelement"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_SAVINGTHROW: ClassVar[str] = "iprp_savingthrow"  # swkotor.exe: LoadIPRPCostTables()
    IPRP_WALK: ClassVar[str] = "iprp_walk"  # swkotor.exe: LoadIPRPCostTables()
    ITEM_PROPERTIES: ClassVar[str] = "itempropdef"  # swkotor.exe: Load2DArrays_ItemPropDef()
    PERCEPTIONS: ClassVar[str] = "ranges"  # swkotor.exe: CSWRules::CSWRules()
    PLACEABLES: ClassVar[str] = "placeables"  # swkotor.exe: Load2DArrays_Placeables()
    PLANETS: ClassVar[str] = "planetary"  # swkotor.exe: Load2DArrays_Planetary()
    PLOT: ClassVar[str] = "plot"  # swkotor.exe: Load2DArrays_PlotXP()
    PORTRAITS: ClassVar[str] = "portraits"  # swkotor.exe: Load2DArrays_Portrait()
    POWERS: ClassVar[str] = "spells"  # swkotor.exe: Load2DArrays_Spells()
    RACES: ClassVar[str] = "racialtypes"  # swkotor.exe: LoadRaceInfo()
    SKILLS: ClassVar[str] = "skills"  # swkotor.exe: LoadSkillInfo()
    SOUNDSETS: ClassVar[str] = "soundset"  # swkotor2.exe: FUN_006ce0c0()
    SPEEDS: ClassVar[str] = "creaturespeed"  # swkotor.exe: Load2DArrays_CreatureSpeed()
    SUBRACES: ClassVar[str] = "subrace"  # swkotor2.exe: FUN_00612ab0()
    TRAPS: ClassVar[str] = "traps"  # swkotor.exe: Load2DArrays_Traps()
    UPGRADES: ClassVar[str] = "upgrade"  # swkotor.exe: CSWGuiUpgrade(), swkotor2.exe: FUN_00730970()
    VIDEO_EFFECTS: ClassVar[str] = "videoeffects"  # swkotor.exe: Load2DArrays_VideoEffects()

    _STRREF_COLUMNS: ClassVar[dict[str, set[str]]] = {}
    _RESREF_COLUMNS: ClassVar[dict[str, set[str]]] = {}
    _GFF_FIELD_TO_2DA: ClassVar[dict[str, ResourceIdentifier]] = {}

    @classmethod
    def init_metadata(cls) -> None:
        if cls._GFF_FIELD_TO_2DA:
            return

        # Merge K1/K2 strref and resref columns into unified maps keyed by filename
        def merge_columns(root_cls: type[ABSColumns2DA]) -> dict[str, set[str]]:
            return root_cls.as_dict()

        cls._STRREF_COLUMNS = {}
        cls._STRREF_COLUMNS.update(merge_columns(K1Columns2DA.StrRefs))
        cls._STRREF_COLUMNS.update(merge_columns(K2Columns2DA.StrRefs))

        cls._RESREF_COLUMNS = {}
        cls._RESREF_COLUMNS.update(merge_columns(K1Columns2DA.ResRefs))
        cls._RESREF_COLUMNS.update(merge_columns(K2Columns2DA.ResRefs))

        # Centralize the GFF field mapping here
        cls._GFF_FIELD_TO_2DA = {
            "ACModifierType": ResourceIdentifier(cls.IPRP_ACMODTYPE, ResourceType.TwoDA),
            "AIStyle": ResourceIdentifier("ai_styles", ResourceType.TwoDA),
            "AlienRaceNode": ResourceIdentifier(cls.RACES, ResourceType.TwoDA),
            "AlienRaceOwner": ResourceIdentifier(cls.RACES, ResourceType.TwoDA),
            "Animation": ResourceIdentifier(cls.DIALOG_ANIMS, ResourceType.TwoDA),
            "Appearance_Type": ResourceIdentifier(cls.APPEARANCES, ResourceType.TwoDA),
            "Appearance": ResourceIdentifier(cls.PLACEABLES, ResourceType.TwoDA),
            "AttackModifier": ResourceIdentifier("iprp_attackmod", ResourceType.TwoDA),
            "BaseItem": ResourceIdentifier(cls.BASEITEMS, ResourceType.TwoDA),
            "BodyBag": ResourceIdentifier("bodybag", ResourceType.TwoDA),
            "BodyVariation": ResourceIdentifier("bodyvariation", ResourceType.TwoDA),
            "BonusFeatID": ResourceIdentifier("iprp_bonusfeat", ResourceType.TwoDA),
            "CameraID": ResourceIdentifier(cls.CAMERAS, ResourceType.TwoDA),
            "CameraStyle": ResourceIdentifier(cls.CAMERAS, ResourceType.TwoDA),
            "CamVidEffect": ResourceIdentifier(cls.VIDEO_EFFECTS, ResourceType.TwoDA),
            "CastSpell": ResourceIdentifier("iprp_spells", ResourceType.TwoDA),
            "Class": ResourceIdentifier(cls.CLASSES, ResourceType.TwoDA),
            "Cursor": ResourceIdentifier(cls.CURSORS, ResourceType.TwoDA),
            "DamageReduction": ResourceIdentifier("iprp_damagered", ResourceType.TwoDA),
            "DamageType": ResourceIdentifier(cls.IPRP_DAMAGETYPE, ResourceType.TwoDA),
            "DamageVsType": ResourceIdentifier("iprp_damagevs", ResourceType.TwoDA),
            "Difficulty": ResourceIdentifier(cls.ENC_DIFFICULTIES, ResourceType.TwoDA),
            "DifficultyIndex": ResourceIdentifier(cls.ENC_DIFFICULTIES, ResourceType.TwoDA),
            "Emotion": ResourceIdentifier(cls.EMOTIONS, ResourceType.TwoDA),
            "FacialAnim": ResourceIdentifier(cls.EXPRESSIONS, ResourceType.TwoDA),
            "Faction": ResourceIdentifier(cls.FACTIONS, ResourceType.TwoDA),
            "FactionID": ResourceIdentifier(cls.FACTIONS, ResourceType.TwoDA),
            "Feat": ResourceIdentifier(cls.FEATS, ResourceType.TwoDA),
            "FeatID": ResourceIdentifier(cls.FEATS, ResourceType.TwoDA),
            "Gender": ResourceIdentifier(cls.GENDERS, ResourceType.TwoDA),
            "GenericType": ResourceIdentifier(cls.DOORS, ResourceType.TwoDA),
            "ImmunityType": ResourceIdentifier(cls.IPRP_IMMUNITY, ResourceType.TwoDA),
            "LightColor": ResourceIdentifier("iprp_lightcol", ResourceType.TwoDA),
            "LoadScreenID": ResourceIdentifier("loadscreens", ResourceType.TwoDA),
            "MarkDown": ResourceIdentifier("merchants", ResourceType.TwoDA),
            "MarkUp": ResourceIdentifier("merchants", ResourceType.TwoDA),
            "ModelVariation": ResourceIdentifier(cls.BASEITEMS, ResourceType.TwoDA),
            "MonsterDamage": ResourceIdentifier("iprp_monstdam", ResourceType.TwoDA),
            "MusicBattle": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "MusicDay": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "MusicDelay": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "MusicNight": ResourceIdentifier("ambientmusic", ResourceType.TwoDA),
            "OnHit": ResourceIdentifier(cls.IPRP_ONHIT, ResourceType.TwoDA),
            "PaletteID": ResourceIdentifier("palette", ResourceType.TwoDA),
            "Param1": ResourceIdentifier(cls.IPRP_PARAMTABLE, ResourceType.TwoDA),
            "Param1Value": ResourceIdentifier(cls.IPRP_PARAMTABLE, ResourceType.TwoDA),
            "PerceptionRange": ResourceIdentifier(cls.PERCEPTIONS, ResourceType.TwoDA),
            "Phenotype": ResourceIdentifier("phenotype", ResourceType.TwoDA),
            "PlanetID": ResourceIdentifier(cls.PLANETS, ResourceType.TwoDA),
            "PlotIndex": ResourceIdentifier(cls.PLOT, ResourceType.TwoDA),
            "PortraitId": ResourceIdentifier(cls.PORTRAITS, ResourceType.TwoDA),
            "Race": ResourceIdentifier(cls.RACES, ResourceType.TwoDA),
            "SavedGame": ResourceIdentifier("saves", ResourceType.TwoDA),
            "SaveType": ResourceIdentifier(cls.IPRP_SAVEELEMENT, ResourceType.TwoDA),
            "SkillBonus": ResourceIdentifier("iprp_skillcost", ResourceType.TwoDA),
            "SkillID": ResourceIdentifier(cls.SKILLS, ResourceType.TwoDA),
            "SoundSetFile": ResourceIdentifier(cls.SOUNDSETS, ResourceType.TwoDA),
            "SpecialWalk": ResourceIdentifier(cls.IPRP_WALK, ResourceType.TwoDA),
            "Spell": ResourceIdentifier(cls.POWERS, ResourceType.TwoDA),
            "SpellId": ResourceIdentifier(cls.POWERS, ResourceType.TwoDA),
            "SpellResistance": ResourceIdentifier("iprp_spellres", ResourceType.TwoDA),
            "Subrace": ResourceIdentifier(cls.SUBRACES, ResourceType.TwoDA),
            "SubraceIndex": ResourceIdentifier(cls.SUBRACES, ResourceType.TwoDA),
            "Subtype": ResourceIdentifier(cls.POWERS, ResourceType.TwoDA),
            "TextureVar": ResourceIdentifier("textures", ResourceType.TwoDA),
            "Trap": ResourceIdentifier("iprp_traptype", ResourceType.TwoDA),
            "TrapType": ResourceIdentifier(cls.TRAPS, ResourceType.TwoDA),
            "UpgradeType": ResourceIdentifier(cls.UPGRADES, ResourceType.TwoDA),
            "VideoResRef": ResourceIdentifier(cls.VIDEO_EFFECTS, ResourceType.TwoDA),
            "VisualType": ResourceIdentifier("visualeffects", ResourceType.TwoDA),
            "WalkRate": ResourceIdentifier(cls.SPEEDS, ResourceType.TwoDA),
            "WeightIncrease": ResourceIdentifier("iprp_weightinc", ResourceType.TwoDA),
        }

    @classmethod
    def gff_field_mapping(cls) -> dict[str, ResourceIdentifier]:
        cls.init_metadata()
        return cls._GFF_FIELD_TO_2DA

    @classmethod
    def columns_for(cls, data_type: Literal["resref", "strref"]) -> dict[str, set[str]]:
        cls.init_metadata()
        return cls._STRREF_COLUMNS if data_type == "strref" else cls._RESREF_COLUMNS

    @classmethod
    def files(cls) -> set[str]:
        cls.init_metadata()
        files: set[str] = set(cls._STRREF_COLUMNS.keys()) | set(cls._RESREF_COLUMNS.keys())
        return files

class TwoDAManager:
    """Manager for 2DA file lookups within an installation.
    
    Provides methods to search for string references or resource references across
    all known 2DA files in a game installation.
    
    References:
    ----------
        Note: This manager is PyKotor-specific for tooling and modding purposes.
    """
    def __init__(self, installation: Installation):
        TwoDARegistry.init_metadata()
        self._installation: Installation = installation

    @classmethod
    def get_column_names(
        cls,
        data_type: Literal["resref", "strref"],
    ) -> list[str]:
        """Retrieve all column names for a given data type across known 2DA files."""
        result: list[str] = []
        for columns in TwoDARegistry.columns_for(data_type).values():
            result.extend(columns)
        return list(set(result))

    def lookup_in_installation(self, query: str, data_type: Literal["resref", "strref"]) -> LookupResult2DA | None:
        from pykotor.resource.formats.twoda.twoda_auto import read_2da  # lazy import
        from pykotor.tools.path import CaseAwarePath

        if not query:
            return None

        targets = TwoDARegistry.columns_for(data_type)
        for filename, columns in targets.items():
            ident = ResourceIdentifier.identify(filename)
            result = self._installation.resource(ident.resname, ident.restype)
            if result is None or result.data is None:
                continue
            table = read_2da(result.data)
            for row_index in range(table.get_height()):
                row = table.get_row(row_index)
                for column in columns:
                    try:
                        cell = row.get_string(column)
                    except Exception:  # noqa: S112
                        continue
                    if cell == query:
                        return LookupResult2DA(
                            filepath=CaseAwarePath(f"{filename}"),
                            row_index=row_index,
                            column_name=column,
                            contents=cell or "",
                            entire_row=row,
                        )
        return None
