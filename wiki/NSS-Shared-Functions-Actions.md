# Actions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)

## ActionPlayAnimation

### Function Signature

```nss
void ActionPlayAnimation(int nAnimation, float fSpeed, float fDurationSeconds);
```

**Routine:** 40

### Description

Causes the action subject (the object executing this action) to play an animation. This action is queued and executed as part of the object's action queue.

### Parameters

- `nAnimation`: The animation constant to play (must be >= 10000). Common constants include:
  - `ANIMATION_LOOPING_PAUSE` - Idle pause animation
  - `ANIMATION_LOOPING_TALK_NORMAL` - Normal talking animation
  - `ANIMATION_LOOPING_TALK_FORCEFUL` - Forceful talking animation
  - `ANIMATION_LOOPING_TALK_LAUGHING` - Laughing animation
  - `ANIMATION_LOOPING_TALK_PLEADING` - Pleading animation
  - `ANIMATION_LOOPING_TALK_SAD` - Sad talking animation
  - See `Animations.2da` for all available animation indices
- `fSpeed`: Speed multiplier for the animation (1.0 = normal speed, 2.0 = double speed, etc.)
- `fDurationSeconds`: Duration control:
  - `-1.0` = Looping animation (plays indefinitely until next animation is applied)
  - `0.0` = Fire-and-forget (plays once, completes when animation finishes)
  - `> 0.0` = Timed animation (plays for specified duration in seconds)

### Critical Requirements

**⚠️ IMPORTANT: Movement Blocking**

Animations **will not play** if the object is moving or has queued movement actions. You **must** call `ClearAllActions()` before queuing an animation to ensure the object is stationary.

**Implementation Reference:** [`vendor/reone/src/libs/game/object/creature.cpp:281-283`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L281-L283) - Animations are blocked if `_movementType != MovementType::None`

### Animation ID Requirements

Animation constants must include the 10000 offset. The animation ID passed must be >= 10000 for the action to succeed. Animation constants (like `ANIMATION_LOOPING_PAUSE`) already include this offset, but if using raw animation indices from `Animations.2da`, add 10000 to the index.

**Implementation Reference:** [`vendor/KotOR.js/src/actions/ActionPlayAnimation.ts:56-62`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/actions/ActionPlayAnimation.ts#L56-L62) - Animation validation requires >= 10000

### Usage Examples

#### Basic Looping Animation

```nss
void main() {
    ClearAllActions();
    ActionPlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, -1.0);
}
```

#### Brief Animation with Delay

```nss
void main() {
    object oNPC = GetObjectByTag("my_npc");
    AssignCommand(oNPC, ClearAllActions());
    DelayCommand(0.2, AssignCommand(oNPC, ActionPlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, 0.1)));
}
```

#### Fire-and-Forget Animation (Plays Once)

```nss
void main() {
    ClearAllActions();
    ActionPlayAnimation(ANIMATION_LOOPING_TALK_NORMAL, 1.0, 0.0);
}
```

#### Pattern from Vanilla Scripts

```nss
// From vendor/Vanilla_KOTOR_Script_Source/TSL/Vanilla/Modules/650DAN_Dantooine_Rebuilt_Enclave/a_vroo_actions.nss
void main() {
    ClearAllActions();
    SetLocalBoolean(OBJECT_SELF, 42, 1);
    DelayCommand(0.8, AssignCommand(GetObjectByTag("vrookcage", 0), 
        ActionPlayAnimation(202, 1.0, 0.0)));
}
```

#### Community Patch Pattern

```nss
// From vendor/K1_Community_Patch/Source/cp_inc_k1.nss:781
void CP_ReturnToBase(location lLoc, int bRun = FALSE) {
    ClearAllActions();
    ActionMoveToLocation(lLoc, bRun);
    ActionDoCommand(SetFacing(GetFacingFromLocation(lLoc)));
    ActionPlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, 0.1);
    ActionDoCommand(SetCommandable(TRUE));
    SetCommandable(FALSE);
}
```

### Common Issues

1. **NPC Stays Frozen**: If the animation doesn't play, the most common cause is that the NPC is still moving or has queued actions. Always call `ClearAllActions()` first.

2. **Animation Doesn't Loop**: For looping animations, use `-1.0` as the duration parameter, not a positive value. Positive values create timed animations that stop after the duration.

3. **Invalid Animation Error**: Ensure the animation constant includes the 10000 offset. If using raw indices from `Animations.2da`, add 10000: `ActionPlayAnimation(10000 + iAnim, 1.0, -1.0)`

4. **Animation Missing from Model**: Even if an animation exists in `Animations.2da`, it may not exist in the specific model file. Verify the animation exists in the model's MDL/MDX files.

### Implementation References

- **KotOR.js**: [`vendor/KotOR.js/src/actions/ActionPlayAnimation.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/actions/ActionPlayAnimation.ts) - Action queue implementation
- **reone**: [`vendor/reone/src/libs/game/action/playanimation.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/action/playanimation.cpp) - Animation execution logic
- **reone Creature**: [`vendor/reone/src/libs/game/object/creature.cpp:256-290`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L256-L290) - Movement blocking check

### Related Functions

- `PlayAnimation()` - Immediate animation execution (non-queued)
- `ClearAllActions()` - Clear action queue and stop movement
- `AssignCommand()` - Queue actions on other objects
- `DelayCommand()` - Delay action execution
