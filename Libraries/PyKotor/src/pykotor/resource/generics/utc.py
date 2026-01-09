from __future__ import annotations

from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from pykotor.common.language import LocalizedString
from pykotor.common.misc import EquipmentSlot, Game, InventoryItem, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, GFFFieldType, GFFList, GFFStruct, bytes_gff, read_gff, write_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTC:
    """Stores creature data.

    UTC files are GFF-based format files that store creature definitions including
    stats, appearance, inventory, feats, and script hooks.

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x00500350 - CSWSCreature::LoadCreature (698 bytes, 101 lines)
                - Main UTC GFF parser entry point
                - Loads creature from GFF structure
                - Function signature: LoadCreature(CSWSCreature* this, CResGFF* param_1, CResStruct* param_2, int param_3)
                - Called from LoadCreatures (0x00504a70) and LoadLimboCreatures (0x004c8c70)
            - 0x00560e60 - CSWSCreatureStats::ReadStatsFromGff (537 bytes)
                - Reads creature stats from GFF (called by LoadCreature)
                - Loads FirstName, LastName, Gender, Race, Subrace, PerceptionRange, and other stat fields
            - 0x004ffda0 - CSWSCreature::ReadItemsFromGff
                - Reads creature inventory items from GFF
            - 0x00500610 - CSWSCreature::SaveCreature
                - UTC GFF writer function
                - Writes all creature fields to GFF structure
            - 0x00749394 - "FirstName" string reference
            - 0x00749388 - "LastName" string reference
            - 0x0074af48 - "Gender" string reference
            - 0x0074af30 - "Race" string reference
            - 0x0074af28 - "Subrace" string reference
            - 0x0074ae20 - "PerceptionRange" string reference
        
        KotOR II / TSL (swkotor2.exe):
            - Functionally equivalent UTC parsing logic
            - Same GFF field structure and parsing behavior
            - String references at different addresses due to binary layout differences
        
        GFF Field Structure (from LoadCreature and ReadStatsFromGff analysis):
            - Root struct fields:
                - "AreaId" (DWORD) - Area identifier
                - "DetectMode" (BYTE) - Detect mode flag
                - "StealthMode" (BYTE) - Stealth mode flag
                - "CreatureSize" (INT32) - Creature size (default 3)
                - "IsDestroyable" (BYTE) - Whether creature is destroyable (default 1)
                - "IsRaiseable" (BYTE) - Whether creature is raiseable (default 1)
                - "DeadSelectable" (BYTE) - Whether dead creature is selectable (default 1)
                - "AmbientAnimState" (BYTE) - Ambient animation state
                - "Animation" (INT32) - Animation ID (default 10000)
                - "CreatnScrptFird" (BYTE) - Creation script fired flag
                - "PM_IsDisguised" (BYTE) - Player module is disguised flag
                - "PM_Appearance" (WORD) - Player module appearance (if disguised)
                - "Listening" (BYTE) - Listening flag
            - Stats struct fields (from ReadStatsFromGff):
                - "FirstName" (CExoLocString) - First name
                - "LastName" (CExoLocString) - Last name
                - "Gender" (BYTE) - Gender identifier
                - "Race" (BYTE) - Race identifier
                - "Subrace" (BYTE) - Subrace identifier
                - "PerceptionRange" (FLOAT) - Perception range
                - Additional stat fields (STR, DEX, CON, INT, WIS, CHA, etc.)
            - Script fields:
                - "ScriptHeartbeat" (CResRef) - Heartbeat script
                - "ScriptOnNotice" (CResRef) - On notice script
                - "ScriptSpellAt" (CResRef) - Spell at script
                - "ScriptAttacked" (CResRef) - Attacked script
                - "ScriptDamaged" (CResRef) - Damaged script
                - "ScriptEndRound" (CResRef) - End round script
                - "ScriptDialogue" (CResRef) - Dialogue script
                - "ScriptSpawn" (CResRef) - Spawn script
                - "ScriptRested" (CResRef) - Rested script
                - "ScriptDeath" (CResRef) - Death script
                - "ScriptUserDefine" (CResRef) - User defined script
                - "ScriptOnBlocked" (CResRef) - On blocked script
            - Item fields:
                - "ItemList" (GFFList) - List of inventory items
            - Spell fields:
                - "SpellList" (GFFList) - List of known spells
        
        Note: UTC files are GFF format files with specific structure definitions (GFFContent.UTC)

    Derivations and Other Implementations:
    ----------
        https://github.com/th3w1zard1/KotOR-dotNET/tree/master/AuroraParsers/UTCObject.cs (UTC parser)
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleCreature.ts (Creature module object)
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTC.cs (UTC class definition)

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this creature template.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:15 (ResRef property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:73 (inherited from ModuleObject)

        tag: "Tag" field. The tag identifier for this creature.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:18 (Tag property)

        comment: "Comment" field. Developer comment for this creature.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:19 (Comment property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:96 (comment field)

        conversation: "Conversation" field. ResRef to the dialog file for this creature.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:16 (Conversation property)

        first_name: "FirstName" field. Localized first name of the creature.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:21 (FirstName property)

        last_name: "LastName" field. Localized last name of the creature.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:22 (LastName property)

        subrace_id: "SubraceIndex" field. Subrace index identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:25 (SubraceID property)

        perception_id: "PerceptionRange" field. Perception range value.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:27 (PerceptionID property)

        race_id: "Race" field. Race identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:24 (RaceID property)

        appearance_id: "Appearance_Type" field. Appearance type identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:28 (AppearanceID property)

        gender_id: "Gender" field. Gender identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:29 (GenderID property)

        faction_id: "FactionID" field. Faction identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:30 (FactionID property)

        walkrate_id: "WalkRate" field. Walk rate identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:31 (WalkRateID property)

        soundset_id: "SoundSetFile" field. Soundset file identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:32 (SoundsetID property)

        portrait_id: "PortraitId" field. Portrait identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:26 (PortraitID property)

        body_variation: "BodyVariation" field. Body variation index.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:38 (BodyVariation property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:82 (bodyVariation field)

        texture_variation: "TextureVar" field. Texture variation index.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:39 (TextureVariation property)

        not_reorienting: "NotReorienting" field. Whether creature should not reorient.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:41 (NotReorientating property)

        party_interact: "PartyInteract" field. Whether party members can interact.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:42 (PartyInteract property)

        no_perm_death: "NoPermDeath" field. Whether creature cannot permanently die.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:43 (NoPermanentDeath property)

        min1_hp: "Min1HP" field. Whether creature HP cannot go below 1.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:44 (Min1HP property)

        plot: "Plot" field. Whether creature is plot-critical.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:45 (Plot property)

        interruptable: "Interruptable" field. Whether creature can be interrupted.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:46 (Interruptable property)

        is_pc: "IsPC" field. Whether creature is a player character.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:47 (IsPC property)

        disarmable: "Disarmable" field. Whether creature can be disarmed.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:48 (Disarmable property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:100 (disarmable field)

        alignment: "GoodEvil" field. Alignment value (good/evil axis).
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:52 (Alignment property)

        challenge_rating: "ChallengeRating" field. Challenge rating value.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:54 (ChallengeRating property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:94 (challengeRating field)

        blindspot: "BlindSpot" field. Blind spot value. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:55 (Blindspot property)

        multiplier_set: "MultiplierSet" field. Multiplier set identifier. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:56 (MultiplierSet property)

        natural_ac: "NaturalAC" field. Natural armor class value.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:58 (NaturalAC property)

        reflex_bonus: "refbonus" field. Reflex save bonus.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:59 (ReflexBonus property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:91 (refbonus field)

        willpower_bonus: "willbonus" field. Will save bonus.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:60 (WillBonus property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:92 (willbonus field)

        fortitude_bonus: "fortbonus" field. Fortitude save bonus.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:61 (FortitudeBonus property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:90 (fortbonus field)

        strength: "Str" field. Strength ability score.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:79 (Strength property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:88 (str field)

        dexterity: "Dex" field. Dexterity ability score.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:80 (Dexterity property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:86 (dex field)

        constitution: "Con" field. Constitution ability score.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:81 (Constitution property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:85 (con field)

        intelligence: "Int" field. Intelligence ability score.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:82 (Intelligence property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:87 (int field)

        wisdom: "Wis" field. Wisdom ability score.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:83 (Wisdom property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:89 (wis field)

        charisma: "Cha" field. Charisma ability score.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:84 (Charisma property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:84 (cha field)

        current_hp: "CurrentHitPoints" field. Current hit points.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:64 (CurrentHP property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:98 (currentHitPoints field)

        max_hp: "MaxHitPoints" field. Maximum hit points.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:65 (MaxHP property)

        hp: "HitPoints" field. Base hit points.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:63 (HP property)

        fp: "CurrentForce" field. Current force points.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:67 (FP property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleCreature.ts:97 (currentForce field)

        max_fp: "ForcePoints" field. Maximum force points.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:68 (MaxFP property)

        on_end_dialog: "ScriptEndDialogu" field. Script to run when dialog ends.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:87 (OnEndDialog property)

        on_blocked: "ScriptOnBlocked" field. Script to run when blocked.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:88 (OnBlocked property)

        on_heartbeat: "ScriptHeartbeat" field. Script to run on heartbeat.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:89 (OnHeartbeat property)

        on_notice: "ScriptOnNotice" field. Script to run when noticing something.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:90 (OnNotice property)

        on_spell: "ScriptSpellAt" field. Script to run when spell is cast at creature.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:91 (OnSpell property)

        on_attacked: "ScriptAttacked" field. Script to run when attacked.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:92 (OnAttack property)

        on_damaged: "ScriptDamaged" field. Script to run when damaged.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:93 (OnDamaged property)

        on_disturbed: "ScriptDisturbed" field. Script to run when disturbed.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:94 (OnDisturbed property)

        on_end_round: "ScriptEndRound" field. Script to run at end of combat round.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:95 (OnEndRound property)

        on_dialog: "ScriptDialogue" field. Script to run when dialog starts.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:96 (OnDialog property)

        on_spawn: "ScriptSpawn" field. Script to run when creature spawns.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:97 (OnSpawn property)

        on_rested: "ScriptRested" field. Script to run when creature rests. Not used by engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:98 (OnRested property)

        on_death: "ScriptDeath" field. Script to run when creature dies.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:99 (OnDeath property)

        on_user_defined: "ScriptUserDefine" field. Script to run on user-defined event.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:100 (OnUserDefined property)

        ignore_cre_path: "IgnoreCrePath" field. Whether to ignore creature pathfinding. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:49 (IgnoreCreaturePath property)

        hologram: "Hologram" field. Whether creature is a hologram. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:50 (Hologram property)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:36 (PaletteID property)

        bodybag_id: "BodyBag" field. Body bag identifier. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:81 (bodyBag field)

        deity: "Deity" field. Deity name. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:99 (deity field)

        description: "Description" field. Localized description. Not used by the game engine.

        lawfulness: "LawfulChaotic" field. Lawfulness value. Not used by the game engine.

        phenotype_id: "Phenotype" field. Phenotype identifier. Not used by the game engine.

        subrace_name: "Subrace" field. Subrace name. Not used by the game engine.

        classes: List of UTCClass objects representing creature classes and levels.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTC.cs:101+ (Classes property)

        feats: List of feat identifiers.

        inventory: List of InventoryItem objects in creature's inventory.

        equipment: Dictionary mapping EquipmentSlot to InventoryItem for equipped items.
    """

    BINARY_TYPE = ResourceType.UTC

    def __init__(self):
        # internal use only, to preserve the original order:
        self._original_feat_mapping: dict[int, int] = {}
        self._extra_unimplemented_skills: list[int] = []

        self.resref: ResRef = ResRef.from_blank()
        self.conversation: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.comment: str = ""

        self.first_name: LocalizedString = LocalizedString.from_invalid()
        self.last_name: LocalizedString = LocalizedString.from_invalid()

        self.subrace_id: int = 0
        self.portrait_id: int = 0
        self.perception_id: int = 0
        self.race_id: int = 0
        self.appearance_id: int = 0
        self.gender_id: int = 0
        self.faction_id: int = 0
        self.walkrate_id: int = 0
        self.soundset_id: int = 0
        self.save_will: int = 0
        self.save_fortitude: int = 0
        self.morale: int = 0
        self.morale_recovery: int = 0
        self.morale_breakpoint: int = 0

        self.body_variation: int = 0
        self.texture_variation: int = 0

        self.portrait_resref: ResRef = ResRef.from_blank()

        self.not_reorienting: bool = False
        self.party_interact: bool = False
        self.no_perm_death: bool = False
        self.min1_hp: bool = False
        self.plot: bool = False
        self.interruptable: bool = False
        self.is_pc: bool = False  # ???
        self.disarmable: bool = False  # ???
        self.ignore_cre_path: bool = False  # KotOR 2 Only
        self.hologram: bool = False  # KotOR 2 Only
        self.will_not_render: bool = False  # Kotor 2 Only

        self.alignment: int = 0
        self.challenge_rating: float = 0.0
        self.blindspot: float = 0.0  # KotOR 2 Only
        self.multiplier_set: int = 0  # KotOR 2 Only

        self.natural_ac: int = 0
        self.reflex_bonus: int = 0
        self.willpower_bonus: int = 0
        self.fortitude_bonus: int = 0

        self.current_hp: int = 0
        self.max_hp: int = 0
        self.hp: int = 0

        self.max_fp: int = 0
        self.fp: int = 0

        self.strength: int = 0
        self.dexterity: int = 0
        self.constitution: int = 0
        self.intelligence: int = 0
        self.wisdom: int = 0
        self.charisma: int = 0

        self.computer_use: int = 0
        self.demolitions: int = 0
        self.stealth: int = 0
        self.awareness: int = 0
        self.persuade: int = 0
        self.repair: int = 0
        self.security: int = 0
        self.treat_injury: int = 0

        self.on_end_dialog: ResRef = ResRef.from_blank()
        self.on_blocked: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_notice: ResRef = ResRef.from_blank()
        self.on_spell: ResRef = ResRef.from_blank()
        self.on_attacked: ResRef = ResRef.from_blank()
        self.on_damaged: ResRef = ResRef.from_blank()
        self.on_disturbed: ResRef = ResRef.from_blank()
        self.on_end_round: ResRef = ResRef.from_blank()
        self.on_dialog: ResRef = ResRef.from_blank()
        self.on_spawn: ResRef = ResRef.from_blank()
        self.on_rested: ResRef = ResRef.from_blank()
        self.on_death: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()

        self.classes: list[UTCClass] = []
        self.feats: list[int] = []
        self.inventory: list[InventoryItem] = []
        self.equipment: dict[EquipmentSlot, InventoryItem] = {}

        # Deprecated:
        self.palette_id: int = 0
        self.bodybag_id: int = 1
        self.deity: str = ""
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.lawfulness: int = 0
        self.phenotype_id: int = 0
        # self.on_rested: ResRef = ResRef.from_blank()
        self.subrace_name: str = ""


