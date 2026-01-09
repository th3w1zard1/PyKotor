from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.language import LocalizedString
from pykotor.common.misc import Game, ResRef
from pykotor.resource.formats.gff import GFF, GFFContent, write_gff
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.formats.gff.gff_data import GFFStruct
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class UTD:
    """Stores door data.

    UTD files are GFF-based format files that store door definitions including
    lock/unlock mechanics, HP, scripts, and appearance.

    References:
    ----------
        KotOR I (swkotor.exe):
            - 0x0058a1f0 - CSWSDoor::LoadDoor (4556 bytes, 499 lines)
                - Main UTD GFF parser entry point
                - Loads all door fields from GFF structure
                - Function signature: LoadDoor(CSWSDoor* this, CResGFF* param_1, CResStruct* param_2, int param_3)
                - Called from LoadDoorExternal (0x0058c5f0) and LoadFromTemplate (0x0058b3d0)
            - 0x0050a0e0 - CSWSArea::LoadDoors
                - Loads doors from area GIT file
            - 0x0058b3d0 - CSWSDoor::LoadFromTemplate
                - Loads door template from ResRef
                - Calls LoadDoor after loading GFF
        
        KotOR II / TSL (swkotor2.exe):
            - Functionally equivalent UTD parsing logic
            - Same GFF field structure and parsing behavior
            - String references at different addresses due to binary layout differences
        
        GFF Field Structure (from LoadDoor analysis):
            - Root struct fields:
                - "Appearance" (DWORD) - Door appearance type identifier
                - "GenericType" (BYTE) - Generic door type
                - "OpenState" (BYTE) - Initial open state (0=closed, 1=opened, 2=locked, 3=unlocked)
                - "AutoRemoveKey" (BYTE) - Whether key is auto-removed after use
                - "Bearing" (FLOAT) - Door bearing/rotation
                - "Faction" (DWORD) - Faction identifier
                - "Fort" (BYTE) - Fortitude save
                - "Will" (BYTE) - Will save
                - "Ref" (BYTE) - Reflex save
                - "HP" (SHORT) - Hit points
                - "CurrentHP" (SHORT) - Current hit points
                - "Invulnerable" (BYTE) - Whether door is invulnerable
                - "Plot" (BYTE) - Whether door is plot-critical
                - "Static" (BYTE) - Whether door is static
                - "Min1HP" (BYTE) - Whether door has minimum 1 HP
                - "KeyName" (CExoString) - Key name/ResRef
                - "KeyRequired" (BYTE) - Whether key is required
                - "OpenLockDC" (BYTE) - Open lock difficulty class
                - "CloseLockDC" (BYTE) - Close lock difficulty class
                - "SecretDoorDC" (BYTE) - Secret door detection difficulty class
                - "Tag" (CExoString) - Door tag identifier
                - "Conversation" (CResRef) - Conversation dialog ResRef
                - "PortraitId" (WORD) - Portrait ID (0xffff = use Portrait ResRef)
                - "Portrait" (CResRef) - Portrait resource reference (if PortraitId == 0xffff)
                - "Hardness" (BYTE) - Hardness value
                - "LocName" (CExoLocString) - Localized door name
                - "Description" (CExoLocString) - Door description
                - Script fields:
                    - "OnClosed" (CResRef) - Script executed when door closes
                    - "OnDamaged" (CResRef) - Script executed when door is damaged
                    - "OnDeath" (CResRef) - Script executed when door is destroyed
                    - "OnDisarm" (CResRef) - Script executed when trap is disarmed
                    - "OnHeartbeat" (CResRef) - Script executed on heartbeat
        
        Note: UTD files are GFF format files with specific structure definitions (GFFContent.UTD)

    Derivations and Other Implementations:
    ----------
        https://github.com/th3w1zard1/Kotor.NET/tree/master/Kotor.NET/Resources/KotorUTD/UTD.cs:11-68 (UTD class definition)
        https://github.com/th3w1zard1/KotOR.js/tree/master/src/module/ModuleDoor.ts:55-167 (Door module object)

    Attributes:
    ----------
        resref: "TemplateResRef" field. The resource reference for this door template.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:59 (TemplateResRef property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:144 (templateResRef field)

        tag: "Tag" field. Tag identifier for this door.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:58 (Tag property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:143 (tag field)

        name: "LocName" field. Localized name of the door.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:33 (LocName property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:133 (locName field)

        auto_remove_key: "AutoRemoveKey" field. Whether key is removed after use.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:15 (AutoRemoveKey property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:120 (autoRemoveKey field)

        conversation: "Conversation" field. ResRef to dialog file for this door.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:18 (Conversation property)

        faction_id: "Faction" field. Faction identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:22 (Faction property)

        plot: "Plot" field. Whether door is plot-critical.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:54 (Plot property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:139 (plot field)

        min1_hp: "Min1HP" field. Whether door HP cannot go below 1. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:34 (Min1HP property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:136 (min1HP field)

        key_required: "KeyRequired" field. Whether a key is required to unlock.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:29 (KeyRequired property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:131 (keyRequired field)

        lockable: "Lockable" field. Whether door can be locked.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:31 (Lockable property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:134 (lockable field)

        locked: "Locked" field. Whether door is currently locked.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:32 (Locked property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:135 (locked field)

        unlock_dc: "OpenLockDC" field. Difficulty class to unlock door.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:49 (OpenLockDC property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:137 (openLockDC field)

        key_name: "KeyName" field. Tag of the key item required.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:28 (KeyName property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:130 (keyName field)

        animation_state: "AnimationState" field. Current animation state. Always 0 in files.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:13 (AnimationState property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:118 (animationState field)
            Note: This field is always 0 in files (verified against engine binaries)

        maximum_hp: "HP" field. Maximum hit points.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:26 (HP property)

        current_hp: "CurrentHP" field. Current hit points.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:19 (CurrentHP property)

        hardness: "Hardness" field. Damage reduction value.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:25 (Hardness property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:128 (hardness field)

        fortitude: "Fort" field. Fortitude save value. Always 0 in files.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:23 (Fort property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:125 (fort field)

        appearance_id: "GenericType" field. Door appearance type identifier.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:24 (GenericType property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:126 (genericType field)

        static: "Static" field. Whether door is static (non-interactive).
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:57 (Static property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:142 (static field)

        on_closed: "OnClosed" field. Script to run when door closes. Always empty in files.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:36 (OnClosed property)
            Note: Verified against engine binaries

        on_damaged: "OnDamaged" field. Script to run when door is damaged. Always empty in files.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:37 (OnDamaged property)
            Note: Verified against engine binaries

        on_death: "OnDeath" field. Script to run when door is destroyed.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:38 (OnDeath property)

        on_heartbeat: "OnHeartbeat" field. Script to run on heartbeat.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:41 (OnHeartbeat property)

        on_lock: "OnLock" field. Script to run when door is locked. Always empty in files.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:42 (OnLock property)
            Note: Verified against engine binaries

        on_melee: "OnMeleeAttacked" field. Script to run when door is melee attacked. Always empty in files.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:43 (OnMeleeAttacked property)
            Note: Verified against engine binaries

        on_open: "OnOpen" field. Script to run when door opens.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:44 (OnOpen property)

        on_unlock: "OnUnlock" field. Script to run when door is unlocked. Always empty in files.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:47 (OnUnlock property)
            Note: Verified against engine binaries

        on_user_defined: "OnUserDefined" field. Script to run on user-defined event.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:48 (OnUserDefined property)

        on_click: "OnClick" field. Script to run when door is clicked.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:35 (OnClick property)

        on_open_failed: "OnFailToOpen" field. Script to run when door fails to open. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:40 (OnFailToOpen property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:390 (used in unlock failure handling)

        comment: "Comment" field. Developer comment. Used in toolset only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:17 (Comment property)
            Note: Verified against engine binaries

        unlock_diff: "OpenLockDiff" field. Unlock difficulty modifier. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:50 (OpenLockDiff property)
            Reference: NorthernLights/AuroraUTD.cs:65 (OpenLockDiff field)

        unlock_diff_mod: "OpenLockDiffMod" field. Additional unlock difficulty modifier. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:51 (OpenLockDiffMod property as sbyte)
            Reference: NorthernLights/AuroraUTD.cs:66 (OpenLockDiffMod field as Char)
            Note: Type discrepancy - reone uses char/int, Kotor.NET uses sbyte, PyKotor uses int

        open_state: "OpenState" field. Current open state (closed/open1/open2). KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:52 (OpenState property)
            Reference: NorthernLights/AuroraUTD.cs:67 (OpenState field)
            Reference: sotor/src/save/read.rs:488 (OpenState in save games)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:56 (openState field)

        not_blastable: "NotBlastable" field. Whether door cannot be blasted. KotOR 2 Only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:67 (NotBlastable property)
            Reference: NorthernLights/AuroraUTD.cs:64 (NotBlastable field)

        palette_id: "PaletteID" field. Palette identifier. Used in toolset only.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:53 (PaletteID property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:138 (paletteID field)
            Note: Verified against engine binaries

        description: "Description" field. Localized description. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:20 (Description property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:123 (description field)
            Note: Verified against engine binaries

        lock_dc: "CloseLockDC" field. Difficulty class to lock door. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:16 (CloseLockDC property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:121 (closeLockDC field)
            Note: Verified against engine binaries

        interruptable: "Interruptable" field. Whether door can be interrupted. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:27 (Interruptable property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:129 (interruptable field)
            Note: Verified against engine binaries

        portrait_id: "PortraitId" field. Portrait identifier. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:55 (PortraitId property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:140 (portraitId field)
            Note: Verified against engine binaries

        trap_detectable: "TrapDetectable" field. Whether trap is detectable. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:60 (TrapDetectable property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:146 (trapDetectable field)
            Note: Verified against engine binaries

        trap_detect_dc: "TrapDetectDC" field. Difficulty class to detect trap. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:61 (TrapDetectDC property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:145 (trapDetectDC field)
            Note: Verified against engine binaries

        trap_disarmable: "TrapDisarmable" field. Whether trap is disarmable. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:62 (TrapDisarmable property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:147 (trapDisarmable field)
            Note: Verified against engine binaries

        trap_disarm_dc: "DisarmDC" field. Difficulty class to disarm trap. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:21 (DisarmDC property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:124 (disarmDC field)
            Note: Verified against engine binaries

        trap_flag: "TrapFlag" field. Whether door has a trap. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:63 (TrapFlag property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:148 (trapFlag field)
            Note: Verified against engine binaries

        trap_one_shot: "TrapOneShot" field. Whether trap fires once. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:64 (TrapOneShot property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:149 (trapOneShot field)
            Note: Verified against engine binaries

        trap_type: "TrapType" field. Type of trap. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:65 (TrapType property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:150 (trapType field)
            Note: Verified against engine binaries

        unused_appearance: "Appearance" field. Appearance identifier. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:14 (Appearance property)
            Note: Verified against engine binaries

        reflex: "Ref" field. Reflex save value. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:56 (Ref property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:141 (ref field)
            Note: Verified against engine binaries

        willpower: "Will" field. Will save value. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:66 (Will property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:151 (will field)
            Note: Verified against engine binaries

        on_disarm: "OnDisarm" field. Script to run when trap is disarmed. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:39 (OnDisarm property)
            Note: Verified against engine binaries

        on_power: "OnSpellCastAt" field. Script to run when spell is cast at door. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:45 (OnSpellCastAt property)
            Note: Verified against engine binaries

        on_trap_triggered: "OnTrapTriggered" field. Script to run when trap triggers. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:46 (OnTrapTriggered property)
            Note: Verified against engine binaries

        loadscreen_id: "LoadScreenID" field. Load screen identifier. Not used by the game engine.
            Reference: https://github.com/th3w1zard1/Kotor.NET/tree/master/UTD.cs:30 (LoadScreenID property)
            Reference: https://github.com/th3w1zard1/KotOR.js/tree/master/ModuleDoor.ts:132 (loadScreenID field)
            Note: Verified against engine binaries
    """

    BINARY_TYPE = ResourceType.UTD

    def __init__(  # noqa: PLR0915
        self,
    ):
        self.resref: ResRef = ResRef.from_blank()
        self.conversation: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.comment: str = ""

        self.name: LocalizedString = LocalizedString.from_invalid()

        self.faction_id: int = 0
        self.appearance_id: int = 0
        self.animation_state: int = 0

        self.auto_remove_key: bool = False
        self.key_name: str = ""
        self.key_required: bool = False
        self.lockable: bool = False
        self.locked: bool = False

        self.unlock_dc: int = 0
        self.unlock_diff: int = 0  # KotOR 2 Only
        self.unlock_diff_mod: int = 0  # KotOR 2 Only
        self.open_state: int = 0  # KotOR 2 Only

        self.min1_hp: bool = False  # KotOR 2 Only
        self.not_blastable: bool = False  # KotOR 2 Only
        self.plot: bool = False
        self.static: bool = False

        self.current_hp: int = 0
        self.maximum_hp: int = 0
        self.fortitude: int = 0
        self.hardness: int = 0

        self.on_click: ResRef = ResRef.from_blank()
        self.on_damaged: ResRef = ResRef.from_blank()
        self.on_death: ResRef = ResRef.from_blank()
        self.on_open_failed: ResRef = ResRef.from_blank()
        self.on_heartbeat: ResRef = ResRef.from_blank()
        self.on_melee: ResRef = ResRef.from_blank()
        self.on_open: ResRef = ResRef.from_blank()
        self.on_user_defined: ResRef = ResRef.from_blank()
        self.on_unlock: ResRef = ResRef.from_blank()
        self.on_lock: ResRef = ResRef.from_blank()
        self.on_closed: ResRef = ResRef.from_blank()

        self.palette_id: int = 0

        # Deprecated:
        self.description: LocalizedString = LocalizedString.from_invalid()
        self.lock_dc: int = 0
        self.interruptable: bool = False
        self.portrait_id: int = 0
        self.trap_detectable: bool = False
        self.trap_disarmable: bool = False
        self.trap_detect_dc: int = 0
        self.trap_disarm_dc: int = 0
        self.trap_type: int = 0
        self.trap_one_shot: bool = True
        self.trap_flag: int = 0
        self.unused_appearance: int = 0
        self.reflex: int = 0
        self.willpower: int = 0
        self.on_disarm: ResRef = ResRef.from_blank()
        self.on_power: ResRef = ResRef.from_blank()
        self.on_trap_triggered: ResRef = ResRef.from_blank()
        self.loadscreen_id: int = 0


