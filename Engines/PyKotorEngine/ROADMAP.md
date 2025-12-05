# PyKotorEngine Development Roadmap

This document tracks the implementation progress of PyKotorEngine, a Panda3D-based engine for rendering Knights of the Old Republic game content. The implementation follows patterns from vendor projects: reone, xoreos, kotor.js, and northernlights.

## Architecture Principles

1. **Use Libraries as much as possible**: Keep engine code focused on Panda3D-specific integration
2. **Follow vendor patterns**: Match reone/xoreos/kotor.js/northernlights implementations as closely as possible
3. **Comprehensive testing**: Write industry-standard pytest tests (no mocks)
4. **Separation of concerns**: Engine = Panda3D integration, Libraries = reusable logic

## Implementation Status

### ✅ Completed

#### Core Engine

- [x] Basic engine initialization (KotorEngine class)
- [x] Panda3D ShowBase integration
- [x] Window configuration and setup
- [x] Default lighting (ambient + directional)
- [x] Scene root creation

#### MDL Model Loading

- [x] Basic MDL/MDX file loading
- [x] Node hierarchy conversion
- [x] Mesh node conversion (basic)
- [x] Vertex format creation (position, normal, UV, tangent space)
- [x] Tangent space computation (moved to Libraries)
- [x] Face winding order handling
- [x] Node type detection (abstracted to PyKotorGL)
- [x] Geometry utilities extraction to Libraries

#### Animation System

- [x] Animation controller base class
- [x] Position controller
- [x] Orientation controller (quaternion SLERP)
- [x] Scale controller
- [x] Color controller
- [x] Alpha controller
- [x] Animation state management
- [x] Animation manager (basic)
- [x] Keyframe interpolation

#### Scene Graph

- [x] Basic scene graph implementation
- [x] Model root management
- [x] Ambient lighting
- [x] Directional lights
- [x] Point lights
- [x] Fog properties

#### Material System

- [x] Basic material manager
- [x] KotOR shader integration (basic)

### 🚧 In Progress

#### MDL Model Loading

- [x] Basic skin mesh geometry (bone weights in vertex format)
- [x] Skeletal animation (bone transforms, skinning matrices - bone hierarchy storage complete)
- [x] Dangly mesh physics constraints (displacement, tightness, period - property storage complete)
- [x] Saber mesh special rendering (saber material flags - property storage complete)
- [x] AABB/walkmesh collision geometry (invisible collision meshes - data storage complete)
- [x] Light node conversion (point/directional lights)
- [x] Emitter node conversion (particle systems - property storage complete)
- [x] Reference node loading (child model loading)

### 📋 Planned

#### Core Engine

- [ ] Resource manager (texture/model caching)
- [ ] Module loading (LYT, GIT, IFO)
- [ ] Area/room management
- [ ] Camera controller
- [ ] Input handling
- [ ] Event system
- [ ] Script integration (NWScript)

#### MDL Model Loading

- [ ] Complete all node type conversions
- [ ] Optimize vertex buffer creation
- [ ] Instance rendering support
- [ ] LOD (Level of Detail) support
- [ ] Model batching/merging

#### Animation System

- [ ] Skeletal animation (bone hierarchy)
- [ ] Animation blending
- [ ] Animation events/callbacks
- [ ] Bezier curve interpolation
- [ ] Animation layers
- [ ] Root motion extraction

#### Rendering Pipeline

- [ ] KotOR-specific shader system
- [ ] Material property mapping
- [ ] Texture atlas support
- [ ] Lightmap rendering
- [ ] Normal mapping
- [ ] Shadow mapping
- [ ] Post-processing effects
- [ ] Render passes (retro/PBR)

#### Particle Systems

- [ ] Emitter node implementation
- [ ] Particle spawning
- [ ] Particle physics
- [ ] Texture animation
- [ ] Billboard rendering

#### Scene Management

- [ ] Walkmesh/collision detection
- [ ] Trigger zones
- [ ] Sound nodes
- [ ] Camera nodes
- [ ] Door/transition handling
- [ ] Placeable objects
- [ ] Creature rendering
- [ ] Item rendering

#### Module System

- [ ] LYT (layout) file loading
- [ ] GIT (game instance template) loading
- [ ] Room/area management
- [ ] Door connections
- [ ] Waypoint system
- [ ] Encounter spawning
- [ ] Store/merchant system

#### Performance

- [ ] Frustum culling
- [ ] Occlusion culling
- [ ] Level-of-detail (LOD)
- [ ] Texture streaming
- [ ] Model instancing
- [ ] Batching optimization

#### Testing

- [ ] Unit tests for MDL loader
- [ ] Unit tests for animation system
- [ ] Unit tests for scene graph
- [ ] Integration tests with real MDL files
- [ ] Performance benchmarks

## Vendor Reference Mapping

### reone (C++)

- `src/libs/scene/graph.cpp` → Scene graph management
- `src/libs/scene/node/model.cpp` → Model loading and node hierarchy
- `src/libs/scene/node/mesh.cpp` → Mesh conversion
- `src/libs/scene/node/light.cpp` → Light nodes
- `src/libs/scene/node/emitter.cpp` → Particle emitters
- `src/libs/scene/animation/` → Animation system
- `src/libs/graphics/mesh.cpp` → Geometry processing

### kotor.js (TypeScript/Three.js)

- `src/three/odyssey/OdysseyModel3D.ts` → Model loading
- `src/odyssey/controllers/` → Animation controllers
- `src/odyssey/OdysseyModelAnimation.ts` → Animation state

### xoreos (C++)

- `src/graphics/mesh.cpp` → Mesh conversion
- `src/graphics/windowman.cpp` → Window management

## File Structure

```
Engines/
├── src/pykotor/engine/panda3d/
│   ├── engine.py              ✅ Basic engine
│   ├── mdl_loader.py          🚧 Model loading (in progress)
│   ├── animation.py            ✅ Animation controllers
│   ├── scene_graph.py         ✅ Scene management
│   ├── module_loader.py       ✅ Module loading (LYT/GIT)
│   ├── materials/
│   │   ├── manager.py         ✅ Material manager
│   │   └── *.frag, *.vert     ✅ Shaders
│   ├── resources/
│   │   └── texture_loader.py  ✅ TPC texture loading
│   └── legacy/                📋 Old code (to be removed)
├── PyKotorEngine/
│   ├── tests/                 📋 Planned
│   └── ROADMAP.md             ✅ This file
```