class UTCClass:
    """Represents a creature class with its level and known powers.

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x005afce0 - CSWSCreatureStats::ReadStatsFromGff (7835 bytes, 1103 lines)
                - Loads ClassList from UTC GFF structure
                - Function signature: ReadStatsFromGff(CSWSCreatureStats* this, CResGFF* param_1, CResStruct* param_2, CSWSCreatureAppearanceInfo* param_3)
                - Called from LoadCreature (0x00500350) and LoadFromTemplate (0x00502820)
            - Reads ClassList (GFFList) at line 459:
                - Class (INT) - class identifier
                - ClassLevel (SHORT) - class level
                - SpellsPerDayList (GFFList) - spells per day list (for Jedi classes):
                    - NumSpellsLeft (BYTE) - number of spells left
                - KnownList0, KnownList1, KnownList2 (GFFList) - known spells/powers lists
        KotOR II / TSL (swkotor2.exe):
            - Functionally identical to K1 implementation
            - Same GFF structure and parsing logic


    Attributes:
    ----------
        class_id: The class identifier.

        class_level: The level in this class.

        powers: List of spell/power identifiers known by this class.
    """

    def __init__(
        self,
        class_id: int,
        class_level: int = 0,
    ):
        # internal use only, to preserve the original order:
        self._original_powers_mapping: dict[int, int] = {}

        self.class_id: int = class_id
        self.class_level: int = class_level
        self.powers: list[int] = []

    def __repr__(self) -> str:
        return f"UTCClass(class_id={self.class_id}, class_level={self.class_level}, powers={self.powers})"

    def __eq__(
        self,
        other: UTCClass | object,
    ):
        if self is other:
            return True
        if isinstance(other, UTCClass):
            return self.class_id == other.class_id and self.class_level == other.class_level
        return NotImplemented


