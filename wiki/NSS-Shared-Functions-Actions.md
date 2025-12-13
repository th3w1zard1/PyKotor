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

### Common Issues and Troubleshooting

#### 1. NPC Stays Frozen / Animation Doesn't Play

If `ActionPlayAnimation` doesn't work even with `ClearAllActions()`, check the following:

**A. Overlay Animation Active**

- If an overlay animation is currently playing, `ActionPlayAnimation` will fail immediately
- **Solution**: Wait for overlay animations to complete, or clear them first

**B. NPC in Conversation/Dialog State**

- Animations are blocked during active conversations (dialog mode)
- **Check**: `GetIsInConversation(oNPC)` returns TRUE
- **Solution**: Wait for conversation to end, or use conversation-specific animation functions

**C. Animation Missing from Model**

- The animation constant may be valid, but the actual animation may not exist in the NPC's model file
- **Check**: Verify the animation exists in the model's MDL/MDX file
- **Solution**: Use a different animation that exists in the model, or check the model file

**D. NPC is Dead or Invalid**

- Dead NPCs or invalid objects cannot play animations
- **Check**: `GetIsDead(oNPC)` or `GetIsObjectValid(oNPC)`

**E. Use `PlayAnimation()` Instead**

- `PlayAnimation()` executes immediately rather than queuing, which can bypass some blocking conditions
- **Example**: `AssignCommand(oNPC, PlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, -1.0))`

**F. Try a Longer Delay**

- Sometimes a small delay after `ClearAllActions()` helps ensure the NPC is fully stationary

```nss
ClearAllActions();
DelayCommand(0.3, ActionPlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, -1.0));
```

**G. Check AI State**

- NPCs with AI turned off or in special states may not respond to animations
- **Solution**: Temporarily disable AI if needed, or check spawn-in conditions

#### 2. Animation Doesn't Loop

For looping animations, use `-1.0` as the duration parameter, not a positive value. Positive values create timed animations that stop after the duration.

#### 3. Invalid Animation Error

Ensure the animation constant includes the 10000 offset. If using raw indices from `Animations.2da`, add 10000: `ActionPlayAnimation(10000 + iAnim, 1.0, -1.0)`

#### 4. Animation Plays But NPC Still Looks Frozen

- The animation may be playing but visually similar to the default pose
- Try a more distinct animation like `ANIMATION_LOOPING_TALK_NORMAL` to verify it's working
- Check if the animation speed is too slow (try `fSpeed = 2.0` to see if it's just slow)

### Implementation References

- **KotOR.js**: [`vendor/KotOR.js/src/actions/ActionPlayAnimation.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/actions/ActionPlayAnimation.ts) - Action queue implementation
- **reone**: [`vendor/reone/src/libs/game/action/playanimation.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/action/playanimation.cpp) - Animation execution logic
- **reone Creature**: [`vendor/reone/src/libs/game/object/creature.cpp:256-290`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L256-L290) - Movement blocking check

### Troubleshooting Script Example

If `ActionPlayAnimation` isn't working, try this diagnostic approach:

```nss
void main() {
    object oNPC = OBJECT_SELF; // or GetObjectByTag("your_npc_tag")
    
    // Diagnostic checks
    if (!GetIsObjectValid(oNPC)) {
        PrintString("ERROR: Invalid NPC");
        return;
    }
    
    if (GetIsDead(oNPC)) {
        PrintString("ERROR: NPC is dead");
        return;
    }
    
    if (GetIsInConversation(oNPC)) {
        PrintString("WARNING: NPC in conversation - animations may be blocked");
    }
    
    // Clear everything first
    AssignCommand(oNPC, ClearAllActions());
    CancelCombat(oNPC);
    
    // Try PlayAnimation instead (immediate, not queued)
    DelayCommand(0.5, AssignCommand(oNPC, PlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, -1.0)));
    
    // Alternative: Try ActionPlayAnimation with longer delay
    // DelayCommand(0.5, AssignCommand(oNPC, ActionPlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, -1.0)));
}
```

### Alternative: Use PlayAnimation() Instead

If `ActionPlayAnimation` consistently fails, try `PlayAnimation()` which executes immediately:

```nss
void main() {
    object oNPC = OBJECT_SELF;
    ClearAllActions();
    AssignCommand(oNPC, PlayAnimation(ANIMATION_LOOPING_PAUSE, 1.0, -1.0));
}
```

**Key Difference:**

- `ActionPlayAnimation()` - Queued action (respects action queue order)
- `PlayAnimation()` - Immediate execution (may bypass some blocking conditions)

### Related Functions

- `PlayAnimation()` - Immediate animation execution (non-queued) - **Try this if ActionPlayAnimation fails**
- `ClearAllActions()` - Clear action queue and stop movement
- `CancelCombat()` - Cancel combat state which may block animations
- `AssignCommand()` - Queue actions on other objects
- `DelayCommand()` - Delay action execution
- `GetIsInConversation()` - Check if object is in conversation (may block animations)