**Note**: Source code is in `Engines/src/pykotor/engine/` to allow namespace expansion:

- `from pykotor.engine.panda3d.mdl_loader import MDLLoader`
- `from pykotor.engine.panda3d.engine import KotorEngine`

## Next Steps (Priority Order)

1. **Complete MDL node type support** (skin, dangly, saber, emitter, light, reference)
2. **Implement skeletal animation** (bone weights, skinning matrices)
3. **Add particle system support** (emitter nodes)
4. **Implement module loading** (LYT, GIT files)
5. **Add comprehensive testing** (pytest with real game files)
6. **Optimize rendering pipeline** (batching, culling, LOD)

## Notes

- All geometry utilities should be in `Libraries/PyKotor/src/pykotor/common/geometry_utils.py`
- All abstract MDL conversion logic should be in `Libraries/PyKotorGL/src/pykotor/gl/models/mdl_converter.py`
- Engine code should only contain Panda3D-specific integration (NodePath, GeomNode, etc.)
- Follow vendor code patterns closely, but adapt to Python/Panda3D idioms

---

## Game Logic Features

### Core Systems

- [ ] Basic module loading/rendering
- [ ] Basic character movement
- [ ] Object targeting
- [ ] Pathfinding
- [ ] Cursors
- [ ] Items
- [ ] Triggers
- [ ] Conversations
- [ ] Script routines
- [ ] Actions
- [ ] Stunt animations
- [ ] Area sounds
- [ ] Containers
- [ ] Party management
- [ ] Saving games
- [ ] Perception
- [ ] Skills
- [ ] Feats
- [ ] Force powers
- [ ] Combat
- [ ] Effects
- [ ] Grenades
- [ ] Traps (mines)
- [ ] Encounters
- [ ] Stores
- [ ] Stealth
- [ ] Map exploration
- [ ] Listening patterns

### GUI Screens

- [ ] Main menu
- [ ] Equipment
- [ ] Inventory
- [ ] Character sheet
- [ ] Abilities
- [ ] Character creation
- [ ] Level up
- [ ] Messages/feedback
- [ ] Journal
- [ ] Map
- [ ] Options
- [ ] Workbench
- [ ] Lab station
- [ ] Loading screen

### Mini-games

- [ ] Swoop racing
- [ ] Man the turrets
- [ ] Pazaak

### Other

- [ ] Multiplayer
- [ ] Real-time combat

## Graphics / Scene Management

- [ ] Textures (TPC, TGA, TXI)
- [ ] Models, animations (MDL, MDX)
- [ ] Walkmeshes (WOK, DWK, PWK)
- [ ] Lip animations
- [ ] Collision detection
- [ ] 3D picking
- [ ] Grass
- [ ] Fog
- [ ] Emitters
- [ ] Danglymeshes
- [ ] Lightsabers

### Advanced Rendering

- [ ] Physically-based rendering
  - [ ] Image-based lighting
- [ ] Cascaded shadow maps
- [ ] Reflection probes
- [ ] Screen-space ambient occlusion
- [ ] Screen-space reflections
- [ ] Order-independent transparency
- [ ] Anti-aliasing (FXAA)

## Supporting Subsystems

- [ ] Resource management (KEY, BIF, ERF, RIM, MOD, 2DA, GFF)
- [ ] Audio playback (WAV, MP3)
- [ ] Script execution (NCS)
- [ ] Movie playback (BIK)
- [ ] GUI controls

## Actions

- [ ] PlayAnimation
- [ ] DoCommand
- [ ] UseTalentOnObject
- [ ] Wait
- [ ] StartConversation
- [ ] MoveToObject
- [ ] Attack
- [ ] PauseConversation
- [ ] ForceMoveToObject
- [ ] ResumeConversation
- [ ] MoveAwayFromObject
- [ ] EquipMostDamagingMelee
- [ ] EquipMostDamagingRanged
- [ ] FollowLeader
- [ ] MoveToLocation
- [ ] JumpToObject
- [ ] JumpToLocation
- [ ] OpenDoor
- [ ] CloseDoor
- [ ] RandomWalk
- [ ] EquipItem
- [ ] UnequipItem
- [ ] CastFakeSpellAtObject
- [ ] TakeItem
- [ ] GiveItem
- [ ] SurrenderToEnemies
- [ ] UnlockObject
- [ ] CastSpellAtObject
- [ ] ForceMoveToLocation
- [ ] LockObject
- [ ] CastFakeSpellAtLocation
- [ ] InteractObject
- [ ] BarkString
- [ ] UseSkill
- [ ] SwitchWeapons
- [ ] FollowOwner
- [ ] PickUpItem
- [ ] PutDownItem
- [ ] SpeakString
- [ ] ForceFollowObject
- [ ] CastSpellAtLocation
- [ ] SpeakStringByStrRef
- [ ] UseFeat
- [ ] UseTalentAtLocation
- [ ] MoveAwayFromLocation
- [ ] EquipMostEffectiveArmor

## Effects