def construct_utc(
    gff: GFF,
) -> UTC:
    """Constructs a UTC object from a GFF structure.

    Parses UTC (creature template) data from a GFF file, reading all fields
    including stats, skills, classes, feats, inventory, and equipment.

    References:
    ----------
        Based on swkotor.exe UTC structure:
        - CSWSCreature::LoadCreature @ 0x00500350 - Loads creature template
        - CSWSCreatureStats::ReadStatsFromGff @ 0x00560e60 - Reads creature stats from GFF
        - CResGFF::CreateGFFFile @ 0x00411260 - Creates GFF file structure
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs (UTC compilation from GFF)
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleCreature.ts (UTC loading via ResourceLoader)

    """
    utc = UTC()

    root = gff.root
    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTC.cs:15 (ResRef property)
    utc.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    
    utc.tag = root.acquire("Tag", "", str)
    
    utc.comment = root.acquire("Comment", "", str)
    
    utc.conversation = root.acquire("Conversation", ResRef.from_blank())

    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTC.cs:21 (FirstName property)
    utc.first_name = root.acquire("FirstName", LocalizedString.from_invalid())
    
    utc.last_name = root.acquire("LastName", LocalizedString.from_invalid())

    
    utc.subrace_id = root.acquire("SubraceIndex", 0)
    
    utc.perception_id = root.acquire("PerceptionRange", 0)
    
    utc.race_id = root.acquire("Race", 0)
    
    utc.appearance_id = root.acquire("Appearance_Type", 0)
    
    utc.gender_id = root.acquire("Gender", 0)
    
    utc.faction_id = root.acquire("FactionID", 0)
    
    utc.walkrate_id = root.acquire("WalkRate", 0)
    
    utc.soundset_id = root.acquire("SoundSetFile", 0)
    
    utc.portrait_id = root.acquire("PortraitId", 0)
    
    utc.palette_id = root.acquire("PaletteID", 0)
    
    utc.bodybag_id = root.acquire("BodyBag", 0)

    # TODO(th3w1zard1): Add these seemingly missing fields into UTCEditor?
    utc.portrait_resref = root.acquire("Portrait", ResRef.from_blank())
    utc.save_will = root.acquire("SaveWill", 0)
    utc.save_fortitude = root.acquire("SaveFortitude", 0)
    utc.morale = root.acquire("Morale", 0)
    utc.morale_recovery = root.acquire("MoraleRecovery", 0)
    utc.morale_breakpoint = root.acquire("MoraleBreakpoint", 0)

    
    utc.body_variation = root.acquire("BodyVariation", 0)
    
    utc.texture_variation = root.acquire("TextureVar", 0)

    
    utc.not_reorienting = bool(root.acquire("NotReorienting", 0))
    
    utc.party_interact = bool(root.acquire("PartyInteract", 0))
    
    utc.no_perm_death = bool(root.acquire("NoPermDeath", 0))
    
    utc.min1_hp = bool(root.acquire("Min1HP", 0))
    
    utc.plot = bool(root.acquire("Plot", 0))
    
    utc.interruptable = bool(root.acquire("Interruptable", 0))
    
    utc.is_pc = bool(root.acquire("IsPC", 0))
    
    utc.disarmable = bool(root.acquire("Disarmable", 0))
    
    utc.ignore_cre_path = bool(root.acquire("IgnoreCrePath", 0))
    
    utc.hologram = bool(root.acquire("Hologram", 0))
    
    utc.will_not_render = bool(root.acquire("WillNotRender", 0))

    
    utc.alignment = root.acquire("GoodEvil", 0)
    
    utc.challenge_rating = root.acquire("ChallengeRating", 0.0)
    
    utc.blindspot = root.acquire("BlindSpot", 0.0)
    
    utc.multiplier_set = root.acquire("MultiplierSet", 0)

    
    utc.natural_ac = root.acquire("NaturalAC", 0)
    
    utc.reflex_bonus = root.acquire("refbonus", 0)
    
    utc.willpower_bonus = root.acquire("willbonus", 0)
    
    utc.fortitude_bonus = root.acquire("fortbonus", 0)

    
    utc.strength = root.acquire("Str", 0)
    
    utc.dexterity = root.acquire("Dex", 0)
    
    utc.constitution = root.acquire("Con", 0)
    
    utc.intelligence = root.acquire("Int", 0)
    
    utc.wisdom = root.acquire("Wis", 0)
    
    utc.charisma = root.acquire("Cha", 0)

    
    utc.current_hp = root.acquire("CurrentHitPoints", 0)
    
    utc.max_hp = root.acquire("MaxHitPoints", 0)
    
    utc.hp = root.acquire("HitPoints", 0)
    
    utc.max_fp = root.acquire("ForcePoints", 0)
    
    utc.fp = root.acquire("CurrentForce", 0)

    
    # Script hooks: ResRefs to NCS scripts executed on specific events
    utc.on_end_dialog = root.acquire("ScriptEndDialogu", ResRef.from_blank())
    
    utc.on_blocked = root.acquire("ScriptOnBlocked", ResRef.from_blank())
    
    utc.on_heartbeat = root.acquire("ScriptHeartbeat", ResRef.from_blank())
    
    utc.on_notice = root.acquire("ScriptOnNotice", ResRef.from_blank())
    
    utc.on_spell = root.acquire("ScriptSpellAt", ResRef.from_blank())
    
    utc.on_attacked = root.acquire("ScriptAttacked", ResRef.from_blank())
    
    utc.on_damaged = root.acquire("ScriptDamaged", ResRef.from_blank())
    
    utc.on_disturbed = root.acquire("ScriptDisturbed", ResRef.from_blank())
    
    utc.on_end_round = root.acquire("ScriptEndRound", ResRef.from_blank())
    
    utc.on_dialog = root.acquire("ScriptDialogue", ResRef.from_blank())
    
    utc.on_spawn = root.acquire("ScriptSpawn", ResRef.from_blank())
    
    utc.on_rested = root.acquire("ScriptRested", ResRef.from_blank())
    
    utc.on_death = root.acquire("ScriptDeath", ResRef.from_blank())
    
    utc.on_user_defined = root.acquire("ScriptUserDefine", ResRef.from_blank())

    
    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:95-103 (SkillList parsing with index-based access)
    # SkillList is a GFF List containing 8 structs, each with a "Rank" uint8 field
    # Skill order: [0] Computer Use, [1] Demolitions, [2] Stealth, [3] Awareness,
    #              [4] Persuade, [5] Repair, [6] Security, [7] Treat Injury
    if not root.exists("SkillList") or root.what_type("SkillList") != GFFFieldType.List:
        if root.exists("SkillList"):
            RobustLogger().error("SkillList in UTC's must be a GFFList, recreating now...")
            del root._fields["SkillList"]
        else:
            RobustLogger().error("SkillList must exist in UTC's, creating now...")
        
        # Create default SkillList with 8 empty skill entries (Rank = 0)
        skill_list = root.set_list("SkillList", GFFList())
        skill_list.add(0).set_uint8("Rank", 0)  # Computer Use
        skill_list.add(1).set_uint8("Rank", 0)  # Demolitions
        skill_list.add(2).set_uint8("Rank", 0)  # Stealth
        skill_list.add(3).set_uint8("Rank", 0)  # Awareness
        skill_list.add(4).set_uint8("Rank", 0)  # Persuade
        skill_list.add(5).set_uint8("Rank", 0)  # Repair
        skill_list.add(6).set_uint8("Rank", 0)  # Security
        skill_list.add(7).set_uint8("Rank", 0)  # Treat Injury
    skill_list_acquired: GFFList = root.acquire("SkillList", GFFList())
    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:96 (skillList.Get(0).Get("Rank")) (skillList.Get(0)
    # Parse each skill from SkillList array by index
    if skill_list_acquired.at(0) is not None:
        skill_struct = skill_list_acquired.at(0)
        assert skill_struct is not None, "SkillList[0] struct is None"
        
        utc.computer_use = skill_struct.acquire("Rank", 0)  # Skill index 0: Computer Use
    if skill_list_acquired.at(1) is not None:
        skill_struct = skill_list_acquired.at(1)
        assert skill_struct is not None, "SkillList[1] struct is None"
        utc.demolitions = skill_struct.acquire("Rank", 0)  # Skill index 1: Demolitions
    if skill_list_acquired.at(2) is not None:
        skill_struct = skill_list_acquired.at(2)
        assert skill_struct is not None, "SkillList[2] struct is None"
        utc.stealth = skill_struct.acquire("Rank", 0)  # Skill index 2: Stealth
    if skill_list_acquired.at(3) is not None:
        skill_struct = skill_list_acquired.at(3)
        assert skill_struct is not None, "SkillList[3] struct is None"
        utc.awareness = skill_struct.acquire("Rank", 0)  # Skill index 3: Awareness
    if skill_list_acquired.at(4) is not None:
        skill_struct = skill_list_acquired.at(4)
        assert skill_struct is not None, "SkillList[4] struct is None"
        utc.persuade = skill_struct.acquire("Rank", 0)  # Skill index 4: Persuade
    if skill_list_acquired.at(5) is not None:
        skill_struct = skill_list_acquired.at(5)
        assert skill_struct is not None, "SkillList[5] struct is None"
        utc.repair = skill_struct.acquire("Rank", 0)  # Skill index 5: Repair
    if skill_list_acquired.at(6) is not None:
        skill_struct = skill_list_acquired.at(6)
        assert skill_struct is not None, "SkillList[6] struct is None"
        utc.security = skill_struct.acquire("Rank", 0)  # Skill index 6: Security
    if skill_list_acquired.at(7) is not None:
        skill_struct = skill_list_acquired.at(7)
        assert skill_struct is not None, "SkillList[7] struct is None"
        utc.treat_injury = skill_struct.acquire("Rank", 0)  # Skill index 7: Treat Injury

    
    # Discrepancy: Some KotOR 1 UTC files contain more than 8 skill entries (up to 20)
    # PyKotor preserves extra skills in _extra_unimplemented_skills for round-trip compatibility
    # NOTE: reone and Kotor.NET only parse the first 8 skills, ignoring extras
    if len(skill_list_acquired._structs) > 8:
        utc._extra_unimplemented_skills = [skill_struct.acquire("Rank", 0) for skill_struct in skill_list_acquired._structs[8:]]

    
    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:105-120 (ClassList parsing)
    # ClassList contains creature classes (e.g., Soldier, Scout, Scoundrel, Jedi Consular, etc.)
    class_list: GFFList = root.acquire("ClassList", GFFList())
    for class_struct in class_list:
        
        class_id = class_struct.acquire("Class", 0)  # Class type identifier (e.g., 0=Soldier, 1=Scout)
        class_level = class_struct.acquire("ClassLevel", 0)  # Level in this class
        utc_class = UTCClass(class_id, class_level)

        
        
        # KnownList0 contains spells/powers known by this class level
        power_list: GFFList = class_struct.acquire("KnownList0", GFFList())
        for index, power_struct in enumerate(power_list):
            
            spell_thing = power_struct.acquire("Spell", 0)  # Spell/power ID
            utc_class.powers.append(spell_thing)
            # PyKotor-specific: Preserve original order for round-trip compatibility
            utc_class._original_powers_mapping[spell_thing] = index

        utc.classes.append(utc_class)

    
    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:122-125 (FeatList parsing)
    # FeatList contains feat identifiers that the creature has
    feat_list: GFFList = root.acquire("FeatList", GFFList())
    for index, feat_struct in enumerate(feat_list):
        
        feat_id_thing: int = feat_struct.acquire("Feat", 0)  # Feat identifier
        utc.feats.append(feat_id_thing)
        # PyKotor-specific: Preserve original order for round-trip compatibility
        utc._original_feat_mapping[feat_id_thing] = index

    
    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:127-140 (Equip_ItemList parsing)
    # Equip_ItemList contains equipped items, struct_id indicates equipment slot
    equipment_list: GFFList = root.acquire("Equip_ItemList", GFFList())
    for equipment_struct in equipment_list:
        
        # struct_id maps to EquipmentSlot enum (e.g., 0=Right Hand, 1=Left Hand, 2=Armor)
        slot = EquipmentSlot(equipment_struct.struct_id)  # Equipment slot from struct_id
        resref = equipment_struct.acquire("EquippedRes", ResRef.from_blank())  # Item ResRef
        droppable = bool(equipment_struct.acquire("Dropable", 0))  # Whether item can be dropped
        utc.equipment[slot] = InventoryItem(resref, droppable)

    
    
    # https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTC/UTCCompiler.cs:142-150 (ItemList parsing)
    # ItemList contains items in creature's inventory (not equipped)
    item_list: GFFList = root.acquire("ItemList", GFFList())
    for item_struct in item_list:
        
        resref = item_struct.acquire("InventoryRes", ResRef.from_blank())  # Item ResRef
        droppable = bool(item_struct.acquire("Dropable", 0))  # Whether item can be dropped
        utc.inventory.append(InventoryItem(resref, droppable))

    return utc


def dismantle_utc(
    utc: UTC,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTC)

    root = gff.root
    root.set_resref("TemplateResRef", utc.resref)
    root.set_string("Tag", utc.tag)
    root.set_string("Comment", utc.comment)
    root.set_resref("Conversation", utc.conversation)

    root.set_locstring("FirstName", utc.first_name)
    root.set_locstring("LastName", utc.last_name)

    root.set_uint8("SubraceIndex", utc.subrace_id)
    root.set_uint8("PerceptionRange", utc.perception_id)
    root.set_uint8("Race", utc.race_id)
    root.set_uint16("Appearance_Type", utc.appearance_id)
    root.set_uint8("Gender", utc.gender_id)
    root.set_uint16("FactionID", utc.faction_id)
    root.set_int32("WalkRate", utc.walkrate_id)
    root.set_uint16("SoundSetFile", utc.soundset_id)
    root.set_uint16("PortraitId", utc.portrait_id)

    # TODO(th3w1zard1): Add these seemingly missing fields into UTCEditor?
    root.set_resref("Portrait", utc.portrait_resref)
    root.set_uint8("SaveWill", utc.save_will)
    root.set_uint8("SaveFortitude", utc.save_fortitude)
    root.set_uint8("Morale", utc.morale)
    root.set_uint8("MoraleRecovery", utc.morale_recovery)
    root.set_uint8("MoraleBreakpoint", utc.morale_breakpoint)

    root.set_uint8("BodyVariation", utc.body_variation)
    root.set_uint8("TextureVar", utc.texture_variation)

    root.set_uint8("NotReorienting", utc.not_reorienting)
    root.set_uint8("PartyInteract", utc.party_interact)
    root.set_uint8("NoPermDeath", utc.no_perm_death)
    root.set_uint8("Min1HP", utc.min1_hp)
    root.set_uint8("Plot", utc.plot)
    root.set_uint8("Interruptable", utc.interruptable)
    root.set_uint8("IsPC", utc.is_pc)
    root.set_uint8("Disarmable", utc.disarmable)

    root.set_uint8("GoodEvil", utc.alignment)
    root.set_single("ChallengeRating", utc.challenge_rating)

    root.set_uint8("NaturalAC", utc.natural_ac)
    root.set_int16("refbonus", utc.reflex_bonus)
    root.set_int16("willbonus", utc.willpower_bonus)
    root.set_int16("fortbonus", utc.fortitude_bonus)

    root.set_uint8("Str", utc.strength)
    root.set_uint8("Dex", utc.dexterity)
    root.set_uint8("Con", utc.constitution)
    root.set_uint8("Int", utc.intelligence)
    root.set_uint8("Wis", utc.wisdom)
    root.set_uint8("Cha", utc.charisma)

    root.set_int16("CurrentHitPoints", utc.current_hp)
    root.set_int16("MaxHitPoints", utc.max_hp)
    root.set_int16("HitPoints", utc.hp)
    root.set_int16("CurrentForce", utc.fp)
    root.set_int16("ForcePoints", utc.max_fp)

    root.set_resref("ScriptEndDialogu", utc.on_end_dialog)
    root.set_resref("ScriptOnBlocked", utc.on_blocked)
    root.set_resref("ScriptHeartbeat", utc.on_heartbeat)
    root.set_resref("ScriptOnNotice", utc.on_notice)
    root.set_resref("ScriptSpellAt", utc.on_spell)
    root.set_resref("ScriptAttacked", utc.on_attacked)
    root.set_resref("ScriptDamaged", utc.on_damaged)
    root.set_resref("ScriptDisturbed", utc.on_disturbed)
    root.set_resref("ScriptEndRound", utc.on_end_round)
    root.set_resref("ScriptDialogue", utc.on_dialog)
    root.set_resref("ScriptSpawn", utc.on_spawn)
    root.set_resref("ScriptRested", utc.on_rested)
    root.set_resref("ScriptDeath", utc.on_death)
    root.set_resref("ScriptUserDefine", utc.on_user_defined)

    root.set_uint8("PaletteID", utc.palette_id)

    skill_list: GFFList = root.set_list("SkillList", GFFList())
    skill_list.add(0).set_uint8("Rank", utc.computer_use)
    skill_list.add(0).set_uint8("Rank", utc.demolitions)
    skill_list.add(0).set_uint8("Rank", utc.stealth)
    skill_list.add(0).set_uint8("Rank", utc.awareness)
    skill_list.add(0).set_uint8("Rank", utc.persuade)
    skill_list.add(0).set_uint8("Rank", utc.repair)
    skill_list.add(0).set_uint8("Rank", utc.security)
    skill_list.add(0).set_uint8("Rank", utc.treat_injury)

    class_list: GFFList = root.set_list("ClassList", GFFList())
    for utc_class in utc.classes:
        class_struct = class_list.add(2)
        class_struct.set_int32("Class", utc_class.class_id)
        class_struct.set_int16("ClassLevel", utc_class.class_level)
        power_list: GFFList = class_struct.set_list("KnownList0", GFFList())
        for power in utc_class.powers:
            power_struct = power_list.add(3)
            power_struct.set_uint16("Spell", power)
            power_struct.set_uint8("SpellFlags", 1)
            power_struct.set_uint8("SpellMetaMagic", 0)

        def _sort_powers(power_struct: GFFStruct):
            return utc_class._original_powers_mapping.get(power_struct.get_uint16("Spell"), float("inf"))

        power_list._structs = sorted(power_list._structs, key=_sort_powers)

    feat_list: GFFList = root.set_list("FeatList", GFFList())
    for feat in utc.feats:
        feat_list.add(1).set_uint16("Feat", feat)

    # Sort utc.feats according to their original index, stored in utc._original_feat_mapping
    def _sort_feats(feat_struct: GFFStruct):
        return utc._original_feat_mapping.get(feat_struct.get_uint16("Feat"), float("inf"))
    feat_list._structs = sorted(feat_list._structs, key=_sort_feats)

    # Not sure what these are for, verified they exist in K1's 'c_drdg.utc' in data\templates.bif. Might be unused in which case this can be deleted.
    if utc._extra_unimplemented_skills:
        for val in utc._extra_unimplemented_skills:
            skill_list.add(0).set_uint8("Rank", val)

    equipment_list: GFFList = root.set_list("Equip_ItemList", GFFList())
    for slot, item in utc.equipment.items():
        equipment_struct = equipment_list.add(slot.value)
        equipment_struct.set_resref("EquippedRes", item.resref)
        if item.droppable:
            equipment_struct.set_uint8("Dropable", value=True)

    item_list: GFFList = root.set_list("ItemList", GFFList())
    for i, item in enumerate(utc.inventory):
        item_struct = item_list.add(i)
        item_struct.set_resref("InventoryRes", item.resref)
        item_struct.set_uint16("Repos_PosX", i)
        item_struct.set_uint16("Repos_Posy", 0)
        if item.droppable:
            item_struct.set_uint8("Dropable", value=True)

    if game.is_k2():
        root.set_single("BlindSpot", utc.blindspot)
        root.set_uint8("MultiplierSet", utc.multiplier_set)
        root.set_uint8("IgnoreCrePath", utc.ignore_cre_path)
        root.set_uint8("Hologram", utc.hologram)
        root.set_uint8("WillNotRender", utc.will_not_render)

    if use_deprecated:
        root.set_uint8("BodyBag", utc.bodybag_id)
        root.set_string("Deity", utc.deity)
        root.set_locstring("Description", utc.description)
        root.set_uint8("LawfulChaotic", utc.lawfulness)
        root.set_int32("Phenotype", utc.phenotype_id)
        root.set_resref("ScriptRested", utc.on_rested)
        root.set_string("Subrace", utc.subrace_name)
        root.set_list("SpecAbilityList", GFFList())
        root.set_list("TemplateList", GFFList())

    return gff


def read_utc(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTC:
    gff: GFF = read_gff(source, offset, size)
    return construct_utc(gff)


def write_utc(
    utc: UTC,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_utc(utc, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utc(
    utc: UTC,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_utc(utc, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