def utd_version(
    gff: GFF,
) -> Game:
    return next(
        (
            Game.K2
            for label in (
                "NotBlastable",
                "OpenLockDiff",
                "OpenLockDiffMod",
                "OpenState",
            )
            if gff.root.exists(label)
        ),
        Game.K1,
    )


def construct_utd(
    gff: GFF,
) -> UTD:
    utd = UTD()

    root = gff.root
    utd.tag = root.acquire("Tag", "")
    utd.name = root.acquire("LocName", LocalizedString.from_invalid())
    utd.resref = root.acquire("TemplateResRef", ResRef.from_blank())
    utd.auto_remove_key = bool(root.acquire("AutoRemoveKey", 0))
    utd.conversation = root.acquire("Conversation", ResRef.from_blank())
    utd.faction_id = root.acquire("Faction", 0)
    utd.plot = bool(root.acquire("Plot", 0))
    utd.min1_hp = bool(root.acquire("Min1HP", 0))
    utd.key_required = bool(root.acquire("KeyRequired", 0))
    utd.lockable = bool(root.acquire("Lockable", 0))
    utd.locked = bool(root.acquire("Locked", 0))
    utd.unlock_dc = root.acquire("OpenLockDC", 0)
    utd.key_name = root.acquire("KeyName", "")
    utd.animation_state = root.acquire("AnimationState", 0)
    utd.maximum_hp = root.acquire("HP", 0)
    utd.current_hp = root.acquire("CurrentHP", 0)
    utd.hardness = root.acquire("Hardness", 0)
    utd.fortitude = root.acquire("Fort", 0)
    utd.on_closed = root.acquire("OnClosed", ResRef.from_blank())
    utd.on_damaged = root.acquire("OnDamaged", ResRef.from_blank())
    utd.on_death = root.acquire("OnDeath", ResRef.from_blank())
    utd.on_heartbeat = root.acquire("OnHeartbeat", ResRef.from_blank())
    utd.on_lock = root.acquire("OnLock", ResRef.from_blank())
    utd.on_melee = root.acquire("OnMeleeAttacked", ResRef.from_blank())
    utd.on_open = root.acquire("OnOpen", ResRef.from_blank())
    utd.on_unlock = root.acquire("OnUnlock", ResRef.from_blank())
    utd.on_user_defined = root.acquire("OnUserDefined", ResRef.from_blank())
    utd.appearance_id = root.acquire("GenericType", 0)
    utd.static = bool(root.acquire("Static", 0))
    utd.open_state = root.acquire("OpenState", 0)
    utd.on_click = root.acquire("OnClick", ResRef.from_blank())
    utd.on_open_failed = root.acquire("OnFailToOpen", ResRef.from_blank())
    utd.comment = root.acquire("Comment", "")
    utd.unlock_diff = root.acquire("OpenLockDiff", 0)
    utd.unlock_diff_mod = root.acquire("OpenLockDiffMod", 0)
    utd.description = root.acquire("Description", LocalizedString.from_invalid())
    utd.lock_dc = root.acquire("CloseLockDC", 0)
    utd.interruptable = bool(root.acquire("Interruptable", 0))
    utd.portrait_id = root.acquire("PortraitId", 0)
    utd.trap_detectable = bool(root.acquire("TrapDetectable", 0))
    utd.trap_detect_dc = root.acquire("TrapDetectDC", 0)
    utd.trap_disarmable = bool(root.acquire("TrapDisarmable", 0))
    utd.trap_disarm_dc = root.acquire("DisarmDC", 0)
    utd.trap_flag = root.acquire("TrapFlag", 0)
    utd.trap_one_shot = bool(root.acquire("TrapOneShot", 0))
    utd.trap_type = root.acquire("TrapType", 0)
    utd.unused_appearance = root.acquire("Appearance", 0)
    utd.reflex = root.acquire("Ref", 0)
    utd.willpower = root.acquire("Will", 0)
    utd.on_disarm = root.acquire("OnDisarm", ResRef.from_blank())
    utd.on_power = root.acquire("OnSpellCastAt", ResRef.from_blank())
    utd.on_trap_triggered = root.acquire("OnTrapTriggered", ResRef.from_blank())
    utd.loadscreen_id = root.acquire("LoadScreenID", 0)
    utd.palette_id = root.acquire("PaletteID", 0)
    utd.not_blastable = bool(root.acquire("NotBlastable", 0))

    return utd


