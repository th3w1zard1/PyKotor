# KotOR NSS files format Documentation

NSS (NWScript Source) files contain human-readable NWScript source code that compiles to [NCS bytecode](NCS-File-Format). The `nwscript.nss` file defines all engine-exposed functions and constants available to scripts. KotOR 1 and KotOR 2 each have their own `nwscript.nss` with game-specific functions and constants.

**Implementation:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/`](https://github.com/th3w1zard1/PyKotor/tree/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/)

**Vendor Script Compilers:**

- [`vendor/xoreos-tools/src/nwscript/`](https://github.com/th3w1zard1/xoreos-tools/tree/master/src/nwscript) - NWScript compiler and decompiler
- [`vendor/KotOR-Scripting-Tool/`](https://github.com/th3w1zard1/KotOR-Scripting-Tool) - Visual NWScript IDE with integrated compiler
- [`vendor/HoloLSP/`](https://github.com/th3w1zard1/HoloLSP) - Language Server Protocol implementation for NWScript
- [`vendor/nwscript-mode.el/`](https://github.com/th3w1zard1/nwscript-mode.el) - Emacs major mode for NWScript editing

**Vendor Script Implementations:**

- [`vendor/xoreos/src/engines/nwscript/`](https://github.com/th3w1zard1/xoreos/tree/master/src/engines/nwscript) - Complete NWScript virtual machine implementation
- [`vendor/reone/src/libs/script/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script) - Script execution engine
- [`vendor/KotOR.js/src/nwscript/`](https://github.com/th3w1zard1/KotOR.js/tree/master/src/nwscript) - TypeScript NWScript interpreter
- [`vendor/Vanilla_KOTOR_Script_Source/`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source) - Decompiled vanilla KotOR scripts for reference

**See Also:**

- [NCS File Format](NCS-File-Format) - Compiled NWScript bytecode format
- [NSS Shared Functions - Actions](NSS-Shared-Functions-Actions) - Action functions documentation
- [NSS Shared Constants](NSS-Shared-Constants-Object-Type-Constants) - Script constants reference
- [GFF-DLG](GFF-DLG) - [dialogue files](GFF-File-Format) that trigger [NCS](NCS-File-Format) scripts
- [2DA Files](2DA-File-Format) - Game data tables referenced by scripts

## Table of Contents

<!-- TOC_START -->
- [KotOR NSS File Format Documentation](#kotor-nss-files-format-documentation)
  - Table of Contents
  - [PyKotor Implementation](#pykotor-implementation)
    - [Compilation Integration](#compilation-integration)
    - [Data Structures](#data-structures)
  - [Shared Functions (K1 \& TSL)](#shared-functions-k1--tsl)
    - [Abilities and Stats](#abilities-and-stats)
      - [`GetAbilityModifier(nAbility, oCreature)` - Routine 331](NSS-Shared-Functions-Abilities-and-Stats)
      - [`GetAbilityScore(oCreature, nAbilityType)` - Routine 139](NSS-Shared-Functions-Abilities-and-Stats)
      - [`GetNPCSelectability(nNPC)` - Routine 709](NSS-Shared-Functions-Abilities-and-Stats)
      - [`SetNPCSelectability(nNPC, nSelectability)` - Routine 708](NSS-Shared-Functions-Abilities-and-Stats)
      - [`SWMG_StartInvulnerability(oFollower)` - Routine 666](NSS-Shared-Functions-Abilities-and-Stats)
    - [Actions](#actions)
      - [`ActionAttack(oAttackee, bPassive)` - Routine 37](NSS-Shared-Functions-Actions)
      - [`ActionBarkString(strRef)` - Routine 700](NSS-Shared-Functions-Actions)
      - [`ActionCastFakeSpellAtLocation(nSpell, lTarget, nProjectilePathType)` - Routine 502](NSS-Shared-Functions-Actions)
      - [`ActionCastFakeSpellAtObject(nSpell, oTarget, nProjectilePathType)` - Routine 501](NSS-Shared-Functions-Actions)
      - [`ActionCastSpellAtLocation(nSpell, lTargetLocation, nMetaMagic, bCheat, nProjectilePathType, bInstantSpell)` - Routine 234](NSS-Shared-Functions-Actions)
      - [`ActionCastSpellAtObject(nSpell, oTarget, nMetaMagic, bCheat, nDomainLevel, nProjectilePathType, bInstantSpell)` - Routine 48](NSS-Shared-Functions-Actions)
      - [`ActionCloseDoor(oDoor)` - Routine 44](NSS-Shared-Functions-Actions)
      - [`ActionDoCommand(aActionToDo)` - Routine 294](NSS-Shared-Functions-Actions)
      - [`ActionEquipItem(oItem, nInventorySlot, bInstant)` - Routine 32](NSS-Shared-Functions-Actions)
      - [`ActionEquipMostDamagingMelee(oVersus, bOffHand)` - Routine 399](NSS-Shared-Functions-Actions)
      - [`ActionEquipMostDamagingRanged(oVersus)` - Routine 400](NSS-Shared-Functions-Actions)
      - [`ActionFollowLeader()` - Routine 730](NSS-Shared-Functions-Actions)
      - [`ActionForceFollowObject(oFollow, fFollowDistance)` - Routine 167](NSS-Shared-Functions-Actions)
      - [`ActionForceMoveToLocation(lDestination, bRun, fTimeout)` - Routine 382](NSS-Shared-Functions-Actions)
      - [`ActionForceMoveToObject(oMoveTo, bRun, fRange, fTimeout)` - Routine 383](NSS-Shared-Functions-Actions)
      - [`ActionGiveItem(oItem, oGiveTo)` - Routine 135](NSS-Shared-Functions-Actions)
      - [`ActionInteractObject(oPlaceable)` - Routine 329](NSS-Shared-Functions-Actions)
      - [`ActionJumpToLocation(lLocation)` - Routine 214](NSS-Shared-Functions-Actions)
      - [`ActionJumpToObject(oToJumpTo, bWalkStraightLineToPoint)` - Routine 196](NSS-Shared-Functions-Actions)
      - [`ActionLockObject(oTarget)` - Routine 484](NSS-Shared-Functions-Actions)
      - [`ActionMoveAwayFromLocation(lMoveAwayFrom, bRun, fMoveAwayRange)` - Routine 360](NSS-Shared-Functions-Actions)
      - [`ActionMoveAwayFromObject(oFleeFrom, bRun, fMoveAwayRange)` - Routine 23](NSS-Shared-Functions-Actions)
      - [`ActionMoveToLocation(lDestination, bRun)` - Routine 21](NSS-Shared-Functions-Actions)
      - [`ActionMoveToObject(oMoveTo, bRun, fRange)` - Routine 22](NSS-Shared-Functions-Actions)
      - [`ActionOpenDoor(oDoor)` - Routine 43](NSS-Shared-Functions-Actions)
      - [`ActionPauseConversation()` - Routine 205](NSS-Shared-Functions-Actions)
      - [`ActionPickUpItem(oItem)` - Routine 34](NSS-Shared-Functions-Actions)
      - [`ActionPlayAnimation(nAnimation, fSpeed, fDurationSeconds)` - Routine 40](NSS-Shared-Functions-Actions)
      - [`ActionPutDownItem(oItem)` - Routine 35](NSS-Shared-Functions-Actions)
      - [`ActionRandomWalk()` - Routine 20](NSS-Shared-Functions-Actions)
      - [`ActionResumeConversation()` - Routine 206](NSS-Shared-Functions-Actions)
      - [`ActionSpeakString(sStringToSpeak, nTalkVolume)` - Routine 39](NSS-Shared-Functions-Actions)
      - [`ActionSpeakStringByStrRef(nStrRef, nTalkVolume)` - Routine 240](NSS-Shared-Functions-Actions)
      - [`ActionStartConversation(oObjectToConverse, sDialogResRef, bPrivateConversation, nConversationType, bIgnoreStartRange, sNameObjectToIgnore1, sNameObjectToIgnore2, sNameObjectToIgnore3, sNameObjectToIgnore4, sNameObjectToIgnore5, sNameObjectToIgnore6, bUseLeader)` - Routine 204](NSS-Shared-Functions-Actions)
      - [`ActionSurrenderToEnemies()` - Routine 379](NSS-Shared-Functions-Actions)
      - [`ActionTakeItem(oItem, oTakeFrom)` - Routine 136](NSS-Shared-Functions-Actions)
      - [`ActionUnequipItem(oItem, bInstant)` - Routine 33](NSS-Shared-Functions-Actions)
      - [`ActionUnlockObject(oTarget)` - Routine 483](NSS-Shared-Functions-Actions)
      - [`ActionUseFeat(nFeat, oTarget)` - Routine 287](NSS-Shared-Functions-Actions)
      - [`ActionUseSkill(nSkill, oTarget, nSubSkill, oItemUsed)` - Routine 288](NSS-Shared-Functions-Actions)
      - [`ActionUseTalentAtLocation(tChosenTalent, lTargetLocation)` - Routine 310](NSS-Shared-Functions-Actions)
      - [`ActionUseTalentOnObject(tChosenTalent, oTarget)` - Routine 309](NSS-Shared-Functions-Actions)
      - [`ActionWait(fSeconds)` - Routine 202](NSS-Shared-Functions-Actions)
    - [Alignment System](#alignment-system)
      - [`AdjustAlignment(oSubject, nAlignment, nShift)` - Routine 201](NSS-Shared-Functions-Alignment-System)
      - [`GetAlignmentGoodEvil(oCreature)` - Routine 127](NSS-Shared-Functions-Alignment-System)
      - [`GetFactionAverageGoodEvilAlignment(oFactionMember)` - Routine 187](NSS-Shared-Functions-Alignment-System)
      - [`VersusAlignmentEffect(eEffect, nLawChaos, nGoodEvil)` - Routine 355](NSS-Shared-Functions-Alignment-System)
    - [Class System](#class-system)
      - [`AddMultiClass(nClassType, oSource)` - Routine 389](NSS-Shared-Functions-Class-System)
      - [`GetClassByPosition(nClassPosition, oCreature)` - Routine 341](NSS-Shared-Functions-Class-System)
      - [`GetFactionMostFrequentClass(oFactionMember)` - Routine 191](NSS-Shared-Functions-Class-System)
      - [`GetLevelByClass(nClassType, oCreature)` - Routine 343](NSS-Shared-Functions-Class-System)
    - [Combat Functions](#combat-functions)
      - [`CancelCombat(oidCreature)` - Routine 54](NSS-Shared-Functions-Combat-Functions)
      - [`CutsceneAttack(oTarget, nAnimation, nAttackResult, nDamage)` - Routine 503](NSS-Shared-Functions-Combat-Functions)
      - [`GetAttackTarget(oCreature)` - Routine 316](NSS-Shared-Functions-Combat-Functions)
      - [`GetAttemptedAttackTarget()` - Routine 361](NSS-Shared-Functions-Combat-Functions)
      - [`GetFirstAttacker(oCreature)` - Routine 727](NSS-Shared-Functions-Combat-Functions)
      - [`GetGoingToBeAttackedBy(oTarget)` - Routine 211](NSS-Shared-Functions-Combat-Functions)
      - [`GetIsInCombat(oCreature)` - Routine 320](NSS-Shared-Functions-Combat-Functions)
      - [`GetLastAttackAction(oAttacker)` - Routine 722](NSS-Shared-Functions-Combat-Functions)
      - [`GetLastAttacker(oAttackee)` - Routine 36](NSS-Shared-Functions-Combat-Functions)
      - [`GetLastAttackMode(oCreature)` - Routine 318](NSS-Shared-Functions-Combat-Functions)
      - [`GetLastAttackResult(oAttacker)` - Routine 725](NSS-Shared-Functions-Combat-Functions)
      - [`GetLastAttackType(oCreature)` - Routine 317](NSS-Shared-Functions-Combat-Functions)
      - [`GetLastKiller()` - Routine 437](NSS-Shared-Functions-Combat-Functions)
      - [`GetNextAttacker(oCreature)` - Routine 728](NSS-Shared-Functions-Combat-Functions)
    - [Dialog and Conversation Functions](#dialog-and-conversation-functions)
      - [`BarkString(oCreature, strRef)` - Routine 671](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`BeginConversation(sResRef, oObjectToDialog)` - Routine 255](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`CancelPostDialogCharacterSwitch()` - Routine 757](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`EventConversation()` - Routine 295](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`GetIsConversationActive()` - Routine 701](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`GetIsInConversation(oObject)` - Routine 445](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`GetLastConversation()` - Routine 711](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`GetLastSpeaker()` - Routine 254](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`HoldWorldFadeInForDialog()` - Routine 760](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`ResetDialogState()` - Routine 749](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`SetDialogPlaceableCamera(nCameraId)` - Routine 461](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`SetLockHeadFollowInDialog(oObject, nValue)` - Routine 506](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`SetLockOrientationInDialog(oObject, nValue)` - Routine 505](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`SpeakOneLinerConversation(sDialogResRef, oTokenTarget)` - Routine 417](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
      - [`SpeakString(sStringToSpeak, nTalkVolume)` - Routine 221](NSS-Shared-Functions-Dialog-and-Conversation-Functions)
    - [Effects System](#effects-system)
      - [`ActionEquipMostEffectiveArmor()` - Routine 404](NSS-Shared-Functions-Effects-System)
      - [`DisableVideoEffect()` - Routine 508](NSS-Shared-Functions-Effects-System)
      - [`EffectAbilityDecrease(nAbility, nModifyBy)` - Routine 446](NSS-Shared-Functions-Effects-System)
      - [`EffectAbilityIncrease(nAbilityToIncrease, nModifyBy)` - Routine 80](NSS-Shared-Functions-Effects-System)
      - [`EffectACDecrease(nValue, nModifyType, nDamageType)` - Routine 450](NSS-Shared-Functions-Effects-System)
      - [`EffectACIncrease(nValue, nModifyType, nDamageType)` - Routine 115](NSS-Shared-Functions-Effects-System)
      - [`EffectAreaOfEffect(nAreaEffectId, sOnEnterScript, sHeartbeatScript, sOnExitScript)` - Routine 171](NSS-Shared-Functions-Effects-System)
      - [`EffectAssuredDeflection(nReturn)` - Routine 252](NSS-Shared-Functions-Effects-System)
      - [`EffectAssuredHit()` - Routine 51](NSS-Shared-Functions-Effects-System)
      - [`EffectAttackDecrease(nPenalty, nModifierType)` - Routine 447](NSS-Shared-Functions-Effects-System)
      - [`EffectAttackIncrease(nBonus, nModifierType)` - Routine 118](NSS-Shared-Functions-Effects-System)
      - [`EffectBeam(nBeamVisualEffect, oEffector, nBodyPart, bMissEffect)` - Routine 207](NSS-Shared-Functions-Effects-System)
      - [`EffectBlasterDeflectionDecrease(nChange)` - Routine 470](NSS-Shared-Functions-Effects-System)
      - [`EffectBlasterDeflectionIncrease(nChange)` - Routine 469](NSS-Shared-Functions-Effects-System)
      - [`EffectBodyFuel()` - Routine 224](NSS-Shared-Functions-Effects-System)
      - [`EffectChoke()` - Routine 159](NSS-Shared-Functions-Effects-System)
      - [`EffectConcealment(nPercentage)` - Routine 458](NSS-Shared-Functions-Effects-System)
      - [`EffectConfused()` - Routine 157](NSS-Shared-Functions-Effects-System)
      - [`EffectCutSceneHorrified()` - Routine 754](NSS-Shared-Functions-Effects-System)
      - [`EffectCutSceneParalyze()` - Routine 755](NSS-Shared-Functions-Effects-System)
      - [`EffectCutSceneStunned()` - Routine 756](NSS-Shared-Functions-Effects-System)
      - [`EffectDamage(nDamageAmount, nDamageType, nDamagePower)` - Routine 79](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageDecrease(nPenalty, nDamageType)` - Routine 448](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageForcePoints(nDamage)` - Routine 372](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageImmunityDecrease(nDamageType, nPercentImmunity)` - Routine 449](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageImmunityIncrease(nDamageType, nPercentImmunity)` - Routine 275](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageIncrease(nBonus, nDamageType)` - Routine 120](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageReduction(nAmount, nDamagePower, nLimit)` - Routine 119](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageResistance(nDamageType, nAmount, nLimit)` - Routine 81](NSS-Shared-Functions-Effects-System)
      - [`EffectDamageShield(nDamageAmount, nRandomAmount, nDamageType)` - Routine 487](NSS-Shared-Functions-Effects-System)
      - [`EffectDeath(nSpectacularDeath, nDisplayFeedback)` - Routine 133](NSS-Shared-Functions-Effects-System)
      - [`EffectDisguise(nDisguiseAppearance)` - Routine 463](NSS-Shared-Functions-Effects-System)
      - [`EffectDispelMagicAll(nCasterLevel)` - Routine 460](NSS-Shared-Functions-Effects-System)
      - [`EffectDispelMagicBest(nCasterLevel)` - Routine 473](NSS-Shared-Functions-Effects-System)
      - [`EffectDroidStun()` - Routine 391](NSS-Shared-Functions-Effects-System)
      - [`EffectEntangle()` - Routine 130](NSS-Shared-Functions-Effects-System)
      - [`EffectForceDrain(nDamage)` - Routine 675](NSS-Shared-Functions-Effects-System)
      - [`EffectForceFizzle()` - Routine 420](NSS-Shared-Functions-Effects-System)
      - [`EffectForceJump(oTarget, nAdvanced)` - Routine 153](NSS-Shared-Functions-Effects-System)
      - [`EffectForcePushed()` - Routine 392](NSS-Shared-Functions-Effects-System)
      - [`EffectForcePushTargeted(lCentre, nIgnoreTestDirectLine)` - Routine 269](NSS-Shared-Functions-Effects-System)
      - [`EffectForceResistanceDecrease(nValue)` - Routine 454](NSS-Shared-Functions-Effects-System)
      - [`EffectForceResistanceIncrease(nValue)` - Routine 212](NSS-Shared-Functions-Effects-System)
      - [`EffectForceResisted(oSource)` - Routine 402](NSS-Shared-Functions-Effects-System)
      - [`EffectForceShield(nShield)` - Routine 459](NSS-Shared-Functions-Effects-System)
      - [`EffectFrightened()` - Routine 158](NSS-Shared-Functions-Effects-System)
      - [`EffectHaste()` - Routine 270](NSS-Shared-Functions-Effects-System)
      - [`EffectHeal(nDamageToHeal)` - Routine 78](NSS-Shared-Functions-Effects-System)
      - [`EffectHealForcePoints(nHeal)` - Routine 373](NSS-Shared-Functions-Effects-System)
      - [`EffectHitPointChangeWhenDying(fHitPointChangePerRound)` - Routine 387](NSS-Shared-Functions-Effects-System)
      - [`EffectHorrified()` - Routine 471](NSS-Shared-Functions-Effects-System)
      - [`EffectImmunity(nImmunityType)` - Routine 273](NSS-Shared-Functions-Effects-System)
      - [`EffectInvisibility(nInvisibilityType)` - Routine 457](NSS-Shared-Functions-Effects-System)
      - [`EffectKnockdown()` - Routine 134](NSS-Shared-Functions-Effects-System)
      - [`EffectLightsaberThrow(oTarget1, oTarget2, oTarget3, nAdvancedDamage)` - Routine 702](NSS-Shared-Functions-Effects-System)
      - [`EffectLinkEffects(eChildEffect, eParentEffect)` - Routine 199](NSS-Shared-Functions-Effects-System)
      - [`EffectMissChance(nPercentage)` - Routine 477](NSS-Shared-Functions-Effects-System)
      - [`EffectModifyAttacks(nAttacks)` - Routine 485](NSS-Shared-Functions-Effects-System)
      - [`EffectMovementSpeedDecrease(nPercentChange)` - Routine 451](NSS-Shared-Functions-Effects-System)
      - [`EffectMovementSpeedIncrease(nNewSpeedPercent)` - Routine 165](NSS-Shared-Functions-Effects-System)
      - [`EffectParalyze()` - Routine 148](NSS-Shared-Functions-Effects-System)
      - [`EffectPoison(nPoisonType)` - Routine 250](NSS-Shared-Functions-Effects-System)
      - [`EffectPsychicStatic()` - Routine 676](NSS-Shared-Functions-Effects-System)
      - [`EffectRegenerate(nAmount, fIntervalSeconds)` - Routine 164](NSS-Shared-Functions-Effects-System)
      - [`EffectResurrection()` - Routine 82](NSS-Shared-Functions-Effects-System)
      - [`EffectSavingThrowDecrease(nSave, nValue, nSaveType)` - Routine 452](NSS-Shared-Functions-Effects-System)
      - [`EffectSavingThrowIncrease(nSave, nValue, nSaveType)` - Routine 117](NSS-Shared-Functions-Effects-System)
      - [`EffectSeeInvisible()` - Routine 466](NSS-Shared-Functions-Effects-System)
      - [`EffectSkillDecrease(nSkill, nValue)` - Routine 453](NSS-Shared-Functions-Effects-System)
      - [`EffectSkillIncrease(nSkill, nValue)` - Routine 351](NSS-Shared-Functions-Effects-System)
      - [`EffectSleep()` - Routine 154](NSS-Shared-Functions-Effects-System)
      - [`EffectSpellImmunity(nImmunityToSpell)` - Routine 149](NSS-Shared-Functions-Effects-System)
      - [`EffectSpellLevelAbsorption(nMaxSpellLevelAbsorbed, nTotalSpellLevelsAbsorbed, nSpellSchool)` - Routine 472](NSS-Shared-Functions-Effects-System)
      - [`EffectStunned()` - Routine 161](NSS-Shared-Functions-Effects-System)
      - [`EffectTemporaryForcePoints(nTempForce)` - Routine 156](NSS-Shared-Functions-Effects-System)
      - [`EffectTemporaryHitpoints(nHitPoints)` - Routine 314](NSS-Shared-Functions-Effects-System)
      - [`EffectTimeStop()` - Routine 467](NSS-Shared-Functions-Effects-System)
      - [`EffectTrueSeeing()` - Routine 465](NSS-Shared-Functions-Effects-System)
      - [`EffectVisualEffect(nVisualEffectId, nMissEffect)` - Routine 180](NSS-Shared-Functions-Effects-System)
      - [`EffectWhirlWind()` - Routine 703](NSS-Shared-Functions-Effects-System)
      - [`EnableVideoEffect(nEffectType)` - Routine 508](NSS-Shared-Functions-Effects-System)
      - [`ExtraordinaryEffect(eEffect)` - Routine 114](NSS-Shared-Functions-Effects-System)
      - [`GetAreaOfEffectCreator(oAreaOfEffectObject)` - Routine 264](NSS-Shared-Functions-Effects-System)
      - [`GetEffectCreator(eEffect)` - Routine 91](NSS-Shared-Functions-Effects-System)
      - [`GetEffectDurationType(eEffect)` - Routine 89](NSS-Shared-Functions-Effects-System)
      - [`GetEffectSpellId(eSpellEffect)` - Routine 305](NSS-Shared-Functions-Effects-System)
      - [`GetEffectSubType(eEffect)` - Routine 90](NSS-Shared-Functions-Effects-System)
      - [`GetEffectType(eEffect)` - Routine 170](NSS-Shared-Functions-Effects-System)
      - [`GetFirstEffect(oCreature)` - Routine 85](NSS-Shared-Functions-Effects-System)
      - [`GetHasFeatEffect(nFeat, oObject)` - Routine 543](NSS-Shared-Functions-Effects-System)
      - [`GetHasSpellEffect(nSpell, oObject)` - Routine 304](NSS-Shared-Functions-Effects-System)
      - [`GetIsEffectValid(eEffect)` - Routine 88](NSS-Shared-Functions-Effects-System)
      - [`GetIsWeaponEffective(oVersus, bOffHand)` - Routine 422](NSS-Shared-Functions-Effects-System)
      - [`GetNextEffect(oCreature)` - Routine 86](NSS-Shared-Functions-Effects-System)
      - [`MagicalEffect(eEffect)` - Routine 112](NSS-Shared-Functions-Effects-System)
      - [`PlayVisualAreaEffect(nEffectID, lTarget)` - Routine 677](NSS-Shared-Functions-Effects-System)
      - [`RemoveEffect(oCreature, eEffect)` - Routine 87](NSS-Shared-Functions-Effects-System)
      - [`SetEffectIcon(eEffect, nIcon)` - Routine 552](NSS-Shared-Functions-Effects-System)
      - [`SupernaturalEffect(eEffect)` - Routine 113](NSS-Shared-Functions-Effects-System)
      - [`SWMG_SetSpeedBlurEffect(bEnabled, fRatio)` - Routine 563](NSS-Shared-Functions-Effects-System)
      - [`VersusRacialTypeEffect(eEffect, nRacialType)` - Routine 356](NSS-Shared-Functions-Effects-System)
      - [`VersusTrapEffect(eEffect)` - Routine 357](NSS-Shared-Functions-Effects-System)
    - [Global Variables](#global-variables)
      - [`GetGlobalBoolean(sIdentifier)` - Routine 578](NSS-Shared-Functions-Global-Variables)
      - [`GetGlobalLocation(sIdentifier)` - Routine 692](NSS-Shared-Functions-Global-Variables)
      - [`GetGlobalNumber(sIdentifier)` - Routine 580](NSS-Shared-Functions-Global-Variables)
      - [`GetGlobalString(sIdentifier)` - Routine 194](NSS-Shared-Functions-Global-Variables)
      - [`SetGlobalBoolean(sIdentifier, nValue)` - Routine 579](NSS-Shared-Functions-Global-Variables)
      - [`SetGlobalFadeIn(fWait, fLength, fR, fG, fB)` - Routine 719](NSS-Shared-Functions-Global-Variables)
      - [`SetGlobalFadeOut(fWait, fLength, fR, fG, fB)` - Routine 720](NSS-Shared-Functions-Global-Variables)
      - [`SetGlobalLocation(sIdentifier, lValue)` - Routine 693](NSS-Shared-Functions-Global-Variables)
      - [`SetGlobalNumber(sIdentifier, nValue)` - Routine 581](NSS-Shared-Functions-Global-Variables)
      - [`SetGlobalString(sIdentifier, sValue)` - Routine 160](NSS-Shared-Functions-Global-Variables)
    - [Item Management](#item-management)
      - [`ChangeItemCost(sItem, fCostMultiplier)` - Routine 747](NSS-Shared-Functions-Item-Management)
      - [`CreateItemOnFloor(sTemplate, lLocation, bUseAppearAnimation)` - Routine 766](NSS-Shared-Functions-Item-Management)
      - [`CreateItemOnObject(sItemTemplate, oTarget, nStackSize)` - Routine 31](NSS-Shared-Functions-Item-Management)
      - [`EventActivateItem(oItem, lTarget, oTarget)` - Routine 424](NSS-Shared-Functions-Item-Management)
      - [`GetBaseItemType(oItem)` - Routine 397](NSS-Shared-Functions-Item-Management)
      - [`GetFirstItemInInventory(oTarget)` - Routine 339](NSS-Shared-Functions-Item-Management)
      - [`GetInventoryDisturbItem()` - Routine 353](NSS-Shared-Functions-Item-Management)
      - [`GetItemActivated()` - Routine 439](NSS-Shared-Functions-Item-Management)
      - [`GetItemActivatedTarget()` - Routine 442](NSS-Shared-Functions-Item-Management)
      - [`GetItemActivatedTargetLocation()` - Routine 441](NSS-Shared-Functions-Item-Management)
      - [`GetItemActivator()` - Routine 440](NSS-Shared-Functions-Item-Management)
      - [`GetItemACValue(oItem)` - Routine 401](NSS-Shared-Functions-Item-Management)
      - [`GetItemInSlot(nInventorySlot, oCreature)` - Routine 155](NSS-Shared-Functions-Item-Management)
      - [`GetItemPossessedBy(oCreature, sItemTag)` - Routine 30](NSS-Shared-Functions-Item-Management)
      - [`GetItemPossessor(oItem)` - Routine 29](NSS-Shared-Functions-Item-Management)
      - [`GetItemStackSize(oItem)` - Routine 138](NSS-Shared-Functions-Item-Management)
      - [`GetLastItemEquipped()` - Routine 52](NSS-Shared-Functions-Item-Management)
      - [`GetModuleItemAcquired()` - Routine 282](NSS-Shared-Functions-Item-Management)
      - [`GetModuleItemAcquiredFrom()` - Routine 283](NSS-Shared-Functions-Item-Management)
      - [`GetModuleItemLost()` - Routine 292](NSS-Shared-Functions-Item-Management)
      - [`GetModuleItemLostBy()` - Routine 293](NSS-Shared-Functions-Item-Management)
      - [`GetNextItemInInventory(oTarget)` - Routine 340](NSS-Shared-Functions-Item-Management)
      - [`GetNumStackedItems(oItem)` - Routine 475](NSS-Shared-Functions-Item-Management)
      - [`GetSpellCastItem()` - Routine 438](NSS-Shared-Functions-Item-Management)
      - [`SetItemNonEquippable(oItem, bNonEquippable)` - Routine 266](NSS-Shared-Functions-Item-Management)
      - [`SetItemStackSize(oItem, nStackSize)` - Routine 150](NSS-Shared-Functions-Item-Management)
    - [Item Properties](#item-properties)
      - [`GetItemHasItemProperty(oItem, nProperty)` - Routine 398](NSS-Shared-Functions-Item-Properties)
    - [Local Variables](#local-variables)
      - [`GetLocalBoolean(oObject, nIndex)` - Routine 679](NSS-Shared-Functions-Local-Variables)
      - [`GetLocalNumber(oObject, nIndex)` - Routine 681](NSS-Shared-Functions-Local-Variables)
      - [`SetLocalBoolean(oObject, nIndex, nValue)` - Routine 680](NSS-Shared-Functions-Local-Variables)
      - [`SetLocalNumber(oObject, nIndex, nValue)` - Routine 682](NSS-Shared-Functions-Local-Variables)
    - [Module and Area Functions](#module-and-area-functions)
      - [`GetArea(oTarget)` - Routine 24](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`GetAreaUnescapable()` - Routine 15](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`GetFirstObjectInArea(oArea, nObjectFilter)` - Routine 93](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`GetModule()` - Routine 242](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`GetModuleFileName()` - Routine 210](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`GetModuleName()` - Routine 561](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`GetNextObjectInArea(oArea, nObjectFilter)` - Routine 94](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`SetAreaFogColor(oArea, fRed, fGreen, fBlue)` - Routine 746](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`SetAreaTransitionBMP(nPredefinedAreaTransition, sCustomAreaTransitionBMP)` - Routine 203](NSS-Shared-Functions-Module-and-Area-Functions)
      - [`SetAreaUnescapable(bUnescapable)` - Routine 14](NSS-Shared-Functions-Module-and-Area-Functions)
    - [Object Query and Manipulation](#object-query-and-manipulation)
      - [`GetNearestCreature(nFirstCriteriaType, nFirstCriteriaValue, oTarget, nNth, nSecondCriteriaType, nSecondCriteriaValue, nThirdCriteriaType, nThirdCriteriaValue)` - Routine 38](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetNearestCreatureToLocation(nFirstCriteriaType, nFirstCriteriaValue, lLocation, nNth, nSecondCriteriaType, nSecondCriteriaValue, nThirdCriteriaType, nThirdCriteriaValue)` - Routine 226](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetNearestObject(nObjectType, oTarget, nNth)` - Routine 227](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetNearestObjectByTag(sTag, oTarget, nNth)` - Routine 229](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetNearestObjectToLocation(nObjectType, lLocation, nNth)` - Routine 228](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetNearestTrapToObject(oTarget, nTrapDetected)` - Routine 488](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetObjectByTag(sTag, nNth)` - Routine 200](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetObjectHeard(oTarget, oSource)` - Routine 290](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetObjectSeen(oTarget, oSource)` - Routine 289](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetObjectType(oTarget)` - Routine 106](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`GetSpellTargetObject()` - Routine 47](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`SWMG_GetObjectByName(sName)` - Routine 585](NSS-Shared-Functions-Object-Query-and-Manipulation)
      - [`SWMG_GetObjectName(oid)` - Routine 597](NSS-Shared-Functions-Object-Query-and-Manipulation)
    - [Other Functions](#other-functions)
      - [`GetAC(oObject, nForFutureUse)` - Routine 116](NSS-Shared-Functions-Other-Functions)
      - [`GetAppearanceType(oCreature)` - Routine 524](NSS-Shared-Functions-Other-Functions)
      - [`GetAttemptedMovementTarget()` - Routine 489](NSS-Shared-Functions-Other-Functions)
      - [`GetAttemptedSpellTarget()` - Routine 375](NSS-Shared-Functions-Other-Functions)
      - [`GetBlockingCreature(oTarget)` - Routine 490](NSS-Shared-Functions-Other-Functions)
      - [`GetBlockingDoor()` - Routine 336](NSS-Shared-Functions-Other-Functions)
      - [`GetButtonMashCheck()` - Routine 267](NSS-Shared-Functions-Other-Functions)
      - [`GetCasterLevel(oCreature)` - Routine 84](NSS-Shared-Functions-Other-Functions)
      - [`GetCategoryFromTalent(tTalent)` - Routine 735](NSS-Shared-Functions-Other-Functions)
      - [`GetChallengeRating(oCreature)` - Routine 494](NSS-Shared-Functions-Other-Functions)
      - [`GetCheatCode(nCode)` - Routine 764](NSS-Shared-Functions-Other-Functions)
      - [`GetClickingObject()` - Routine 326](NSS-Shared-Functions-Other-Functions)
      - [`GetCommandable(oTarget)` - Routine 163](NSS-Shared-Functions-Other-Functions)
      - [`GetCreatureHasTalent(tTalent, oCreature)` - Routine 306](NSS-Shared-Functions-Other-Functions)
      - [`GetCreatureMovmentType(oidCreature)` - Routine 566](NSS-Shared-Functions-Other-Functions)
      - [`GetCreatureSize(oCreature)` - Routine 479](NSS-Shared-Functions-Other-Functions)
      - [`GetCreatureTalentBest(nCategory, nCRMax, oCreature, nInclusion, nExcludeType, nExcludeId)` - Routine 308](NSS-Shared-Functions-Other-Functions)
      - [`GetCreatureTalentRandom(nCategory, oCreature, nInclusion)` - Routine 307](NSS-Shared-Functions-Other-Functions)
      - [`GetCurrentAction(oObject)` - Routine 522](NSS-Shared-Functions-Other-Functions)
      - [`GetCurrentForcePoints(oObject)` - Routine 55](NSS-Shared-Functions-Other-Functions)
      - [`GetCurrentHitPoints(oObject)` - Routine 49](NSS-Shared-Functions-Other-Functions)
      - [`GetCurrentStealthXP()` - Routine 474](NSS-Shared-Functions-Other-Functions)
      - [`GetDamageDealtByType(nDamageType)` - Routine 344](NSS-Shared-Functions-Other-Functions)
      - [`GetDifficultyModifier()` - Routine 523](NSS-Shared-Functions-Other-Functions)
      - [`GetDistanceBetween(oObjectA, oObjectB)` - Routine 151](NSS-Shared-Functions-Other-Functions)
      - [`GetDistanceBetween2D(oObjectA, oObjectB)` - Routine 319](NSS-Shared-Functions-Other-Functions)
      - [`GetDistanceBetweenLocations(lLocationA, lLocationB)` - Routine 298](NSS-Shared-Functions-Other-Functions)
      - [`GetDistanceBetweenLocations2D(lLocationA, lLocationB)` - Routine 334](NSS-Shared-Functions-Other-Functions)
      - [`GetDistanceToObject(oObject)` - Routine 41](NSS-Shared-Functions-Other-Functions)
      - [`GetDistanceToObject2D(oObject)` - Routine 335](NSS-Shared-Functions-Other-Functions)
      - [`GetEncounterActive(oEncounter)` - Routine 276](NSS-Shared-Functions-Other-Functions)
      - [`GetEncounterDifficulty(oEncounter)` - Routine 297](NSS-Shared-Functions-Other-Functions)
      - [`GetEncounterSpawnsCurrent(oEncounter)` - Routine 280](NSS-Shared-Functions-Other-Functions)
      - [`GetEncounterSpawnsMax(oEncounter)` - Routine 278](NSS-Shared-Functions-Other-Functions)
      - [`GetEnteringObject()` - Routine 25](NSS-Shared-Functions-Other-Functions)
      - [`GetExitingObject()` - Routine 26](NSS-Shared-Functions-Other-Functions)
      - [`GetFacing(oTarget)` - Routine 28](NSS-Shared-Functions-Other-Functions)
      - [`GetFacingFromLocation(lLocation)` - Routine 225](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionAverageLevel(oFactionMember)` - Routine 189](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionAverageReputation(oSourceFactionMember, oTarget)` - Routine 186](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionAverageXP(oFactionMember)` - Routine 190](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionBestAC(oFactionMember, bMustBeVisible)` - Routine 193](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionEqual(oFirstObject, oSecondObject)` - Routine 172](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionGold(oFactionMember)` - Routine 185](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionLeader(oMemberOfFaction)` - Routine 562](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionLeastDamagedMember(oFactionMember, bMustBeVisible)` - Routine 184](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionMostDamagedMember(oFactionMember, bMustBeVisible)` - Routine 183](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionStrongestMember(oFactionMember, bMustBeVisible)` - Routine 182](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionWeakestMember(oFactionMember, bMustBeVisible)` - Routine 181](NSS-Shared-Functions-Other-Functions)
      - [`GetFactionWorstAC(oFactionMember, bMustBeVisible)` - Routine 192](NSS-Shared-Functions-Other-Functions)
      - [`GetFirstFactionMember(oMemberOfFaction, bPCOnly)` - Routine 380](NSS-Shared-Functions-Other-Functions)
      - `GetFirstInPersistentObject(oPersistentObject, nResidentObjectType, nPersistentZone)`
      - [`GetFirstObjectInShape(nShape, fSize, lTarget, bLineOfSight, nObjectFilter, vOrigin)` - Routine 128](NSS-Shared-Functions-Other-Functions)
      - [`GetFirstPC()` - Routine 548](NSS-Shared-Functions-Other-Functions)
      - [`GetFortitudeSavingThrow(oTarget)` - Routine 491](NSS-Shared-Functions-Other-Functions)
      - [`GetFoundEnemyCreature(oTarget)` - Routine 495](NSS-Shared-Functions-Other-Functions)
      - [`GetGameDifficulty()` - Routine 513](NSS-Shared-Functions-Other-Functions)
      - [`GetGender(oCreature)` - Routine 358](NSS-Shared-Functions-Other-Functions)
      - [`GetGold(oTarget)` - Routine 418](NSS-Shared-Functions-Other-Functions)
      - [`GetGoldPieceValue(oItem)` - Routine 311](NSS-Shared-Functions-Other-Functions)
      - [`GetGoodEvilValue(oCreature)` - Routine 125](NSS-Shared-Functions-Other-Functions)
      - [`GetHasInventory(oObject)` - Routine 570](NSS-Shared-Functions-Other-Functions)
      - [`GetHasSpell(nSpell, oCreature)` - Routine 377](NSS-Shared-Functions-Other-Functions)
      - [`GetHitDice(oCreature)` - Routine 166](NSS-Shared-Functions-Other-Functions)
      - [`GetIdentified(oItem)` - Routine 332](NSS-Shared-Functions-Other-Functions)
      - [`GetIdFromTalent(tTalent)` - Routine 363](NSS-Shared-Functions-Other-Functions)
      - [`GetInventoryDisturbType()` - Routine 352](NSS-Shared-Functions-Other-Functions)
      - [`GetIsDawn()` - Routine 407](NSS-Shared-Functions-Other-Functions)
      - [`GetIsDay()` - Routine 405](NSS-Shared-Functions-Other-Functions)
      - [`GetIsDead(oCreature)` - Routine 140](NSS-Shared-Functions-Other-Functions)
      - [`GetIsDebilitated(oCreature)` - Routine 732](NSS-Shared-Functions-Other-Functions)
      - [`GetIsDoorActionPossible(oTargetDoor, nDoorAction)` - Routine 337](NSS-Shared-Functions-Other-Functions)
      - [`GetIsDusk()` - Routine 408](NSS-Shared-Functions-Other-Functions)
      - [`GetIsEncounterCreature(oCreature)` - Routine 409](NSS-Shared-Functions-Other-Functions)
      - [`GetIsEnemy(oTarget, oSource)` - Routine 235](NSS-Shared-Functions-Other-Functions)
      - [`GetIsFriend(oTarget, oSource)` - Routine 236](NSS-Shared-Functions-Other-Functions)
      - [`GetIsImmune(oCreature, nImmunityType, oVersus)` - Routine 274](NSS-Shared-Functions-Other-Functions)
      - [`GetIsLinkImmune(oTarget, eEffect)` - Routine 390](NSS-Shared-Functions-Other-Functions)
      - [`GetIsListening(oObject)` - Routine 174](NSS-Shared-Functions-Other-Functions)
      - [`GetIsLiveContentAvailable(nPkg)` - Routine 748](NSS-Shared-Functions-Other-Functions)
      - [`GetIsNeutral(oTarget, oSource)` - Routine 237](NSS-Shared-Functions-Other-Functions)
      - [`GetIsNight()` - Routine 406](NSS-Shared-Functions-Other-Functions)
      - [`GetIsObjectValid(oObject)` - Routine 42](NSS-Shared-Functions-Other-Functions)
      - [`GetIsOpen(oObject)` - Routine 443](NSS-Shared-Functions-Other-Functions)
      - [`GetIsPlaceableObjectActionPossible(oPlaceable, nPlaceableAction)` - Routine 546](NSS-Shared-Functions-Other-Functions)
      - [`GetIsPoisoned(oObject)` - Routine 751](NSS-Shared-Functions-Other-Functions)
      - [`GetIsTalentValid(tTalent)` - Routine 359](NSS-Shared-Functions-Other-Functions)
      - [`GetIsTrapped(oObject)` - Routine 551](NSS-Shared-Functions-Other-Functions)
      - [`GetJournalEntry(szPlotID)` - Routine 369](NSS-Shared-Functions-Other-Functions)
      - [`GetJournalQuestExperience(szPlotID)` - Routine 384](NSS-Shared-Functions-Other-Functions)
      - [`GetLastAssociateCommand(oAssociate)` - Routine 321](NSS-Shared-Functions-Other-Functions)
      - [`GetLastClosedBy()` - Routine 260](NSS-Shared-Functions-Other-Functions)
      - [`GetLastDamager()` - Routine 346](NSS-Shared-Functions-Other-Functions)
      - [`GetLastDisarmed()` - Routine 347](NSS-Shared-Functions-Other-Functions)
      - [`GetLastDisturbed()` - Routine 348](NSS-Shared-Functions-Other-Functions)
      - [`GetLastForcePowerUsed(oAttacker)` - Routine 723](NSS-Shared-Functions-Other-Functions)
      - [`GetLastHostileActor(oVictim)` - Routine 556](NSS-Shared-Functions-Other-Functions)
      - [`GetLastHostileTarget(oAttacker)` - Routine 721](NSS-Shared-Functions-Other-Functions)
      - [`GetLastLocked()` - Routine 349](NSS-Shared-Functions-Other-Functions)
      - [`GetLastOpenedBy()` - Routine 376](NSS-Shared-Functions-Other-Functions)
      - [`GetLastPazaakResult()` - Routine 365](NSS-Shared-Functions-Other-Functions)
      - [`GetLastPerceived()` - Routine 256](NSS-Shared-Functions-Other-Functions)
      - [`GetLastPerceptionHeard()` - Routine 257](NSS-Shared-Functions-Other-Functions)
      - [`GetLastPerceptionInaudible()` - Routine 258](NSS-Shared-Functions-Other-Functions)
      - [`GetLastPerceptionSeen()` - Routine 259](NSS-Shared-Functions-Other-Functions)
      - [`GetLastPerceptionVanished()` - Routine 261](NSS-Shared-Functions-Other-Functions)
      - [`GetLastRespawnButtonPresser()` - Routine 419](NSS-Shared-Functions-Other-Functions)
      - [`GetLastSpell()` - Routine 246](NSS-Shared-Functions-Other-Functions)
      - [`GetLastSpellCaster()` - Routine 245](NSS-Shared-Functions-Other-Functions)
      - [`GetLastSpellHarmful()` - Routine 423](NSS-Shared-Functions-Other-Functions)
      - [`GetLastTrapDetected(oTarget)` - Routine 486](NSS-Shared-Functions-Other-Functions)
      - [`GetLastUnlocked()` - Routine 350](NSS-Shared-Functions-Other-Functions)
      - [`GetLastUsedBy()` - Routine 330](NSS-Shared-Functions-Other-Functions)
      - [`GetLastWeaponUsed(oCreature)` - Routine 328](NSS-Shared-Functions-Other-Functions)
      - [`GetLevelByPosition(nClassPosition, oCreature)` - Routine 342](NSS-Shared-Functions-Other-Functions)
      - [`GetListenPatternNumber()` - Routine 195](NSS-Shared-Functions-Other-Functions)
      - [`GetLoadFromSaveGame()` - Routine 251](NSS-Shared-Functions-Other-Functions)
      - [`GetLocation(oObject)` - Routine 213](NSS-Shared-Functions-Other-Functions)
      - [`GetLocked(oTarget)` - Routine 325](NSS-Shared-Functions-Other-Functions)
      - [`GetLockKeyRequired(oObject)` - Routine 537](NSS-Shared-Functions-Other-Functions)
      - [`GetLockKeyTag(oObject)` - Routine 538](NSS-Shared-Functions-Other-Functions)
      - [`GetLockLockable(oObject)` - Routine 539](NSS-Shared-Functions-Other-Functions)
      - [`GetLockLockDC(oObject)` - Routine 541](NSS-Shared-Functions-Other-Functions)
      - [`GetLockUnlockDC(oObject)` - Routine 540](NSS-Shared-Functions-Other-Functions)
      - [`GetMatchedSubstring(nString)` - Routine 178](NSS-Shared-Functions-Other-Functions)
      - [`GetMatchedSubstringsCount()` - Routine 179](NSS-Shared-Functions-Other-Functions)
      - [`GetMaxForcePoints(oObject)` - Routine 56](NSS-Shared-Functions-Other-Functions)
      - [`GetMaxHitPoints(oObject)` - Routine 50](NSS-Shared-Functions-Other-Functions)
      - [`GetMaxStealthXP()` - Routine 464](NSS-Shared-Functions-Other-Functions)
      - [`GetMinOneHP(oObject)` - Routine 715](NSS-Shared-Functions-Other-Functions)
      - [`GetMovementRate(oCreature)` - Routine 496](NSS-Shared-Functions-Other-Functions)
      - [`GetName(oObject)` - Routine 253](NSS-Shared-Functions-Other-Functions)
      - [`GetNextFactionMember(oMemberOfFaction, bPCOnly)` - Routine 381](NSS-Shared-Functions-Other-Functions)
      - `GetNextInPersistentObject(oPersistentObject, nResidentObjectType, nPersistentZone)`
      - [`GetNextObjectInShape(nShape, fSize, lTarget, bLineOfSight, nObjectFilter, vOrigin)` - Routine 129](NSS-Shared-Functions-Other-Functions)
      - [`GetNextPC()` - Routine 548](NSS-Shared-Functions-Other-Functions)
      - [`GetNPCAIStyle(oCreature)` - Routine 705](NSS-Shared-Functions-Other-Functions)
      - [`GetPCLevellingUp()` - Routine 542](NSS-Shared-Functions-Other-Functions)
      - [`GetPlaceableIllumination(oPlaceable)` - Routine 545](NSS-Shared-Functions-Other-Functions)
      - [`GetPlanetAvailable(nPlanet)` - Routine 743](NSS-Shared-Functions-Other-Functions)
      - [`GetPlanetSelectable(nPlanet)` - Routine 741](NSS-Shared-Functions-Other-Functions)
      - [`GetPlotFlag(oTarget)` - Routine 455](NSS-Shared-Functions-Other-Functions)
      - [`GetPosition(oTarget)` - Routine 27](NSS-Shared-Functions-Other-Functions)
      - [`GetPositionFromLocation(lLocation)` - Routine 223](NSS-Shared-Functions-Other-Functions)
      - [`GetRacialType(oCreature)` - Routine 107](NSS-Shared-Functions-Other-Functions)
      - [`GetReflexAdjustedDamage(nDamage, oTarget, nDC, nSaveType, oSaveVersus)` - Routine 299](NSS-Shared-Functions-Other-Functions)
      - [`GetReflexSavingThrow(oTarget)` - Routine 493](NSS-Shared-Functions-Other-Functions)
      - [`GetReputation(oSource, oTarget)` - Routine 208](NSS-Shared-Functions-Other-Functions)
      - [`GetRunScriptVar()` - Routine 565](NSS-Shared-Functions-Other-Functions)
      - [`GetSelectedPlanet()` - Routine 744](NSS-Shared-Functions-Other-Functions)
      - [`GetSoloMode()` - Routine 462](NSS-Shared-Functions-Other-Functions)
      - [`GetSpellId()` - Routine 248](NSS-Shared-Functions-Other-Functions)
      - [`GetSpellSaveDC()` - Routine 111](NSS-Shared-Functions-Other-Functions)
      - [`GetSpellTarget(oCreature)` - Routine 752](NSS-Shared-Functions-Other-Functions)
      - [`GetSpellTargetLocation()` - Routine 222](NSS-Shared-Functions-Other-Functions)
      - [`GetStandardFaction(oObject)` - Routine 713](NSS-Shared-Functions-Other-Functions)
      - [`GetStartingLocation()` - Routine 411](NSS-Shared-Functions-Other-Functions)
      - [`GetStealthXPDecrement()` - Routine 498](NSS-Shared-Functions-Other-Functions)
      - [`GetStealthXPEnabled()` - Routine 481](NSS-Shared-Functions-Other-Functions)
      - [`GetStringByStrRef(nStrRef)` - Routine 239](NSS-Shared-Functions-Other-Functions)
      - [`GetStringLeft(sString, nCount)` - Routine 63](NSS-Shared-Functions-Other-Functions)
      - [`GetStringLength(sString)` - Routine 59](NSS-Shared-Functions-Other-Functions)
      - [`GetStringLowerCase(sString)` - Routine 61](NSS-Shared-Functions-Other-Functions)
      - [`GetStringRight(sString, nCount)` - Routine 62](NSS-Shared-Functions-Other-Functions)
      - [`GetStringUpperCase(sString)` - Routine 60](NSS-Shared-Functions-Other-Functions)
      - [`GetSubRace(oCreature)` - Routine 497](NSS-Shared-Functions-Other-Functions)
      - [`GetSubScreenID()` - Routine 53](NSS-Shared-Functions-Other-Functions)
      - [`GetSubString(sString, nStart, nCount)` - Routine 65](NSS-Shared-Functions-Other-Functions)
      - [`GetTag(oObject)` - Routine 168](NSS-Shared-Functions-Other-Functions)
      - [`GetTimeHour()` - Routine 16](NSS-Shared-Functions-Other-Functions)
      - [`GetTimeMillisecond()` - Routine 19](NSS-Shared-Functions-Other-Functions)
      - [`GetTimeMinute()` - Routine 17](NSS-Shared-Functions-Other-Functions)
      - [`GetTimeSecond()` - Routine 18](NSS-Shared-Functions-Other-Functions)
      - [`GetTotalDamageDealt()` - Routine 345](NSS-Shared-Functions-Other-Functions)
      - [`GetTransitionTarget(oTransition)` - Routine 198](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapBaseType(oTrapObject)` - Routine 531](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapCreator(oTrapObject)` - Routine 533](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapDetectable(oTrapObject)` - Routine 528](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapDetectDC(oTrapObject)` - Routine 536](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapDetectedBy(oTrapObject, oCreature)` - Routine 529](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapDisarmable(oTrapObject)` - Routine 527](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapDisarmDC(oTrapObject)` - Routine 535](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapFlagged(oTrapObject)` - Routine 530](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapKeyTag(oTrapObject)` - Routine 534](NSS-Shared-Functions-Other-Functions)
      - [`GetTrapOneShot(oTrapObject)` - Routine 532](NSS-Shared-Functions-Other-Functions)
      - [`GetTypeFromTalent(tTalent)` - Routine 362](NSS-Shared-Functions-Other-Functions)
      - [`GetUserActionsPending()` - Routine 514](NSS-Shared-Functions-Other-Functions)
      - [`GetUserDefinedEventNumber()` - Routine 247](NSS-Shared-Functions-Other-Functions)
      - [`GetWasForcePowerSuccessful(oAttacker)` - Routine 726](NSS-Shared-Functions-Other-Functions)
      - [`GetWaypointByTag(sWaypointTag)` - Routine 197](NSS-Shared-Functions-Other-Functions)
      - [`GetWeaponRanged(oItem)` - Routine 511](NSS-Shared-Functions-Other-Functions)
      - [`GetWillSavingThrow(oTarget)` - Routine 492](NSS-Shared-Functions-Other-Functions)
      - [`GetXP(oCreature)` - Routine 395](NSS-Shared-Functions-Other-Functions)
      - `Random(nMaxInteger)`
      - [`SetAssociateListenPatterns(oTarget)` - Routine 327](NSS-Shared-Functions-Other-Functions)
      - [`SetAvailableNPCId()` - Routine 767](NSS-Shared-Functions-Other-Functions)
      - [`SetButtonMashCheck(nCheck)` - Routine 268](NSS-Shared-Functions-Other-Functions)
      - [`SetCameraFacing(fDirection)` - Routine 45](NSS-Shared-Functions-Other-Functions)
      - [`SetCameraMode(oPlayer, nCameraMode)` - Routine 504](NSS-Shared-Functions-Other-Functions)
      - [`SetCommandable(bCommandable, oTarget)` - Routine 162](NSS-Shared-Functions-Other-Functions)
      - [`SetCurrentStealthXP(nCurrent)` - Routine 478](NSS-Shared-Functions-Other-Functions)
      - [`SetCustomToken(nCustomTokenNumber, sTokenValue)` - Routine 284](NSS-Shared-Functions-Other-Functions)
      - [`SetEncounterActive(nNewValue, oEncounter)` - Routine 277](NSS-Shared-Functions-Other-Functions)
      - [`SetEncounterDifficulty(nEncounterDifficulty, oEncounter)` - Routine 296](NSS-Shared-Functions-Other-Functions)
      - [`SetEncounterSpawnsCurrent(nNewValue, oEncounter)` - Routine 281](NSS-Shared-Functions-Other-Functions)
      - [`SetEncounterSpawnsMax(nNewValue, oEncounter)` - Routine 279](NSS-Shared-Functions-Other-Functions)
      - [`SetFacing(fDirection)` - Routine 10](NSS-Shared-Functions-Other-Functions)
      - [`SetFacingPoint(vTarget)` - Routine 143](NSS-Shared-Functions-Other-Functions)
      - [`SetForcePowerUnsuccessful(nResult, oCreature)` - Routine 731](NSS-Shared-Functions-Other-Functions)
      - [`SetFormation(oAnchor, oCreature, nFormationPattern, nPosition)` - Routine 729](NSS-Shared-Functions-Other-Functions)
      - [`SetGoodEvilValue(oCreature, nAlignment)` - Routine 750](NSS-Shared-Functions-Other-Functions)
      - [`SetIdentified(oItem, bIdentified)` - Routine 333](NSS-Shared-Functions-Other-Functions)
      - [`SetIsDestroyable(bDestroyable, bRaiseable, bSelectableWhenDead)` - Routine 323](NSS-Shared-Functions-Other-Functions)
      - [`SetJournalQuestEntryPicture(szPlotID, oObject, nPictureIndex, bAllPartyMemebers, bAllPlayers)` - Routine 678](NSS-Shared-Functions-Other-Functions)
      - [`SetLightsaberPowered(oCreature, bOverride, bPowered, bShowTransition)` - Routine 421](NSS-Shared-Functions-Other-Functions)
      - [`SetListening(oObject, bValue)` - Routine 175](NSS-Shared-Functions-Other-Functions)
      - [`SetListenPattern(oObject, sPattern, nNumber)` - Routine 176](NSS-Shared-Functions-Other-Functions)
      - [`SetLocked(oTarget, bLocked)` - Routine 324](NSS-Shared-Functions-Other-Functions)
      - [`SetMapPinEnabled(oMapPin, nEnabled)` - Routine 386](NSS-Shared-Functions-Other-Functions)
      - [`SetMaxHitPoints(oObject, nMaxHP)` - Routine 758](NSS-Shared-Functions-Other-Functions)
      - [`SetMaxStealthXP(nMax)` - Routine 468](NSS-Shared-Functions-Other-Functions)
      - [`SetMinOneHP(oObject, nMinOneHP)` - Routine 716](NSS-Shared-Functions-Other-Functions)
      - [`SetNPCAIStyle(oCreature, nStyle)` - Routine 707](NSS-Shared-Functions-Other-Functions)
      - [`SetPlaceableIllumination(oPlaceable, bIlluminate)` - Routine 544](NSS-Shared-Functions-Other-Functions)
      - [`SetPlanetAvailable(nPlanet, bAvailable)` - Routine 742](NSS-Shared-Functions-Other-Functions)
      - [`SetPlanetSelectable(nPlanet, bSelectable)` - Routine 740](NSS-Shared-Functions-Other-Functions)
      - [`SetPlotFlag(oTarget, nPlotFlag)` - Routine 456](NSS-Shared-Functions-Other-Functions)
      - [`SetReturnStrref(bShow, srStringRef, srReturnQueryStrRef)` - Routine 152](NSS-Shared-Functions-Other-Functions)
      - [`SetSoloMode(bActivate)` - Routine 753](NSS-Shared-Functions-Other-Functions)
      - [`SetStealthXPDecrement(nDecrement)` - Routine 499](NSS-Shared-Functions-Other-Functions)
      - [`SetStealthXPEnabled(bEnabled)` - Routine 482](NSS-Shared-Functions-Other-Functions)
      - [`SetTime(nHour, nMinute, nSecond, nMillisecond)` - Routine 12](NSS-Shared-Functions-Other-Functions)
      - [`SetTrapDetectedBy(oTrap, oDetector)` - Routine 550](NSS-Shared-Functions-Other-Functions)
      - [`SetTrapDisabled(oTrap)` - Routine 555](NSS-Shared-Functions-Other-Functions)
      - [`SetTutorialWindowsEnabled(bEnabled)` - Routine 516](NSS-Shared-Functions-Other-Functions)
      - [`SetXP(oCreature, nXpAmount)` - Routine 394](NSS-Shared-Functions-Other-Functions)
    - [Party Management](#party-management)
      - [`GetPartyAIStyle()` - Routine 704](NSS-Shared-Functions-Party-Management)
      - [`GetPartyMemberByIndex(nIndex)` - Routine 577](NSS-Shared-Functions-Party-Management)
      - [`GetPartyMemberCount()` - Routine 126](NSS-Shared-Functions-Party-Management)
      - [`SetPartyAIStyle(nStyle)` - Routine 706](NSS-Shared-Functions-Party-Management)
      - [`SetPartyLeader(nNPC)` - Routine 13](NSS-Shared-Functions-Party-Management)
    - [Player Character Functions](#player-character-functions)
      - [`GetIsPC(oCreature)` - Routine 217](NSS-Shared-Functions-Player-Character-Functions)
      - [`GetLastPlayerDied()` - Routine 291](NSS-Shared-Functions-Player-Character-Functions)
      - [`GetLastPlayerDying()` - Routine 410](NSS-Shared-Functions-Player-Character-Functions)
      - [`GetPCSpeaker()` - Routine 238](NSS-Shared-Functions-Player-Character-Functions)
      - [`GetPlayerRestrictMode(oObject)` - Routine 83](NSS-Shared-Functions-Player-Character-Functions)
      - [`SetPlayerRestrictMode(bRestrict)` - Routine 58](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayer()` - Routine 611](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerAccelerationPerSecond()` - Routine 645](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerInvincibility()` - Routine 642](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerMaxSpeed()` - Routine 667](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerMinSpeed()` - Routine 644](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerOffset()` - Routine 641](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerOrigin()` - Routine 655](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerSpeed()` - Routine 643](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerTunnelInfinite()` - Routine 717](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerTunnelNeg()` - Routine 653](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_GetPlayerTunnelPos()` - Routine 646](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_IsPlayer(oid)` - Routine 600](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerAccelerationPerSecond(fAPS)` - Routine 651](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerInvincibility(fInvincibility)` - Routine 648](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerMaxSpeed(fMaxSpeed)` - Routine 668](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerMinSpeed(fMinSpeed)` - Routine 650](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerOffset(vOffset)` - Routine 647](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerOrigin(vOrigin)` - Routine 656](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerSpeed(fSpeed)` - Routine 649](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerTunnelInfinite(vInfinite)` - Routine 718](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerTunnelNeg(vTunnel)` - Routine 654](NSS-Shared-Functions-Player-Character-Functions)
      - [`SWMG_SetPlayerTunnelPos(vTunnel)` - Routine 652](NSS-Shared-Functions-Player-Character-Functions)
    - [Skills and Feats](#skills-and-feats)
      - [`GetHasFeat(nFeat, oCreature)` - Routine 285](NSS-Shared-Functions-Skills-and-Feats)
      - [`GetHasSkill(nSkill, oCreature)` - Routine 286](NSS-Shared-Functions-Skills-and-Feats)
      - [`GetLastCombatFeatUsed(oAttacker)` - Routine 724](NSS-Shared-Functions-Skills-and-Feats)
      - [`GetMetaMagicFeat()` - Routine 105](NSS-Shared-Functions-Skills-and-Feats)
      - [`GetSkillRank(nSkill, oTarget)` - Routine 315](NSS-Shared-Functions-Skills-and-Feats)
    - [Sound and Music Functions](#sound-and-music-functions)
      - [`GetIsPlayableRacialType(oCreature)` - Routine 312](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`GetStrRefSoundDuration(nStrRef)` - Routine 571](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`PlaySound(sSoundName)` - Routine 46](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SetMusicVolume(fVolume)` - Routine 765](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SWMG_GetSoundFrequency(oFollower, nSound)` - Routine 683](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SWMG_GetSoundFrequencyIsRandom(oFollower, nSound)` - Routine 685](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SWMG_GetSoundVolume(oFollower, nSound)` - Routine 687](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SWMG_PlayAnimation(oObject, sAnimName, bLooping, bQueue, bOverlay)` - Routine 586](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SWMG_SetSoundFrequency(oFollower, nSound, nFrequency)` - Routine 684](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SWMG_SetSoundFrequencyIsRandom(oFollower, nSound, bIsRandom)` - Routine 686](NSS-Shared-Functions-Sound-and-Music-Functions)
      - [`SWMG_SetSoundVolume(oFollower, nSound, nVolume)` - Routine 688](NSS-Shared-Functions-Sound-and-Music-Functions)
  - [K1-Only Functions](#k1-only-functions)
    - Other Functions
  - [TSL-Only Functions](#tsl-only-functions)
    - [Actions](#actions)
      - [`ActionFollowOwner(fRange)` - Routine 398](NSS-Shared-Functions-Actions)
      - [`ActionSwitchWeapons()` - Routine 401](NSS-Shared-Functions-Actions)
    - [Class System](#class-system)
      - [`SetInputClass(nClass)` - Routine 342](NSS-Shared-Functions-Other-Functions)
    - [Combat Functions](#combat-functions)
      - [`GetCombatActionsPending(oCreature)` - Routine 315](NSS-Shared-Functions-Other-Functions)
      - [`SetFakeCombatState(oObject, nEnable)` - Routine 791](NSS-Shared-Functions-Other-Functions)
    - [Dialog and Conversation Functions](#dialog-and-conversation-functions)
      - [`SetKeepStealthInDialog(nStealthState)` - Routine 507](NSS-Shared-Functions-Other-Functions)
    - [Effects System](#effects-system)
      - [`EffectBlind()` - Routine 778](NSS-Shared-Functions-Effects-System)
      - [`EffectCrush()` - Routine 781](NSS-Shared-Functions-Effects-System)
      - [`EffectDroidConfused()` - Routine 782](NSS-Shared-Functions-Effects-System)
      - [`EffectDroidScramble()` - Routine 783](NSS-Shared-Functions-Effects-System)
      - [`EffectFactionModifier(nNewFaction)` - Routine 784](NSS-Shared-Functions-Effects-System)
      - [`EffectForceBody(nLevel)` - Routine 770](NSS-Shared-Functions-Effects-System)
      - [`EffectForceSight()` - Routine 771](NSS-Shared-Functions-Effects-System)
      - [`EffectFPRegenModifier(nPercent)` - Routine 779](NSS-Shared-Functions-Effects-System)
      - [`EffectFury()` - Routine 777](NSS-Shared-Functions-Effects-System)
      - [`EffectMindTrick()` - Routine 772](NSS-Shared-Functions-Effects-System)
      - [`EffectVPRegenModifier(nPercent)` - Routine 780](NSS-Shared-Functions-Effects-System)
      - [`RemoveEffectByExactMatch(oCreature, eEffect)` - Routine 87](NSS-Shared-Functions-Effects-System)
      - [`RemoveEffectByID(oCreature, nEffectID)` - Routine 89](NSS-Shared-Functions-Effects-System)
    - Global Variables
    - Item Management
      - [`GetItemComponent()` - Routine 771](NSS-Shared-Functions-Item-Management)
      - [`GetItemComponentPieceValue()` - Routine 771](NSS-Shared-Functions-Item-Management)
    - Object Query and Manipulation
      - `GetObjectPersonalSpace(aObject)`
    - Other Functions
      - `AdjustCreatureAttributes(oObject, nAttribute, nAmount)`
      - `AssignPUP(nPUP, nNPC)`
      - `ChangeObjectAppearance(oObjectToChange, nAppearance)`
      - `CreatureFlourishWeapon(oObject)`
      - `DetonateMine(oMine)`
      - `DisableHealthRegen(nFlag)`
      - `DisableMap(nFlag)`
      - `EnableRain(nFlag)`
      - `EnableRendering(oObject, bEnable)`
      - `ForceHeartbeat(oCreature)`
      - [`GetBonusForcePoints(oCreature)` - Routine 803](NSS-Shared-Functions-Other-Functions)
      - [`GetChemicalPieceValue()` - Routine 775](NSS-Shared-Functions-Other-Functions)
      - [`GetChemicals()` - Routine 774](NSS-Shared-Functions-Other-Functions)
      - `GetHealTarget(oidHealer)`
      - [`GetInfluence(nNPC)` - Routine 795](NSS-Shared-Functions-Other-Functions)
      - `GetIsPuppet(oPUP)`
      - `GetIsXBox()`
      - `GetLastForfeitViolation()`
      - `GetPUPOwner(oPUP)`
      - [`GetRacialSubType(oTarget)` - Routine 798](NSS-Shared-Functions-Other-Functions)
      - `GetRandomDestination(oCreature, rangeLimit)`
      - [`GetScriptParameter(nIndex)` - Routine 768](NSS-Shared-Functions-Other-Functions)
      - `GetScriptStringParameter()`
      - [`GetSpellAcquired(nSpell, oCreature)` - Routine 377](NSS-Shared-Functions-Other-Functions)
      - `GetSpellBaseForcePointCost(nSpellID)`
      - [`GetSpellForcePointCost()` - Routine 776](NSS-Shared-Functions-Other-Functions)
      - `GetSpellFormMask(nSpellID)`
      - `HasLineOfSight(vSource, vTarget, oSource, oTarget)`
      - `IsFormActive(oCreature, nFormID)`
      - `IsInTotalDefense(oCreature)`
      - `IsMeditating(oCreature)`
      - `IsRunning(oCreature)`
      - `IsStealthed(oCreature)`
      - `ModifyFortitudeSavingThrowBase(aObject, aModValue)`
      - `ModifyReflexSavingThrowBase(aObject, aModValue)`
      - `ModifyWillSavingThrowBase(aObject, aModValue)`
      - `RemoveHeartbeat(oPlaceable)`
      - `ResetCreatureAILevel(oObject)`
      - `SaveNPCByObject(nNPC, oidCharacter)`
      - `SavePUPByObject(nPUP, oidPuppet)`
      - [`SetBonusForcePoints(oCreature, nBonusFP)` - Routine 801](NSS-Shared-Functions-Other-Functions)
      - `SetCreatureAILevel(oObject, nPriority)`
      - `SetCurrentForm(oCreature, nFormID)`
      - `SetDisableTransit(nFlag)`
      - [`SetFadeUntilScript()` - Routine 769](NSS-Shared-Functions-Other-Functions)
      - `SetForceAlwaysUpdate(oObject, nFlag)`
      - `SetForfeitConditions(nForfeitFlags)`
      - `SetHealTarget(oidHealer, oidTarget)`
      - [`SetInfluence(nNPC, nInfluence)` - Routine 796](NSS-Shared-Functions-Other-Functions)
      - [`SetOrientOnClick(oCreature, nState)` - Routine 794](NSS-Shared-Functions-Other-Functions)
      - `ShowDemoScreen(sTexture, nTimeout, nDisplayString, nDisplayX, nDisplayY)`
      - `SpawnAvailablePUP(nPUP, lLocation)`
      - `UnlockAllSongs()`
      - `YavinHackDoorClose(oCreature)`
    - Party Management
      - [`AddAvailablePUPByObject(nPUP, oPuppet)`](#addavailablepupbyobjectnpup-opuppet)
      - [`AddAvailablePUPByTemplate(nPUP, sTemplate)`](#addavailablepupbytemplatenpup-stemplate)
      - [`AddPartyPuppet(nPUP, oidCreature)`](#addpartypuppetnpup-oidcreature)
      - [`GetIsPartyLeader(oCharacter)`](#getispartyleaderocharacter)
      - [`GetPartyLeader()`](#getpartyleader)
      - [`RemoveNPCFromPartyToBase(nNPC)`](#removenpcfrompartytobasennpc)
    - Player Character Functions
      - `GetIsPlayerMadeCharacter(oidCharacter)`
      - `SWMG_PlayerApplyForce(vForce)`
    - Skills and Feats
      - `AdjustCreatureSkills(oObject, nSkill, nAmount)`
      - [`GetFeatAcquired(nFeat, oCreature)` - Routine 285](NSS-Shared-Functions-Skills-and-Feats)
      - [`GetOwnerDemolitionsSkill(oObject)` - Routine 793](NSS-Shared-Functions-Other-Functions)
      - `GetSkillRankBase(nSkill, oObject)`
    - Sound and Music Functions
      - `DisplayDatapad(oDatapad)`
      - `DisplayMessageBox(nStrRef, sIcon)`
      - `PlayOverlayAnimation(oTarget, nAnimation)`
  - [Shared Constants (K1 \& TSL)](#shared-constants-k1--tsl)
    - [Ability Constants](#ability-constants)
      - `ABILITY_CHARISMA`
      - `ABILITY_CONSTITUTION`
      - `ABILITY_DEXTERITY`
      - `ABILITY_INTELLIGENCE`
      - `ABILITY_STRENGTH`
      - `ABILITY_WISDOM`
    - [Alignment Constants](#alignment-constants)
      - `ALIGNMENT_ALL`
      - `ALIGNMENT_DARK_SIDE`
      - `ALIGNMENT_LIGHT_SIDE`
      - `ALIGNMENT_NEUTRAL`
      - `ITEM_PROPERTY_AC_BONUS_VS_ALIGNMENT_GROUP`
      - `ITEM_PROPERTY_ATTACK_BONUS_VS_ALIGNMENT_GROUP`
      - `ITEM_PROPERTY_DAMAGE_BONUS_VS_ALIGNMENT_GROUP`
      - `ITEM_PROPERTY_ENHANCEMENT_BONUS_VS_ALIGNMENT_GROUP`
      - `ITEM_PROPERTY_USE_LIMITATION_ALIGNMENT_GROUP`
    - [Class Type Constants](#class-type-constants)
      - `CLASS_TYPE_COMBATDROID`
      - `CLASS_TYPE_EXPERTDROID`
      - `CLASS_TYPE_INVALID`
      - `CLASS_TYPE_JEDICONSULAR`
      - `CLASS_TYPE_JEDIGUARDIAN`
      - `CLASS_TYPE_JEDISENTINEL`
      - `CLASS_TYPE_MINION`
      - `CLASS_TYPE_SCOUNDREL`
      - `CLASS_TYPE_SCOUT`
      - `CLASS_TYPE_SOLDIER`
    - [Inventory Constants](#inventory-constants)
      - `INVENTORY_DISTURB_TYPE_ADDED`
      - `INVENTORY_DISTURB_TYPE_REMOVED`
      - `INVENTORY_DISTURB_TYPE_STOLEN`
      - `INVENTORY_SLOT_BELT`
      - `INVENTORY_SLOT_BODY`
      - `INVENTORY_SLOT_CARMOUR`
      - `INVENTORY_SLOT_CWEAPON_B`
      - `INVENTORY_SLOT_CWEAPON_L`
      - `INVENTORY_SLOT_CWEAPON_R`
      - `INVENTORY_SLOT_HANDS`
      - `INVENTORY_SLOT_HEAD`
      - `INVENTORY_SLOT_IMPLANT`
      - `INVENTORY_SLOT_LEFTARM`
      - `INVENTORY_SLOT_LEFTWEAPON`
      - `INVENTORY_SLOT_RIGHTARM`
      - `INVENTORY_SLOT_RIGHTWEAPON`
      - `NUM_INVENTORY_SLOTS`
    - [NPC Constants](#npc-constants)
      - `NPC_AISTYLE_AID`
      - `NPC_AISTYLE_DEFAULT_ATTACK`
      - `NPC_AISTYLE_GRENADE_THROWER`
      - `NPC_AISTYLE_JEDI_SUPPORT`
      - `NPC_AISTYLE_MELEE_ATTACK`
      - `NPC_AISTYLE_RANGED_ATTACK`
      - `NPC_CANDEROUS`
      - `NPC_HK_47`
      - `NPC_PLAYER`
      - `NPC_T3_M4`
    - [Object Type Constants](#object-type-constants)
      - `OBJECT_TYPE_ALL`
      - `OBJECT_TYPE_AREA_OF_EFFECT`
      - `OBJECT_TYPE_CREATURE`
      - `OBJECT_TYPE_DOOR`
      - `OBJECT_TYPE_ENCOUNTER`
      - `OBJECT_TYPE_INVALID`
      - `OBJECT_TYPE_ITEM`
      - `OBJECT_TYPE_PLACEABLE`
      - `OBJECT_TYPE_SOUND`
      - `OBJECT_TYPE_STORE`
      - `OBJECT_TYPE_TRIGGER`
      - `OBJECT_TYPE_WAYPOINT`
    - [Other Constants](#other-constants)
      - `AC_ARMOUR_ENCHANTMENT_BONUS`
      - `AC_DEFLECTION_BONUS`
      - `AC_DODGE_BONUS`
      - `AC_NATURAL_BONUS`
      - `AC_SHIELD_ENCHANTMENT_BONUS`
      - `AC_VS_DAMAGE_TYPE_ALL`
      - `ACTION_ANIMALEMPATHY`
      - `ACTION_ATTACKOBJECT`
      - `ACTION_CASTSPELL`
      - `ACTION_CLOSEDOOR`
      - `ACTION_COUNTERSPELL`
      - `ACTION_DIALOGOBJECT`
      - `ACTION_DISABLETRAP`
      - `ACTION_DROPITEM`
      - `ACTION_EXAMINETRAP`
      - `ACTION_FLAGTRAP`
      - `ACTION_FOLLOW`
      - `ACTION_FOLLOWLEADER`
      - `ACTION_HEAL`
      - `ACTION_INVALID`
      - `ACTION_ITEMCASTSPELL`
      - `ACTION_LOCK`
      - `ACTION_MOVETOPOINT`
      - `ACTION_OPENDOOR`
      - `ACTION_OPENLOCK`
      - `ACTION_PICKPOCKET`
      - `ACTION_PICKUPITEM`
      - `ACTION_QUEUEEMPTY`
      - `ACTION_RECOVERTRAP`
      - `ACTION_REST`
      - `ACTION_SETTRAP`
      - `ACTION_SIT`
      - `ACTION_TAUNT`
      - `ACTION_USEOBJECT`
      - `ACTION_WAIT`
      - `ANIMATION_FIREFORGET_ACTIVATE`
      - `ANIMATION_FIREFORGET_BOW`
      - `ANIMATION_FIREFORGET_CHOKE`
      - `ANIMATION_FIREFORGET_CUSTOM01`
      - `ANIMATION_FIREFORGET_GREETING`
      - `ANIMATION_FIREFORGET_HEAD_TURN_LEFT`
      - `ANIMATION_FIREFORGET_HEAD_TURN_RIGHT`
      - `ANIMATION_FIREFORGET_INJECT`
      - `ANIMATION_FIREFORGET_PAUSE_BORED`
      - `ANIMATION_FIREFORGET_PAUSE_SCRATCH_HEAD`
      - `ANIMATION_FIREFORGET_PERSUADE`
      - `ANIMATION_FIREFORGET_SALUTE`
      - `ANIMATION_FIREFORGET_TAUNT`
      - `ANIMATION_FIREFORGET_THROW_HIGH`
      - `ANIMATION_FIREFORGET_THROW_LOW`
      - `ANIMATION_FIREFORGET_TREAT_INJURED`
      - `ANIMATION_FIREFORGET_USE_COMPUTER`
      - `ANIMATION_FIREFORGET_VICTORY1`
      - `ANIMATION_FIREFORGET_VICTORY2`
      - `ANIMATION_FIREFORGET_VICTORY3`
      - `ANIMATION_LOOPING_CHOKE`
      - `ANIMATION_LOOPING_DANCE`
      - `ANIMATION_LOOPING_DANCE1`
      - `ANIMATION_LOOPING_DEACTIVATE`
      - `ANIMATION_LOOPING_DEAD`
      - `ANIMATION_LOOPING_DEAD_PRONE`
      - `ANIMATION_LOOPING_FLIRT`
      - `ANIMATION_LOOPING_GET_LOW`
      - `ANIMATION_LOOPING_GET_MID`
      - `ANIMATION_LOOPING_HORROR`
      - `ANIMATION_LOOPING_KNEEL_TALK_ANGRY`
      - `ANIMATION_LOOPING_KNEEL_TALK_SAD`
      - `ANIMATION_LOOPING_LISTEN`
      - `ANIMATION_LOOPING_LISTEN_INJURED`
      - `ANIMATION_LOOPING_MEDITATE`
      - `ANIMATION_LOOPING_PAUSE`
      - `ANIMATION_LOOPING_PAUSE2`
      - `ANIMATION_LOOPING_PAUSE3`
      - `ANIMATION_LOOPING_PAUSE_DRUNK`
      - `ANIMATION_LOOPING_PAUSE_TIRED`
      - `ANIMATION_LOOPING_PRONE`
      - `ANIMATION_LOOPING_READY`
      - `ANIMATION_LOOPING_SLEEP`
      - `ANIMATION_LOOPING_SPASM`
      - `ANIMATION_LOOPING_TALK_FORCEFUL`
      - `ANIMATION_LOOPING_TALK_INJURED`
      - `ANIMATION_LOOPING_TALK_LAUGHING`
      - `ANIMATION_LOOPING_TALK_NORMAL`
      - `ANIMATION_LOOPING_TALK_PLEADING`
      - `ANIMATION_LOOPING_TALK_SAD`
      - `ANIMATION_LOOPING_TREAT_INJURED`
      - `ANIMATION_LOOPING_USE_COMPUTER`
      - `ANIMATION_LOOPING_WELD`
      - `ANIMATION_LOOPING_WORSHIP`
      - `ANIMATION_PLACEABLE_ACTIVATE`
      - `ANIMATION_PLACEABLE_ANIMLOOP01`
      - `ANIMATION_PLACEABLE_ANIMLOOP02`
      - `ANIMATION_PLACEABLE_ANIMLOOP03`
      - `ANIMATION_PLACEABLE_ANIMLOOP04`
      - `ANIMATION_PLACEABLE_ANIMLOOP05`
      - `ANIMATION_PLACEABLE_ANIMLOOP06`
      - `ANIMATION_PLACEABLE_ANIMLOOP07`
      - `ANIMATION_PLACEABLE_ANIMLOOP08`
      - `ANIMATION_PLACEABLE_ANIMLOOP09`
      - `ANIMATION_PLACEABLE_ANIMLOOP10`
      - `ANIMATION_PLACEABLE_CLOSE`
      - `ANIMATION_PLACEABLE_DEACTIVATE`
      - `ANIMATION_PLACEABLE_OPEN`
      - `ANIMATION_ROOM_SCRIPTLOOP01`
      - `ANIMATION_ROOM_SCRIPTLOOP02`
      - `ANIMATION_ROOM_SCRIPTLOOP03`
      - `ANIMATION_ROOM_SCRIPTLOOP04`
      - `ANIMATION_ROOM_SCRIPTLOOP05`
      - `ANIMATION_ROOM_SCRIPTLOOP06`
      - `ANIMATION_ROOM_SCRIPTLOOP07`
      - `ANIMATION_ROOM_SCRIPTLOOP08`
      - `ANIMATION_ROOM_SCRIPTLOOP09`
      - `ANIMATION_ROOM_SCRIPTLOOP10`
      - `ANIMATION_ROOM_SCRIPTLOOP11`
      - `ANIMATION_ROOM_SCRIPTLOOP12`
      - `ANIMATION_ROOM_SCRIPTLOOP13`
      - `ANIMATION_ROOM_SCRIPTLOOP14`
      - `ANIMATION_ROOM_SCRIPTLOOP15`
      - `ANIMATION_ROOM_SCRIPTLOOP16`
      - `ANIMATION_ROOM_SCRIPTLOOP17`
      - `ANIMATION_ROOM_SCRIPTLOOP18`
      - `ANIMATION_ROOM_SCRIPTLOOP19`
      - `ANIMATION_ROOM_SCRIPTLOOP20`
      - `AOE_MOB_BLINDING`
      - `AOE_MOB_CIRCCHAOS`
      - `AOE_MOB_CIRCEVIL`
      - `AOE_MOB_CIRCGOOD`
      - `AOE_MOB_CIRCLAW`
      - `AOE_MOB_DRAGON_FEAR`
      - `AOE_MOB_ELECTRICAL`
      - `AOE_MOB_FEAR`
      - `AOE_MOB_FIRE`
      - `AOE_MOB_FROST`
      - `AOE_MOB_INVISIBILITY_PURGE`
      - `AOE_MOB_MENACE`
      - `AOE_MOB_PROTECTION`
      - `AOE_MOB_SILENCE`
      - `AOE_MOB_STUN`
      - `AOE_MOB_TYRANT_FOG`
      - `AOE_MOB_UNEARTHLY`
      - `AOE_MOB_UNNATURAL`
      - `AOE_PER_CREEPING_DOOM`
      - `AOE_PER_DARKNESS`
      - `AOE_PER_DELAY_BLAST_FIREBALL`
      - `AOE_PER_ENTANGLE`
      - `AOE_PER_EVARDS_BLACK_TENTACLES`
      - `AOE_PER_FOGACID`
      - `AOE_PER_FOGFIRE`
      - `AOE_PER_FOGGHOUL`
      - `AOE_PER_FOGKILL`
      - `AOE_PER_FOGMIND`
      - `AOE_PER_FOGSTINK`
      - `AOE_PER_GREASE`
      - `AOE_PER_INVIS_SPHERE`
      - `AOE_PER_STORM`
      - `AOE_PER_WALLBLADE`
      - `AOE_PER_WALLFIRE`
      - `AOE_PER_WALLWIND`
      - `AOE_PER_WEB`
      - `AREA_TRANSITION_CASTLE_01`
      - `AREA_TRANSITION_CASTLE_02`
      - `AREA_TRANSITION_CASTLE_03`
      - `AREA_TRANSITION_CASTLE_04`
      - `AREA_TRANSITION_CASTLE_05`
      - `AREA_TRANSITION_CASTLE_06`
      - `AREA_TRANSITION_CASTLE_07`
      - `AREA_TRANSITION_CASTLE_08`
      - `AREA_TRANSITION_CITY`
      - `AREA_TRANSITION_CITY_01`
      - `AREA_TRANSITION_CITY_02`
      - `AREA_TRANSITION_CITY_03`
      - `AREA_TRANSITION_CITY_04`
      - `AREA_TRANSITION_CITY_05`
      - `AREA_TRANSITION_CRYPT`
      - `AREA_TRANSITION_CRYPT_01`
      - `AREA_TRANSITION_CRYPT_02`
      - `AREA_TRANSITION_CRYPT_03`
      - `AREA_TRANSITION_CRYPT_04`
      - `AREA_TRANSITION_CRYPT_05`
      - `AREA_TRANSITION_DUNGEON_01`
      - `AREA_TRANSITION_DUNGEON_02`
      - `AREA_TRANSITION_DUNGEON_03`
      - `AREA_TRANSITION_DUNGEON_04`
      - `AREA_TRANSITION_DUNGEON_05`
      - `AREA_TRANSITION_DUNGEON_06`
      - `AREA_TRANSITION_DUNGEON_07`
      - `AREA_TRANSITION_DUNGEON_08`
      - `AREA_TRANSITION_FOREST`
      - `AREA_TRANSITION_FOREST_01`
      - `AREA_TRANSITION_FOREST_02`
      - `AREA_TRANSITION_FOREST_03`
      - `AREA_TRANSITION_FOREST_04`
      - `AREA_TRANSITION_FOREST_05`
      - `AREA_TRANSITION_INTERIOR_01`
      - `AREA_TRANSITION_INTERIOR_02`
      - `AREA_TRANSITION_INTERIOR_03`
      - `AREA_TRANSITION_INTERIOR_04`
      - `AREA_TRANSITION_INTERIOR_05`
      - `AREA_TRANSITION_INTERIOR_06`
      - `AREA_TRANSITION_INTERIOR_07`
      - `AREA_TRANSITION_INTERIOR_08`
      - `AREA_TRANSITION_INTERIOR_09`
      - `AREA_TRANSITION_INTERIOR_10`
      - `AREA_TRANSITION_INTERIOR_11`
      - `AREA_TRANSITION_INTERIOR_12`
      - `AREA_TRANSITION_INTERIOR_13`
      - `AREA_TRANSITION_INTERIOR_14`
      - `AREA_TRANSITION_INTERIOR_15`
      - `AREA_TRANSITION_INTERIOR_16`
      - `AREA_TRANSITION_MINES_01`
      - `AREA_TRANSITION_MINES_02`
      - `AREA_TRANSITION_MINES_03`
      - `AREA_TRANSITION_MINES_04`
      - `AREA_TRANSITION_MINES_05`
      - `AREA_TRANSITION_MINES_06`
      - `AREA_TRANSITION_MINES_07`
      - `AREA_TRANSITION_MINES_08`
      - `AREA_TRANSITION_MINES_09`
      - `AREA_TRANSITION_RANDOM`
      - `AREA_TRANSITION_RURAL`
      - `AREA_TRANSITION_RURAL_01`
      - `AREA_TRANSITION_RURAL_02`
      - `AREA_TRANSITION_RURAL_03`
      - `AREA_TRANSITION_RURAL_04`
      - `AREA_TRANSITION_RURAL_05`
      - `AREA_TRANSITION_SEWER_01`
      - `AREA_TRANSITION_SEWER_02`
      - `AREA_TRANSITION_SEWER_03`
      - `AREA_TRANSITION_SEWER_04`
      - `AREA_TRANSITION_SEWER_05`
      - `AREA_TRANSITION_USER_DEFINED`
      - `ATTACK_BONUS_MISC`
      - `ATTACK_BONUS_OFFHAND`
      - `ATTACK_BONUS_ONHAND`
      - `ATTACK_RESULT_ATTACK_FAILED`
      - `ATTACK_RESULT_ATTACK_RESISTED`
      - `ATTACK_RESULT_AUTOMATIC_HIT`
      - `ATTACK_RESULT_CRITICAL_HIT`
      - `ATTACK_RESULT_DEFLECTED`
      - `ATTACK_RESULT_HIT_SUCCESSFUL`
      - `ATTACK_RESULT_INVALID`
      - `ATTACK_RESULT_MISS`
      - `ATTACK_RESULT_PARRIED`
      - `ATTITUDE_AGGRESSIVE`
      - `ATTITUDE_DEFENSIVE`
      - `ATTITUDE_NEUTRAL`
      - `ATTITUDE_SPECIAL`
      - `BASE_ITEM_ADHESIVE_GRENADE`
      - `BASE_ITEM_ADRENALINE`
      - `BASE_ITEM_AESTHETIC_ITEM`
      - `BASE_ITEM_ARMOR_CLASS_4`
      - `BASE_ITEM_ARMOR_CLASS_5`
      - `BASE_ITEM_ARMOR_CLASS_6`
      - `BASE_ITEM_ARMOR_CLASS_7`
      - `BASE_ITEM_ARMOR_CLASS_8`
      - `BASE_ITEM_ARMOR_CLASS_9`
      - `BASE_ITEM_BASIC_CLOTHING`
      - `BASE_ITEM_BELT`
      - `BASE_ITEM_BLASTER_CARBINE`
      - `BASE_ITEM_BLASTER_PISTOL`
      - `BASE_ITEM_BLASTER_RIFLE`
      - `BASE_ITEM_BOWCASTER`
      - `BASE_ITEM_COLLAR_LIGHT`
      - `BASE_ITEM_COMBAT_SHOTS`
      - `BASE_ITEM_CREATURE_HIDE_ITEM`
      - `BASE_ITEM_CREATURE_ITEM_PIERCE`
      - `BASE_ITEM_CREATURE_ITEM_SLASH`
      - `BASE_ITEM_CREATURE_WEAPON_SL_PRC`
      - `BASE_ITEM_CREDITS`
      - `BASE_ITEM_CRYOBAN_GRENADE`
      - `BASE_ITEM_DATA_PAD`
      - `BASE_ITEM_DISRUPTER_PISTOL`
      - `BASE_ITEM_DISRUPTER_RIFLE`
      - `BASE_ITEM_DOUBLE_BLADED_LIGHTSABER`
      - `BASE_ITEM_DOUBLE_BLADED_SWORD`
      - `BASE_ITEM_DROID_COMPUTER_SPIKE_MOUNT`
      - `BASE_ITEM_DROID_HEAVY_PLATING`
      - `BASE_ITEM_DROID_LIGHT_PLATING`
      - `BASE_ITEM_DROID_MEDIUM_PLATING`
      - `BASE_ITEM_DROID_MOTION_SENSORS`
      - `BASE_ITEM_DROID_REPAIR_EQUIPMENT`
      - `BASE_ITEM_DROID_SEARCH_SCOPE`
      - `BASE_ITEM_DROID_SECURITY_SPIKE_MOUNT`
      - `BASE_ITEM_DROID_SHIELD`
      - `BASE_ITEM_DROID_SONIC_SENSORS`
      - `BASE_ITEM_DROID_TARGETING_COMPUTERS`
      - `BASE_ITEM_DROID_UTILITY_DEVICE`
      - `BASE_ITEM_FIRE_GRENADE`
      - `BASE_ITEM_FLASH_GRENADE`
      - `BASE_ITEM_FOREARM_BANDS`
      - `BASE_ITEM_FRAGMENTATION_GRENADES`
      - `BASE_ITEM_GAMMOREAN_BATTLEAXE`
      - `BASE_ITEM_GAUNTLETS`
      - `BASE_ITEM_GHAFFI_STICK`
      - `BASE_ITEM_GLOW_ROD`
      - `BASE_ITEM_HEAVY_BLASTER`
      - `BASE_ITEM_HEAVY_REPEATING_BLASTER`
      - `BASE_ITEM_HOLD_OUT_BLASTER`
      - `BASE_ITEM_IMPLANT_1`
      - `BASE_ITEM_IMPLANT_2`
      - `BASE_ITEM_IMPLANT_3`
      - `BASE_ITEM_INVALID`
      - `BASE_ITEM_ION_BLASTER`
      - `BASE_ITEM_ION_GRENADE`
      - `BASE_ITEM_ION_RIFLE`
      - `BASE_ITEM_JEDI_KNIGHT_ROBE`
      - `BASE_ITEM_JEDI_MASTER_ROBE`
      - `BASE_ITEM_JEDI_ROBE`
      - `BASE_ITEM_LIGHTSABER`
      - `BASE_ITEM_LIGHTSABER_CRYSTALS`
      - `BASE_ITEM_LONG_SWORD`
      - `BASE_ITEM_MASK`
      - `BASE_ITEM_MEDICAL_EQUIPMENT`
      - `BASE_ITEM_PLOT_USEABLE_ITEMS`
      - `BASE_ITEM_POISON_GRENADE`
      - `BASE_ITEM_PROGRAMMING_SPIKES`
      - `BASE_ITEM_QUARTER_STAFF`
      - `BASE_ITEM_REPEATING_BLASTER`
      - `BASE_ITEM_SECURITY_SPIKES`
      - `BASE_ITEM_SHORT_LIGHTSABER`
      - `BASE_ITEM_SHORT_SWORD`
      - `BASE_ITEM_SONIC_GRENADE`
      - `BASE_ITEM_SONIC_PISTOL`
      - `BASE_ITEM_SONIC_RIFLE`
      - `BASE_ITEM_STUN_BATON`
      - `BASE_ITEM_STUN_GRENADES`
      - `BASE_ITEM_THERMAL_DETONATOR`
      - `BASE_ITEM_TORCH`
      - `BASE_ITEM_TRAP_KIT`
      - `BASE_ITEM_VIBRO_BLADE`
      - `BASE_ITEM_VIBRO_DOUBLE_BLADE`
      - `BASE_ITEM_VIBRO_SWORD`
      - `BASE_ITEM_WOOKIE_WARBLADE`
      - `BODY_NODE_CHEST`
      - `BODY_NODE_HAND`
      - `BODY_NODE_HAND_LEFT`
      - `BODY_NODE_HAND_RIGHT`
      - `BODY_NODE_HEAD`
      - `CAMERA_MODE_CHASE_CAMERA`
      - `CAMERA_MODE_STIFF_CHASE_CAMERA`
      - `CAMERA_MODE_TOP_DOWN`
      - `COMBAT_MODE_FLURRY_OF_BLOWS`
      - `COMBAT_MODE_IMPROVED_POWER_ATTACK`
      - `COMBAT_MODE_INVALID`
      - `COMBAT_MODE_PARRY`
      - `COMBAT_MODE_POWER_ATTACK`
      - `COMBAT_MODE_RAPID_SHOT`
      - `CONVERSATION_TYPE_CINEMATIC`
      - `CONVERSATION_TYPE_COMPUTER`
      - `CREATURE_SIZE_HUGE`
      - `CREATURE_SIZE_INVALID`
      - `CREATURE_SIZE_LARGE`
      - `CREATURE_SIZE_MEDIUM`
      - `CREATURE_SIZE_SMALL`
      - `CREATURE_SIZE_TINY`
      - `CREATURE_TYPE_CLASS`
      - `CREATURE_TYPE_DOES_NOT_HAVE_SPELL_EFFECT`
      - `CREATURE_TYPE_HAS_SPELL_EFFECT`
      - `CREATURE_TYPE_IS_ALIVE`
      - `CREATURE_TYPE_PERCEPTION`
      - `CREATURE_TYPE_PLAYER_CHAR`
      - `CREATURE_TYPE_RACIAL_TYPE`
      - `CREATURE_TYPE_REPUTATION`
      - `DAMAGE_BONUS_1`
      - `DAMAGE_BONUS_1d10`
      - `DAMAGE_BONUS_1d4`
      - `DAMAGE_BONUS_1d6`
      - `DAMAGE_BONUS_1d8`
      - `DAMAGE_BONUS_2`
      - `DAMAGE_BONUS_2d6`
      - `DAMAGE_BONUS_3`
      - `DAMAGE_BONUS_4`
      - `DAMAGE_BONUS_5`
      - `DAMAGE_POWER_ENERGY`
      - `DAMAGE_POWER_NORMAL`
      - `DAMAGE_POWER_PLUS_FIVE`
      - `DAMAGE_POWER_PLUS_FOUR`
      - `DAMAGE_POWER_PLUS_ONE`
      - `DAMAGE_POWER_PLUS_THREE`
      - `DAMAGE_POWER_PLUS_TWO`
      - `DAMAGE_TYPE_ACID`
      - `DAMAGE_TYPE_BLASTER`
      - `DAMAGE_TYPE_BLUDGEONING`
      - `DAMAGE_TYPE_COLD`
      - `DAMAGE_TYPE_DARK_SIDE`
      - `DAMAGE_TYPE_ELECTRICAL`
      - `DAMAGE_TYPE_FIRE`
      - `DAMAGE_TYPE_ION`
      - `DAMAGE_TYPE_LIGHT_SIDE`
      - `DAMAGE_TYPE_PIERCING`
      - `DAMAGE_TYPE_SLASHING`
      - `DAMAGE_TYPE_SONIC`
      - `DAMAGE_TYPE_UNIVERSAL`
      - `DIRECTION_EAST`
      - `DIRECTION_NORTH`
      - `DIRECTION_SOUTH`
      - `DIRECTION_WEST`
      - `DISGUISE_TYPE_C_BANTHA`
      - `DISGUISE_TYPE_C_BRITH`
      - `DISGUISE_TYPE_C_DEWBACK`
      - `DISGUISE_TYPE_C_DRDASSASSIN`
      - `DISGUISE_TYPE_C_DRDASTRO`
      - `DISGUISE_TYPE_C_DRDG`
      - `DISGUISE_TYPE_C_DRDMKFOUR`
      - `DISGUISE_TYPE_C_DRDMKONE`
      - `DISGUISE_TYPE_C_DRDMKTWO`
      - `DISGUISE_TYPE_C_DRDPROBE`
      - `DISGUISE_TYPE_C_DRDPROT`
      - `DISGUISE_TYPE_C_DRDSENTRY`
      - `DISGUISE_TYPE_C_DRDSPYDER`
      - `DISGUISE_TYPE_C_DRDWAR`
      - `DISGUISE_TYPE_C_FIRIXA`
      - `DISGUISE_TYPE_C_GAMMOREAN`
      - `DISGUISE_TYPE_C_GIZKA`
      - `DISGUISE_TYPE_C_HUTT`
      - `DISGUISE_TYPE_C_IRIAZ`
      - `DISGUISE_TYPE_C_ITHORIAN`
      - `DISGUISE_TYPE_C_JAWA`
      - `DISGUISE_TYPE_C_KATAARN`
      - `DISGUISE_TYPE_C_KHOUNDA`
      - `DISGUISE_TYPE_C_KHOUNDB`
      - `DISGUISE_TYPE_C_KINRATH`
      - `DISGUISE_TYPE_C_KRAYTDRAGON`
      - `DISGUISE_TYPE_C_MYKAL`
      - `DISGUISE_TYPE_C_RAKGHOUL`
      - `DISGUISE_TYPE_C_RANCOR`
      - `DISGUISE_TYPE_C_RONTO`
      - `DISGUISE_TYPE_C_SEABEAST`
      - `DISGUISE_TYPE_C_SELKATH`
      - `DISGUISE_TYPE_C_TACH`
      - `DISGUISE_TYPE_C_TUKATA`
      - `DISGUISE_TYPE_C_TWOHEAD`
      - `DISGUISE_TYPE_C_VERKAAL`
      - `DISGUISE_TYPE_C_WRAID`
      - `DISGUISE_TYPE_COMMONER_FEM_BLACK`
      - `DISGUISE_TYPE_COMMONER_FEM_OLD_ASIAN`
      - `DISGUISE_TYPE_COMMONER_FEM_OLD_BLACK`
      - `DISGUISE_TYPE_COMMONER_FEM_OLD_WHITE`
      - `DISGUISE_TYPE_COMMONER_FEM_WHITE`
      - `DISGUISE_TYPE_COMMONER_MAL_BLACK`
      - `DISGUISE_TYPE_COMMONER_MAL_OLD_ASIAN`
      - `DISGUISE_TYPE_COMMONER_MAL_OLD_BLACK`
      - `DISGUISE_TYPE_COMMONER_MAL_OLD_WHITE`
      - `DISGUISE_TYPE_COMMONER_MAL_WHITE`
      - `DISGUISE_TYPE_CZERKA_OFFICER_BLACK`
      - `DISGUISE_TYPE_CZERKA_OFFICER_OLD_ASIAN`
      - `DISGUISE_TYPE_CZERKA_OFFICER_OLD_BLACK`
      - `DISGUISE_TYPE_CZERKA_OFFICER_OLD_WHITE`
      - `DISGUISE_TYPE_CZERKA_OFFICER_WHITE`
      - `DISGUISE_TYPE_DROID_ASTRO_02`
      - `DISGUISE_TYPE_DROID_ASTRO_03`
      - `DISGUISE_TYPE_DROID_PROTOCOL_02`
      - `DISGUISE_TYPE_DROID_PROTOCOL_03`
      - `DISGUISE_TYPE_DROID_PROTOCOL_04`
      - `DISGUISE_TYPE_DROID_WAR_02`
      - `DISGUISE_TYPE_DROID_WAR_03`
      - `DISGUISE_TYPE_DROID_WAR_04`
      - `DISGUISE_TYPE_DROID_WAR_05`
      - `DISGUISE_TYPE_ENVIRONMENTSUIT`
      - `DISGUISE_TYPE_ENVIRONMENTSUIT_02`
      - `DISGUISE_TYPE_GAMMOREAN_02`
      - `DISGUISE_TYPE_GAMMOREAN_03`
      - `DISGUISE_TYPE_GAMMOREAN_04`
      - `DISGUISE_TYPE_HUTT_02`
      - `DISGUISE_TYPE_HUTT_03`
      - `DISGUISE_TYPE_HUTT_04`
      - `DISGUISE_TYPE_ITHORIAN_02`
      - `DISGUISE_TYPE_ITHORIAN_03`
      - `DISGUISE_TYPE_JEDI_ASIAN_FEMALE_01`
      - `DISGUISE_TYPE_JEDI_ASIAN_FEMALE_02`
      - `DISGUISE_TYPE_JEDI_ASIAN_FEMALE_03`
      - `DISGUISE_TYPE_JEDI_ASIAN_FEMALE_04`
      - `DISGUISE_TYPE_JEDI_ASIAN_FEMALE_05`
      - `DISGUISE_TYPE_JEDI_ASIAN_MALE_01`
      - `DISGUISE_TYPE_JEDI_ASIAN_MALE_02`
      - `DISGUISE_TYPE_JEDI_ASIAN_MALE_03`
      - `DISGUISE_TYPE_JEDI_ASIAN_MALE_04`
      - `DISGUISE_TYPE_JEDI_ASIAN_MALE_05`
      - `DISGUISE_TYPE_JEDI_ASIAN_OLD_FEM`
      - `DISGUISE_TYPE_JEDI_ASIAN_OLD_MALE`
      - `DISGUISE_TYPE_JEDI_BLACK_FEMALE_01`
      - `DISGUISE_TYPE_JEDI_BLACK_FEMALE_02`
      - `DISGUISE_TYPE_JEDI_BLACK_FEMALE_03`
      - `DISGUISE_TYPE_JEDI_BLACK_FEMALE_04`
      - `DISGUISE_TYPE_JEDI_BLACK_FEMALE_05`
      - `DISGUISE_TYPE_JEDI_BLACK_MALE_01`
      - `DISGUISE_TYPE_JEDI_BLACK_MALE_02`
      - `DISGUISE_TYPE_JEDI_BLACK_MALE_03`
      - `DISGUISE_TYPE_JEDI_BLACK_MALE_04`
      - `DISGUISE_TYPE_JEDI_BLACK_MALE_05`
      - `DISGUISE_TYPE_JEDI_BLACK_OLD_FEM`
      - `DISGUISE_TYPE_JEDI_BLACK_OLD_MALE`
      - `DISGUISE_TYPE_JEDI_WHITE_FEMALE_02`
      - `DISGUISE_TYPE_JEDI_WHITE_FEMALE_03`
      - `DISGUISE_TYPE_JEDI_WHITE_FEMALE_04`
      - `DISGUISE_TYPE_JEDI_WHITE_FEMALE_05`
      - `DISGUISE_TYPE_JEDI_WHITE_MALE_02`
      - `DISGUISE_TYPE_JEDI_WHITE_MALE_03`
      - `DISGUISE_TYPE_JEDI_WHITE_MALE_04`
      - `DISGUISE_TYPE_JEDI_WHITE_MALE_05`
      - `DISGUISE_TYPE_JEDI_WHITE_OLD_FEM`
      - `DISGUISE_TYPE_JEDI_WHITE_OLD_MALE`
      - `DISGUISE_TYPE_KATH_HOUND_A02`
      - `DISGUISE_TYPE_KATH_HOUND_A03`
      - `DISGUISE_TYPE_KATH_HOUND_A04`
      - `DISGUISE_TYPE_KATH_HOUND_B02`
      - `DISGUISE_TYPE_KATH_HOUND_B03`
      - `DISGUISE_TYPE_KATH_HOUND_B04`
      - `DISGUISE_TYPE_N_ADMRLSAULKAR`
      - `DISGUISE_TYPE_N_BITH`
      - `DISGUISE_TYPE_N_CALONORD`
      - `DISGUISE_TYPE_N_COMMF`
      - `DISGUISE_TYPE_N_COMMKIDF`
      - `DISGUISE_TYPE_N_COMMKIDM`
      - `DISGUISE_TYPE_N_COMMM`
      - `DISGUISE_TYPE_N_CZERLAOFF`
      - `DISGUISE_TYPE_N_DARKJEDIF`
      - `DISGUISE_TYPE_N_DARKJEDIM`
      - `DISGUISE_TYPE_N_DARTHBAND`
      - `DISGUISE_TYPE_N_DARTHMALAK`
      - `DISGUISE_TYPE_N_DARTHREVAN`
      - `DISGUISE_TYPE_N_DODONNA`
      - `DISGUISE_TYPE_N_DUROS`
      - `DISGUISE_TYPE_N_FATCOMF`
      - `DISGUISE_TYPE_N_FATCOMM`
      - `DISGUISE_TYPE_N_JEDICOUNTF`
      - `DISGUISE_TYPE_N_JEDICOUNTM`
      - `DISGUISE_TYPE_N_JEDIMALEK`
      - `DISGUISE_TYPE_N_JEDIMEMF`
      - `DISGUISE_TYPE_N_JEDIMEMM`
      - `DISGUISE_TYPE_N_MANDALORIAN`
      - `DISGUISE_TYPE_N_RAKATA`
      - `DISGUISE_TYPE_N_REPOFF`
      - `DISGUISE_TYPE_N_REPSOLD`
      - `DISGUISE_TYPE_N_RODIAN`
      - `DISGUISE_TYPE_N_SITHAPPREN`
      - `DISGUISE_TYPE_N_SITHCOMF`
      - `DISGUISE_TYPE_N_SITHCOMM`
      - `DISGUISE_TYPE_N_SITHSOLDIER`
      - `DISGUISE_TYPE_N_SMUGGLER`
      - `DISGUISE_TYPE_N_SWOOPGANG`
      - `DISGUISE_TYPE_N_TUSKEN`
      - `DISGUISE_TYPE_N_TUSKENF`
      - `DISGUISE_TYPE_N_TWILEKF`
      - `DISGUISE_TYPE_N_TWILEKM`
      - `DISGUISE_TYPE_N_WALRUSMAN`
      - `DISGUISE_TYPE_N_WOOKIEF`
      - `DISGUISE_TYPE_N_WOOKIEM`
      - `DISGUISE_TYPE_N_YODA`
      - `DISGUISE_TYPE_P_BASTILLA`
      - `DISGUISE_TYPE_P_CAND`
      - `DISGUISE_TYPE_P_CARTH`
      - `DISGUISE_TYPE_P_FEM_A_LRG_01`
      - `DISGUISE_TYPE_P_FEM_A_LRG_02`
      - `DISGUISE_TYPE_P_FEM_A_LRG_03`
      - `DISGUISE_TYPE_P_FEM_A_LRG_04`
      - `DISGUISE_TYPE_P_FEM_A_LRG_05`
      - `DISGUISE_TYPE_P_FEM_A_MED_01`
      - `DISGUISE_TYPE_P_FEM_A_MED_02`
      - `DISGUISE_TYPE_P_FEM_A_MED_03`
      - `DISGUISE_TYPE_P_FEM_A_MED_04`
      - `DISGUISE_TYPE_P_FEM_A_MED_05`
      - `DISGUISE_TYPE_P_FEM_A_SML_01`
      - `DISGUISE_TYPE_P_FEM_A_SML_02`
      - `DISGUISE_TYPE_P_FEM_A_SML_03`
      - `DISGUISE_TYPE_P_FEM_A_SML_04`
      - `DISGUISE_TYPE_P_FEM_A_SML_05`
      - `DISGUISE_TYPE_P_FEM_B_LRG_01`
      - `DISGUISE_TYPE_P_FEM_B_LRG_02`
      - `DISGUISE_TYPE_P_FEM_B_LRG_03`
      - `DISGUISE_TYPE_P_FEM_B_LRG_04`
      - `DISGUISE_TYPE_P_FEM_B_LRG_05`
      - `DISGUISE_TYPE_P_FEM_B_MED_01`
      - `DISGUISE_TYPE_P_FEM_B_MED_02`
      - `DISGUISE_TYPE_P_FEM_B_MED_03`
      - `DISGUISE_TYPE_P_FEM_B_MED_04`
      - `DISGUISE_TYPE_P_FEM_B_MED_05`
      - `DISGUISE_TYPE_P_FEM_B_SML_01`
      - `DISGUISE_TYPE_P_FEM_B_SML_02`
      - `DISGUISE_TYPE_P_FEM_B_SML_03`
      - `DISGUISE_TYPE_P_FEM_B_SML_04`
      - `DISGUISE_TYPE_P_FEM_B_SML_05`
      - `DISGUISE_TYPE_P_FEM_C_LRG_01`
      - `DISGUISE_TYPE_P_FEM_C_LRG_02`
      - `DISGUISE_TYPE_P_FEM_C_LRG_03`
      - `DISGUISE_TYPE_P_FEM_C_LRG_04`
      - `DISGUISE_TYPE_P_FEM_C_LRG_05`
      - `DISGUISE_TYPE_P_FEM_C_MED_01`
      - `DISGUISE_TYPE_P_FEM_C_MED_02`
      - `DISGUISE_TYPE_P_FEM_C_MED_03`
      - `DISGUISE_TYPE_P_FEM_C_MED_04`
      - `DISGUISE_TYPE_P_FEM_C_MED_05`
      - `DISGUISE_TYPE_P_FEM_C_SML_01`
      - `DISGUISE_TYPE_P_FEM_C_SML_02`
      - `DISGUISE_TYPE_P_FEM_C_SML_03`
      - `DISGUISE_TYPE_P_FEM_C_SML_04`
      - `DISGUISE_TYPE_P_FEM_C_SML_05`
      - `DISGUISE_TYPE_P_HK47`
      - `DISGUISE_TYPE_P_JOLEE`
      - `DISGUISE_TYPE_P_JUHANI`
      - `DISGUISE_TYPE_P_MAL_A_LRG_01`
      - `DISGUISE_TYPE_P_MAL_A_LRG_02`
      - `DISGUISE_TYPE_P_MAL_A_LRG_03`
      - `DISGUISE_TYPE_P_MAL_A_LRG_04`
      - `DISGUISE_TYPE_P_MAL_A_LRG_05`
      - `DISGUISE_TYPE_P_MAL_A_MED_01`
      - `DISGUISE_TYPE_P_MAL_A_MED_02`
      - `DISGUISE_TYPE_P_MAL_A_MED_03`
      - `DISGUISE_TYPE_P_MAL_A_MED_04`
      - `DISGUISE_TYPE_P_MAL_A_MED_05`
      - `DISGUISE_TYPE_P_MAL_A_SML_01`
      - `DISGUISE_TYPE_P_MAL_A_SML_02`
      - `DISGUISE_TYPE_P_MAL_A_SML_03`
      - `DISGUISE_TYPE_P_MAL_A_SML_04`
      - `DISGUISE_TYPE_P_MAL_A_SML_05`
      - `DISGUISE_TYPE_P_MAL_B_LRG_01`
      - `DISGUISE_TYPE_P_MAL_B_LRG_02`
      - `DISGUISE_TYPE_P_MAL_B_LRG_03`
      - `DISGUISE_TYPE_P_MAL_B_LRG_04`
      - `DISGUISE_TYPE_P_MAL_B_LRG_05`
      - `DISGUISE_TYPE_P_MAL_B_MED_01`
      - `DISGUISE_TYPE_P_MAL_B_MED_02`
      - `DISGUISE_TYPE_P_MAL_B_MED_03`
      - `DISGUISE_TYPE_P_MAL_B_MED_04`
      - `DISGUISE_TYPE_P_MAL_B_MED_05`
      - `DISGUISE_TYPE_P_MAL_B_SML_01`
      - `DISGUISE_TYPE_P_MAL_B_SML_02`
      - `DISGUISE_TYPE_P_MAL_B_SML_03`
      - `DISGUISE_TYPE_P_MAL_B_SML_04`
      - `DISGUISE_TYPE_P_MAL_B_SML_05`
      - `DISGUISE_TYPE_P_MAL_C_LRG_01`
      - `DISGUISE_TYPE_P_MAL_C_LRG_02`
      - `DISGUISE_TYPE_P_MAL_C_LRG_03`
      - `DISGUISE_TYPE_P_MAL_C_LRG_04`
      - `DISGUISE_TYPE_P_MAL_C_LRG_05`
      - `DISGUISE_TYPE_P_MAL_C_MED_01`
      - `DISGUISE_TYPE_P_MAL_C_MED_02`
      - `DISGUISE_TYPE_P_MAL_C_MED_03`
      - `DISGUISE_TYPE_P_MAL_C_MED_04`
      - `DISGUISE_TYPE_P_MAL_C_MED_05`
      - `DISGUISE_TYPE_P_MAL_C_SML_01`
      - `DISGUISE_TYPE_P_MAL_C_SML_02`
      - `DISGUISE_TYPE_P_MAL_C_SML_03`
      - `DISGUISE_TYPE_P_MAL_C_SML_04`
      - `DISGUISE_TYPE_P_MAL_C_SML_05`
      - `DISGUISE_TYPE_P_MISSION`
      - `DISGUISE_TYPE_P_T3M3`
      - `DISGUISE_TYPE_P_ZAALBAR`
      - `DISGUISE_TYPE_RAKATA_02`
      - `DISGUISE_TYPE_RAKATA_03`
      - `DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_BLACK`
      - `DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_OLD_ASIAN`
      - `DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_OLD_BLACK`
      - `DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_OLD_WHITE`
      - `DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_BLACK`
      - `DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_OLD_ASIAN`
      - `DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_OLD_BLACK`
      - `DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_OLD_WHITE`
      - `DISGUISE_TYPE_RODIAN_02`
      - `DISGUISE_TYPE_RODIAN_03`
      - `DISGUISE_TYPE_RODIAN_04`
      - `DISGUISE_TYPE_SELKATH_02`
      - `DISGUISE_TYPE_SELKATH_03`
      - `DISGUISE_TYPE_SHYRACK_01`
      - `DISGUISE_TYPE_SHYRACK_02`
      - `DISGUISE_TYPE_SITH_FEM_ASIAN`
      - `DISGUISE_TYPE_SITH_FEM_BLACK`
      - `DISGUISE_TYPE_SITH_FEM_OLD_ASIAN`
      - `DISGUISE_TYPE_SITH_FEM_OLD_BLACK`
      - `DISGUISE_TYPE_SITH_FEM_OLD_WHITE`
      - `DISGUISE_TYPE_SITH_FEM_WHITE`
      - `DISGUISE_TYPE_SITH_MAL_ASIAN`
      - `DISGUISE_TYPE_SITH_MAL_BLACK`
      - `DISGUISE_TYPE_SITH_MAL_OLD_ASIAN`
      - `DISGUISE_TYPE_SITH_MAL_OLD_BLACK`
      - `DISGUISE_TYPE_SITH_MAL_OLD_WHITE`
      - `DISGUISE_TYPE_SITH_MAL_WHITE`
      - `DISGUISE_TYPE_SITH_SOLDIER_03`
      - `DISGUISE_TYPE_SWOOP_GANG_02`
      - `DISGUISE_TYPE_SWOOP_GANG_03`
      - `DISGUISE_TYPE_SWOOP_GANG_04`
      - `DISGUISE_TYPE_SWOOP_GANG_05`
      - `DISGUISE_TYPE_TEST`
      - `DISGUISE_TYPE_TURRET`
      - `DISGUISE_TYPE_TURRET2`
      - `DISGUISE_TYPE_TUSKAN_RAIDER_02`
      - `DISGUISE_TYPE_TUSKAN_RAIDER_03`
      - `DISGUISE_TYPE_TUSKAN_RAIDER_04`
      - `DISGUISE_TYPE_TWILEK_FEMALE_02`
      - `DISGUISE_TYPE_TWILEK_MALE_02`
      - `DISGUISE_TYPE_WOOKIE_FEMALE_02`
      - `DISGUISE_TYPE_WOOKIE_FEMALE_03`
      - `DISGUISE_TYPE_WOOKIE_FEMALE_04`
      - `DISGUISE_TYPE_WOOKIE_FEMALE_05`
      - `DISGUISE_TYPE_WOOKIE_MALE_02`
      - `DISGUISE_TYPE_WOOKIE_MALE_03`
      - `DISGUISE_TYPE_WOOKIE_MALE_04`
      - `DISGUISE_TYPE_WOOKIE_MALE_05`
      - `DISGUISE_TYPE_WRAID_02`
      - `DISGUISE_TYPE_WRAID_03`
      - `DISGUISE_TYPE_WRAID_04`
      - `DISGUISE_TYPE_YUTHURA_BAN`
      - `DOOR_ACTION_BASH`
      - `DOOR_ACTION_IGNORE`
      - `DOOR_ACTION_KNOCK`
      - `DOOR_ACTION_OPEN`
      - `DOOR_ACTION_UNLOCK`
      - `DURATION_TYPE_INSTANT`
      - `DURATION_TYPE_PERMANENT`
      - `DURATION_TYPE_TEMPORARY`
      - `EFFECT_TYPE_ABILITY_DECREASE`
      - `EFFECT_TYPE_ABILITY_INCREASE`
      - `EFFECT_TYPE_AC_DECREASE`
      - `EFFECT_TYPE_AC_INCREASE`
      - `EFFECT_TYPE_ARCANE_SPELL_FAILURE`
      - `EFFECT_TYPE_AREA_OF_EFFECT`
      - `EFFECT_TYPE_ASSUREDDEFLECTION`
      - `EFFECT_TYPE_ASSUREDHIT`
      - `EFFECT_TYPE_ATTACK_DECREASE`
      - `EFFECT_TYPE_ATTACK_INCREASE`
      - `EFFECT_TYPE_BEAM`
      - `EFFECT_TYPE_BLINDNESS`
      - `EFFECT_TYPE_CHARMED`
      - `EFFECT_TYPE_CONCEALMENT`
      - `EFFECT_TYPE_CONFUSED`
      - `EFFECT_TYPE_CURSE`
      - `EFFECT_TYPE_DAMAGE_DECREASE`
      - `EFFECT_TYPE_DAMAGE_IMMUNITY_DECREASE`
      - `EFFECT_TYPE_DAMAGE_IMMUNITY_INCREASE`
      - `EFFECT_TYPE_DAMAGE_INCREASE`
      - `EFFECT_TYPE_DAMAGE_REDUCTION`
      - `EFFECT_TYPE_DAMAGE_RESISTANCE`
      - `EFFECT_TYPE_DARKNESS`
      - `EFFECT_TYPE_DAZED`
      - `EFFECT_TYPE_DEAF`
      - `EFFECT_TYPE_DISEASE`
      - `EFFECT_TYPE_DISGUISE`
      - `EFFECT_TYPE_DISPELMAGICALL`
      - `EFFECT_TYPE_DISPELMAGICBEST`
      - `EFFECT_TYPE_DOMINATED`
      - `EFFECT_TYPE_ELEMENTALSHIELD`
      - `EFFECT_TYPE_ENEMY_ATTACK_BONUS`
      - `EFFECT_TYPE_ENTANGLE`
      - `EFFECT_TYPE_FORCE_RESISTANCE_DECREASE`
      - `EFFECT_TYPE_FORCE_RESISTANCE_INCREASE`
      - `EFFECT_TYPE_FORCEJUMP`
      - `EFFECT_TYPE_FRIGHTENED`
      - `EFFECT_TYPE_HASTE`
      - `EFFECT_TYPE_IMMUNITY`
      - `EFFECT_TYPE_IMPROVEDINVISIBILITY`
      - `EFFECT_TYPE_INVALIDEFFECT`
      - `EFFECT_TYPE_INVISIBILITY`
      - `EFFECT_TYPE_INVULNERABLE`
      - `EFFECT_TYPE_LIGHTSABERTHROW`
      - `EFFECT_TYPE_MISS_CHANCE`
      - `EFFECT_TYPE_MOVEMENT_SPEED_DECREASE`
      - `EFFECT_TYPE_MOVEMENT_SPEED_INCREASE`
      - `EFFECT_TYPE_NEGATIVELEVEL`
      - `EFFECT_TYPE_PARALYZE`
      - `EFFECT_TYPE_POISON`
      - `EFFECT_TYPE_REGENERATE`
      - `EFFECT_TYPE_RESURRECTION`
      - `EFFECT_TYPE_SANCTUARY`
      - `EFFECT_TYPE_SAVING_THROW_DECREASE`
      - `EFFECT_TYPE_SAVING_THROW_INCREASE`
      - `EFFECT_TYPE_SEEINVISIBLE`
      - `EFFECT_TYPE_SILENCE`
      - `EFFECT_TYPE_SKILL_DECREASE`
      - `EFFECT_TYPE_SKILL_INCREASE`
      - `EFFECT_TYPE_SLEEP`
      - `EFFECT_TYPE_SLOW`
      - `EFFECT_TYPE_SPELL_IMMUNITY`
      - `EFFECT_TYPE_SPELLLEVELABSORPTION`
      - `EFFECT_TYPE_STUNNED`
      - `EFFECT_TYPE_TEMPORARY_HITPOINTS`
      - `EFFECT_TYPE_TIMESTOP`
      - `EFFECT_TYPE_TRUESEEING`
      - `EFFECT_TYPE_TURNED`
      - `EFFECT_TYPE_ULTRAVISION`
      - `EFFECT_TYPE_VISUAL`
      - `ENCOUNTER_DIFFICULTY_EASY`
      - `ENCOUNTER_DIFFICULTY_HARD`
      - `ENCOUNTER_DIFFICULTY_IMPOSSIBLE`
      - `ENCOUNTER_DIFFICULTY_NORMAL`
      - `ENCOUNTER_DIFFICULTY_VERY_EASY`
      - `FALSE`
      - `FEAT_ADVANCED_DOUBLE_WEAPON_FIGHTING`
      - `FEAT_ADVANCED_GUARD_STANCE`
      - `FEAT_ADVANCED_JEDI_DEFENSE`
      - `FEAT_AMBIDEXTERITY`
      - `FEAT_ARMOUR_PROF_HEAVY`
      - `FEAT_ARMOUR_PROF_LIGHT`
      - `FEAT_ARMOUR_PROF_MEDIUM`
      - `FEAT_BATTLE_MEDITATION`
      - `FEAT_CAUTIOUS`
      - `FEAT_CRITICAL_STRIKE`
      - `FEAT_DOUBLE_WEAPON_FIGHTING`
      - `FEAT_DROID_UPGRADE_1`
      - `FEAT_DROID_UPGRADE_2`
      - `FEAT_DROID_UPGRADE_3`
      - `FEAT_EMPATHY`
      - `FEAT_FLURRY`
      - `FEAT_FORCE_FOCUS_ADVANCED`
      - `FEAT_FORCE_FOCUS_ALTER`
      - `FEAT_FORCE_FOCUS_CONTROL`
      - `FEAT_FORCE_FOCUS_MASTERY`
      - `FEAT_FORCE_FOCUS_SENSE`
      - `FEAT_GEAR_HEAD`
      - `FEAT_GREAT_FORTITUDE`
      - `FEAT_GUARD_STANCE`
      - `FEAT_IMPLANT_LEVEL_1`
      - `FEAT_IMPLANT_LEVEL_2`
      - `FEAT_IMPLANT_LEVEL_3`
      - `FEAT_IMPROVED_CRITICAL_STRIKE`
      - `FEAT_IMPROVED_FLURRY`
      - `FEAT_IMPROVED_POWER_ATTACK`
      - `FEAT_IMPROVED_POWER_BLAST`
      - `FEAT_IMPROVED_RAPID_SHOT`
      - `FEAT_IMPROVED_SNIPER_SHOT`
      - `FEAT_IRON_WILL`
      - `FEAT_JEDI_DEFENSE`
      - `FEAT_LIGHTNING_REFLEXES`
      - `FEAT_MASTER_CRITICAL_STRIKE`
      - `FEAT_MASTER_GUARD_STANCE`
      - `FEAT_MASTER_JEDI_DEFENSE`
      - `FEAT_MASTER_POWER_ATTACK`
      - `FEAT_MASTER_POWER_BLAST`
      - `FEAT_MASTER_SNIPER_SHOT`
      - `FEAT_MULTI_SHOT`
      - `FEAT_PERCEPTIVE`
      - `FEAT_POWER_ATTACK`
      - `FEAT_POWER_BLAST`
      - `FEAT_PROFICIENCY_ALL`
      - `FEAT_RAPID_SHOT`
      - `FEAT_SKILL_FOCUS_AWARENESS`
      - `FEAT_SKILL_FOCUS_COMPUTER_USE`
      - `FEAT_SKILL_FOCUS_DEMOLITIONS`
      - `FEAT_SKILL_FOCUS_PERSUADE`
      - `FEAT_SKILL_FOCUS_REPAIR`
      - `FEAT_SKILL_FOCUS_SECURITY`
      - `FEAT_SKILL_FOCUS_STEALTH`
      - `FEAT_SKILL_FOCUS_TREAT_INJUURY`
      - `FEAT_SNEAK_ATTACK_10D6`
      - `FEAT_SNEAK_ATTACK_1D6`
      - `FEAT_SNEAK_ATTACK_2D6`
      - `FEAT_SNEAK_ATTACK_3D6`
      - `FEAT_SNEAK_ATTACK_4D6`
      - `FEAT_SNEAK_ATTACK_5D6`
      - `FEAT_SNEAK_ATTACK_6D6`
      - `FEAT_SNEAK_ATTACK_7D6`
      - `FEAT_SNEAK_ATTACK_8D6`
      - `FEAT_SNEAK_ATTACK_9D6`
      - `FEAT_SNIPER_SHOT`
      - `FEAT_TOUGHNESS`
      - `FEAT_UNCANNY_DODGE_1`
      - `FEAT_UNCANNY_DODGE_2`
      - `FEAT_WEAPON_FOCUS_BLASTER`
      - `FEAT_WEAPON_FOCUS_BLASTER_RIFLE`
      - `FEAT_WEAPON_FOCUS_GRENADE`
      - `FEAT_WEAPON_FOCUS_HEAVY_WEAPONS`
      - `FEAT_WEAPON_FOCUS_LIGHTSABER`
      - `FEAT_WEAPON_FOCUS_MELEE_WEAPONS`
      - `FEAT_WEAPON_FOCUS_SIMPLE_WEAPONS`
      - `FEAT_WEAPON_PROFICIENCY_BLASTER`
      - `FEAT_WEAPON_PROFICIENCY_BLASTER_RIFLE`
      - `FEAT_WEAPON_PROFICIENCY_GRENADE`
      - `FEAT_WEAPON_PROFICIENCY_HEAVY_WEAPONS`
      - `FEAT_WEAPON_PROFICIENCY_LIGHTSABER`
      - `FEAT_WEAPON_PROFICIENCY_MELEE_WEAPONS`
      - `FEAT_WEAPON_PROFICIENCY_SIMPLE_WEAPONS`
      - `FEAT_WEAPON_SPECIALIZATION_BLASTER`
      - `FEAT_WEAPON_SPECIALIZATION_BLASTER_RIFLE`
      - `FEAT_WEAPON_SPECIALIZATION_GRENADE`
      - `FEAT_WEAPON_SPECIALIZATION_HEAVY_WEAPONS`
      - `FEAT_WEAPON_SPECIALIZATION_LIGHTSABER`
      - `FEAT_WEAPON_SPECIALIZATION_MELEE_WEAPONS`
      - `FEAT_WEAPON_SPECIALIZATION_SIMPLE_WEAPONS`
      - `FEAT_WHIRLWIND_ATTACK`
      - `FORCE_POWER_AFFECT_MIND`
      - `FORCE_POWER_AFFLICTION`
      - `FORCE_POWER_ALL_FORCE_POWERS`
      - `FORCE_POWER_CHOKE`
      - `FORCE_POWER_CURE`
      - `FORCE_POWER_DEATH_FIELD`
      - `FORCE_POWER_DOMINATE`
      - `FORCE_POWER_DRAIN_LIFE`
      - `FORCE_POWER_DROID_DESTROY`
      - `FORCE_POWER_DROID_DISABLE`
      - `FORCE_POWER_DROID_STUN`
      - `FORCE_POWER_FEAR`
      - `FORCE_POWER_FORCE_ARMOR`
      - `FORCE_POWER_FORCE_AURA`
      - `FORCE_POWER_FORCE_BREACH`
      - `FORCE_POWER_FORCE_IMMUNITY`
      - `FORCE_POWER_FORCE_JUMP`
      - `FORCE_POWER_FORCE_JUMP_ADVANCED`
      - `FORCE_POWER_FORCE_MIND`
      - `FORCE_POWER_FORCE_PUSH`
      - `FORCE_POWER_FORCE_SHIELD`
      - `FORCE_POWER_FORCE_STORM`
      - `FORCE_POWER_FORCE_WAVE`
      - `FORCE_POWER_FORCE_WHIRLWIND`
      - `FORCE_POWER_HEAL`
      - `FORCE_POWER_HOLD`
      - `FORCE_POWER_HORROR`
      - `FORCE_POWER_INSANITY`
      - `FORCE_POWER_KILL`
      - `FORCE_POWER_KNIGHT_MIND`
      - `FORCE_POWER_KNIGHT_SPEED`
      - `FORCE_POWER_LIGHT_SABER_THROW`
      - `FORCE_POWER_LIGHT_SABER_THROW_ADVANCED`
      - `FORCE_POWER_LIGHTNING`
      - `FORCE_POWER_MASTER_ALTER`
      - `FORCE_POWER_MASTER_CONTROL`
      - `FORCE_POWER_MASTER_SENSE`
      - `FORCE_POWER_MIND_MASTERY`
      - `FORCE_POWER_PLAGUE`
      - `FORCE_POWER_REGENERATION`
      - `FORCE_POWER_REGNERATION_ADVANCED`
      - `FORCE_POWER_RESIST_COLD_HEAT_ENERGY`
      - `FORCE_POWER_RESIST_FORCE`
      - `FORCE_POWER_RESIST_POISON_DISEASE_SONIC`
      - `FORCE_POWER_SHOCK`
      - `FORCE_POWER_SLEEP`
      - `FORCE_POWER_SLOW`
      - `FORCE_POWER_SPEED_BURST`
      - `FORCE_POWER_SPEED_MASTERY`
      - `FORCE_POWER_STUN`
      - `FORCE_POWER_SUPRESS_FORCE`
      - `FORCE_POWER_WOUND`
      - `FORMATION_LINE`
      - `FORMATION_WEDGE`
      - `GAME_DIFFICULTY_CORE_RULES`
      - `GAME_DIFFICULTY_DIFFICULT`
      - `GAME_DIFFICULTY_EASY`
      - `GAME_DIFFICULTY_NORMAL`
      - `GAME_DIFFICULTY_VERY_EASY`
      - `GENDER_BOTH`
      - `GENDER_FEMALE`
      - `GENDER_MALE`
      - `GENDER_NONE`
      - `GENDER_OTHER`
      - `GUI_PANEL_PLAYER_DEATH`
      - `IMMUNITY_TYPE_ABILITY_DECREASE`
      - `IMMUNITY_TYPE_AC_DECREASE`
      - `IMMUNITY_TYPE_ATTACK_DECREASE`
      - `IMMUNITY_TYPE_BLINDNESS`
      - `IMMUNITY_TYPE_CHARM`
      - `IMMUNITY_TYPE_CONFUSED`
      - `IMMUNITY_TYPE_CRITICAL_HIT`
      - `IMMUNITY_TYPE_CURSED`
      - `IMMUNITY_TYPE_DAMAGE_DECREASE`
      - `IMMUNITY_TYPE_DAMAGE_IMMUNITY_DECREASE`
      - `IMMUNITY_TYPE_DAZED`
      - `IMMUNITY_TYPE_DEAFNESS`
      - `IMMUNITY_TYPE_DEATH`
      - `IMMUNITY_TYPE_DISEASE`
      - `IMMUNITY_TYPE_DOMINATE`
      - `IMMUNITY_TYPE_ENTANGLE`
      - `IMMUNITY_TYPE_FEAR`
      - `IMMUNITY_TYPE_FORCE_RESISTANCE_DECREASE`
      - `IMMUNITY_TYPE_KNOCKDOWN`
      - `IMMUNITY_TYPE_MIND_SPELLS`
      - `IMMUNITY_TYPE_MOVEMENT_SPEED_DECREASE`
      - `IMMUNITY_TYPE_NEGATIVE_LEVEL`
      - `IMMUNITY_TYPE_NONE`
      - `IMMUNITY_TYPE_PARALYSIS`
      - `IMMUNITY_TYPE_POISON`
      - `IMMUNITY_TYPE_SAVING_THROW_DECREASE`
      - `IMMUNITY_TYPE_SILENCE`
      - `IMMUNITY_TYPE_SKILL_DECREASE`
      - `IMMUNITY_TYPE_SLEEP`
      - `IMMUNITY_TYPE_SLOW`
      - `IMMUNITY_TYPE_SNEAK_ATTACK`
      - `IMMUNITY_TYPE_STUN`
      - `IMMUNITY_TYPE_TRAP`
      - `INVALID_STANDARD_FACTION`
      - `INVISIBILITY_TYPE_DARKNESS`
      - `INVISIBILITY_TYPE_IMPROVED`
      - `INVISIBILITY_TYPE_NORMAL`
      - `ITEM_PROPERTY_ABILITY_BONUS`
      - `ITEM_PROPERTY_AC_BONUS`
      - `ITEM_PROPERTY_AC_BONUS_VS_DAMAGE_TYPE`
      - `ITEM_PROPERTY_AC_BONUS_VS_RACIAL_GROUP`
      - `ITEM_PROPERTY_ACTIVATE_ITEM`
      - `ITEM_PROPERTY_ATTACK_BONUS`
      - `ITEM_PROPERTY_ATTACK_BONUS_VS_RACIAL_GROUP`
      - `ITEM_PROPERTY_ATTACK_PENALTY`
      - `ITEM_PROPERTY_BLASTER_BOLT_DEFLECT_DECREASE`
      - `ITEM_PROPERTY_BLASTER_BOLT_DEFLECT_INCREASE`
      - `ITEM_PROPERTY_BONUS_FEAT`
      - `ITEM_PROPERTY_COMPUTER_SPIKE`
      - `ITEM_PROPERTY_DAMAGE_BONUS`
      - `ITEM_PROPERTY_DAMAGE_BONUS_VS_RACIAL_GROUP`
      - `ITEM_PROPERTY_DAMAGE_REDUCTION`
      - `ITEM_PROPERTY_DAMAGE_RESISTANCE`
      - `ITEM_PROPERTY_DAMAGE_VULNERABILITY`
      - `ITEM_PROPERTY_DECREASED_ABILITY_SCORE`
      - `ITEM_PROPERTY_DECREASED_AC`
      - `ITEM_PROPERTY_DECREASED_ATTACK_MODIFIER`
      - `ITEM_PROPERTY_DECREASED_DAMAGE`
      - `ITEM_PROPERTY_DECREASED_SAVING_THROWS`
      - `ITEM_PROPERTY_DECREASED_SAVING_THROWS_SPECIFIC`
      - `ITEM_PROPERTY_DECREASED_SKILL_MODIFIER`
      - `ITEM_PROPERTY_DROID_REPAIR_KIT`
      - `ITEM_PROPERTY_ENHANCEMENT_BONUS`
      - `ITEM_PROPERTY_ENHANCEMENT_BONUS_VS_RACIAL_GROUP`
      - `ITEM_PROPERTY_EXTRA_MELEE_DAMAGE_TYPE`
      - `ITEM_PROPERTY_EXTRA_RANGED_DAMAGE_TYPE`
      - `ITEM_PROPERTY_FREEDOM_OF_MOVEMENT`
      - `ITEM_PROPERTY_IMMUNITY`
      - `ITEM_PROPERTY_IMMUNITY_DAMAGE_TYPE`
      - `ITEM_PROPERTY_IMPROVED_FORCE_RESISTANCE`
      - `ITEM_PROPERTY_IMPROVED_SAVING_THROW`
      - `ITEM_PROPERTY_IMPROVED_SAVING_THROW_SPECIFIC`
      - `ITEM_PROPERTY_KEEN`
      - `ITEM_PROPERTY_LIGHT`
      - `ITEM_PROPERTY_MASSIVE_CRITICALS`
      - `ITEM_PROPERTY_MIGHTY`
      - `ITEM_PROPERTY_MONSTER_DAMAGE`
      - `ITEM_PROPERTY_NO_DAMAGE`
      - `ITEM_PROPERTY_ON_HIT_PROPERTIES`
      - `ITEM_PROPERTY_ON_MONSTER_HIT`
      - `ITEM_PROPERTY_REGENERATION`
      - `ITEM_PROPERTY_REGENERATION_FORCE_POINTS`
      - `ITEM_PROPERTY_SECURITY_SPIKE`
      - `ITEM_PROPERTY_SKILL_BONUS`
      - `ITEM_PROPERTY_SPECIAL_WALK`
      - `ITEM_PROPERTY_TRAP`
      - `ITEM_PROPERTY_TRUE_SEEING`
      - `ITEM_PROPERTY_UNLIMITED_AMMUNITION`
      - `ITEM_PROPERTY_USE_LIMITATION_CLASS`
      - `ITEM_PROPERTY_USE_LIMITATION_FEAT`
      - `ITEM_PROPERTY_USE_LIMITATION_RACIAL_TYPE`
      - `LIVE_CONTENT_PKG1`
      - `LIVE_CONTENT_PKG2`
      - `LIVE_CONTENT_PKG3`
      - `LIVE_CONTENT_PKG4`
      - `LIVE_CONTENT_PKG5`
      - `LIVE_CONTENT_PKG6`
      - `MOVEMENT_SPEED_DEFAULT`
      - `MOVEMENT_SPEED_DMFAST`
      - `MOVEMENT_SPEED_FAST`
      - `MOVEMENT_SPEED_IMMOBILE`
      - `MOVEMENT_SPEED_NORMAL`
      - `MOVEMENT_SPEED_PC`
      - `MOVEMENT_SPEED_SLOW`
      - `MOVEMENT_SPEED_VERYFAST`
      - `MOVEMENT_SPEED_VERYSLOW`
      - `PARTY_AISTYLE_AGGRESSIVE`
      - `PARTY_AISTYLE_DEFENSIVE`
      - `PARTY_AISTYLE_PASSIVE`
      - `PERCEPTION_HEARD`
      - `PERCEPTION_HEARD_AND_NOT_SEEN`
      - `PERCEPTION_NOT_HEARD`
      - `PERCEPTION_NOT_SEEN`
      - `PERCEPTION_NOT_SEEN_AND_NOT_HEARD`
      - `PERCEPTION_SEEN`
      - `PERCEPTION_SEEN_AND_HEARD`
      - `PERCEPTION_SEEN_AND_NOT_HEARD`
      - `PERSISTENT_ZONE_ACTIVE`
      - `PERSISTENT_ZONE_FOLLOW`
      - `PI`
      - `PLACEABLE_ACTION_BASH`
      - `PLACEABLE_ACTION_KNOCK`
      - `PLACEABLE_ACTION_UNLOCK`
      - `PLACEABLE_ACTION_USE`
      - `PLAYER_CHAR_IS_PC`
      - `PLAYER_CHAR_NOT_PC`
      - `PLOT_O_BIG_MONSTERS`
      - `PLOT_O_DOOM`
      - `PLOT_O_SCARY_STUFF`
      - `POISON_ABILITY_SCORE_AVERAGE`
      - `POISON_ABILITY_SCORE_MILD`
      - `POISON_ABILITY_SCORE_VIRULENT`
      - `POISON_DAMAGE_AVERAGE`
      - `POISON_DAMAGE_MILD`
      - `POISON_DAMAGE_VIRULENT`
      - `POLYMORPH_TYPE_BADGER`
      - `POLYMORPH_TYPE_BALOR`
      - `POLYMORPH_TYPE_BOAR`
      - `POLYMORPH_TYPE_BROWN_BEAR`
      - `POLYMORPH_TYPE_COW`
      - `POLYMORPH_TYPE_DEATH_SLAAD`
      - `POLYMORPH_TYPE_DIRE_BADGER`
      - `POLYMORPH_TYPE_DIRE_BOAR`
      - `POLYMORPH_TYPE_DIRE_BROWN_BEAR`
      - `POLYMORPH_TYPE_DIRE_PANTHER`
      - `POLYMORPH_TYPE_DIRE_WOLF`
      - `POLYMORPH_TYPE_DOOM_KNIGHT`
      - `POLYMORPH_TYPE_ELDER_AIR_ELEMENTAL`
      - `POLYMORPH_TYPE_ELDER_EARTH_ELEMENTAL`
      - `POLYMORPH_TYPE_ELDER_FIRE_ELEMENTAL`
      - `POLYMORPH_TYPE_ELDER_WATER_ELEMENTAL`
      - `POLYMORPH_TYPE_FIRE_GIANT`
      - `POLYMORPH_TYPE_GIANT_SPIDER`
      - `POLYMORPH_TYPE_HUGE_AIR_ELEMENTAL`
      - `POLYMORPH_TYPE_HUGE_EARTH_ELEMENTAL`
      - `POLYMORPH_TYPE_HUGE_FIRE_ELEMENTAL`
      - `POLYMORPH_TYPE_HUGE_WATER_ELEMENTAL`
      - `POLYMORPH_TYPE_IMP`
      - `POLYMORPH_TYPE_IRON_GOLEM`
      - `POLYMORPH_TYPE_PANTHER`
      - `POLYMORPH_TYPE_PENGUIN`
      - `POLYMORPH_TYPE_PIXIE`
      - `POLYMORPH_TYPE_QUASIT`
      - `POLYMORPH_TYPE_RED_DRAGON`
      - `POLYMORPH_TYPE_SUCCUBUS`
      - `POLYMORPH_TYPE_TROLL`
      - `POLYMORPH_TYPE_UMBER_HULK`
      - `POLYMORPH_TYPE_WERECAT`
      - `POLYMORPH_TYPE_WERERAT`
      - `POLYMORPH_TYPE_WEREWOLF`
      - `POLYMORPH_TYPE_WOLF`
      - `POLYMORPH_TYPE_YUANTI`
      - `POLYMORPH_TYPE_ZOMBIE`
      - `PROJECTILE_PATH_TYPE_ACCELERATING`
      - `PROJECTILE_PATH_TYPE_BALLISTIC`
      - `PROJECTILE_PATH_TYPE_DEFAULT`
      - `PROJECTILE_PATH_TYPE_HIGH_BALLISTIC`
      - `PROJECTILE_PATH_TYPE_HOMING`
      - `RACIAL_TYPE_ALL`
      - `RACIAL_TYPE_DROID`
      - `RACIAL_TYPE_ELF`
      - `RACIAL_TYPE_GNOME`
      - `RACIAL_TYPE_HALFELF`
      - `RACIAL_TYPE_HALFLING`
      - `RACIAL_TYPE_HUMAN`
      - `RACIAL_TYPE_INVALID`
      - `RACIAL_TYPE_UNKNOWN`
      - `RADIUS_SIZE_COLOSSAL`
      - `RADIUS_SIZE_GARGANTUAN`
      - `RADIUS_SIZE_HUGE`
      - `RADIUS_SIZE_LARGE`
      - `RADIUS_SIZE_MEDIUM`
      - `RADIUS_SIZE_SMALL`
      - `REPUTATION_TYPE_ENEMY`
      - `REPUTATION_TYPE_FRIEND`
      - `REPUTATION_TYPE_NEUTRAL`
      - `SAVING_THROW_ALL`
      - `SAVING_THROW_FORT`
      - `SAVING_THROW_REFLEX`
      - `SAVING_THROW_TYPE_ACID`
      - `SAVING_THROW_TYPE_ALL`
      - `SAVING_THROW_TYPE_BLASTER`
      - `SAVING_THROW_TYPE_COLD`
      - `SAVING_THROW_TYPE_DARK_SIDE`
      - `SAVING_THROW_TYPE_DEATH`
      - `SAVING_THROW_TYPE_DISEASE`
      - `SAVING_THROW_TYPE_ELECTRICAL`
      - `SAVING_THROW_TYPE_FEAR`
      - `SAVING_THROW_TYPE_FIRE`
      - `SAVING_THROW_TYPE_FORCE_POWER`
      - `SAVING_THROW_TYPE_ION`
      - `SAVING_THROW_TYPE_LIGHT_SIDE`
      - `SAVING_THROW_TYPE_MIND_AFFECTING`
      - `SAVING_THROW_TYPE_NONE`
      - `SAVING_THROW_TYPE_PARALYSIS`
      - `SAVING_THROW_TYPE_POISON`
      - `SAVING_THROW_TYPE_SNEAK_ATTACK`
      - `SAVING_THROW_TYPE_SONIC`
      - `SAVING_THROW_TYPE_TRAP`
      - `SAVING_THROW_WILL`
      - `SHAPE_CONE`
      - `SHAPE_CUBE`
      - `SHAPE_SPELLCONE`
      - `SHAPE_SPELLCYLINDER`
      - `SHAPE_SPHERE`
      - `SHIELD_ANTIQUE_DROID`
      - `SHIELD_DROID_ENERGY_1`
      - `SHIELD_DROID_ENERGY_2`
      - `SHIELD_DROID_ENERGY_3`
      - `SHIELD_DROID_ENVIRO_1`
      - `SHIELD_DROID_ENVIRO_2`
      - `SHIELD_DROID_ENVIRO_3`
      - `SHIELD_DUELING_ECHANI`
      - `SHIELD_DUELING_YUSANIS`
      - `SHIELD_ECHANI`
      - `SHIELD_ENERGY`
      - `SHIELD_ENERGY_ARKANIAN`
      - `SHIELD_ENERGY_SITH`
      - `SHIELD_MANDALORIAN_MELEE`
      - `SHIELD_MANDALORIAN_POWER`
      - `SHIELD_PLOT_TAR_M09AA`
      - `SHIELD_PLOT_UNK_M44AA`
      - `SHIELD_VERPINE_PROTOTYPE`
      - `SKILL_AWARENESS`
      - `SKILL_COMPUTER_USE`
      - `SKILL_DEMOLITIONS`
      - `SKILL_MAX_SKILLS`
      - `SKILL_PERSUADE`
      - `SKILL_REPAIR`
      - `SKILL_SECURITY`
      - `SKILL_STEALTH`
      - `SKILL_TREAT_INJURY`
      - `sLanguage`
      - `SPECIAL_ABILITY_BATTLE_MEDITATION`
      - `SPECIAL_ABILITY_BODY_FUEL`
      - `SPECIAL_ABILITY_CAMOFLAGE`
      - `SPECIAL_ABILITY_CATHAR_REFLEXES`
      - `SPECIAL_ABILITY_COMBAT_REGENERATION`
      - `SPECIAL_ABILITY_DOMINATE_MIND`
      - `SPECIAL_ABILITY_ENHANCED_SENSES`
      - `SPECIAL_ABILITY_PSYCHIC_STANCE`
      - `SPECIAL_ABILITY_RAGE`
      - `SPECIAL_ABILITY_SENTINEL_STANCE`
      - `SPECIAL_ABILITY_TAUNT`
      - `SPECIAL_ABILITY_WARRIOR_STANCE`
      - `SPECIAL_ABILITY_WHIRLING_DERVISH`
      - `SPECIAL_ATTACK_CALLED_SHOT_ARM`
      - `SPECIAL_ATTACK_CALLED_SHOT_LEG`
      - `SPECIAL_ATTACK_DISARM`
      - `SPECIAL_ATTACK_FLURRY_OF_BLOWS`
      - `SPECIAL_ATTACK_IMPROVED_DISARM`
      - `SPECIAL_ATTACK_IMPROVED_KNOCKDOWN`
      - `SPECIAL_ATTACK_INVALID`
      - `SPECIAL_ATTACK_KNOCKDOWN`
      - `SPECIAL_ATTACK_RAPID_SHOT`
      - `SPECIAL_ATTACK_SAP`
      - `SPECIAL_ATTACK_STUNNING_FIST`
      - `STANDARD_FACTION_ENDAR_SPIRE`
      - `STANDARD_FACTION_FRIENDLY_1`
      - `STANDARD_FACTION_FRIENDLY_2`
      - `STANDARD_FACTION_GIZKA_1`
      - `STANDARD_FACTION_GIZKA_2`
      - `STANDARD_FACTION_GLB_XOR`
      - `STANDARD_FACTION_HOSTILE_1`
      - `STANDARD_FACTION_HOSTILE_2`
      - `STANDARD_FACTION_INSANE`
      - `STANDARD_FACTION_NEUTRAL`
      - `STANDARD_FACTION_PREDATOR`
      - `STANDARD_FACTION_PREY`
      - `STANDARD_FACTION_PTAT_TUSKAN`
      - `STANDARD_FACTION_RANCOR`
      - `STANDARD_FACTION_SURRENDER_1`
      - `STANDARD_FACTION_SURRENDER_2`
      - `STANDARD_FACTION_TRAP`
      - `SUBRACE_NONE`
      - `SUBRACE_WOOKIE`
      - `SUBSCREEN_ID_ABILITY`
      - `SUBSCREEN_ID_CHARACTER_RECORD`
      - `SUBSCREEN_ID_EQUIP`
      - `SUBSCREEN_ID_ITEM`
      - `SUBSCREEN_ID_MAP`
      - `SUBSCREEN_ID_MESSAGES`
      - `SUBSCREEN_ID_NONE`
      - `SUBSCREEN_ID_OPTIONS`
      - `SUBSCREEN_ID_QUEST`
      - `SUBSKILL_EXAMINETRAP`
      - `SUBSKILL_FLAGTRAP`
      - `SUBSKILL_RECOVERTRAP`
      - `SUBTYPE_EXTRAORDINARY`
      - `SUBTYPE_MAGICAL`
      - `SUBTYPE_SUPERNATURAL`
      - `SWMINIGAME_TRACKFOLLOWER_SOUND_DEATH`
      - `SWMINIGAME_TRACKFOLLOWER_SOUND_ENGINE`
      - `TALENT_EXCLUDE_ALL_OF_TYPE`
      - `TALENT_TYPE_FEAT`
      - `TALENT_TYPE_FORCE`
      - `TALENT_TYPE_SKILL`
      - `TALENT_TYPE_SPELL`
      - `TALKVOLUME_SHOUT`
      - `TALKVOLUME_SILENT_SHOUT`
      - `TALKVOLUME_SILENT_TALK`
      - `TALKVOLUME_TALK`
      - `TALKVOLUME_WHISPER`
      - `TRAP_BASE_TYPE_FLASH_STUN_AVERAGE`
      - `TRAP_BASE_TYPE_FLASH_STUN_DEADLY`
      - `TRAP_BASE_TYPE_FLASH_STUN_MINOR`
      - `TRAP_BASE_TYPE_FRAGMENTATION_MINE_AVERAGE`
      - `TRAP_BASE_TYPE_FRAGMENTATION_MINE_DEADLY`
      - `TRAP_BASE_TYPE_FRAGMENTATION_MINE_MINOR`
      - `TRAP_BASE_TYPE_LASER_SLICING_AVERAGE`
      - `TRAP_BASE_TYPE_LASER_SLICING_DEADLY`
      - `TRAP_BASE_TYPE_LASER_SLICING_MINOR`
      - `TRAP_BASE_TYPE_POISON_GAS_AVERAGE`
      - `TRAP_BASE_TYPE_POISON_GAS_DEADLY`
      - `TRAP_BASE_TYPE_POISON_GAS_MINOR`
      - `TRUE`
      - `TUTORIAL_WINDOW_RETURN_TO_BASE`
      - `TUTORIAL_WINDOW_START_SWOOP_RACE`
      - `VIDEO_EFFECT_FREELOOK_HK47`
      - `VIDEO_EFFECT_FREELOOK_T3M4`
      - `VIDEO_EFFECT_NONE`
      - `VIDEO_EFFECT_SECURITY_CAMERA`
    - [Planet Constants](#planet-constants)
      - `PLANET_DANTOOINE`
      - `PLANET_EBON_HAWK`
      - `PLANET_KORRIBAN`
      - `PLANET_LIVE_01`
      - `PLANET_LIVE_02`
      - `PLANET_LIVE_03`
      - `PLANET_LIVE_04`
      - `PLANET_LIVE_05`
    - [Visual Effects (VFX)](#visual-effects-vfx)
      - `VFX_ARD_HEAT_SHIMMER`
      - `VFX_ARD_LIGHT_BLIND`
      - `VFX_ARD_LIGHT_YELLOW_10`
      - `VFX_ARD_LIGHT_YELLOW_20`
      - `VFX_BEAM_COLD_RAY`
      - `VFX_BEAM_DEATH_FIELD_TENTACLE`
      - `VFX_BEAM_DRAIN_LIFE`
      - `VFX_BEAM_DROID_DESTROY`
      - `VFX_BEAM_DROID_DISABLE`
      - `VFX_BEAM_FLAME_SPRAY`
      - `VFX_BEAM_ION_RAY_01`
      - `VFX_BEAM_ION_RAY_02`
      - `VFX_BEAM_LIGHTNING_DARK_L`
      - `VFX_BEAM_LIGHTNING_DARK_S`
      - `VFX_BEAM_STUN_RAY`
      - `VFX_COM_BLASTER_DEFLECTION`
      - `VFX_COM_BLASTER_IMPACT`
      - `VFX_COM_BLASTER_IMPACT_GROUND`
      - `VFX_COM_CRITICAL_STRIKE_IMPROVED_SABER`
      - `VFX_COM_CRITICAL_STRIKE_IMPROVED_STAFF`
      - `VFX_COM_CRITICAL_STRIKE_MASTERY_SABER`
      - `VFX_COM_CRITICAL_STRIKE_MASTERY_STAFF`
      - `VFX_COM_DROID_EXPLOSION_1`
      - `VFX_COM_DROID_EXPLOSION_2`
      - `VFX_COM_FLURRY_IMPROVED_SABER`
      - `VFX_COM_FLURRY_IMPROVED_STAFF`
      - `VFX_COM_FORCE_RESISTED`
      - `VFX_COM_JEDI_FORCE_FIZZLE`
      - `VFX_COM_MULTI_SHOT`
      - `VFX_COM_POWER_ATTACK_IMPROVED_SABER`
      - `VFX_COM_POWER_ATTACK_IMPROVED_STAFF`
      - `VFX_COM_POWER_ATTACK_MASTERY_SABER`
      - `VFX_COM_POWER_ATTACK_MASTERY_STAFF`
      - `VFX_COM_POWER_BLAST_IMPROVED`
      - `VFX_COM_POWER_BLAST_MASTERY`
      - `VFX_COM_RAPID_SHOT_IMPROVED`
      - `VFX_COM_SNIPER_SHOT_IMPROVED`
      - `VFX_COM_SNIPER_SHOT_MASTERY`
      - `VFX_COM_SPARKS_BLASTER`
      - `VFX_COM_SPARKS_LARGE`
      - `VFX_COM_SPARKS_LIGHTSABER`
      - `VFX_COM_SPARKS_PARRY_METAL`
      - `VFX_COM_WHIRLWIND_STRIKE_SABER`
      - `VFX_COM_WHIRLWIND_STRIKE_STAFF`
      - `VFX_DUR_BODY_FUAL`
      - `VFX_DUR_CARBONITE_CHUNKS`
      - `VFX_DUR_CARBONITE_ENCASING`
      - `VFX_DUR_FORCE_WHIRLWIND`
      - `VFX_DUR_HOLD`
      - `VFX_DUR_INVISIBILITY`
      - `VFX_DUR_KNIGHTS_SPEED`
      - `VFX_DUR_PSYCHIC_STATIC`
      - `VFX_DUR_SHIELD_BLUE_01`
      - `VFX_DUR_SHIELD_BLUE_02`
      - `VFX_DUR_SHIELD_BLUE_03`
      - `VFX_DUR_SHIELD_BLUE_04`
      - `VFX_DUR_SHIELD_BLUE_MARK_I`
      - `VFX_DUR_SHIELD_BLUE_MARK_II`
      - `VFX_DUR_SHIELD_BLUE_MARK_IV`
      - `VFX_DUR_SHIELD_CHROME_01`
      - `VFX_DUR_SHIELD_CHROME_02`
      - `VFX_DUR_SHIELD_GREEN_01`
      - `VFX_DUR_SHIELD_RED_01`
      - `VFX_DUR_SHIELD_RED_02`
      - `VFX_DUR_SHIELD_RED_MARK_I`
      - `VFX_DUR_SHIELD_RED_MARK_II`
      - `VFX_DUR_SHIELD_RED_MARK_IV`
      - `VFX_DUR_SPEED`
      - `VFX_DUR_STEALTH_PULSE`
      - `VFX_FNF_FORCE_WAVE`
      - `VFX_FNF_GRAVITY_GENERATOR`
      - `VFX_FNF_GRENADE_ADHESIVE`
      - `VFX_FNF_GRENADE_CRYOBAN`
      - `VFX_FNF_GRENADE_FRAGMENTATION`
      - `VFX_FNF_GRENADE_ION`
      - `VFX_FNF_GRENADE_PLASMA`
      - `VFX_FNF_GRENADE_POISON`
      - `VFX_FNF_GRENADE_SONIC`
      - `VFX_FNF_GRENADE_STUN`
      - `VFX_FNF_GRENADE_THERMAL_DETONATOR`
      - `VFX_FNF_PLOT_MAN_SONIC_WAVE`
      - `VFX_IMP_CHOKE`
      - `VFX_IMP_CURE`
      - `VFX_IMP_FLAME`
      - `VFX_IMP_FORCE_BREACH`
      - `VFX_IMP_FORCE_JUMP_ADVANCED`
      - `VFX_IMP_FORCE_PUSH`
      - `VFX_IMP_FORCE_WAVE`
      - `VFX_IMP_FORCE_WHIRLWIND`
      - `VFX_IMP_GRENADE_ADHESIVE_PERSONAL`
      - `VFX_IMP_HEAL`
      - `VFX_IMP_HEALING_SMALL`
      - `VFX_IMP_MIND_FORCE`
      - `VFX_IMP_MIND_KINIGHT`
      - `VFX_IMP_MIND_MASTERY`
      - `VFX_IMP_MIRV`
      - `VFX_IMP_MIRV_IMPACT`
      - `VFX_IMP_SCREEN_SHAKE`
      - `VFX_IMP_SPEED_KNIGHT`
      - `VFX_IMP_SPEED_MASTERY`
      - `VFX_IMP_STUN`
      - `VFX_IMP_SUPPRESS_FORCE`
      - `VFX_NONE`
      - `VFX_PRO_AFFLICT`
      - `VFX_PRO_DEATH_FIELD`
      - `VFX_PRO_DRAIN`
      - `VFX_PRO_DROID_DISABLE`
      - `VFX_PRO_DROID_KILL`
      - `VFX_PRO_FORCE_ARMOR`
      - `VFX_PRO_FORCE_AURA`
      - `VFX_PRO_FORCE_SHIELD`
      - `VFX_PRO_LIGHTNING_JEDI`
      - `VFX_PRO_LIGHTNING_L`
      - `VFX_PRO_LIGHTNING_L_SOUND`
      - `VFX_PRO_LIGHTNING_S`
      - `VFX_PRO_RESIST_ELEMENTS`
      - `VFX_PRO_RESIST_FORCE`
      - `VFX_PRO_RESIST_POISON`
  - [K1-Only Constants](#k1-only-constants)
    - NPC Constants
      - `NPC_BASTILA`
      - `NPC_CARTH`
      - `NPC_JOLEE`
      - `NPC_JUHANI`
      - `NPC_MISSION`
      - `NPC_ZAALBAR`
    - Other Constants
      - `TUTORIAL_WINDOW_MOVEMENT_KEYS`
    - Planet Constants
      - `PLANET_ENDAR_SPIRE`
      - `PLANET_KASHYYYK`
      - `PLANET_LEVIATHAN`
      - `PLANET_MANAAN`
      - `PLANET_STAR_FORGE`
      - `PLANET_TARIS`
      - `PLANET_TATOOINE`
      - `PLANET_UNKNOWN_WORLD`
  - [TSL-Only Constants](#tsl-only-constants)
    - Class Type Constants
      - `CLASS_TYPE_BOUNTYHUNTER`
      - `CLASS_TYPE_JEDIMASTER`
      - `CLASS_TYPE_JEDIWATCHMAN`
      - `CLASS_TYPE_JEDIWEAPONMASTER`
      - `CLASS_TYPE_SITHASSASSIN`
      - `CLASS_TYPE_SITHLORD`
      - `CLASS_TYPE_SITHMARAUDER`
      - `CLASS_TYPE_TECHSPECIALIST`
    - Inventory Constants
      - `INVENTORY_SLOT_LEFTWEAPON2`
      - `INVENTORY_SLOT_RIGHTWEAPON2`
    - NPC Constants
      - `NPC_AISTYLE_HEALER`
      - `NPC_AISTYLE_MONSTER_POWERS`
      - `NPC_AISTYLE_PARTY_AGGRO`
      - `NPC_AISTYLE_PARTY_DEFENSE`
      - `NPC_AISTYLE_PARTY_RANGED`
      - `NPC_AISTYLE_PARTY_REMOTE`
      - `NPC_AISTYLE_PARTY_STATIONARY`
      - `NPC_AISTYLE_PARTY_SUPPORT`
      - `NPC_AISTYLE_SKIRMISH`
      - `NPC_AISTYLE_TURTLE`
      - `NPC_ATTON`
      - `NPC_BAO_DUR`
      - `NPC_DISCIPLE`
      - `NPC_G0T0`
      - `NPC_HANDMAIDEN`
      - `NPC_HANHARR`
      - `NPC_KREIA`
      - `NPC_MIRA`
      - `NPC_VISAS`
    - Other Constants
      - `ACTION_FOLLOWOWNER`
      - `AI_LEVEL_HIGH`
      - `AI_LEVEL_LOW`
      - `AI_LEVEL_NORMAL`
      - `AI_LEVEL_VERY_HIGH`
      - `AI_LEVEL_VERY_LOW`
      - `ANIMATION_FIREFORGET_DIVE_ROLL`
      - `ANIMATION_FIREFORGET_FORCE_CAST`
      - `ANIMATION_FIREFORGET_OPEN`
      - `ANIMATION_FIREFORGET_SCREAM`
      - `ANIMATION_LOOPING_CHECK_BODY`
      - `ANIMATION_LOOPING_CHOKE_WORKING`
      - `ANIMATION_LOOPING_CLOSED`
      - `ANIMATION_LOOPING_MEDITATE_STAND`
      - `ANIMATION_LOOPING_RAGE`
      - `ANIMATION_LOOPING_SIT_AND_MEDITATE`
      - `ANIMATION_LOOPING_SIT_CHAIR`
      - `ANIMATION_LOOPING_SIT_CHAIR_COMP1`
      - `ANIMATION_LOOPING_SIT_CHAIR_COMP2`
      - `ANIMATION_LOOPING_SIT_CHAIR_DRINK`
      - `ANIMATION_LOOPING_SIT_CHAIR_PAZAK`
      - `ANIMATION_LOOPING_STEALTH`
      - `ANIMATION_LOOPING_UNLOCK_DOOR`
      - `BASE_ITEM_FORCE_PIKE`
      - `BASE_ITEM_WRIST_LAUNCHER`
      - `EFFECT_TYPE_DROID_CONFUSED`
      - `EFFECT_TYPE_DROIDSCRAMBLE`
      - `EFFECT_TYPE_MINDTRICK`
      - `FEAT_CLASS_SKILL_AWARENESS`
      - `FEAT_CLASS_SKILL_COMPUTER_USE`
      - `FEAT_CLASS_SKILL_DEMOLITIONS`
      - `FEAT_CLASS_SKILL_REPAIR`
      - `FEAT_CLASS_SKILL_SECURITY`
      - `FEAT_CLASS_SKILL_STEALTH`
      - `FEAT_CLASS_SKILL_TREAT_INJURY`
      - `FEAT_CLOSE_COMBAT`
      - `FEAT_CRAFT`
      - `FEAT_DARK_SIDE_CORRUPTION`
      - `FEAT_DEFLECT`
      - `FEAT_DROID_INTERFACE`
      - `FEAT_DUAL_STRIKE`
      - `FEAT_EVASION`
      - `FEAT_FIGHTING_SPIRIT`
      - `FEAT_FINESSE_LIGHTSABERS`
      - `FEAT_FINESSE_MELEE_WEAPONS`
      - `FEAT_FORCE_CHAIN`
      - `FEAT_HEROIC_RESOLVE`
      - `FEAT_IGNORE_PAIN_1`
      - `FEAT_IGNORE_PAIN_2`
      - `FEAT_IGNORE_PAIN_3`
      - `FEAT_IMPLANT_SWITCHING`
      - `FEAT_IMPROVED_CLOSE_COMBAT`
      - `FEAT_IMPROVED_DUAL_STRIKE`
      - `FEAT_IMPROVED_FORCE_CAMOUFLAGE`
      - `FEAT_IMPROVED_PRECISE_SHOT`
      - `FEAT_INCREASE_COMBAT_DAMAGE_1`
      - `FEAT_INCREASE_COMBAT_DAMAGE_2`
      - `FEAT_INCREASE_COMBAT_DAMAGE_3`
      - `FEAT_INCREASE_MELEE_DAMAGE_1`
      - `FEAT_INCREASE_MELEE_DAMAGE_2`
      - `FEAT_INCREASE_MELEE_DAMAGE_3`
      - `FEAT_INNER_STRENGTH_1`
      - `FEAT_INNER_STRENGTH_2`
      - `FEAT_INNER_STRENGTH_3`
      - `FEAT_KINETIC_COMBAT`
      - `FEAT_LIGHT_SIDE_ENLIGHTENMENT`
      - `FEAT_MANDALORIAN_COURAGE`
      - `FEAT_MASTER_DUAL_STRIKE`
      - `FEAT_MASTER_FORCE_CAMOUFLAGE`
      - `FEAT_MASTER_PRECISE_SHOT`
      - `FEAT_MASTERCRAFT_ARMOR_1`
      - `FEAT_MASTERCRAFT_ARMOR_2`
      - `FEAT_MASTERCRAFT_ARMOR_3`
      - `FEAT_MASTERCRAFT_WEAPONS_1`
      - `FEAT_MASTERCRAFT_WEAPONS_2`
      - `FEAT_MASTERCRAFT_WEAPONS_3`
      - `FEAT_MENTOR`
      - `FEAT_MOBILITY`
      - `FEAT_PERSONAL_CLOAKING_SHIELD`
      - `FEAT_PRECISE_SHOT`
      - `FEAT_PRECISE_SHOT_IV`
      - `FEAT_PRECISE_SHOT_V`
      - `FEAT_REGENERATE_FORCE_POINTS`
      - `FEAT_REGENERATE_VITALITY_POINTS`
      - `FEAT_SPIRIT`
      - `FEAT_STEALTH_RUN`
      - `FEAT_SUPERIOR_WEAPON_FOCUS_LIGHTSABER_1`
      - `FEAT_SUPERIOR_WEAPON_FOCUS_LIGHTSABER_2`
      - `FEAT_SUPERIOR_WEAPON_FOCUS_LIGHTSABER_3`
      - `FEAT_SUPERIOR_WEAPON_FOCUS_TWO_WEAPON_1`
      - `FEAT_SUPERIOR_WEAPON_FOCUS_TWO_WEAPON_2`
      - `FEAT_SUPERIOR_WEAPON_FOCUS_TWO_WEAPON_3`
      - `FEAT_SURVIVAL`
      - `FEAT_TARGETING_1`
      - `FEAT_TARGETING_10`
      - `FEAT_TARGETING_2`
      - `FEAT_TARGETING_3`
      - `FEAT_TARGETING_4`
      - `FEAT_TARGETING_5`
      - `FEAT_TARGETING_6`
      - `FEAT_TARGETING_7`
      - `FEAT_TARGETING_8`
      - `FEAT_TARGETING_9`
      - `FEAT_WAR_VETERAN`
      - `FORCE_POWER_BAT_MED_ENEMY`
      - `FORCE_POWER_BATTLE_MEDITATION_PC`
      - `FORCE_POWER_BATTLE_PRECOGNITION`
      - `FORCE_POWER_BEAST_CONFUSION`
      - `FORCE_POWER_BEAST_TRICK`
      - `FORCE_POWER_BREATH_CONTROL`
      - `FORCE_POWER_CONFUSION`
      - `FORCE_POWER_CRUSH_OPPOSITION_I`
      - `FORCE_POWER_CRUSH_OPPOSITION_II`
      - `FORCE_POWER_CRUSH_OPPOSITION_III`
      - `FORCE_POWER_CRUSH_OPPOSITION_IV`
      - `FORCE_POWER_CRUSH_OPPOSITION_V`
      - `FORCE_POWER_CRUSH_OPPOSITION_VI`
      - `FORCE_POWER_DRAIN_FORCE`
      - `FORCE_POWER_DROID_CONFUSION`
      - `FORCE_POWER_DROID_TRICK`
      - `FORCE_POWER_FORCE_BARRIER`
      - `FORCE_POWER_FORCE_BODY`
      - `FORCE_POWER_FORCE_CAMOUFLAGE`
      - `FORCE_POWER_FORCE_CRUSH`
      - `FORCE_POWER_FORCE_ENLIGHTENMENT`
      - `FORCE_POWER_FORCE_REDIRECTION`
      - `FORCE_POWER_FORCE_REPULSION`
      - `FORCE_POWER_FORCE_SCREAM`
      - `FORCE_POWER_FORCE_SIGHT`
      - `FORCE_POWER_FURY`
      - `FORCE_POWER_IMP_BAT_MED_ENEMY`
      - `FORCE_POWER_IMPROVED_BATTLE_MEDITATION_PC`
      - `FORCE_POWER_IMPROVED_DRAIN_FORCE`
      - `FORCE_POWER_IMPROVED_FORCE_BARRIER`
      - `FORCE_POWER_IMPROVED_FORCE_BODY`
      - `FORCE_POWER_IMPROVED_FORCE_CAMOUFLAGE`
      - `FORCE_POWER_IMPROVED_FORCE_SCREAM`
      - `FORCE_POWER_IMPROVED_FURY`
      - `FORCE_POWER_IMPROVED_REVITALIZE`
      - `FORCE_POWER_INSPIRE_FOLLOWERS_I`
      - `FORCE_POWER_INSPIRE_FOLLOWERS_II`
      - `FORCE_POWER_INSPIRE_FOLLOWERS_III`
      - `FORCE_POWER_INSPIRE_FOLLOWERS_IV`
      - `FORCE_POWER_INSPIRE_FOLLOWERS_V`
      - `FORCE_POWER_INSPIRE_FOLLOWERS_VI`
      - `FORCE_POWER_MAS_BAT_MED_ENEMY`
      - `FORCE_POWER_MASTER_BATTLE_MEDITATION_PC`
      - `FORCE_POWER_MASTER_DRAIN_FORCE`
      - `FORCE_POWER_MASTER_ENERGY_RESISTANCE`
      - `FORCE_POWER_MASTER_FORCE_BARRIER`
      - `FORCE_POWER_MASTER_FORCE_BODY`
      - `FORCE_POWER_MASTER_FORCE_CAMOUFLAGE`
      - `FORCE_POWER_MASTER_FORCE_SCREAM`
      - `FORCE_POWER_MASTER_FURY`
      - `FORCE_POWER_MASTER_HEAL`
      - `FORCE_POWER_MASTER_REVITALIZE`
      - `FORCE_POWER_MIND_TRICK`
      - `FORCE_POWER_PRECOGNITION`
      - `FORCE_POWER_REVITALIZE`
      - `FORCE_POWER_WOOKIEE_RAGE_I`
      - `FORCE_POWER_WOOKIEE_RAGE_II`
      - `FORCE_POWER_WOOKIEE_RAGE_III`
      - `FORFEIT_DXUN_SWORD_ONLY`
      - `FORFEIT_NO_ARMOR`
      - `FORFEIT_NO_FORCE_POWERS`
      - `FORFEIT_NO_ITEM_BUT_SHIELD`
      - `FORFEIT_NO_ITEMS`
      - `FORFEIT_NO_LIGHTSABER`
      - `FORFEIT_NO_RANGED`
      - `FORFEIT_NO_WEAPONS`
      - `FORM_FORCE_I_FOCUS`
      - `FORM_FORCE_II_POTENCY`
      - `FORM_FORCE_III_AFFINITY`
      - `FORM_FORCE_IV_MASTERY`
      - `FORM_SABER_I_SHII_CHO`
      - `FORM_SABER_II_MAKASHI`
      - `FORM_SABER_III_SORESU`
      - `FORM_SABER_IV_ATARU`
      - `FORM_SABER_V_SHIEN`
      - `FORM_SABER_VI_NIMAN`
      - `FORM_SABER_VII_JUYO`
      - `IMMUNITY_TYPE_DROID_CONFUSED`
      - `IMPLANT_AGI`
      - `IMPLANT_END`
      - `IMPLANT_NONE`
      - `IMPLANT_REGEN`
      - `IMPLANT_STR`
      - `ITEM_PROPERTY_DAMPEN_SOUND`
      - `ITEM_PROPERTY_DISGUISE`
      - `ITEM_PROPERTY_DOORCUTTING`
      - `ITEM_PROPERTY_DOORSABERING`
      - `ITEM_PROPERTY_LIMIT_USE_BY_GENDER`
      - `ITEM_PROPERTY_LIMIT_USE_BY_PC`
      - `ITEM_PROPERTY_LIMIT_USE_BY_SUBRACE`
      - `POISON_ABILITY_AND_DAMAGE_AVERAGE`
      - `POISON_ABILITY_AND_DAMAGE_VIRULENT`
      - `POISON_DAMAGE_KYBER_DART`
      - `POISON_DAMAGE_KYBER_DART_HALF`
      - `POISON_DAMAGE_NORMAL_DART`
      - `POISON_DAMAGE_ROCKET`
      - `PUP_OTHER1`
      - `PUP_OTHER2`
      - `PUP_SENSORBALL`
      - `SHIELD_DREXL`
      - `SHIELD_HEAT`
      - `SHIELD_PLOT_MAN_M28AA`
      - `STANDARD_FACTION_ONE_ON_ONE`
      - `STANDARD_FACTION_PARTYPUPPET`
      - `STANDARD_FACTION_SELF_LOATHING`
      - `TRAP_BASE_TYPE_FLASH_STUN_DEVASTATING`
      - `TRAP_BASE_TYPE_FLASH_STUN_STRONG`
      - `TRAP_BASE_TYPE_FRAGMENTATION_MINE_DEVASTATING`
      - `TRAP_BASE_TYPE_FRAGMENTATION_MINE_STRONG`
      - `TRAP_BASE_TYPE_LASER_SLICING_DEVASTATING`
      - `TRAP_BASE_TYPE_LASER_SLICING_STRONG`
      - `TRAP_BASE_TYPE_POISON_GAS_DEVASTATING`
      - `TRAP_BASE_TYPE_POISON_GAS_STRONG`
      - `TRAP_BASE_TYPE_SONIC_CHARGE_AVERAGE`
      - `TRAP_BASE_TYPE_SONIC_CHARGE_DEADLY`
      - `TRAP_BASE_TYPE_SONIC_CHARGE_DEVASTATING`
      - `TRAP_BASE_TYPE_SONIC_CHARGE_MINOR`
      - `TRAP_BASE_TYPE_SONIC_CHARGE_STRONG`
      - `TUTORIAL_WINDOW_TEMP1`
      - `TUTORIAL_WINDOW_TEMP10`
      - `TUTORIAL_WINDOW_TEMP11`
      - `TUTORIAL_WINDOW_TEMP12`
      - `TUTORIAL_WINDOW_TEMP13`
      - `TUTORIAL_WINDOW_TEMP14`
      - `TUTORIAL_WINDOW_TEMP15`
      - `TUTORIAL_WINDOW_TEMP2`
      - `TUTORIAL_WINDOW_TEMP3`
      - `TUTORIAL_WINDOW_TEMP4`
      - `TUTORIAL_WINDOW_TEMP5`
      - `TUTORIAL_WINDOW_TEMP6`
      - `TUTORIAL_WINDOW_TEMP7`
      - `TUTORIAL_WINDOW_TEMP8`
      - `TUTORIAL_WINDOW_TEMP9`
      - `VIDEO_EFFECT_CLAIRVOYANCE`
      - `VIDEO_EFFECT_CLAIRVOYANCEFULL`
      - `VIDEO_EFFECT_FORCESIGHT`
      - `VIDEO_EFFECT_FURY_1`
      - `VIDEO_EFFECT_FURY_2`
      - `VIDEO_EFFECT_FURY_3`
      - `VIDEO_EFFECT_VISAS_FREELOOK`
      - `VIDEO_FFECT_SECURITY_NO_LABEL`
    - Planet Constants
      - `PLANET_DXUN`
      - `PLANET_HARBINGER`
      - `PLANET_LIVE_06`
      - `PLANET_M4_78`
      - `PLANET_MALACHOR_V`
      - `PLANET_NAR_SHADDAA`
      - `PLANET_ONDERON`
      - `PLANET_PERAGUS`
      - `PLANET_TELOS`
    - Visual Effects (VFX)
      - `VFX_DUR_ELECTRICAL_SPARK`
      - `VFX_DUR_HOLO_PROJECT`
  - [KOTOR Library Files](#kotor-library-files)
    - [`k_inc_cheat`](#k_inc_cheat)
    - [`k_inc_dan`](#k_inc_dan)
    - [`k_inc_debug`](#k_inc_debug)
    - [`k_inc_drop`](#k_inc_drop)
    - [`k_inc_ebonhawk`](#k_inc_ebonhawk)
    - [`k_inc_end`](#k_inc_end)
    - [`k_inc_endgame`](#k_inc_endgame)
    - [`k_inc_force`](#k_inc_force)
    - [`k_inc_generic`](#k_inc_generic)
    - [`k_inc_gensupport`](#k_inc_gensupport)
    - [`k_inc_kas`](#k_inc_kas)
    - [`k_inc_lev`](#k_inc_lev)
    - [`k_inc_man`](#k_inc_man)
    - [`k_inc_stunt`](#k_inc_stunt)
    - [`k_inc_switch`](#k_inc_switch)
    - [`k_inc_tar`](#k_inc_tar)
    - [`k_inc_tat`](#k_inc_tat)
    - [`k_inc_treasure`](#k_inc_treasure)
    - [`k_inc_unk`](#k_inc_unk)
    - [`k_inc_utility`](#k_inc_utility)
    - [`k_inc_walkways`](#k_inc_walkways)
    - [`k_inc_zone`](#k_inc_zone)
  - [TSL Library Files](#tsl-library-files)
    - [`a_global_inc`](#a_global_inc)
    - [`a_influence_inc`](#a_influence_inc)
    - [`a_localn_inc`](#a_localn_inc)
    - `k_inc_cheat`
    - `k_inc_debug`
    - [`k_inc_disguise`](#k_inc_disguise)
    - `k_inc_drop`
    - [`k_inc_fab`](#k_inc_fab)
    - [`k_inc_fakecombat`](#k_inc_fakecombat)
    - `k_inc_force`
    - `k_inc_generic`
    - `k_inc_gensupport`
    - [`k_inc_glob_party`](#k_inc_glob_party)
    - [`k_inc_hawk`](#k_inc_hawk)
    - [`k_inc_item_gen`](#k_inc_item_gen)
    - [`k_inc_npckill`](#k_inc_npckill)
    - [`k_inc_q_crystal`](#k_inc_q_crystal)
    - [`k_inc_quest_hk`](#k_inc_quest_hk)
    - `k_inc_switch`
    - [`k_inc_treas_k2`](#k_inc_treas_k2)
    - `k_inc_treasure`
    - `k_inc_utility`
    - `k_inc_walkways`
    - `k_inc_zone`
    - [`k_oei_hench_inc`](#k_oei_hench_inc)
  - [Compilation Process](#compilation-process)
    - [Attempts to Uncomment or Modify](#attempts-to-uncomment-or-modify)
    - [Commented-Out Elements in nwscript.nss](#commented-out-elements-in-nwscriptnss)
    - [Common Modder Workarounds](#common-modder-workarounds)
    - [Forum Discussions and Community Knowledge](#forum-discussions-and-community-knowledge)
    - [Key Citations](#key-citations)
    - [Key Examples of Commented Elements](#key-examples-of-commented-elements)
    - [Reasons for Commented-Out Elements](#reasons-for-commented-out-elements)
  - [Reference Implementations](#reference-implementations)
    - Other Constants
      - `TRUE` **(K1 \& TSL)**
      - `FALSE` **(K1 \& TSL)**
      - `PI` **(K1 \& TSL)**
      - `ATTITUDE_NEUTRAL` **(K1 \& TSL)**
      - `ATTITUDE_AGGRESSIVE` **(K1 \& TSL)**
      - `ATTITUDE_DEFENSIVE` **(K1 \& TSL)**
      - `ATTITUDE_SPECIAL` **(K1 \& TSL)**
      - `RADIUS_SIZE_SMALL` **(K1 \& TSL)**
      - `RADIUS_SIZE_MEDIUM` **(K1 \& TSL)**
      - `RADIUS_SIZE_LARGE` **(K1 \& TSL)**
      - `RADIUS_SIZE_HUGE` **(K1 \& TSL)**
      - `RADIUS_SIZE_GARGANTUAN` **(K1 \& TSL)**
      - `RADIUS_SIZE_COLOSSAL` **(K1 \& TSL)**
      - `ATTACK_RESULT_INVALID` **(K1 \& TSL)**
      - `ATTACK_RESULT_HIT_SUCCESSFUL` **(K1 \& TSL)**
      - `ATTACK_RESULT_CRITICAL_HIT` **(K1 \& TSL)**
      - `ATTACK_RESULT_AUTOMATIC_HIT` **(K1 \& TSL)**
      - `ATTACK_RESULT_MISS` **(K1 \& TSL)**
      - `ATTACK_RESULT_ATTACK_RESISTED` **(K1 \& TSL)**
      - `ATTACK_RESULT_ATTACK_FAILED` **(K1 \& TSL)**
      - `ATTACK_RESULT_PARRIED` **(K1 \& TSL)**
      - `ATTACK_RESULT_DEFLECTED` **(K1 \& TSL)**
      - `AOE_PER_FOGACID` **(K1 \& TSL)**
      - `AOE_PER_FOGFIRE` **(K1 \& TSL)**
      - `AOE_PER_FOGSTINK` **(K1 \& TSL)**
      - `AOE_PER_FOGKILL` **(K1 \& TSL)**
      - `AOE_PER_FOGMIND` **(K1 \& TSL)**
      - `AOE_PER_WALLFIRE` **(K1 \& TSL)**
      - `AOE_PER_WALLWIND` **(K1 \& TSL)**
      - `AOE_PER_WALLBLADE` **(K1 \& TSL)**
      - `AOE_PER_WEB` **(K1 \& TSL)**
      - `AOE_PER_ENTANGLE` **(K1 \& TSL)**
      - `AOE_PER_DARKNESS` **(K1 \& TSL)**
      - `AOE_MOB_CIRCEVIL` **(K1 \& TSL)**
      - `AOE_MOB_CIRCGOOD` **(K1 \& TSL)**
      - `AOE_MOB_CIRCLAW` **(K1 \& TSL)**
      - `AOE_MOB_CIRCCHAOS` **(K1 \& TSL)**
      - `AOE_MOB_FEAR` **(K1 \& TSL)**
      - `AOE_MOB_BLINDING` **(K1 \& TSL)**
      - `AOE_MOB_UNEARTHLY` **(K1 \& TSL)**
      - `AOE_MOB_MENACE` **(K1 \& TSL)**
      - `AOE_MOB_UNNATURAL` **(K1 \& TSL)**
      - `AOE_MOB_STUN` **(K1 \& TSL)**
      - `AOE_MOB_PROTECTION` **(K1 \& TSL)**
      - `AOE_MOB_FIRE` **(K1 \& TSL)**
      - `AOE_MOB_FROST` **(K1 \& TSL)**
      - `AOE_MOB_ELECTRICAL` **(K1 \& TSL)**
      - `AOE_PER_FOGGHOUL` **(K1 \& TSL)**
      - `AOE_MOB_TYRANT_FOG` **(K1 \& TSL)**
      - `AOE_PER_STORM` **(K1 \& TSL)**
      - `AOE_PER_INVIS_SPHERE` **(K1 \& TSL)**
      - `AOE_MOB_SILENCE` **(K1 \& TSL)**
      - `AOE_PER_DELAY_BLAST_FIREBALL` **(K1 \& TSL)**
      - `AOE_PER_GREASE` **(K1 \& TSL)**
      - `AOE_PER_CREEPING_DOOM` **(K1 \& TSL)**
      - `AOE_PER_EVARDS_BLACK_TENTACLES` **(K1 \& TSL)**
      - `AOE_MOB_INVISIBILITY_PURGE` **(K1 \& TSL)**
      - `AOE_MOB_DRAGON_FEAR` **(K1 \& TSL)**
      - `FORCE_POWER_ALL_FORCE_POWERS` **(K1 \& TSL)**
      - `FORCE_POWER_MASTER_ALTER` **(K1 \& TSL)**
      - `FORCE_POWER_MASTER_CONTROL` **(K1 \& TSL)**
      - `FORCE_POWER_MASTER_SENSE` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_JUMP_ADVANCED` **(K1 \& TSL)**
      - `FORCE_POWER_LIGHT_SABER_THROW_ADVANCED` **(K1 \& TSL)**
      - `FORCE_POWER_REGNERATION_ADVANCED` **(K1 \& TSL)**
      - `FORCE_POWER_AFFECT_MIND` **(K1 \& TSL)**
      - `FORCE_POWER_AFFLICTION` **(K1 \& TSL)**
      - `FORCE_POWER_SPEED_BURST` **(K1 \& TSL)**
      - `FORCE_POWER_CHOKE` **(K1 \& TSL)**
      - `FORCE_POWER_CURE` **(K1 \& TSL)**
      - `FORCE_POWER_DEATH_FIELD` **(K1 \& TSL)**
      - `FORCE_POWER_DROID_DISABLE` **(K1 \& TSL)**
      - `FORCE_POWER_DROID_DESTROY` **(K1 \& TSL)**
      - `FORCE_POWER_DOMINATE` **(K1 \& TSL)**
      - `FORCE_POWER_DRAIN_LIFE` **(K1 \& TSL)**
      - `FORCE_POWER_FEAR` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_ARMOR` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_AURA` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_BREACH` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_IMMUNITY` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_JUMP` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_MIND` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_PUSH` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_SHIELD` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_STORM` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_WAVE` **(K1 \& TSL)**
      - `FORCE_POWER_FORCE_WHIRLWIND` **(K1 \& TSL)**
      - `FORCE_POWER_HEAL` **(K1 \& TSL)**
      - `FORCE_POWER_HOLD` **(K1 \& TSL)**
      - `FORCE_POWER_HORROR` **(K1 \& TSL)**
      - `FORCE_POWER_INSANITY` **(K1 \& TSL)**
      - `FORCE_POWER_KILL` **(K1 \& TSL)**
      - `FORCE_POWER_KNIGHT_MIND` **(K1 \& TSL)**
      - `FORCE_POWER_KNIGHT_SPEED` **(K1 \& TSL)**
      - `FORCE_POWER_LIGHTNING` **(K1 \& TSL)**
      - `FORCE_POWER_MIND_MASTERY` **(K1 \& TSL)**
      - `FORCE_POWER_SPEED_MASTERY` **(K1 \& TSL)**
      - `FORCE_POWER_PLAGUE` **(K1 \& TSL)**
      - `FORCE_POWER_REGENERATION` **(K1 \& TSL)**
      - `FORCE_POWER_RESIST_COLD_HEAT_ENERGY` **(K1 \& TSL)**
      - `FORCE_POWER_RESIST_FORCE` **(K1 \& TSL)**
      - `FORCE_POWER_SHOCK` **(K1 \& TSL)**
      - `FORCE_POWER_SLEEP` **(K1 \& TSL)**
      - `FORCE_POWER_SLOW` **(K1 \& TSL)**
      - `FORCE_POWER_STUN` **(K1 \& TSL)**
      - `FORCE_POWER_DROID_STUN` **(K1 \& TSL)**
      - `FORCE_POWER_SUPRESS_FORCE` **(K1 \& TSL)**
      - `FORCE_POWER_LIGHT_SABER_THROW` **(K1 \& TSL)**
      - `FORCE_POWER_WOUND` **(K1 \& TSL)**
      - `PERSISTENT_ZONE_ACTIVE` **(K1 \& TSL)**
      - `PERSISTENT_ZONE_FOLLOW` **(K1 \& TSL)**
      - `INVALID_STANDARD_FACTION` **(K1 \& TSL)**
      - `STANDARD_FACTION_HOSTILE_1` **(K1 \& TSL)**
      - `STANDARD_FACTION_FRIENDLY_1` **(K1 \& TSL)**
      - `STANDARD_FACTION_HOSTILE_2` **(K1 \& TSL)**
      - `STANDARD_FACTION_FRIENDLY_2` **(K1 \& TSL)**
      - `STANDARD_FACTION_NEUTRAL` **(K1 \& TSL)**
      - `STANDARD_FACTION_INSANE` **(K1 \& TSL)**
      - `STANDARD_FACTION_PTAT_TUSKAN` **(K1 \& TSL)**
      - `STANDARD_FACTION_GLB_XOR` **(K1 \& TSL)**
      - `STANDARD_FACTION_SURRENDER_1` **(K1 \& TSL)**
      - `STANDARD_FACTION_SURRENDER_2` **(K1 \& TSL)**
      - `STANDARD_FACTION_PREDATOR` **(K1 \& TSL)**
      - `STANDARD_FACTION_PREY` **(K1 \& TSL)**
      - `STANDARD_FACTION_TRAP` **(K1 \& TSL)**
      - `STANDARD_FACTION_ENDAR_SPIRE` **(K1 \& TSL)**
      - `STANDARD_FACTION_RANCOR` **(K1 \& TSL)**
      - `STANDARD_FACTION_GIZKA_1` **(K1 \& TSL)**
      - `STANDARD_FACTION_GIZKA_2` **(K1 \& TSL)**
      - `SUBSKILL_FLAGTRAP` **(K1 \& TSL)**
      - `SUBSKILL_RECOVERTRAP` **(K1 \& TSL)**
      - `SUBSKILL_EXAMINETRAP` **(K1 \& TSL)**
      - `TALENT_TYPE_FORCE` **(K1 \& TSL)**
      - `TALENT_TYPE_SPELL` **(K1 \& TSL)**
      - `TALENT_TYPE_FEAT` **(K1 \& TSL)**
      - `TALENT_TYPE_SKILL` **(K1 \& TSL)**
      - `TALENT_EXCLUDE_ALL_OF_TYPE` **(K1 \& TSL)**
      - `GUI_PANEL_PLAYER_DEATH` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_WEREWOLF` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_WERERAT` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_WERECAT` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_GIANT_SPIDER` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_TROLL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_UMBER_HULK` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_PIXIE` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_ZOMBIE` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_RED_DRAGON` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_FIRE_GIANT` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_BALOR` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_DEATH_SLAAD` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_IRON_GOLEM` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_HUGE_FIRE_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_HUGE_WATER_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_HUGE_EARTH_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_HUGE_AIR_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_ELDER_FIRE_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_ELDER_WATER_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_ELDER_EARTH_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_ELDER_AIR_ELEMENTAL` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_BROWN_BEAR` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_PANTHER` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_WOLF` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_BOAR` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_BADGER` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_PENGUIN` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_COW` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_DOOM_KNIGHT` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_YUANTI` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_IMP` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_QUASIT` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_SUCCUBUS` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_DIRE_BROWN_BEAR` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_DIRE_PANTHER` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_DIRE_WOLF` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_DIRE_BOAR` **(K1 \& TSL)**
      - `POLYMORPH_TYPE_DIRE_BADGER` **(K1 \& TSL)**
      - `CREATURE_SIZE_INVALID` **(K1 \& TSL)**
      - `CREATURE_SIZE_TINY` **(K1 \& TSL)**
      - `CREATURE_SIZE_SMALL` **(K1 \& TSL)**
      - `CREATURE_SIZE_MEDIUM` **(K1 \& TSL)**
      - `CREATURE_SIZE_LARGE` **(K1 \& TSL)**
      - `CREATURE_SIZE_HUGE` **(K1 \& TSL)**
      - `CAMERA_MODE_CHASE_CAMERA` **(K1 \& TSL)**
      - `CAMERA_MODE_TOP_DOWN` **(K1 \& TSL)**
      - `CAMERA_MODE_STIFF_CHASE_CAMERA` **(K1 \& TSL)**
      - `GAME_DIFFICULTY_VERY_EASY` **(K1 \& TSL)**
      - `GAME_DIFFICULTY_EASY` **(K1 \& TSL)**
      - `GAME_DIFFICULTY_NORMAL` **(K1 \& TSL)**
      - `GAME_DIFFICULTY_CORE_RULES` **(K1 \& TSL)**
      - `GAME_DIFFICULTY_DIFFICULT` **(K1 \& TSL)**
      - `ACTION_MOVETOPOINT` **(K1 \& TSL)**
      - `ACTION_PICKUPITEM` **(K1 \& TSL)**
      - `ACTION_DROPITEM` **(K1 \& TSL)**
      - `ACTION_ATTACKOBJECT` **(K1 \& TSL)**
      - `ACTION_CASTSPELL` **(K1 \& TSL)**
      - `ACTION_OPENDOOR` **(K1 \& TSL)**
      - `ACTION_CLOSEDOOR` **(K1 \& TSL)**
      - `ACTION_DIALOGOBJECT` **(K1 \& TSL)**
      - `ACTION_DISABLETRAP` **(K1 \& TSL)**
      - `ACTION_RECOVERTRAP` **(K1 \& TSL)**
      - `ACTION_FLAGTRAP` **(K1 \& TSL)**
      - `ACTION_EXAMINETRAP` **(K1 \& TSL)**
      - `ACTION_SETTRAP` **(K1 \& TSL)**
      - `ACTION_OPENLOCK` **(K1 \& TSL)**
      - `ACTION_LOCK` **(K1 \& TSL)**
      - `ACTION_USEOBJECT` **(K1 \& TSL)**
      - `ACTION_ANIMALEMPATHY` **(K1 \& TSL)**
      - `ACTION_REST` **(K1 \& TSL)**
      - `ACTION_TAUNT` **(K1 \& TSL)**
      - `ACTION_ITEMCASTSPELL` **(K1 \& TSL)**
      - `ACTION_COUNTERSPELL` **(K1 \& TSL)**
      - `ACTION_HEAL` **(K1 \& TSL)**
      - `ACTION_PICKPOCKET` **(K1 \& TSL)**
      - `ACTION_FOLLOW` **(K1 \& TSL)**
      - `ACTION_WAIT` **(K1 \& TSL)**
      - `ACTION_SIT` **(K1 \& TSL)**
      - `ACTION_FOLLOWLEADER` **(K1 \& TSL)**
      - `ACTION_INVALID` **(K1 \& TSL)**
      - `ACTION_QUEUEEMPTY` **(K1 \& TSL)**
      - `SWMINIGAME_TRACKFOLLOWER_SOUND_ENGINE` **(K1 \& TSL)**
      - `SWMINIGAME_TRACKFOLLOWER_SOUND_DEATH` **(K1 \& TSL)**
      - `PLOT_O_DOOM` **(K1 \& TSL)**
      - `PLOT_O_SCARY_STUFF` **(K1 \& TSL)**
      - `PLOT_O_BIG_MONSTERS` **(K1 \& TSL)**
      - `FORMATION_WEDGE` **(K1 \& TSL)**
      - `FORMATION_LINE` **(K1 \& TSL)**
      - `SUBSCREEN_ID_NONE` **(K1 \& TSL)**
      - `SUBSCREEN_ID_EQUIP` **(K1 \& TSL)**
      - `SUBSCREEN_ID_ITEM` **(K1 \& TSL)**
      - `SUBSCREEN_ID_CHARACTER_RECORD` **(K1 \& TSL)**
      - `SUBSCREEN_ID_ABILITY` **(K1 \& TSL)**
      - `SUBSCREEN_ID_MAP` **(K1 \& TSL)**
      - `SUBSCREEN_ID_QUEST` **(K1 \& TSL)**
      - `SUBSCREEN_ID_OPTIONS` **(K1 \& TSL)**
      - `SUBSCREEN_ID_MESSAGES` **(K1 \& TSL)**
      - `SHIELD_DROID_ENERGY_1` **(K1 \& TSL)**
      - `SHIELD_DROID_ENERGY_2` **(K1 \& TSL)**
      - `SHIELD_DROID_ENERGY_3` **(K1 \& TSL)**
      - `SHIELD_DROID_ENVIRO_1` **(K1 \& TSL)**
      - `SHIELD_DROID_ENVIRO_2` **(K1 \& TSL)**
      - `SHIELD_DROID_ENVIRO_3` **(K1 \& TSL)**
      - `SHIELD_ENERGY` **(K1 \& TSL)**
      - `SHIELD_ENERGY_SITH` **(K1 \& TSL)**
      - `SHIELD_ENERGY_ARKANIAN` **(K1 \& TSL)**
      - `SHIELD_ECHANI` **(K1 \& TSL)**
      - `SHIELD_MANDALORIAN_MELEE` **(K1 \& TSL)**
      - `SHIELD_MANDALORIAN_POWER` **(K1 \& TSL)**
      - `SHIELD_DUELING_ECHANI` **(K1 \& TSL)**
      - `SHIELD_DUELING_YUSANIS` **(K1 \& TSL)**
      - `SHIELD_VERPINE_PROTOTYPE` **(K1 \& TSL)**
      - `SHIELD_ANTIQUE_DROID` **(K1 \& TSL)**
      - `SHIELD_PLOT_TAR_M09AA` **(K1 \& TSL)**
      - `SHIELD_PLOT_UNK_M44AA` **(K1 \& TSL)**
      - `VIDEO_EFFECT_NONE` **(K1 \& TSL)**
      - `VIDEO_EFFECT_SECURITY_CAMERA` **(K1 \& TSL)**
      - `VIDEO_EFFECT_FREELOOK_T3M4` **(K1 \& TSL)**
      - `VIDEO_EFFECT_FREELOOK_HK47` **(K1 \& TSL)**
      - `TUTORIAL_WINDOW_START_SWOOP_RACE` **(K1 \& TSL)**
      - `TUTORIAL_WINDOW_RETURN_TO_BASE` **(K1 \& TSL)**
      - `TUTORIAL_WINDOW_MOVEMENT_KEYS` **(K1)**
      - `LIVE_CONTENT_PKG1` **(K1 \& TSL)**
      - `LIVE_CONTENT_PKG2` **(K1 \& TSL)**
      - `LIVE_CONTENT_PKG3` **(K1 \& TSL)**
      - `LIVE_CONTENT_PKG4` **(K1 \& TSL)**
      - `LIVE_CONTENT_PKG5` **(K1 \& TSL)**
      - `LIVE_CONTENT_PKG6` **(K1 \& TSL)**
      - `sLanguage` **(K1)**
      - `FORM_MASK_FORCE_FOCUS` **(TSL)**
      - `FORM_MASK_ENDURING_FORCE` **(TSL)**
      - `FORM_MASK_FORCE_AMPLIFICATION` **(TSL)**
      - `FORM_MASK_FORCE_POTENCY` **(TSL)**
      - `FORM_MASK_REGENERATION` **(TSL)**
      - `FORM_MASK_POWER_OF_THE_DARK_SIDE` **(TSL)**
      - `FORCE_POWER_MASTER_ENERGY_RESISTANCE` **(TSL)**
      - `FORCE_POWER_MASTER_HEAL` **(TSL)**
      - `FORCE_POWER_FORCE_BARRIER` **(TSL)**
      - `FORCE_POWER_IMPROVED_FORCE_BARRIER` **(TSL)**
      - `FORCE_POWER_MASTER_FORCE_BARRIER` **(TSL)**
      - `FORCE_POWER_BATTLE_MEDITATION_PC` **(TSL)**
      - `FORCE_POWER_IMPROVED_BATTLE_MEDITATION_PC` **(TSL)**
      - `FORCE_POWER_MASTER_BATTLE_MEDITATION_PC` **(TSL)**
      - `FORCE_POWER_BAT_MED_ENEMY` **(TSL)**
      - `FORCE_POWER_IMP_BAT_MED_ENEMY` **(TSL)**
      - `FORCE_POWER_MAS_BAT_MED_ENEMY` **(TSL)**
      - `FORCE_POWER_CRUSH_OPPOSITION_I` **(TSL)**
      - `FORCE_POWER_CRUSH_OPPOSITION_II` **(TSL)**
      - `FORCE_POWER_CRUSH_OPPOSITION_III` **(TSL)**
      - `FORCE_POWER_CRUSH_OPPOSITION_IV` **(TSL)**
      - `FORCE_POWER_CRUSH_OPPOSITION_V` **(TSL)**
      - `FORCE_POWER_CRUSH_OPPOSITION_VI` **(TSL)**
      - `FORCE_POWER_FORCE_BODY` **(TSL)**
      - `FORCE_POWER_IMPROVED_FORCE_BODY` **(TSL)**
      - `FORCE_POWER_MASTER_FORCE_BODY` **(TSL)**
      - `FORCE_POWER_DRAIN_FORCE` **(TSL)**
      - `FORCE_POWER_IMPROVED_DRAIN_FORCE` **(TSL)**
      - `FORCE_POWER_MASTER_DRAIN_FORCE` **(TSL)**
      - `FORCE_POWER_FORCE_CAMOUFLAGE` **(TSL)**
      - `FORCE_POWER_IMPROVED_FORCE_CAMOUFLAGE` **(TSL)**
      - `FORCE_POWER_MASTER_FORCE_CAMOUFLAGE` **(TSL)**
      - `FORCE_POWER_FORCE_SCREAM` **(TSL)**
      - `FORCE_POWER_IMPROVED_FORCE_SCREAM` **(TSL)**
      - `FORCE_POWER_MASTER_FORCE_SCREAM` **(TSL)**
      - `FORCE_POWER_FORCE_REPULSION` **(TSL)**
      - `FORCE_POWER_FURY` **(TSL)**
      - `FORCE_POWER_IMPROVED_FURY` **(TSL)**
      - `FORCE_POWER_MASTER_FURY` **(TSL)**
      - `FORCE_POWER_INSPIRE_FOLLOWERS_I` **(TSL)**
      - `FORCE_POWER_INSPIRE_FOLLOWERS_II` **(TSL)**
      - `FORCE_POWER_INSPIRE_FOLLOWERS_III` **(TSL)**
      - `FORCE_POWER_INSPIRE_FOLLOWERS_IV` **(TSL)**
      - `FORCE_POWER_INSPIRE_FOLLOWERS_V` **(TSL)**
      - `FORCE_POWER_INSPIRE_FOLLOWERS_VI` **(TSL)**
      - `FORCE_POWER_REVITALIZE` **(TSL)**
      - `FORCE_POWER_IMPROVED_REVITALIZE` **(TSL)**
      - `FORCE_POWER_MASTER_REVITALIZE` **(TSL)**
      - `FORCE_POWER_FORCE_SIGHT` **(TSL)**
      - `FORCE_POWER_FORCE_CRUSH` **(TSL)**
      - `FORCE_POWER_PRECOGNITION` **(TSL)**
      - `FORCE_POWER_BATTLE_PRECOGNITION` **(TSL)**
      - `FORCE_POWER_FORCE_ENLIGHTENMENT` **(TSL)**
      - `FORCE_POWER_MIND_TRICK` **(TSL)**
      - `FORCE_POWER_CONFUSION` **(TSL)**
      - `FORCE_POWER_BEAST_TRICK` **(TSL)**
      - `FORCE_POWER_BEAST_CONFUSION` **(TSL)**
      - `FORCE_POWER_DROID_TRICK` **(TSL)**
      - `FORCE_POWER_DROID_CONFUSION` **(TSL)**
      - `FORCE_POWER_BREATH_CONTROL` **(TSL)**
      - `FORCE_POWER_WOOKIEE_RAGE_I` **(TSL)**
      - `FORCE_POWER_WOOKIEE_RAGE_II` **(TSL)**
      - `FORCE_POWER_WOOKIEE_RAGE_III` **(TSL)**
      - `FORM_LIGHTSABER_PADAWAN_I` **(TSL)**
      - `FORM_LIGHTSABER_PADAWAN_II` **(TSL)**
      - `FORM_LIGHTSABER_PADAWAN_III` **(TSL)**
      - `FORM_LIGHTSABER_DAKLEAN_I` **(TSL)**
      - `FORM_LIGHTSABER_DAKLEAN_II` **(TSL)**
      - `FORM_LIGHTSABER_DAKLEAN_III` **(TSL)**
      - `FORM_LIGHTSABER_SENTINEL_I` **(TSL)**
      - `FORM_LIGHTSABER_SENTINEL_II` **(TSL)**
      - `FORM_LIGHTSABER_SENTINEL_III` **(TSL)**
      - `FORM_LIGHTSABER_SODAK_I` **(TSL)**
      - `FORM_LIGHTSABER_SODAK_II` **(TSL)**
      - `FORM_LIGHTSABER_SODAK_III` **(TSL)**
      - `FORM_LIGHTSABER_ANCIENT_I` **(TSL)**
      - `FORM_LIGHTSABER_ANCIENT_II` **(TSL)**
      - `FORM_LIGHTSABER_ANCIENT_III` **(TSL)**
      - `FORM_LIGHTSABER_MASTER_I` **(TSL)**
      - `FORM_LIGHTSABER_MASTER_II` **(TSL)**
      - `FORM_LIGHTSABER_MASTER_III` **(TSL)**
      - `FORM_CONSULAR_FORCE_FOCUS_I` **(TSL)**
      - `FORM_CONSULAR_FORCE_FOCUS_II` **(TSL)**
      - `FORM_CONSULAR_FORCE_FOCUS_III` **(TSL)**
      - `FORM_CONSULAR_ENDURING_FORCE_I` **(TSL)**
      - `FORM_CONSULAR_ENDURING_FORCE_II` **(TSL)**
      - `FORM_CONSULAR_ENDURING_FORCE_III` **(TSL)**
      - `FORM_CONSULAR_FORCE_AMPLIFICATION_I` **(TSL)**
      - `FORM_CONSULAR_FORCE_AMPLIFICATION_II` **(TSL)**
      - `FORM_CONSULAR_FORCE_AMPLIFICATION_III` **(TSL)**
      - `FORM_CONSULAR_FORCE_SHELL_I` **(TSL)**
      - `FORM_CONSULAR_FORCE_SHELL_II` **(TSL)**
      - `FORM_CONSULAR_FORCE_SHELL_III` **(TSL)**
      - `FORM_CONSULAR_FORCE_POTENCY_I` **(TSL)**
      - `FORM_CONSULAR_FORCE_POTENCY_II` **(TSL)**
      - `FORM_CONSULAR_FORCE_POTENCY_III` **(TSL)**
      - `FORM_CONSULAR_REGENERATION_I` **(TSL)**
      - `FORM_CONSULAR_REGENERATION_II` **(TSL)**
      - `FORM_CONSULAR_REGENERATION_III` **(TSL)**
      - `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_I` **(TSL)**
      - `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_II` **(TSL)**
      - `FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_III` **(TSL)**
      - `FORM_SABER_I_SHII_CHO` **(TSL)**
      - `FORM_SABER_II_MAKASHI` **(TSL)**
      - `FORM_SABER_III_SORESU` **(TSL)**
      - `FORM_SABER_IV_ATARU` **(TSL)**
      - `FORM_SABER_V_SHIEN` **(TSL)**
      - `FORM_SABER_VI_NIMAN` **(TSL)**
      - `FORM_SABER_VII_JUYO` **(TSL)**
      - `FORM_FORCE_I_FOCUS` **(TSL)**
      - `FORM_FORCE_II_POTENCY` **(TSL)**
      - `FORM_FORCE_III_AFFINITY` **(TSL)**
      - `FORM_FORCE_IV_MASTERY` **(TSL)**
      - `STANDARD_FACTION_SELF_LOATHING` **(TSL)**
      - `STANDARD_FACTION_ONE_ON_ONE` **(TSL)**
      - `STANDARD_FACTION_PARTYPUPPET` **(TSL)**
      - `ACTION_FOLLOWOWNER` **(TSL)**
      - `PUP_SENSORBALL` **(TSL)**
      - `PUP_OTHER1` **(TSL)**
      - `PUP_OTHER2` **(TSL)**
      - `SHIELD_PLOT_MAN_M28AA` **(TSL)**
      - `SHIELD_HEAT` **(TSL)**
      - `SHIELD_DREXL` **(TSL)**
      - `VIDEO_EFFECT_CLAIRVOYANCE` **(TSL)**
      - `VIDEO_EFFECT_FORCESIGHT` **(TSL)**
      - `VIDEO_EFFECT_VISAS_FREELOOK` **(TSL)**
      - `VIDEO_EFFECT_CLAIRVOYANCEFULL` **(TSL)**
      - `VIDEO_EFFECT_FURY_1` **(TSL)**
      - `VIDEO_EFFECT_FURY_2` **(TSL)**
      - `VIDEO_EFFECT_FURY_3` **(TSL)**
      - `VIDEO_FFECT_SECURITY_NO_LABEL` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP1` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP2` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP3` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP4` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP5` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP6` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP7` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP8` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP9` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP10` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP11` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP12` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP13` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP14` **(TSL)**
      - `TUTORIAL_WINDOW_TEMP15` **(TSL)**
      - `AI_LEVEL_VERY_HIGH` **(TSL)**
      - `AI_LEVEL_HIGH` **(TSL)**
      - `AI_LEVEL_NORMAL` **(TSL)**
      - `AI_LEVEL_LOW` **(TSL)**
      - `AI_LEVEL_VERY_LOW` **(TSL)**
      - `IMPLANT_NONE` **(TSL)**
      - `IMPLANT_REGEN` **(TSL)**
      - `IMPLANT_STR` **(TSL)**
      - `IMPLANT_END` **(TSL)**
      - `IMPLANT_AGI` **(TSL)**
      - `FORFEIT_NO_FORCE_POWERS` **(TSL)**
      - `FORFEIT_NO_ITEMS` **(TSL)**
      - `FORFEIT_NO_WEAPONS` **(TSL)**
      - `FORFEIT_DXUN_SWORD_ONLY` **(TSL)**
      - `FORFEIT_NO_ARMOR` **(TSL)**
      - `FORFEIT_NO_RANGED` **(TSL)**
      - `FORFEIT_NO_LIGHTSABER` **(TSL)**
      - `FORFEIT_NO_ITEM_BUT_SHIELD` **(TSL)**
  - [Cross-References](#cross-references)
<!-- TOC_END -->

## PyKotor Implementation

PyKotor implements `nwscript.nss` definitions in three Python modules:

### data structures

**`Libraries/PyKotor/src/pykotor/common/script.py`:**

- `ScriptFunction`: Represents a function signature with return type, name, parameters, description, and raw string
- `ScriptParam`: Represents a function parameter with type, name, and optional default value
- `ScriptConstant`: Represents a constant with type, name, and value
- `DataType`: Enumeration of all NWScript data types (INT, [float](GFF-File-Format), string, OBJECT, vector, etc.)

**`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`:**

- `KOTOR_FUNCTIONS`: List of 772 `ScriptFunction` objects for KotOR 1
- `TSL_FUNCTIONS`: List of functions for KotOR 2 (The Sith Lords)
- `KOTOR_CONSTANTS`: List of 1489 `ScriptConstant` objects for KotOR 1
- `TSL_CONSTANTS`: List of constants for KotOR 2

**`Libraries/PyKotor/src/pykotor/common/scriptlib.py`:**

- `KOTOR_LIBRARY`: Dictionary mapping library file names to their source code content (e.g., `"k_inc_generic"`, `"k_inc_utility"`)
- `TSL_LIBRARY`: Dictionary for KotOR 2 library files

### Compilation Integration


1. **Parser Initialization**: The `NssParser` is created with game-specific functions and constants:

   ```python
   nss_parser = NssParser(
       functions=KOTOR_FUNCTIONS if game.is_k1() else TSL_FUNCTIONS,
       constants=KOTOR_CONSTANTS if game.is_k1() else TSL_CONSTANTS,
       library=KOTOR_LIBRARY if game.is_k1() else TSL_LIBRARY,
       library_lookup=lookup_arg,
   )
   ```

2. **Function Resolution**: When the parser encounters a function call, it:
   - Looks up the function name in the functions list
   - Validates parameter types and counts
   - Resolves the routine number (index in the functions list)
   - Generates an `ACTION` instruction with the routine number

3. **Constant Resolution**: When the parser encounters a constant:
   - Looks up the constant name in the constants list
   - Replaces the constant with its value
   - Generates appropriate `CONSTx` instruction

4. **Library Inclusion**: When the parser encounters `#include`:
   - Looks up the library name in the library dictionary
   - Parses the included source code
   - Merges functions and constants into the current scope

**Reference:** [`Libraries/PyKotor/src/pykotor/common/script.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/script.py) (data structures), [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py) (function/constant definitions), [`Libraries/PyKotor/src/pykotor/common/scriptlib.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py) (library files)

---

## Shared Functions (K1 & TSL)

<!-- SHARED_FUNCTIONS_START -->

### Abilities and Stats

See [Abilities and Stats](NSS-Shared-Functions-Abilities-and-Stats) for detailed documentation.

### Actions

See [Actions](NSS-Shared-Functions-Actions) for detailed documentation.

### Alignment System

See [Alignment System](NSS-Shared-Functions-Alignment-System) for detailed documentation.

### Class System

See [Class System](NSS-Shared-Functions-Class-System) for detailed documentation.

### Combat Functions

See [Combat Functions](NSS-Shared-Functions-Combat-Functions) for detailed documentation.

### Dialog and Conversation Functions

See [Dialog and Conversation Functions](NSS-Shared-Functions-Dialog-and-Conversation-Functions) for detailed documentation.

### Effects System

See [Effects System](NSS-Shared-Functions-Effects-System) for detailed documentation.

### Global Variables

See [Global Variables](NSS-Shared-Functions-Global-Variables) for detailed documentation.

### Item Management

See [Item Management](NSS-Shared-Functions-Item-Management) for detailed documentation.

### Item Properties

See [Item Properties](NSS-Shared-Functions-Item-Properties) for detailed documentation.

### Local Variables

See [Local Variables](NSS-Shared-Functions-Local-Variables) for detailed documentation.

### Module and Area Functions

See [Module and Area Functions](NSS-Shared-Functions-Module-and-Area-Functions) for detailed documentation.

### Object Query and Manipulation

See [Object Query and Manipulation](NSS-Shared-Functions-Object-Query-and-Manipulation) for detailed documentation.

### Other Functions

See [Other Functions](NSS-Shared-Functions-Other-Functions) for detailed documentation.

### Party Management

<a id="addavailablenpcbyobject"></a>


- `694. AddAvailableNPCByObject`
- This adds a NPC to the list of available party members using
- a game object as the template
- Returns if true if successful, false if the NPC had already
- been added or the object specified is invalid

- `nNPC`: int
- `oCreature`: object

<a id="addavailablenpcbytemplate"></a>


- `697. AddAvailableNPCByTemplate`
- This adds a NPC to the list of available party members using
- a template
- Returns if true if successful, false if the NPC had already
- been added or the template specified is invalid

- `nNPC`: int
- `sTemplate`: string

<a id="addpartymember"></a>


- `574. AddPartyMember`
- Adds a creature to the party
- Returns whether the addition was successful
- AddPartyMember

- `nNPC`: int
- `oCreature`: object

<a id="addtoparty"></a>


- `572. AddToParty`
- Add oPC to oPartyLeader's party.  This will only work on two PCs.
- - oPC: player to add to a party
- - oPartyLeader: player already in the party

- `oPC`: object
- `oPartyLeader`: object

<a id="getpartyaistyle"></a>

#### `GetPartyAIStyle()` - Routine 704

- `704. GetPartyAIStyle`
- Returns the party ai style

<a id="getpartymemberbyindex"></a>

#### `GetPartyMemberByIndex(nIndex)` - Routine 577

- `577. GetPartyMemberByIndex`
- Returns the party member at a given index in the party.
- The order of members in the party can vary based on
- who the current leader is (member 0 is always the current
- party leader).
- GetPartyMemberByIndex

- `nIndex`: int

<a id="getpartymembercount"></a>

#### `GetPartyMemberCount()` - Routine 126

- `126. GetPartyMemberCount`
- GetPartyMemberCount
- Returns a count of how many members [ARE](GFF-File-Format) in the party including the player character

<a id="isnpcpartymember"></a>


- `699. IsNPCPartyMember`
- Returns if a given NPC constant is in the party currently

- `nNPC`: int

<a id="isobjectpartymember"></a>


- `576. IsObjectPartyMember`
- Returns whether a specified creature is a party member
- IsObjectPartyMember

- `oCreature`: object

<a id="removefromparty"></a>


- `573. RemoveFromParty`
- Remove oPC from their current party. This will only work on a PC.
- - oPC: removes this player from whatever party they're currently in.

- `oPC`: object

<a id="removepartymember"></a>


- `575. RemovePartyMember`
- Removes a creature from the party
- Returns whether the removal was syccessful
- RemovePartyMember

- `nNPC`: int

<a id="setpartyaistyle"></a>

#### `SetPartyAIStyle(nStyle)` - Routine 706

- `706. SetPartyAIStyle`
- Sets the party ai style

- `nStyle`: int

<a id="setpartyleader"></a>

#### `SetPartyLeader(nNPC)` - Routine 13

- `13. SetPartyLeader`
- Sets (by NPC constant) which party member should be the controlled
- character

- `nNPC`: int

<a id="showpartyselectiongui"></a>


- `712. ShowPartySelectionGUI`
- ShowPartySelectionGUI
- Brings up the party selection [GUI](GFF-File-Format) for the player to
- select the members of the party from
- if exit script is specified, will be executed when
- the [GUI](GFF-File-Format) is exited

- `sExitScript`: string (default: ``)
- `nForceNPC1`: int
- `nForceNPC2`: int

<a id="switchplayercharacter"></a>


- `11. SwitchPlayerCharacter`
- Switches the main character to a specified NPC
- -1 specifies to switch back to the original PC

- `nNPC`: int

### Player Character Functions

See [Player Character Functions](NSS-Shared-Functions-Player-Character-Functions) for detailed documentation.

### Skills and Feats

See [Skills and Feats](NSS-Shared-Functions-Skills-and-Feats) for detailed documentation.

### Sound and Music Functions

See [Sound and Music Functions](NSS-Shared-Functions-Sound-and-Music-Functions) for detailed documentation.

## K1-Only Functions

<!-- K1_ONLY_FUNCTIONS_START -->

### Other Functions

See [Other Functions](NSS-K1-Only-Functions-Other-Functions) for detailed documentation.

## TSL-Only Functions

<!-- TSL_ONLY_FUNCTIONS_START -->

### Actions

See [Actions](NSS-TSL-Only-Functions-Actions) for detailed documentation.

### Class System

See [Class System](NSS-TSL-Only-Functions-Class-System) for detailed documentation.

### Combat Functions

See [Combat Functions](NSS-TSL-Only-Functions-Combat-Functions) for detailed documentation.

### Dialog and Conversation Functions

See [Dialog and Conversation Functions](NSS-TSL-Only-Functions-Dialog-and-Conversation-Functions) for detailed documentation.

### Effects System

See [Effects System](NSS-TSL-Only-Functions-Effects-System) for detailed documentation.

### Global Variables

See [Global Variables](NSS-TSL-Only-Functions-Global-Variables) for detailed documentation.

### Item Management

See [Item Management](NSS-TSL-Only-Functions-Item-Management) for detailed documentation.

### Object Query and Manipulation

See [Object Query and Manipulation](NSS-TSL-Only-Functions-Object-Query-and-Manipulation) for detailed documentation.

### Other Functions

See [Other Functions](NSS-TSL-Only-Functions-Other-Functions) for detailed documentation.

### Party Management

<a id="addavailablepupbyobject"></a>

#### `AddAvailablePUPByObject(nPUP, oPuppet)`

- 837
- RWT-OEI 07/17/04
- This function adds a Puppet to the Puppet Table by
- creature ID
- Returns 1 if successful, 0 if there was an error

- `nPUP`: int
- `oPuppet`: object

<a id="addavailablepupbytemplate"></a>

#### `AddAvailablePUPByTemplate(nPUP, sTemplate)`

- 836
- RWT-OEI 07/17/04
- This function adds a Puppet to the Puppet Table by
- template.
- Returns 1 if successful, 0 if there was an error

- `nPUP`: int
- `sTemplate`: string

<a id="addpartypuppet"></a>

#### `AddPartyPuppet(nPUP, oidCreature)`

- 840
- RWT-OEI 07/18/04
- This adds an existing puppet object to the party. The
- puppet object must already exist via SpawnAvailablePUP
- and must already be available via AddAvailablePUP*

- `nPUP`: int
- `oidCreature`: object

<a id="getispartyleader"></a>

#### `GetIsPartyLeader(oCharacter)`

- 844
- RWT-OEI 07/21/04
- Returns TRUE if the object ID passed is the character
- that the player is actively controlling at that point.
- Note that this function is *NOT* able to return correct

- `oCharacter`: object

<a id="getpartyleader"></a>

#### `GetPartyLeader()`

- 845
- RWT-OEI 07/21/04
- Returns the object ID of the character that the player
- is actively controlling. This is the 'Party Leader'.
- Returns object Invalid on error

<a id="removenpcfrompartytobase"></a>

#### `RemoveNPCFromPartyToBase(nNPC)`

- 846
- JAB-OEI 07/22/04
- Will remove the CNPC from the 3 person party, and remove
- him/her from the area, effectively sending the CNPC back
- to the base. The CNPC data is still stored in the

- `nNPC`: int

### Player Character Functions

See [Player Character Functions](NSS-TSL-Only-Functions-Player-Character-Functions) for detailed documentation.

### Skills and Feats

See [Skills and Feats](NSS-TSL-Only-Functions-Skills-and-Feats) for detailed documentation.

### Sound and Music Functions

See [Sound and Music Functions](NSS-TSL-Only-Functions-Sound-and-Music-Functions) for detailed documentation.

## Shared Constants (K1 & TSL)

<!-- SHARED_CONSTANTS_START -->

### Ability Constants

See [Ability Constants](NSS-Shared-Constants-Ability-Constants) for detailed documentation.

### Alignment Constants

See [Alignment Constants](NSS-Shared-Constants-Alignment-Constants) for detailed documentation.

### Class type Constants

See [Class type Constants](NSS-Shared-Constants-Class-Type-Constants) for detailed documentation.

### Inventory Constants

See [Inventory Constants](NSS-Shared-Constants-Inventory-Constants) for detailed documentation.

### NPC Constants

See [NPC Constants](NSS-Shared-Constants-NPC-Constants) for detailed documentation.

### Object type Constants

See [Object type Constants](NSS-Shared-Constants-Object-Type-Constants) for detailed documentation.

### Other Constants

See [Other Constants](NSS-Shared-Constants-Other-Constants) for detailed documentation.

### Planet Constants

See [Planet Constants](NSS-Shared-Constants-Planet-Constants) for detailed documentation.

### Visual Effects (VFX)

See [Visual Effects (VFX)](NSS-Shared-Constants-Visual-Effects-(VFX).md) for detailed documentation.

## K1-Only Constants

<!-- K1_ONLY_CONSTANTS_START -->

### NPC Constants

See [NPC Constants](NSS-K1-Only-Constants-NPC-Constants) for detailed documentation.

### Other Constants

See [Other Constants](NSS-K1-Only-Constants-Other-Constants) for detailed documentation.

### Planet Constants

See [Planet Constants](NSS-K1-Only-Constants-Planet-Constants) for detailed documentation.

## TSL-Only Constants

<!-- TSL_ONLY_CONSTANTS_START -->

### Class type Constants

See [Class type Constants](NSS-TSL-Only-Constants-Class-Type-Constants) for detailed documentation.

### Inventory Constants

See [Inventory Constants](NSS-TSL-Only-Constants-Inventory-Constants) for detailed documentation.

### NPC Constants

See [NPC Constants](NSS-TSL-Only-Constants-NPC-Constants) for detailed documentation.

### Other Constants

See [Other Constants](NSS-TSL-Only-Constants-Other-Constants) for detailed documentation.

### Planet Constants

See [Planet Constants](NSS-TSL-Only-Constants-Planet-Constants) for detailed documentation.

### Visual Effects (VFX)

See [Visual Effects (VFX)](NSS-TSL-Only-Constants-Visual-Effects-(VFX).md) for detailed documentation.

## KOTOR Library files

<!-- KOTOR_LIBRARY_START -->

<a id="k_inc_cheat"></a>

#### `k_inc_cheat`

**Description**: :: k_inc_cheat

**Usage**: `#include "k_inc_cheat"`

**Source Code**:

```nss
//:: k_inc_cheat
/*
    This will be localized area for all
    Cheat Bot scripting.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_debug"
//Takes a PLANET_ Constant
void CH_SetPlanetaryGlobal(int nPlanetConstant);
//Makes the specified party member available to the PC
void CH_SetPartyMemberAvailable(int nNPC);
//::///////////////////////////////////////////////
//:: Set Planet Local
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    VARIABLE = K_CURRENT_PLANET
        Endar Spire     5
        Taris           10
        Dantooine       15
        --Kashyyk       20
        --Manaan        25
        --Korriban      30
        --Tatooine      35
        Leviathan       40
        Unknown World   45
        Star Forge      50
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: Oct 16, 2002
//:://////////////////////////////////////////////
void CH_SetPlanetaryGlobal(int nPlanetConstant)
{
    if(nPlanetConstant == PLANET_ENDAR_SPIRE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 5);
    }
    else if(nPlanetConstant == PLANET_TARIS)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 10);
    }
    else if(nPlanetConstant == PLANET_DANTOOINE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 15);
    }
    else if(nPlanetConstant == PLANET_KASHYYYK)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 20);
... (77 more lines)
```

<a id="k_inc_dan"></a>

#### `k_inc_dan`

**Description**: Dan

**Usage**: `#include "k_inc_dan"`

**Source Code**:

```nss
#include "k_inc_generic"
#include "k_inc_utility"
int ROMANCE_DONE = 4;
int JUHANI_RESCUED = 1;
int JEDI_TRAINING_DONE = 7;
int JEDI_PATH_GUARDIAN = 1;
int JEDI_PATH_SENTINEL = 2;
int JEDI_PATH_CONSULAR = 3;
int DROID_STARTED = 1;
int DROID_DESTROYED = 2;
int DROID_DECEIVED = 3;
int DROID_RETURNED = 4;
int DROID_HELPED = 5;
int DROID_FINISHED = 6;
string sBastilaTag = "bastila";
string sCarthTag = "carth";
string sCouncilTag = "dan13_WP_council";
string SABER_BLUE = "g_w_lghtsbr01";
string SABER_GREEN = "g_w_lghtsbr03";
string SABER_GOLD = "g_w_lghtsbr04";
string WANDERING_HOUND_TAG = "dan_wanderhound";
//places an instance of a character based on the tag/template
// **TAG MUST BE THE SAME AS TEMPLATE**
void PlaceNPC(string sTag, string sLocation = "");
//Get Carth's Object
object GetCarth();
//Gets Bastila's object
object GetBastila();
//gets the center of the council chamber
vector GetChamberCenter();
// creature move along a waypoint path. Not interuptable.
void PlotMove(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);
// creature move along a waypoint path. Not interuptable. Destroys self at the end
void PlotLeave(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);
// returns true is a trigger has not been fired yet
// intended for one shot triggers
int HasNeverTriggered();
//returns true if, on Korriban, the player has convinced Yuthura to come to Dantooine.
int YuthuraHasDefected();
//Sets the progression of the Elise plot on Dantooine
void SetElisePlot(int nValue);
// returns true if the player has started the Elise plot
int ElisePlotStarted();
// returns true if the player has agreed to help the droid after it has returned to elise
int GetDroidHelped();
// returns true if c369 has been spoken to
int GetEliseDroidMet();
//  the Elise plot has not started yet
int GetElisePlotNeverStared();
// returns true if Elise has gone to the Jedi compund
... (283 more lines)
```

<a id="k_inc_debug"></a>

#### `k_inc_debug`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_debug"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Debug Include
//:: k_inc_debug
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This contains the functions for inserting
    debug information into the scripts.
    This include will use Db as its two letter
    function prefix.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
//Inserts a print string into the log file for debugging purposes.
void Db_MyPrintString(string sString);
//Makes the object running the script say a speak string.
void Db_MySpeakString(string sString);
//Makes the nearest PC say a speakstring.
void Db_AssignPCDebugString(string sString);
//Basically, a wrapper for AurPostString
void Db_PostString(string sString = "",int x = 5,int y = 5,float fShow = 1.0);
//::///////////////////////////////////////////////
//:: Debug Print String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Inserts a print string into the log file for
    debugging purposes.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
void Db_MyPrintString(string sString)
{
    if(!ShipBuild())
    {
        PrintString(sString);
    }
}
//::///////////////////////////////////////////////
//:: Debug Speak String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Makes the object running the script say a
    speak string.
*/
... (47 more lines)
```

<a id="k_inc_drop"></a>

#### `k_inc_drop`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_drop"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Treasure drop Include
//:: k_inc_drop
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
// Contains the functions for handling creatures dropping random treasure
//Only human creatures not of the beast subrace willdrop treasure dependant
//on their hit dice
//:://////////////////////////////////////////////
//:: Created By: Aidan Scanlan On: 02/06/03
//:://////////////////////////////////////////////
int DR_HIGH_LEVEL = 15;
int DR_MEDIUM_LEVEL = 10;
int DR_LOW_LEVEL = 5;
int DR_SUBRACE_BEAST = 2;
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF);
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF);
// creates a low level treasure: med pack/repair, frag grenade, credits
void DR_CreateLowTreasure();
// creates midlevel treasure: adv-med/repair, any gredade, stims, credits
void DR_CreateMidTreasure();
// creates high treasure: adv stims, grenades, ultra med/repair, credits
void DR_CreateHighTreasure();
// Creates 1-4 credits
void DR_CreateFillerCredits();
/////////////////////////////////////////////////////////////////////////
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF)
{
    int nRace = GetRacialType(oTarget);
    int nFaction = GetStandardFaction(oTarget);
    int nSubRace = GetSubRace(oTarget);
    if(Random(4) == 0 &&
       nRace != RACIAL_TYPE_DROID &&
       nSubRace != DR_SUBRACE_BEAST)
    {
        //AurPostString("will drop",5,5,5.0);
        DR_CreateRandomTreasure(oTarget);
        return TRUE;
    }
    return FALSE;
}
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF)
{
    int nLevel = GetHitDice(oTarget);
    if (nLevel > DR_HIGH_LEVEL)
    {
... (185 more lines)
```

<a id="k_inc_ebonhawk"></a>

#### `k_inc_ebonhawk`

**Description**: :: k_inc_ebonhawk

**Usage**: `#include "k_inc_ebonhawk"`

**Source Code**:

```nss
//:: k_inc_ebonhawk
/*
     Ebon Hawk include file
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//This checks the Star Map plot to see if it is at state 30.
int EBO_CheckStarMapPlot();
//Bastila intiates conversation with the PC
void EBO_BastilaStartConversation2();
//Should Bastila intiates conversation with the PC
int EBO_ShouldBastilaStartConversation();
//Bastila intiates conversation with the PC
void EBO_BastilaStartConversation2();
//Advances the state of the bounty hunters plot after galaxy map selections are made
void EBO_PlayBountyHunterCutScene();
//Play the current cutscene for taking off from the planet.
void EBO_PlayTakeOff(int nCurrentPlanet);
//Play the corrent cutscene for landing on the planet.
void EBO_PlayLanding(int nDestination);
//Creates items on the PC based on the NPC they are talking to.
void EBO_CreateEquipmentOnPC();
//Checks if the PC needs equipment based on the NPC they are talking to.
int EBO_GetIsEquipmentNeeded();
//Determines the number items held with specific tags
int EBO_CheckInventoryNumbers(string sTag1, string sTag2 = "", string sTag3 = "", string sTag4 = "");
//Returns the scripting constant for the current planet.
int EBO_GetCurrentPlanet();
//Returns the scripting constant for the future planet.
int EBO_GetFuturePlanet();
//Returns the correct K_CURRENT_PLANET value when a Planetary.2DA index is passed in.
int EBO_GetPlanetFrom2DA(int nPlanetIndex);
//Starts the correct sequence based on the planet being traveled to.
void EBO_PlayRenderSequence();
//::///////////////////////////////////////////////
//:: Check Star Map
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    If the variable K_STAR_MAP is at 30 and
    the variable K_CAPTURED_LEV = 5 then
    run the leviathan module.
    K_CAPTURED_LEV States
    0 = Pre Leviathan
    5 = Captured
    10 = Escaped
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: Oct 3, 2002
... (800 more lines)
```

<a id="k_inc_end"></a>

#### `k_inc_end`

**Description**: End

**Usage**: `#include "k_inc_end"`

**Source Code**:

```nss
#include "k_inc_utility"
#include "k_inc_generic"
string sTraskTag = "end_trask";
string sTraskWP = "endwp_tarsk01";
string sCarthTag = "Carth";
string SOLDIER_WEAPON = "g_w_blstrrfl001";
string SOLDIER_ITEM01 = "g_i_adrnaline003";
string SOLDIER_ITEM02 = "";
string SCOUT_WEAPON = "g_w_blstrpstl001";
string SCOUT_ITEM01 = "g_i_adrnaline002";
string SCOUT_ITEM02 = "g_i_implant101";
string SCOUNDREL_WEAPON = "g_w_blstrpstl001";
string SCOUNDREL_ITEM01 = "g_i_secspike01";
string SCOUNDREL_ITEM02 = "g_i_progspike01";
int ROOM3_DEAD = 3;
int ROOM5_DEAD = 4;
int ROOM7_DEAD = 2;
int TRASK_DEFAULT = -1;
int TRASK_MUST_GET_GEAR = 0;
int TRASK_GEAR_DONE = 1;
int TRASK_TARGET_DONE = 2;
int TRASK_MUST_EQUIP = 3;
int TRASK_EQUIP_DONE = 4;
int TRASK_MUST_MAP = 5;
int TRASK_MAP_DONE = 6;
int TRASK_MUST_SWITCH = 7;
int TRASK_SWITCH_DONE = 8;
int TRASK_SWITCH_REMIND = 9;
int TRASK_CARTH_BRIDGE = 10;
int TRASK_BRIDGE_DONE = 11;
int TRASK_MUST_DOOR = 12;
int TRASK_DOOR_DONE = 13;
int TRASK_ROOM3_DONE = 14;
int TRASK_MUST_MEDPACK = 15;
int TRASK_COMBAT_WARNING = 16;
int TRASK_COMBAT_WARNING2 = 17;
int TRASK_COMPUTER_DONE = 18;
int TRASK_MUST_DROID = 19;
int TRASK_DROID_DONE = 20;
int TRASK_MUST_MAP_02 = 21;
int TRASK_NOTHING_02 = 22;
//int TRASK_COMBAT_WARNING = 27;
int TRASK_LEVEL_INIT = 28;
int TRASK_MUST_LEVEL = 29;
int TRASK_PARTY_LEVEL = 30;
int TRASK_LEVEL_DONE = 31;
string LOCKER_TAG = "end_locker01";
string STEALTH_UNIT = "g_i_belt010";
//returns Trask's object id
object GetTrask();
... (194 more lines)
```

<a id="k_inc_endgame"></a>

#### `k_inc_endgame`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_endgame"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: Name k_inc_endgame
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
     This include houses all of the stunt/render
     calls for the end game. This will be for
     modules sta_m45ac and sta_m45ad.
*/
//:://////////////////////////////////////////////
//:: Created By: Brad Prince
//:: Created On: Mar 6, 2003
//:://////////////////////////////////////////////
///////////////////////
// LIGHT SIDE scenes //
///////////////////////
// SCENE 1 BO2 - Player kills Bastila on sta_m45ac
void ST_PlayBastilaLight();
// SCENE 2 C01 - Player returns after watching SCENE 1.
void ST_PlayReturnToStarForgeLight();
// SCENE 3 A - Star Forge under attack.
void ST_PlayStarForgeUnderAttack();
// SCENE 4 B - End game credits - Light.
void ST_PlayEndCreditsLight();
//////////////////////////////////////////////////
//////////////////////
// DARK SIDE scenes //
//////////////////////
// SCENE 1 B01 - Bastila leaves party to meditate before generator puzzle.
void ST_PlayBastilaDark();
// SCENE 2 C - Player returns after watching SCENE 1.
void ST_PlayReturnToStarForgeDark();
// SCENE 3 A - The Republic dies.
void ST_PlayRepublicDies();
// SCENE 4 B - The Sith Ceremony.
void ST_PlaySithCeremony();
// SCENE 5 C - End game credits - Dark.
void ST_PlayEndCreditsDark();
//////////////////////////////////////////////////
//                  FUNCTIONS                   //
//////////////////////////////////////////////////
///////////////////////
// LIGHT SIDE scenes //
///////////////////////
// SCENE 1 BO2 - Player kills Bastila on sta_m45ac
void ST_PlayBastilaLight()
{
    StartNewModule("STUNT_50a","", "50b");
}
// SCENE 2 C01 - Player returns after watching SCENE 1.
... (44 more lines)
```

<a id="k_inc_force"></a>

#### `k_inc_force`

**Description**: :: k_inc_force

**Usage**: `#include "k_inc_force"`

**Source Code**:

```nss
//:: k_inc_force
/*
    v1.0
    Force Powers Include for KOTOR
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
float fLightningDuration = 1.0;
//These variables are set in the script run area.
int SWFP_PRIVATE_SAVE_TYPE;
int SWFP_PRIVATE_SAVE_VERSUS_TYPE;
int SWFP_DAMAGE;
int SWFP_DAMAGE_TYPE;
int SWFP_DAMAGE_VFX;
int SWFP_HARMFUL;
int SWFP_SHAPE;
//Runs the script section for the particular force power.
void  Sp_RunForcePowers();
//Immunity and Resist Spell check for the force power.
//The eDamage checks whether the target is immune to the damage effect
int Sp_BlockingChecks(object oTarget, effect eEffect, effect eEffect2, effect eDamage);
//Makes the necessary saving throws
int Sp_MySavingThrows(object oTarget);
//Remove an effect of a specific type
void Sp_RemoveSpecificEffect(int nEffectTypeID, object oTarget);
//Remove an effect from a specific force power.
void Sp_RemoveSpellEffects(int nSpell_ID, object oCaster, object oTarget);
// Delays the application of a spell effect by an amount determined by distance.
float Sp_GetSpellEffectDelay(location SpellTargetLocation, object oTarget);
//Randomly delays the effect application for a default of 0.0 to 0.75 seconds
float Sp_GetRandomDelay(float fMinimumTime = 0.0, float MaximumTime = 0.75);
//Gets a saving throw appropriate to the jedi using the force power.
int Sp_GetJediDCSave();
///Apply effects in a sphere shape.
void Sp_SphereSaveHalf(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
//Apply effects to a single target.
void Sp_SingleTarget(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effect to an area and negate on a save.
void Sp_SphereBlocking(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
// /Apply effect to an object and negate on a save.
void Sp_SingleTargetBlocking(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effects for a for power.
void Sp_ApplyForcePowerEffects(float fTime, effect eEffect, object oTarget);
//Apply effects to targets.
void Sp_ApplyEffects(int nBlocking, object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration2, int nRacial = RACIAL_TYPE_ALL);
//Removes all effects from the spells , Knights Mind, Mind Mastery and Battle Meditation
void Sp_RemoveBuffSpell();
//Prints a string for the spell stript
void SP_MyPrintString(string sString);
//Posts a string for the spell script
... (2163 more lines)
```

<a id="k_inc_generic"></a>

#### `k_inc_generic`

**Description**: :: k_inc_generic

**Usage**: `#include "k_inc_generic"`

**Source Code**:

```nss
//:: k_inc_generic
/*
    v1.5
    Generic Include for KOTOR
    Post Clean Up as of March 3, 2003
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_gensupport"
#include "k_inc_walkways"
#include "k_inc_drop"
struct tLastRound
{
    int nLastAction;
    int nLastActionID;
    int nLastTalentCode;
    object oLastTarget;
    int nTalentSuccessCode;
    int nIsLastTargetDebil;
    int nLastCombo;
    int nLastComboIndex;
    int nCurrentCombo;
    int nBossSwitchCurrent;
};
struct tLastRound tPR;
//LOCAL BOOLEANS RANGE FROM 0 to 96
int AMBIENT_PRESENCE_DAY_ONLY = 1;        //POSSIBLE CUT
int AMBIENT_PRESENCE_NIGHT_ONLY = 2;      //POSSIBLE CUT
int AMBIENT_PRESENCE_ALWAYS_PRESENT = 3;
int SW_FLAG_EVENT_ON_PERCEPTION =   20;
int SW_FLAG_EVENT_ON_ATTACKED   =   21;
int SW_FLAG_EVENT_ON_DAMAGED    =   22;
int SW_FLAG_EVENT_ON_FORCE_AFFECTED = 23;
int SW_FLAG_EVENT_ON_DISTURBED = 24;
int SW_FLAG_EVENT_ON_COMBAT_ROUND_END = 25;
int SW_FLAG_EVENT_ON_DIALOGUE    = 26;
int SW_FLAG_EVENT_ON_DEATH       = 27;
int SW_FLAG_EVENT_ON_HEARTBEAT   = 28;
//int SW_FLAG_AMBIENT_ANIMATIONS = 29;          located in k_inc_walkways
//int SW_FLAG_AMBIENT_ANIMATIONS_MOBILE = 30;   located in k_inc_walkways
int SW_FLAG_FAST_BUFF            = 31;   //POSSIBLE CUT
int SW_FLAG_ASC_IS_BUSY          = 32;   //POSSIBLE CUT
int SW_FLAG_ASC_AGGRESSIVE_MODE  = 33;   //POSSIBLE CUT
int SW_FLAG_AMBIENT_DAY_ONLY     = 40;   //POSSIBLE CUT
int SW_FLAG_AMBIENT_NIGHT_ONLY   = 43;   //POSSIBLE CUT
int SW_FLAG_EVENT_ON_SPELL_CAST_AT = 44;
int SW_FLAG_EVENT_ON_BLOCKED     = 45;
int SW_FLAG_ON_DIALOGUE_COMPUTER = 48;
int SW_FLAG_FORMATION_POSITION_0 = 49;   //POSSIBLE CUT
int SW_FLAG_FORMATION_POSITION_1 = 50;   //POSSIBLE CUT
... (2182 more lines)
```

<a id="k_inc_gensupport"></a>

#### `k_inc_gensupport`

**Description**: :: k_inc_gensupport

**Usage**: `#include "k_inc_gensupport"`

**Source Code**:

```nss
//:: k_inc_gensupport
/*
    v1.0
    Support Include for k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//BOSS ATTACK TYPES
int SW_BOSS_ATTACK_TYPE_GRENADE = 1;
int SW_BOSS_ATTACK_TYPE_FORCE_POWER = 2;
int SW_BOSS_ATTACK_TYPE_NPC = 3;
int SW_BOSS_ATTACK_TYPE_PC = 4;
int SW_BOSS_ATTACK_ANY = 5;
int SW_BOSS_ATTACK_DROID = 6;
//LOCAL NUMBERS
int SW_NUMBER_COMBO_ROUTINE = 3;
int SW_NUMBER_COMBO_INDEX = 4;
int SW_NUMBER_LAST_COMBO = 5;
int SW_NUMBER_ROUND_COUNTER = 6;
int SW_NUMBER_COMBAT_ZONE = 7;
//COMBO CONSTANTS
int SW_COMBO_RANGED_FEROCIOUS = 1;
int SW_COMBO_RANGED_AGGRESSIVE = 2;
int SW_COMBO_RANGED_DISCIPLINED = 3;
int SW_COMBO_RANGED_CAUTIOUS = 4;
int SW_COMBO_MELEE_FEROCIOUS = 5;
int SW_COMBO_MELEE_AGGRESSIVE = 6;
int SW_COMBO_MELEE_DISCIPLINED = 7;
int SW_COMBO_MELEE_CAUTIOUS = 8;
int SW_COMBO_BUFF_PARTY = 9;
int SW_COMBO_BUFF_DEBILITATE = 10;
int SW_COMBO_BUFF_DAMAGE = 11;
int SW_COMBO_BUFF_DEBILITATE_DESTROY = 12;
int SW_COMBO_SUPRESS_DEBILITATE_DESTROY = 13;
int SW_COMBO_SITH_ATTACK = 14;
int SW_COMBO_BUFF_ATTACK = 15;
int SW_COMBO_SITH_CONFOUND = 16;
int SW_COMBO_JEDI_SMITE = 17;
int SW_COMBO_SITH_TAUNT = 18;
int SW_COMBO_SITH_BLADE = 19;
int SW_COMBO_SITH_CRUSH = 20;
int SW_COMBO_JEDI_CRUSH = 21;
int SW_COMBO_SITH_BRUTALIZE = 22;
int SW_COMBO_SITH_DRAIN = 23;
int SW_COMBO_SITH_ESCAPE = 24;
int SW_COMBO_JEDI_BLITZ = 25;
int SW_COMBO_SITH_SPIKE = 26;
int SW_COMBO_SITH_SCYTHE = 27;
... (3004 more lines)
```

<a id="k_inc_kas"></a>

#### `k_inc_kas`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_kas"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: Include
//:: k_inc_kas
//:: Copyright (c) 2002 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This is the include file for Kashyyyk.
*/
//:://////////////////////////////////////////////
//:: Created By: John Winski
//:: Created On: July 29, 2002
//:://////////////////////////////////////////////
#include "k_inc_utility"
#include "k_inc_generic"
int GetGorwookenSpawnGlobal()
{
    return GetGlobalBoolean("kas_SpawnGorwook");
}
void SetGorwookenSpawnGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("kas_SpawnGorwook", bValue);
    }
    return;
}
int GetEliBeenKilledGlobal()
{
    return GetGlobalBoolean("kas_elikilled");
}
void SetEliBeenKilledGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("kas_elikilled", bValue);
    }
    return;
}
int GetJaarakConfessedGlobal()
{
    return GetGlobalBoolean("kas_JaarakConfessed");
}
void SetJaarakConfessedGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("kas_JaarakConfessed", bValue);
    }
    return;
}
... (1263 more lines)
```

<a id="k_inc_lev"></a>

#### `k_inc_lev`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_lev"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: k_inc_lev
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
  include file for leviathan
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 26, 2002
//:://////////////////////////////////////////////
#include "k_inc_debug"
#include "k_inc_utility"
//mark an object for cleanup by the LEV_CleanupDeadObjects function
void LEV_MarkForCleanup(object obj);
//destroy all objects whose PLOT_10 flag has been set
void LEV_CleanupDeadObjects(object oArea);
//mark object for cleanup and move to nearest exit
void LEV_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE);
//fill container with treasure from table
void LEV_AddTreasureToContainer(object oContainer,int iTable,int iAmount);
//strip inventory from oTarget and put it in oDest
void LEV_StripCharacter(object oTarget,object oDest);
//::///////////////////////////////////////////////
//:: LEV_MarkForCleanup
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
//mark an object for cleanup by the TAR_CleanupDeadObjects function
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 26, 2002
//:://////////////////////////////////////////////
void LEV_MarkForCleanup(object obj)
{
  UT_SetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10,TRUE);
}
//::///////////////////////////////////////////////
//:: LEV_CleanupDeadObjects
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
//destroy all objects whose PLOT_10 flag has been set
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 15, 2002
//:://////////////////////////////////////////////
void LEV_CleanupDeadObjects(object oArea)
... (117 more lines)
```

<a id="k_inc_man"></a>

#### `k_inc_man`

**Description**: :: Name

**Usage**: `#include "k_inc_man"`

**Source Code**:

```nss
//:: Name
/*
     Desc
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
#include "k_inc_utility"
int SHIP_TAKEOFF_CUTSCENE = 1;
int SHIP_LANDING_CUTSCENE = 2;
int NONE = 0;
int QUEEDLE = 1;
int CASSANDRA = 2;
int JAX = 3;
int QUEEDLE_CHAMP = 4;
int QUEEDLE_TIME = 3012;
int CASSANDRA_TIME = 2702;
int JAX_TIME = 2548;
int CHAMP_TIME = 2348;
int PLOT_HARVEST_STOPPED = 3;
int PLOT_KOLTO_DESTROYED = 4;
//effect EFFECT_STEAM = EffectDamage(15);
int STEAM_DAMAGE_AMOUNT = 25;
string RACE_DEFAULT = GetStringByStrRef(32289);
string STEAM_PLACEABLE = "man27_visstm0";
string ROLAND_TAG = "man26_repdip";
void PlaceShip(string sTag,location lLoc);
void RemoveShip(string sTag);
void PlaceNPC(string sTag);
// switches current player models to envirosuit models.
void DonSuits();
// switches the envirosuit model back to the regular player models
void RemoveSuits();
// deactivates all turrets on the map with the corresponding tag
// if no tag is given it will default to the tag of the calling object
void DeactivateTurrets(string sTag = "");
//used to make a given condition only fire once
//***note uses SW_PLOT_BOOLEAN_10***
int HasNeverTriggered();
// Sets a global to track who the player is racing
void SetOpponent(int nOpponent);
//Returns thte current race opponent
int GetOpponent();
//Sets a cutom token in racetime format
void SetTokenRaceTime(int nToken, int nRacerTime);
//returns the main plot global for Manaan
int GetManaanMainPlotVariable();
// returns true if poison has been released if the Hrakert rift
int KoltoDestroyed();
// Removes instances and deactives Selkath encounters
... (748 more lines)
```

<a id="k_inc_stunt"></a>

#### `k_inc_stunt`

**Description**: :: Stunt/Render Include

**Usage**: `#include "k_inc_stunt"`

**Source Code**:

```nss
//:: Stunt/Render Include
/*
     This Include File runs
     the stunt and cutscenes
     for the game.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//INDIVIDUAL STUNT MODULE CALLS ******************************************************************************************************
//LEV_A: Pulled out of hyperspace by the Leviathan, load STUNT_16
void ST_PlayLevCaptureStunt();
//LEV_A: Capture by the Leviathan, load ebo_m40aa
void ST_PlayLevCaptureStunt02();
//Load Turret Module Opening 07_3
void ST_PlayStuntTurret_07_3();
//Plays the Bastila torture scene
void ST_PlayBastilaTorture();
//Load Turret Module Opening 07_4
void ST_PlayStuntTurret_07_4();
//Load Leviathan Bombardment Stunt_06 covered by Render 5
void ST_PlayTarisEscape();
//Load Stunt_07 covered by Render 6a and 05_1C
void ST_PlayTarisEscape02();
//Load the Fighter Mini-Game m12ab covered by Render 07_3
void ST_PlayTarisEscape03();
//Load Dantooine module covered by hyperspace and dant landing
void ST_PlayDantooineLanding();
//Leaving Dantooine for the first time, going to STUNT_12 covered by Dant takeoff and hyperspace
void ST_PlayDantooineTakeOff();
//Plays the correct vision based on the value of K_FUTURE_PLANET from a stunt module
void ST_PlayVisionStunt();
//Plays the correct vision based on the value of K_FUTURE_PLANET with a take-off
void ST_PlayVisionStunt02();
//Plays the starforge approach
void ST_PlayStarForgeApproach();
//Plays the Damage Ebon Hawk Stunt scene
void ST_PlayStunt35();
//Shows the crash landing on the Unknown World
void ST_PlayUnknownWorldLanding();
//Shows the take-off from the Unknown World
void ST_PlayUnknownWorldTakeOff();
//Landing on the Star Forge
void ST_PlayStarForgeLanding();
//Goes to the Leviathan Mini-Game covered by the Escape Render
void ST_PlayLeviathanEscape01();
//UBER FUNCTIONS *********************************************************************************************************************
//This determines what to play after a Fighter Mini Game is run
void ST_PlayPostTurret();
//Play the appropriate take off render
string ST_GetTakeOffRender();
... (685 more lines)
```

<a id="k_inc_switch"></a>

#### `k_inc_switch`

**Description**: :: k_inc_switch

**Usage**: `#include "k_inc_switch"`

**Source Code**:

```nss
//:: k_inc_switch
/*
     A simple include defining all of the
     events in the game as constants.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//DEFAULT AI EVENTS
int KOTOR_DEFAULT_EVENT_ON_HEARTBEAT           = 1001;
int KOTOR_DEFAULT_EVENT_ON_PERCEPTION          = 1002;
int KOTOR_DEFAULT_EVENT_ON_COMBAT_ROUND_END    = 1003;
int KOTOR_DEFAULT_EVENT_ON_DIALOGUE            = 1004;
int KOTOR_DEFAULT_EVENT_ON_ATTACKED            = 1005;
int KOTOR_DEFAULT_EVENT_ON_DAMAGE              = 1006;
int KOTOR_DEFAULT_EVENT_ON_DEATH               = 1007;
int KOTOR_DEFAULT_EVENT_ON_DISTURBED           = 1008;
int KOTOR_DEFAULT_EVENT_ON_BLOCKED             = 1009;
int KOTOR_DEFAULT_EVENT_ON_FORCE_AFFECTED      = 1010;
int KOTOR_DEFAULT_EVENT_ON_GLOBAL_DIALOGUE_END = 1011;
int KOTOR_DEFAULT_EVENT_ON_PATH_BLOCKED        = 1012;
//HENCHMEN AI EVENTS
int KOTOR_HENCH_EVENT_ON_HEARTBEAT           = 2001;
int KOTOR_HENCH_EVENT_ON_PERCEPTION          = 2002;
int KOTOR_HENCH_EVENT_ON_COMBAT_ROUND_END    = 2003;
int KOTOR_HENCH_EVENT_ON_DIALOGUE            = 2004;
int KOTOR_HENCH_EVENT_ON_ATTACKED            = 2005;
int KOTOR_HENCH_EVENT_ON_DAMAGE              = 2006;
int KOTOR_HENCH_EVENT_ON_DEATH               = 2007;
int KOTOR_HENCH_EVENT_ON_DISTURBED           = 2008;
int KOTOR_HENCH_EVENT_ON_BLOCKED             = 2009;
int KOTOR_HENCH_EVENT_ON_FORCE_AFFECTED      = 2010;
int KOTOR_HENCH_EVENT_ON_GLOBAL_DIALOGUE_END = 2011;
int KOTOR_HENCH_EVENT_ON_PATH_BLOCKED        = 2012;
int KOTOR_HENCH_EVENT_ON_ENTER_5m            = 2013;
int KOTOR_HENCH_EVENT_ON_EXIT_5m             = 2014;
//MISC AI EVENTS
int KOTOR_MISC_DETERMINE_COMBAT_ROUND                = 3001;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_PC          = 3002;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_INDEX_ZERO  = 3003;

```

<a id="k_inc_tar"></a>

#### `k_inc_tar`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_tar"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: k_inc_tar
//:: k_inc_tar
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
  include file for taris
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: July 16, 2002
//:://////////////////////////////////////////////
#include "k_inc_debug"
#include "k_inc_utility"
//performs a standard creature transformation where the original creature
//is destroyed and a new creature is put in its place.  returns a reference
//to the new creature.
object TAR_TransformCreature(object oTarget = OBJECT_INVALID,string sTemplate = "");
//test routine for walking waypoints
void TAR_WalkWaypoints();
//mark an object for cleanup by the TAR_CleanupDeadObjects function
void TAR_MarkForCleanup(object obj = OBJECT_SELF);
//destroy all objects whose PLOT_10 flag has been set
void TAR_CleanupDeadObjects(object oArea);
//make object do an uninterruptible path move
void TAR_PlotMovePath(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);
//make object do an uninterruptible move to an object
void TAR_PlotMoveObject(object oTarget,int nRun = FALSE);
//make object do an uninterruptible move to a location
void TAR_PlotMoveLocation(location lTarget,int nRun = FALSE);
//check for rukil's apprentice journal
int TAR_PCHasApprenticeJournal();
//return number of promised land journals player has
int TAR_GetNumberPromisedLandJournals();
//toggle the state of sith armor
void TAR_ToggleSithArmor();
//fill container with treasure from table
void TAR_AddTreasureToContainer(object oContainer,int iTable,int iAmount);
//returns TRUE if object is wearing sith armor
int TAR_GetWearingSithArmor(object oTarget = OBJECT_INVALID);
//strip sith armor from party, equipping another appropriate item (if available)
//returns the sith armor object if it was being worn
object TAR_StripSithArmor();
//teleport party member
void TAR_TeleportPartyMember(object oPartyMember, location lDest);
//makes the sith armor equippable
void TAR_EnableSithArmor();
//strip all items from an object
void TAR_StripCharacter(object oTarget,object oDest);
//::///////////////////////////////////////////////
... (488 more lines)
```

<a id="k_inc_tat"></a>

#### `k_inc_tat`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_tat"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: Include
//:: k_inc_tat
//:: Copyright (c) 2002 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This is the include file for Tatooine.
*/
//:://////////////////////////////////////////////
//:: Created By: John Winski
//:: Created On: September 3, 2002
//:://////////////////////////////////////////////
#include "k_inc_utility"
#include "k_inc_generic"
// racer constants
int NONE = 0;
int GARM = 1;
int YUKA = 2;
int ZORIIS = 3;
// race time constants
int GARM_TIME = 2600;
int YUKA_TIME = 2470;
int ZORIIS_TIME = 2350;
string RACE_DEFAULT = GetStringByStrRef(32289);
int GetGammoreansDeadGlobal()
{
    return GetGlobalBoolean("tat_GammoreansDead");
}
void SetGammoreansDeadGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("tat_GammoreansDead", bValue);
    }
    return;
}
int GetMetKomadLodgeGlobal()
{
    return GetGlobalBoolean("tat_MetKomadLodge");
}
void SetMetKomadLodgeGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("tat_MetKomadLodge", bValue);
    }
    return;
}
int GetSharinaAccusedGurkeGlobal()
{
... (2055 more lines)
```

<a id="k_inc_treasure"></a>

#### `k_inc_treasure`

**Description**: :: k_inc_treasure

**Usage**: `#include "k_inc_treasure"`

**Source Code**:

```nss
//:: k_inc_treasure
/*
     contains code for filling containers using treasure tables
*/
//:: Created By:  Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
//
//  March 15, 2003  J.B.
//      removed parts and spikes from tables
//
//constants for container types
int SWTR_DEBUG = TRUE;  //set to false to disable console/file logging
int SWTR_TABLE_CIVILIAN_CONTAINER = 1;
int SWTR_TABLE_MILITARY_CONTAINER_LOW = 2;
int SWTR_TABLE_MILITARY_CONTAINER_MID = 3;
int SWTR_TABLE_MILITARY_CONTAINER_HIGH = 4;
int SWTR_TABLE_CORPSE_CONTAINER_LOW = 5;
int SWTR_TABLE_CORPSE_CONTAINER_MID = 6;
int SWTR_TABLE_CORPSE_CONTAINER_HIGH = 7;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_LOW = 8;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_MID = 9;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_HIGH = 10;
int SWTR_TABLE_DROID_CONTAINER_LOW = 11;
int SWTR_TABLE_DROID_CONTAINER_MID = 12;
int SWTR_TABLE_DROID_CONTAINER_HIGH = 13;
int SWTR_TABLE_RAKATAN_CONTAINER = 14;
int SWTR_TABLE_SANDPERSON_CONTAINER = 15;
//Fill an object with treasure from the specified table
//This is the only function that should be used outside this include file
void SWTR_PopulateTreasure(object oContainer,int iTable,int iItems = 1,int bUnique = TRUE);
//for internal debugging use only, output string to the log file and console if desired
void SWTR_Debug_PostString(string sStr,int bConsole = TRUE,int x = 5,int y = 5,float fTime = 5.0)
{
  if(SWTR_DEBUG)
  {
    if(bConsole)
    {
      AurPostString("SWTR_DEBUG - " + sStr,x,y,fTime);
    }
    PrintString("SWTR_DEBUG - " + sStr);
  }
}
//return whether i>=iLow and i<=iHigh
int SWTR_InRange(int i,int iLow,int iHigh)
{
  if(i >= iLow && i <= iHigh)
  {
    return(TRUE);
  }
  else
... (773 more lines)
```

<a id="k_inc_unk"></a>

#### `k_inc_unk`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_unk"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: k_inc_unk
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
  include file for unknown world
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: Sept. 9, 2002
//:://////////////////////////////////////////////
#include "k_inc_debug"
#include "k_inc_utility"
#include "k_inc_generic"
//mark an object for cleanup by the UNK_CleanupDeadObjects function
void UNK_MarkForCleanup(object obj);
//destroy all objects whose PLOT_10 flag has been set
void UNK_CleanupDeadObjects(object oArea);
//mark object for cleanup and move to nearest exit
void UNK_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE);
//test if red rakata are hostile
int UNK_GetRedRakataHostile();
//test if black rakata are hostile
int UNK_GetBlackRakataHostile();
//make red rakatans hostile
void UNK_SetRedRakataHostile();
//make black rakatans hostile
void UNK_SetBlackRakataHostile();
//make black rakatans neutral
void UNK_SetBlackRakataNeutral();
//fill container with treasure from table
void UNK_AddTreasureToContainer(object oContainer,int iTable,int iAmount);
// unavoidable damage to all within radius
void UNK_RakDefence(string sObjectTag, float fDistance, int bIndiscriminant = TRUE);
//::///////////////////////////////////////////////
//:: UNK_MarkForCleanup
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
//mark an object for cleanup by the TAR_CleanupDeadObjects function
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 26, 2002
//:://////////////////////////////////////////////
void UNK_MarkForCleanup(object obj)
{
  UT_SetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10,TRUE);
}
//::///////////////////////////////////////////////
... (254 more lines)
```

<a id="k_inc_utility"></a>

#### `k_inc_utility`

**Description**: :: k_inc_utility

**Usage**: `#include "k_inc_utility"`

**Source Code**:

```nss
//:: k_inc_utility
/*
    common functions used throughout various scripts
    Modified by Peter T. 17/03/03
    - Added UT_MakeNeutral2(), UT_MakeHostile1(), UT_MakeFriendly1() and UT_MakeFriendly2()
*/
//:: Created By: Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
// Plot Flag Constants.
int SW_PLOT_BOOLEAN_01 = 0;
int SW_PLOT_BOOLEAN_02 = 1;
int SW_PLOT_BOOLEAN_03 = 2;
int SW_PLOT_BOOLEAN_04 = 3;
int SW_PLOT_BOOLEAN_05 = 4;
int SW_PLOT_BOOLEAN_06 = 5;
int SW_PLOT_BOOLEAN_07 = 6;
int SW_PLOT_BOOLEAN_08 = 7;
int SW_PLOT_BOOLEAN_09 = 8;
int SW_PLOT_BOOLEAN_10 = 9;
int SW_PLOT_HAS_TALKED_TO = 10;
int SW_PLOT_COMPUTER_OPEN_DOORS = 11;
int SW_PLOT_COMPUTER_USE_GAS = 12;
int SW_PLOT_COMPUTER_DEACTIVATE_TURRETS = 13;
int SW_PLOT_COMPUTER_DEACTIVATE_DROIDS = 14;
int SW_PLOT_COMPUTER_MODIFY_DROID = 15;
int SW_PLOT_REPAIR_WEAPONS = 16;
int SW_PLOT_REPAIR_TARGETING_COMPUTER = 17;
int SW_PLOT_REPAIR_SHIELDS = 18;
int SW_PLOT_REPAIR_ACTIVATE_PATROL_ROUTE = 19;
// UserDefined events
int HOSTILE_RETREAT = 1100;
//Alignment Adjustment Constants
int SW_CONSTANT_DARK_HIT_HIGH = -6;
int SW_CONSTANT_DARK_HIT_MEDIUM = -5;
int SW_CONSTANT_DARK_HIT_LOW = -4;
int SW_CONSTANT_LIGHT_HIT_LOW = -2;
int SW_CONSTANT_LIGHT_HIT_MEDIUM = -1;
int SW_CONSTANT_LIGHT_HIT_HIGH = 0;
// Returns a pass value based on the object's level and DC rating of 0, 1, or 2 (easy, medium, difficult)
// December 20 2001: Changed so that the difficulty is determined by the
// NPC's Hit Dice
int AutoDC(int DC, int nSkill, object oTarget);
//  checks for high charisma
int IsCharismaHigh();
//  checks for low charisma
int IsCharismaLow();
//  checks for normal charisma
int IsCharismaNormal();
//  checks for high intelligence
int IsIntelligenceHigh();
... (2759 more lines)
```

<a id="k_inc_walkways"></a>

#### `k_inc_walkways`

**Description**: :: k_inc_walkways

**Usage**: `#include "k_inc_walkways"`

**Source Code**:

```nss
//:: k_inc_walkways
/*
    v1.0
    Walk Way Points Include
    used by k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
int WALKWAYS_CURRENT_POSITION = 0;
int WALKWAYS_END_POINT = 1;
int WALKWAYS_SERIES_NUMBER = 2;
int    SW_FLAG_AMBIENT_ANIMATIONS    =    29;
int    SW_FLAG_AMBIENT_ANIMATIONS_MOBILE =    30;
int    SW_FLAG_WAYPOINT_WALK_ONCE    =    34;
int    SW_FLAG_WAYPOINT_WALK_CIRCULAR    =    35;
int    SW_FLAG_WAYPOINT_WALK_PATH    =    36;
int    SW_FLAG_WAYPOINT_WALK_STOP    =    37; //One to three
int    SW_FLAG_WAYPOINT_WALK_RANDOM    =    38;
int SW_FLAG_WAYPOINT_WALK_RUN    =   39;
int SW_FLAG_WAYPOINT_DIRECTION = 41;
int SW_FLAG_WAYPOINT_DEACTIVATE = 42;
int SW_FLAG_WAYPOINT_WALK_STOP_LONG = 46;
int SW_FLAG_WAYPOINT_WALK_STOP_RANDOM = 47;
//Makes OBJECT_SELF walk way points based on the spawn in conditions set out.
void GN_WalkWayPoints();
//Sets the series number from 01 to 99 on a creature so that the series number and not the creature's tag is used for walkway points
void GN_SetWalkWayPointsSeries(int nSeriesNumber);
//Sets Generic Spawn In Conditions
void GN_SetSpawnInCondition(int nFlag, int nState = TRUE);
//Gets the boolean state of a generic spawn in condition.
int GN_GetSpawnInCondition(int nFlag);
//Moves an object to the last waypoint in a series
void GN_MoveToLastWayPoint(object oToMove);
//Moves an object to a random point in the series
void GN_MoveToRandomWayPoint(object oToMove);
//Moves an object to a sepcific point in the series
void GN_MoveToSpecificWayPoint(object oToMove, int nArrayNumber);
//Determines the correct direction to proceed in a walkway points array.
int GN_GetWayPointDirection(int nEndArray, int nCurrentPosition);
//Should only be called from within SetListendingPatterns
void GN_SetUpWayPoints();
//Play an animation between way points.
void GN_PlayWalkWaysAnimation();
//Inserts a print string into the log file for debugging purposes for the walkways include.
void WK_MyPrintString(string sString);
//Are valid walkway points available
int GN_CheckWalkWays(object oTarget);
//::///////////////////////////////////////////////
... (566 more lines)
```

<a id="k_inc_zone"></a>

#### `k_inc_zone`

**Description**: :: k_inc_zones

**Usage**: `#include "k_inc_zone"`

**Source Code**:

```nss
//:: k_inc_zones
/*
     Zone including for controlling
     the chaining of creatures
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
//Function run by the trigger to catalog the control nodes followers
void ZN_CatalogFollowers();
//Checks zone conditional on creature to if they belong to the zone
int ZN_CheckIsFollower(object oController, object oTarget);
//Checks the distance and creatures around the PC to see if it should return home.
int ZN_CheckReturnConditions();
//Gets the followers to move back to the controller object
void ZN_MoveToController(object oController, object oFollower);
//Checks to see if a specific individual needs to return to the controller.
int ZN_CheckFollowerReturnConditions(object oTarget);
//::///////////////////////////////////////////////
//:: Catalog Zone Followers
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
     Catalogs all creatures within
     the trigger area and marks
     them with an integer which
     is part of the creature's
     tag.
     Use local number SW_NUMBER_LAST_COMBO
     as a test. A new local number will
     be defined if the system works.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: April 7, 2003
//:://////////////////////////////////////////////
void ZN_CatalogFollowers()
{
    GN_PostString("FIRING", 10,10, 10.0);
    if(GetLocalBoolean(OBJECT_SELF, 10) == FALSE) //Has talked to boolean
    {
        string sZoneTag = GetTag(OBJECT_SELF);
        int nZoneNumber = StringToInt(GetStringRight(sZoneTag, 2));
        //Set up creature followers
        object oZoneFollower = GetFirstInPersistentObject();
        while(GetIsObjectValid(oZoneFollower))
        {
            SetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE, nZoneNumber);
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower = " + GN_ReturnDebugName(oZoneFollower));
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower Zone # = " + GN_ITS(GetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE)));
... (110 more lines)
```

<!-- KOTOR_LIBRARY_END -->

## TSL Library files

<!-- TSL_LIBRARY_START -->

<a id="a_global_inc"></a>

#### `a_global_inc`

**Description**: Global Inc

**Usage**: `#include "a_global_inc"`

**Source Code**:

```nss

//:: a_global_inc
/*
    parameter 1 = string identifier for a global number
    parameter 2 = amount to increment GetGlobalNumber(param1)
*/
//:: Created By: Anthony Davis
#include "k_inc_debug"
void main()
{
    string tString = GetScriptStringParameter();
    int tInt = GetScriptParameter( 1 );
    SetGlobalNumber(tString, GetGlobalNumber(tString) + tInt);
}

```

<a id="a_influence_inc"></a>

#### `a_influence_inc`

**Description**: a_influence_inc

**Usage**: `#include "a_influence_inc"`

**Source Code**:

```nss
// a_influence_inc
/* Parameter Count: 2
Increases an NPC's influence.
Param1 - The NPC value of the player whose influence is increased.
Param2 - magnitude of influence change:
    1 - low
    2 - medium
    3 - high
    all others - medium
NPC numbers, as specified in NPC.2da
0       Atton
1       BaoDur
2       Mand
3       g0t0
4       Handmaiden
5       hk47
6       Kreia
7       Mira
8       T3m4
9       VisasMarr
10      Hanharr
11      Disciple
*/
//
// KDS 06/16/04
void main()
{
int nInfluenceLow = 8;
int nInfluenceMedium = 8;
int nInfluenceHigh = 8;
int nNPC = GetScriptParameter(1);
int nImpact = GetScriptParameter(2);
int nInfluenceChange;
switch (nImpact)
{
    case 1:
        nInfluenceChange = nInfluenceLow;
        break;
    case 2:
        nInfluenceChange = nInfluenceMedium;
        break;
    case 3:
        nInfluenceChange = nInfluenceHigh;
        break;
    default:
        nInfluenceChange = nInfluenceMedium;
        break;
}
ModifyInfluence (nNPC, nInfluenceChange);
}
... (1 more lines)
```

<a id="a_localn_inc"></a>

#### `a_localn_inc`

**Description**: a_localn_inc

**Usage**: `#include "a_localn_inc"`

**Source Code**:

```nss
// a_localn_inc
// Parameter Count: 2
// Param1 - The local number # to increment (range 12-31)
// Param2 - the amount to increment Param1 by (default = 1)
// Param3 - Optional string parameter to refer to another object's local #
//
// KDS 06/15/04
// Modified TDE 7/31/04
#include "k_inc_debug"
#include "k_inc_utility"
void main()
{
    int nLocalNumber = GetScriptParameter( 1 );
    int nValue = GetScriptParameter ( 2 );
    // Added optional string parameter to refer to another object's local #
    string sTag = GetScriptStringParameter();
    object oObject;
    // If sTag is empty, use the object that called the script
    if ( sTag == "" ) oObject = OBJECT_SELF;
    else oObject = GetObjectByTag(sTag);
    if (nValue == 0) nValue = 1;
    SetLocalNumber(oObject, nLocalNumber,
        GetLocalNumber(oObject, nLocalNumber) + nValue);
}

```

<a id="k_inc_cheat"></a>

#### `k_inc_cheat`

**Description**: :: k_inc_cheat

**Usage**: `#include "k_inc_cheat"`

**Source Code**:

```nss
//:: k_inc_cheat
/*
    This will be localized area for all
    Cheat Bot scripting.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_debug"
//Takes a PLANET_ Constant
void CH_SetPlanetaryGlobal(int nPlanetConstant);
//Makes the specified party member available to the PC
void CH_SetPartyMemberAvailable(int nNPC);
//::///////////////////////////////////////////////
//:: Set Planet Local
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    VARIABLE = K_CURRENT_PLANET
        Endar Spire     5
        Taris           10
        Dantooine       15
        --Kashyyk       20
        --Manaan        25
        --Korriban      30
        --Tatooine      35
        Leviathan       40
        Unknown World   45
        Star Forge      50
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: Oct 16, 2002
//:://////////////////////////////////////////////
void CH_SetPlanetaryGlobal(int nPlanetConstant)
{
/*
    if(nPlanetConstant == PLANET_ENDAR_SPIRE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 5);
    }
    else if(nPlanetConstant == PLANET_TARIS)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 10);
    }
    else if(nPlanetConstant == PLANET_DANTOOINE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 15);
    }
    else if(nPlanetConstant == PLANET_KASHYYYK)
    {
... (81 more lines)
```

<a id="k_inc_debug"></a>

#### `k_inc_debug`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_debug"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Debug Include
//:: k_inc_debug
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This contains the functions for inserting
    debug information into the scripts.
    This include will use Db as its two letter
    function prefix.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
//Inserts a print string into the log file for debugging purposes.
void Db_MyPrintString(string sString);
//Makes the object running the script say a speak string.
void Db_MySpeakString(string sString);
//Makes the nearest PC say a speakstring.
void Db_AssignPCDebugString(string sString);
//Basically, a wrapper for AurPostString
void Db_PostString(string sString = "",int x = 5,int y = 5,float fShow = 1.0);
//::///////////////////////////////////////////////
//:: Debug Print String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Inserts a print string into the log file for
    debugging purposes.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
void Db_MyPrintString(string sString)
{
    if(!ShipBuild())
    {
        PrintString(sString);
    }
}
//::///////////////////////////////////////////////
//:: Debug Speak String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Makes the object running the script say a
    speak string.
*/
... (47 more lines)
```

<a id="k_inc_disguise"></a>

#### `k_inc_disguise`

**Description**: :: k_inc_disguise

**Usage**: `#include "k_inc_disguise"`

**Source Code**:

```nss
//:: k_inc_disguise
/*
    This script contains all functions necessary to add and
    remove disguises on all party members.
*/
void DonEnvironmentSuit() {
    object oPC;
    int nMax = GetPartyMemberCount();
    int nIdx;
    effect eChange = EffectDisguise(DISGUISE_TYPE_ENVIRONMENTSUIT);
    for(nIdx = 0;nIdx < nMax; nIdx++)
    {
        ApplyEffectToObject(DURATION_TYPE_PERMANENT,eChange,GetPartyMemberByIndex(nIdx));
    }
}
void DonSpaceSuit() {
    int nMax = GetPartyMemberCount();
    int nIdx;
    effect eChange = EffectDisguise(DISGUISE_TYPE_ENVIRONMENTSUIT_02);
    for(nIdx = 0;nIdx < nMax; nIdx++)
    {
        object oPartyMember = GetPartyMemberByIndex(nIdx);
        ApplyEffectToObject(DURATION_TYPE_PERMANENT,eChange,oPartyMember);
    }
}
void RemoveDisguises() {
    int nDisguise = EFFECT_TYPE_DISGUISE;
    object oPC;
    effect eEffect;
    int nMax = GetPartyMemberCount();
    int nIdx;
    for(nIdx = 0;nIdx < nMax; nIdx++)
    {
        oPC = GetPartyMemberByIndex(nIdx);
        eEffect = GetFirstEffect(oPC);
        while(GetIsEffectValid(eEffect))
        {
            if(GetEffectType(eEffect) == nDisguise)
            {
                RemoveEffect(oPC,eEffect);
            }
            eEffect = GetNextEffect(oPC);
        }
    }
}

```

<a id="k_inc_drop"></a>

#### `k_inc_drop`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_drop"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Treasure drop Include
//:: k_inc_drop
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
// Contains the functions for handling creatures dropping random treasure
//Only human creatures not of the beast subrace willdrop treasure dependant
//on their hit dice
//:://////////////////////////////////////////////
//:: Created By: Aidan Scanlan On: 02/06/03
//:://////////////////////////////////////////////
int DR_HIGH_LEVEL = 15;
int DR_MEDIUM_LEVEL = 10;
int DR_LOW_LEVEL = 5;
int DR_SUBRACE_BEAST = 2;
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF);
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF);
// creates a low level treasure: med pack/repair, frag grenade, credits
void DR_CreateLowTreasure();
// creates midlevel treasure: adv-med/repair, any gredade, stims, credits
void DR_CreateMidTreasure();
// creates high treasure: adv stims, grenades, ultra med/repair, credits
void DR_CreateHighTreasure();
// Creates 1-4 credits
void DR_CreateFillerCredits();
/////////////////////////////////////////////////////////////////////////
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF)
{
    int nRace = GetRacialType(oTarget);
    int nFaction = GetStandardFaction(oTarget);
    int nSubRace = GetSubRace(oTarget);
    if(Random(4) == 0 &&
       nRace != RACIAL_TYPE_DROID &&
       nSubRace != DR_SUBRACE_BEAST)
    {
        //AurPostString("will drop",5,5,5.0);
        DR_CreateRandomTreasure(oTarget);
        return TRUE;
    }
    return FALSE;
}
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF)
{
    int nLevel = GetHitDice(oTarget);
    if (nLevel > DR_HIGH_LEVEL)
    {
... (185 more lines)
```

<a id="k_inc_fab"></a>

#### `k_inc_fab`

**Description**: k_inc_fab

**Usage**: `#include "k_inc_fab"`

**Source Code**:

```nss
// k_inc_fab
/*
    Ferret's Wacky Include Script - YAY
    A running compilation of short cuts
    to make life easier
*/
// FAB 3/11
// This spawns in a creature with resref sCreature
// in waypoint location "sp_<sCreature><nInstance>"
object FAB_Spawn( string sCreature, int nInstance = 0 );
// This makes oAct face in the direction of oFace
// if oFace is left blank it defaults to the PC
void FAB_Face( object oAct, object oFace = OBJECT_INVALID );
// This function teleports the PC to oWP then any
// other CNPCs are teleported behind the PC.
// WARNING: Make sure that behind the waypoint there
// are valid points for the CNPCs to teleport to.
void FAB_PCPort( object oWP );
// This function returns a location directly behind the object
// you pass it. The float can be changed to determine how far
// behind the PC.
location FAB_Behind( object oTarg, float fMult = 2.5 );
// This spawns in a creature with resref sCreature
// in waypoint location "sp_<sCreature><nInstance>"
object FAB_Spawn( string sCreature, int nInstance = 0 )
{
    string sWP;
    if ( nInstance == 0 ) sWP = "sp_" + sCreature ;
    else sWP = "sp_" + sCreature + IntToString( nInstance );
    return CreateObject( OBJECT_TYPE_CREATURE, sCreature, GetLocation( GetObjectByTag( sWP ) ));
}
// This makes oAct face in the direction of oFace
// if oFace is left blank it defaults to the PC
void FAB_Face( object oAct, object oFace = OBJECT_INVALID )
{
    if ( oFace == OBJECT_INVALID ) oFace = GetFirstPC();
    AssignCommand( oAct, SetFacingPoint( GetPositionFromLocation(GetLocation(oFace)) ));
}
// This function teleports the PC to oWP then any
// other CNPCs are teleported behind the PC.
// WARNING: Make sure that behind the waypoint there
// are valid points for the CNPCs to teleport to.
void FAB_PCPort( object oWP )
{
    AurPostString("Testing!",5,4,2.0);
    //object oWP = GetObjectByTag( "tp_test" );
    //object oTarg = GetFirstPC();
    object oTarg = GetPartyMemberByIndex(0);
    DelayCommand( 0.1, AssignCommand( oTarg, ClearAllActions() ));
    DelayCommand( 0.2, AssignCommand( oTarg, ActionJumpToObject(oWP) ) );
... (72 more lines)
```

<a id="k_inc_fakecombat"></a>

#### `k_inc_fakecombat`

**Description**: :: k_inc_fakecombat

**Usage**: `#include "k_inc_fakecombat"`

**Source Code**:

```nss
//:: k_inc_fakecombat
/*
     routines for doing fake combat
*/
//:: Created By: Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
void FAI_EnableFakeMode(object oTarget,int iFaction);
void FAI_DisableFakeMode(object oTarget,int iFaction);
void FAI_PerformFakeAttack(object oAttacker,object oTarget,int bLethal = FALSE);
void FAI_PerformFakeTalent(object oAttacker,object oTarget,talent t,int bLethal = FALSE);
void FAI_EnableFakeMode(object oTarget,int iFaction)
{
  if(!GetIsObjectValid(oTarget))
  {
    return;
  }
  SetCommandable(TRUE,oTarget);
  AssignCommand(oTarget,ClearAllActions());
  SetLocalBoolean(oTarget,SW_FLAG_AI_OFF,TRUE);
  AurPostString("TURNING AI OFF - " + GetTag(oTarget),5,5,5.0);
  ChangeToStandardFaction(oTarget,iFaction);
  SetMinOneHP(oTarget,TRUE);
}
void FAI_DisableFakeMode(object oTarget,int iFaction)
{
  if(!GetIsObjectValid(oTarget))
  {
    return;
  }
  SetCommandable(TRUE,oTarget);
  SetLocalBoolean(oTarget,SW_FLAG_AI_OFF,FALSE);
  ChangeToStandardFaction(oTarget,iFaction);
  SetMinOneHP(oTarget,FALSE);
}
void DoFakeAttack(object oTarget,int bLethal)
{
  if(bLethal)
  {
    SetMinOneHP(oTarget,FALSE);
    ApplyEffectToObject(DURATION_TYPE_INSTANT,EffectDamage(GetCurrentHitPoints(oTarget)-1),
      oTarget);
    //CutsceneAttack(oTarget,ACTION_ATTACKOBJECT,ATTACK_RESULT_HIT_SUCCESSFUL,1000);
  }
  //else
  //{
    ApplyEffectToObject(DURATION_TYPE_TEMPORARY,EffectAssuredHit(),OBJECT_SELF,3.0);
    ActionAttack(oTarget);
 //}
}
... (28 more lines)
```

<a id="k_inc_force"></a>

#### `k_inc_force`

**Description**: :: k_inc_force

**Usage**: `#include "k_inc_force"`

**Source Code**:

```nss
//:: k_inc_force
/*
    v1.0
    Force Powers Include for KOTOR
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
float fLightningDuration = 1.0;
//These variables are set in the script run area.
int SWFP_PRIVATE_SAVE_TYPE;
int SWFP_PRIVATE_SAVE_VERSUS_TYPE;
int SWFP_DAMAGE;
int SWFP_DAMAGE_TYPE;
int SWFP_DAMAGE_VFX;
int SWFP_HARMFUL;
int SWFP_SHAPE;
//Runs the script section for the particular force power.
void  Sp_RunForcePowers();
//Immunity and Resist Spell check for the force power.
//The eDamage checks whether the target is immune to the damage effect
int Sp_BlockingChecks(object oTarget, effect eEffect, effect eEffect2, effect eDamage);
//Makes the necessary saving throws
int Sp_MySavingThrows(object oTarget, int iSpellDC = 0);
//Remove an effect of a specific type
void Sp_RemoveSpecificEffect(int nEffectTypeID, object oTarget);
//Remove an effect from a specific force power.
void Sp_RemoveSpellEffects(int nSpell_ID, object oCaster, object oTarget);
// Delays the application of a spell effect by an amount determined by distance.
float Sp_GetSpellEffectDelay(location SpellTargetLocation, object oTarget);
//Randomly delays the effect application for a default of 0.0 to 0.75 seconds
float Sp_GetRandomDelay(float fMinimumTime = 0.0, float MaximumTime = 0.75);
//Gets a saving throw appropriate to the jedi using the force power.
int Sp_GetJediDCSave();
///Apply effects in a sphere shape.
void Sp_SphereSaveHalf(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
//Apply effects to a single target.
void Sp_SingleTarget(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effect to an area and negate on a save.
void Sp_SphereBlocking(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
// /Apply effect to an object and negate on a save.
void Sp_SingleTargetBlocking(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effects for a for power.
void Sp_ApplyForcePowerEffects(float fTime, effect eEffect, object oTarget);
//Apply effects to targets.
void Sp_ApplyEffects(int nBlocking, object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration2, int nRacial = RACIAL_TYPE_ALL);
//Removes all effects from the spells , Knights Mind, Mind Mastery and Battle Meditation
void Sp_RemoveBuffSpell();
//Prints a string for the spell stript
void SP_MyPrintString(string sString);
//Posts a string for the spell script
... (6373 more lines)
```

<a id="k_inc_generic"></a>

#### `k_inc_generic`

**Description**: :: k_inc_generic

**Usage**: `#include "k_inc_generic"`

**Source Code**:

```nss
//:: k_inc_generic
/*
    v1.5
    Generic Include for KOTOR
    Post Clean Up as of March 3, 2003
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_gensupport"
#include "k_inc_walkways"
#include "k_inc_drop"
struct tLastRound
{
    int nLastAction;
    int nLastActionID;
    int nLastTalentCode;
    object oLastTarget;
    int nTalentSuccessCode;
    int nIsLastTargetDebil;
    int nLastCombo;
    int nLastComboIndex;
    int nCurrentCombo;
    int nBossSwitchCurrent;
};
struct tLastRound tPR;
//LOCAL BOOLEANS RANGE FROM 0 to 96
int AMBIENT_PRESENCE_DAY_ONLY = 1;        //POSSIBLE CUT
int AMBIENT_PRESENCE_NIGHT_ONLY = 2;      //POSSIBLE CUT
int AMBIENT_PRESENCE_ALWAYS_PRESENT = 3;
int SW_FLAG_EVENT_ON_PERCEPTION =   20;
int SW_FLAG_EVENT_ON_ATTACKED   =   21;
int SW_FLAG_EVENT_ON_DAMAGED    =   22;
int SW_FLAG_EVENT_ON_FORCE_AFFECTED = 23;
int SW_FLAG_EVENT_ON_DISTURBED = 24;
int SW_FLAG_EVENT_ON_COMBAT_ROUND_END = 25;
int SW_FLAG_EVENT_ON_DIALOGUE    = 26;
int SW_FLAG_EVENT_ON_DEATH       = 27;
int SW_FLAG_EVENT_ON_HEARTBEAT   = 28;
//int SW_FLAG_AMBIENT_ANIMATIONS = 29;          located in k_inc_walkways
// DJS-OEI 3/31/2004
// Since I misinformed the designers early on about the
// number of local boolean the game was using internally,
// they started using flags 30 thru 64 for plot-related
// stuff. This started causing problems since it was signalling
// the AI to perform incorrect behaviors. I've set aside the
// 30-64 range for designer use and increased the values of
// the remaining flags (as well as the engine's total storage
// capacity) so their current scripts will still work. We need
// to recompile all global and MOD embedded scripts so they use
// the new values.
... (3672 more lines)
```

<a id="k_inc_gensupport"></a>

#### `k_inc_gensupport`

**Description**: :: k_inc_gensupport

**Usage**: `#include "k_inc_gensupport"`

**Source Code**:

```nss
//:: k_inc_gensupport
/*
    v1.0
    Support Include for k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//BOSS ATTACK TYPES
int SW_BOSS_ATTACK_TYPE_GRENADE = 1;
int SW_BOSS_ATTACK_TYPE_FORCE_POWER = 2;
int SW_BOSS_ATTACK_TYPE_NPC = 3;
int SW_BOSS_ATTACK_TYPE_PC = 4;
int SW_BOSS_ATTACK_ANY = 5;
int SW_BOSS_ATTACK_DROID = 6;
//LOCAL NUMBERS
int SW_NUMBER_COMBO_ROUTINE = 3;
int SW_NUMBER_COMBO_INDEX = 4;
int SW_NUMBER_LAST_COMBO = 5;
int SW_NUMBER_ROUND_COUNTER = 6;
int SW_NUMBER_COMBAT_ZONE = 7;
int SW_NUMBER_HEALERAI_THRESHOLD = 8;
int SW_NUMBER_HEALERAI_PERCENTAGE = 9;
int SW_NUMBER_COOLDOWN = 10; // fak - oei, rounds before firing again
int SW_NUMBER_COOLDOWN_FIRE = 11; // fak - oei, threshold at which turret fires
//COMBO CONSTANTS
int SW_COMBO_RANGED_FEROCIOUS = 1;
int SW_COMBO_RANGED_AGGRESSIVE = 2;
int SW_COMBO_RANGED_DISCIPLINED = 3;
int SW_COMBO_RANGED_CAUTIOUS = 4;
int SW_COMBO_MELEE_FEROCIOUS = 5;
int SW_COMBO_MELEE_AGGRESSIVE = 6;
int SW_COMBO_MELEE_DISCIPLINED = 7;
int SW_COMBO_MELEE_CAUTIOUS = 8;
int SW_COMBO_BUFF_PARTY = 9;
int SW_COMBO_BUFF_DEBILITATE = 10;
int SW_COMBO_BUFF_DAMAGE = 11;
int SW_COMBO_BUFF_DEBILITATE_DESTROY = 12;
int SW_COMBO_SUPRESS_DEBILITATE_DESTROY = 13;
int SW_COMBO_SITH_ATTACK = 14;
int SW_COMBO_BUFF_ATTACK = 15;
int SW_COMBO_SITH_CONFOUND = 16;
int SW_COMBO_JEDI_SMITE = 17;
int SW_COMBO_SITH_TAUNT = 18;
int SW_COMBO_SITH_BLADE = 19;
int SW_COMBO_SITH_CRUSH = 20;
int SW_COMBO_JEDI_CRUSH = 21;
int SW_COMBO_SITH_BRUTALIZE = 22;
int SW_COMBO_SITH_DRAIN = 23;
... (3828 more lines)
```

<a id="k_inc_glob_party"></a>

#### `k_inc_glob_party`

**Description**: Glob Party

**Usage**: `#include "k_inc_glob_party"`

**Source Code**:

```nss

//:: k_inc_glob_party
/*
These global scripts are to be used to spawn actual party member objects with thier correct equipment, stats, levels, etc.
Use this to place party members for required scripts and cutscenes.
*/
#include "k_inc_debug"
// FUNCTION DECLARATIONS
string  GetNPCTag( int nNPC );
int     GetNPCConstant( string sTag );
void    ClearPlayerParty();
void    SetPlayerParty(int aNPC_CONSTANT_1, int aNPC_CONSTANT_2);
object  SpawnIndividualPartyMember(int aNPC_CONSTANT, string sWP = "WP_gspawn_");
void    SpawnAllAvailablePartyMembers();
object  SpawnIndividualPuppet(int aNPC_CONSTANT, string sWP = "WP_gspawn_");
string  GetPuppetTag( int nNPC );
int     GetPuppetConstant( string sTag );
// FUNCTION DEFINITIONS:
// Sets the Player created character to be the party leader
// and returns all other party members to the 'party base'.
void ClearPlayerParty()
{
    SetPartyLeader(NPC_PLAYER);
    int i;
    for(i = 0; i < 12; i++)
    {
        if(IsNPCPartyMember( i ))
            RemoveNPCFromPartyToBase( i );
    }
}
// sets the Player created character to be the party leader and then fills the party
// with the passed in constants PROVIDED that they have been previously add to the
// 'party base'
void SetPlayerParty(int aNPC_CONSTANT_1, int aNPC_CONSTANT_2)
{
    ClearPlayerParty();
    object oPartyMember1 = SpawnIndividualPartyMember(aNPC_CONSTANT_1);
    object oPartyMember2 = SpawnIndividualPartyMember(aNPC_CONSTANT_2);
    if(GetIsObjectValid(oPartyMember1) )
    {
        AddPartyMember(aNPC_CONSTANT_1, oPartyMember1);
    }
    if(GetIsObjectValid(oPartyMember2) )
    {
        AddPartyMember(aNPC_CONSTANT_2, oPartyMember2);
    }
}
// Will return the tag of the party member constant passed in.
// Will return 'ERROR' if an invalid constant is passed in.
string GetNPCTag( int nNPC )
... (205 more lines)
```

<a id="k_inc_hawk"></a>

#### `k_inc_hawk`

**Description**: Hawk

**Usage**: `#include "k_inc_hawk"`

**Source Code**:

```nss

//:: Script Name
/*
    Desc
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_glob_party"
#include "k_oei_hench_inc"
void StopCombat()
{
    object oPC = GetFirstPC();
    CancelCombat(oPC);
    int i;
    object oEnemy;
    for(i = 0;i < 20;i++)
    {
        oEnemy = GetObjectByTag("REThug4", i);
        if(GetIsObjectValid(oEnemy))
        {
            ChangeToStandardFaction( oEnemy,STANDARD_FACTION_NEUTRAL );
            CancelCombat(oEnemy);
        }
        oEnemy = GetObjectByTag("REThug5", i);
        if(GetIsObjectValid(oEnemy))
        {
            ChangeToStandardFaction( oEnemy,STANDARD_FACTION_NEUTRAL );
            CancelCombat(oEnemy);
        }
    }
    //take care of the captain
    oEnemy = GetObjectByTag("RECapt");
    if(GetIsObjectValid(oEnemy))
    {
        ChangeToStandardFaction( oEnemy,STANDARD_FACTION_NEUTRAL );
        CancelCombat(oEnemy);
    }
}
void ClearEnemies()
{
    int i;
    object oEnemy;
    for(i = 0;i < 20;i++)
    {
        oEnemy = GetObjectByTag("REThug4", i);
        if(GetIsObjectValid(oEnemy))
            DestroyObject(oEnemy);
        oEnemy = GetObjectByTag("REThug5", i);
        if(GetIsObjectValid(oEnemy))
            DestroyObject(oEnemy);
... (346 more lines)
```

<a id="k_inc_item_gen"></a>

#### `k_inc_item_gen`

**Description**: Item Gen

**Usage**: `#include "k_inc_item_gen"`

**Source Code**:

```nss

//:: k_inc_item_gen.nss
/*
    Global script used to generate items on the PC based on the
    NPC being spoken to.
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_debug"
//Checks the Player's inventory and determines based on OBJECT_SELF
//whether the Player needs equipment.
//Returns TRUE if the Player needs equipment.
//Returns FALSE if the Player does NOT equipment.
int  GetIsEquipmentNeeded();
//Creates equipment on the PC based on the NPC they are talking to.
void CreateEquipmentOnPC();
//Counts and totals up to four different items within the Player's inventory.
int  CheckInventoryNumbers(string sTag1, string sTag2 = "", string sTag3 = "", string sTag4 = "");
//Checks the Player's inventory and determines based on OBJECT_SELF
//whether the Player needs equipment.
//Returns TRUE if the Player needs equipment.
//Returns FALSE if the Player does NOT equipment.
//Global and modified version of EBO_GetIsEquipmentNeeded() from Kotor1
int GetIsEquipmentNeeded()
{
    int nNumber, nGlobal;
    string sTag = GetTag(OBJECT_SELF);
    int nJediFound = (GetGlobalNumber("000_Jedi_Found")*2) + 10;
    if(sTag == "mira")//Mira
    {
        int bMakeLethalGrenades = GetLocalBoolean( OBJECT_SELF, 31 );
        if(bMakeLethalGrenades)
        {//lethals only
            nNumber = CheckInventoryNumbers("g_w_fraggren01","G_W_FIREGREN001");
            nGlobal = GetGlobalNumber("K_MIRA_ITEMS");
            if((nNumber <= 10 && nGlobal < nJediFound) || nGlobal == 0)
            {
                return TRUE;
            }
            return FALSE;
        }
        else
        {//non lethal grenades only, stuns and adhesives
            nNumber = CheckInventoryNumbers("G_w_StunGren01","g_w_adhsvgren001","G_W_CRYOBGREN001","g_w_iongren01");
            nGlobal = GetGlobalNumber("K_MIRA_ITEMS");
            if((nNumber <= 10 && nGlobal < nJediFound) || nGlobal == 0)
            {
                return TRUE;
            }
            return FALSE;
... (222 more lines)
```

<a id="k_inc_npckill"></a>

#### `k_inc_npckill`

**Description**: Richard Taylor

**Usage**: `#include "k_inc_npckill"`

**Source Code**:

```nss
//Richard Taylor
//OEI 08/08/04
//Various functions to help with killing creatures in
//violent and damaging explosions.
//When this function is called on something it will
//destroy the oCreature after nDelay seconds and do nDamage to
//everyone within 4 meters radius.
void DamagingExplosion(object oCreature, int nDelay, int nDamage );
//When this function is called on something it will
//destroy the oCreature after nDelay seconds but not
//damage anyone in the explosion
void NonDamagingExplosion(object oCreature, int nDelay);
//When this function is called on something it will do
//an EffectDeath on oCreature after nSeconds
void KillCreature(object oCreature, int nDelay);
int GR_GetGrenadeDC(object oTarget);
void DamagingExplosion( object oCreature, int nDelay, int nDamage )
{
    //IF there is a delay just call ourselves after ndelay seconds and
    //not have a delay next time
    if ( nDelay > 0 )
    {
        //AurPostString( "Delaying Damaging", 10, 25, 5.0f );
        DelayCommand( IntToFloat(nDelay), DamagingExplosion(oCreature, 0, nDamage ));
        return;
    }
    //AurPostString( "Executing Damaging", 10, 26, 5.0f );
    int nDC = 15;
    int nDCCheck = 0;
    location oLoc = GetLocation(oCreature);
    float oOri = GetFacing(oCreature);
    vector vPos = GetPositionFromLocation( oLoc );
    vPos.z = vPos.z + 1.0f ;
    location oExplosionLoc = Location( vPos, oOri );
    object oTarget = GetFirstObjectInShape(SHAPE_SPHERE, 4.0, oLoc, FALSE, 65);
    while (GetIsObjectValid(oTarget) && nDamage > 0 )
    {
        int nFaction = GetStandardFaction( oTarget );
        if ( oTarget != OBJECT_SELF && nFaction != STANDARD_FACTION_NEUTRAL )
        {
            nDCCheck = nDC;
            nDCCheck -= GR_GetGrenadeDC(oTarget);
            if ( !ReflexSave(oTarget, nDCCheck, SAVING_THROW_TYPE_NONE))
            {
                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectDamage(nDamage, DAMAGE_TYPE_PIERCING), oTarget);
            }
            else
            {//Do a evasion check
                int nApply = 0;
                if ( GetHasFeat( FEAT_EVASION, oTarget ) )
... (70 more lines)
```

<a id="k_inc_q_crystal"></a>

#### `k_inc_q_crystal`

**Description**: :: a_q_cryst_change

**Usage**: `#include "k_inc_q_crystal"`

**Source Code**:

```nss
//:: a_q_cryst_change
/*
Takes the quest crystal the player has, if any.
Gives the player the appropriate quest crystal for their alignment/level
*/
//:: Created By: Kevin Saunders, 06/26/04
//:: Copyright 2004 Obsidian Entertainment
#include "k_inc_utility"
int GetPCLevel()
{
    int n = GetGlobalNumber("G_PC_LEVEL");
    return(n);
}
string GetPCAlignType()
{
    string s;
    if(IsDark()) s = "1";
    if(IsNeutral()) s = "2";
    if(IsLight()) s = "3";
    if(IsDarkComplete()) s = "0";
    if(IsLightComplete()) s = "4";
    return(s);
}
int GetCrystalLevel()
{
    int n = 1 + (GetPCLevel() - 9)/3;
    if(n < 1) n = 1;
    if(n > 9) n = 9;
    return(n);
}

```

<a id="k_inc_quest_hk"></a>

#### `k_inc_quest_hk`

**Description**: Gives the player the next component needed for the HK quest.

**Usage**: `#include "k_inc_quest_hk"`

**Source Code**:

```nss
// Gives the player the next component needed for the HK quest.
// kds, 09/06/04
#include "k_inc_treas_k2"
void GiveHKPart(string sString)
{
    int k = 1;
    string sHKpart = "hkpart0";
    string sItem;
    object oItem = OBJECT_SELF;
    object oRecipient;
    if(sString != "") oRecipient = GetObjectByTag(sString);
        else oRecipient = OBJECT_SELF;
if(GetJournalEntry("RebuildHK47") < 80)
{
    for(k; GetIsObjectValid(oItem); k++)
    {
    sItem = sHKpart + IntToString(k);
    oItem = GetItemPossessedBy (GetPartyLeader(),sItem);
    }
    //AddJournalQuestEntry("LightsaberQuest",10*i);
}
CreateItemOnObject( sItem, oRecipient, 1 );
}

```

<a id="k_inc_switch"></a>

#### `k_inc_switch`

**Description**: :: k_inc_switch

**Usage**: `#include "k_inc_switch"`

**Source Code**:

```nss
//:: k_inc_switch
/*
     A simple include defining all of the
     events in the game as constants.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//DEFAULT AI EVENTS
int KOTOR_DEFAULT_EVENT_ON_HEARTBEAT           = 1001;
int KOTOR_DEFAULT_EVENT_ON_PERCEPTION          = 1002;
int KOTOR_DEFAULT_EVENT_ON_COMBAT_ROUND_END    = 1003;
int KOTOR_DEFAULT_EVENT_ON_DIALOGUE            = 1004;
int KOTOR_DEFAULT_EVENT_ON_ATTACKED            = 1005;
int KOTOR_DEFAULT_EVENT_ON_DAMAGE              = 1006;
int KOTOR_DEFAULT_EVENT_ON_DEATH               = 1007;
int KOTOR_DEFAULT_EVENT_ON_DISTURBED           = 1008;
int KOTOR_DEFAULT_EVENT_ON_BLOCKED             = 1009;
int KOTOR_DEFAULT_EVENT_ON_FORCE_AFFECTED      = 1010;
int KOTOR_DEFAULT_EVENT_ON_GLOBAL_DIALOGUE_END = 1011;
int KOTOR_DEFAULT_EVENT_ON_PATH_BLOCKED        = 1012;
//HENCHMEN AI EVENTS
int KOTOR_HENCH_EVENT_ON_HEARTBEAT           = 2001;
int KOTOR_HENCH_EVENT_ON_PERCEPTION          = 2002;
int KOTOR_HENCH_EVENT_ON_COMBAT_ROUND_END    = 2003;
int KOTOR_HENCH_EVENT_ON_DIALOGUE            = 2004;
int KOTOR_HENCH_EVENT_ON_ATTACKED            = 2005;
int KOTOR_HENCH_EVENT_ON_DAMAGE              = 2006;
int KOTOR_HENCH_EVENT_ON_DEATH               = 2007;
int KOTOR_HENCH_EVENT_ON_DISTURBED           = 2008;
int KOTOR_HENCH_EVENT_ON_BLOCKED             = 2009;
int KOTOR_HENCH_EVENT_ON_FORCE_AFFECTED      = 2010;
int KOTOR_HENCH_EVENT_ON_GLOBAL_DIALOGUE_END = 2011;
int KOTOR_HENCH_EVENT_ON_PATH_BLOCKED        = 2012;
int KOTOR_HENCH_EVENT_ON_ENTER_5m            = 2013;
int KOTOR_HENCH_EVENT_ON_EXIT_5m             = 2014;
//MISC AI EVENTS
int KOTOR_MISC_DETERMINE_COMBAT_ROUND                = 3001;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_PC          = 3002;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_INDEX_ZERO  = 3003;
// DJS-OEI 6/12/2004
// Miscellaneous KotOR2 events
// This user-defined event is sent to the Area when the player's
// created character has performed an action that is currently
// considered forbidden for combats in the area.
int KOTOR2_MISC_PC_COMBAT_FORFEIT                    = 4001;

```

<a id="k_inc_treas_k2"></a>

#### `k_inc_treas_k2`

**Description**: Treas K2

**Usage**: `#include "k_inc_treas_k2"`

**Source Code**:

```nss
#include "k_inc_q_crystal"
#include "k_inc_treasure"
/*
This include files contains the functions used to randomly generate item treasure
based upon the players' level.
Item classifications
hundreds digit = item class
tens digit = item sub-class
ones digit = specifies specific item resref
(* = these items have been created through at least level 10)
Weapons 100
*  111 - Blaster
*  121 - Blaster Rifle
*  131 - Melee
*  141 - Lightsaber (regular)
*  142 - Lightsaber (short)
*  143 - Lightsaber (Double)
Upgrades 200
Upgrade - Ranged 210
*  211 - Targeting scope
*  212 - Firing Chamber
*  213 - Power Pack
Upgrade - Melee 220
*  221 - Grip
*  222 - Edge
*  223 - Energy Cell
Upgrade - Armor 230
*  231 - Overlay
*  232 - Underlay
Upgrades - Lightsaber 240
  241 - Emitter
*  242 - Lens
  243 - Energy Cell
  244 - Crystals
  245 - Color Crystals
Equipment - 300
*  311 - Belts
*  321 - Gloves
*  331 - Head Gear
   Implants - 340
*   341 - Level 1
*   342 - Level 2
*   343 - Level 3
*   344 - Level 4
Armor - 400
*  411 - Light armor
*  421 - Medium armor
*  431 - Heavy armor
*  441 - Jedi Robes
Droid Items - 500
... (816 more lines)
```

<a id="k_inc_treasure"></a>

#### `k_inc_treasure`

**Description**: :: k_inc_treasure

**Usage**: `#include "k_inc_treasure"`

**Source Code**:

```nss
//:: k_inc_treasure
/*
     contains code for filling containers using treasure tables
*/
//:: Created By:  Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
//
//  March 15, 2003  J.B.
//      removed parts and spikes from tables
//
//constants for container types
int SWTR_DEBUG = TRUE;  //set to false to disable console/file logging
int SWTR_TABLE_CIVILIAN_CONTAINER = 1;
int SWTR_TABLE_MILITARY_CONTAINER_LOW = 2;
int SWTR_TABLE_MILITARY_CONTAINER_MID = 3;
int SWTR_TABLE_MILITARY_CONTAINER_HIGH = 4;
int SWTR_TABLE_CORPSE_CONTAINER_LOW = 5;
int SWTR_TABLE_CORPSE_CONTAINER_MID = 6;
int SWTR_TABLE_CORPSE_CONTAINER_HIGH = 7;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_LOW = 8;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_MID = 9;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_HIGH = 10;
int SWTR_TABLE_DROID_CONTAINER_LOW = 11;
int SWTR_TABLE_DROID_CONTAINER_MID = 12;
int SWTR_TABLE_DROID_CONTAINER_HIGH = 13;
int SWTR_TABLE_RAKATAN_CONTAINER = 14;
int SWTR_TABLE_SANDPERSON_CONTAINER = 15;
//Fill an object with treasure from the specified table
//This is the only function that should be used outside this include file
void SWTR_PopulateTreasure(object oContainer,int iTable,int iItems = 1,int bUnique = TRUE);
//for internal debugging use only, output string to the log file and console if desired
void SWTR_Debug_PostString(string sStr,int bConsole = TRUE,int x = 5,int y = 5,float fTime = 5.0)
{
  if(SWTR_DEBUG)
  {
    if(bConsole)
    {
      AurPostString("SWTR_DEBUG - " + sStr,x,y,fTime);
    }
    PrintString("SWTR_DEBUG - " + sStr);
  }
}
//return whether i>=iLow and i<=iHigh
int SWTR_InRange(int i,int iLow,int iHigh)
{
  if(i >= iLow && i <= iHigh)
  {
    return(TRUE);
  }
  else
... (773 more lines)
```

<a id="k_inc_utility"></a>

#### `k_inc_utility`

**Description**: :: k_inc_utility

**Usage**: `#include "k_inc_utility"`

**Source Code**:

```nss
//:: k_inc_utility
/*
    common functions used throughout various scripts
    Modified by Peter T. 17/03/03
    - Added UT_MakeNeutral2(), UT_MakeHostile1(), UT_MakeFriendly1() and UT_MakeFriendly2()
*/
//:: Created By: Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
// Plot Flag Constants.
int SW_PLOT_BOOLEAN_01 = 0;
int SW_PLOT_BOOLEAN_02 = 1;
int SW_PLOT_BOOLEAN_03 = 2;
int SW_PLOT_BOOLEAN_04 = 3;
int SW_PLOT_BOOLEAN_05 = 4;
int SW_PLOT_BOOLEAN_06 = 5;
int SW_PLOT_BOOLEAN_07 = 6;
int SW_PLOT_BOOLEAN_08 = 7;
int SW_PLOT_BOOLEAN_09 = 8;
int SW_PLOT_BOOLEAN_10 = 9;
int SW_PLOT_HAS_TALKED_TO = 10;
int SW_PLOT_COMPUTER_OPEN_DOORS = 11;
int SW_PLOT_COMPUTER_USE_GAS = 12;
int SW_PLOT_COMPUTER_DEACTIVATE_TURRETS = 13;
int SW_PLOT_COMPUTER_DEACTIVATE_DROIDS = 14;
int SW_PLOT_COMPUTER_MODIFY_DROID = 15;
int SW_PLOT_REPAIR_WEAPONS = 16;
int SW_PLOT_REPAIR_TARGETING_COMPUTER = 17;
int SW_PLOT_REPAIR_SHIELDS = 18;
int SW_PLOT_REPAIR_ACTIVATE_PATROL_ROUTE = 19;
// UserDefined events
int HOSTILE_RETREAT = 1100;
//Alignment Adjustment Constants
int SW_CONSTANT_DARK_HIT_HIGH = -6;
int SW_CONSTANT_DARK_HIT_MEDIUM = -5;
int SW_CONSTANT_DARK_HIT_LOW = -4;
int SW_CONSTANT_LIGHT_HIT_LOW = -2;
int SW_CONSTANT_LIGHT_HIT_MEDIUM = -1;
int SW_CONSTANT_LIGHT_HIT_HIGH = 0;
// Returns a pass value based on the object's level and DC rating of 0, 1, or 2 (easy, medium, difficult)
// December 20 2001: Changed so that the difficulty is determined by the
// NPC's Hit Dice
int AutoDC(int DC, int nSkill, object oTarget);
//  checks for high charisma
int IsCharismaHigh();
//  checks for low charisma
int IsCharismaLow();
//  checks for normal charisma
int IsCharismaNormal();
//  checks for high intelligence
int IsIntelligenceHigh();
... (2998 more lines)
```

<a id="k_inc_walkways"></a>

#### `k_inc_walkways`

**Description**: :: k_inc_walkways

**Usage**: `#include "k_inc_walkways"`

**Source Code**:

```nss
//:: k_inc_walkways
/*
    v1.0
    Walk Way Points Include
    used by k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
int WALKWAYS_CURRENT_POSITION = 0;
int WALKWAYS_END_POINT = 1;
int WALKWAYS_SERIES_NUMBER = 2;
int SW_FLAG_AMBIENT_ANIMATIONS  =   29;
// DJS-OEI 3/31/2004
// Modified to make room for designer-reserved values.
/*
int SW_FLAG_AMBIENT_ANIMATIONS_MOBILE = 30;
int SW_FLAG_WAYPOINT_WALK_ONCE  =   34;
int SW_FLAG_WAYPOINT_WALK_CIRCULAR  =   35;
int SW_FLAG_WAYPOINT_WALK_PATH  =   36;
int SW_FLAG_WAYPOINT_WALK_STOP  =   37; //One to three
int SW_FLAG_WAYPOINT_WALK_RANDOM    =   38;
int SW_FLAG_WAYPOINT_WALK_RUN    =   39;
int SW_FLAG_WAYPOINT_DIRECTION = 41;
int SW_FLAG_WAYPOINT_DEACTIVATE = 42;
int SW_FLAG_WAYPOINT_WALK_STOP_LONG = 46;
int SW_FLAG_WAYPOINT_WALK_STOP_RANDOM = 47;
int SW_FLAG_WAYPOINT_START_AT_NEAREST = 73;
*/
int SW_FLAG_AMBIENT_ANIMATIONS_MOBILE = 65;
int SW_FLAG_WAYPOINT_START_AT_NEAREST = 98;
int SW_FLAG_WAYPOINT_WALK_ONCE  =   99;
int SW_FLAG_WAYPOINT_WALK_CIRCULAR  =   100;
int SW_FLAG_WAYPOINT_WALK_PATH  =   101;
int SW_FLAG_WAYPOINT_WALK_RANDOM    =   103;
int SW_FLAG_WAYPOINT_WALK_RUN    =   104;
int SW_FLAG_WAYPOINT_DIRECTION = 105;
int SW_FLAG_WAYPOINT_DEACTIVATE = 106;
//new constants for WAYPOINT PAUSING
int SW_FLAG_WAYPOINT_PAUSE_SHORT  = 102;
int SW_FLAG_WAYPOINT_PAUSE_LONG   = 107;
int SW_FLAG_WAYPOINT_PAUSE_RANDOM = 108;
//old constants for WAYPOINT PAUSING. kept for backwards compatibility
int SW_FLAG_WAYPOINT_WALK_STOP        = 102;// DON'T USE ANYMORE
int SW_FLAG_WAYPOINT_WALK_STOP_LONG   = 107;// DON'T USE ANYMORE
int SW_FLAG_WAYPOINT_WALK_STOP_RANDOM = 108;// DON'T USE ANYMORE
//AWD-OEI 06/23/04 adding a local to store the waypoint animation
int SW_FLAG_USE_WAYPOINT_ANIMATION = 109;
//Makes OBJECT_SELF walk way points based on the spawn in conditions set out.
... (676 more lines)
```

<a id="k_inc_zone"></a>

#### `k_inc_zone`

**Description**: :: k_inc_zones

**Usage**: `#include "k_inc_zone"`

**Source Code**:

```nss
//:: k_inc_zones
/*
     Zone including for controlling
     the chaining of creatures
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
//Function run by the trigger to catalog the control nodes followers
void ZN_CatalogFollowers();
//Checks zone conditional on creature to if they belong to the zone
int ZN_CheckIsFollower(object oController, object oTarget);
//Checks the distance and creatures around the PC to see if it should return home.
int ZN_CheckReturnConditions();
//Gets the followers to move back to the controller object
void ZN_MoveToController(object oController, object oFollower);
//Checks to see if a specific individual needs to return to the controller.
int ZN_CheckFollowerReturnConditions(object oTarget);
//::///////////////////////////////////////////////
//:: Catalog Zone Followers
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
     Catalogs all creatures within
     the trigger area and marks
     them with an integer which
     is part of the creature's
     tag.
     Use local number SW_NUMBER_LAST_COMBO
     as a test. A new local number will
     be defined if the system works.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: April 7, 2003
//:://////////////////////////////////////////////
void ZN_CatalogFollowers()
{
    GN_PostString("FIRING", 10,10, 10.0);
    if(GetLocalBoolean(OBJECT_SELF, 10) == FALSE) //Has talked to boolean
    {
        string sZoneTag = GetTag(OBJECT_SELF);
        int nZoneNumber = StringToInt(GetStringRight(sZoneTag, 2));
        //Set up creature followers
        object oZoneFollower = GetFirstInPersistentObject();
        while(GetIsObjectValid(oZoneFollower))
        {
            SetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE, nZoneNumber);
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower = " + GN_ReturnDebugName(oZoneFollower));
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower Zone # = " + GN_ITS(GetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE)));
... (110 more lines)
```

<a id="k_oei_hench_inc"></a>

#### `k_oei_hench_inc`

**Description**: K Oei Hench Inc

**Usage**: `#include "k_oei_hench_inc"`

**Source Code**:

```nss

//:: Script Name
/*
    Desc
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
// Modified by JAB-OEI 7/23/04
// Added special scripts for the 711KOR fight with the entire party
#include "k_inc_generic"
#include "k_inc_utility"
void DoSpecialSpawnIn(object pObject);
void DoSpecialUserDefined(object pObject, int pUserEvent);
//Party Member SpawnIns
void DoAttonSpawnIn(object oPartyMember, string sModuleName);
void DoBaoDurSpawnIn(object oPartyMember, string sModuleName);
void DoMandSpawnIn(object oPartyMember, string sModuleName);
void DoDiscipleSpawnIn(object oPartyMember, string sModuleName);
void DoG0T0SpawnIn(object oPartyMember, string sModuleName);
void DoHandmaidenSpawnIn(object oPartyMember, string sModuleName);
void DoHanharrSpawnIn(object oPartyMember, string sModuleName);
void DoHK47SpawnIn(object oPartyMember, string sModuleName);
void DoKreiaSpawnIn(object oPartyMember, string sModuleName);
void DoMiraSpawnIn(object oPartyMember, string sModuleName);
void DoRemoteSpawnIn(object oPartyMember, string sModuleName);
void DoT3M4SpawnIn(object oPartyMember, string sModuleName);
void DoVisasMarrSpawnIn(object oPartyMember, string sModuleName);
//Party Member UserDefs
void DoAttonUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoBaoDurUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoMandUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoDiscipleUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoG0T0UserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoHandmaidenUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoHanharrUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoHK47UserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoKreiaUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoMiraUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoRemoteUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoT3M4UserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoVisasMarrUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoRemoteDefaultUserDef(object oPartyMember, int pUserEvent);
void Do711UserDef(object oPartyMember,int pUserEvent);
void DoSpecialSpawnIn(object pObject)
{
    AurPostString("DoSpecialSpawnIn" + GetTag(pObject), 18, 18, 3.0);
    if(GetIsObjectValid(pObject))
    {
        string tTag = GetTag(pObject);//should be a party member tag
        string sModuleName = GetModuleName();
... (1373 more lines)
```

<!-- TSL_LIBRARY_END -->

## Compilation Process


1. **Parser Creation**: `NssParser` initialized with game-specific functions/constants
2. **Source Parsing**: NSS source code parsed into Abstract Syntax Tree (AST)
3. **Function Resolution**: Function calls resolved to routine numbers via function list lookup
4. **Constant Substitution**: Constants replaced with their literal values
5. **Bytecode Generation**: AST compiled to [NCS](NCS-File-Format) bytecode instructions
6. **Optimization**: Post-compilation optimizers applied (NOP removal, etc.)

**Function Call Resolution:**

```nss
// Source code
int result = GetGlobalNumber("K_QUEST_COMPLETED");
```

```nss
// Compiler looks up "GetGlobalNumber" in KOTOR_FUNCTIONS
// Finds it at index 159 (routine number)
// Generates: ACTION 159 with 1 argument (string "K_QUEST_COMPLETED")
```

**Constant Resolution:**

```nss
// Source code
if (nPlanet == PLANET_TARIS) { ... }
```

```nss
// Compiler looks up PLANET_TARIS in KOTOR_CONSTANTS
// Finds value: 1
// Generates: CONSTI 1 (pushes integer 1 onto stack)
```

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py), [`wiki/NCS-File-Format.md#engine-function-calls`](NCS-File-Format)

---

## Commented-Out Elements in nwscript.nss

The `nwscript.nss` files in **KotOR 1 and 2** contain numerous constants and functions that [ARE](GFF-File-Format) commented out (prefixed with `//`). These represent features from the original **Neverwinter Nights (NWN)** scripting system that were **not implemented or supported in KotOR's Aurora engine variant**. BioWare deliberately disabled these elements to prevent crashes, errors, or undefined behavior if used.

### Reasons for Commented-Out Elements

KOTOR's `nwscript.nss` retains many NWN-era declarations but prefixes unsupported ones with `//` to disable them during compilation. This deliberate choice by BioWare ensures:

- **Engine Compatibility**: KOTOR's Aurora implementation lacks opcodes or assets for certain NWN features (e.g., advanced [animations](MDL-MDX-File-Format), UI behaviors), leading to crashes or no-ops if invoked.

- **Modder Safety**: Prevents accidental use in custom scripts, which would fail at runtime. file-internal comments often explicitly state `// disabled` (e.g., for creature orientation in dialogues).

- **Game-Specific Differences**: K1 and K2/TSL `nwscript.nss` vary slightly; K2 has a notorious syntax error in `SetOrientOnClick` (fixed by modders via override).

No official BioWare documentation explains this (as KOTOR predates widespread modding support), but forum consensus attributes it to engine streamlining for single-player RPG vs. NWN's multiplayer focus.

### [KEY](KEY-File-Format) Examples of Commented Elements

| Category | Examples | Notes from nwscript.nss |
|----------|----------|-------------------------|
| [animations](MDL-MDX-File-Format) | `//int ANIMATION_LOOPING_LOOK_FAR = 5;`<br>`//int ANIMATION_LOOPING_SIT_CHAIR = 6;`<br>`//int ANIMATION_LOOPING_SIT_CROSS = 7;` | Not usable in KOTOR; modders note them when scripting custom behaviors. |
| Effects/Functions | `EffectMovementSpeedIncrease` (with detailed commented description) | Function exists but capped (~200%); higher values ignored, despite "turbo" cheat allowing more. |
| Behaviors | `SetOrientOnClick` | Syntax-broken in early K2; comments note `// disabled` for orient-to-player on click. |

### Common Modder Workarounds

Modders have developed several strategies for working with commented-out elements:

- **Override nwscript.nss**: Extract from `scripts.bif` via Holocron Toolset, fix issues (e.g., K2 syntax error at line ~5710), place in `Override` folder for compilers/DeNCS.

- **Add custom constants**: Modders append new ones (e.g., for feats) rather than uncommenting old.

- **Avoid direct edits**: Messing with core declarations risks compilation failures across all scripts.

**Standard Override Workflow:**

1. Extract via Holocron Toolset (`scripts.bif > Script, Source > nwscript.nss`).
2. Edit (fix/add), save as `.nss` in `Override`.
3. Use with `nwnnsscomp` for compilation.

**K2 Syntax Fix:**

The notorious K2 syntax error in `SetOrientOnClick` can be fixed by changing:

```nss
void SetOrientOnClick( object = OBJECT_SELF, ... )
```

to:

```nss
void SetOrientOnClick( object oCreature = OBJECT_SELF, ... )
```

### Forum Discussions and Community Knowledge

Modding communities actively reference these commented sections, especially on **Deadly Stream** (primary KOTOR hub), **LucasForums archives**, **Holowan Laboratories** (via MixNMojo/Mixmojo forums), and Reddit.

| Forum | [KEY](KEY-File-Format) Threads | Topics Covered |
|-------|-------------|----------------|
| Deadly Stream | [Script Shack](https://deadlystream.com/topic/4808-fair-strides-script-shack/page/7/), [nwscript.nss Request](https://deadlystream.com/topic/6892-nwscriptnss/) | [animations](MDL-MDX-File-Format), overrides |
| LucasForums Archive | [Syntax Error](https://www.lucasforumsarchive.com/thread/142901-syntax-error-in-kotor2-nwscriptnss), [Don't Mess with It](https://www.lucasforumsarchive.com/thread/168643-im-trying-to-change-classes2da) | Fixes, warnings |
| Reddit r/kotor | [Movement Speed](https://www.reddit.com/r/kotor/comments/9dr8iy/modding_question_movement_speed_increase_in_k2/) | Effect caps |
| Czerka R&D Wiki | [nwscript.nss](https://czerka-rd.fandom.com/wiki/Nwscript.nss) | General documentation |

**Notable Discussion Points:**

- **Deadly Stream - Fair Strides' Script Shack** (2016 thread, 100+ pages): Users troubleshooting [animations](MDL-MDX-File-Format) [flag](GFF-File-Format) the exact commented lines (e.g., `ANIMATION_LOOPING_*`), confirming they can't be used natively. No successful uncommenting reported; focus on alternatives like `ActionPlayAnimation` workarounds.

- **Reddit r/kotor** (2018): Thread on speed boosts quotes the commented description for `EffectMovementSpeedIncrease` (line ~165). Users test values >200% (no effect due to cap), note "turbo" cheat bypasses it partially.

- **LucasForums Archive** (2004-2007 threads): Multiple posts warn against editing `nwscript.nss` ("very bad idea... loads of trouble"). Syntax fix for K2 widely shared; `// disabled` snippets appear in context of `SetOrientOnClick`.

### Attempts to Uncomment or Modify

- **Direct Uncommenting**: No documented successes; implied to cause runtime crashes (engine lacks implementation). Forums advise against.

- **Overrides & Additions**: Standard modding workflow (see above). Examples: TSLPatcher/TSL Patcher tools bundle fixed versions; mods like Hardcore/Improved AI reference custom includes (not core uncomments).

- **Advanced Usage**: DeNCS/ncs2nss require game-specific `nwscript.nss` for accurate decompiles; modders parse it for custom tools.

In summary, while no one has publicly shared a "uncomment everything" patch (likely futile), the modding scene thrives on careful overrides, with thousands of posts across these sites confirming the practice since 2003.

### [KEY](KEY-File-Format) Citations

- [Deadly Stream: Fair Strides' Script Shack](https://deadlystream.com/topic/4808-fair-strides-script-shack/page/7/)
- [Czerka Wiki: nwscript.nss](https://czerka-rd.fandom.com/wiki/Nwscript.nss)
- [LucasForums: Syntax Error in K2 nwscript.nss](https://www.lucasforumsarchive.com/thread/142901-syntax-error-in-kotor2-nwscriptnss)
- [Reddit: Movement Speed Modding](https://www.reddit.com/r/kotor/comments/9dr8iy/modding_question_movement_speed_increase_in_k2/)
- [Deadly Stream: nwscript.nss Thread](https://deadlystream.com/topic/6892-nwscriptnss/)
- [LucasForums: Warning on Editing nwscript.nss](https://www.lucasforumsarchive.com/thread/168643-im-trying-to-change-classes2da)

---

## Reference Implementations

**Parsing nwscript.nss:**

- [`vendor/reone/src/apps/dataminer/routines.cpp:149-184`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/routines.cpp) - Parses nwscript.nss using regex patterns for constants and functions
- [`vendor/reone/src/apps/dataminer/routines.cpp:382-427`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/routines.cpp) - Extracts functions from nwscript.nss in chitin.key for K1 and K2
- [`vendor/xoreos-tools/src/nwscript/actions.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/actions.cpp) - Actions data parsing for decompilation
- [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/ncsfile.cpp) - [NCS file](NCS-File-Format) parsing with actions data integration
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript_actions.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript_actions.cs) - Unity C# actions table
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript.cs) - Unity C# NWScript class
- [`vendor/KotOR-Scripting-Tool/NWN Script/NWScriptParser.cs`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/NWScriptParser.cs) - C# parser for nwscript.nss

**Function Definitions:**

- [`vendor/KotOR.js/src/nwscript/NWScript.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScript.ts) - TypeScript function definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts) - KotOR 1 definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK2.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK2.ts) - KotOR 2 definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptParser.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptParser.ts) - TypeScript parser for nwscript.nss
- [`vendor/KotOR.js/src/nwscript/NWScriptInstructionSet.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstructionSet.ts) - Instruction set definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptConstants.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptConstants.ts) - Constant definitions
- [`vendor/HoloLSP/server/src/nwscript/`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript/) - Language server definitions
- [`vendor/HoloLSP/server/src/nwscript-parser.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-parser.ts) - Language server parser
- [`vendor/HoloLSP/server/src/nwscript-lexer.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-lexer.ts) - Language server lexer
- [`vendor/HoloLSP/server/src/nwscript-ast.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-ast.ts) - Language server AST
- [`vendor/HoloLSP/syntaxes/nwscript.tmLanguage.json`](https://github.com/th3w1zard1/HoloLSP/blob/master/syntaxes/nwscript.tmLanguage.json) - TextMate syntax definition
- [`vendor/nwscript-mode.el/nwscript-mode.el`](https://github.com/th3w1zard1/nwscript-mode.el/blob/master/nwscript-mode.el) - Emacs mode for NWScript
- [`vendor/nwscript-ts-mode/`](https://github.com/th3w1zard1/nwscript-ts-mode) - TypeScript mode for NWScript

**Original Sources:**

- [`vendor/Vanilla_KOTOR_Script_Source`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source) - Original KotOR script sources including nwscript.nss
- [`vendor/Vanilla_KOTOR_Script_Source/K1/Data/scripts.bif/`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source/tree/master/K1/Data/scripts.bif) - KotOR 1 script sources from [BIF](BIF-File-Format)
- [`vendor/Vanilla_KOTOR_Script_Source/TSL/Vanilla/Data/Scripts/`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source/tree/master/TSL/Vanilla/Data/Scripts) - KotOR 2 script sources
- [`vendor/KotOR-Scripting-Tool/NWN Script/k1/nwscript.nss`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/k1/nwscript.nss) - KotOR 1 nwscript.nss
- [`vendor/KotOR-Scripting-Tool/NWN Script/k2/nwscript.nss`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/k2/nwscript.nss) - KotOR 2 nwscript.nss
- [`vendor/NorthernLights/Scripts/k1_nwscript.nss`](https://github.com/th3w1zard1/NorthernLights/blob/master/Scripts/k1_nwscript.nss) - KotOR 1 nwscript.nss (NorthernLights)
- [`vendor/NorthernLights/Scripts/k2_nwscript.nss`](https://github.com/th3w1zard1/NorthernLights/blob/master/Scripts/k2_nwscript.nss) - KotOR 2 nwscript.nss (NorthernLights)

**PyKotor Implementation:**

- [`Libraries/PyKotor/src/pykotor/common/script.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/script.py) - data structures (ScriptFunction, ScriptConstant, DataType)
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py) - Function and constant definitions (772 K1 functions, 1489 K1 constants)
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py) - Library file definitions (k_inc_generic, k_inc_utility, etc.)
- [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py) - Compilation integration

**Other Implementations:**

- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) - C# [NCS](NCS-File-Format) format with actions data support
- [`vendor/KotORModSync/KOTORModSync.Core/Data/NWScriptHeader.cs`](https://github.com/th3w1zard1/KotORModSync/blob/master/KOTORModSync.Core/Data/NWScriptHeader.cs) - C# NWScript header parser
- [`vendor/KotORModSync/KOTORModSync.Core/Data/NWScriptFileReader.cs`](https://github.com/th3w1zard1/KotORModSync/blob/master/KOTORModSync.Core/Data/NWScriptFileReader.cs) - C# NWScript file reader

**NWScript VM and Execution:**

- [`vendor/reone/src/libs/script/format/ncsreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp) - [NCS](NCS-File-Format) bytecode reader
- [`vendor/reone/src/libs/script/format/ncswriter.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncswriter.cpp) - [NCS](NCS-File-Format) bytecode writer
- [`vendor/xoreos/src/aurora/nwscript/`](https://github.com/th3w1zard1/xoreos/tree/master/src/aurora/nwscript) - NWScript VM implementation
- [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp) - [NCS file](NCS-File-Format) parsing and execution
- [`vendor/xoreos/src/aurora/nwscript/object.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/object.h) - NWScript object type definitions
- [`vendor/xoreos/src/engines/kotorbase/object.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/object.h) - KotOR object implementation
- [`vendor/NorthernLights/Assets/Scripts/ncs/control.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/control.cs) - Unity C# [NCS](NCS-File-Format) VM control
- [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs) - Unity C# [NCS](NCS-File-Format) reader
- [`vendor/KotOR.js/src/odyssey/controllers/NWScriptController.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/controllers/NWScriptController.ts) - TypeScript NWScript VM [controller](MDL-MDX-File-Format)
- [`vendor/KotOR.js/src/nwscript/NWScriptInstance.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstance.ts) - TypeScript NWScript instance
- [`vendor/KotOR.js/src/nwscript/NWScriptStack.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStack.ts) - TypeScript stack implementation
- [`vendor/KotOR.js/src/nwscript/NWScriptSubroutine.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptSubroutine.ts) - TypeScript subroutine handling

**Documentation and Specifications:**

- [`vendor/xoreos-docs/`](https://github.com/th3w1zard1/xoreos-docs) - xoreos documentation including format specifications
- [`vendor/xoreos-docs/specs/torlack/ncs.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/ncs.html) - [NCS](NCS-File-Format) format specification (if available)

**NWScript Language Support:**

- [`vendor/HoloLSP/server/src/kotor-definitions.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/kotor-definitions.ts) - KotOR function and constant definitions for language server
- [`vendor/HoloLSP/server/src/nwscript-runtime.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-runtime.ts) - NWScript runtime definitions
- [`vendor/HoloLSP/server/src/server.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/server.ts) - Language server implementation with NWScript support

**NWScript Parsing and Compilation:**

- [`vendor/xoreos-tools/src/nwscript/decompiler.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/decompiler.cpp) - [NCS](NCS-File-Format) decompiler implementation

**NWScript Execution:**

- [`vendor/reone/src/libs/script/execution/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/execution) - NWScript VM execution engine
- [`vendor/reone/src/libs/script/vm/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/vm) - Virtual machine implementation
- [`vendor/xoreos/src/aurora/nwscript/execution.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/execution.cpp) - NWScript execution engine
- [`vendor/xoreos/src/aurora/nwscript/variable.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/variable.cpp) - Variable handling
- [`vendor/xoreos/src/aurora/nwscript/function.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/function.cpp) - Function call handling
- [`vendor/NorthernLights/Assets/Scripts/ncs/control.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/control.cs) - Unity C# [NCS](NCS-File-Format) VM control and execution
- [`vendor/KotOR.js/src/nwscript/NWScriptController.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptController.ts) - TypeScript NWScript [controller](MDL-MDX-File-Format) and execution

**Routine Implementations:**

- [`vendor/reone/src/libs/script/routine/main/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/main) - Main routine implementations
- [`vendor/reone/src/libs/script/routine/action/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/action) - Action routine implementations
- [`vendor/reone/src/libs/script/routine/effect/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/effect) - Effect routine implementations
- [`vendor/xoreos/src/engines/kotorbase/script/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/script/routines.cpp) - KotOR-specific routine implementations

**NWScript type System:**

- [`vendor/xoreos/src/aurora/nwscript/types.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/types.h) - NWScript type definitions
- [`vendor/xoreos/src/aurora/nwscript/types.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/types.cpp) - type system implementation
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptDataType.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptDataType.ts) - TypeScript data type enumerations
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptTypes.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptTypes.ts) - TypeScript type definitions

**NWScript Events:**

- [`vendor/KotOR.js/src/nwscript/events/NWScriptEvent.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/events/NWScriptEvent.ts) - Event handling
- [`vendor/KotOR.js/src/nwscript/events/NWScriptEventFactory.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/events/NWScriptEventFactory.ts) - Event factory
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptEventType.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptEventType.ts) - Event type enumerations

**NWScript Bytecode:**

- [`vendor/KotOR.js/src/nwscript/NWScriptOPCodes.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptOPCodes.ts) - Opcode definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptInstruction.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstruction.ts) - Instruction handling
- [`vendor/KotOR.js/src/nwscript/NWScriptInstructionInfo.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstructionInfo.ts) - Instruction information
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptByteCode.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptByteCode.ts) - Bytecode enumerations

**NWScript Stack:**

- [`vendor/KotOR.js/src/nwscript/NWScriptStack.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStack.ts) - Stack implementation
- [`vendor/KotOR.js/src/nwscript/NWScriptStackVariable.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStackVariable.ts) - Stack variable handling

**NWScript Interface Definitions:**

- [`vendor/KotOR.js/src/interface/nwscript/INWScriptStoreState.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/interface/nwscript/INWScriptStoreState.ts) - Store state interface
- [`vendor/KotOR.js/src/interface/nwscript/INWScriptDefAction.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/interface/nwscript/INWScriptDefAction.ts) - Action definition interface

**NWScript AST and Parsing:**

- [`vendor/KotOR.js/src/nwscript/AST/nwscript.jison.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/AST/nwscript.jison.ts) - Jison parser grammar
- [`vendor/HoloLSP/server/src/nwscript-ast.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-ast.ts) - Abstract syntax tree definitions

**Game-Specific NWScript Extensions:**

- [`vendor/xoreos/src/engines/kotorbase/script/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/script/routines.cpp) - KotOR-specific routine implementations
- [`vendor/xoreos/src/engines/nwn/script/functions_action.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_action.cpp) - NWN action function implementations
- [`vendor/NorthernLights/Assets/Scripts/ncs/constants.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/constants.cs) - NWScript constant definitions
- [`vendor/reone/src/libs/game/script/routines.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/script/routines.cpp) - Game-specific routine implementations
- [`vendor/reone/include/reone/game/script/routines.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/game/script/routines.h) - Game routine header
- [`vendor/xoreos-tools/src/nwscript/subroutine.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/subroutine.cpp) - Subroutine handling
- [`vendor/xoreos-tools/src/nwscript/subroutine.h`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/subroutine.h) - Subroutine header
- [`vendor/xoreos/src/engines/kotorbase/types.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/types.h) - KotOR type definitions including base item types
- [`vendor/KotOR.js/src/module/Module.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/Module.ts) - Module loading and management
- [`vendor/KotOR.js/src/module/ModuleArea.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleArea.ts) - Area management and transitions
- [`vendor/xoreos/src/engines/nwn/module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/module.cpp) - NWN module implementation
- [`vendor/xoreos/src/engines/nwn2/module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/module.cpp) - NWN2 module implementation
- [`vendor/xoreos/src/engines/nwn2/module.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/module.h) - NWN2 module header
- [`vendor/xoreos/src/engines/dragonage2/script/functions_module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/dragonage2/script/functions_module.cpp) - Dragon Age 2 module functions
- [`vendor/xoreos/src/engines/nwn/script/functions_effect.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_effect.cpp) - NWN effect function implementations
- [`vendor/xoreos/src/engines/nwn/script/functions_object.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_object.cpp) - NWN object function implementations
- [`vendor/xoreos/src/engines/nwn2/script/functions.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/script/functions.cpp) - NWN2 function implementations
- [`vendor/reone/src/libs/script/routine/action/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/action) - Action routine implementations
- [`vendor/reone/src/libs/script/routine/effect/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/effect) - Effect routine implementations
- [`vendor/reone/src/libs/script/routine/object/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/object) - Object routine implementations
- [`vendor/reone/src/libs/script/routine/party/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/party) - Party routine implementations
- [`vendor/reone/src/libs/script/routine/combat/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/combat) - Combat routine implementations
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript_actions.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript_actions.cs) - Complete actions table mapping routine numbers to function names
- [`vendor/NorthernLights/Assets/Scripts/Systems/AuroraActions/AuroraAction.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/Systems/AuroraActions/AuroraAction.cs) - Action system implementation

---

### Other Constants

See [Other Constants](NSS-TSL-Only-Constants-Other-Constants) for detailed documentation.

## Cross-References

- **[NCS File Format](NCS-File-Format.md)**: Compiled bytecode format that NSS compiles to
- **[GFF File Format](GFF-File-Format.md)**: Scripts [ARE](GFF-File-Format) stored in [GFF](GFF-File-Format) files ([UTC](GFF-File-Format), [UTD](GFF-File-Format), etc.)
- **[KEY File Format](KEY-File-Format.md)**: nwscript.nss is stored in [chitin.key](KEY-File-Format)