- [ ] VisualEffect
- [ ] Heal
- [ ] Resurrection
- [ ] Beam
- [ ] Damage
- [ ] Death
- [ ] LinkEffects
- [ ] Choke
- [ ] AbilityIncrease
- [ ] HealForcePoints
- [ ] ForcePushTargeted
- [ ] Poison
- [ ] DroidStun
- [ ] Horrified
- [ ] DamageResistance
- [ ] AssuredHit
- [ ] ForcePushed
- [ ] Disguise
- [ ] Sleep
- [ ] ForceFizzle
- [ ] SavingThrowIncrease
- [ ] Stunned
- [ ] DamageImmunityIncrease
- [ ] Paralyze
- [ ] DamageIncrease
- [ ] AttackIncrease
- [ ] CutSceneParalyze
- [ ] MovementSpeedDecrease
- [ ] ACDecrease
- [ ] DamageForcePoints
- [ ] ACIncrease
- [ ] MovementSpeedIncrease
- [ ] AbilityDecrease
- [ ] Entangle
- [ ] ForceShield
- [ ] ForceResisted
- [ ] LightsaberThrow
- [ ] Immunity
- [ ] TemporaryHitpoints
- [ ] WhirlWind
- [ ] ModifyAttacks
- [ ] ForceResistanceIncrease
- [ ] SkillIncrease
- [ ] TemporaryForcePoints
- [ ] AttackDecrease
- [ ] SavingThrowDecrease
- [ ] Regenerate
- [ ] BodyFuel
- [ ] TrueSeeing
- [ ] PsychicStatic
- [ ] Invisibility
- [ ] BlasterDeflectionIncrease
- [ ] CutSceneHorrified
- [ ] DamageDecrease
- [ ] CutSceneStunned
- [ ] VPRegenModifier
- [ ] FactionModifier
- [ ] Blind
- [ ] MindTrick
- [ ] ForceBody
- [ ] Fury
- [ ] Crush
- [ ] ForceSight
- [ ] DroidScramble
- [ ] DamageReduction
- [ ] Knockdown
- [ ] SpellImmunity
- [ ] ForceJump
- [ ] Confused
- [ ] Frightened
- [ ] AreaOfEffect
- [ ] AssuredDeflection
- [ ] Haste
- [ ] HitPointChangeWhenDying
- [ ] DamageImmunityDecrease
- [ ] SkillDecrease
- [ ] ForceResistanceDecrease
- [ ] Concealment
- [ ] DispelMagicAll
- [ ] SeeInvisible
- [ ] TimeStop
- [ ] BlasterDeflectionDecrease
- [ ] SpellLevelAbsorption
- [ ] DispelMagicBest
- [ ] MissChance
- [ ] DamageShield
- [ ] ForceDrain
- [ ] FPRegenModifier
- [ ] DroidConfused

## Script Routines