def dismantle_utd(
    utd: UTD,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.UTD)

    root: GFFStruct = gff.root
    root.set_string("Tag", utd.tag)
    root.set_locstring("LocName", utd.name)
    root.set_resref("TemplateResRef", utd.resref)
    root.set_uint8("AutoRemoveKey", utd.auto_remove_key)
    root.set_resref("Conversation", utd.conversation)
    root.set_uint32("Faction", utd.faction_id)
    root.set_uint8("Plot", utd.plot)
    root.set_uint8("Min1HP", utd.min1_hp)
    root.set_uint8("KeyRequired", utd.key_required)
    root.set_uint8("Lockable", utd.lockable)
    root.set_uint8("Locked", utd.locked)
    root.set_uint8("OpenLockDC", utd.unlock_dc)
    root.set_string("KeyName", utd.key_name)
    root.set_uint8("AnimationState", utd.animation_state)
    root.set_int16("HP", utd.maximum_hp)
    root.set_int16("CurrentHP", utd.current_hp)
    root.set_uint8("Hardness", utd.hardness)
    root.set_uint8("Fort", utd.fortitude)
    root.set_resref("OnClosed", utd.on_closed)
    root.set_resref("OnDamaged", utd.on_damaged)
    root.set_resref("OnDeath", utd.on_death)
    root.set_resref("OnHeartbeat", utd.on_heartbeat)
    root.set_resref("OnLock", utd.on_lock)
    root.set_resref("OnMeleeAttacked", utd.on_melee)
    root.set_resref("OnOpen", utd.on_open)
    root.set_resref("OnUnlock", utd.on_unlock)
    root.set_resref("OnUserDefined", utd.on_user_defined)
    root.set_uint8("GenericType", utd.appearance_id)
    root.set_uint8("Static", utd.static)
    root.set_resref("OnClick", utd.on_click)
    root.set_resref("OnFailToOpen", utd.on_open_failed)
    root.set_string("Comment", utd.comment)

    if game.is_k2():
        root.set_uint8("OpenLockDiff", utd.unlock_diff)
        root.set_int8("OpenLockDiffMod", utd.unlock_diff_mod)
        root.set_uint8("OpenState", utd.open_state)
        root.set_uint8("NotBlastable", utd.not_blastable)

    if use_deprecated:
        root.set_locstring("Description", utd.description)
        root.set_uint8("CloseLockDC", utd.lock_dc)
        root.set_uint8("Interruptable", utd.interruptable)
        root.set_uint16("PortraitId", utd.portrait_id)
        root.set_uint8("TrapDetectable", utd.trap_detectable)
        root.set_uint8("TrapDetectDC", utd.trap_detect_dc)
        root.set_uint8("TrapDisarmable", utd.trap_disarmable)
        root.set_uint8("DisarmDC", utd.trap_disarm_dc)
        root.set_uint8("TrapFlag", utd.trap_flag)
        root.set_uint8("TrapOneShot", utd.trap_one_shot)
        root.set_uint8("TrapType", utd.trap_type)
        root.set_uint32("Appearance", utd.unused_appearance)
        root.set_uint8("Ref", utd.reflex)
        root.set_uint8("Will", utd.willpower)
        root.set_resref("OnDisarm", utd.on_disarm)
        root.set_resref("OnSpellCastAt", utd.on_power)
        root.set_resref("OnTrapTriggered", utd.on_trap_triggered)
        root.set_uint16("LoadScreenID", utd.loadscreen_id)
        root.set_uint8("PaletteID", utd.palette_id)

    return gff


def read_utd(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> UTD:
    gff: GFF = read_gff(source, offset, size)
    return construct_utd(gff)


def write_utd(
    utd: UTD,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff: GFF = dismantle_utd(utd, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_utd(
    utd: UTD,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff: GFF = dismantle_utd(utd, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