- [ ] GetIsObjectValid
- [ ] GetHasSpell
- [ ] GetBaseItemType
- [ ] IntToString
- [ ] TalentSpell
- [ ] Random
- [ ] GetIsTalentValid
- [ ] GetObjectByTag
- [ ] GetCreatureTalentRandom
- [ ] GetCreatureHasTalent
- [ ] ActionPlayAnimation
- [ ] AssignCommand
- [ ] GetFirstPC
- [ ] ClearAllActions
- [ ] GetWaypointByTag
- [ ] GetIdFromTalent
- [ ] DelayCommand
- [ ] GetRacialType
- [ ] GetPartyMemberByIndex
- [ ] ActionDoCommand
- [ ] GetGlobalNumber
- [ ] GetHasSpellEffect
- [ ] GetTag
- [ ] IsObjectPartyMember
- [ ] SetLocalNumber
- [ ] GetLocalNumber
- [ ] SetListenPattern
- [ ] GetLocation
- [ ] GetNearestCreature
- [ ] GetGlobalBoolean
- [ ] CreateItemOnObject
- [ ] ActionUseTalentOnObject
- [ ] IntToFloat
- [ ] SetGlobalNumber
- [ ] GiveXPToCreature
- [ ] GetCurrentHitPoints
- [ ] GetDistanceBetween
- [ ] GetIsDead
- [ ] SetLocalBoolean
- [ ] GetLocalBoolean
- [ ] GetNPCAIStyle
- [ ] ApplyEffectToObject
- [ ] GetHitDice
- [ ] GetHasFeat
- [ ] SetGlobalBoolean
- [ ] d6
- [ ] GetLevelByClass
- [ ] GetGender
- [ ] GetObjectSeen
- [ ] ActionWait
- [ ] GetCreatureTalentBest
- [ ] GetIsEnemy
- [ ] DestroyObject
- [ ] GetStandardFaction
- [ ] ActionStartConversation
- [ ] ActionMoveToObject
- [ ] GetNearestObjectByTag
- [ ] GetMaxHitPoints
- [ ] d100
- [ ] GetTypeFromTalent
- [ ] ActionAttack
- [ ] CancelCombat
- [ ] ActionPauseConversation
- [ ] ActionForceMoveToObject
- [ ] d3
- [ ] GetItemInSlot
- [ ] ActionResumeConversation
- [ ] GetPCSpeaker
- [ ] SetCommandable
- [ ] GetIsPC
- [ ] ShipBuild
- [ ] GetFirstObjectInShape
- [ ] GetNextObjectInShape
- [ ] GetIsDebilitated
- [ ] CreateObject
- [ ] GetStringByStrRef
- [ ] ChangeToStandardFaction
- [ ] GetPosition
- [ ] d8
- [ ] GetStringLength
- [ ] GetStringLeft
- [ ] JumpToObject
- [ ] d12
- [ ] GetDistanceToObject2D
- [ ] GetDistanceBetween2D
- [ ] AurPostString
- [ ] GetEnteringObject
- [ ] ObjectToString
- [ ] GetItemPossessedBy
- [ ] GetLastHostileTarget
- [ ] EffectVisualEffect
- [ ] SetFacingPoint
- [ ] StringToInt
- [ ] GetStringRight
- [ ] SetListening
- [ ] GetSubRace
- [ ] PrintString
- [ ] GetIsEncounterCreature
- [ ] SignalEvent
- [ ] GetFirstItemInInventory
- [ ] GetAttackTarget
- [ ] GetIsEffectValid
- [ ] GetNextItemInInventory
- [ ] GetUserDefinedEventNumber
- [ ] GetFirstEffect
- [ ] GetNextEffect
- [ ] GetName
- [ ] GetEffectType
- [ ] GetPlayerRestrictMode
- [ ] FloatToString
- [ ] ActionMoveAwayFromObject
- [ ] TalentFeat
- [ ] GetPartyAIStyle
- [ ] EventUserDefined
- [ ] GetCategoryFromTalent
- [ ] GetLastForcePowerUsed
- [ ] SetGlobalFadeOut
- [ ] StartNewModule
- [ ] NoClicksFor
- [ ] EffectHeal
- [ ] GetArea
- [ ] SetGlobalFadeIn
- [ ] EffectResurrection
- [ ] SetLocked
- [ ] IsNPCPartyMember
- [ ] SetPartyLeader
- [ ] GetAttemptedAttackTarget
- [ ] GetIsFriend
- [ ] EffectBeam
- [ ] PlayAnimation
- [ ] AddJournalQuestEntry
- [ ] ApplyEffectAtLocation
- [ ] GetFacing
- [ ] SetFacing
- [ ] GetLastHostileActor
- [ ] ActionEquipMostDamagingMelee
- [ ] ActionEquipMostDamagingRanged
- [ ] GetCommandable
- [ ] GetSoloMode
- [ ] d4
- [ ] GetUserActionsPending
- [ ] ActionFollowLeader
- [ ] GetLastAttackAction
- [ ] GetLastCombatFeatUsed
- [ ] GetLastAttackResult
- [ ] GetWasForcePowerSuccessful
- [ ] ExecuteScript
- [ ] ActionMoveToLocation
- [ ] GetSkillRank
- [ ] SoundObjectPlay
- [ ] FloatToInt
- [ ] EffectDamage
- [ ] EffectDeath
- [ ] PlaySound
- [ ] RevealMap
- [ ] ActionJumpToObject
- [ ] SetItemStackSize
- [ ] Vector
- [ ] GiveGoldToCreature
- [ ] SetDialogPlaceableCamera
- [ ] ActionJumpToLocation
- [ ] ActionOpenDoor
- [ ] GetGold
- [ ] GetItemStackSize
- [ ] AddAvailableNPCByTemplate
- [ ] TakeGoldFromCreature
- [ ] IsAvailableCreature
- [ ] GetFirstObjectInArea
- [ ] GetNextObjectInArea
- [ ] ActionCloseDoor
- [ ] SWMG_PlayAnimation
- [ ] ClearAllEffects
- [ ] JumpToLocation
- [ ] GetNearestObject
- [ ] RemoveJournalQuestEntry
- [ ] GetPartyMemberCount
- [ ] EffectLinkEffects
- [ ] PlayRoomAnimation
- [ ] GetDistanceToObject
- [ ] ActionRandomWalk
- [ ] SetMinOneHP
- [ ] SetPlotFlag
- [ ] RemovePartyMember
- [ ] GetModule
- [ ] GetLocked
- [ ] GetIsInConversation
- [ ] GetLastUsedBy
- [ ] GetGoodEvilValue
- [ ] VectorNormalize
- [ ] GetSubString
- [ ] BarkString
- [ ] ActionEquipItem
- [ ] AdjustAlignment
- [ ] SetCustomToken
- [ ] ActionUnequipItem
- [ ] GiveItem
- [ ] SetMapPinEnabled
- [ ] SetLockOrientationInDialog
- [ ] ShowPartySelectionGUI
- [ ] CutsceneAttack
- [ ] PlayMovie
- [ ] SetPlanetSelectable
- [ ] EffectChoke
- [ ] GetLevelByPosition
- [ ] SaveNPCState
- [ ] GetIsInCombat
- [ ] AddPartyMember
- [ ] SoundObjectStop
- [ ] GetAttemptedSpellTarget
- [ ] SetNPCAIStyle
- [ ] ActionCastFakeSpellAtObject
- [ ] GetSpellId
- [ ] SetEffectIcon
- [ ] SpawnAvailableNPC
- [ ] AdjustReputation
- [ ] OpenStore
- [ ] EventSpellCastAt
- [ ] EffectAbilityIncrease
- [ ] SetEncounterActive
- [ ] GetCurrentForcePoints
- [ ] GetNumStackedItems
- [ ] ActionTakeItem
- [ ] RemoveEffect
- [ ] FindSubString
- [ ] GetLastPazaakResult
- [ ] GetIsNeutral
- [ ] EffectHealForcePoints
- [ ] GetExitingObject
- [ ] SurrenderToEnemies
- [ ] PlayPazaak
- [ ] EffectForcePushTargeted
- [ ] ActionGiveItem
- [ ] GetJournalEntry
- [ ] GetIsConversationActive
- [ ] ActionSurrenderToEnemies
- [ ] SpeakString
- [ ] SoundObjectFadeAndStop
- [ ] GetSpellTargetLocation
- [ ] d20
- [ ] SetLockHeadFollowInDialog
- [ ] EffectPoison
- [ ] SetAreaUnescapable
- [ ] MusicBackgroundStop
- [ ] GetMaxForcePoints
- [ ] abs
- [ ] SetItemNonEquippable
- [ ] GetEffectSpellId
- [ ] GetLoadFromSaveGame
- [ ] GivePlotXP
- [ ] SetPlanetAvailable
- [ ] PlayRumblePattern
- [ ] EffectDroidStun
- [ ] d10
- [ ] Location
- [ ] SetLightsaberPowered
- [ ] GetAbilityScore
- [ ] GetFirstInPersistentObject
- [ ] SWMG_SetPlayerAccelerationPerSecond
- [ ] EffectHorrified
- [ ] EffectDamageResistance
- [ ] EffectAssuredHit
- [ ] SetIsDestroyable
- [ ] GetCurrentAction
- [ ] SWMG_SetPlayerMinSpeed
- [ ] SWMG_SetPlayerMaxSpeed
- [ ] EffectForcePushed
- [ ] GetIsLiveContentAvailable
- [ ] EffectDisguise
- [ ] BeginConversation
- [ ] SWMG_GetPlayer
- [ ] GetLastPerceived
- [ ] MusicBackgroundPlay
- [ ] MusicBattlePlay
- [ ] GetAttemptedMovementTarget
- [ ] AwardStealthXP
- [ ] EffectSleep
- [ ] SetNPCSelectability
- [ ] ActionUnlockObject
- [ ] RemoveAvailableNPC
- [ ] SWMG_RemoveAnimation
- [ ] GetIsOpen
- [ ] EffectForceFizzle
- [ ] GetNextInPersistentObject
- [ ] GetRunScriptVar
- [ ] EndGame
- [ ] GetModuleItemAcquired
- [ ] GetLastOpenedBy
- [ ] ReflexSave
- [ ] EffectSavingThrowIncrease
- [ ] SWMG_GetPlayerSpeed
- [ ] GetTimeHour
- [ ] AddToParty
- [ ] GetAbilityModifier
- [ ] GetListenPatternNumber
- [ ] EffectStunned
- [ ] GetLastAttacker
- [ ] EffectDamageImmunityIncrease
- [ ] EffectParalyze
- [ ] GetSpellTargetObject
- [ ] GetSpellTarget
- [ ] GetLastSpeaker
- [ ] EffectDamageIncrease
- [ ] ChangeFactionByFaction
- [ ] GetObjectType
- [ ] SWMG_SetPlayerSpeed
- [ ] GetTimeMinute
- [ ] GetTimeSecond
- [ ] GetTimeMillisecond
- [ ] GetClassByPosition
- [ ] SetReturnStrref
- [ ] GetFactionEqual
- [ ] GetModuleFileName
- [ ] GetCurrentStealthXP
- [ ] GetHasInventory
- [ ] AddAvailableNPCByObject
- [ ] EffectAttackIncrease
- [ ] EffectCutSceneParalyze
- [ ] GetXP
- [ ] MusicBattleStop
- [ ] SurrenderRetainBuffs
- [ ] EffectMovementSpeedDecrease
- [ ] SWMG_GetPosition
- [ ] ShowUpgradeScreen
- [ ] GetAppearanceType
- [ ] DisplayFeedBackText
- [ ] EffectACDecrease
- [ ] WillSave
- [ ] SetPlayerRestrictMode
- [ ] EffectDamageForcePoints
- [ ] ActionCastSpellAtObject
- [ ] HoldWorldFadeInForDialog
- [ ] ActionForceMoveToLocation
- [ ] ActionLockObject
- [ ] EffectACIncrease
- [ ] EffectMovementSpeedIncrease
- [ ] EffectAbilityDecrease
- [ ] GetGlobalLocation
- [ ] SWMG_SetLateralAccelerationPerSecond
- [ ] SWMG_OnDeath
- [ ] SWMG_SetPlayerTunnelPos
- [ ] SWMG_SetPlayerTunnelNeg
- [ ] GetLastPerceptionSeen
- [ ] GetIsLinkImmune
- [ ] SoundObjectSetVolume
- [ ] SWMG_SetSpeedBlurEffect
- [ ] SetGlobalLocation
- [ ] EffectEntangle
- [ ] ActionCastFakeSpellAtLocation
- [ ] ChangeItemCost
- [ ] GetLastDamager
- [ ] EffectForceShield
- [ ] SetGlobalString
- [ ] ResistForce
- [ ] GetEncounterActive
- [ ] MusicBackgroundChangeDay
- [ ] MusicBackgroundChangeNight
- [ ] GetNPCSelectability
- [ ] SwitchPlayerCharacter
- [ ] ShowTutorialWindow
- [ ] ResetDialogState
- [ ] AddMultiClass
- [ ] GetIsPoisoned
- [ ] d2
- [ ] FortitudeSave
- [ ] GetPlotFlag
- [ ] EffectForceResisted
- [ ] GetIsDoorActionPossible
- [ ] DoDoorAction
- [ ] EffectLightsaberThrow
- [ ] SetXP
- [ ] GetLastSpell
- [ ] CreateItemOnFloor
- [ ] GetNextPC
- [ ] SWMG_GetIsInvulnerable
- [ ] SWMG_GetPlayerAccelerationPerSecond
- [ ] EffectImmunity
- [ ] GetReflexAdjustedDamage
- [ ] SWMG_AdjustFollowerHitPoints
- [ ] SWMG_GetLastFollowerHit
- [ ] SWMG_StartInvulnerability
- [ ] EffectTemporaryHitpoints
- [ ] RoundsToSeconds
- [ ] SoundObjectSetFixedVariance
- [ ] GetGlobalString
- [ ] GetLastSpellCaster
- [ ] EffectWhirlWind
- [ ] CancelPostDialogCharacterSwitch
- [ ] ActionInteractObject
- [ ] RemoveFromParty
- [ ] ActionBarkString
- [ ] DisableVideoEffect
- [ ] EffectModifyAttacks
- [ ] SWMG_GetHitPoints
- [ ] SetSoloMode
- [ ] ActionUseSkill
- [ ] EffectForceResistanceIncrease
- [ ] ShowGalaxyMap
- [ ] GetLastPerceptionVanished
- [ ] GetBlockingDoor
- [ ] GetTotalDamageDealt
- [ ] GetCreatureSize
- [ ] SWMG_GetEnemy
- [ ] PauseGame
- [ ] GetSpellSaveDC
- [ ] EffectSkillIncrease
- [ ] GetInventoryDisturbItem
- [ ] AmbientSoundPlay
- [ ] AmbientSoundStop
- [ ] GetSelectedPlanet
- [ ] GetEffectCreator
- [ ] EffectTemporaryForcePoints
- [ ] GetInventoryDisturbType
- [ ] GetItemActivated
- [ ] SetMaxStealthXP
- [ ] SetCurrentStealthXP
- [ ] SetStealthXPEnabled
- [ ] StartCreditSequence
- [ ] IsCreditSequenceInProgress
- [ ] PlayVisualAreaEffect
- [ ] SurrenderByFaction
- [ ] SetAvailableNPCId
- [ ] GetPositionFromLocation
- [ ] GetHasSkill
- [ ] QueueMovie
- [ ] EnableVideoEffect
- [ ] PlayMovieQueue
- [ ] EffectAttackDecrease
- [ ] GetTrapBaseType
- [ ] SWMG_SetFollowerHitPoints
- [ ] EffectSavingThrowDecrease
- [ ] SWMG_GetPlayerOffset
- [ ] SoundObjectGetPitchVariance
- [ ] SetMaxHitPoints
- [ ] EffectRegenerate
- [ ] SWMG_OnDamage
- [ ] EffectBodyFuel
- [ ] GetIsImmune
- [ ] GetLastSpellHarmful
- [ ] EffectTrueSeeing
- [ ] GetBlockingCreature
- [ ] GetFoundEnemyCreature
- [ ] DuplicateHeadAppearance
- [ ] GetCreatureMovmentType
- [ ] EffectPsychicStatic
- [ ] GetMinOneHP
- [ ] GetAreaUnescapable
- [ ] GetItemPossessor
- [ ] GetSubScreenID
- [ ] GetCasterLevel
- [ ] GetMetaMagicFeat
- [ ] HoursToSeconds
- [ ] GetFactionAverageReputation
- [ ] ShowLevelUpGUI
- [ ] SetButtonMashCheck
- [ ] GetLastPlayerDied
- [ ] GetDamageDealtByType
- [ ] GetLastKiller
- [ ] GetItemActivator
- [ ] EffectInvisibility
- [ ] EffectBlasterDeflectionIncrease
- [ ] DoSinglePlayerAutoSave
- [ ] MusicBackgroundGetBattleTrack
- [ ] SWMG_GetEnemyCount
- [ ] GetCheatCode
- [ ] SetMusicVolume
- [ ] GetScriptParameter
- [ ] GetPartyLeader
- [ ] GetObjectPersonalSpace
- [ ] IncrementGlobalNumber
- [ ] SetHealTarget
- [ ] GetModuleName
- [ ] GetRandomDestination
- [ ] GetScriptStringParameter
- [ ] GetPUPOwner
- [ ] GetIsPuppet
- [ ] ActionSwitchWeapons
- [ ] GetIsPartyLeader
- [ ] SetFadeUntilScript
- [ ] IsStealthed
- [ ] GetSpellAcquired
- [ ] HasLineOfSight
- [ ] SetCreatureAILevel
- [ ] ActionFollowOwner
- [ ] GetHealTarget
- [ ] GetSpellBaseForcePointCost
- [ ] GetCombatActionsPending
- [ ] GetInfluence
- [ ] SetOrientOnClick
- [ ] ResetCreatureAILevel
- [ ] RemoveNPCFromPartyToBase
- [ ] SWMG_GetSwoopUpgrade
- [ ] SetKeepStealthInDialog
- [ ] CreatureFlourishWeapon
- [ ] AdjustCreatureAttributes
- [ ] SetFakeCombatState
- [ ] SetForceAlwaysUpdate
- [ ] SetForfeitConditions
- [ ] GrantSpell
- [ ] RemoveHeartbeat
- [ ] GetIsXBox
- [ ] SpawnMine
- [ ] RemoveEffectByID
- [ ] SetInfluence
- [ ] SWMG_GetMaxHitPoints
- [ ] ModifyInfluence
- [ ] IsFormActive
- [ ] ForceHeartbeat
- [ ] EnableRendering
- [ ] GetOwnerDemolitionsSkill
- [ ] SWMG_GetObjectName
- [ ] EffectCutSceneHorrified
- [ ] SWMG_DestroyMiniGameObject
- [ ] AddBonusForcePoints
- [ ] GetIsTrapped
- [ ] SWMG_GetSphereRadius
- [ ] SWMG_PlayerApplyForce
- [ ] SpawnAvailablePUP
- [ ] GetAlignmentGoodEvil
- [ ] ShowChemicalUpgradeScreen
- [ ] PlayOverlayAnimation
- [ ] DetonateMine
- [ ] GetFacingFromLocation
- [ ] StopRumblePattern
- [ ] EffectDamageDecrease
- [ ] GetLastForfeitViolation
- [ ] DisableMap
- [ ] SetInputClass
- [ ] DisplayMessageBox
- [ ] DisplayDatapad
- [ ] RemoveEffectByExactMatch
- [ ] GetSkillRankBase
- [ ] FaceObjectAwayFromObject
- [ ] SWMG_GetPlayerMinSpeed
- [ ] SWMG_SetPlayerInvincibility
- [ ] EffectCutSceneStunned
- [ ] EffectVPRegenModifier
- [ ] SWMG_GetTrackPosition
- [ ] SWMG_SetFollowerPosition
- [ ] DecrementGlobalNumber
- [ ] SWMG_SetJumpSpeed
- [ ] IsRunning
- [ ] ModifyWillSavingThrowBase
- [ ] EffectFactionModifier
- [ ] ChangeObjectAppearance
- [ ] AdjustCreatureSkills
- [ ] GetReputation
- [ ] GetGameDifficulty
- [ ] SWMG_GetLastObstacleHit
- [ ] GetSpellForcePointCost
- [ ] EffectBlind
- [ ] ShowSwoopUpgradeScreen
- [ ] GrantFeat
- [ ] IsMeditating
- [ ] ModifyReflexSavingThrowBase
- [ ] AddAvailablePUPByObject
- [ ] AssignPUP
- [ ] EffectMindTrick
- [ ] DisableHealthRegen
- [ ] SetDisableTransit
- [ ] AngleToVector
- [ ] GetLastClosedBy
- [ ] GetLastWeaponUsed
- [ ] GetItemHasItemProperty
- [ ] SoundObjectSetPosition
- [ ] SetTrapDetectedBy
- [ ] EffectForceBody
- [ ] EffectFury
- [ ] EffectCrush
- [ ] YavinHackDoorClose
- [ ] EffectForceSight
- [ ] ModifyFortitudeSavingThrowBase
- [ ] EffectDroidScramble
- [ ] UnlockAllSongs
- [ ] SetCurrentForm
- [ ] GetIsPlayerMadeCharacter
- [ ] RebuildPartyTable
- [ ] PrintFloat
- [ ] PrintInteger
- [ ] PrintObject
- [ ] SetTime
- [ ] ActionPickUpItem
- [ ] ActionPutDownItem
- [ ] ActionSpeakString
- [ ] SetCameraFacing
- [ ] GetLastItemEquipped
- [ ] GetStringUpperCase
- [ ] GetStringLowerCase
- [ ] InsertString
- [ ] fabs
- [ ] cos
- [ ] sin
- [ ] tan
- [ ] acos
- [ ] asin
- [ ] atan
- [ ] log
- [ ] pow
- [ ] sqrt
- [ ] GetEffectDurationType
- [ ] GetEffectSubType
- [ ] VectorMagnitude
- [ ] MagicalEffect
- [ ] SupernaturalEffect
- [ ] ExtraordinaryEffect
- [ ] GetAC
- [ ] EffectDamageReduction
- [ ] TurnsToSeconds
- [ ] EffectKnockdown
- [ ] PrintVector
- [ ] VectorToAngle
- [ ] TouchAttackMelee
- [ ] TouchAttackRanged
- [ ] EffectSpellImmunity
- [ ] EffectForceJump
- [ ] EffectConfused
- [ ] EffectFrightened
- [ ] ActionForceFollowObject
- [ ] EffectAreaOfEffect
- [ ] ChangeFaction
- [ ] GetIsListening
- [ ] TestStringAgainstPattern
- [ ] GetMatchedSubstring
- [ ] GetMatchedSubstringsCount
- [ ] GetFactionWeakestMember
- [ ] GetFactionStrongestMember
- [ ] GetFactionMostDamagedMember
- [ ] GetFactionLeastDamagedMember
- [ ] GetFactionGold
- [ ] GetFactionAverageGoodEvilAlignment
- [ ] SoundObjectGetFixedVariance
- [ ] GetFactionAverageLevel
- [ ] GetFactionAverageXP
- [ ] GetFactionMostFrequentClass
- [ ] GetFactionWorstAC
- [ ] GetFactionBestAC
- [ ] GetTransitionTarget
- [ ] SetAreaTransitionBMP
- [ ] GetGoingToBeAttackedBy
- [ ] FeetToMeters
- [ ] YardsToMeters
- [ ] GetNearestCreatureToLocation
- [ ] GetNearestObjectToLocation
- [ ] StringToFloat
- [ ] ActionCastSpellAtLocation
- [ ] ActionSpeakStringByStrRef
- [ ] RandomName
- [ ] EffectAssuredDeflection
- [ ] GetLastPerceptionHeard
- [ ] GetLastPerceptionInaudible
- [ ] GetAreaOfEffectCreator
- [ ] GetButtonMashCheck
- [ ] EffectHaste
- [ ] GetEncounterSpawnsMax
- [ ] SetEncounterSpawnsMax
- [ ] GetEncounterSpawnsCurrent
- [ ] SetEncounterSpawnsCurrent
- [ ] GetModuleItemAcquiredFrom
- [ ] ActionUseFeat
- [ ] GetObjectHeard
- [ ] GetModuleItemLost
- [ ] GetModuleItemLostBy
- [ ] EventConversation
- [ ] SetEncounterDifficulty
- [ ] GetEncounterDifficulty
- [ ] GetDistanceBetweenLocations
- [ ] TalentSkill
- [ ] ActionUseTalentAtLocation
- [ ] GetGoldPieceValue
- [ ] GetIsPlayableRacialType
- [ ] GetLastAttackType
- [ ] GetLastAttackMode
- [ ] GetLastAssociateCommand
- [ ] GetClickingObject
- [ ] SetAssociateListenPatterns
- [ ] GetIdentified
- [ ] SetIdentified
- [ ] GetDistanceBetweenLocations2D
- [ ] GetLastDisarmed
- [ ] GetLastDisturbed
- [ ] GetLastLocked
- [ ] GetLastUnlocked
- [ ] VersusAlignmentEffect
- [ ] VersusRacialTypeEffect
- [ ] VersusTrapEffect
- [ ] ActionMoveAwayFromLocation
- [ ] SendMessageToPC
- [ ] GetFirstFactionMember
- [ ] GetNextFactionMember
- [ ] GetJournalQuestExperience
- [ ] EffectHitPointChangeWhenDying
- [ ] PopUpGUIPanel
- [ ] IntToHexString
- [ ] GetItemACValue
- [ ] ExploreAreaForPlayer
- [ ] ActionEquipMostEffectiveArmor
- [ ] GetIsDay
- [ ] GetIsNight
- [ ] GetIsDawn
- [ ] GetIsDusk
- [ ] GetLastPlayerDying
- [ ] GetStartingLocation
- [ ] SpeakOneLinerConversation
- [ ] GetLastRespawnButtonPresser
- [ ] GetIsWeaponEffective
- [ ] EventActivateItem
- [ ] MusicBackgroundSetDelay
- [ ] MusicBattleChange
- [ ] AmbientSoundChangeDay
- [ ] AmbientSoundChangeNight
- [ ] GetSpellCastItem
- [ ] GetItemActivatedTargetLocation
- [ ] GetItemActivatedTarget
- [ ] EffectDamageImmunityDecrease
- [ ] EffectSkillDecrease
- [ ] EffectForceResistanceDecrease
- [ ] EffectConcealment
- [ ] EffectDispelMagicAll
- [ ] GetMaxStealthXP
- [ ] EffectSeeInvisible
- [ ] EffectTimeStop
- [ ] EffectBlasterDeflectionDecrease
- [ ] EffectSpellLevelAbsorption
- [ ] EffectDispelMagicBest
- [ ] EffectMissChance
- [ ] GetStealthXPEnabled
- [ ] GetLastTrapDetected
- [ ] EffectDamageShield
- [ ] GetNearestTrapToObject
- [ ] GetFortitudeSavingThrow
- [ ] GetWillSavingThrow
- [ ] GetReflexSavingThrow
- [ ] GetChallengeRating
- [ ] GetMovementRate
- [ ] GetStealthXPDecrement
- [ ] SetStealthXPDecrement
- [ ] SetCameraMode
- [ ] CutsceneMove
- [ ] GetWeaponRanged
- [ ] SetTutorialWindowsEnabled
- [ ] SWMG_GetLateralAccelerationPerSecond
- [ ] GetDifficultyModifier
- [ ] FloatingTextStrRefOnCreature
- [ ] FloatingTextStringOnCreature
- [ ] GetTrapDisarmable
- [ ] GetTrapDetectable
- [ ] GetTrapDetectedBy
- [ ] GetTrapFlagged
- [ ] GetTrapOneShot
- [ ] GetTrapCreator
- [ ] GetTrapKeyTag
- [ ] GetTrapDisarmDC
- [ ] GetTrapDetectDC
- [ ] GetLockKeyRequired
- [ ] GetLockKeyTag
- [ ] GetLockLockable
- [ ] GetLockUnlockDC
- [ ] GetLockLockDC
- [ ] GetPCLevellingUp
- [ ] GetHasFeatEffect
- [ ] SetPlaceableIllumination
- [ ] GetPlaceableIllumination
- [ ] GetIsPlaceableObjectActionPossible
- [ ] DoPlaceableObjectAction
- [ ] PopUpDeathGUIPanel
- [ ] SetTrapDisabled
- [ ] ExportAllCharacters
- [ ] MusicBackgroundGetDayTrack
- [ ] MusicBackgroundGetNightTrack
- [ ] WriteTimestampedLogEntry
- [ ] GetFactionLeader
- [ ] AmbientSoundSetDayVolume
- [ ] AmbientSoundSetNightVolume
- [ ] GetStrRefSoundDuration
- [ ] SWMG_GetLastEvent
- [ ] SWMG_GetLastEventModelName
- [ ] SWMG_GetObjectByName
- [ ] SWMG_GetLastBulletHitDamage
- [ ] SWMG_GetLastBulletHitTarget
- [ ] SWMG_GetLastBulletHitShooter
- [ ] SWMG_OnBulletHit
- [ ] SWMG_OnObstacleHit
- [ ] SWMG_GetLastBulletFiredDamage
- [ ] SWMG_GetLastBulletFiredTarget
- [ ] SWMG_IsFollower
- [ ] SWMG_IsPlayer
- [ ] SWMG_IsEnemy
- [ ] SWMG_IsTrigger
- [ ] SWMG_IsObstacle
- [ ] SWMG_GetLastHPChange
- [ ] SWMG_GetCameraNearClip
- [ ] SWMG_GetCameraFarClip
- [ ] SWMG_SetCameraClip
- [ ] SWMG_GetObstacleCount
- [ ] SWMG_GetObstacle
- [ ] SWMG_SetMaxHitPoints
- [ ] SWMG_SetSphereRadius
- [ ] SWMG_GetNumLoops
- [ ] SWMG_SetNumLoops
- [ ] SWMG_GetGunBankCount
- [ ] SWMG_GetGunBankBulletModel
- [ ] SWMG_GetGunBankGunModel
- [ ] SWMG_GetGunBankDamage
- [ ] SWMG_GetGunBankTimeBetweenShots
- [ ] SWMG_GetGunBankLifespan
- [ ] SWMG_GetGunBankSpeed
- [ ] SWMG_GetGunBankTarget
- [ ] SWMG_SetGunBankBulletModel
- [ ] SWMG_SetGunBankGunModel
- [ ] SWMG_SetGunBankDamage
- [ ] SWMG_SetGunBankTimeBetweenShots
- [ ] SWMG_SetGunBankLifespan
- [ ] SWMG_SetGunBankSpeed
- [ ] SWMG_SetGunBankTarget
- [ ] SWMG_GetLastBulletHitPart
- [ ] SWMG_IsGunBankTargetting
- [ ] SWMG_GetPlayerInvincibility
- [ ] SWMG_GetPlayerTunnelPos
- [ ] SWMG_SetPlayerOffset
- [ ] SWMG_GetPlayerTunnelNeg
- [ ] SWMG_GetPlayerOrigin
- [ ] SWMG_SetPlayerOrigin
- [ ] SWMG_GetGunBankHorizontalSpread
- [ ] SWMG_GetGunBankVerticalSpread
- [ ] SWMG_GetGunBankSensingRadius
- [ ] SWMG_GetGunBankInaccuracy
- [ ] SWMG_SetGunBankHorizontalSpread
- [ ] SWMG_SetGunBankVerticalSpread
- [ ] SWMG_SetGunBankSensingRadius
- [ ] SWMG_SetGunBankInaccuracy
- [ ] SWMG_GetPlayerMaxSpeed
- [ ] AddJournalWorldEntry
- [ ] AddJournalWorldEntryStrref
- [ ] DeleteJournalWorldAllEntries
- [ ] DeleteJournalWorldEntry
- [ ] DeleteJournalWorldEntryStrref
- [ ] EffectForceDrain
- [ ] SetJournalQuestEntryPicture
- [ ] SWMG_GetSoundFrequency
- [ ] SWMG_SetSoundFrequency
- [ ] SWMG_GetSoundFrequencyIsRandom
- [ ] SWMG_SetSoundFrequencyIsRandom
- [ ] SWMG_GetSoundVolume
- [ ] SWMG_SetSoundVolume
- [ ] SoundObjectSetPitchVariance
- [ ] SoundObjectGetVolume
- [ ] SetPartyAIStyle
- [ ] GetLastConversation
- [ ] SWMG_GetPlayerTunnelInfinite
- [ ] SWMG_SetPlayerTunnelInfinite
- [ ] GetFirstAttacker
- [ ] GetNextAttacker
- [ ] SetFormation
- [ ] SetForcePowerUnsuccessful
- [ ] GetPlanetSelectable
- [ ] GetPlanetAvailable
- [ ] SetAreaFogColor
- [ ] SetGoodEvilValue
- [ ] SuppressStatusSummaryEntry
- [ ] GetItemComponent
- [ ] GetItemComponentPieceValue
- [ ] GetChemicals
- [ ] GetChemicalPieceValue
- [ ] EffectFPRegenModifier
- [ ] GetFeatAcquired
- [ ] GetRacialSubType
- [ ] SetBonusForcePoints
- [ ] GetBonusForcePoints
- [ ] IsMoviePlaying
- [ ] EffectDroidConfused
- [ ] IsInTotalDefense
- [ ] GetSpellFormMask
- [ ] ShowDemoScreen
- [ ] AddAvailablePUPByTemplate
- [ ] AddPartyPuppet
- [ ] EnableRain
- [ ] SaveNPCByObject
- [ ] SavePUPByObject