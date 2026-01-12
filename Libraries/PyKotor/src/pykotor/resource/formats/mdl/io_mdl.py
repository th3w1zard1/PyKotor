"""Binary MDL/MDX file I/O operations.

This module handles reading and writing binary MDL/MDX format files used in KotOR.
The MDL file contains node hierarchy, animations, and metadata, while the MDX file
contains vertex data, faces, and geometry payload.

I/O and Parsing Functions (Engine Implementation):
-------------------------------------------------
These functions correspond to the game engine's MDL/MDX parsing implementation:

    - LoadModel - K1: 0x00464200, TSL: 0x0047a570
      * Main model loader entry point (172 bytes, 6 callees, 2 callers)
        * Signature: Model * __cdecl LoadModel(int param_1, undefined4 param_2)
        * Logic (from decompilation):
          * Saves CurrentModel to stack
          * Returns NULL if param_1 is 0
          * Sets CurrentModel to NULL
          * Gets IODispatcher singleton via IODispatcher::GetRef() @ (K1: 0x004a0580, TSL: 0x004cda00)
          * Calls IODispatcher::ReadSync() @ (K1: 0x004a15d0, TSL: 0x004cead0) with param_1 and param_2
          * ReadSync creates Input object and calls Input::Read() @ (K1: 0x004a1260, TSL: 0x004ce780)
          * Input::Read() calls InputBinary::Read() which parses MDL/MDX binary format
          * Result is MaxTree* which is converted to Model* via MaxTree::AsModel() @ (K1: 0x0043e1c0, TSL: 0x0044ff90)
          * MaxTree::AsModel() checks if type == 2 (MODEL_TYPE) and returns cast or NULL
          * If model loaded successfully, iterates through modelsList.data array
          * Compares model names using __stricmp() on (modelsList.data[i]->tree).name vs (this_01->tree).name
          * If duplicate found, calls Model::~Model() and MaxTree::operator.delete() on new model
          * Returns cached model from modelsList.data[iVar3]
          * If no duplicate, returns the newly loaded model
          * Restores CurrentModel from stack
          * Returns NULL if model loading failed
        * Callees (call chain depth 3+):
          * ~Model() @ (K1: 0x0043f790, TSL: 0x004527d0) (destructor, called if duplicate found)
          * IODispatcher::GetRef() @ (K1: 0x004a0580, TSL: 0x004cda00) (singleton accessor)
          * MaxTree::AsModel() @ (K1: 0x0043e1c0, TSL: 0x0044ff90) (type check and cast)
          * __stricmp() @ (K1: 0x0070acaf, TSL: 0x0077e24f) (case-insensitive string comparison)
          * operator.delete() @ (K1: 0x0044aec0, TSL: 0x0045f520) (memory deallocation)
          * IODispatcher::ReadSync() @ (K1: 0x004a15d0, TSL: 0x004cead0) (file I/O dispatcher)
            * Input::Read() @ (K1: 0x004a1260, TSL: 0x004ce780) (parses MDL/MDX format)
              * InputBinary::Read() (binary parser)
              * AurResGetNextLine() @ (K1: 0x0044bfa0, TSL: N/A - ASCII MDL format not supported in TSL) (line reading for ASCII MDL)
              * AurResGet() @ (K1: 0x0044c740, TSL: 0x00460db0) (resource data access)
              * FuncInterp() @ (K1: 0x0044c1f0, TSL: N/A - ASCII MDL format not supported in TSL) (function interpolation for animations)
        * Callers (call chain showing usage):
          * NewCAurObject() @ (K1: 0x00449cc0, TSL: 0x0045e2e0) -> LoadModel() @ (K1: 0x00449d9d, TSL: 0x0047a570)
            * Called from: HideWieldedItems(), LoadSpellVisual(), LoadConjureVisual(), AddObstacle(),
              SetWeather(), LoadVisualEffect(), SetGunModel(), SpawnRooms(), CollapsePartTree(),
              FireGunCallback(), LoadAnimatedCamera(), SetPlayer(), LoadModel(), LoadModelAttachment(),
              AddEnemy(), LoadLight(), AddGun(), CreateReferenceObjects(), ChunkyParticle(),
              CreateMuzzleFlash(), SpawnPartsForTile(), SetProjectileVelAndAccel(), SpawnHitVisuals(),
              LoadArea(), SpawnVisualEffect(), AddPlaceableObjectLight(), LoadBeam(), ApplyShadowBlob(),
              SetPlayer(), AddModel(), SpawnRoom()
          * LoadAddInAnimations() @ (K1: 0x00440890, TSL: 0x004538d0) -> LoadModel() @ (K1: 0x004408f7, TSL: 0x0047a570)
            * Member of Gob class, loads additional animations for models
            * Searches for model using FindModel(param_1)
            * If not found, appends ".mdl" extension and opens file
            * Calls LoadModel() with FILE* handle
            * Synchronizes animation trees with MaxTree::SynchronizeTree()
        * Global State: Uses CurrentModel global variable (thread-local context)
        * Data Structures: Accesses modelsList (global array/vector of Model*)
      * TSL: Function not found at same address pattern. Likely refactored or renamed.
        * Search methodology: Searched for IODispatcher::ReadSync pattern, MaxTree::AsModel pattern,
          and __stricmp usage with modelsList - no direct match found.
        * Hypothesis: Model loading may be integrated into higher-level creature/placeable loaders.

    - IODispatcher::ReadSync - K1: 0x004a15d0, TSL: 0x004cead0
      * Synchronous I/O dispatcher for model files (36 bytes)
        * Signature: void __thiscall IODispatcher::ReadSync(IODispatcher *this, FILE *param_1, FILE *param_2)
        * Logic (from decompilation):
          * Creates Input object on stack (12 bytes)
          * Calls Input::Read(local_10, param_1, param_2)
          * Input::Read() handles actual MDL/MDX parsing
          * Returns
        * Callees:
          * Input::Read() @ (K1: 0x004a1260, TSL: 0x004ce780) (main parsing function)
            * InputBinary::Read() (binary format parser)
            * AurResGetNextLine() @ (K1: 0x0044bfa0, TSL: N/A - ASCII MDL format not supported in TSL) (line reading for ASCII MDL)
            * AurResGet() @ (K1: 0x0044c740, TSL: 0x00460db0) (resource data access)
            * FuncInterp() @ (K1: 0x0044c1f0, TSL: N/A - ASCII MDL format not supported in TSL) (function interpolation for animations)
        * Callers:
          * LoadModel() @ (K1: 0x00464200, TSL: 0x0047a570) (main entry point)

    - MaxTree::AsModel - K1: 0x0043e1c0, TSL: 0x0044ff90
      * Type check and cast function (16 bytes, 88 callers)
        * Signature: Model * __thiscall MaxTree::AsModel(MaxTree *this)
        * Logic (from decompilation):
          * Checks if (this->type & 0x7f) == 2 (MODEL_TYPE constant)
          * Uses bitwise trick: ~-(uint)(condition) creates 0xFFFFFFFF if true, 0 if false
          * ANDs result with (uint)this to return this cast to Model* or NULL
          * Equivalent to: return ((this->type & 0x7f) == 2) ? (Model*)this : NULL;
        * Callers (88 total, examples):
          * ProcessSkinSeams() @ (K1: 0x004392b6, TSL: 0x0044a920), (K1: 0x00439986, TSL: 0x0044a920) (skin seam processing - both addresses are call sites within ProcessSkinSeams)
          * FindModel() @ (K1: 0x00464176, TSL: 0x0047a480) (model lookup)
          * LoadModel() @ (K1: 0x00464236, TSL: 0x0047a570) (main loader)
          * BuildVertexArrays() @ (K1: 0x00478b50, TSL: 0x00495620) (vertex array construction - both addresses are call sites within BuildVertexArrays)
          * Input::Read() @ (K1: 0x004a1435, TSL: 0x004ce8c0), (K1: 0x004a1362, TSL: 0x004ce8c0), (K1: 0x004a1373, TSL: 0x004ce8c0), (K1: 0x004a1503, TSL: 0x004ce8c0) (parsing - call sites within Input::Read)

    Function Discovery Methodology:
    ------------------------------
    Functions are located through:
    1. String cross-references: Search for relevant strings (e.g., ".mdl", "ModelName", error messages)
       and trace back to functions that reference them
    2. Call chain analysis: Follow callers/callees from known entry points
    3. VTable offsets: For virtual functions, locate via vtable entries in class structures
    4. Import references: Search for imported library functions that are called by model functions
    5. Decompilation patterns: Match decompiled logic patterns across executables

    Engine-Level Model Loading Functions:
    -------------------------------------
    These functions are part of the game engine's object system and handle loading models
    into creature, placeable, and other game objects. These are higher-level functions
    that use the binary MDL/MDX I/O functions above.

    - CSWCCreature::LoadModel - K1: 0x0061b380, TSL: 0x00669ea0 (CSWCCreature::LoadModel_Internal)
      * Creature-specific model loader (842 bytes, 10 callees)
        * Signature: undefined4 __thiscall CSWCCreature::LoadModel(CSWCCreature *this, undefined4 *param_1, undefined4 param_2, char param_3)
        * Logic (from decompilation):
          * Checks if this->field158_0x358 (cached anim_base) is non-NULL
          * If cached exists, destructs current anim_base via vtable call, then assigns cached
          * Sets this->field159_0x35c from this->field158_0x358
          * If current anim_base exists and field44_0xc4 == param_3, skips to model loading
          * Otherwise destructs current anim_base and creates new based on param_3 switch:
            * case 0: Allocates 0xf0 bytes, constructs CSWCAnimBase @ (K1: 0x0069dfb0, TSL: 0x006f8340)
            * case 1: Allocates 0x1c4 bytes, constructs CSWCAnimBaseHead @ (K1: 0x0069bb80, TSL: 0x006f5e60) with param=1
            * case 2: Allocates 0x1d0 bytes, constructs CSWCAnimBaseWield @ (K1: 0x00699dd0, TSL: 0x006f41b0) with param=1
            * case 3: Allocates 0x220 bytes, constructs CSWCAnimBaseHeadWield @ (K1: 0x00698ec0, TSL: 0x006f32a0)
          * Each anim base type has different vtable and member layouts
          * After construction, calls RegisterCallbacks() @ (K1: 0x0061ab40, TSL: 0x00693fe0)
          * Then calls anim_base->vtable[3](param_1, param_2) - loads model resource
          * If loading fails, uses sprintf() with error string and returns 0
          * Error string: "CSWCCreature::LoadModel(): Failed to load creature model '%s'." @ (K1: 0x0074f85c, TSL: 0x007c82fc)
          * Cross-reference: Error string referenced at @ (K1: 0x0061b5cf, TSL: 0x0066a0f0) in LoadModel function
          * On success, calls anim_base->vtable[2](param_3) for additional setup if param_3 is special value
          * Returns 1 on success, 0 on failure
        * Callees:
          * operator_new() @ (K1: 0x006fa7e6, TSL: 0x0076d9f6) (memory allocation, called 5 times)
          * CSWCAnimBaseWield::CSWCAnimBaseWield() @ (K1: 0x00699dd0, TSL: 0x006f41b0) (two-weapon anim base constructor)
          * CSWCAnimBaseHeadWield::CSWCAnimBaseHeadWield() @ (K1: 0x00698ec0, TSL: 0x006f32a0) (head + wield anim base)
          * CSWCAnimBase::CSWCAnimBase() @ (K1: 0x0069dfb0, TSL: 0x006f8340) (base anim base constructor)
          * CSWCAnimBaseTW::CSWCAnimBaseTW() @ (K1: 0x0069cbd0, TSL: 0x006f6fb0) (two-weapon variant)
          * sprintf() @ (K1: 0x006fadb0, TSL: 0x0076dac2) (error message formatting)
          * CResRef::CopyToString() @ (K1: 0x00405f70, TSL: 0x00406050) (resource reference string conversion)
          * CResRef::GetResRefStr() @ (K1: 0x00405fe0, TSL: N/A) (K1 equivalent - uses circular buffer like TSL's CopyToString)
          * RegisterCallbacks() @ (K1: 0x0061ab40, TSL: 0x00693fe0) (callback registration)
          * CSWCAnimBaseHead::CSWCAnimBaseHead() @ (K1: 0x0069bb80, TSL: 0x006f5e60) (head anim base constructor)
          * CSWAnimBase::Set() @ (K1: 0x00698e30, TSL: 0x006f3210) (anim base setup, called 4 times)
        * Callers: None found via direct references (vtable call via object method)
        * VTable Entry: Located at offset in CSWCCreature class structure
        * String References:
          * Error string @ (K1: 0x0074f85c, TSL: 0x007c82fc): "CSWCCreature::LoadModel(): Failed to load creature model '%s'."
            * Referenced in LoadModel error handler (inline code) @ (K1: 0x0061b5cf within CSWCCreature::LoadModel @ 0x0061b380, TSL: 0x0066a0f0) via sprintf() call
            * Used when anim_base->vtable[3] returns 0 (model loading failure)
      * Creature model loader (1379 bytes, 11 callees)
        * Signature: undefined4 __thiscall CSWCCreature::LoadModel_Internal(int param_1, undefined4 *param_2, undefined4 param_3, char param_4)
        * Address: (K1: 0x0061b380, TSL: 0x00669ea0) (verified via vtable entry at CSWCCreature_LoadModel_vtable_entry @ (K1: 0x0074f670, TSL: 0x007c8040) pointing to this function)
        * Discovery Method: Located via vtable data reference at CSWCCreature_LoadModel_vtable_entry @ (K1: 0x0074f670, TSL: 0x007c8040), which stores function pointer to (K1: 0x0061b380, TSL: 0x00669ea0)
        * NOTE: In K1, CSWCCreature::LoadModel at 0x0061b380 contains all logic inline (842 bytes). In TSL, the logic was split into CSWCCreature::LoadModel (wrapper at 0x0066a0f0) and CSWCCreature::LoadModel_Internal (implementation at 0x00669ea0, 1379 bytes).
        * Logic (from exhaustive decompilation - EXHAUSTIVE DIFFERENCES from K1):
          * EXECUTION FLOW:
          * 1. Exception handling setup: Saves ExceptionList, initializes SEH frame with __CxxFrameHandler3 @ (K1: 0x00728076, TSL: 0x0079cc86)
          * 2. Cached anim_base check: Checks *(int*)(param_1 + 0x370) for cached anim_base (was this->field158_0x358 in K1)
          *    - If cached exists (non-NULL), destructs current anim_base via vtable[0](1) call at offset 0x68
          *    - Assigns cached to *(undefined4**)(param_1 + 0x68)
          *    - Clears cache: *(undefined4*)(param_1 + 0x370) = 0
          *    - Copies field159: *(undefined4*)(param_1 + 0x200) = *(undefined4*)(param_1 + 0x374)
          *    - Clears field159 cache: *(undefined4*)(param_1 + 0x374) = 0
          * 3. Current anim_base validation: Checks *(undefined4**)(param_1 + 0x68) (was this->object.anim_base in K1)
          *    - If non-NULL and *(char*)(anim_base + 0x31) == param_4 (type matches), jumps to model loading (label within CSWCCreature::LoadModel_Internal @ (K1: 0x0061b5a7, TSL: 0x0066a0c8))
          *      - NOTE: In K1, this is label LAB_0061b5a7 within CSWCCreature::LoadModel() @ 0x0061b380. In TSL, it's a label within CSWCCreature::LoadModel_Internal() @ 0x00669ea0.
          *    - Otherwise, destructs current anim_base via vtable[0](1) and proceeds to allocation
          * 4. Switch-based anim_base allocation (param_4 determines type):
          *    * case '\0' (0): Standard anim base
          *      - Allocates 0xfc bytes via operator_new() @ (K1: 0x006fa7e6, TSL: 0x0076d9f6) (was 0xf0 in K1, 12 bytes larger)
          *      - Calls CSWCAnimBase::CSWCAnimBase() @ (K1: 0x0069dfb0, TSL: 0x006f8340) (CSWCAnimBase constructor equivalent, 409 bytes)
          *      - Sets *(undefined4**)(param_1 + 0x68) = constructed anim_base
          *    * case '\x01' (1): Head anim base
          *      - Allocates 0x1d0 bytes (was 0x1c4 in K1, 12 bytes larger)
          *      - Calls CSWCAnimBaseHead::CSWCAnimBaseHead(pvVar4, 1) @ (K1: 0x0069bb80, TSL: 0x006f5e60) (CSWCAnimBaseHead constructor, 229 bytes)
          *      - Adjusts pointer via vtable[4] offset calculation: *(int*)(*piVar6 + 4) + (int)piVar6
          *    * case '\x02' (2): Wield anim base
          *      - Allocates 0x1dc bytes (was 0x1d0 in K1, 12 bytes larger)
          *      - Calls CSWCAnimBaseWield::CSWCAnimBaseWield(pvVar4, 1) @ (K1: 0x00699dd0, TSL: 0x006f41b0) (CSWCAnimBaseWield constructor, 256 bytes)
          *      - Adjusts pointer via vtable[4] offset calculation
          *    * case '\x03' (3): Head + Wield anim base
          *      - Allocates 0x22c bytes (was 0x220 in K1, 12 bytes larger)
          *      - Calls CSWCAnimBaseHeadWield::CSWCAnimBaseHeadWield(pvVar4, 1) @ (K1: 0x00698ec0, TSL: 0x006f32a0) (CSWCAnimBaseHeadWield constructor, 197 bytes)
          *      - Adjusts pointer via vtable[4] offset calculation
          *    * case '\v' (0x0b, 11): Two-Weapon anim base (NEW in TSL, not in K1)
          *      - Allocates 0x180 bytes (384 bytes)
          *      - Calls CSWCAnimBaseTW::CSWCAnimBaseTW() @ (K1: 0x0069cbd0, TSL: 0x006f6fb0) (CSWCAnimBaseTW constructor, 307 bytes)
          *      - Sets vtable to CSWCAnimBaseTW_vtable @ (K1: 0x00754e58, TSL: 0x007ce078)
          *      - Initializes 5 CResRef fields (K1) / CExoString fields (TSL) via CResRef_operator_assign_InitFromString() @ (K1: 0x00406290, TSL: 0x00405f40)
          *        - NOTE: In K1, uses CResRef::operator=() to initialize from empty string. In TSL, uses CExoString_InitEmpty().
          *      - Sets field at offset 0x31 to 0x0b (two-weapon type identifier)
          *      - Clears flags: param_1[0x5e] = 0, param_1[0x5f] = 0
          *      - Zeroes 5 additional fields (0x3f through 0x43)
          *    * default: Falls through to error handler (switchD_00669f38_caseD_4)
          * 5. Animation setup (after successful allocation):
          *    - Calls CSWAnimBase::Set() @ (K1: 0x00698e30, TSL: 0x006f3210) (Set equivalent, 81 bytes) 4 times with hardcoded float constants:
          *      * CSWAnimBase::Set(anim_base, 0, 0x44e74000) @ (K1: 0x00698e30, TSL: 0x006f3210) = 1216.0f (was Set() call in K1)
          *      * CSWAnimBase::Set(anim_base, 1, 0x45ce4000) @ (K1: 0x00698e30, TSL: 0x006f3210) = 6600.0f
          *      * CSWAnimBase::Set(anim_base, 2, 0x3f6ccccd) @ (K1: 0x00698e30, TSL: 0x006f3210) = 0.9f
          *      * CSWAnimBase::Set(anim_base, 3, 0x40533333) @ (K1: 0x00698e30, TSL: 0x006f3210) = 3.3f
          *    - CSWAnimBase::Set() @ (K1: 0x00698e30, TSL: 0x006f3210) implements switch-based setter: param_1 determines offset (4, 8, 0xc, 0x10)
          *    - Sets *(undefined4*)(param_1 + 0x200) = 0 (field159 initialization)
          * 6. Model resource loading:
          *    - Calls anim_base->vtable[0xc](param_2, param_3) (load model method, offset 0xc = 3rd vtable entry)
          *    - If loading fails (returns 0), calls error handler:
          *      * Calls CResRef::CopyToString(param_2) @ (K1: 0x00405f70, TSL: 0x00406050) (resource name getter, 72 bytes)
          *        - CResRef::CopyToString() @ (K1: 0x00405f70, TSL: 0x00406050) stores param_1 (CResRef internal data, 4 dwords) into circular buffer
          *        - K1: CResRef::GetResRefStr() @ (K1: 0x00405fe0) uses CResRef_GetResRefStr_Buffer @ (K1: 0x007a3d00, TSL: N/A) and CResRef_GetResRefStr_BufferIndex @ (K1: 0x007a3d48, TSL: N/A)
          *        - TSL: CResRef_CopyToString() uses CResRef_CopyToString_Buffer @ (K1: N/A, TSL: 0x008286e0) and CResRef_CopyToString_BufferIndex @ (K1: N/A, TSL: 0x00828728)
          *        - Uses modulo 4 circular buffer: BufferIndex = (BufferIndex + 1) & 0x80000003
          *        - Stores 4 dwords (16 bytes) at offset iVar1 = BufferIndex * 0x11 (17 bytes per entry, 4-entry buffer)
          *        - Stores null terminator at offset 0x10
          *        - Returns pointer to stored string
          *      * Calls sprintf(acStack_10c, "CSWCCreature::LoadModel(): Failed to load creature model '%s'.") @ (K1: 0x006fadb0, TSL: 0x0076dac2)
          *        - sprintf() @ (K1: 0x006fadb0, TSL: 0x0076dac2) is sprintf equivalent (88 bytes, 133 references)
          *        - Creates FILE structure on stack for formatting
          *        - Calls _vfprintf() @ (K1: N/A - standard library function, TSL: vswprintf_internal() @ 0x0077252f) (vswprintf equivalent) with format string
          *          NOTE: In K1, sprintf() uses _vfprintf() directly (standard library). TSL uses vswprintf_internal() for wide character string formatting.
          *        - Null-terminates result
          *      * Returns 0 (failure)
          * 7. Special parameter handling (param_3 checks):
          *    - If param_3 is -1, -2, -3, or -4 (special values), performs additional setup:
          *      * Calls anim_base->vtable[8](param_3) @ (K1: 0x0061b3e2, TSL: 0x0066a150) to get model attachment (call site within CSWCCreature::LoadModel_Internal)
          *        - NOTE: In K1, this is at offset 0x62 within CSWCCreature::LoadModel() @ 0x0061b380. In TSL, it's at offset 0xb0 within CSWCCreature::LoadModel_Internal() @ 0x00669ea0.
          *      * Calls attachment->vtable[0x74](param_1) (29th entry) - attachment setup
          *      * Calls attachment->vtable[0x7c](GameObjectType_Constant_5 @ (K1: 0x00746634, TSL: 0x007beaec)) (31st entry) - game object types setup (value: 5)
          *    - If param_3 == -1 (headconjure special case):
          *      * Initializes quaternion on stack: {0, 0, 0, 1.0f}
          *      * Calls RegisterCallbacks_Headconjure(param_1) @ (K1: 0x0061ab40, TSL: 0x00669570) (RegisterCallbacks for headconjure, 532 bytes)
          *        - RegisterCallbacks_Headconjure() @ (K1: 0x0061ab40, TSL: 0x00669570) registers sound callbacks via anim_base->vtable[8](0xff)
          *        - NOTE: In K1, RegisterCallbacks_Headconjure is the same function as RegisterCallbacks (both at 0x0061ab40, 532 bytes). In TSL, they are separate functions.
          *        - Registers callbacks for: "snd_Footstep", "snd_Footstep" (second callback), "snd_hitground", "SwingShort", "SwingLong",
          *          "SwingTwirl", "Clash", "Contact", "HitParry", "blur_start", "blur_end", "doneattack01", "doneattack02",
          *          "GetPersonalRadius", "GetCreatureRadius", "GetPath"
          *        - Stores callback IDs in creature structure offsets 0x404, 0x408, 0x410, 0x414, 0x418, 0x41c, 0x420, 0x424, 0x428, 0x42c, 0x430, 0x434, 0x438, 0x43c, 0x440, 0x444
          *      * Calls anim_base->vtable[0xa0]("headconjure", &uStack_134, &uStack_128) (40th entry, finds dummy node)
          *      * If headconjure dummy not found (returns 0), sets *(float*)(param_1 + 0xa4) = 0x40066666 (3.2f, default value)
          *      * Otherwise, calculates: *(float*)(param_1 + 0xa4) = fStack_12c - fStack_12c * FloatConstant_0_125 @ (K1: 0x0073f400, TSL: 0x007b7428)
          *        - FloatConstant_0_125 @ (K1: 0x0073f400, TSL: 0x007b7428): Float constant 0.125f (cross-referenced in 9 locations, scale factor)
          * 8. Callback registration:
          *    - Calls RegisterCallbacks(param_1) @ (K1: 0x0061ab40, TSL: 0x00693fe0) (RegisterCallbacks equivalent, 100 bytes, 177 references)
          *      - RegisterCallbacks() @ (K1: 0x0061ab40, TSL: 0x00693fe0) checks if *(int*)(param_1 + 0xf8) is NULL (cached callback result)
          *      - If NULL and *(int*)(param_1 + 0xe4) == 0, calls GetObjectTypeID() @ (K1: N/A - not used, TSL: 0x004dc2e0) and GetObjectByTypeID() @ (K1: N/A - not used, TSL: 0x004dc650) to get callback handler
          *        NOTE: In K1, RegisterCallbacks() does not use GetObjectTypeID/GetObjectByTypeID. It directly calls anim_base->vtable[8](0xff) to get the callback handler.
          *      - Calls handler->vtable[0x10]() to get callback object
          *      - Stores result in *(void**)(param_1 + 0xf8)
          *      - If callback object exists, calls SetCallbackTarget(callback, param_1) @ (K1: N/A - not used, TSL: 0x005056f0) to register callbacks
          *        NOTE: In K1, RegisterCallbacks() directly registers callbacks via handler->vtable[0x28]() without using SetCallbackTarget. TSL uses SetCallbackTarget() for callback registration.
          *      - Returns *(undefined4*)(param_1 + 0xf8)
          *    - If callback registration succeeds:
          *      * Calls callback->vtable[0x30]() to get animation object
          *      * If animation exists:
          *        - Checks *(int*)(animation + 0x24c) and calls anim_base->vtable[0x18c](1) if non-NULL (31st entry)
          *        - Checks *(int*)(animation + 0x254) and calls anim_base->vtable[0x1a0](0) if non-NULL (40th entry)
          *      * Calls anim_base->vtable[0x1a0](1) (40th entry, enable animation)
          *    - Gets creature size class: sVar1 = *(short*)(*(int*)(param_1 + 0x310) + 0x80)
          *    - Calls anim_base->vtable[0x168](sVar1) (90th entry, set size class)
          *    - If size class < 0x3d (61):
          *      * If size class < 0x29 (41), performs interpolation calculations:
          *        - fVar9 = 1.0f
          *        - fVar10 = (float)(0x28 - sVar1) * FloatConstant_0_0125 @ (K1: Inline constant 0x3c888889, TSL: 0x007c82ec)
          *        - fVar12 = (FloatConstant_1_0 @ (K1: Inline constant 0x3f800000, TSL: 0x007b5774) - fVar10) * FloatConstant_0_65 @ (K1: Inline constant 0x3d266666, TSL: 0x007c82e8)
          *        - fVar11 = fVar10 * FloatConstant_0_05 @ (K1: Inline constant 0x3d4ccccd, TSL: 0x007b9700) + fVar12
          *        - fVar12 = fVar10 * FloatConstant_0_01 @ (K1: Inline constant 0x3c23d70a, TSL: 0x007b5f88) + fVar12
          *        - FloatConstant_0_0125 @ (K1: Inline constant 0x3c888889, TSL: 0x007c82ec): Float constant 0.0125f (cross-referenced 4 times, interpolation factor)
          *          NOTE: In K1, this constant is used inline in code (0x3c888889 = 0.0125f). In TSL, it's stored as a data constant.
          *        - FloatConstant_1_0 @ (K1: Inline constant 0x3f800000, TSL: 0x007b5774): Float constant 1.0f (cross-referenced 78 times, scale factor)
          *          NOTE: In K1, this constant is used inline in code (0x3f800000 = 1.0f). In TSL, it's stored as a data constant.
          *        - FloatConstant_0_65 @ (K1: Inline constant 0x3d266666, TSL: 0x007c82e8): Float constant 0.65f (cross-referenced 8 times, interpolation factor)
          *          NOTE: In K1, this constant is used inline in code (0x3d266666 = 0.65f). In TSL, it's stored as a data constant.
          *        - FloatConstant_0_05 @ (K1: Inline constant 0x3d4ccccd, TSL: 0x007b9700): Float constant 0.05f (cross-referenced 1 time, interpolation weight)
          *          NOTE: In K1, this constant is used inline in code (0x3d4ccccd = 0.05f). In TSL, it's stored as a data constant.
          *        - FloatConstant_0_01 @ (K1: Inline constant 0x3c23d70a, TSL: 0x007b5f88): Float constant 0.01f (cross-referenced 1 time, interpolation weight)
          *          NOTE: In K1, this constant is used inline in code (0x3c23d70a = 0.01f). In TSL, it's stored as a data constant.
          * 9. Return: Returns 1 on success, 0 on failure
          * MEMORY LAYOUT CHANGES (K1 vs TSL):
          * - anim_base: param_1 + 0x68 (was this->object.anim_base, offset 0x358 in K1)
          * - cached_anim_base: param_1 + 0x370 (was this->field158_0x358, +24 bytes offset change)
          * - field159: param_1 + 0x200 (was this->field65_0x1f8, +8 bytes offset change)
          * - cached_field159: param_1 + 0x374 (new in TSL, was not cached in K1)
          * - size_class_access: param_1 + 0x310 + 0x80 (was different offset in K1)
          * - callback_cache: param_1 + 0xf8 (new in TSL, was not cached in K1)
          * - callback_flag: param_1 + 0xe4 (new in TSL, callback registration flag)
          * ALLOCATION SIZE COMPARISON:
          * - Standard: 0xfc (252 bytes) in TSL vs 0xf0 (240 bytes) in K1 (+12 bytes)
          * - Head: 0x1d0 (464 bytes) in TSL vs 0x1c4 (452 bytes) in K1 (+12 bytes)
          * - Wield: 0x1dc (476 bytes) in TSL vs 0x1d0 (464 bytes) in K1 (+12 bytes)
          * - HeadWield: 0x22c (556 bytes) in TSL vs 0x220 (544 bytes) in K1 (+12 bytes)
          * - TwoWeapon: 0x180 (384 bytes) in TSL (NEW, not present in K1)
          * VTABLE OFFSET COMPARISON:
          * - Load model: offset 0xc (3rd entry) in TSL vs offset 0xc in K1 (same)
          * - Get attachment: offset 0x8 (2nd entry) in TSL vs offset 0x8 in K1 (same)
          * - Destructor: offset 0x0 (1st entry) in TSL vs offset 0x0 in K1 (same)
          * - Find dummy: offset 0xa0 (40th entry) in TSL vs different offset in K1
          * - Set size: offset 0x168 (90th entry) in TSL vs different offset in K1
          * - Enable animation: offset 0x1a0 (104th entry) in TSL vs different offset in K1
          * - Attachment setup: offset 0x74 (29th entry) in TSL vs offset 0x74 in K1 (same)
          * - Game object types: offset 0x7c (31st entry) in TSL vs offset 0x7c in K1 (same)
          * - Animation checks: offset 0x18c (39th entry) in TSL vs different offset in K1
          * CALLEES (11 total, verified via decompilation):
          * - CSWCAnimBase::CSWCAnimBase() @ (K1: 0x0069dfb0, TSL: 0x006f8340): CSWCAnimBase constructor (409 bytes, 8 callers)
          *   * Initializes vtable to CSWCAnimBase_vtable @ (K1: 0x00754f60, TSL: 0x007ce180)
          *   * Initializes 5 CResRef fields (K1) / CExoString fields (TSL) via CResRef_operator_assign_InitFromString() @ (K1: 0x00406290, TSL: 0x00406350) with empty strings
          *     - NOTE: In K1, uses CResRef::operator=() to initialize from empty string. In TSL, uses CExoString_InitFromString().
          *   * Initializes quaternion via Quaternion_InitDefault() @ (K1: 0x004ac960, TSL: 0x004da020) with default values
          *     - NOTE: In K1, uses Quaternion::Quaternion() constructor with unitVectorZ and 0.0 angle. In TSL, uses Quaternion_Set() function.
          *   * Sets default scale to 1.0f
          *   * Sets flags: param_1[0x37] = 1 (active flag)
          *   * Called from CSWCAnimBaseTW::CSWCAnimBaseTW() @ (K1: 0x0069cbd0, TSL: 0x006f6fb0) (CSWCAnimBaseTW constructor) and directly
          * - CSWCAnimBaseHead::CSWCAnimBaseHead() @ (K1: 0x0069bb80, TSL: 0x006f5e60): CSWCAnimBaseHead constructor (229 bytes, 3 callers)
          *   * If param_1 != 0, sets vtable to CSWCAnimBaseHead_vtable @ (K1: 0x00754e40, TSL: 0x007ce060), calls CSWCAnimBaseTW::CSWCAnimBaseTW() @ (K1: 0x0069cbd0, TSL: 0x006f6fb0) on offset 0x50 sub-object
          *   * Sets vtable offset for base class to CSWCAnimBaseHead_base_vtable @ (K1: Calculated dynamically from CSWCAnimBaseHead_vtable offset, TSL: 0x007cdf68)
          *     NOTE: In K1, the base class vtable offset is calculated at line 20: `*(undefined ***)(this + *(int *)(*(int *)this + 4)) = &CSWCAnimBaseHead_AnimBase_vtable;`
          *     The offset is calculated as `*(int *)(*(int *)this + 4)` (vtable offset) and the base vtable pointer is stored at that calculated offset.
          *     TSL uses a separate base class vtable pointer constant at 0x007cdf68.
          *   * Initializes 2 CResRef fields (K1) / CExoString fields (TSL) via CResRef_InitEmpty() @ (K1: 0x00405ed0, TSL: 0x00405f40) (offsets 0x1c, 0x30)
          *     - NOTE: In K1, uses CResRef::CResRef() constructor. In TSL, uses CExoString_InitEmpty().
          *   * Sets field at offset 0xc4 to 1 (type identifier)
          *   * Sets field at offset 0x48 to 0x7f000000 (INF, scale maximum)
          * - CSWCAnimBaseWield::CSWCAnimBaseWield() @ (K1: 0x00699dd0, TSL: 0x006f41b0): CSWCAnimBaseWield constructor (256 bytes, 3 callers)
          *   * If param_1 != 0, sets vtable to CSWCAnimBaseWield_vtable @ (K1: 0x00754d00, TSL: 0x007cdf20), calls CSWCAnimBaseTW::CSWCAnimBaseTW() @ (K1: 0x0069cbd0, TSL: 0x006f6fb0) on offset 0x5c sub-object
          *   * Sets vtable offset for base class to CSWCAnimBaseWield_base_vtable @ (K1: CSWCAnimBaseWield_AnimBase_vtable @ 0x00754c08, TSL: 0x007cde28)
          *     NOTE: In K1, the base class vtable offset is calculated at line 20: `*(undefined ***)(this + *(int *)(*(int *)this + 4)) = &CSWCAnimBaseWield_AnimBase_vtable;`
          *     The offset is calculated as `*(int *)(*(int *)this + 4)` (vtable offset) and the base vtable pointer (CSWCAnimBaseWield_AnimBase_vtable @ 0x00754c08) is stored at that calculated offset.
          *     TSL uses a separate base class vtable pointer constant at 0x007cde28.
          *   * Initializes 2 CResRef fields (K1) / CExoString fields (TSL) via CResRef_InitEmpty() @ (K1: 0x00405ed0, TSL: 0x00405f40) (offsets 4, 0x14)
          *     - NOTE: In K1, uses CResRef::CResRef() constructor. In TSL, uses CExoString_InitEmpty().
          *   * Calls CExoString_InitEmpty() @ (K1: 0x00405ed0, TSL: 0x005ff130) on 2 fields (offsets 0x24, 0x2c) - string cleanup/initialization
          *     - NOTE: In K1, uses CResRef::CResRef() constructor. In TSL, uses CExoString_InitEmpty() (16 bytes, zeros 2 dwords).
          *   * Sets field at offset 0xc4 to 2 (type identifier)
          *   * Zeroes 6 fields (offsets 0x34, 0x38, 0x48, 0x4c, 0x50, 0x54)
          * - CSWCAnimBaseHeadWield::CSWCAnimBaseHeadWield() @ (K1: 0x00698ec0, TSL: 0x006f32a0): CSWCAnimBaseHeadWield constructor (197 bytes, 2 callers)
          *   * If param_1 != 0:
          *     - Sets vtable to CSWCAnimBaseHeadWield_vtable @ (K1: 0x00754bf0, TSL: 0x007cde10)
          *     - Sets field at offset 0x188 to CSWCAnimBaseHeadWield_HeadSubObject_vtable @ (K1: 0x00754be8, TSL: 0x007cde08) (CSWCAnimBaseHead sub-object vtable)
          *     - Sets field at offset 0x1d4 to CSWCAnimBaseHeadWield_WieldSubObject_vtable @ (K1: 0x00754be0, TSL: 0x007cde00) (CSWCAnimBaseWield sub-object vtable)
          *     - Calls CSWCAnimBaseTW::CSWCAnimBaseTW() @ (K1: 0x0069cbd0, TSL: 0x006f6fb0) on offset 8 sub-object
          *     - Calls CSWCAnimBaseHead::CSWCAnimBaseHead() @ (K1: 0x0069bb80, TSL: 0x006f5e60) on offset 0x188 sub-object (Head constructor)
          *     - Calls CSWCAnimBaseWield::CSWCAnimBaseWield() @ (K1: 0x00699dd0, TSL: 0x006f41b0) on offset 0x1d4 sub-object (Wield constructor)
          *   * Sets field at offset 0xc4 to 3 (type identifier)
          * - CSWCAnimBaseTW::CSWCAnimBaseTW() @ (K1: 0x0069cbd0, TSL: 0x006f6fb0): CSWCAnimBaseTW constructor (307 bytes, 5 callers)
          *   * Calls CSWCAnimBase::CSWCAnimBase() @ (K1: 0x0069dfb0, TSL: 0x006f8340) first (base CSWCAnimBase construction)
          *   * Sets vtable to CSWCAnimBaseTW_vtable @ (K1: 0x00754e58, TSL: 0x007ce078)
          *   * Initializes 4 CResRef fields (K1) / CExoString fields (TSL) via CResRef_InitEmpty() @ (K1: 0x00405ed0, TSL: 0x00405f40) (offsets 0x4a, 0x4f, 0x54, 0x59)
          *     - NOTE: In K1, uses CResRef::CResRef() constructor. In TSL, uses CExoString_InitEmpty().
          *   * Sets field at offset 0x31 to 0x0b (two-weapon type)
          *   * Zeroes flags: param_1[0x5e] = 0, param_1[0x5f] = 0
          *   * Initializes 5 additional fields to 0 (offsets 0x3f through 0x43)
          * - CSWAnimBase::Set() @ (K1: 0x00698e30, TSL: 0x006f3210): Set equivalent (81 bytes, 8 callers)
          *   * Switch-based setter: param_1 (0-3) determines which field to set
          *   * case 0: Sets *(undefined4*)(this + 4) = param_2
          *   * case 1: Sets *(undefined4*)(this + 8) = param_2
          *   * case 2: Sets *(undefined4*)(this + 0xc) = param_2
          *   * case 3: Sets *(undefined4*)(this + 0x10) = param_2
          *   * Returns 1 on success, 0 on default case
          *   * Called 4 times in LoadModel_Internal with hardcoded float values
          * - RegisterCallbacks() @ (K1: 0x0061ab40, TSL: 0x00693fe0): RegisterCallbacks equivalent (K1: 532 bytes, TSL: 100 bytes, 177 references)
          *   * NOTE: In K1, RegisterCallbacks() is the same function as RegisterCallbacks_Headconjure() (both at 0x0061ab40, 532 bytes).
          *   * In TSL, RegisterCallbacks() (0x00693fe0, 100 bytes) is a separate, simpler function that uses GetObjectTypeID/GetObjectByTypeID.
          *   * K1 RegisterCallbacks() directly calls anim_base->vtable[8](0xff) to get callback handler, then registers 16 callbacks.
          *   * TSL RegisterCallbacks() checks if *(int*)(param_1 + 0xf8) is cached (callback result)
          *   * TSL: If NULL and *(int*)(param_1 + 0xe4) == 0:
          *     - Calls GetObjectTypeID(*(uint*)(param_1 + 4)) @ (K1: N/A - not used, TSL: 0x004dc2e0) to get callback type ID
          *     - Calls GetObjectByTypeID(*(void**)(CallbackRegistry @ (K1: N/A, TSL: 0x008283d4) + 8), uVar1) @ (K1: N/A - not used, TSL: 0x004dc650) to get callback handler from registry
          *     - If handler exists, calls handler->vtable[0x10]() to get callback object
          *     - Stores callback in *(void**)(param_1 + 0xf8)
          *     - If callback exists, calls SetCallbackTarget(callback, param_1) @ (K1: N/A - not used, TSL: 0x005056f0) to register callbacks
          *   * Returns *(undefined4*)(param_1 + 0xf8)
          *   * Called 4 times in LoadModel_Internal at lines 170, 175 (twice conditionally)
          * - RegisterCallbacks_Headconjure() @ (K1: 0x0061ab40, TSL: 0x00669570): RegisterCallbacks for headconjure (532 bytes, 1 caller)
          *   * Signature: void __fastcall RegisterCallbacks_Headconjure(int param_1) @ (K1: 0x0061ab40, TSL: 0x00669570)
          *   * NOTE: In K1, RegisterCallbacks_Headconjure is the same function as RegisterCallbacks (both at 0x0061ab40, 532 bytes). In TSL, they are separate functions.
          *   * Logic (from decompilation):
          *     * Gets callback handler via anim_base->vtable[8](0xff) call at *(undefined4**)(param_1 + 0x68)
          *     * If handler exists (piVar1 != NULL):
          *       * Registers 16 sound/animation callbacks via handler->vtable[0x28]() call
          *       * Each callback registered with 0x461c3c00 (10000.0f) as distance parameter
          *       * Stores callback function pointers in creature structure at offsets 0x404 through 0x444
          *     * Returns void
          *   * Callees:
          *     * anim_base->vtable[8](0xff) @ *(undefined4**)(param_1 + 0x68) (callback handler getter)
          *     * handler->vtable[0x28]() (callback registration, called 16 times)
          *     * HitGroundEvent() @ (K1: 0x0060b400, TSL: 0x00657590) (callback function pointer, used for "snd_hitground")
          *     * SwingShortEvent() @ (K1: 0x00610c90, TSL: 0x0065d0c0) (callback function pointer, used for "SwingShort")
          *     * SwingLongEvent() @ (K1: 0x00610d10, TSL: 0x0065d140) (callback function pointer, used for "SwingLong")
          *     * SwingTwirlEvent() @ (K1: 0x00610d90, TSL: 0x0065d1c0) (callback function pointer, used for "SwingTwirl")
          *     * HitClashEvent() @ (K1: 0x00610e10, TSL: 0x0065d240) (callback function pointer, used for "Clash")
          *     * HitContactEvent() @ (K1: 0x00610e90, TSL: 0x0065d2c0) (callback function pointer, used for "Contact")
          *     * HitParryEvent() @ (K1: 0x00610ec0, TSL: 0x0065d2f0) (callback function pointer, used for "HitParry")
          *     * Blur() @ (K1: 0x00449ab0, TSL: 0x00664030) (callback function pointer, used for "blur_start")
          *     * Unblur() @ (K1: 0x00616a10, TSL: 0x00664040) (callback function pointer, used for "blur_end", "doneattack01", "doneattack02")
          *     * GetPersonalRadius() @ (K1: 0x0060e120, TSL: 0x0065a330) (callback function pointer, used for "GetPersonalRadius")
          *     * GetCreatureRadius() @ (K1: 0x0060e170, TSL: 0x0065a380) (callback function pointer, used for "GetCreatureRadius")
          *     * GetPath() @ (K1: 0x0060e1c0, TSL: 0x0065a3d0) (callback function pointer, used for "GetPath")
          *   * Registers 16 sound/animation callbacks:
          *     - "snd_Footstep" @ (K1: 0x0074f838, TSL: 0x007c82d0) (referenced at (K1: 0x0061ab65, TSL: 0x006695f0), stores at param_1 + 0x3ec)
          *     - "hit" @ (K1: 0x0074f834, TSL: 0x007c82cc) (sound reference, referenced at (K1: 0x0061ab82, TSL: 0x006695fa), stores at param_1 + 0x3f0)
          *     - "snd_hitground" @ (K1: 0x0074f824, TSL: 0x007c82bc) (referenced at (K1: 0x0061aba1, TSL: 0x0066960a), stores at param_1 + 0x3f8)
          *     - "SwingShort" @ (K1: 0x0074f48c, TSL: 0x007c7e00) (referenced at (K1: 0x0061abc0, TSL: 0x00669612), stores at param_1 + 0x3fc)
          *     - "SwingLong" @ (K1: 0x0074f498, TSL: 0x007c7e0c) (referenced at (K1: 0x0061abdf, TSL: 0x0066961e), stores at param_1 + 0x400)
          *     - "SwingTwirl" @ (K1: 0x0074f4a4, TSL: 0x007c7e18) (referenced at (K1: 0x0061abfe, TSL: 0x0066962a), stores at param_1 + 0x404)
          *     - "Clash" @ (K1: 0x0074f4b0, TSL: 0x007c7e24) (referenced at (K1: 0x0061ac1d, TSL: 0x00669636), stores at param_1 + 0x408)
          *     - "Contact" @ (K1: 0x0074f81c, TSL: 0x007c82b4) (referenced at (K1: 0x0061ac3c, TSL: 0x00669642), stores at param_1 + 0x40c)
          *     - "HitParry" @ (K1: 0x0074f810, TSL: 0x007c82a8) (referenced at (K1: 0x0061ac5b, TSL: 0x0066964e), stores at param_1 + 0x410)
          *     - "blur_start" @ (K1: 0x0074f804, TSL: 0x007c829c) (referenced at (K1: 0x0061ac7a, TSL: 0x0066965a), stores at param_1 + 0x414)
          *     - "blur_end" @ (K1: 0x0074f7f8, TSL: 0x007c8290) (referenced at (K1: 0x0061ac99, TSL: 0x00669666), stores at param_1 + 0x418)
          *     - "doneattack01" @ (K1: 0x0074f7e8, TSL: 0x007c8280) (referenced at (K1: 0x0061acb8, TSL: 0x00669672), stores at param_1 + 0x41c)
          *     - "doneattack02" @ (K1: 0x0074f7d8, TSL: 0x007c8270) (referenced at (K1: 0x0061acd7, TSL: 0x0066967e), stores at param_1 + 0x420)
          *     - "GetPersonalRadius" @ (K1: 0x00742f30, TSL: 0x007bb13c) (referenced at (K1: 0x0061acf6, TSL: 0x0066968a), stores at param_1 + 0x424)
          *     - "GetCreatureRadius" @ (K1: 0x00742f1c, TSL: 0x007bb128) (referenced at (K1: 0x0061ad15, TSL: 0x00669696), stores at param_1 + 0x428)
          *     - "GetPath" @ (K1: 0x00742f14, TSL: 0x007bb120) (referenced at (K1: 0x0061ad34, TSL: 0x006696a2), stores at param_1 + 0x42c)
          *   * All callbacks registered with 0x461c3c00 (10000.0f) as distance parameter
          *   * All string references verified via cross-reference search in TSL executable
          * - CResRef_CopyToString() / CResRef_GetResRefStr() @ (K1: 0x00405fe0, TSL: 0x00406050): Resource name cache/getter (K1: different implementation, TSL: 72 bytes, 35 references)
          *   * Signature: K1: char* __thiscall CResRef::GetResRefStr(CResRef *this), TSL: void __fastcall CResRef_CopyToString(undefined4 *param_1)
          *   * Logic (from decompilation):
          *     * Implements circular buffer cache for CExoString resource names
          *     * K1: Uses CResRef::GetResRefStr() @ (K1: 0x00405fe0) with CResRef_GetResRefStr_Buffer @ (K1: 0x007a3d00) and CResRef_GetResRefStr_BufferIndex @ (K1: 0x007a3d48)
          *       - Returns char* pointer to cached string in buffer
          *     * TSL: Uses CResRef_CopyToString() with CResRef_CopyToString_Buffer @ (TSL: 0x008286e0) and CResRef_CopyToString_BufferIndex @ (TSL: 0x00828728)
          *       - Updates buffer index: BufferIndex = (BufferIndex + 1) & 0x80000003
          *       - Handles negative modulo: if (int)BufferIndex < 0, adjusts to positive range
          *       - Calculates storage offset: iVar1 = BufferIndex * 0x11 (17 bytes per entry, 4-entry buffer)
          *       - Stores 4 dwords (16 bytes) from param_1 to buffer at Buffer + iVar1
          *       - Appends null terminator at offset 0x10 (16th byte of entry)
          *       - Returns void (modifies global buffer)
          *   * Callees: None (pure arithmetic/memory operations)
          *   * Callers: CSWCCreature::LoadModel error handler @ (K1: 0x0061b5cf, TSL: 0x0066a0f0) (called once for error message formatting), plus 34 other functions
          *   * Usage: Caches resource names for error messages and logging (4-entry circular buffer prevents memory leaks)
          * - sprintf() @ (K1: 0x006fadb0, TSL: 0x0076dac2): sprintf equivalent (K1: 88 bytes, TSL: 88 bytes, 133 references)
          *   * Creates FILE structure on stack for string formatting
          *   * K1: Calls _vfprintf() with format string and arguments
          *   * TSL: Calls vswprintf_internal() @ (K1: N/A - uses _vfprintf() instead, TSL: 0x0077252f) (vswprintf equivalent) with format string and arguments
          *     NOTE: In K1, sprintf() uses _vfprintf() directly (standard library function). TSL uses vswprintf_internal() for wide character string formatting.
          *   * Null-terminates result string
          *   * Returns formatted string count
          * - operator_new() @ (K1: 0x006fa7e6, TSL: 0x0076d9f6): Memory allocator (14 bytes, 2548 references)
          *   * Calls __nh_malloc(param_1, 1) for aligned allocation
          *   * Returns allocated memory pointer or NULL
          *   * Called 5 times in LoadModel_Internal for different anim_base types
          * CALLERS: None found via direct references (vtable call via object method)
          * VTABLE ENTRY: Located at offset in CSWCCreature class structure, stored at (K1: 0x0074f670, TSL: 0x007c8040)
          *   * NOTE: In K1, the vtable entry at 0x0074f670 points to CSWCCreature::LoadModel @ 0x0061b380. This is the vtable entry for CSWCCreature::LoadModel_Internal, referenced in CSWCCreature::LoadModel at K1: 0x0061b3e2 (call site: anim_base->vtable[8](param_3))
          * STRING REFERENCES (verified via cross-references):
          * - Error string @ (K1: 0x0074f85c, TSL: 0x007c82fc): "CSWCCreature::LoadModel(): Failed to load creature model '%s'."
          *   * Referenced in CSWCCreature::LoadModel error handler @ (K1: 0x0061b5cf, TSL: 0x0066a0f0)
          *   * Format string used in sprintf() @ (K1: 0x006fadb0, TSL: 0x0076dac2) (sprintf equivalent)
          *   * Cross-referenced from error handler function only
          * - "headconjure" @ (K1: Inline string literal at 0x0061b676, TSL: 0x007c82f0): Dummy node name for spell visual positioning
          *   * Referenced in LoadModel_Internal @ (K1: 0x0061b676, TSL: 0x0066a1a5) via anim_base->vtable[0xa0]() call
          *   * NOTE: In K1, the string "headconjure" is passed directly as a string literal at line 148 of CSWCCreature::LoadModel (0x0061b676). The string is stored inline in the code segment rather than as a data constant. Related strings found: "Bheadconjure" @ 0x0074f84f (used elsewhere).
          *   * Also referenced in 7 other functions: [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x00702e20), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x00701870), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x00700da0), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x006f8590), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x006efe40), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x006a5490), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x006efaf0)
          *   * Used to find headconjure dummy node in model hierarchy for spell effect positioning
          * - "_head_hit" @ (K1: 0x00753918, TSL: 0x007ccaf8): Hit detection node suffix
          *   * Referenced in 3 functions: [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x00700da0), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x00705d20), [TODO: Name this function]() @ (K1: TODO: Find this address, TSL: 0x007052a0)
          *   * Not directly used in LoadModel_Internal, but related to model hit detection setup
          * - "snd_Footstep" @ (K1: 0x0074f838, TSL: 0x007c82d0): Footstep sound callback name
          *   * Referenced only in RegisterCallbacks() @ (K1: 0x0061ab40, TSL: 0x00669595)
          *   * Used to register footstep sound callback for creature animations
          * - "snd_hitground" @ (K1: 0x0074f824, TSL: 0x007c82bc): Hit ground sound callback name
          *   * Referenced only in RegisterCallbacks() @ (K1: 0x0061ab40, TSL: 0x006695d1)
          *   * Used to register hit ground sound callback for creature animations
          * DATA CONSTANTS (verified via cross-references):
          * - GameObjectType_Constant_5 @ (K1: 0x00746634, TSL: 0x007beaec): Game object types constant (value: 5, cross-referenced 78 times)
          *   * Verified in both executables via cross-reference search
          *   * Passed to anim_base->vtable[0x7c]() for game object type setup
          *   * Labeled as GAME_OBJECT_TYPES_00746634 in K1
          * - FloatConstant_0_125 @ (K1: 0x0073f400, TSL: 0x007b7428): Float scale factor (0.125f, cross-referenced 9 times)
          *   * Used in headconjure calculation: fStack_12c - fStack_12c * FloatConstant_0_125 @ (K1: 0x0073f400, TSL: 0x007b7428)
          *   * Labeled as FLOAT_0073f400 in K1
          * - FloatConstant_0_0125 @ (K1: Inline constant 0x3c888889, TSL: 0x007c82ec): Float interpolation factor (0.0125f, cross-referenced 4 times)
          *   * Used in size class interpolation: (float)(0x28 - sVar1) * FloatConstant_0_0125 @ (K1: Inline constant 0x3c888889, TSL: 0x007c82ec)
          *   * NOTE: In K1, this constant is used inline in code (0x3c888889 = 0.0125f). In TSL, it's stored as a data constant.
          * - FloatConstant_1_0 @ (K1: Inline constant 0x3f800000, TSL: 0x007b5774): Float scale factor (1.0f, cross-referenced 78 times)
          *   * Used in size class interpolation: (FloatConstant_1_0 @ (K1: Inline constant 0x3f800000, TSL: 0x007b5774) - fVar10) * FloatConstant_0_65 @ (K1: Inline constant 0x3d266666, TSL: 0x007c82e8)
          *   * NOTE: In K1, this constant is used inline in code (0x3f800000 = 1.0f). In TSL, it's stored as a data constant.
          * - FloatConstant_0_65 @ (K1: Inline constant 0x3d266666, TSL: 0x007c82e8): Float interpolation factor (0.65f, cross-referenced 8 times)
          *   * Used in size class interpolation calculations
          *   * NOTE: In K1, this constant is used inline in code (0x3d266666 = 0.65f). In TSL, it's stored as a data constant.
          * - FloatConstant_0_05 @ (K1: Inline constant 0x3d4ccccd, TSL: 0x007b9700): Float interpolation weight (0.05f, cross-referenced 1 time)
          *   * Used in size class interpolation: fVar10 * FloatConstant_0_05 @ (K1: Inline constant 0x3d4ccccd, TSL: 0x007b9700) + fVar12
          *   * NOTE: In K1, this constant is used inline in code (0x3d4ccccd = 0.05f). In TSL, it's stored as a data constant.
          * - FloatConstant_0_01 @ (K1: Inline constant 0x3c23d70a, TSL: 0x007b5f88): Float interpolation weight (0.01f, cross-referenced 1 time)
          *   * Used in size class interpolation: fVar10 * FloatConstant_0_01 @ (K1: Inline constant 0x3c23d70a, TSL: 0x007b5f88) + fVar12
          *   * NOTE: In K1, this constant is used inline in code (0x3c23d70a = 0.01f). In TSL, it's stored as a data constant.
          * - SizeClassConstant_5 @ (K1: TODO: Find this address, TSL: 0x007c514c): Size class constant (value: 5, cross-referenced 22 times)
          *   * Used in SizeClassValidationFunction() @ (K1: TODO: Find this address, TSL: 0x0051f0b0) for size class validation
          *   * TSL: Validates creature size class, returns size class value based on creature properties
          * KEY DIFFERENCES FROM K1:
          * 1. Additional case '\v' (0x0b) for two-weapon anim base (not present in K1)
          * 2. Different allocation sizes for all anim base types (+12 bytes each)
          * 3. Different memory offsets for class members (due to structure layout changes)
          * 4. Additional caching mechanism for anim_base and field159 (offsets 0x370, 0x374)
          * 5. Additional callback caching mechanism (offset 0xf8)
          * 6. Different vtable offsets for some methods (Find dummy, Set size, Enable animation)
          * 7. Additional interpolation calculations for size class (not present in K1)
          * 8. Additional headconjure positioning calculation with FloatConstant_0_125 @ (K1: 0x0073f400, TSL: 0x007b7428) scale factor
          * 9. Different string addresses (expected with recompilation)
          * 10. Obfuscated function names (FUN_* instead of clear names)
          * ERROR HANDLER: CSWCCreature::LoadModel @ 0x0066a0f0 (43 bytes, separate function)
          *   * Signature: undefined4 __thiscall CSWCCreature::LoadModel(char *param_1)
          *   * Logic: Calls sprintf equivalent @ (K1: 0x006fadb0, TSL: 0x0076dac2) with error string format and resource name
          *   * Called from: switch case 4 (default case) in LoadModel_Internal
          *   * Returns: 0 (failure)
          *   * Note: This is a separate error handler function, not the main LoadModel function

    - CSWCPlaceable::LoadModel @ (K1: 0x006823f0, TSL: 0x006d9721)
      * Placeable object model loader (504 bytes, 10 callees)
        * Signature: undefined4 __thiscall CSWCPlaceable::LoadModel(CSWCPlaceable *this, CResRef *param_1, byte param_2, byte param_3)
        * Logic (from decompilation):
          * Checks if (this->object).anim_base is NULL
          * If NULL, allocates 0xf0 bytes and constructs CSWCAnimBasePlaceable @ 0x006e4e50
          * Calls anim_base->vtable[3](param_1) to load model resource
          * If loading fails, returns 0
          * Calls anim_base->vtable[2](param_2) to get model attachment
          * If attachment exists, calls attachment->vtable[29](this) and attachment->vtable[31](GAME_OBJECT_TYPES)
          * Extracts model name from param_1 using CResRef::CopyToString()
          * Gets substring from position 4 using CExoString::SubString()
          * Constructs hit detection string by appending "_head_hit" to model name
          * Returns 1 on success
        * Callees:
          * operator_new() @ 0x006fa7e6 (memory allocation)
          * CResRef::CopyToString() @ (K1: 0x00405f70, TSL: 0x00406050) - resource name extraction
          * CExoString::CExoString() @ (K1: 0x005e5a90, TSL: 0x00630a90) - string constructor)
          * CExoString::CStr() @ (K1: 0x005e5670, TSL: 0x006306b0) - C string accessor)
          * CExoString::CExoString() @ (K1: 0x005b3190, TSL: 0x005ff130) - empty string constructor)
          * CExoString::operator+() @ (K1: 0x005e5d10, TSL: 0x00630dd0) - string concatenation)
          * CSWCAnimBasePlaceable::CSWCAnimBasePlaceable() @ (K1: 0x006e4e50, TSL: 0x00755970) - placeable anim base)
          * CExoString::SubString() @ (K1: 0x005e6270, TSL: 0x00631330) - substring extraction
          * CExoString::operator=() @ (K1: 0x005e5c50, TSL: 0x00630c50) - string assignment, called 2 times
          * CExoString::~CExoString() @ (K1: 0x005e5c20, TSL: 0x00630c20) - string destructor, called 4 times
        * String References: "_head_hit" (hardcoded in function, not in string table)

    - CSWCCreature::UnloadModel @ (K1: 0x0060c8e0, TSL: N/A - likely inlined or different implementation)
      * Creature model unloader (42 bytes, 1 callee)
        * Signature: void __thiscall CSWCCreature::UnloadModel(CSWCCreature *this)
        * Logic (from decompilation):
          * Gets (this->object).anim_base
          * If anim_base is non-NULL:
            * Calls anim_base->vtable[30]() (unload/cleanup method, vtable offset 0x78)
            * Calls anim_base->vtable[0](1) (destructor with delete flag)
            * Sets (this->object).anim_base to NULL
          * Returns
        * Callees:
          * anim_base->vtable[30]() (unload method, virtual call)
          * anim_base->vtable[0](1) (destructor, virtual call)
        * VTable Entry: Located in CSWCCreature class structure
      * TSL: Function likely inlined or has different implementation pattern

    Resource Management Functions:
    ------------------------------
    - CResMDL::CResMDL - K1: 0x005cea50, TSL: N/A - likely inlined or different implementation
      * MDL resource constructor (36 bytes, 1 callee)
        * Signature: void __thiscall CResMDL::CResMDL(CResMDL *this)
        * Logic (from decompilation analysis via cross-references):
          * Initializes vtable pointer to CResMDL_vtable
          * Calls CRes::CRes() base class constructor
          * Sets field1_0x28 = 0 (resource state flag)
          * Sets size = 0 (resource data size)
          * Sets data = NULL (resource data pointer)
        * Callees:
          * CRes::CRes() (base class constructor)
        * Callers:
          * LoadMesh() @ 0x0059680c (called when loading mesh resources)
          * SetResRef() @ 0x00710270 (called when setting resource reference)
        * VTable: CResMDL_vtable located in data section
      * TSL: Constructor likely inlined in resource allocation code or has different implementation pattern

    - CResMDL::~CResMDL (destructor) - K1: 0x005cea80, TSL: 0x00435200
      * MDL resource destructor (11 bytes, 1 callee)
        * Signature: void __thiscall CResMDL::~CResMDL(CResMDL *this)
        * Logic (from decompilation):
          * Sets vtable to CResMDL_vtable (restores vtable for proper destruction)
          * Calls CRes::~CRes() base class destructor
          * Returns
        * Callees:
          * CRes::~CRes() (base class destructor)
        * VTable: CResMDL_vtable @ 0x0074c404

    - CResMDL::~CResMDL (deleting destructor) - K1: 0x005cea90, TSL: 0x00447740
      * MDL resource deleting destructor (27 bytes, 1 callee)
        * Signature: int ** __thiscall CResMDL::~CResMDL(CResMDL *this, byte param_1)
        * Logic (from decompilation):
          * Calls ~CResMDL(this) (non-deleting destructor)
          * Checks if param_1 & 1 (delete flag is set)
          * If flag set, calls _free(this) to deallocate memory
          * Returns this pointer cast to int**
        * Callees:
          * ~CResMDL() @ 0x005cea80 (non-deleting destructor)
          * _free() (memory deallocation, conditional)
        * VTable Entry: CResMDL_vtable + offset for deleting destructor

    Error Messages:
    --------------
    - "CSWCCreature::LoadModel(): Failed to load creature model '%s'." - K1: 0x0074f85c, TSL: 0x007c82fc
      * Referenced in CSWCCreature::LoadModel() @ 0x0061b5cf
        * Used in sprintf() call when anim_base->vtable[3] returns 0
        * param_1 is resource name from CResRef::GetResRefStr()
      * TSL: Referenced in CSWCCreature::LoadModel error handler @ 0x0066a0f0
        * Used in sprintf() @ (K1: 0x006fadb0, TSL: 0x0076dac2) (sprintf equivalent/wrapper)
        * Resource name obtained via CResRef::CopyToString() @ (K1: 0x00405f70, TSL: 0x00406050)

    - "Model %s nor the default model %s could be loaded." - K1: 0x00751c70, TSL: 0x007cad14
      * Generic model loading failure message
      * Format: Takes two model names (requested and default fallback)

    String References (File Extensions):
    -----------------------------------
    - ".mdl" extension - K1: 0x00740ca8, TSL: 0x007b8d28
      * Referenced in 3 locations:
        * Input::Read() @ (K1: 0x004a13ba, TSL: 0x004ce8c0) - file extension check (call site within Input::Read)
        * Input::Read() @ (K1: 0x004a1465, TSL: 0x004ce8c0) - file extension check (call site within Input::Read)
        * LoadAddInAnimations() @ (K1: 0x004408ce, TSL: 0x004538d0) - appends to model name for file opening
      * Usage: Used to construct file paths when loading MDL files
      * Verified via REVA MCP: Found in TSL at 0x007b8d28, referenced in LoadAddInAnimations() decompilation

References:
----------
    Based on swkotor.exe (K1) and swkotor2.exe (TSL) MDL/MDX I/O implementation.
    All addresses verified via REVA MCP tools through string cross-references,
    call chain analysis, and decompilation.
"""

from __future__ import annotations

import math
import os

from typing import TYPE_CHECKING, ClassVar, cast

from pykotor.common.misc import Color, Game
from pykotor.common.stream import BinaryReader, BinaryWriter
from pykotor.resource.formats.mdl.mdl_data import (
    MDL,
    MDLAABBNode,
    MDLAnimation,
    MDLBoneVertex,
    MDLConstraint,
    MDLController,
    MDLControllerRow,
    MDLEvent,
    MDLFace,
    MDLMesh,
    MDLNode,
    MDLNodeFlags,
    MDLSkin,
    _mdl_recompute_mesh_face_payload,
)
from pykotor.resource.formats.mdl.mdl_types import MDLClassification, MDLControllerType, MDLNodeType
from utility.common.geometry import Vector2, Vector3, Vector4

# Debug logging: Enable via environment variable PYKOTOR_DEBUG_MDL=1
_DEBUG_MDL = os.environ.get("PYKOTOR_DEBUG_MDL", "").strip() in ("1", "true", "True", "TRUE", "yes", "Yes", "YES")

if TYPE_CHECKING:
    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

    from pykotor.common.stream import BinaryWriterBytearray
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


# Fast-loading flags for render-only mode
MDL_FAST_LOAD_FLAGS = {
    "skip_controllers": True,
    "skip_animations": True,
    "minimal_mesh_data": True,
}


class _ModelHeader:
    SIZE: ClassVar[Literal[0xC4]] = 196

    def __init__(self):
        self.geometry: _GeometryHeader = _GeometryHeader()
        # Reference: K1 swkotor.exe:0x004a1030, TSL swkotor2.exe:0x004ce550 (InputBinary::Reset function parses Model structure)
        # Binary file layout after geometry header (0x50 bytes):
        self.model_type: int = 0  # Model classification type (uint8 at binary offset 0x50)
        self.subclassification: int = 0  # Model subclassification value (uint8 at binary offset 0x51)
        # Reference: K1 swkotor.exe:0x004a1030, TSL swkotor2.exe:0x004ce550 (InputBinary::Reset function)
        # Field at 0x52 is alignment padding byte - not directly accessed in Reset() parsing function
        # Used for 4-byte alignment between subclassification (uint8) and child_model_count (uint32 starting at 0x54)
        self.padding0: int = 0  # Alignment padding byte (uint8 at binary offset 0x52) - ensures proper alignment for subsequent uint32 fields
        self.fog: int = 0  # Fog flag/parameter (uint8 at binary offset 0x53)
        self.child_model_count: int = 0  # Number of child models (uint32 at binary offset 0x54)
        self.offset_to_animations: int = 0  # Offset to animation data array (uint32)
        self.animation_count: int = 0  # Number of animations (uint32)
        self.animation_count2: int = 0  # Animation count duplicate/alternate (uint32)
        # Reference: K1 swkotor.exe:0x004a1030, TSL swkotor2.exe:0x004ce550 (Reset function accesses param_1 + 100 = 0x64)
        self.parent_model_pointer: int = 0  # Pointer to parent model (context-dependent, uint32 at binary offset 0x64)
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.anim_scale: float = 0.0
        self.supermodel: str = ""
        self.offset_to_super_root: int = 0  # Offset to supermodel root node (uint32)
        # Reference: K1 swkotor.exe:0x004a1030, TSL swkotor2.exe:0x004ce550 (InputBinary::Reset function accesses param_1 + 0xa8 for offset_to_super_root and param_1 + 0xac for mdx_data_buffer_offset)
        # Used by Reset() function as offset into MDX data buffer: reads value at param_1 + 0xac, then accesses param_2 + value to copy MDX data
        # Line 27: iVar3 = *(int *)(param_1 + 0xac); reads the offset
        # Line 32: pbVar8 = param_2 + iVar3; uses it to locate data within MDX buffer
        self.mdx_data_buffer_offset: int = 0  # Offset into MDX data buffer for data copying operations (uint32 at binary offset 0xac). Used by Reset() function to locate data within MDX buffer.
        self.mdx_size: int = 0  # MDX geometry data size in bytes (uint32)
        self.mdx_offset: int = 0
        self.offset_to_name_offsets: int = 0
        self.name_offsets_count: int = 0
        self.name_offsets_count2: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _ModelHeader:
        self.geometry = _GeometryHeader().read(reader)
        self.model_type = reader.read_uint8()  # Model classification type (uint8 at binary offset 0x50)
        self.subclassification = reader.read_uint8()  # Model subclassification value (uint8 at binary offset 0x51)
        # Reference: K1 swkotor.exe:0x004a1030, TSL swkotor2.exe:0x004ce550 (InputBinary::Reset function)
        # Alignment padding byte - not directly accessed in Reset() parsing function
        # Used for 4-byte alignment between subclassification (uint8) and child_model_count (uint32 starting at 0x54)
        self.padding0 = reader.read_uint8()  # Alignment padding byte (uint8 at binary offset 0x52) - ensures proper alignment for subsequent uint32 fields
        self.fog = reader.read_uint8()  # Fog flag/parameter (uint8 at binary offset 0x53)
        self.child_model_count = reader.read_uint32()  # Number of child models (uint32 at binary offset 0x54)
        self.offset_to_animations = reader.read_uint32()
        animation_count_raw = reader.read_uint32()
        if animation_count_raw > 0x7FFFFFFF:
            animation_count_raw = 0x7FFFFFFF
        self.animation_count = animation_count_raw
        animation_count2_raw = reader.read_uint32()
        if animation_count2_raw > 0x7FFFFFFF:
            animation_count2_raw = 0x7FFFFFFF
        self.animation_count2 = animation_count2_raw
        self.parent_model_pointer = reader.read_uint32()  # Pointer to parent model (context-dependent, uint32 at binary offset 0x64)
        self.bounding_box_min = reader.read_vector3()
        self.bounding_box_max = reader.read_vector3()
        self.radius = reader.read_single()
        self.anim_scale = reader.read_single()
        self.supermodel = reader.read_terminated_string("\0", 32)
        self.offset_to_super_root = reader.read_uint32()  # Offset to supermodel root node (uint32)
        # Reference: K1 swkotor.exe:0x004a1030, TSL swkotor2.exe:0x004ce550 (Reset function accesses param_1 + 0xa8)
        # Field name preserved from cchargin mdl_info.html documentation
        # Second field in the Names array header structure (at binary offset 0xac in file, 0x5C in model header)
        # Used by Reset() function as offset into MDX data buffer: reads value at param_1 + 0xac, then accesses param_2 + value to copy MDX data
        self.mdx_data_buffer_offset = (
            reader.read_uint32()
        )  # Offset into MDX data buffer for data copying operations (uint32 at binary offset 0xac). Used by Reset() function to locate data within MDX buffer.
        self.mdx_size = reader.read_uint32()
        self.mdx_offset = reader.read_uint32()
        self.offset_to_name_offsets = reader.read_uint32()
        name_offsets_count_raw = reader.read_uint32()
        if name_offsets_count_raw > 0x7FFFFFFF:
            name_offsets_count_raw = 0x7FFFFFFF
        self.name_offsets_count = name_offsets_count_raw
        name_offsets_count2_raw = reader.read_uint32()
        if name_offsets_count2_raw > 0x7FFFFFFF:
            name_offsets_count2_raw = 0x7FFFFFFF
        self.name_offsets_count2 = name_offsets_count2_raw
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        self.geometry.write(writer)
        writer.write_uint8(self.model_type)
        writer.write_uint8(self.subclassification)
        writer.write_uint8(self.padding0)
        writer.write_uint8(self.fog)
        writer.write_uint32(self.child_model_count)
        writer.write_uint32(self.offset_to_animations)
        animation_count_clamped = min(self.animation_count, 0x7FFFFFFF)
        writer.write_uint32(animation_count_clamped)
        animation_count2_clamped = min(self.animation_count2, 0x7FFFFFFF)
        writer.write_uint32(animation_count2_clamped)
        writer.write_uint32(self.parent_model_pointer)
        writer.write_vector3(self.bounding_box_min)
        writer.write_vector3(self.bounding_box_max)
        writer.write_single(self.radius)
        writer.write_single(self.anim_scale)
        writer.write_string(self.supermodel, string_length=32, encoding="ascii", errors="ignore")
        writer.write_uint32(self.offset_to_super_root)
        # Second field in the Names array header structure (at binary offset 0xac in file, 0x5C in model header)
        # Used by Reset() function as offset into MDX data buffer: reads value at param_1 + 0xac, then accesses param_2 + value to copy MDX data
        writer.write_uint32(self.mdx_data_buffer_offset)
        writer.write_uint32(self.mdx_size)
        writer.write_uint32(self.mdx_offset)
        writer.write_uint32(self.offset_to_name_offsets)
        name_offsets_count_clamped = min(self.name_offsets_count, 0x7FFFFFFF)
        writer.write_uint32(name_offsets_count_clamped)
        name_offsets_count2_clamped = min(self.name_offsets_count2, 0x7FFFFFFF)
        writer.write_uint32(name_offsets_count2_clamped)


class _GeometryHeader:
    SIZE: ClassVar[Literal[0x50]] = 80

    K1_FUNCTION_POINTER0: ClassVar[Literal[0x413670]] = 4273776
    K2_FUNCTION_POINTER0: ClassVar[Literal[0x416310]] = 4285200
    K1_ANIM_FUNCTION_POINTER0: ClassVar[Literal[0x4134F0]] = 4273392
    K2_ANIM_FUNCTION_POINTER0: ClassVar[Literal[0x416190]] = 4284816

    K1_FUNCTION_POINTER1: ClassVar[Literal[0x405520]] = 4216096
    K2_FUNCTION_POINTER1: ClassVar[Literal[0x405600]] = 4216320
    K1_ANIM_FUNCTION_POINTER1: ClassVar[Literal[0x43ECE0]] = 4451552
    K2_ANIM_FUNCTION_POINTER1: ClassVar[Literal[0x4503B0]] = 4522928

    GEOM_TYPE_ROOT: ClassVar[Literal[2]] = 2
    GEOM_TYPE_ANIM: ClassVar[Literal[5]] = 5

    # MDLOps uses these specific padding bytes when compiling ASCII to binary.
    # Using the same values ensures byte-level parity with MDLOps output.
    MDLOPS_PADDING: ClassVar[Literal[b"\x31\x96\xbd"]] = b"\x31\x96\xbd"

    def __init__(self):
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.model_name: str = ""
        self.root_node_offset: int = 0
        self.node_count: int = 0
        self.unknown0: bytes = b"\x00" * 28
        self.geometry_type: int = 0
        # For writing, always use MDLOps padding bytes for parity
        self.padding: bytes = self.MDLOPS_PADDING

    def read(
        self,
        reader: BinaryReader,
    ) -> _GeometryHeader:
        self.function_pointer0 = reader.read_uint32()
        self.function_pointer1 = reader.read_uint32()
        self.model_name = reader.read_terminated_string("\0", 32)
        self.root_node_offset = reader.read_uint32()
        node_count_raw = reader.read_uint32()
        if node_count_raw > 0x7FFFFFFF:
            node_count_raw = 0x7FFFFFFF
        self.node_count = node_count_raw
        self.unknown0 = reader.read_bytes(28)
        self.geometry_type = reader.read_uint8()
        self.padding = reader.read_bytes(3)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.function_pointer0)
        writer.write_uint32(self.function_pointer1)
        writer.write_string(self.model_name, string_length=32, encoding="ascii")
        writer.write_uint32(self.root_node_offset)
        node_count_clamped = min(self.node_count, 0x7FFFFFFF)
        writer.write_uint32(node_count_clamped)
        writer.write_bytes(self.unknown0)
        writer.write_uint8(self.geometry_type)
        # Always write MDLOps padding bytes for parity
        # writer.write_bytes(self.padding)
        writer.write_bytes(self.MDLOPS_PADDING)


class _AnimationHeader:
    SIZE: ClassVar[Literal[0x88]] = _GeometryHeader.SIZE + 56

    def __init__(self):
        self.geometry: _GeometryHeader = _GeometryHeader()
        self.duration: float = 0.0
        self.transition: float = 0.0
        self.root: str = ""
        self.offset_to_events: int = 0
        self.event_count: int = 0
        self.event_count2: int = 0
        self.unknown0: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _AnimationHeader:
        self.geometry = _GeometryHeader().read(reader)
        self.duration = reader.read_single()
        self.transition = reader.read_single()
        self.root = reader.read_terminated_string("\0", 32)
        self.offset_to_events = reader.read_uint32()
        event_count_raw = reader.read_uint32()
        if event_count_raw > 0x7FFFFFFF:
            event_count_raw = 0x7FFFFFFF
        self.event_count = event_count_raw
        event_count2_raw = reader.read_uint32()
        if event_count2_raw > 0x7FFFFFFF:
            event_count2_raw = 0x7FFFFFFF
        self.event_count2 = event_count2_raw
        self.unknown0 = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        self.geometry.write(writer)
        writer.write_single(self.duration)
        writer.write_single(self.transition)
        writer.write_string(self.root, string_length=32, encoding="ascii")
        writer.write_uint32(self.offset_to_events)
        event_count_clamped = min(self.event_count, 0x7FFFFFFF)
        writer.write_uint32(event_count_clamped)
        event_count2_clamped = min(self.event_count2, 0x7FFFFFFF)
        writer.write_uint32(event_count2_clamped)
        writer.write_uint32(self.unknown0)


class _Animation:
    def __init__(self):
        self.header: _AnimationHeader = _AnimationHeader()
        self.events: list[_EventStructure] = []
        self.w_nodes: list[_Node] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _Animation:
        self.header = _AnimationHeader().read(reader)

        # read events
        return self

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ):
        self.header.write(writer)
        for event in self.events:
            event.write(writer)
        for node in self.w_nodes:
            node.write(writer, game)

    def events_offset(self) -> int:
        # Always after header
        return _AnimationHeader.SIZE

    def events_size(self) -> int:
        return _EventStructure.SIZE * len(self.events)

    def nodes_offset(self) -> int:
        """Returns offset of the first node relative to the start of the animation data."""
        # Always after events
        return self.events_offset() + self.events_size()

    def nodes_size(self):
        return sum(node.calc_size(Game.K1) for node in self.w_nodes)

    def size(self) -> int:
        return self.nodes_offset() + self.nodes_size()


class _EventStructure:
    SIZE: ClassVar[Literal[0x24]] = 36

    def __init__(self):
        self.activation_time: float = 0.0
        self.event_name: str = ""

    def read(
        self,
        reader: BinaryReader,
    ) -> _EventStructure:
        self.activation_time = reader.read_single()
        self.event_name = reader.read_terminated_string("\0", 32)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_single(self.activation_time)
        writer.write_string(self.event_name, string_length=32, encoding="ascii")


class _Controller:
    SIZE: ClassVar[Literal[0x10]] = 16

    def __init__(self):
        self.type_id: int = 0
        self.unknown0: int = 0xFFFF
        self.row_count: int = 0
        self.key_offset: int = 0
        self.data_offset: int = 0
        self.column_count: int = 0
        self.unknown1: bytes = b"\x00" * 3

    def read(
        self,
        reader: BinaryReader,
    ) -> _Controller:
        self.type_id = reader.read_uint32()
        self.unknown0 = reader.read_uint16()
        self.row_count = reader.read_uint16()
        self.key_offset = reader.read_uint16()
        self.data_offset = reader.read_uint16()
        self.column_count = reader.read_uint8()
        self.unknown1 = reader.read_bytes(3)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.type_id)
        writer.write_uint16(self.unknown0)
        writer.write_uint16(self.row_count)
        writer.write_uint16(self.key_offset)
        writer.write_uint16(self.data_offset)
        writer.write_uint8(self.column_count)
        writer.write_bytes(self.unknown1)


class _Node:
    SIZE: ClassVar[Literal[0x50]] = 80

    _dangly_constraints: list[MDLConstraint] | None = None
    _aabb_nodes: list[MDLAABBNode] | None = None
    _aabb_tree_size: int | None = None

    """
    Ordering:
        # Node Header
        # Trimesh Header
        # ...
        # Face indices count array
        # Face indices offset array
        # Faces
        # Vertices
        # Inverted counter array
        # Children
        # Controllers
        # Controller Data
    """

    def __init__(self):
        self.header: _NodeHeader | None = _NodeHeader()
        self.trimesh: _TrimeshHeader | None = None
        self.skin: _SkinmeshHeader | None = None
        self.light: _LightHeader | None = None
        self.emitter: _EmitterHeader | None = None
        self.reference: _ReferenceHeader | None = None
        self.dangly: _DanglymeshHeader | None = None
        self.children_offsets: list[int] = []

        self.w_children: list[_Node] = []
        self.w_controllers: list[_Controller] = []
        self.w_controller_data: list[float] = []

    def read(
        self,
        reader: BinaryReader,
        game: Game,
    ) -> _Node:
        self.header = _NodeHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.MESH:
            self.trimesh = _TrimeshHeader().read(reader, game)

        if self.header.type_id & MDLNodeFlags.SKIN:
            self.skin = _SkinmeshHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.LIGHT:
            self.light = _LightHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.EMITTER:
            self.emitter = _EmitterHeader().read(reader)

        if self.header.type_id & MDLNodeFlags.REFERENCE:
            self.reference = _ReferenceHeader().read(reader)

        # Danglymesh sub-sub-header follows trimesh header (28 bytes: l[3]f[3]l)
        if (
            self.header.type_id & MDLNodeFlags.DANGLY
            and self.trimesh is not None
        ):
            self.dangly = _DanglymeshHeader().read(reader)

        # AABB nodes have an extra 4-byte field (aabbloc) after the trimesh header
        # This extends the header from 332/340 bytes to 336/344 bytes
        if (
            self.header.type_id & MDLNodeFlags.AABB
            and self.trimesh is not None
        ):
            # Read the AABB tree offset (aabbloc)
            # MDLOps stores this as (absolute_offset - 12), but since BinaryReader has
            # set_offset(+12) applied, the raw value can be used directly without adjustment.
            aabb_offset_raw: int = reader.read_int32()
            # Do NOT add 12 here - the reader's offset is already adjusted
            self.trimesh.offset_to_aabb = aabb_offset_raw if aabb_offset_raw > 0 else 0

        if self.trimesh is not None:
            self.trimesh.read_extra(reader)
        if self.skin is not None:
            self.skin.read_extra(reader)

        # Read the children offsets array.
        #
        # IMPORTANT: When `children_count == 0`, MDLOps commonly leaves `childrenloc` as 0.
        # Seeking to 0 here would desync the caller's expectations and can cascade into bogus
        # controller reads. Only seek/read when there are actual children.
        if self.header.children_count == 0:
            self.children_offsets = []
            return self

        # MDLOps stores offsets as (absolute_offset - 12), but since BinaryReader has
        # set_offset(+12) applied, the raw value can be used directly without adjustment.
        child_loc: int = self.header.offset_to_children
        if (
            child_loc in (0, 0xFFFFFFFF)
            or child_loc >= reader.size()
            or self.header.children_count > 0x7FFFFFFF  # Prevent negative values when interpreted as signed
            or (self.header.children_count * 4) + child_loc > reader.size()
        ):
            self.header.children_count = 0
            self.header.children_count2 = 0
            self.children_offsets = []
            return self

        try:
            reader.seek(child_loc)
            self.children_offsets = [reader.read_uint32() for _ in range(self.header.children_count)]
        except Exception:
            # If reading fails, set to empty to prevent corruption.
            self.header.children_count = 0
            self.header.children_count2 = 0
            self.children_offsets = []
        return self

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ):
        assert self.header is not None, "Node header is required"
        self.header.write(writer)

        if self.trimesh is not None:
            self.trimesh.write(writer, game)

        if self.skin is not None:
            self.skin.write(writer)

        if self.light is not None:
            self.light.write(writer)

        if self.emitter is not None:
            self.emitter.write(writer)

        if self.reference is not None:
            self.reference.write(writer)

        # Danglymesh sub-sub-header follows trimesh header
        if self.dangly is not None:
            self.dangly.write(writer)

        # AABB nodes have an extra 4-byte field (aabbloc) after the trimesh header
        # This extends the header from 332/340 bytes to 336/344 bytes
        #
        # The AABB tree is written IMMEDIATELY after the aabbloc field, not after all node data
        if (
            self.header.type_id & MDLNodeFlags.AABB
            and self.trimesh is not None
        ):
            # Write aabbloc field: the offset to AABB tree (position + 4 = right after this field)
            # MDLOps writes: pack("L", ((tell(BMDLOUT) - 12) + 4))
            #
            # This matches MDLOps exactly: (current_position - 12) + 4
            aabb_tree_pos = (writer.position() - 12) + 4
            writer.write_int32(aabb_tree_pos)
            # Write AABB tree immediately after aabbloc field
            self._write_aabb_extra(writer)

        if self.trimesh is not None:
            self._write_trimesh_data(writer)
        if self.dangly is not None:
            self._write_dangly_extra(writer)
        if self.skin is not None:
            self._write_skin_extra(writer)
        for child_offset in self.children_offsets:
            writer.write_uint32(child_offset)

        for controller in self.w_controllers:
            controller.write(writer)

        # Write controller data - compressed quaternions need special handling
        # Compressed quaternions are stored as uint32s, not floats
        # We need to iterate through controllers to identify which data entries are compressed quaternions
        data_idx = 0
        for controller in self.w_controllers:
            # Write time keys (floats)
            for _ in range(controller.row_count):
                if data_idx < len(self.w_controller_data):
                    writer.write_single(self.w_controller_data[data_idx])
                    data_idx += 1
            # Write data values
            # Check if this is a compressed quaternion controller (type 20, column_count 2)
            is_compressed_quat = controller.type_id == int(MDLControllerType.ORIENTATION) and controller.column_count == 2
            if is_compressed_quat:
                # Compressed quaternions: write as uint32s (1 per row, reinterpreted from float)
                import struct as struct_module

                for _ in range(controller.row_count):
                    if data_idx < len(self.w_controller_data):
                        # Reinterpret float as uint32 (same bits, NOT numeric conversion)
                        float_val = self.w_controller_data[data_idx]
                        compressed_uint32 = struct_module.unpack("<I", struct_module.pack("<f", float_val))[0]
                        writer.write_uint32(compressed_uint32)
                        data_idx += 1
            else:
                # Regular controller data: write as floats
                # Calculate number of floats per row from column_count
                # Bezier flag is encoded in bit 4 (0x10) of column_count
                is_bezier = bool(controller.column_count & 0x10)
                floats_per_row = controller.column_count & ~0x10  # Strip bezier flag if present
                if is_bezier:
                    # Bezier controllers: 3 floats per column
                    floats_per_row = floats_per_row * 3
                for _ in range(controller.row_count):
                    for _ in range(floats_per_row):
                        if data_idx < len(self.w_controller_data):
                            writer.write_single(self.w_controller_data[data_idx])
                            data_idx += 1

        if len(self.children_offsets) != self.header.children_count:
            msg = f"Number of child offsets in array does not match header count in {self.header.name_id} ({len(self.children_offsets)} vs {self.header.children_count})."
            raise ValueError(msg)

    def _write_trimesh_data(
        self,
        writer: BinaryWriter,
    ):
        """Write trimesh data in MDLOps order.
        MDLOps writes mesh data in this order:
        1. faces (7903-7907)
        2. indices_counts / pntr_to_vert_num (7909-7914)
        3. vertices / vertcoords (7917-7921)
        4. indices_offsets / pntr_to_vert_loc (7923-7928)
        5. counters / array3 (7930-7934)
        6. vertindexes (7936-7940)
        """
        assert self.trimesh is not None

        # 1. Write faces (full _Face structs)
        for face in self.trimesh.faces:
            face.write(writer)

        # 2. Write indices counts array (pntr_to_vert_num)
        for count in self.trimesh.indices_counts:
            writer.write_uint32(count)

        # 3. Write vertices (Vector3 array / vertcoords)
        for vertex in self.trimesh.vertices:
            writer.write_vector3(vertex)

        # 4. Write indices offsets array (pntr_to_vert_loc)
        for offset in self.trimesh.indices_offsets:
            writer.write_uint32(offset)

        # 5. Write inverted counters array (array3)
        for counter in self.trimesh.inverted_counters:
            writer.write_uint32(counter)

        # 6. Write vertex indices array (vertindexes)
        # Format: 3 int16s per face (vertex1, vertex2, vertex3)
        for face in self.trimesh.faces:
            writer.write_int16(face.vertex1)
            writer.write_int16(face.vertex2)
            writer.write_int16(face.vertex3)

    def dangly_extra_size(self) -> int:
        """Size of dangly constraints array (1 float per constraint = 4 bytes each)."""
        if not self.dangly:
            return 0
        if self._dangly_constraints is None:
            return 0
        return len(self._dangly_constraints) * 4

    def _write_aabb_extra(
        self,
        writer: BinaryWriter,
    ) -> None:
        """Write AABB tree recursively, matching MDLOps depth-first traversal.
        Format: Each node is 40 bytes: 6 floats (bbox) + 4 int32s (child offsets + face_index + unknown)
        """
        if self._aabb_nodes is None:
            return
        aabb_nodes: list[MDLAABBNode] = self._aabb_nodes
        if len(aabb_nodes) == 0:
            return

        tree_start = writer.position()
        node_index = [0]  # Mutable counter for tracking which node we're writing

        def _write_aabb_recursive(
            writer: BinaryWriter,
            start_pos: int,
        ) -> int:
            """Recursively write AABB node and return last written position.

            Args:
                writer: BinaryWriter instance
                start_pos: Position to write this node at

            Returns:
                Last written position (end of subtree rooted at this node)
            """
            if node_index[0] >= len(aabb_nodes):
                return start_pos

            idx = node_index[0]
            node = aabb_nodes[idx]

            # Write bbox (6 floats = 24 bytes)
            writer.seek(start_pos)
            writer.write_vector3(node.bbox_min)
            writer.write_vector3(node.bbox_max)

            if node.face_index != -1:
                # Leaf node: write (0, 0, face_index, 0)
                #
                writer.write_int32(0)
                writer.write_int32(0)
                writer.write_int32(node.face_index)
                writer.write_int32(0)  # MDLOps always writes 0, not node.unknown
                node_index[0] += 1
                return start_pos + 40
            else:
                # Branch node: write children first, then fix child pointers
                # Left child is immediately after this node
                left_child_pos = start_pos + 40
                node_index[0] += 1
                right_child_pos = _write_aabb_recursive(writer, left_child_pos)
                last_pos = _write_aabb_recursive(writer, right_child_pos)

                # Seek back to write child pointers (at offset 24 from start_pos)
                # Format: (left_offset - 12, right_offset - 12, -1, 0)
                #
                writer.seek(start_pos + 24)
                writer.write_int32(left_child_pos - 12)
                writer.write_int32(right_child_pos - 12)
                writer.write_int32(-1)
                writer.write_int32(0)  # MDLOps always writes 0, not node.unknown

                return last_pos

        # Write recursively starting from tree_start
        _write_aabb_recursive(writer, tree_start)

        # Seek to end of AABB tree (calculated as tree_start + count * 40)
        final_pos = tree_start + len(aabb_nodes) * 40
        writer.seek(final_pos)

    def _write_dangly_extra(
        self,
        writer: BinaryWriter,
    ) -> None:
        """Write danglymesh constraints array after vertices."""
        assert self.dangly is not None
        # Constraints are written as floats (4 bytes each, one float per vertex)
        # MDLOps writes constraints after the dangly sub-sub-header
        constraints = self._dangly_constraints or []
        for constraint in constraints:
            # Constraints are stored as single float values
            # Extract from constraint.type if it was stored there, otherwise use 0.0
            if constraint.type != 0:
                constraint_value = float(constraint.type) / 1000000.0
            else:
                constraint_value = 0.0
            writer.write_single(constraint_value)

    def _write_skin_extra(
        self,
        writer: BinaryWriter,
    ) -> None:
        """Write variable-length skin blocks referenced by _SkinmeshHeader offsets."""
        assert self.skin is not None
        # Layout we write (immediately after trimesh vertex array):
        #   bonemap (float32 * count)
        #   qbones  (Vector4 * count)
        #   tbones  (Vector3 * count)
        #   unknown0 (float32 * count) [currently unused]
        if self.skin.bonemap_count and self.skin.bonemap:
            for v in self.skin.bonemap[: self.skin.bonemap_count]:
                writer.write_single(float(v))
        if self.skin.qbones_count and self.skin.qbones:
            for q in self.skin.qbones[: self.skin.qbones_count]:
                writer.write_vector4(q)
        if self.skin.tbones_count and self.skin.tbones:
            for t in self.skin.tbones[: self.skin.tbones_count]:
                writer.write_vector3(t)
        if self.skin.unknown0_count:
            # Not currently modeled; write zeros to match declared count.
            for _ in range(int(self.skin.unknown0_count)):
                writer.write_single(0.0)

    def all_headers_size(
        self,
        game: Game,
    ) -> int:
        size = _Node.SIZE
        if self.trimesh:
            size += _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE
        if self.skin:
            size += _SkinmeshHeader.SIZE
        if self.light:
            # Light header size: 15 uint32s (offsets/counts) + 1 float (flare_radius) + 7 uint32s (light properties) = 92 bytes
            size += 92
        if self.emitter:
            # MDLOps emitter_header template is 224 bytes:
            #   f[3]L[5]Z[32]*4 Z[16] L[2] S C Z[32] C L
            # See: ` `$structs{'subhead'}{'5k1'}` / `'5k2'`.
            size += 224
        if self.reference:
            # Reference header size: 32-byte string + 1 uint32 = 36 bytes
            size += 36
        return size

    def faces_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: faces come immediately after headers (and AABB if present)
        offset = self.all_headers_size(game)
        # AABB tree (if present) comes after aabbloc field but before faces
        if self.header and self.header.type_id & MDLNodeFlags.AABB and self.trimesh:
            offset += 4  # aabbloc field
            offset += self.aabb_extra_size()  # AABB tree
        return offset

    def indices_counts_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: pntr_to_vert_num (indices_counts) comes right after faces
        #
        offset = self.faces_offset(game)
        if self.trimesh:
            offset += self.trimesh.faces_size()
        return offset

    def vertices_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: vertcoords comes after indices_counts array
        #
        offset = self.indices_counts_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.indices_counts) * 4
        return offset

    def indices_offsets_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: pntr_to_vert_loc (indices_offsets) comes after vertices
        #
        offset = self.vertices_offset(game)
        if self.trimesh:
            offset += self.trimesh.vertices_size()
        return offset

    def inverted_counters_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: array3 (counters) comes after indices_offsets
        #
        offset = self.indices_offsets_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.indices_offsets) * 4
        return offset

    def vertex_indices_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: vertindexes comes after counters
        #
        offset = self.inverted_counters_offset(game)
        if self.trimesh:
            offset += len(self.trimesh.inverted_counters) * 4
        return offset

    def children_offsets_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: child node indexes comes after vertindexes
        #
        offset = self.vertex_indices_offset(game)
        if self.trimesh:
            offset += self.trimesh.vertex_indices_size()
        if self.dangly:
            offset += self.dangly_extra_size()
        if self.skin:
            offset += self.skin_extra_size()
        return offset

    def children_offsets_size(self) -> int:
        assert self.header is not None
        return 4 * self.header.children_count

    def controllers_offset(
        self,
        game: Game,
    ) -> int:
        # MDLOps layout: controllers comes after children_offsets
        #
        return self.children_offsets_offset(game) + self.children_offsets_size()

    def controllers_size(self) -> int:
        return _Controller.SIZE * len(self.w_controllers)

    def controller_data_offset(
        self,
        game: Game,
    ) -> int:
        return self.controllers_offset(game) + self.controllers_size()

    def controller_data_size(self) -> int:
        return len(self.w_controller_data) * 4

    def skin_extra_size(self) -> int:
        """Size of variable-length skin payload blocks written after vertices (MDL, not MDX)."""
        if not self.skin:
            return 0
        bonemap_bytes = int(self.skin.bonemap_count) * 4
        qbones_bytes = int(self.skin.qbones_count) * 16
        tbones_bytes = int(self.skin.tbones_count) * 12
        # unknown0 block currently not modeled; keep stable at 0 unless counts are set.
        unknown0_bytes = int(self.skin.unknown0_count) * 4
        return bonemap_bytes + qbones_bytes + tbones_bytes + unknown0_bytes

    def aabb_extra_size(self) -> int:
        """Size of AABB tree written immediately after aabbloc field (before trimesh data)."""
        if not (self.header and self.header.type_id & MDLNodeFlags.AABB and self.trimesh):
            return 0
        if self._aabb_nodes is None:
            return 0
        aabb_nodes: list[MDLAABBNode] = self._aabb_nodes
        # Each AABB node is 40 bytes: 6 floats (24 bytes) + 4 int32s (16 bytes)
        return len(aabb_nodes) * 40

    def calc_size(
        self,
        game: Game,
    ) -> int:
        return self.controller_data_offset(game) + self.controller_data_size()


class _NodeHeader:
    SIZE = 80

    def __init__(self):
        self.type_id: int = 1
        self.name_id: int = 0
        self.node_id: int = 0
        self.padding0: int = 0
        self.offset_to_root: int = 0
        self.offset_to_parent: int = 0
        self.position: Vector3 = Vector3.from_null()
        self.orientation: Vector4 = Vector4.from_null()
        self.offset_to_children: int = 0
        self.children_count: int = 0
        self.children_count2: int = 0
        self.offset_to_controllers: int = 0
        self.controller_count: int = 0
        self.controller_count2: int = 0
        self.offset_to_controller_data: int = 0
        self.controller_data_length: int = 0
        self.controller_data_length2: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _NodeHeader:
        # MDLOps nodeheader template: "SSSSllffffffflllllllll"
        # The 4 uint16 fields are ordered such that the 3rd short is the node index/id used as the primary key.
        # MDLOps does NOT store the node's name index here (it writes 0 for the 4th short) and derives names
        # from the model "partnames" array indexed by `node_id`.
        # See `
        #   - read: `node = unpack("x[ss]s", $buffer)` (3rd short)
        #   - write: `pack("SSSS", nodetype, supernode, $i, 0)` (4th short constant 0)
        self.type_id = reader.read_uint16()
        self.padding0 = reader.read_uint16()
        self.node_id = reader.read_uint16()
        self.name_id = reader.read_uint16()
        self.offset_to_root = reader.read_uint32()
        self.offset_to_parent = reader.read_uint32()
        self.position = reader.read_vector3()
        self.orientation.w = reader.read_single()
        self.orientation.x = reader.read_single()
        self.orientation.y = reader.read_single()
        self.orientation.z = reader.read_single()
        self.offset_to_children = reader.read_uint32()
        # Clamp children_count to prevent Perl from interpreting it as negative (values >= 2^31)
        # MDLOps reads this as a signed integer, so we must ensure it's < 2^31
        children_count_raw = reader.read_uint32()
        if children_count_raw > 0x7FFFFFFF:
            children_count_raw = 0x7FFFFFFF
        self.children_count = children_count_raw
        # Read children_count2 as a separate field to maintain correct file position
        # The binary format has two separate uint32 fields for children_count and children_count2
        children_count2_raw = reader.read_uint32()
        if children_count2_raw > 0x7FFFFFFF:
            children_count2_raw = 0x7FFFFFFF
        self.children_count2 = children_count2_raw
        self.offset_to_controllers = reader.read_uint32()
        self.controller_count = reader.read_uint32()
        self.controller_count2 = reader.read_uint32()
        self.offset_to_controller_data = reader.read_uint32()
        # Clamp controller_data_length to prevent Perl from interpreting it as negative (values >= 2^31)
        # MDLOps reads this as a signed integer, so we must ensure it's < 2^31
        controller_data_length_raw = reader.read_uint32()
        if controller_data_length_raw > 0x7FFFFFFF:
            controller_data_length_raw = 0x7FFFFFFF
        self.controller_data_length = controller_data_length_raw
        controller_data_length2_raw = reader.read_uint32()
        if controller_data_length2_raw > 0x7FFFFFFF:
            controller_data_length2_raw = 0x7FFFFFFF
        self.controller_data_length2 = controller_data_length2_raw
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint16(self.type_id)
        writer.write_uint16(self.padding0)
        writer.write_uint16(self.node_id)
        writer.write_uint16(self.name_id)
        writer.write_uint32(self.offset_to_root)
        writer.write_uint32(self.offset_to_parent)
        writer.write_vector3(self.position)
        writer.write_single(self.orientation.w)
        writer.write_single(self.orientation.x)
        writer.write_single(self.orientation.y)
        writer.write_single(self.orientation.z)
        writer.write_uint32(self.offset_to_children)
        # Clamp children_count to prevent Perl from interpreting it as negative (values >= 2^31)
        # MDLOps reads this as a signed integer in some contexts, so we must ensure it's < 2^31
        children_count_clamped = min(self.children_count, 0x7FFFFFFF)
        writer.write_uint32(children_count_clamped)
        children_count2_clamped = min(self.children_count2, 0x7FFFFFFF)
        writer.write_uint32(children_count2_clamped)
        writer.write_uint32(self.offset_to_controllers)
        # Clamp controller_count to prevent Perl from interpreting it as negative (values >= 2^31)
        controller_count_clamped = min(self.controller_count, 0x7FFFFFFF)
        writer.write_uint32(controller_count_clamped)
        controller_count2_clamped = min(self.controller_count2, 0x7FFFFFFF)
        writer.write_uint32(controller_count2_clamped)
        writer.write_uint32(self.offset_to_controller_data)
        # Clamp controller_data_length to prevent Perl from interpreting it as negative (values >= 2^31)
        controller_data_length_clamped = min(self.controller_data_length, 0x7FFFFFFF)
        writer.write_uint32(controller_data_length_clamped)
        controller_data_length2_clamped = min(self.controller_data_length2, 0x7FFFFFFF)
        writer.write_uint32(controller_data_length2_clamped)


class _MDXDataFlags:
    # NOTE: These constants mirror MDLOps' MDX_* bitfield definitions.
    # See `
    VERTEX: Literal[0x00000001] = 0x00000001
    TEX0: Literal[0x00000002] = 0x00000002
    TEX1: Literal[0x00000004] = 0x00000004
    TEX2: Literal[0x00000008] = 0x00000008
    TEX3: Literal[0x00000010] = 0x00000010
    NORMAL: Literal[0x00000020] = 0x00000020
    COLOR: Literal[0x00000040] = 0x00000040
    TANGENT_SPACE: Literal[0x00000080] = 0x00000080


class _TrimeshHeader:
    # MDLOps defines these as 332 (K1) and 340 (K2).
    # See ` `$structs{'subhead'}{'33k1'}` and `'33k2'`.
    K1_SIZE: Literal[0x14C] = 332
    K2_SIZE: Literal[0x154] = 340

    K1_FUNCTION_POINTER0: Literal[0x405750] = 4216656
    K2_FUNCTION_POINTER0: Literal[0x405830] = 4216880
    K1_SKIN_FUNCTION_POINTER0: Literal[0x405710] = 4216592
    K2_SKIN_FUNCTION_POINTER0: Literal[0x4057F0] = 4216816
    K1_DANGLY_FUNCTION_POINTER0: Literal[0x405740] = 4216640
    K2_DANGLY_FUNCTION_POINTER0: Literal[0x405820] = 4216864

    K1_FUNCTION_POINTER1: Literal[0x405760] = 4216672
    K2_FUNCTION_POINTER1: Literal[0x405840] = 4216896
    K1_SKIN_FUNCTION_POINTER1: Literal[0x405720] = 4216608
    K2_SKIN_FUNCTION_POINTER1: Literal[0x405800] = 4216832
    K1_DANGLY_FUNCTION_POINTER1: Literal[0x405730] = 4216624
    K2_DANGLY_FUNCTION_POINTER1: Literal[0x405810] = 4216848

    def __init__(self):
        self.function_pointer0: int = 0
        self.function_pointer1: int = 0
        self.offset_to_faces: int = 0
        self.faces_count: int = 0
        self.faces_count2: int = 0
        self.bounding_box_min: Vector3 = Vector3.from_null()
        self.bounding_box_max: Vector3 = Vector3.from_null()
        self.radius: float = 0.0
        self.average: Vector3 = Vector3.from_null()
        self.diffuse: Vector3 = Vector3.from_null()
        self.ambient: Vector3 = Vector3.from_null()
        self.transparency_hint: int = 0
        self.texture1: str = ""
        self.texture2: str = ""
        # Two 12-byte blocks in MDLOps template: `Z[12]Z[12]` (treated as opaque padding/unknown).
        self.unknown0: bytes = b"\x00" * 24
        self.offset_to_indices_counts: int = 0
        self.indices_counts_count: int = 0
        self.indices_counts_count2: int = 0
        self.offset_to_indices_offset: int = 0
        self.indices_offsets_count: int = 0
        self.indices_offsets_count2: int = 0
        self.offset_to_counters: int = 0
        self.counters_count: int = 0
        self.counters_count2: int = 0
        # Reference: wiki/MDL-MDX-File-Format.md:380 - "Unknown values" at offset 212 (0xD4)
        # Typically `{-1, -1, 0}` as three int32 values (12 bytes total)
        self.unknown1: bytes = b"\xff\xff\xff\xff" + b"\xff\xff\xff\xff" + b"\x00\x00\x00\x00"  # Unknown values (3 int32s, typically {-1, -1, 0})
        # Reference: wiki/MDL-MDX-File-Format.md:381 - "Saber Unknown data" at offset 224 (0xE0)
        # Data specific to lightsaber meshes (8 bytes)
        self.saber_unknowns: bytes = b"\x00" * 8  # Saber Unknown data (8 bytes, lightsaber-specific)
        # Reference: wiki/MDL-MDX-File-Format.md:382 - "Unknown" at offset 232 (0xE8)
        # Signed int32 in MDLOps template (single `l`).
        self.unknown2: int = 0  # Unknown field (int32 at binary offset 0xE8, purpose unknown)
        self.uv_direction: Vector2 = Vector2.from_null()
        self.uv_jitter: float = 0.0
        self.uv_speed: float = 0.0
        self.mdx_data_size: int = 0
        self.mdx_data_bitmap: int = 0
        # MDLOps template stores 13 signed int32 values here (`l[13]`).
        # The first 10 are well-understood MDX row offsets; the final 3 are unknown/unused.
        self.mdx_vertex_offset: int = 0
        self.mdx_normal_offset: int = 0
        self.mdx_color_offset: int = 0
        # NOTE: despite the historic naming in PyKotor, these correspond to MDLOps' tex0/tex1 offsets.
        self.mdx_texture1_offset: int = 0  # tex0
        self.mdx_texture2_offset: int = 0  # tex1
        self.mdx_uv3_offset: int = 0  # tex2 (unconfirmed)
        self.mdx_uv4_offset: int = 0  # tex3 (unconfirmed)
        self.mdx_tangent_offset: int = 0
        self.mdx_unknown_offset: int = 0
        self.mdx_unknown2_offset: int = 0
        self.mdx_unknown3_offset: int = 0
        self.vertex_count: int = 0
        self.texture_count: int = 1
        self.has_lightmap: int = 0
        self.rotate_texture: int = 0
        self.background: int = 0
        self.has_shadow: int = 0
        self.beaming: int = 0
        self.render: int = 0
        self.total_area: float = 0.0
        # Tail fields (after flags) differ between K1 and K2 in MDLOps template.
        # K1: `S f L[3]`
        # K2: `S L[2] f L[3]` but tail_short is replaced by CCssL (10 bytes) for dirt fields
        self.tail_short: int = 0  # unknown uint16 (index 72 in MDLOps' unpacked array, K1 only)
        # K2 dirt fields (replace tail_short, 10 bytes total: CCssL)
        self.dirt_enabled: bool = False  # uint8
        self.dirt_texture: int = 1  # int16
        self.dirt_worldspace: int = 1  # int16
        self.hologram_donotdraw: bool = False  # uint32
        self.k2_tail_long1: int = 0  # K2 only (after dirt fields)
        self.k2_tail_long2: int = 0  # K2 only (after dirt fields)
        self.tail_long0: int = 0  # unknown uint32 preceding MDX/vertex offsets (index 74/76)
        self.mdx_data_offset: int = 0
        self.vertices_offset: int = 0
        # AABB nodes have an extra 4-byte field (aabbloc) after the trimesh header
        # This is only present for nodes with AABB flag (NODE_AABB = 545)
        self.offset_to_aabb: int = 0

        self.faces: list[_Face] = []
        self.vertices: list[Vector3] = []
        self.indices_offsets: list[int] = []
        self.indices_counts: list[int] = []
        self.inverted_counters: list[int] = []

    def read(
        self,
        reader: BinaryReader,
        game: Game,
    ) -> _TrimeshHeader:
        start_pos = reader.position()
        self.function_pointer0 = reader.read_uint32()
        self.function_pointer1 = reader.read_uint32()
        self.offset_to_faces = reader.read_uint32()
        faces_count_raw = reader.read_uint32()
        if faces_count_raw > 0x7FFFFFFF:
            faces_count_raw = 0x7FFFFFFF
        self.faces_count = faces_count_raw
        faces_count2_raw = reader.read_uint32()
        if faces_count2_raw > 0x7FFFFFFF:
            faces_count2_raw = 0x7FFFFFFF
        self.faces_count2 = faces_count2_raw
        self.bounding_box_min = reader.read_vector3()
        self.bounding_box_max = reader.read_vector3()
        self.radius = reader.read_single()
        self.average = reader.read_vector3()
        self.diffuse = reader.read_vector3()
        self.ambient = reader.read_vector3()
        self.transparency_hint = reader.read_uint32()
        self.texture1 = reader.read_terminated_string("\0", 32)
        self.texture2 = reader.read_terminated_string("\0", 32)
        self.unknown0 = reader.read_bytes(24)
        self.offset_to_indices_counts = reader.read_uint32()
        indices_counts_count_raw = reader.read_uint32()
        if indices_counts_count_raw > 0x7FFFFFFF:
            indices_counts_count_raw = 0x7FFFFFFF
        self.indices_counts_count = indices_counts_count_raw
        indices_counts_count2_raw = reader.read_uint32()
        if indices_counts_count2_raw > 0x7FFFFFFF:
            indices_counts_count2_raw = 0x7FFFFFFF
        self.indices_counts_count2 = indices_counts_count2_raw
        self.offset_to_indices_offset = reader.read_uint32()
        indices_offsets_count_raw = reader.read_uint32()
        if indices_offsets_count_raw > 0x7FFFFFFF:
            indices_offsets_count_raw = 0x7FFFFFFF
        self.indices_offsets_count = indices_offsets_count_raw
        indices_offsets_count2_raw = reader.read_uint32()
        if indices_offsets_count2_raw > 0x7FFFFFFF:
            indices_offsets_count2_raw = 0x7FFFFFFF
        self.indices_offsets_count2 = indices_offsets_count2_raw
        self.offset_to_counters = reader.read_uint32()
        counters_count_raw = reader.read_uint32()
        if counters_count_raw > 0x7FFFFFFF:
            counters_count_raw = 0x7FFFFFFF
        self.counters_count = counters_count_raw
        counters_count2_raw = reader.read_uint32()
        if counters_count2_raw > 0x7FFFFFFF:
            counters_count2_raw = 0x7FFFFFFF
        self.counters_count2 = counters_count2_raw
        # Reference: wiki/MDL-MDX-File-Format.md:380 - "Unknown values" (3 int32s, typically {-1, -1, 0})
        self.unknown1 = reader.read_bytes(12)  # Unknown values (3 int32s, MDLOps `l[3]`, typically {-1, -1, 0})
        # Reference: wiki/MDL-MDX-File-Format.md:381 - "Saber Unknown data" (8 bytes, lightsaber-specific)
        self.saber_unknowns = reader.read_bytes(8)  # Saber Unknown data (8 bytes, MDLOps `C[8]`, lightsaber-specific)
        # Reference: wiki/MDL-MDX-File-Format.md:382 - "Unknown" field at offset 232 (0xE8)
        self.unknown2 = reader.read_int32()  # Unknown field (int32 at binary offset 0xE8, purpose unknown)
        self.uv_direction = reader.read_vector2()
        self.uv_jitter = reader.read_single()
        self.uv_speed = reader.read_single()

        # MDLOps `l[13]` (signed). Convert negative values to the sentinel 0xFFFFFFFF.
        def _read_i32_as_u32() -> int:
            v: int = reader.read_int32()
            return 0xFFFFFFFF if v < 0 else v

        self.mdx_data_size = _read_i32_as_u32()  # index 51
        self.mdx_data_bitmap = _read_i32_as_u32()  # index 52
        self.mdx_vertex_offset = _read_i32_as_u32()  # index 53
        self.mdx_normal_offset = _read_i32_as_u32()  # index 54
        self.mdx_color_offset = _read_i32_as_u32()  # index 55
        self.mdx_texture1_offset = _read_i32_as_u32()  # index 56 (tex0)
        self.mdx_texture2_offset = _read_i32_as_u32()  # index 57 (tex1)
        self.mdx_uv3_offset = _read_i32_as_u32()  # index 58 (tex2)
        self.mdx_uv4_offset = _read_i32_as_u32()  # index 59 (tex3)
        self.mdx_tangent_offset = _read_i32_as_u32()  # index 60 (tangent space)
        self.mdx_unknown_offset = _read_i32_as_u32()  # index 61 (unknown)
        self.mdx_unknown2_offset = _read_i32_as_u32()  # index 62 (unknown)
        self.mdx_unknown3_offset = _read_i32_as_u32()  # index 63 (unknown)
        self.vertex_count = reader.read_uint16()
        self.texture_count = reader.read_uint16()
        self.has_lightmap = reader.read_uint8()
        self.rotate_texture = reader.read_uint8()
        self.background = reader.read_uint8()
        self.has_shadow = reader.read_uint8()
        self.beaming = reader.read_uint8()
        self.render = reader.read_uint8()
        if game == Game.K2:
            # K2 dirt fields replace tail_short (2 bytes) with CCssL (10 bytes)
            #
            self.dirt_enabled = reader.read_uint8() != 0
            _padding = reader.read_uint8()  # padding byte
            self.dirt_texture = reader.read_int16()
            self.dirt_worldspace = reader.read_int16()
            # Read hologram_donotdraw as uint32, but only set to True if the value is explicitly 1
            # Some models may have uninitialized memory (non-zero garbage) that should be treated as 0
            hologram_value = reader.read_uint32()
            self.hologram_donotdraw = hologram_value == 1
            # Store in tail fields for compatibility (not used in K2)
            self.tail_short = 0
            self.k2_tail_long1 = reader.read_uint32()
            self.k2_tail_long2 = reader.read_uint32()
        else:
            self.tail_short = reader.read_uint16()
        self.total_area = reader.read_single()
        self.tail_long0 = reader.read_uint32()
        self.mdx_data_offset = reader.read_uint32()
        self.vertices_offset = reader.read_uint32()
        # Ensure we consumed exactly the MDLOps-defined header size.
        expected = _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE
        reader.seek(start_pos + expected)
        return self

    def read_extra(
        self,
        reader: BinaryReader,
    ):
        # NOTE: MDL offsets are stored relative to the start of the MDL data block.
        # MDLBinaryReader already compensates for the leading 12-byte wrapper via `BinaryReader.set_offset(+12)`.
        # Therefore, loc fields in the file can be used directly with this reader.
        def _loc(off: int) -> int:
            return off

        # Indices counts array
        if self.offset_to_indices_counts not in (0, 0xFFFFFFFF) and self.indices_counts_count > 0:
            counts_bytes = self.indices_counts_count * 4  # uint32 per count
            loc = _loc(self.offset_to_indices_counts)
            if loc <= reader.size() and (loc + counts_bytes) <= reader.size():
                reader.seek(loc)
                self.indices_counts = [reader.read_uint32() for _ in range(self.indices_counts_count)]

        # Indices offsets array
        if self.offset_to_indices_offset not in (0, 0xFFFFFFFF) and self.indices_offsets_count > 0:
            offsets_bytes = self.indices_offsets_count * 4  # uint32 per offset
            loc = _loc(self.offset_to_indices_offset)
            if loc <= reader.size() and (loc + offsets_bytes) <= reader.size():
                reader.seek(loc)
                self.indices_offsets = [reader.read_uint32() for _ in range(self.indices_offsets_count)]

        # Inverted counters (array3) - read from offset_to_counters when counters_count > 0
        if self.offset_to_counters not in (0, 0xFFFFFFFF) and self.counters_count > 0:
            counters_bytes = self.counters_count * 4  # uint32 per counter
            loc = _loc(self.offset_to_counters)
            if loc <= reader.size() and (loc + counters_bytes) <= reader.size():
                reader.seek(loc)
                self.inverted_counters = [reader.read_uint32() for _ in range(self.counters_count)]

        # Faces
        if self.offset_to_faces not in (0, 0xFFFFFFFF) and self.faces_count > 0:
            faces_bytes = self.faces_count * _Face.SIZE
            loc = _loc(self.offset_to_faces)
            if loc <= reader.size() and (loc + faces_bytes) <= reader.size():
                reader.seek(loc)
                self.faces = [_Face().read(reader) for _ in range(self.faces_count)]

        # CRITICAL: Validate vertex_count from faces BEFORE reading vertices
        # If faces reference vertex indices, vertex_count must be at least max_index + 1
        if self.faces:
            max_vertex_index = 0
            for face in self.faces:
                max_vertex_index = max(max_vertex_index, face.vertex1, face.vertex2, face.vertex3)
            required_vertex_count = max_vertex_index + 1
            if required_vertex_count > self.vertex_count:
                # Faces require more vertices than header says - use face-based count (authoritative)
                self.vertex_count = required_vertex_count

        # Vertices
        if self.vertices_offset not in (0, 0xFFFFFFFF) and self.vertex_count > 0:
            vertices_bytes = self.vertex_count * 12  # Vector3 of floats
            loc = _loc(self.vertices_offset)
            if loc <= reader.size() and (loc + vertices_bytes) <= reader.size():
                reader.seek(loc)
                self.vertices = [reader.read_vector3() for _ in range(self.vertex_count)]

    def write(
        self,
        writer: BinaryWriter,
        game: Game,
    ):
        start_pos = writer.position()
        writer.write_uint32(self.function_pointer0)
        writer.write_uint32(self.function_pointer1)
        writer.write_uint32(self.offset_to_faces)
        # Clamp faces_count to prevent Perl from interpreting it as negative (values >= 2^31)
        faces_count_clamped = min(self.faces_count, 0x7FFFFFFF)
        writer.write_uint32(faces_count_clamped)
        faces_count2_clamped = min(self.faces_count2, 0x7FFFFFFF)
        writer.write_uint32(faces_count2_clamped)
        writer.write_vector3(self.bounding_box_min)
        writer.write_vector3(self.bounding_box_max)
        writer.write_single(self.radius)
        writer.write_vector3(self.average)
        writer.write_vector3(self.diffuse)
        writer.write_vector3(self.ambient)
        writer.write_uint32(self.transparency_hint)
        writer.write_string(self.texture1, string_length=32, encoding="ascii")
        writer.write_string(self.texture2, string_length=32, encoding="ascii")
        writer.write_bytes(self.unknown0)
        writer.write_uint32(self.offset_to_indices_counts)
        # Clamp all counts to prevent Perl from interpreting them as negative (values >= 2^31)
        indices_counts_count_clamped = min(self.indices_counts_count, 0x7FFFFFFF)
        writer.write_uint32(indices_counts_count_clamped)
        indices_counts_count2_clamped = min(self.indices_counts_count2, 0x7FFFFFFF)
        writer.write_uint32(indices_counts_count2_clamped)
        writer.write_uint32(self.offset_to_indices_offset)
        indices_offsets_count_clamped = min(self.indices_offsets_count, 0x7FFFFFFF)
        writer.write_uint32(indices_offsets_count_clamped)
        indices_offsets_count2_clamped = min(self.indices_offsets_count2, 0x7FFFFFFF)
        writer.write_uint32(indices_offsets_count2_clamped)
        writer.write_uint32(self.offset_to_counters)
        counters_count_clamped = min(self.counters_count, 0x7FFFFFFF)
        writer.write_uint32(counters_count_clamped)
        counters_count2_clamped = min(self.counters_count2, 0x7FFFFFFF)
        writer.write_uint32(counters_count2_clamped)
        # Reference: wiki/MDL-MDX-File-Format.md:380-382 - Unknown values, Saber Unknown data, Unknown field
        writer.write_bytes(self.unknown1)  # Unknown values (3 int32s, typically {-1, -1, 0})
        writer.write_bytes(self.saber_unknowns)  # Saber Unknown data (8 bytes, lightsaber-specific)
        writer.write_int32(self.unknown2)  # Unknown field (int32 at offset 0xE8)
        writer.write_vector2(self.uv_direction)
        writer.write_single(self.uv_jitter)
        writer.write_single(self.uv_speed)

        # MDLOps writes these as signed int32 values. Emit 0xFFFFFFFF as -1.
        def _write_u32_as_i32(v: int) -> None:
            writer.write_int32(-1 if v == 0xFFFFFFFF else int(v))

        _write_u32_as_i32(self.mdx_data_size)
        _write_u32_as_i32(self.mdx_data_bitmap)
        _write_u32_as_i32(self.mdx_vertex_offset)
        _write_u32_as_i32(self.mdx_normal_offset)
        _write_u32_as_i32(self.mdx_color_offset)
        _write_u32_as_i32(self.mdx_texture1_offset)
        _write_u32_as_i32(self.mdx_texture2_offset)
        _write_u32_as_i32(self.mdx_uv3_offset)
        _write_u32_as_i32(self.mdx_uv4_offset)
        _write_u32_as_i32(self.mdx_tangent_offset)
        _write_u32_as_i32(self.mdx_unknown_offset)
        _write_u32_as_i32(self.mdx_unknown2_offset)
        _write_u32_as_i32(self.mdx_unknown3_offset)
        # Vertex count is stored as uint16 in the on-disk header.
        # Some real-world models use a full 0..65535 index range, requiring 65536 vertices;
        # MDLOps handles this by storing 0 in the uint16 field to mean 65536.
        if self.vertex_count < 0 or self.vertex_count > 65536:
            raise ValueError(f"vertex_count out of range for uint16/MDLOps semantics: {self.vertex_count}")
        writer.write_uint16(0 if self.vertex_count == 65536 else self.vertex_count)
        # Clamp texture_count to prevent issues (uint16 max is 65535)
        texture_count_clamped = min(self.texture_count, 65535)
        writer.write_uint16(texture_count_clamped)
        writer.write_uint8(self.has_lightmap)
        writer.write_uint8(self.rotate_texture)
        writer.write_uint8(self.background)
        writer.write_uint8(self.has_shadow)
        writer.write_uint8(self.beaming)
        writer.write_uint8(self.render)
        if game == Game.K2:
            # K2 dirt fields replace tail_short (2 bytes) with CCssL (10 bytes) + 2 uint32s (8 bytes)
            #
            writer.write_uint8(1 if self.dirt_enabled else 0)
            writer.write_uint8(0)  # padding byte
            writer.write_int16(self.dirt_texture if self.dirt_texture else 1)
            writer.write_int16(self.dirt_worldspace if self.dirt_worldspace else 1)
            writer.write_uint32(1 if self.hologram_donotdraw else 0)
            writer.write_uint32(self.k2_tail_long1)
            writer.write_uint32(self.k2_tail_long2)
        else:
            writer.write_uint16(self.tail_short)
        writer.write_single(self.total_area)
        writer.write_uint32(self.tail_long0)
        writer.write_uint32(self.mdx_data_offset)
        writer.write_uint32(self.vertices_offset)
        expected = _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE
        written = writer.position() - start_pos
        if written != expected:
            raise ValueError(f"_TrimeshHeader.write wrote {written} bytes, expected {expected}")

    def header_size(
        self,
        game: Game,
    ) -> int:
        return _TrimeshHeader.K1_SIZE if game == Game.K1 else _TrimeshHeader.K2_SIZE

    def faces_size(self) -> int:
        return len(self.faces) * _Face.SIZE

    def vertices_size(self) -> int:
        return len(self.vertices) * 12

    def vertex_indices_size(self) -> int:
        """Size of vertex indices array (3 int16s per face = 6 bytes per face).
        """
        return len(self.faces) * 6  # 3 shorts per face


class _DanglymeshHeader:
    def __init__(self):
        self.offset_to_contraints: int = 0
        self.constraints_count: int = 0
        self.constraints_count2: int = 0
        self.displacement: float = 0.0
        self.tightness: float = 0.0
        self.period: float = 0.0
        # Reference: MDLOps documentation - danglyverts pointer (offset-12)
        # This field stores the offset to danglyverts data, typically 0 or offset-12 from constraint pointer
        self.danglyverts_offset: int = 0  # Danglyverts pointer (offset-12, uint32)

    def read(
        self,
        reader: BinaryReader,
    ) -> _DanglymeshHeader:
        self.offset_to_contraints = reader.read_uint32()
        constraints_count_raw = reader.read_uint32()
        self.constraints_count = min(constraints_count_raw, 0x7FFFFFFF)
        constraints_count2_raw = reader.read_uint32()
        self.constraints_count2 = min(constraints_count2_raw, 0x7FFFFFFF)
        self.displacement = reader.read_single()
        self.tightness = reader.read_single()
        self.period = reader.read_single()
        # Reference: MDLOps documentation - danglyverts pointer (offset-12)
        self.danglyverts_offset = reader.read_uint32()  # Danglyverts pointer (offset-12, uint32)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        # MDLOps writes: pack("lll", 0, vertnum, vertnum) then f[3] then l
        # First 3 int32s: constraint pointer (offset-12), constraints_count, constraints_count2
        writer.write_uint32(self.offset_to_contraints)
        constraints_count_clamped = min(self.constraints_count, 0x7FFFFFFF)
        writer.write_uint32(constraints_count_clamped)
        constraints_count2_clamped = min(self.constraints_count2, 0x7FFFFFFF)
        writer.write_uint32(constraints_count2_clamped)
        # Then 3 floats: displacement, tightness, period
        writer.write_single(self.displacement)
        writer.write_single(self.tightness)
        writer.write_single(self.period)
        # Then danglyverts pointer (offset-12), typically 0 or offset-12 from constraint pointer
        writer.write_uint32(self.danglyverts_offset)  # danglyverts pointer


class _SkinmeshHeader:
    SIZE: ClassVar[int] = 100

    def __init__(self):
        # Reference: wiki/MDL-MDX-File-Format.md:443 - Skinmesh header structure
        # Offset 332/340 (K1/K2): "Unknown Weights" - Purpose unknown (possibly compilation weights)
        self.unknown_weights: int = 0  # Unknown Weights (int32 at binary offset 0x0 relative to skinmesh header, 0x14c/0x154 absolute)
        # Offset 336/344: Second unknown int32 field (not documented in wiki, but present in binary layout)
        self.unknown3: int = 0  # Unknown field (int32 at binary offset 0x4 relative to skinmesh header, 0x150/0x158 absolute)
        # Offset 340/348: Third unknown int32 field (not documented in wiki, but present in binary layout)
        self.unknown4: int = 0  # Unknown field (int32 at binary offset 0x8 relative to skinmesh header, 0x154/0x15c absolute)
        self.offset_to_mdx_weights: int = 0
        self.offset_to_mdx_bones: int = 0
        self.offset_to_bonemap: int = 0
        self.bonemap_count: int = 0
        self.offset_to_qbones: int = 0
        self.qbones_count: int = 0
        self.qbones_count2: int = 0
        self.offset_to_tbones: int = 0
        self.tbones_count: int = 0
        self.tbones_count2: int = 0
        # Reference: wiki/MDL-MDX-File-Format.md:454 - "Unknown array" at offset 384/392
        self.offset_to_unknown0: int = 0  # Offset to unknown array (uint32 at offset 0x34 relative to skinmesh header, 0x180/0x188 absolute)
        self.unknown0_count: int = 0  # Count of unknown array entries (uint32, documented as "Purpose unknown" in wiki)
        self.unknown0_count2: int = 0  # Duplicate count of unknown array entries (uint32)
        self.bones: tuple[int, ...] = tuple(-1 for _ in range(16))
        # Reference: wiki/MDL-MDX-File-Format.md:456 - "Padding" at offset 428/436 (uint16)
        # Note: Wiki documents uint16 padding, but code reads uint32. Structure may differ or wiki incomplete.
        # After bones array (16 uint16s = 32 bytes ending at 428/436), this field follows.
        self.unknown1: int = 0  # Padding/unknown field (uint32, wiki documents uint16 padding at 428/436 - structure mismatch)

        # NOTE: Some implementations store bonemap values as float32; we store them as ints.
        self.bonemap: list[int] = []
        self.tbones: list[Vector3] = []
        self.qbones: list[Vector4] = []

    def read(
        self,
        reader: BinaryReader,
    ) -> _SkinmeshHeader:
        # Reference: wiki/MDL-MDX-File-Format.md:443 - "Unknown Weights" field
        self.unknown_weights = reader.read_int32()  # Unknown Weights (possibly compilation weights)
        self.unknown3 = reader.read_int32()  # Unknown field (int32 at offset 0x4, not documented in wiki)
        self.unknown4 = reader.read_int32()  # Unknown field (int32 at offset 0x8, not documented in wiki)
        self.offset_to_mdx_weights = reader.read_uint32()
        self.offset_to_mdx_bones = reader.read_uint32()
        self.offset_to_bonemap = reader.read_uint32()
        bonemap_count_raw = reader.read_uint32()
        self.bonemap_count = min(bonemap_count_raw, 0x7FFFFFFF)
        self.offset_to_qbones = reader.read_uint32()
        qbones_count_raw = reader.read_uint32()
        self.qbones_count = min(qbones_count_raw, 0x7FFFFFFF)
        qbones_count2_raw = reader.read_uint32()
        self.qbones_count2 = min(qbones_count2_raw, 0x7FFFFFFF)
        self.offset_to_tbones = reader.read_uint32()
        tbones_count_raw = reader.read_uint32()
        self.tbones_count = min(tbones_count_raw, 0x7FFFFFFF)
        tbones_count2_raw = reader.read_uint32()
        self.tbones_count2 = min(tbones_count2_raw, 0x7FFFFFFF)
        self.offset_to_unknown0 = reader.read_uint32()
        # Reference: wiki/MDL-MDX-File-Format.md:454 - Unknown array count
        unknown0_count_raw = reader.read_uint32()  # Count of unknown array entries (Purpose unknown)
        self.unknown0_count = min(unknown0_count_raw, 0x7FFFFFFF)
        unknown0_count2_raw = reader.read_uint32()  # Duplicate count of unknown array entries
        self.unknown0_count2 = min(unknown0_count2_raw, 0x7FFFFFFF)
        self.bones = tuple(reader.read_uint16() for _ in range(16))
        # Reference: wiki/MDL-MDX-File-Format.md:456 - Padding at offset 428/436 (wiki: uint16, code: uint32 - mismatch)
        self.unknown1 = reader.read_uint32()  # Padding/unknown field (wiki documents uint16 padding, code reads uint32)
        return self

    def read_extra(
        self,
        reader: BinaryReader,
    ):
        # All offsets in MDL are relative to the MDL data section. Some models (or partially read headers)
        # may contain invalid offsets; guard against OOB seeks to keep parsing robust.
        if self.offset_to_bonemap not in (0, 0xFFFFFFFF) and self.bonemap_count > 0:
            # bonemap is stored as floats in some implementations; keep current behavior but validate bounds.
            bonemap_bytes = self.bonemap_count * 4
            if self.offset_to_bonemap <= reader.size() and (self.offset_to_bonemap + bonemap_bytes) <= reader.size():
                reader.seek(self.offset_to_bonemap)
                self.bonemap = [int(reader.read_single()) for _ in range(self.bonemap_count)]

        if self.offset_to_tbones not in (0, 0xFFFFFFFF) and self.tbones_count > 0:
            tbones_bytes = self.tbones_count * 12
            if self.offset_to_tbones <= reader.size() and (self.offset_to_tbones + tbones_bytes) <= reader.size():
                reader.seek(self.offset_to_tbones)
                self.tbones = [reader.read_vector3() for _ in range(self.tbones_count)]

        if self.offset_to_qbones not in (0, 0xFFFFFFFF) and self.qbones_count > 0:
            qbones_bytes = self.qbones_count * 16
            if self.offset_to_qbones <= reader.size() and (self.offset_to_qbones + qbones_bytes) <= reader.size():
                reader.seek(self.offset_to_qbones)
                self.qbones = [reader.read_vector4() for _ in range(self.qbones_count)]

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_int32(self.unknown_weights)  # Unknown Weights (possibly compilation weights)
        writer.write_int32(self.unknown3)  # Unknown field (not documented in wiki)
        writer.write_int32(self.unknown4)  # Unknown field (not documented in wiki)
        writer.write_uint32(self.offset_to_mdx_weights)
        writer.write_uint32(self.offset_to_mdx_bones)
        writer.write_uint32(self.offset_to_bonemap)
        bonemap_count_clamped = min(self.bonemap_count, 0x7FFFFFFF)
        writer.write_uint32(bonemap_count_clamped)
        writer.write_uint32(self.offset_to_qbones)
        qbones_count_clamped = min(self.qbones_count, 0x7FFFFFFF)
        writer.write_uint32(qbones_count_clamped)
        qbones_count2_clamped = min(self.qbones_count2, 0x7FFFFFFF)
        writer.write_uint32(qbones_count2_clamped)
        writer.write_uint32(self.offset_to_tbones)
        tbones_count_clamped = min(self.tbones_count, 0x7FFFFFFF)
        writer.write_uint32(tbones_count_clamped)
        tbones_count2_clamped = min(self.tbones_count2, 0x7FFFFFFF)
        writer.write_uint32(tbones_count2_clamped)
        writer.write_uint32(self.offset_to_unknown0)
        # Reference: wiki/MDL-MDX-File-Format.md:454 - Unknown array count
        unknown0_count_clamped = min(self.unknown0_count, 0x7FFFFFFF)  # Count of unknown array entries
        writer.write_uint32(unknown0_count_clamped)
        unknown0_count2_clamped = min(self.unknown0_count2, 0x7FFFFFFF)  # Duplicate count of unknown array entries
        writer.write_uint32(unknown0_count2_clamped)
        for i in range(16):
            writer.write_uint16(self.bones[i])
        # Reference: wiki/MDL-MDX-File-Format.md:456 - Padding (wiki: uint16, code: uint32 - structure mismatch)
        writer.write_uint32(self.unknown1)  # Padding/unknown field (wiki documents uint16, code writes uint32)


class _SaberHeader:
    def __init__(self):
        self.offset_to_vertices: int = 0
        self.offset_to_texcoords: int = 0
        self.offset_to_normals: int = 0
        # Reference: wiki/MDL-MDX-File-Format.md:472-473 - Lightsaber header structure
        # Offset 344/352 (K1/K2): "Unknown 1" - Purpose unknown
        self.unknown0: int = 0  # Unknown 1 (uint32 at binary offset 0xC relative to saber header, 0x158/0x160 absolute)
        # Offset 348/356 (K1/K2): "Unknown 2" - Purpose unknown
        self.unknown1: int = 0  # Unknown 2 (uint32 at binary offset 0x10 relative to saber header, 0x15C/0x164 absolute)

    def read(
        self,
        reader: BinaryReader,
    ) -> _SaberHeader:
        self.offset_to_vertices = reader.read_uint32()
        self.offset_to_texcoords = reader.read_uint32()
        self.offset_to_normals = reader.read_uint32()
        # Reference: wiki/MDL-MDX-File-Format.md:472-473 - "Unknown 1" and "Unknown 2" fields
        self.unknown0 = reader.read_uint32()  # Unknown 1 (Purpose unknown)
        self.unknown1 = reader.read_uint32()  # Unknown 2 (Purpose unknown)
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_uint32(self.offset_to_vertices)
        writer.write_uint32(self.offset_to_texcoords)
        writer.write_uint32(self.offset_to_normals)
        # Reference: wiki/MDL-MDX-File-Format.md:472-473 - "Unknown 1" and "Unknown 2" fields
        writer.write_uint32(self.unknown0)  # Unknown 1 (Purpose unknown)
        writer.write_uint32(self.unknown1)  # Unknown 2 (Purpose unknown)


class _LightHeader:
    def __init__(self):
        # Reference: wiki/MDL-MDX-File-Format.md:484 - Structure mismatch: wiki documents "Unknown/Padding" (4 floats, 16 bytes) at offset 0
        # Code reads 3 uint32s (12 bytes): offset + 2 counts. Structure differs from wiki documentation.
        self.offset_to_unknown0: int = 0  # Offset to unknown array (uint32, wiki documents float padding - structure mismatch)
        self.unknown0_count: int = 0  # Count of unknown array entries (uint32, wiki documents float padding - structure mismatch)
        self.unknown0_count2: int = 0  # Duplicate count of unknown array entries (uint32, wiki documents float padding - structure mismatch)
        self.offset_to_flare_sizes: int = 0
        self.flare_sizes_count: int = 0
        self.flare_sizes_count2: int = 0
        self.offset_to_flare_positions: int = 0
        self.flare_positions_count: int = 0
        self.flare_positions_count2: int = 0
        self.offset_to_flare_colors: int = 0
        self.flare_colors_count: int = 0
        self.flare_colors_count2: int = 0
        self.offset_to_flare_textures: int = 0
        self.flare_textures_count: int = 0
        self.flare_textures_count2: int = 0
        self.flare_radius: float = 0.0
        self.light_priority: int = 0
        self.ambient_only: int = 0
        self.dynamic_type: int = 0
        self.affect_dynamic: int = 0
        self.shadow: int = 0
        self.flare: int = 0
        self.fading_light: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _LightHeader:
        # Reference: wiki/MDL-MDX-File-Format.md:484 - Structure mismatch: wiki documents 4 floats (16 bytes) at offset 0
        # Code reads 3 uint32s (12 bytes) - structure differs from wiki
        self.offset_to_unknown0 = reader.read_uint32()  # Offset to unknown array (wiki documents float padding - mismatch)
        unknown0_count_raw = reader.read_uint32()  # Count of unknown array entries (wiki documents float padding - mismatch)
        self.unknown0_count = min(unknown0_count_raw, 0x7FFFFFFF)
        unknown0_count2_raw = reader.read_uint32()  # Duplicate count of unknown array entries (wiki documents float padding - mismatch)
        self.unknown0_count2 = min(unknown0_count2_raw, 0x7FFFFFFF)
        self.offset_to_flare_sizes = reader.read_uint32()
        flare_sizes_count_raw = reader.read_uint32()
        self.flare_sizes_count = min(flare_sizes_count_raw, 0x7FFFFFFF)
        flare_sizes_count2_raw = reader.read_uint32()
        self.flare_sizes_count2 = min(flare_sizes_count2_raw, 0x7FFFFFFF)
        self.offset_to_flare_positions = reader.read_uint32()
        flare_positions_count_raw = reader.read_uint32()
        self.flare_positions_count = min(flare_positions_count_raw, 0x7FFFFFFF)
        flare_positions_count2_raw = reader.read_uint32()
        self.flare_positions_count2 = min(flare_positions_count2_raw, 0x7FFFFFFF)
        self.offset_to_flare_colors = reader.read_uint32()
        flare_colors_count_raw = reader.read_uint32()
        self.flare_colors_count = min(flare_colors_count_raw, 0x7FFFFFFF)
        flare_colors_count2_raw = reader.read_uint32()
        self.flare_colors_count2 = min(flare_colors_count2_raw, 0x7FFFFFFF)
        self.offset_to_flare_textures = reader.read_uint32()
        flare_textures_count_raw = reader.read_uint32()
        self.flare_textures_count = min(flare_textures_count_raw, 0x7FFFFFFF)
        flare_textures_count2_raw = reader.read_uint32()
        self.flare_textures_count2 = min(flare_textures_count2_raw, 0x7FFFFFFF)
        self.flare_radius = reader.read_single()
        self.light_priority = reader.read_uint32()
        self.ambient_only = reader.read_uint32()
        self.dynamic_type = reader.read_uint32()
        self.affect_dynamic = reader.read_uint32()
        self.shadow = reader.read_uint32()
        self.flare = reader.read_uint32()
        self.fading_light = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        # Reference: wiki/MDL-MDX-File-Format.md:484 - Structure mismatch: wiki documents 4 floats (16 bytes) at offset 0
        # Code writes 3 uint32s (12 bytes) - structure differs from wiki
        writer.write_uint32(self.offset_to_unknown0)  # Offset to unknown array (wiki documents float padding - mismatch)
        unknown0_count_clamped = min(self.unknown0_count, 0x7FFFFFFF)  # Count of unknown array entries (wiki documents float padding - mismatch)
        writer.write_uint32(unknown0_count_clamped)
        unknown0_count2_clamped = min(self.unknown0_count2, 0x7FFFFFFF)  # Duplicate count (wiki documents float padding - mismatch)
        writer.write_uint32(unknown0_count2_clamped)
        writer.write_uint32(self.offset_to_flare_sizes)
        flare_sizes_count_clamped = min(self.flare_sizes_count, 0x7FFFFFFF)
        writer.write_uint32(flare_sizes_count_clamped)
        flare_sizes_count2_clamped = min(self.flare_sizes_count2, 0x7FFFFFFF)
        writer.write_uint32(flare_sizes_count2_clamped)
        writer.write_uint32(self.offset_to_flare_positions)
        flare_positions_count_clamped = min(self.flare_positions_count, 0x7FFFFFFF)
        writer.write_uint32(flare_positions_count_clamped)
        flare_positions_count2_clamped = min(self.flare_positions_count2, 0x7FFFFFFF)
        writer.write_uint32(flare_positions_count2_clamped)
        writer.write_uint32(self.offset_to_flare_colors)
        flare_colors_count_clamped = min(self.flare_colors_count, 0x7FFFFFFF)
        writer.write_uint32(flare_colors_count_clamped)
        flare_colors_count2_clamped = min(self.flare_colors_count2, 0x7FFFFFFF)
        writer.write_uint32(flare_colors_count2_clamped)
        writer.write_uint32(self.offset_to_flare_textures)
        flare_textures_count_clamped = min(self.flare_textures_count, 0x7FFFFFFF)
        writer.write_uint32(flare_textures_count_clamped)
        flare_textures_count2_clamped = min(self.flare_textures_count2, 0x7FFFFFFF)
        writer.write_uint32(flare_textures_count2_clamped)
        writer.write_single(self.flare_radius)
        writer.write_uint32(self.light_priority)
        writer.write_uint32(self.ambient_only)
        writer.write_uint32(self.dynamic_type)
        writer.write_uint32(self.affect_dynamic)
        writer.write_uint32(self.shadow)
        writer.write_uint32(self.flare)
        writer.write_uint32(self.fading_light)


class _EmitterHeader:
    def __init__(self):
        # MDLOps emitter_header template (size 224):
        #   f[3]L[5]Z[32]Z[32]Z[32]Z[32]Z[16]L[2]SCZ[32]CL
        # See: ` lines ~176-190 and ~6889+.
        self.dead_space: float = 0.0
        self.blast_radius: float = 0.0
        self.blast_length: float = 0.0

        self.branch_count: int = 0  # L (numBranches)
        # NOTE: Stored as uint32 in MDLOps' template (L), despite some external docs treating it as float.
        # We keep it as uint32 for mdlops parity and map to/from MDLEmitter as float where needed.
        self.control_point_smoothing: int = 0  # L (controlptsmoothing)
        self.x_grid: int = 0  # L
        self.y_grid: int = 0  # L
        self.spawn_type: int = 0  # L (spawntype)

        self.update: str = ""  # Z[32]
        self.render: str = ""  # Z[32]
        self.blend: str = ""  # Z[32]
        self.texture: str = ""  # Z[32]
        self.chunk_name: str = ""  # Z[16]

        self.twosided_texture: int = 0  # L
        self.loop: int = 0  # L
        self.render_order: int = 0  # S
        self.frame_blending: int = 0  # C (uint8)
        self.depth_texture: str = ""  # Z[32] (32-byte null-terminated string)
        # Reference: MDLOps template "SCZ[32]CL" - C byte (padding byte, MDLOps writes 0)
        self.unknown1: int = 0  # Padding byte (uint8, MDLOps template: C, always writes 0 for alignment)
        self.flags: int = 0  # L (emitterflags, uint32)

    def read(
        self,
        reader: BinaryReader,
    ) -> _EmitterHeader:
        self.dead_space = reader.read_single()
        self.blast_radius = reader.read_single()
        self.blast_length = reader.read_single()

        self.branch_count = reader.read_uint32()
        self.control_point_smoothing = reader.read_uint32()
        self.x_grid = reader.read_uint32()
        self.y_grid = reader.read_uint32()
        self.spawn_type = reader.read_uint32()

        self.update = reader.read_terminated_string("\0", 32)
        self.render = reader.read_terminated_string("\0", 32)
        self.blend = reader.read_terminated_string("\0", 32)
        self.texture = reader.read_terminated_string("\0", 32)
        self.chunk_name = reader.read_terminated_string("\0", 16)

        self.twosided_texture = reader.read_uint32()
        self.loop = reader.read_uint32()
        self.render_order = reader.read_uint16()
        self.frame_blending = reader.read_uint8()
        self.depth_texture = reader.read_terminated_string("\0", 32)
        self.unknown1 = reader.read_uint8()
        self.flags = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_single(self.dead_space)
        writer.write_single(self.blast_radius)
        writer.write_single(self.blast_length)

        writer.write_uint32(self.branch_count)
        writer.write_uint32(self.control_point_smoothing)
        writer.write_uint32(self.x_grid)
        writer.write_uint32(self.y_grid)
        writer.write_uint32(self.spawn_type)

        writer.write_string(self.update, string_length=32, encoding="ascii")
        writer.write_string(self.render, string_length=32, encoding="ascii")
        writer.write_string(self.blend, string_length=32, encoding="ascii")
        writer.write_string(self.texture, string_length=32, encoding="ascii")
        writer.write_string(self.chunk_name, string_length=16, encoding="ascii")

        writer.write_uint32(self.twosided_texture)
        writer.write_uint32(self.loop)
        writer.write_uint16(self.render_order)
        writer.write_uint8(self.frame_blending)
        writer.write_string(self.depth_texture, string_length=32, encoding="ascii")
        writer.write_uint8(self.unknown1)
        writer.write_uint32(self.flags)


class _ReferenceHeader:
    def __init__(self):
        self.model: str = ""
        self.reattachable: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _ReferenceHeader:
        self.model = reader.read_terminated_string("\0", 32)
        self.reattachable = reader.read_uint32()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_string(self.model, string_length=32, encoding="ascii")
        writer.write_uint32(self.reattachable)


class _Face:
    SIZE = 32

    def __init__(self):
        self.normal: Vector3 = Vector3.from_null()
        self.plane_coefficient: float = 0.0
        self.material: int = 0
        self.adjacent1: int = 0
        self.adjacent2: int = 0
        self.adjacent3: int = 0
        self.vertex1: int = 0
        self.vertex2: int = 0
        self.vertex3: int = 0

    def read(
        self,
        reader: BinaryReader,
    ) -> _Face:
        self.normal = reader.read_vector3()
        self.plane_coefficient = reader.read_single()
        self.material = reader.read_uint32()
        self.adjacent1 = reader.read_uint16()
        self.adjacent2 = reader.read_uint16()
        self.adjacent3 = reader.read_uint16()
        self.vertex1 = reader.read_uint16()
        self.vertex2 = reader.read_uint16()
        self.vertex3 = reader.read_uint16()
        return self

    def write(
        self,
        writer: BinaryWriter,
    ):
        writer.write_vector3(self.normal)
        writer.write_single(self.plane_coefficient)
        writer.write_uint32(self.material)
        writer.write_uint16(self.adjacent1)
        writer.write_uint16(self.adjacent2)
        writer.write_uint16(self.adjacent3)
        writer.write_uint16(self.vertex1)
        writer.write_uint16(self.vertex2)
        writer.write_uint16(self.vertex3)


# Geometry calculation utilities
# Reference: https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:463-520


def _calculate_face_area(v1: Vector3, v2: Vector3, v3: Vector3) -> float:
    """Calculate a triangle face's surface area using Heron's formula.

    Args:
    ----
        v1: First vertex position
        v2: Second vertex position
        v3: Third vertex position

    Returns:
    -------
        The surface area of the triangle

    References:
    ----------
        Based on swkotor.exe geometry calculations:
        - Triangle area calculation uses standard Heron's formula
        - Used in mesh processing and collision detection
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:465-488

        Formula: Uses Heron's formula with semi-perimeter
    """
    # Calculate edge lengths (mdlops:471-482)
    import math

    a = math.sqrt((v1.x - v2.x) ** 2 + (v1.y - v2.y) ** 2 + (v1.z - v2.z) ** 2)

    b = math.sqrt((v1.x - v3.x) ** 2 + (v1.y - v3.y) ** 2 + (v1.z - v3.z) ** 2)

    c = math.sqrt((v2.x - v3.x) ** 2 + (v2.y - v3.y) ** 2 + (v2.z - v3.z) ** 2)

    # Semi-perimeter (mdlops:483)
    s = (a + b + c) / 2.0

    # Heron's formula (mdlops:485-487)
    inter = s * (s - a) * (s - b) * (s - c)
    return math.sqrt(inter) if inter > 0.0 else 0.0


def _decompress_quaternion(compressed: int) -> Vector4:
    """Decompress a packed quaternion from a 32-bit integer.

    KotOR uses compressed quaternions for orientation controllers to save space.
    The compression packs X, Y, Z components into 11, 11, and 10 bits respectively,
    with W calculated from the constraint that |q| = 1.

    Args:
    ----
        compressed: 32-bit packed quaternion value

    Returns:
    -------
        Vector4: Decompressed quaternion (x, y, z, w)

    References:
    ----------
        Based on swkotor.exe quaternion compression:
        - CompressQuaternionKey @ (K1: 0x00464b50, TSL: N/A - likely inlined or different implementation) - Compresses quaternion to 32-bit integer (742 bytes, 4 callees)
          * Packs X, Y, Z components into 11, 11, and 10 bits respectively
          * Maps quaternion components from [-1, 1] to integer ranges
          * W component is computed from constraint |q| = 1
          * TSL: Decompression logic is present in GetQuaternionFromIndexLocation, compression may be inlined in MDL parsing
        - Quaternion::Quaternion @ (K1: 0x004ac960, TSL: N/A - likely inlined or different implementation) - Quaternion constructor (146 bytes, 1 callee)
          * Creates quaternion from axis-angle representation
          * Used for orientation parsing in MDL controllers
          * TSL: May be inlined or have different implementation pattern
        - GetQuaternionValue @ (K1: 0x004831b0, TSL: 0x004b3b90) - Gets quaternion value (382 bytes, 3 callees)
        - GetQuaternionFromIndexLocation @ (K1: 0x00483050, TSL: 0x004b3a30) - Gets quaternion from index (347 bytes)
          * TSL: Also handles decompression of compressed quaternions (bit extraction: 0x7ff mask, >> 0xb, >> 0x16)
        - slerp @ (K1: 0x004a9e00, TSL: 0x004d8c80) - Spherical linear interpolation for quaternions
        - quaternionScalarMult @ (K1: 0x004a9b80, TSL: N/A - likely inlined) - Quaternion scalar multiplication (47 bytes)
        - quaternionDotProduct @ (K1: 0x004a9d30, TSL: N/A - likely inlined in slerp) - Quaternion dot product (37 bytes)
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/kotorblender/tree/master/io_scene_kotor/format/mdl/reader.py:850-868

        Formula: X uses bits 0-10 (11 bits), Y uses bits 11-21 (11 bits),
                 Z uses bits 22-31 (10 bits), W computed from magnitude

    Notes:
    -----
        The compressed format maps values to [-1, 1] range:
        - X: 11 bits -> [0, 2047] -> mapped to [-1, 1]
        - Y: 11 bits -> [0, 2047] -> mapped to [-1, 1]
        - Z: 10 bits -> [0, 1023] -> mapped to [-1, 1]
        - W: Computed from sqrt(1 - x² - y² - z²) if mag < 1, else 0
    """
    # Extract components from packed integer (kotorblender:855-858)
    # X component: bits 0-10 (11 bits, mask 0x7FF = 2047)
    x = ((compressed & 0x7FF) / 1023.0) - 1.0

    # Y component: bits 11-21 (11 bits, shift 11 then mask 0x7FF)
    y = (((compressed >> 11) & 0x7FF) / 1023.0) - 1.0

    # Z component: bits 22-31 (10 bits, shift 22, max value 1023)
    z = ((compressed >> 22) / 511.0) - 1.0

    # Calculate W from quaternion unit constraint (kotorblender:859-863)
    mag2 = x * x + y * y + z * z
    if mag2 < 1.0:
        import math

        w = math.sqrt(1.0 - mag2)
    else:
        w = 0.0

    return Vector4(x, y, z, w)


def _compress_quaternion(quat: Vector4) -> int:
    """Compress a quaternion into a 32-bit integer.

    Inverse of _decompress_quaternion. Packs X, Y, Z components into a single
    32-bit value. The W component is not stored as it can be recomputed from
    the quaternion unit constraint.

    Args:
    ----
        quat: Quaternion to compress (x, y, z, w)

    Returns:
    -------
        int: 32-bit packed quaternion value

    References:
    ----------
        Original BioWare engine binaries (from swkotor.exe, swkotor2.exe)
        Original BioWare engine binaries
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/kotorblender/tree/master/io_scene_kotor/format/mdl/reader.py:850-868 (decompression)
        Inverse operation derived from decompression algorithm


    Notes:
    -----
        Values are clamped to [-1, 1] range before packing to prevent overflow.
    """

    # Clamp values to valid range
    x = max(-1.0, min(1.0, quat.x))
    y = max(-1.0, min(1.0, quat.y))
    z = max(-1.0, min(1.0, quat.z))

    # Map from [-1, 1] to integer ranges and pack
    # X: [-1, 1] -> [0, 2047] (11 bits)
    x_packed = int((x + 1.0) * 1023.0) & 0x7FF

    # Y: [-1, 1] -> [0, 2047] (11 bits)
    y_packed = int((y + 1.0) * 1023.0) & 0x7FF

    # Z: [-1, 1] -> [0, 1023] (10 bits)
    z_packed = int((z + 1.0) * 511.0) & 0x3FF

    # Pack into single 32-bit integer
    return x_packed | (y_packed << 11) | (z_packed << 22)


def _calculate_face_normal(
    v1: Vector3,
    v2: Vector3,
    v3: Vector3,
) -> tuple[Vector3, float]:
    """Calculate a triangle face normal and triangle area.

    Returns:
        (normal, area) where:
        - normal is a unit-length Vector3 (or zero-vector if degenerate)
        - area is the triangle area (always non-negative)
    """
    # Edges
    e1 = Vector3(v2.x - v1.x, v2.y - v1.y, v2.z - v1.z)
    e2 = Vector3(v3.x - v1.x, v3.y - v1.y, v3.z - v1.z)

    # Cross product e1 x e2
    cx = (e1.y * e2.z) - (e1.z * e2.y)
    cy = (e1.z * e2.x) - (e1.x * e2.z)
    cz = (e1.x * e2.y) - (e1.y * e2.x)

    mag = math.sqrt((cx * cx) + (cy * cy) + (cz * cz))
    area = 0.5 * mag
    if mag <= 0.0:
        return Vector3.from_null(), 0.0

    inv = 1.0 / mag
    return Vector3(cx * inv, cy * inv, cz * inv), area


def _calculate_tangent_space(
    v0: Vector3,
    v1: Vector3,
    v2: Vector3,
    uv0: tuple[float, float],
    uv1: tuple[float, float],
    uv2: tuple[float, float],
    face_normal: Vector3,
) -> tuple[Vector3, Vector3]:
    """Calculate tangent and binormal vectors for a triangle face.

    Uses the standard UV-derivative method and returns normalized vectors. For degenerate
    UVs, returns a stable fallback basis.
    """
    # Position deltas
    dp1 = Vector3(v1.x - v0.x, v1.y - v0.y, v1.z - v0.z)
    dp2 = Vector3(v2.x - v0.x, v2.y - v0.y, v2.z - v0.z)

    # UV deltas
    duv1x, duv1y = (uv1[0] - uv0[0]), (uv1[1] - uv0[1])
    duv2x, duv2y = (uv2[0] - uv0[0]), (uv2[1] - uv0[1])

    det = (duv1x * duv2y) - (duv1y * duv2x)
    if abs(det) < 1e-12:
        return Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)

    r = 1.0 / det
    tx = (dp1.x * duv2y - dp2.x * duv1y) * r
    ty = (dp1.y * duv2y - dp2.y * duv1y) * r
    tz = (dp1.z * duv2y - dp2.z * duv1y) * r
    bx = (dp2.x * duv1x - dp1.x * duv2x) * r
    by = (dp2.y * duv1x - dp1.y * duv2x) * r
    bz = (dp2.z * duv1x - dp1.z * duv2x) * r

    # Orthonormalize tangent against normal
    dot_nt = (face_normal.x * tx) + (face_normal.y * ty) + (face_normal.z * tz)
    tx -= face_normal.x * dot_nt
    ty -= face_normal.y * dot_nt
    tz -= face_normal.z * dot_nt

    tlen = math.sqrt((tx * tx) + (ty * ty) + (tz * tz))
    if tlen <= 1e-12:
        tangent = Vector3(1.0, 0.0, 0.0)
    else:
        inv = 1.0 / tlen
        tangent = Vector3(tx * inv, ty * inv, tz * inv)

    # Orthonormalize binormal against normal and tangent
    dot_nb = (face_normal.x * bx) + (face_normal.y * by) + (face_normal.z * bz)
    bx -= face_normal.x * dot_nb
    by -= face_normal.y * dot_nb
    bz -= face_normal.z * dot_nb
    dot_tb = (tangent.x * bx) + (tangent.y * by) + (tangent.z * bz)
    bx -= tangent.x * dot_tb
    by -= tangent.y * dot_tb
    bz -= tangent.z * dot_tb

    blen = math.sqrt((bx * bx) + (by * by) + (bz * bz))
    if blen <= 1e-12:
        binormal = Vector3(0.0, 1.0, 0.0)
    else:
        inv = 1.0 / blen
        binormal = Vector3(bx * inv, by * inv, bz * inv)

    return tangent, binormal


class MDLBinaryReader:
    """Binary MDL/MDX file reader.

    This class provides loading of MDL (model) and MDX (model extension) files.
    Supports both full loading and fast loading optimized for rendering.

    Args:
    ----
        source: The source of the MDL data
        offset: The byte offset within the source
        size: Size of the data to read
        source_ext: The source of the MDX data
        offset_ext: The byte offset within the MDX source
        size_ext: Size of the MDX data to read
        game: The game version (K1 or K2)
        fast_load: If True, skips animations and controllers for faster loading (optimized for rendering)

    References:
    ----------
        Based on swkotor.exe MDL structure:
        - LoadModel @ (K1: 0x00464200, TSL: 0x0047a570) - High-level model loader (172 bytes, 42 lines)
          * Loads MDL/MDX through IODispatcher::ReadSync
          * Manages model cache (modelsList) to avoid duplicate loads
          * Returns Model* pointer or nullptr on failure
        - CSWCCreature::LoadModel @ (K1: 0x0061b380, TSL: 0x00669ea0) - Creature model loader (842 bytes, 167 lines)
          * Loads creature models with animation base setup
          * Handles different model types: base, head, wield, head+wield, two-weapon
          * Sets up CSWCAnimBase, CSWCAnimBaseHead, CSWCAnimBaseWield, etc.
          * Registers callbacks and sets model properties
        - CSWCPlaceable::LoadModel @ (K1: 0x006823f0, TSL: 0x006d9721) - Placeable model loader (504 bytes, 105 lines)
          * Loads placeable models with animation base
          * Handles head hit detection ("_head_hit" node lookup)
          * Sets up CSWCAnimBasePlaceable
        - CSWCCreature::UnloadModel @ (K1: 0x0060c8e0, TSL: N/A - likely inlined) - Unloads creature models (42 bytes, 19 lines)
          * Releases animation base resources
          * Clears anim_base pointer
        - CSWCObject::UnloadModel @ (K1: 0x00646650, TSL: N/A - likely inlined) - Unloads object models (13 bytes, calls anim_base->vtable[0x74]())
          * Different from CSWCCreature::UnloadModel (uses vtable offset 0x74 vs 0x78)
        - UnloadModel call site @ (K1: 0x006825f0, TSL: 0x006d9721) (within CSWCPlaceable::LoadModel) - Additional unload function call
        - MdlNode::AsMdlNodeTriMesh @ (K1: 0x0043e400, TSL: 0x004501d0) - Converts node to trimesh type
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Derivations and Other Implementations:
        ----------
        - https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1649-1778 (Controller structure and bezier detection)
        - https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:5470-5596 (Tangent space calculation)
        - https://github.com/th3w1zard1/kotorblender/tree/master/format/mdl/reader.py:850-868 (Quaternion decompression)
        - https://github.com/th3w1zard1/KotOR.js/tree/master/src/loaders/MDLLoader.ts (Model loading architecture)


    """

    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
        source_ext: SOURCE_TYPES | None = None,
        offset_ext: int = 0,
        size_ext: int = 0,
        game: Game = Game.K2,
        fast_load: bool = False,
    ):
        self._reader: BinaryReader = BinaryReader.from_auto(source, offset)

        self._reader_ext: BinaryReader | None = (
            None
            if source_ext is None
            else BinaryReader.from_auto(source_ext, offset_ext)
        )

        # first 12 bytes do not count in offsets used within the file
        self._reader.set_offset(self._reader.offset() + 12)

        self._fast_load: bool = fast_load
        self.game: Game = game

    def load(
        self,
        auto_close: bool = True,  # noqa: FBT002, FBT001
    ) -> MDL:
        """Load the MDL file.

        Args:
        ----
            auto_close: If True, automatically close readers after loading

        Returns:
        -------
            The loaded MDL instance
        """
        self._mdl: MDL = MDL()
        self._names: list[str] = []

        model_header: _ModelHeader = _ModelHeader().read(self._reader)

        # Determine game version from the file header function pointers.
        # This is more reliable than using per-node function pointer values.
        if (
            model_header.geometry.function_pointer0 == _GeometryHeader.K1_FUNCTION_POINTER0
            and model_header.geometry.function_pointer1 == _GeometryHeader.K1_FUNCTION_POINTER1
        ):
            self.game = Game.K1
        elif (
            model_header.geometry.function_pointer0 == _GeometryHeader.K2_FUNCTION_POINTER0
            and model_header.geometry.function_pointer1 == _GeometryHeader.K2_FUNCTION_POINTER1
        ):
            self.game = Game.K2

        self._mdl.name = model_header.geometry.model_name
        self._mdl.supermodel = model_header.supermodel
        self._mdl.fog = bool(model_header.fog)
        # model_type corresponds to classification
        self._mdl.classification = MDLClassification(model_header.model_type)
        # subclassification corresponds to classification_unk1
        self._mdl.classification_unk1 = model_header.subclassification
        self._mdl.animation_scale = model_header.anim_scale
        # Bounding box and radius from model header
        self._mdl.bmin = model_header.bounding_box_min
        self._mdl.bmax = model_header.bounding_box_max
        self._mdl.radius = model_header.radius

        self._load_names(model_header)
        self._order2nameindex: list[int] = []
        self._get_node_order(model_header.geometry.root_node_offset)
        self._mdl.root = self._load_node(model_header.geometry.root_node_offset, None)

        # Detect headlink: if offset_to_super_root differs from root_node_offset and neck_g exists,
        # this is a head model.
        if model_header.offset_to_super_root != model_header.geometry.root_node_offset:
            # Check if neck_g node exists in the model
            for node in self._mdl.all_nodes():
                if node.name == "neck_g":
                    self._mdl.headlink = "1"
                    break

        # Skip animations when fast loading (not needed for rendering)
        if not self._fast_load:
            self._reader.seek(model_header.offset_to_animations)
            animation_offsets: list[int] = [
                self._reader.read_uint32()
                for _ in range(model_header.animation_count)
            ]
            for animation_offset in animation_offsets:
                anim: MDLAnimation = self._load_anim(animation_offset)
                self._mdl.anims.append(anim)

        if auto_close:
            self._reader.close()
            if self._reader_ext is not None:
                self._reader_ext.close()

        return self._mdl

    def _load_names(
        self,
        model_header: _ModelHeader,
    ):
        name_indexes_offset: int = model_header.offset_to_name_offsets
        self._reader.seek(name_indexes_offset)
        name_indexes_count: int = model_header.name_offsets_count
        name_indexes_raw: bytes = self._reader.read_bytes(4 * name_indexes_count)
        name_indexes_unpacked: list[int] = []
        for i in range(name_indexes_count):
            name_indexes_unpacked.append(
                int.from_bytes(
                    name_indexes_raw[i * 4 : (i + 1) * 4],
                    byteorder="little",
                    signed=True,
                ),
            )

        names_size: int = model_header.offset_to_animations - (
            model_header.offset_to_name_offsets
            + (4 * name_indexes_count)
        )
        names_raw: bytes = self._reader.read_bytes(names_size)

        names_list: list[str] = []
        current_pos: int = 0
        for _ in range(name_indexes_count):
            null_pos: int = names_raw.find(b"\x00", current_pos)
            if null_pos == -1:
                null_pos = len(names_raw)
            name_bytes: bytes = names_raw[current_pos:null_pos]
            name: str = name_bytes.decode("ascii", errors="ignore")
            names_list.append(name)
            current_pos = null_pos + 1
            if current_pos >= len(names_raw):
                break

        self._names = names_list

    def _get_node_order(
        self,
        startnode: int,
    ):
        startnode += 12
        self._reader.seek(startnode + 4)
        name_index: int = self._reader.read_uint16()
        self._order2nameindex.append(name_index)

        self._reader.seek(startnode + 44)
        child_array_offset: int = self._reader.read_uint32()
        child_array_length: int = self._reader.read_uint32()

        if child_array_length > 0 and child_array_offset not in (0, 0xFFFFFFFF):
            self._reader.seek(child_array_offset + 12)
            child_offsets: list[int] = [self._reader.read_uint32() for _ in range(child_array_length)]
            for child_offset in child_offsets:
                if child_offset not in (0, 0xFFFFFFFF):
                    self._get_node_order(child_offset)

    def _load_node(
        self,
        offset: int,
        parent: MDLNode | None,
    ) -> MDLNode:
        self._reader.seek(offset)
        bin_node: _Node = _Node().read(self._reader, self.game)
        assert bin_node.header is not None

        node: MDLNode = MDLNode()
        node.node_id = bin_node.header.node_id
        # MDLOps derives node names from the "partnames" array by node_id (not from the nodeheader 4th short).
        node.name = self._names[bin_node.header.node_id] if 0 <= bin_node.header.node_id < len(self._names) else ""
        node.position = bin_node.header.position
        node.orientation = bin_node.header.orientation
        node.node_type = MDLNodeType.DUMMY

        # Check for AABB flag - nodes with AABB flag should be marked as AABB type
        # A node can have both MESH and AABB flags (walkmesh with visible geometry)
        if bin_node.header.type_id & MDLNodeFlags.AABB:
            node.node_type = MDLNodeType.AABB
            from pykotor.resource.formats.mdl.mdl_data import MDLAABBNode, MDLWalkmesh

            if node.aabb is None:
                node.aabb = MDLWalkmesh()

            # Read AABB tree if offset is valid
            if bin_node.trimesh and bin_node.trimesh.offset_to_aabb > 0:
                # Read AABB tree recursively (depth-first, matching MDLOps)
                #
                def _read_aabb_recursive(
                    reader: BinaryReader,
                    offset: int,
                ) -> tuple[int, list[MDLAABBNode]]:
                    """Recursively read AABB tree node and its children.

                    Returns:
                        (count, nodes): Number of nodes read and list of AABB nodes
                    """
                    if offset == 0 or offset >= reader.size() or offset + 40 > reader.size():
                        return (0, [])

                    reader.seek(offset)
                    # Read 6 floats (bounding box min/max)
                    bbox_min: Vector3 = reader.read_vector3()
                    bbox_max: Vector3 = reader.read_vector3()
                    # Read 4 int32s: left child offset, right child offset, face index, unknown
                    # NOTE: Child offsets in the file are stored as (absolute_offset - 12), but since
                    # BinaryReader has set_offset(+12) applied, these can be used directly.
                    left_child: int = reader.read_int32()
                    right_child: int = reader.read_int32()
                    face_index: int = reader.read_int32()
                    unknown: int = reader.read_int32()

                    aabb_node = MDLAABBNode(
                        bbox_min=bbox_min,
                        bbox_max=bbox_max,
                        face_index=face_index,
                        left_child_offset=left_child,
                        right_child_offset=right_child,
                        unknown=unknown,
                    )

                    nodes = [aabb_node]
                    count = 1

                    # If this is a branch node (face_index == -1), recursively read children
                    if face_index == -1:
                        if left_child != 0:
                            child_count, child_nodes = _read_aabb_recursive(reader, left_child)
                            count += child_count
                            nodes.extend(child_nodes)
                        if right_child != 0:
                            child_count, child_nodes = _read_aabb_recursive(reader, right_child)
                            count += child_count
                            nodes.extend(child_nodes)

                    return (count, nodes)

                # Read AABB tree starting from the offset
                _, aabb_nodes = _read_aabb_recursive(self._reader, bin_node.trimesh.offset_to_aabb)
                node.aabb.aabbs = aabb_nodes

        # Check for LIGHT flag - nodes with LIGHT flag should be marked as LIGHT type
        if bin_node.header.type_id & MDLNodeFlags.LIGHT:
            node.node_type = MDLNodeType.LIGHT
            from pykotor.resource.formats.mdl.mdl_data import MDLDynamicType, MDLLight

            if bin_node.light is not None:
                node.light = MDLLight()
                node.light.ambient_only = bool(bin_node.light.ambient_only)
                node.light.dynamic_type = MDLDynamicType(bin_node.light.dynamic_type)
                node.light.shadow = bool(bin_node.light.shadow)
                node.light.flare = bool(bin_node.light.flare)
                node.light.light_priority = bin_node.light.light_priority
                node.light.fading_light = bool(bin_node.light.fading_light)
                node.light.flare_radius = bin_node.light.flare_radius

                # Read flare data (sizes, positions, colors, textures)
                #
                light_header = bin_node.light

                # Flare textures: array of string pointers, each pointing to a 12-byte null-terminated string
                if light_header.flare_textures_count > 0 and light_header.offset_to_flare_textures not in (0, 0xFFFFFFFF):
                    node.light.flare_textures = []
                    saved_pos = self._reader.position()
                    try:
                        # Read texture name pointers (each pointer is 4 bytes)
                        self._reader.seek(light_header.offset_to_flare_textures)
                        texture_pointers: list[int] = []
                        for _ in range(light_header.flare_textures_count):
                            if self._reader.position() + 4 <= self._reader.size():
                                ptr = self._reader.read_uint32()
                                if ptr not in (0, 0xFFFFFFFF):
                                    texture_pointers.append(ptr)

                        # Read texture names from pointers
                        for texture_ptr in texture_pointers:
                            if texture_ptr <= self._reader.size() - 12:
                                self._reader.seek(texture_ptr)
                                texture_name = self._reader.read_terminated_string("\0", 12)
                                if texture_name:
                                    node.light.flare_textures.append(texture_name)
                    finally:
                        self._reader.seek(saved_pos)

                # Flare sizes: array of floats (4 bytes each)
                if light_header.flare_sizes_count > 0 and light_header.offset_to_flare_sizes not in (0, 0xFFFFFFFF):
                    node.light.flare_sizes = []
                    saved_pos = self._reader.position()
                    try:
                        self._reader.seek(light_header.offset_to_flare_sizes)
                        for _ in range(light_header.flare_sizes_count):
                            if self._reader.position() + 4 <= self._reader.size():
                                size = self._reader.read_single()
                                node.light.flare_sizes.append(size)
                    finally:
                        self._reader.seek(saved_pos)

                # Flare positions: array of floats (4 bytes each)
                if light_header.flare_positions_count > 0 and light_header.offset_to_flare_positions not in (0, 0xFFFFFFFF):
                    node.light.flare_positions = []
                    saved_pos = self._reader.position()
                    try:
                        self._reader.seek(light_header.offset_to_flare_positions)
                        for _ in range(light_header.flare_positions_count):
                            if self._reader.position() + 4 <= self._reader.size():
                                position = self._reader.read_single()
                                node.light.flare_positions.append(position)
                    finally:
                        self._reader.seek(saved_pos)

                # Flare color shifts: array of Vector3 (12 bytes each = 3 floats)
                if light_header.flare_colors_count > 0 and light_header.offset_to_flare_colors not in (0, 0xFFFFFFFF):
                    node.light.flare_color_shifts = []
                    saved_pos = self._reader.position()
                    try:
                        self._reader.seek(light_header.offset_to_flare_colors)
                        for _ in range(light_header.flare_colors_count):
                            if self._reader.position() + 12 <= self._reader.size():
                                r = self._reader.read_single()
                                g = self._reader.read_single()
                                b = self._reader.read_single()
                                node.light.flare_color_shifts.append((r, g, b))
                    finally:
                        self._reader.seek(saved_pos)

        # Check for EMITTER flag - nodes with EMITTER flag should be marked as EMITTER type
        #
        if bin_node.header.type_id & MDLNodeFlags.EMITTER:
            node.node_type = MDLNodeType.EMITTER
            from pykotor.resource.formats.mdl.mdl_data import MDLEmitter

            if bin_node.emitter is not None:
                node.emitter = MDLEmitter()
                # Read emitter properties in same order as MDLOps (lines 1960-1981)
                node.emitter.dead_space = bin_node.emitter.dead_space
                node.emitter.blast_radius = bin_node.emitter.blast_radius
                node.emitter.blast_length = bin_node.emitter.blast_length
                node.emitter.branch_count = bin_node.emitter.branch_count
                node.emitter.control_point_smoothing = float(bin_node.emitter.control_point_smoothing)
                node.emitter.x_grid = int(bin_node.emitter.x_grid)
                node.emitter.y_grid = int(bin_node.emitter.y_grid)
                node.emitter.spawn_type = int(bin_node.emitter.spawn_type)
                node.emitter.update = bin_node.emitter.update
                node.emitter.render = bin_node.emitter.render
                node.emitter.blend = bin_node.emitter.blend
                node.emitter.texture = bin_node.emitter.texture
                node.emitter.chunk_name = bin_node.emitter.chunk_name
                node.emitter.two_sided_texture = bin_node.emitter.twosided_texture
                node.emitter.loop = bin_node.emitter.loop
                node.emitter.render_order = int(bin_node.emitter.render_order)
                node.emitter.frame_blender = int(bin_node.emitter.frame_blending)
                node.emitter.depth_texture = bin_node.emitter.depth_texture
                # NOTE: bin_node.emitter.unknown1 (index 18) is read but not used in MDLEmitter
                # MDLOps stores it as m_bUnknown1 but doesn't expose it (line 1980)
                node.emitter.flags = bin_node.emitter.flags
                # MDLOps parses flags into individual booleans (lines 1983-1996), but we store as flags enum

        # Check for REFERENCE flag - nodes with REFERENCE flag should be marked as REFERENCE type
        if bin_node.header.type_id & MDLNodeFlags.REFERENCE:
            node.node_type = MDLNodeType.REFERENCE
            from pykotor.resource.formats.mdl.mdl_data import MDLReference

            if bin_node.reference is not None:
                node.reference = MDLReference()
                node.reference.model = bin_node.reference.model
                node.reference.reattachable = bool(bin_node.reference.reattachable)

        if bin_node.trimesh is not None:
            # Check for SKIN flag - skin nodes should use MDLSkin (mdlops:320, NODE_SKIN = 97)
            # Check for DANGLY flag - danglymesh nodes should use MDLDangly
            if bin_node.header.type_id & MDLNodeFlags.SKIN:
                node.mesh = MDLMesh()
                node.node_type = MDLNodeType.SKIN
            elif bin_node.header.type_id & MDLNodeFlags.DANGLY:
                from pykotor.resource.formats.mdl.mdl_data import MDLDangly

                node.dangly = MDLDangly()
                node.mesh = node.dangly  # MDLDangly inherits from MDLMesh
                node.node_type = MDLNodeType.DANGLYMESH
            else:
                node.mesh = MDLMesh()
                # Only set TRIMESH type if special node type flags are not set
                # A node can have both MESH and AABB flags (walkmesh with visible geometry)
                # LIGHT, EMITTER, and REFERENCE flags also take precedence over TRIMESH
                if not (bin_node.header.type_id & (MDLNodeFlags.AABB | MDLNodeFlags.LIGHT | MDLNodeFlags.EMITTER | MDLNodeFlags.REFERENCE)):
                    node.node_type = MDLNodeType.TRIMESH
            node.mesh.shadow = bool(bin_node.trimesh.has_shadow)
            # render is stored as uint8 in binary (0 or 1), convert to bool for MDLMesh
            # bool(0) = False, bool(1) = True, bool(any non-zero) = True
            node.mesh.render = bool(bin_node.trimesh.render)
            node.mesh.background_geometry = bool(bin_node.trimesh.background)
            node.mesh.has_lightmap = bool(bin_node.trimesh.has_lightmap)
            node.mesh.rotate_texture = bool(bin_node.trimesh.rotate_texture)
            node.mesh.beaming = bool(bin_node.trimesh.beaming)
            node.mesh.diffuse = Color.from_bgr_vector3(bin_node.trimesh.diffuse)
            node.mesh.ambient = Color.from_bgr_vector3(bin_node.trimesh.ambient)
            node.mesh.texture_1 = bin_node.trimesh.texture1
            node.mesh.texture_2 = bin_node.trimesh.texture2
            node.mesh.bb_min = bin_node.trimesh.bounding_box_min
            node.mesh.bb_max = bin_node.trimesh.bounding_box_max
            node.mesh.radius = bin_node.trimesh.radius
            node.mesh.average = bin_node.trimesh.average
            node.mesh.area = bin_node.trimesh.total_area
            node.mesh.transparency_hint = bin_node.trimesh.transparency_hint
            # K2 dirt fields (only present in K2 models)
            if self.game == Game.K2:
                node.mesh.dirt_enabled = bin_node.trimesh.dirt_enabled
                node.mesh.dirt_texture = bin_node.trimesh.dirt_texture
                node.mesh.dirt_worldspace = bin_node.trimesh.dirt_worldspace
                node.mesh.hologram_donotdraw = bin_node.trimesh.hologram_donotdraw
                # Legacy alias
                node.mesh.hide_in_hologram = bin_node.trimesh.hologram_donotdraw
            # Tangent space flag from MDX data bitmap
            node.mesh.tangent_space = bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TANGENT_SPACE)
            # Stored as 8 raw bytes in the binary trimesh header; normalize to a tuple[int,...] for MDLMesh.
            node.mesh.saber_unknowns = cast(
                "tuple[int, int, int, int, int, int, int, int]",
                tuple(int(b) for b in bin_node.trimesh.saber_unknowns),
            )

            # Vertex positions can be stored either in MDL (K1-style) or in MDX blocks.
            # Match MDLOps exactly: use vertex_count from header, no verification, no inference, no fallbacks
            vcount = bin_node.trimesh.vertex_count
            node.mesh.vertex_positions = []

            # Read vertices: try MDX first if valid, otherwise fall back to MDL
            vertices_read = False
            if (
                bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX)
                and self._reader_ext is not None
                and self._reader_ext.size() > 0
                and bin_node.trimesh.mdx_data_offset not in (0, 0xFFFFFFFF)
                and bin_node.trimesh.mdx_data_size > 0
                and vcount > 0
            ):
                # Read from MDX
                vertex_offset = 0 if bin_node.trimesh.mdx_vertex_offset == 0xFFFFFFFF else bin_node.trimesh.mdx_vertex_offset
                for i in range(vcount):
                    seek_pos = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size + vertex_offset
                    if seek_pos + 12 <= self._reader_ext.size():
                        self._reader_ext.seek(seek_pos)
                        node.mesh.vertex_positions.append(
                            Vector3(
                                self._reader_ext.read_single(),
                                self._reader_ext.read_single(),
                                self._reader_ext.read_single(),
                            )
                        )
                vertices_read = True

            if not vertices_read and vcount > 0 and bin_node.trimesh.vertices_offset not in (0, 0xFFFFFFFF):
                # Read from MDL
                vertices_bytes = vcount * 12
                if bin_node.trimesh.vertices_offset + vertices_bytes <= self._reader.size():
                    self._reader.seek(bin_node.trimesh.vertices_offset)
                    node.mesh.vertex_positions = [self._reader.read_vector3() for _ in range(vcount)]

            if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL) and self._reader_ext is not None and self._reader_ext.size() > 0:
                node.mesh.vertex_normals = []
            if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0) and self._reader_ext is not None and self._reader_ext.size() > 0:
                node.mesh.vertex_uv1 = []
                node.mesh.vertex_uvs = node.mesh.vertex_uv1
            if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX1) and self._reader_ext is not None and self._reader_ext.size() > 0:
                node.mesh.vertex_uv2 = []

            mdx_offset: int = bin_node.trimesh.mdx_data_offset
            mdx_block_size: int = bin_node.trimesh.mdx_data_size
            for i in range(vcount):
                if bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL) and self._reader_ext is not None and self._reader_ext.size() > 0:
                    if node.mesh.vertex_normals is None:
                        node.mesh.vertex_normals = []
                    normal_pos = mdx_offset + i * mdx_block_size + bin_node.trimesh.mdx_normal_offset
                    if normal_pos + 12 <= self._reader_ext.size():  # Need 12 bytes for Vector3
                        self._reader_ext.seek(normal_pos)
                        x, y, z = (
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                        )
                        node.mesh.vertex_normals.append(Vector3(x, y, z))
                    else:
                        # Bounds check failed - use null normal
                        node.mesh.vertex_normals.append(Vector3.from_null())

                if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0 and self._reader_ext is not None and self._reader_ext.size() > 0:
                    assert node.mesh.vertex_uv1 is not None
                    uv1_pos = mdx_offset + i * mdx_block_size + bin_node.trimesh.mdx_texture1_offset
                    if uv1_pos + 8 <= self._reader_ext.size():  # Need 8 bytes for Vector2
                        self._reader_ext.seek(uv1_pos)
                        u, v = (
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                        )
                        node.mesh.vertex_uv1.append(Vector2(u, v))
                    else:
                        # Bounds check failed - use null UV
                        node.mesh.vertex_uv1.append(Vector2(0.0, 0.0))

                if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX1 and self._reader_ext is not None and self._reader_ext.size() > 0:
                    assert node.mesh.vertex_uv2 is not None
                    uv2_pos = mdx_offset + i * mdx_block_size + bin_node.trimesh.mdx_texture2_offset
                    if uv2_pos + 8 <= self._reader_ext.size():  # Need 8 bytes for Vector2
                        self._reader_ext.seek(uv2_pos)
                        u, v = (
                            self._reader_ext.read_single(),
                            self._reader_ext.read_single(),
                        )
                        node.mesh.vertex_uv2.append(Vector2(u, v))
                    else:
                        # Bounds check failed - use null UV
                        node.mesh.vertex_uv2.append(Vector2(0.0, 0.0))

            # If we couldn't load normals (no MDX or no NORMAL flag), keep a sane default.
            if node.mesh.vertex_normals is None:
                node.mesh.vertex_normals = [Vector3.from_null() for _ in range(vcount)]

            for bin_face in bin_node.trimesh.faces:
                face = MDLFace()
                node.mesh.faces.append(face)
                face.v1 = bin_face.vertex1
                face.v2 = bin_face.vertex2
                face.v3 = bin_face.vertex3
                face.a1 = bin_face.adjacent1
                face.a2 = bin_face.adjacent2
                face.a3 = bin_face.adjacent3
                face.normal = bin_face.normal
                face.coefficient = int(bin_face.plane_coefficient)
                # Unpack material into material (low 5 bits) and smoothgroup (high bits)
                # This ensures the internal MDLFace state is canonical (split fields).
                packed = bin_face.material
                face.material = packed & 0x1F
                face.smoothgroup = packed >> 5

            # Preserve inverted_counters and indices arrays for roundtrip compatibility
            if bin_node.trimesh.inverted_counters:
                node.mesh.inverted_counters = bin_node.trimesh.inverted_counters.copy()
            if bin_node.trimesh.indices_counts:
                node.mesh.indices_counts = bin_node.trimesh.indices_counts.copy()
            if bin_node.trimesh.indices_offsets:
                node.mesh.indices_offsets = bin_node.trimesh.indices_offsets.copy()
            node.mesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count

            # Deterministically derive binary-only face payload from mesh geometry so
            # binary and ASCII parse paths converge (no ASCII syntax extensions).
            if not self._fast_load:
                _mdl_recompute_mesh_face_payload(node.mesh)

            # Read danglymesh constraints if present
            #
            if bin_node.dangly is not None and node.dangly is not None:
                node.dangly.displacement = bin_node.dangly.displacement
                node.dangly.tightness = bin_node.dangly.tightness
                node.dangly.period = bin_node.dangly.period
                # Read constraints array (offset uses offset-12 semantics, so add 12)
                # MDLOps: darray[9] = "constraints+" with template "f[4]" (line 232)
                # MDLOps: skips constraints+ if not NODE_HAS_DANGLY (line 2175: if ($i == 9 && !($nodetype & NODE_HAS_DANGLY)) {next;})
                # MDLOps: reads offset from subhead[79] + 12 (line 2176: $temp = $ref->{$node}{'subhead'}{'unpacked'}[$structs{'darray'}[$i]{'loc'} + $temp2] + 12;)
                # MDLOps: unpacks constraints as floats from "constraints+" array (line 2401: $ref->{$node}{'constraints'}[$i] = $ref->{$node}{$structs{'darray'}[9]{'name'}}{'unpacked'}[$i];)
                # MDLOps: writes constraints as pack("f", $_) for each constraint (line 7264)
                if bin_node.dangly.offset_to_contraints not in (0, 0xFFFFFFFF) and bin_node.dangly.constraints_count > 0:
                    saved_pos: int = self._reader.position()
                    try:
                        # MDLOps line 2176: offset + 12 (offset-12 semantics)
                        constraint_loc: int = bin_node.dangly.offset_to_contraints + 12
                        self._reader.seek(constraint_loc)
                        # MDLOps line 2401: constraints are floats, one per vertex
                        # MDLOps line 7264: pack("f", $_) for each constraint
                        for _ in range(bin_node.dangly.constraints_count):
                            if self._reader.position() + 4 <= self._reader.size():
                                constraint_value: float = self._reader.read_single()
                                # Store constraint as MDLConstraint object (MDLDangly.constraints expects list[MDLConstraint])
                                from pykotor.resource.formats.mdl.mdl_data import MDLConstraint

                                constraint = MDLConstraint()
                                # Store float value in constraint.type field (temporary workaround for MDLConstraint structure)
                                constraint.type = int(constraint_value * 1000000) if constraint_value != 0.0 else 0  # type: ignore[assignment]
                                node.dangly.constraints.append(constraint)
                    finally:
                        self._reader.seek(saved_pos)

        if bin_node.skin is not None:
            node.skin = MDLSkin()
            node.skin.bone_indices = bin_node.skin.bones
            node.skin.bonemap = bin_node.skin.bonemap
            node.skin.tbones = bin_node.skin.tbones
            node.skin.qbones = bin_node.skin.qbones

            if self._reader_ext is not None and self._reader_ext.size() > 0:
                assert bin_node.trimesh is not None
                for i in range(bin_node.trimesh.vertex_count):
                    vertex_bone = MDLBoneVertex()
                    node.skin.vertex_bones.append(vertex_bone)

                    mdx_offset = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size
                    bones_pos = mdx_offset + bin_node.skin.offset_to_mdx_bones
                    if bones_pos + 16 <= self._reader_ext.size():
                        self._reader_ext.seek(bones_pos)
                        t1 = self._reader_ext.read_single()
                        t2 = self._reader_ext.read_single()
                        t3 = self._reader_ext.read_single()
                        t4 = self._reader_ext.read_single()
                        vertex_bone.vertex_indices = (t1, t2, t3, t4)

                    mdx_offset = bin_node.trimesh.mdx_data_offset + i * bin_node.trimesh.mdx_data_size
                    weights_pos = mdx_offset + bin_node.skin.offset_to_mdx_weights
                    if weights_pos + 16 <= self._reader_ext.size():
                        self._reader_ext.seek(weights_pos)
                        w1 = self._reader_ext.read_single()
                        w2 = self._reader_ext.read_single()
                        w3 = self._reader_ext.read_single()
                        w4 = self._reader_ext.read_single()
                        vertex_bone.vertex_weights = (w1, w2, w3, w4)

        for child_offset in bin_node.children_offsets:
            child_node: MDLNode = self._load_node(child_offset, node)
            node.children.append(child_node)

        # Skip controllers when fast loading (not needed for rendering)
        if not self._fast_load:
            # MDLOps stores offsets as (absolute_offset - 12), but since BinaryReader has
            # set_offset(+12) applied, the raw values can be used directly without adjustment.
            controllers_base = bin_node.header.offset_to_controllers
            controller_data_base = bin_node.header.offset_to_controller_data
            for i in range(bin_node.header.controller_count):
                offset = controllers_base + i * _Controller.SIZE
                controller: MDLController = self._load_controller(
                    offset,
                    controller_data_base,
                )
                node.controllers.append(controller)

        return node

    def _load_anim(
        self,
        offset,
    ) -> MDLAnimation:
        self._reader.seek(offset)

        bin_anim: _AnimationHeader = _AnimationHeader().read(self._reader)

        bin_events: list[_EventStructure] = []
        self._reader.seek(bin_anim.offset_to_events)
        for _ in range(bin_anim.event_count):
            bin_event: _EventStructure = _EventStructure().read(self._reader)
            bin_events.append(bin_event)

        anim = MDLAnimation()

        anim.name = bin_anim.geometry.model_name
        anim.root_model = bin_anim.root
        anim.anim_length = bin_anim.duration
        anim.transition_length = bin_anim.transition

        for bin_event in bin_events:
            event = MDLEvent()
            event.name = bin_event.event_name
            event.activation_time = bin_event.activation_time
            anim.events.append(event)

        anim.root = self._load_node(bin_anim.geometry.root_node_offset, None)

        return anim

    def _load_controller(
        self,
        offset: int,
        data_offset: int,
    ) -> MDLController:
        self._reader.seek(offset)
        bin_controller: _Controller = _Controller().read(self._reader)

        row_count: int = bin_controller.row_count
        column_count: int = bin_controller.column_count

        # key_offset/data_offset are stored as uint16 float-index offsets relative to the start of the
        # controller-data block (not byte offsets). Convert to bytes when seeking.
        self._reader.seek(data_offset + (bin_controller.key_offset * 4))
        # Read time keys with bounds checking
        time_keys: list[float] = []
        bytes_per_key = 4  # Each float is 4 bytes
        for _ in range(row_count):
            # Check bounds before reading each key
            if self._reader.position() + bytes_per_key > self._reader.size():
                break
            time_keys.append(self._reader.read_single())

        # There are some special cases when reading controller data rows.
        data_pointer: int = data_offset + (bin_controller.data_offset * 4)
        self._reader.seek(data_pointer)

        # Detect bezier interpolation flag (bit 4 = 0x10) in column count
        # https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1704-1710 - Bezier flag detection
        # https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1749-1756 - Bezier data expansion (3 values per column)
        bezier_flag: int = 0x10
        is_bezier: bool = bool(column_count & bezier_flag)

        # Declare data variable once before the if/else block
        data: list[list[float]] = []

        # Orientation data stored in controllers is sometimes compressed into 4 bytes. We need to check for that and
        # uncompress the quaternion if that is the case.
        # https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1714-1719 - Compressed quaternion detection
        # Compressed quaternions use column_count=2 as a FLAG (not 2 values per row!)
        # Each compressed quaternion is stored as a single uint32, NOT uint32 + padding float
        # https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1719 - "$template .= 'L' x $_->[2]" - just row_count uint32s
        if (
            bin_controller.type_id == MDLControllerType.ORIENTATION
            and bin_controller.column_count == 2
        ):
            # Detected compressed quaternions - set the model flag
            self._mdl.compress_quaternions = 1
            for _ in range(bin_controller.row_count):
                # Check bounds before reading - need 4 bytes (just the uint32, no padding)
                if self._reader.position() + 4 > self._reader.size():
                    break
                compressed: int = self._reader.read_uint32()
                decompressed: Vector4 = _decompress_quaternion(compressed)
                data.append([decompressed.x, decompressed.y, decompressed.z, decompressed.w])
        else:
            # https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1721-1726 - Bezier data reading
            # Bezier controllers store 3 floats per column: (value, in_tangent, out_tangent)
            # Non-bezier controllers store 1 float per column
            if is_bezier:
                base_columns: int = column_count - bezier_flag
                effective_columns: int = base_columns * 3
            else:
                effective_columns = column_count

            # Ensure we have at least some columns to read
            if effective_columns <= 0:
                effective_columns = column_count & ~bezier_flag  # Strip bezier flag

            # Read controller data with bounds checking
            bytes_per_row: int = effective_columns * 4  # Each float is 4 bytes
            for _ in range(row_count):
                # Check bounds before reading each row
                if self._reader.position() + bytes_per_row > self._reader.size():
                    break
                row_data: list[float] = [
                    self._reader.read_single()
                    for _ in range(effective_columns)
                ]
                data.append(row_data)

        controller_type: int = bin_controller.type_id
        # Validate controller type - function pointer values (4273776 for K1, 4285200 for K2) indicate
        # we're reading from the wrong location (geometry header data instead of controller data).
        # Valid controller types are small integers (< 1000), so detect invalid values.
        # https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:325-405 - Valid controller types are 8, 20, 36, 76, 80, 84, 88, etc.
        if controller_type > 1000 or controller_type < 0:
            # Invalid controller type - likely reading from wrong offset, skip this controller
            # Return INVALID controller type to prevent crash
            controller_type_enum = MDLControllerType.INVALID
        else:
            try:
                controller_type_enum = MDLControllerType(controller_type)
            except ValueError:
                # Controller type not in enum, use INVALID
                controller_type_enum = MDLControllerType.INVALID

        # Handle case where we didn't read all rows due to bounds issues
        actual_row_count: int = min(len(time_keys), len(data), row_count)
        rows: list[MDLControllerRow] = [
            MDLControllerRow(time_keys[i], data[i])
            for i in range(actual_row_count)
        ]
        # https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1709 - Store bezier flag with controller
        controller = MDLController(
            controller_type_enum,
            rows,
            is_bezier=is_bezier,
        )
        return controller


class MDLBinaryWriter:
    """Binary MDL/MDX file writer.

    Writes MDL (model) and MDX (model extension) files from MDL data structures.

    References:
    ----------
        Based on swkotor.exe MDL structure:
        - LoadModel @ (K1: 0x00464200, TSL: 0x0047a570) - High-level model loader (172 bytes, 42 lines)
          * Loads MDL/MDX through IODispatcher::ReadSync
          * Manages model cache (modelsList) to avoid duplicate loads
        - CSWCCreature::LoadModel @ (K1: 0x0061b380, TSL: 0x00669ea0) - Creature model loader (842 bytes, 167 lines)
          * Loads creature models with animation base setup
          * Handles different model types: base, head, wield, head+wield, two-weapon
        - CSWCPlaceable::LoadModel @ (K1: 0x006823f0, TSL: 0x006d9721) - Placeable model loader (504 bytes, 105 lines)
          * Loads placeable models with animation base
          * Handles head hit detection ("_head_hit" node lookup)
        - CSWCCreature::UnloadModel @ (K1: 0x0060c8e0, TSL: N/A - likely inlined) - Unloads creature models (42 bytes, 19 lines)
        - CSWCObject::UnloadModel @ (K1: 0x00646650, TSL: N/A - likely inlined), @ (K1: 0x006825f0, TSL: 0x006d9721) (call site within CSWCPlaceable::LoadModel) - Additional unload functions
        - MdlNode::AsMdlNodeTriMesh @ (K1: 0x0043e400, TSL: 0x004501d0) - Converts node to trimesh type
        - Original BioWare engine binaries (swkotor.exe, swkotor2.exe)
        
        Derivations and Other Implementations:
        ----------
        https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm (Binary MDL writing paths)
        https://github.com/th3w1zard1/kotorblender/tree/master/format/mdl/writer.py (MDL writing reference)


    """

    def __init__(
        self,
        mdl: MDL,
        target: TARGET_TYPES,
        target_ext: TARGET_TYPES | None,
    ):
        self._mdl: MDL = mdl

        self._target: TARGET_TYPES = target
        self._target_ext: TARGET_TYPES | None = target_ext
        self._writer: BinaryWriterBytearray = BinaryWriter.to_bytearray()
        self._writer_ext: BinaryWriterBytearray = BinaryWriter.to_bytearray()

        self.game: Game = Game.K1

        self._name_offsets: list[int] = []
        self._anim_offsets: list[int] = []
        self._node_offsets: list[int] = []

        self._bin_anim_nodes: dict[str, _Node] = {}
        self._mdl_nodes: list[MDLNode] = []
        self._bin_nodes: list[_Node] = []
        self._bin_anims: list[_Animation] = []
        self._names: list[str] = []
        self._file_header: _ModelHeader = _ModelHeader()

    def write(
        self,
        auto_close: bool = True,
    ):
        self._mdl_nodes[:] = self._mdl.all_nodes()
        self._bin_nodes[:] = [_Node() for _ in self._mdl_nodes]
        self._bin_anims[:] = [_Animation() for _ in self._mdl.anims]
        # Node names in binary are stored in the "partnames" array and are indexed by node_id.
        # MDLOps writes `node_id` as the index into this array and writes 0 for the nodeheader's 4th short.
        # Therefore, we must keep this array in node_id order (no de-dupe).
        self._names = [n.name for n in self._mdl_nodes]

        # Determine game version: K2 models always have dirt fields in the binary format
        # If any node has dirt fields that were read (not just defaults), it's K2
        # Check if dirt fields exist and differ from defaults, or if hologram_donotdraw is set
        # Also check if any node has K2-specific features (even at defaults, their presence indicates K2)
        self.game = Game.K1
        for node in self._mdl_nodes:
            if node.mesh:
                # Check if dirt fields are present (K2 always has them, even if all zeros)
                # The presence of these fields (even with default values) indicates K2
                # But we need to check if they were actually read from binary, not just initialized
                # Since all MDLMesh instances have these fields now, we check if they differ from defaults
                # or if hologram_donotdraw is set (which is K2-only)
                # Also check if the node has been marked as having K2 features (e.g., by checking if
                # dirt fields were explicitly set, or if hologram_donotdraw was read from binary)
                if node.mesh.dirt_enabled or node.mesh.dirt_texture != 1 or node.mesh.dirt_worldspace != 1 or node.mesh.hologram_donotdraw:
                    self.game = Game.K2
                    break
                # Also check if hide_in_hologram is set (legacy alias for hologram_donotdraw)
                if node.mesh.hide_in_hologram:
                    self.game = Game.K2
                    break
                # If the node has K2-specific fields that were read (even at defaults), it's K2
                # Check if these fields differ from defaults, or if hologram_donotdraw is set (K2-only)
                # For now, we'll use a heuristic: if the model has any mesh nodes and we're writing,
                # check if the original binary had K2 function pointers by checking if dirt fields were read
                # This is imperfect, but we don't have access to the original binary's function pointers

        self._anim_offsets[:] = [0 for _ in self._bin_anims]
        self._node_offsets[:] = [0 for _ in self._bin_nodes]
        self._file_header = _ModelHeader()

        self._update_all_data()

        self._calc_top_offsets()
        self._calc_inner_offsets()

        self._write_all()

        if auto_close:
            self._writer.close()
            if self._writer_ext is not None:
                self._writer_ext.close()

    def _update_all_data(self):
        for i, bin_node in enumerate(self._bin_nodes):
            self._update_node(bin_node, self._mdl_nodes[i], node_id_override=i)

        for i, bin_anim in enumerate(self._bin_anims):
            self._update_anim(bin_anim, self._mdl.anims[i])

    def _update_node(
        self,
        bin_node: _Node,
        mdl_node: MDLNode,
        *,
        node_id_override: int | None = None,
        is_animation: bool = False,
    ):
        assert bin_node.header is not None
        bin_node.header.type_id = self._node_type(mdl_node)
        bin_node.header.position = mdl_node.position
        bin_node.header.orientation = mdl_node.orientation
        # Set children_count now so calc_size() returns correct values during _calc_top_offsets()
        # This is critical for correct node offset calculation
        actual_children_count: int = len(mdl_node.children)
        if actual_children_count > 0x7FFFFFFF:
            actual_children_count = 0x7FFFFFFF
        bin_node.header.children_count = bin_node.header.children_count2 = actual_children_count
        # MDLOps writes 0 for the nodeheader's 4th short; names come from partnames[node_id].
        bin_node.header.name_id = 0
        # Node IDs are positional within their node array (geometry or animation), not global by name.
        # When writing, always prefer the caller-provided order.
        node_id = node_id_override if node_id_override is not None else 0
        bin_node.header.node_id = node_id
        # MDLOps: padding0 (2nd uint16) is actually the supernode field.
        # If supernode is defined, use it. Otherwise default to the node index.
        # See MDLOpsM.pm line 6687-6691: $work = $i when supernode is undefined.
        bin_node.header.padding0 = node_id

        # Determine the appropriate function pointer values to write
        if self.game == Game.K1:
            if mdl_node.skin is not None:
                fp0 = _TrimeshHeader.K1_SKIN_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_SKIN_FUNCTION_POINTER1
            elif mdl_node.dangly is not None:
                fp0 = _TrimeshHeader.K1_DANGLY_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_DANGLY_FUNCTION_POINTER1
            else:
                fp0 = _TrimeshHeader.K1_FUNCTION_POINTER0
                fp1 = _TrimeshHeader.K1_FUNCTION_POINTER1
        elif mdl_node.skin is not None:
            fp0 = _TrimeshHeader.K2_SKIN_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_SKIN_FUNCTION_POINTER1
        elif mdl_node.dangly is not None:
            fp0 = _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_DANGLY_FUNCTION_POINTER1
        else:
            fp0 = _TrimeshHeader.K2_FUNCTION_POINTER0
            fp1 = _TrimeshHeader.K2_FUNCTION_POINTER1

        # Create trimesh header if node has a mesh or if node_type indicates it should have one
        # This ensures we preserve mesh structure even if mesh object is missing
        # Emitter, Light, AABB, and Skin nodes can also have mesh data
        if mdl_node.mesh is not None or mdl_node.node_type in (
            MDLNodeType.TRIMESH,
            MDLNodeType.DANGLYMESH,
            MDLNodeType.EMITTER,
            MDLNodeType.LIGHT,
            MDLNodeType.AABB,
            MDLNodeType.SKIN,
        ):
            # If mesh is None but node_type indicates mesh, create empty mesh to preserve structure
            if mdl_node.mesh is None:
                from pykotor.resource.formats.mdl.mdl_data import MDLMesh

                mdl_node.mesh = MDLMesh()
            bin_node.trimesh = _TrimeshHeader()
            bin_node.trimesh.function_pointer0 = fp0
            bin_node.trimesh.function_pointer1 = fp1
            bin_node.trimesh.average = mdl_node.mesh.average
            # Create dangly header if this is a danglymesh node
            if mdl_node.dangly is not None:
                bin_node.dangly = _DanglymeshHeader()
                bin_node.dangly.displacement = mdl_node.dangly.displacement
                bin_node.dangly.tightness = mdl_node.dangly.tightness
                bin_node.dangly.period = mdl_node.dangly.period
                bin_node.dangly.constraints_count = len(mdl_node.dangly.constraints)
                bin_node.dangly.constraints_count2 = len(mdl_node.dangly.constraints)
                # Store constraints for writing later (store on bin_node for access during write)
                bin_node._dangly_constraints = list(mdl_node.dangly.constraints)

            # Store AABB tree for writing later if this is an AABB node
            # Always initialize _aabb_nodes when aabb exists, even if empty, to match AABB flag behavior
            if mdl_node.aabb is not None:
                if mdl_node.aabb.aabbs:
                    bin_node._aabb_nodes = list(mdl_node.aabb.aabbs)
                else:
                    bin_node._aabb_nodes = []
                bin_node.trimesh.offset_to_aabb = 0  # Will be calculated during offset calculation
            bin_node.trimesh.radius = mdl_node.mesh.radius
            bin_node.trimesh.bounding_box_max = mdl_node.mesh.bb_max
            bin_node.trimesh.bounding_box_min = mdl_node.mesh.bb_min
            bin_node.trimesh.total_area = mdl_node.mesh.area
            bin_node.trimesh.texture1 = mdl_node.mesh.texture_1
            bin_node.trimesh.texture2 = mdl_node.mesh.texture_2
            bin_node.trimesh.diffuse = mdl_node.mesh.diffuse.bgr_vector3()
            bin_node.trimesh.ambient = mdl_node.mesh.ambient.bgr_vector3()
            # render is stored as uint8 in binary (0 or 1), convert from bool to int
            # Ensure we preserve the exact value: False -> 0, True -> 1
            bin_node.trimesh.render = 1 if mdl_node.mesh.render else 0
            bin_node.trimesh.transparency_hint = mdl_node.mesh.transparency_hint
            bin_node.trimesh.uv_jitter = mdl_node.mesh.uv_jitter
            bin_node.trimesh.uv_speed = mdl_node.mesh.uv_jitter_speed
            bin_node.trimesh.uv_direction.x = mdl_node.mesh.uv_direction_x
            bin_node.trimesh.uv_direction.y = mdl_node.mesh.uv_direction_y
            # Flags are stored as uint8 in binary (0 or 1), convert from bool to int
            # Ensure we preserve the exact value: False -> 0, True -> 1
            bin_node.trimesh.has_lightmap = 1 if mdl_node.mesh.has_lightmap else 0
            bin_node.trimesh.rotate_texture = 1 if mdl_node.mesh.rotate_texture else 0
            bin_node.trimesh.background = 1 if mdl_node.mesh.background_geometry else 0
            bin_node.trimesh.has_shadow = 1 if mdl_node.mesh.shadow else 0
            bin_node.trimesh.beaming = 1 if mdl_node.mesh.beaming else 0
            # render is already set above, no need to set it again
            # K2 dirt fields (only present in K2 models)
            if self.game == Game.K2:
                bin_node.trimesh.dirt_enabled = mdl_node.mesh.dirt_enabled
                bin_node.trimesh.dirt_texture = mdl_node.mesh.dirt_texture if mdl_node.mesh.dirt_texture else 1
                bin_node.trimesh.dirt_worldspace = mdl_node.mesh.dirt_worldspace if mdl_node.mesh.dirt_worldspace else 1
                # Only use hologram_donotdraw, not hide_in_hologram (which is just a legacy alias)
                # hide_in_hologram is set from hologram_donotdraw when reading, so they should match
                # Write as uint32 (1 or 0), but _TrimeshHeader stores it as bool, so convert
                bin_node.trimesh.hologram_donotdraw = bool(mdl_node.mesh.hologram_donotdraw)
            bin_node.trimesh.saber_unknowns = bytes(mdl_node.mesh.saber_unknowns)

            # Set vertex_count from vertex_positions length - match MDLOps exactly
            # No fallbacks, no inference - use what's in the data
            if mdl_node.mesh.vertex_positions:
                bin_node.trimesh.vertex_count = len(mdl_node.mesh.vertex_positions)
                bin_node.trimesh.vertices = mdl_node.mesh.vertex_positions
            else:
                bin_node.trimesh.vertex_count = 0
                bin_node.trimesh.vertices = []

            # Preserve indices arrays and inverted_counters if they were read from the original binary
            # These are needed for MDLOps compatibility
            if mdl_node.mesh.inverted_counters:
                bin_node.trimesh.inverted_counters = list(mdl_node.mesh.inverted_counters)
                bin_node.trimesh.counters_count = bin_node.trimesh.counters_count2 = len(bin_node.trimesh.inverted_counters)
            else:
                # If not preserved, use empty arrays (MDLOps will regenerate them)
                bin_node.trimesh.inverted_counters = []
                bin_node.trimesh.counters_count = bin_node.trimesh.counters_count2 = 0

            # Preserve indices arrays if available from original binary
            bin_node.trimesh.indices_counts = list(mdl_node.mesh.indices_counts)
            bin_node.trimesh.indices_offsets = list(mdl_node.mesh.indices_offsets)
            bin_node.trimesh.indices_counts_count = bin_node.trimesh.indices_counts_count2 = len(bin_node.trimesh.indices_counts)
            # Preserve original indices_offsets_count from binary header if available, otherwise use array length
            original_count = int(mdl_node.mesh.indices_offsets_count)
            if original_count > 0:
                bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = original_count
                if not bin_node.trimesh.indices_offsets:
                    bin_node.trimesh.indices_offsets = [0] * original_count
            else:
                bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = len(bin_node.trimesh.indices_offsets)

            bin_node.trimesh.faces_count = bin_node.trimesh.faces_count2 = len(mdl_node.mesh.faces)
            for face in mdl_node.mesh.faces:
                bin_face = _Face()
                bin_node.trimesh.faces.append(bin_face)
                bin_face.vertex1 = face.v1
                bin_face.vertex2 = face.v2
                bin_face.vertex3 = face.v3
                bin_face.adjacent1 = face.a1
                bin_face.adjacent2 = face.a2
                bin_face.adjacent3 = face.a3
                # Repack surface material (low 5 bits) and smoothgroup (high bits)
                surface = face.material & 0x1F
                smooth = face.smoothgroup
                bin_face.material = surface | (smooth << 5)
                bin_face.plane_coefficient = face.coefficient
                bin_face.normal = face.normal

        # Skin header + extra blocks (bonemap/qbones/tbones) + per-vertex MDX bones/weights.
        if mdl_node.skin:
            bin_node.skin = _SkinmeshHeader()
            skin = mdl_node.skin

            # Bone indices table in header is fixed-size (16 uint16).
            bones = list(skin.bone_indices)
            bones16: list[int] = [(int(b) if i < len(bones) else -1) for i, b in enumerate(bones[:16] + [-1] * 16)]
            bin_node.skin.bones = tuple(int(b) for b in bones16[:16])

            # Bonemap + bind pose transforms.
            bin_node.skin.bonemap = [int(x) for x in skin.bonemap]
            bin_node.skin.bonemap_count = len(bin_node.skin.bonemap)

            qbones = list(skin.qbones)
            tbones = list(skin.tbones)
            if not qbones and self._mdl_nodes:
                qbones = [Vector4.from_null() for _ in self._mdl_nodes]
            if not tbones and self._mdl_nodes:
                tbones = [Vector3.from_null() for _ in self._mdl_nodes]
            bin_node.skin.qbones = list(qbones)
            bin_node.skin.tbones = list(tbones)
            bin_node.skin.qbones_count = bin_node.skin.qbones_count2 = len(bin_node.skin.qbones)
            bin_node.skin.tbones_count = bin_node.skin.tbones_count2 = len(bin_node.skin.tbones)

            # Unknown0 block currently not modeled.
            bin_node.skin.unknown0_count = bin_node.skin.unknown0_count2 = 0
            bin_node.skin.offset_to_unknown0 = 0

            # Offsets to bonemap/qbones/tbones are filled in _calc_skin_offsets().
            bin_node.skin.offset_to_bonemap = 0
            bin_node.skin.offset_to_qbones = 0
            bin_node.skin.offset_to_tbones = 0

            # MDX per-vertex bones/weights offsets are filled in _update_mdx().
            bin_node.skin.offset_to_mdx_bones = 0
            bin_node.skin.offset_to_mdx_weights = 0

        # Light header data
        if mdl_node.light is not None:
            bin_node.light = _LightHeader()
            light = mdl_node.light
            # Copy basic light properties
            bin_node.light.ambient_only = 1 if light.ambient_only else 0
            bin_node.light.dynamic_type = int(light.dynamic_type)
            bin_node.light.shadow = 1 if light.shadow else 0
            bin_node.light.flare = 1 if light.flare else 0
            bin_node.light.light_priority = light.light_priority
            bin_node.light.fading_light = 1 if light.fading_light else 0
            bin_node.light.flare_radius = light.flare_radius
            bin_node.light.affect_dynamic = 0  # TODO: preserve if available in MDLLight
            # Flare data offsets and counts will be calculated elsewhere during writing
            # Initialize to 0 for now - they'll be set when flare data is written
            bin_node.light.offset_to_unknown0 = 0
            bin_node.light.unknown0_count = 0
            bin_node.light.unknown0_count2 = 0
            bin_node.light.offset_to_flare_sizes = 0
            bin_node.light.flare_sizes_count = len(light.flare_sizes)
            bin_node.light.flare_sizes_count2 = bin_node.light.flare_sizes_count
            bin_node.light.offset_to_flare_positions = 0
            bin_node.light.flare_positions_count = len(light.flare_positions)
            bin_node.light.flare_positions_count2 = bin_node.light.flare_positions_count
            bin_node.light.offset_to_flare_colors = 0
            bin_node.light.flare_colors_count = len(light.flare_color_shifts)
            bin_node.light.flare_colors_count2 = bin_node.light.flare_colors_count
            bin_node.light.offset_to_flare_textures = 0
            bin_node.light.flare_textures_count = len(light.flare_textures)
            bin_node.light.flare_textures_count2 = bin_node.light.flare_textures_count

        # Emitter header data
        # Create emitter header if node has emitter data or if node_type indicates it should be an emitter
        if mdl_node.emitter is not None or mdl_node.node_type == MDLNodeType.EMITTER:
            if not mdl_node.emitter:
                from pykotor.resource.formats.mdl.mdl_data import MDLEmitter

                mdl_node.emitter = MDLEmitter()
            bin_node.emitter = _EmitterHeader()
            emitter = mdl_node.emitter
            bin_node.emitter.dead_space = emitter.dead_space
            bin_node.emitter.blast_radius = emitter.blast_radius
            bin_node.emitter.blast_length = emitter.blast_length
            bin_node.emitter.branch_count = emitter.branch_count
            bin_node.emitter.control_point_smoothing = int(emitter.control_point_smoothing)
            bin_node.emitter.x_grid = int(emitter.x_grid)
            bin_node.emitter.y_grid = int(emitter.y_grid)
            bin_node.emitter.spawn_type = int(emitter.spawn_type)
            bin_node.emitter.update = emitter.update
            bin_node.emitter.render = emitter.render
            bin_node.emitter.blend = emitter.blend
            bin_node.emitter.texture = emitter.texture
            bin_node.emitter.chunk_name = emitter.chunk_name
            bin_node.emitter.twosided_texture = emitter.two_sided_texture
            bin_node.emitter.loop = emitter.loop
            # MDLOps encodes renderorder as uint16 and frame blending as uint8.
            ro = int(emitter.render_order)
            if ro < 0:
                ro = 0
            if ro > 0xFFFF:
                ro = 0xFFFF
            bin_node.emitter.render_order = ro
            fb = int(emitter.frame_blender)
            if fb < 0:
                fb = 0
            if fb > 0xFF:
                fb = 0xFF
            bin_node.emitter.frame_blending = fb
            bin_node.emitter.depth_texture = emitter.depth_texture
            # MDLOps writes this byte as 0 (m_bUnknown1 in perl).
            bin_node.emitter.unknown1 = 0
            bin_node.emitter.flags = emitter.flags

        # Reference header data
        if mdl_node.reference is not None:
            bin_node.reference = _ReferenceHeader()
            reference = mdl_node.reference
            bin_node.reference.model = reference.model
            bin_node.reference.reattachable = 1 if reference.reattachable else 0

        # Controller key/data offsets are stored as uint16 *byte offsets* relative to the start of
        # the controller-data block (header.offset_to_controller_data).
        #
        # Layout in controller-data block:
        #   [time keys (row_count floats)] + [row data (row_count * data_floats_per_row floats)]
        #
        # References:
        #   - https://github.com/th3w1zard1/mdlops/tree/master/MDLOpsM.pm:1649-1778
        #   - 
        cur_float_offset = 0
        for mdl_controller in mdl_node.controllers:
            bin_controller = _Controller()
            bin_controller.type_id = mdl_controller.controller_type
            bin_controller.row_count = len(mdl_controller.rows)
            if bin_controller.row_count == 0:
                continue

            first_row = mdl_controller.rows[0]
            data_floats_per_row = len(first_row.data)
            if data_floats_per_row < 0:
                data_floats_per_row = 0

            # Handle compressed quaternions for orientation controllers
            # If compress_quaternions is set and this is an orientation controller with 4 floats per row,
            # set column_count to 2 (compressed quaternions use 2 columns: compressed uint32 + padding)
            if self._mdl.compress_quaternions == 1 and mdl_controller.controller_type == MDLControllerType.ORIENTATION and data_floats_per_row == 4:
                bin_controller.column_count = 2  # Compressed quaternions use 2 columns
            # Encode bezier flag in column_count bit 4 (16) as per mdlops.
            # For bezier controllers, each logical column stores 3 floats per row.
            elif mdl_controller.is_bezier:
                logical_cols = data_floats_per_row // 3 if data_floats_per_row >= 3 else data_floats_per_row
                bin_controller.column_count = int(logical_cols) | 16
            else:
                bin_controller.column_count = int(data_floats_per_row)

            # MDLOps uses specific values for unknown0 and unknown1 based on controller type and context.
            # See MDLOpsM.pm lines 7490-7556 for the complete logic.
            ctrl_type = mdl_controller.controller_type
            node_type = bin_node.header.type_id

            if is_animation:
                # Animation controllers use different unknown0 values
                if ctrl_type == MDLControllerType.POSITION:
                    bin_controller.unknown0 = 16
                    bin_controller.unknown1 = b"\x00\x00\x00"
                elif ctrl_type == MDLControllerType.ORIENTATION:
                    bin_controller.unknown0 = 28
                    bin_controller.unknown1 = b"\x00\x00\x00"
                else:
                    bin_controller.unknown0 = 0xFFFF
                    bin_controller.unknown1 = b"\x00\x00\x00"
            else:
                # Geometry controllers
                bin_controller.unknown0 = 0xFFFF  # Always -1 for geometry
                if ctrl_type == MDLControllerType.POSITION:
                    bin_controller.unknown1 = b"\x57\x49\x00"  # "WI"
                elif ctrl_type == MDLControllerType.ORIENTATION:
                    bin_controller.unknown1 = b"\x39\x47\x00"  # "9G"
                elif ctrl_type in (132, MDLControllerType.SELFILLUMCOLOR):  # ALPHA=132, SELFILLUMCOLOR=100
                    bin_controller.unknown1 = b"\xe3\x77\x11"  # 227,119,17
                elif ctrl_type == MDLControllerType.SCALE:  # 36
                    bin_controller.unknown1 = b"\x32\x12\x00"  # 50,18,0
                elif (node_type == MDLNodeFlags.LIGHT or True) and ctrl_type in (MDLControllerType.RADIUS, MDLControllerType.MULTIPLIER, MDLControllerType.COLOR):
                    # Light controllers: radius(88), multiplier(140), color(76)
                    bin_controller.unknown1 = b"\xff\x72\x11"  # 255,114,17
                elif node_type & MDLNodeFlags.EMITTER:
                    # Emitter node controllers
                    bin_controller.unknown1 = b"\x63\x79\x11"  # 99,121,17
                else:
                    bin_controller.unknown1 = b"\x00\x00\x00"

            # Offsets are float-index offsets into the controller-data array.
            bin_controller.key_offset = cur_float_offset
            bin_controller.data_offset = cur_float_offset + bin_controller.row_count

            # Adjust float offset calculation for compressed quaternions
            # Compressed quaternions use 1 float per row (just the uint32 reinterpreted as float)
            if self._mdl.compress_quaternions == 1 and mdl_controller.controller_type == MDLControllerType.ORIENTATION and data_floats_per_row == 4:
                # Compressed quaternions: 1 float per row (compressed uint32 as float)
                # Plus row_count for time keys
                cur_float_offset += bin_controller.row_count + bin_controller.row_count
            else:
                cur_float_offset += bin_controller.row_count + (bin_controller.row_count * data_floats_per_row)
            bin_node.w_controllers.append(bin_controller)

        bin_node.w_controller_data = []
        for controller in mdl_node.controllers:
            for row in controller.rows:
                bin_node.w_controller_data.append(row.time)
            for row in controller.rows:
                # Handle compressed quaternions for orientation controllers
                # If compress_quaternions is set and this is an orientation controller with 4 floats per row,
                # compress the quaternion data
                if self._mdl.compress_quaternions == 1 and controller.controller_type == MDLControllerType.ORIENTATION and len(row.data) == 4:
                    # Compress quaternion (x, y, z, w) into a single uint32
                    quat = Vector4(row.data[0], row.data[1], row.data[2], row.data[3])
                    compressed = _compress_quaternion(quat)
                    # Reinterpret uint32 as float (same bits, NOT numeric conversion)
                    # MDLOps stores compressed quaternions as raw uint32 bytes in the float array
                    import struct

                    compressed_as_float = struct.unpack("<f", struct.pack("<I", compressed))[0]
                    bin_node.w_controller_data.append(compressed_as_float)
                    # MDLOps does NOT write a padding float - column_count=2 is just a flag
                else:
                    bin_node.w_controller_data.extend(row.data)

        controller_count_actual = len(mdl_node.controllers)
        controller_count_clamped = min(controller_count_actual, 0x7FFFFFFF)
        bin_node.header.controller_count = bin_node.header.controller_count2 = controller_count_clamped
        # Clamp controller_data_length to prevent Perl from interpreting it as negative (values >= 2^31)
        # MDLOps reads this as a signed integer, so we must ensure it's < 2^31
        # If the data is too large, truncate it to match the clamped length to prevent MDLOps from reading too much
        controller_data_length: int = len(bin_node.w_controller_data)
        if controller_data_length > 0x7FFFFFFF:
            # Truncate w_controller_data to match the clamped length to prevent MDLOps "Out of memory" errors
            # MDLOps will read exactly controller_data_length floats, so we must write exactly that many
            bin_node.w_controller_data = bin_node.w_controller_data[:0x7FFFFFFF]
            controller_data_length = 0x7FFFFFFF
        bin_node.header.controller_data_length = bin_node.header.controller_data_length2 = controller_data_length

    def _update_anim(
        self,
        bin_anim: _Animation,
        mdl_anim: MDLAnimation,
    ):
        if self.game == Game.K1:
            bin_anim.header.geometry.function_pointer0 = _GeometryHeader.K1_ANIM_FUNCTION_POINTER0
            bin_anim.header.geometry.function_pointer1 = _GeometryHeader.K1_ANIM_FUNCTION_POINTER1
        else:
            bin_anim.header.geometry.function_pointer0 = _GeometryHeader.K2_ANIM_FUNCTION_POINTER0
            bin_anim.header.geometry.function_pointer1 = _GeometryHeader.K2_ANIM_FUNCTION_POINTER1

        bin_anim.header.geometry.geometry_type = 5
        bin_anim.header.geometry.model_name = mdl_anim.name
        bin_anim.header.geometry.node_count = 0
        bin_anim.header.duration = mdl_anim.anim_length
        bin_anim.header.transition = mdl_anim.transition_length
        bin_anim.header.root = mdl_anim.root_model
        event_count_actual = len(mdl_anim.events)
        event_count_clamped = min(event_count_actual, 0x7FFFFFFF)
        bin_anim.header.event_count = bin_anim.header.event_count2 = event_count_clamped

        for mdl_event in mdl_anim.events:
            bin_event = _EventStructure()
            bin_event.event_name = mdl_event.name
            bin_event.activation_time = mdl_event.activation_time
            bin_anim.events.append(bin_event)

        all_nodes: list[MDLNode] = mdl_anim.all_nodes()
        bin_nodes: list[_Node] = []
        # Animation nodes share the same name table (partnames) as geometry nodes.
        # The node_id must match the geometry node with the same name.
        # Build a name -> node_id mapping from geometry nodes.
        geom_name_to_id: dict[str, int] = {name: idx for idx, name in enumerate(self._names)}
        for mdl_node in all_nodes:
            bin_node = _Node()
            # Look up node_id from geometry node name, default to 0 if not found
            node_id = geom_name_to_id.get(mdl_node.name, 0)
            self._update_node(bin_node, mdl_node, node_id_override=node_id, is_animation=True)
            bin_nodes.append(bin_node)
        bin_anim.w_nodes = bin_nodes

    def _update_mdx(
        self,
        bin_node: _Node,
        mdl_node: MDLNode,
    ):
        assert bin_node.trimesh is not None
        assert mdl_node.mesh is not None

        bin_node.trimesh.mdx_data_offset = self._writer_ext.size()

        # Initialize all MDX offset fields to 0xFFFFFFFF to indicate "not present"
        # MDLOps uses -1 (0xFFFFFFFF) as the sentinel for unused offsets
        bin_node.trimesh.mdx_vertex_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_normal_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_color_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_texture1_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_texture2_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_uv3_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_uv4_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_tangent_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_unknown_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_unknown2_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_unknown3_offset = 0xFFFFFFFF
        bin_node.trimesh.mdx_data_bitmap = 0

        # MDLOps decompiler expects vertex coordinates to be present in MDX rows when an MDX is available,
        # keyed by MDXDataBitmap's VERTEX bit and mdxvertcoordsloc (offset 0).
        #
        # Without this, MDLOps will output `verts N` but omit the vertex coordinate list entirely.
        suboffset = 0
        bin_node.trimesh.mdx_vertex_offset = suboffset
        bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.VERTEX
        suboffset += 12

        if mdl_node.mesh.vertex_normals:
            bin_node.trimesh.mdx_normal_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.NORMAL
            suboffset += 12

        # Use vertex_count from trimesh header, but prefer vertex_positions length if available
        # This ensures we write the correct number of vertices
        vertex_positions_len = len(mdl_node.mesh.vertex_positions) if mdl_node.mesh.vertex_positions else 0
        vcount = vertex_positions_len if vertex_positions_len > 0 else bin_node.trimesh.vertex_count
        # Ensure vcount matches vertex_positions length if vertex_positions exists
        if vertex_positions_len > 0 and vcount != vertex_positions_len:
            vcount = vertex_positions_len
            bin_node.trimesh.vertex_count = vcount
        # MDLOps requires texture vertex data in MDX if texture name is set
        # Check both list existence and non-empty to ensure we have valid UV data
        uv1_len = len(mdl_node.mesh.vertex_uv1) if mdl_node.mesh.vertex_uv1 else 0
        uv2_len = len(mdl_node.mesh.vertex_uv2) if mdl_node.mesh.vertex_uv2 else 0
        has_uv1 = mdl_node.mesh.vertex_uv1 is not None and uv1_len == vcount and vcount > 0
        has_uv2 = mdl_node.mesh.vertex_uv2 is not None and uv2_len == vcount and vcount > 0

        # Only set TEX0 flag if texture name is valid (not None, not empty, not "NULL")
        if has_uv1:
            bin_node.trimesh.mdx_texture1_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEX0
            if _DEBUG_MDL:
                print(f"DEBUG _update_mdx: Node {mdl_node.name} has_uv1=True texture1={mdl_node.mesh.texture_1} bitmap=0x{bin_node.trimesh.mdx_data_bitmap:08X} TEX0={bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0)} texture1_offset={bin_node.trimesh.mdx_texture1_offset}")
            assert bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0, f"Failed to set TEX0 flag for node {mdl_node.name}"
            suboffset += 8
        elif (  # has_texture1
            mdl_node.mesh.texture_1 is not None
            and mdl_node.mesh.texture_1.strip() != ""
            and mdl_node.mesh.texture_1.upper() != "NULL"
        ) and vcount > 0:
            # Texture name exists but no valid UV data - generate default UV coordinates
            # This ensures MDLOps can find tverts data when it reads the binary
            if not mdl_node.mesh.vertex_uv1 or len(mdl_node.mesh.vertex_uv1) != vcount:
                mdl_node.mesh.vertex_uv1 = [Vector2(0.0, 0.0) for _ in range(vcount)]
            bin_node.trimesh.mdx_texture1_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEX0
            if _DEBUG_MDL:
                print(f"DEBUG _update_mdx: Node {mdl_node.name} has_uv1=False texture1={mdl_node.mesh.texture_1} vcount={vcount} generated default UVs bitmap=0x{bin_node.trimesh.mdx_data_bitmap:08X} TEX0={bool(bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0)}")
            suboffset += 8

        # Only set TEX1 flag if texture name is valid (not None, not empty, not "NULL")
        if has_uv2:
            bin_node.trimesh.mdx_texture2_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEX1
            suboffset += 8
        elif (  # has_texture2
            mdl_node.mesh.texture_2 is not None
            and mdl_node.mesh.texture_2.strip() != ""
            and mdl_node.mesh.texture_2.upper() != "NULL"
        ) and vcount > 0:
            # Texture name exists but no valid UV data - generate default UV coordinates
            if not mdl_node.mesh.vertex_uv2 or len(mdl_node.mesh.vertex_uv2) != vcount:
                mdl_node.mesh.vertex_uv2 = [Vector2(0.0, 0.0) for _ in range(vcount)]
            bin_node.trimesh.mdx_texture2_offset = suboffset
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TEX1
            suboffset += 8

        # Tangent space flag (for bump/normal mapping)
        # The TANGENT_SPACE flag is just a hint - actual tangent/bitangent vectors are calculated at runtime
        # We just need to preserve the flag from the original binary
        if mdl_node.mesh.tangent_space:
            bin_node.trimesh.mdx_data_bitmap |= _MDXDataFlags.TANGENT_SPACE
            # NOTE: mdx_tangent_offset is not used when only the flag is set (tangent data is calculated, not stored)

        # Skin nodes store per-vertex bone indices + weights (4 floats each) in MDX.
        if mdl_node.skin is not None and bin_node.skin is not None:
            bin_node.skin.offset_to_mdx_bones = suboffset
            suboffset += 16
            bin_node.skin.offset_to_mdx_weights = suboffset
            suboffset += 16

        # mdx_data_size is the size of ONE vertex's MDX data block (used for calculating offsets when reading)
        # This includes all per-vertex data (normals, UVs, skin data) but NOT padding
        bin_node.trimesh.mdx_data_size = suboffset

        # Write MDX data based on bitmap flags, not just list existence
        # This ensures we only write data that's actually in the MDX structure
        # Write per-vertex data for all vertices (use vcount from header, not vertex_positions length)
        for i in range(vcount):
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.VERTEX:
                # Use vertex from vertex_positions if available, otherwise use null vertex
                position = (
                    mdl_node.mesh.vertex_positions[i]
                    if (mdl_node.mesh.vertex_positions and i < len(mdl_node.mesh.vertex_positions))
                    else Vector3.from_null()
                )
                self._writer_ext.write_vector3(position)
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.NORMAL:
                # Only write normals if they're actually in MDX (bitmap flag set)
                norm = (
                    mdl_node.mesh.vertex_normals[i]
                    if (mdl_node.mesh.vertex_normals and i < len(mdl_node.mesh.vertex_normals))
                    else Vector3.from_null()
                )
                self._writer_ext.write_vector3(norm)
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX0:
                # Only write UV1 if it's actually in MDX (bitmap flag set)
                uv1 = (
                    mdl_node.mesh.vertex_uv1[i]
                    if (mdl_node.mesh.vertex_uv1 and i < len(mdl_node.mesh.vertex_uv1))
                    else Vector2(0.0, 0.0)
                )
                self._writer_ext.write_vector2(uv1)
            if bin_node.trimesh.mdx_data_bitmap & _MDXDataFlags.TEX1:
                # Only write UV2 if it's actually in MDX (bitmap flag set)
                uv2 = (
                    mdl_node.mesh.vertex_uv2[i]
                    if (mdl_node.mesh.vertex_uv2 and i < len(mdl_node.mesh.vertex_uv2))
                    else Vector2(0.0, 0.0)
                )
                self._writer_ext.write_vector2(uv2)

            if mdl_node.skin and bin_node.skin is not None:
                # Bone indices/weights are stored as 4 floats each.
                vb = None
                try:
                    vb = mdl_node.skin.vertex_bones[i]
                except Exception:
                    vb = None
                if vb is None:
                    idxs = (-1.0, -1.0, -1.0, -1.0)
                    wts = (0.0, 0.0, 0.0, 0.0)
                else:
                    idxs = tuple(float(x) for x in vb.vertex_indices)
                    raw_weights = tuple(float(x) for x in vb.vertex_weights)
                    total = raw_weights[0] + raw_weights[1] + raw_weights[2] + raw_weights[3]
                    if total and abs(total - 1.0) > 1e-4:
                        # Normalize to sum to 1.0 like MDLOps postprocessnodes
                        inv = 1.0 / total
                        wts = tuple(w * inv for w in raw_weights)
                    else:
                        wts = raw_weights
                for x in idxs:
                    self._writer_ext.write_single(float(x))
                for w in wts:
                    self._writer_ext.write_single(float(w))

        # MDX terminator row + alignment: mirror MDLOps
        row_floats: int = max(0, int(bin_node.trimesh.mdx_data_size / 4))
        sentinel: float = 10_000_000.0 if mdl_node.skin is None else 1_000_000.0
        zeros_to_add: int = max(0, row_floats - 3 - (0 if mdl_node.skin is None else 8))  # type: ignore[operator]
        # Terminator row
        for value in (sentinel, sentinel, sentinel):
            self._writer_ext.write_single(value)
        for _ in range(zeros_to_add):
            self._writer_ext.write_single(0.0)
        # Extra padding block for skin meshes
        if mdl_node.skin is not None:
            for value in (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0):
                self._writer_ext.write_single(value)
        # 16-byte alignment padding (MDLOps alignment rule)
        mdx_written: int = self._writer_ext.size() - bin_node.trimesh.mdx_data_offset
        alignment_padding: int = (16 - (mdx_written % 16)) % 16
        if alignment_padding > 0:
            pad_floats: int = alignment_padding // 4
            for _ in range(pad_floats):
                self._writer_ext.write_single(0.0)

    def _calc_top_offsets(self):
        offset_to_name_offsets: int = _ModelHeader.SIZE

        offset_to_names: int = offset_to_name_offsets + 4 * len(self._names)
        name_offset: int = offset_to_names
        for name in self._names:
            self._name_offsets.append(name_offset)
            name_offset += len(name) + 1

        offset_to_anim_offsets: int = name_offset
        offset_to_anims: int = name_offset + (4 * len(self._bin_anims))
        anim_offset: int = offset_to_anims
        for i, anim in enumerate(self._bin_anims):
            self._anim_offsets[i] = anim_offset
            anim_offset += anim.size()

        offset_to_node_offset: int = anim_offset
        node_offset: int = offset_to_node_offset
        for i, bin_node in enumerate(self._bin_nodes):
            self._node_offsets[i] = node_offset
            node_offset += bin_node.calc_size(self.game)

        self._file_header.geometry.root_node_offset = offset_to_node_offset
        self._file_header.offset_to_name_offsets = offset_to_name_offsets
        self._file_header.offset_to_super_root = 0
        self._file_header.offset_to_animations = offset_to_anim_offsets

    def _calc_inner_offsets(self):
        for i, bin_anim in enumerate(self._bin_anims):
            bin_anim.header.offset_to_events = self._anim_offsets[i] + bin_anim.events_offset()
            bin_anim.header.geometry.root_node_offset = self._anim_offsets[i] + bin_anim.nodes_offset()

            node_offsets: list[int] = []
            node_offset: int = self._anim_offsets[i] + bin_anim.nodes_offset()
            for bin_node in bin_anim.w_nodes:
                node_offsets.append(node_offset)
                node_offset += bin_node.calc_size(self.game)

            self._calc_node_offsets_for_context(
                bin_nodes=bin_anim.w_nodes,
                bin_offsets=node_offsets,
                mdl_nodes=self._mdl.anims[i].all_nodes(),
            )

        self._calc_node_offsets_for_context(
            bin_nodes=self._bin_nodes,
            bin_offsets=self._node_offsets,
            mdl_nodes=self._mdl_nodes,
        )

    def _calc_node_offsets_for_context(
        self,
        *,
        bin_nodes: list[_Node],
        bin_offsets: list[int],
        mdl_nodes: list[MDLNode],
    ) -> None:
        """Populate per-node child offsets + header offsets for a single node array (geometry OR animation)."""
        if len(bin_nodes) != len(mdl_nodes):
            raise ValueError(f"bin_nodes and mdl_nodes length mismatch ({len(bin_nodes)} vs {len(mdl_nodes)})")

        idx_by_id: dict[int, int] = {
            id(n): i
            for i, n in enumerate(mdl_nodes)
        }
        parent_by_idx: dict[int, int] = {}
        for parent_idx, parent in enumerate(mdl_nodes):
            for child in parent.children:
                child_idx = idx_by_id.get(id(child))
                if child_idx is not None:
                    parent_by_idx[child_idx] = parent_idx

        for i in range(len(bin_nodes)):
            bin_node: _Node = bin_nodes[i]
            mdl_node: MDLNode = mdl_nodes[i]
            node_offset: int = bin_offsets[i]

            # Child offsets from the MDL node tree
            bin_node.children_offsets = []
            for child in mdl_node.children:
                child_idx: int | None = idx_by_id.get(id(child))
                if child_idx is not None:
                    bin_node.children_offsets.append(bin_offsets[child_idx])

            assert bin_node.header is not None
            # Ensure children_count matches the actual number of children_offsets
            # This is critical for MDLOps compatibility - the count must match the array length
            actual_children_count: int = len(bin_node.children_offsets)
            # Clamp to prevent Perl from interpreting it as negative (values >= 2^31)
            if actual_children_count > 0x7FFFFFFF:
                actual_children_count = 0x7FFFFFFF
            bin_node.header.children_count = bin_node.header.children_count2 = actual_children_count

            # MDLOps writes 0 for controller offsets when both controller_count and
            # controller_data_length are 0 (no controllers at all)
            # MDLOps stores offsets as (absolute_offset - 12) in the file format
            #
            if bin_node.header.controller_count == 0 and bin_node.header.controller_data_length == 0:
                bin_node.header.offset_to_controllers = 0
                bin_node.header.offset_to_controller_data = 0
            else:
                absolute_controllers_offset: int = node_offset + bin_node.controllers_offset(self.game)
                absolute_controller_data_offset: int = node_offset + bin_node.controller_data_offset(self.game)
                # Store as (absolute_offset - 12) to match MDLOps format
                bin_node.header.offset_to_controllers = absolute_controllers_offset - 12
                bin_node.header.offset_to_controller_data = absolute_controller_data_offset - 12

            # MDLOps: when children_count == 0, offset_to_children equals offset_to_controllers
            # MDLOps stores offsets as (absolute_offset - 12) in the file format
            #
            if actual_children_count == 0:
                bin_node.header.offset_to_children = bin_node.header.offset_to_controllers
            else:
                absolute_children_offset: int = node_offset + bin_node.children_offsets_offset(self.game)
                # Store as (absolute_offset - 12) to match MDLOps format
                bin_node.header.offset_to_children = absolute_children_offset - 12
            bin_node.header.offset_to_root = 0
            parent_idx: int | None = parent_by_idx.get(i)
            # MDLOps stores offsets as (absolute_offset - 12) in the file format
            #
            if parent_idx is not None:
                absolute_parent_offset: int = bin_offsets[parent_idx]
                # Store as (absolute_offset - 12) to match MDLOps format
                bin_node.header.offset_to_parent = absolute_parent_offset - 12
            else:
                bin_node.header.offset_to_parent = 0

            if bin_node.trimesh is not None:
                self._calc_trimesh_offsets(node_offset, bin_node)
            if bin_node.dangly is not None:
                self._calc_dangly_offsets(node_offset, bin_node)
            if bin_node.skin is not None:
                self._calc_skin_offsets(node_offset, bin_node)
            if bin_node.header.type_id & MDLNodeFlags.AABB and bin_node.trimesh is not None:
                self._calc_aabb_offsets(node_offset, bin_node)

    def _calc_dangly_offsets(
        self,
        node_offset: int,
        bin_node: _Node,
    ) -> None:
        assert bin_node.dangly is not None, "Dangly node is required"
        # Constraints follow vertices
        after_vertices: int = node_offset + bin_node.vertices_offset(self.game)
        if bin_node.trimesh is not None:
            after_vertices += bin_node.trimesh.vertices_size()
        if bin_node.dangly.constraints_count > 0:
            # MDLOps uses offset-12 semantics for constraint pointer
            bin_node.dangly.offset_to_contraints = after_vertices - 12
        else:
            bin_node.dangly.offset_to_contraints = 0

    def _calc_aabb_offsets(
        self,
        node_offset: int,
        bin_node: _Node,
    ) -> None:
        """Calculate AABB tree offset.

        AABB tree is written after all other node data (faces, vertices, etc.).
        """
        assert bin_node.trimesh is not None, "Trimesh node is required"
        # _aabb_nodes is always initialized when AABB flag is set (empty list if no aabbs)
        # Type check ensures we handle the None case (should not occur after initialization)
        if bin_node._aabb_nodes is None:
            bin_node.trimesh.offset_to_aabb = 0
            return

        aabb_nodes: list[MDLAABBNode] = bin_node._aabb_nodes
        if len(aabb_nodes) == 0:
            bin_node.trimesh.offset_to_aabb = 0
            return

        # AABB tree is written immediately after all headers and the aabbloc field.
        #
        # The layout is: headers -> aabbloc field (4 bytes) -> AABB tree -> faces
        # So the AABB tree position is: node_offset + all_headers_size + 4 (for aabbloc field)
        aabb_tree_offset: int = node_offset + bin_node.all_headers_size(self.game) + 4

        # AABB tree size: 40 bytes per node
        aabb_tree_size: int = len(aabb_nodes) * 40
        bin_node.trimesh.offset_to_aabb = aabb_tree_offset
        # Store size for writing
        bin_node._aabb_tree_size = aabb_tree_size

    def _calc_skin_offsets(
        self,
        node_offset: int,
        bin_node: _Node,
    ) -> None:
        assert bin_node.skin is not None, "Skin node is required"
        # Place skin variable payload blocks immediately after the vertex array.
        after_vertices: int = node_offset + bin_node.vertices_offset(self.game)
        if bin_node.trimesh is not None:
            after_vertices += bin_node.trimesh.vertices_size()

        cur: int = after_vertices
        if bin_node.skin.bonemap_count:
            bin_node.skin.offset_to_bonemap = cur
            cur += int(bin_node.skin.bonemap_count) * 4
        else:
            bin_node.skin.offset_to_bonemap = 0

        if bin_node.skin.qbones_count:
            bin_node.skin.offset_to_qbones = cur
            cur += int(bin_node.skin.qbones_count) * 16
        else:
            bin_node.skin.offset_to_qbones = 0

        if bin_node.skin.tbones_count:
            bin_node.skin.offset_to_tbones = cur
            cur += int(bin_node.skin.tbones_count) * 12
        else:
            bin_node.skin.offset_to_tbones = 0

        if bin_node.skin.unknown0_count:
            bin_node.skin.offset_to_unknown0 = cur
            cur += int(bin_node.skin.unknown0_count) * 4
        else:
            bin_node.skin.offset_to_unknown0 = 0

    def _calc_trimesh_offsets(
        self,
        node_offset: int,
        bin_node: _Node,
    ):
        assert bin_node.trimesh is not None, "Trimesh node is required"
        bin_node.trimesh.offset_to_counters = node_offset + bin_node.inverted_counters_offset(self.game)
        bin_node.trimesh.offset_to_indices_counts = node_offset + bin_node.indices_counts_offset(self.game)
        bin_node.trimesh.offset_to_indices_offset = node_offset + bin_node.indices_offsets_offset(self.game)
        # indices_offsets stores offsets relative to the start of the indices data block
        # If indices_offsets is empty but count > 0, create the correct number of offsets (all 0)
        # This ensures the count matches the array length, preventing MDLOps from reading beyond bounds
        if (
            bin_node.trimesh.indices_offsets_count > 0
            and not bin_node.trimesh.indices_offsets
        ):
            # No offsets preserved - create the correct number of offsets (all set to 0)
            # This matches the count that was preserved from the original binary header
            bin_node.trimesh.indices_offsets = [0] * bin_node.trimesh.indices_offsets_count
        # If indices_offsets already has values, preserve them (they're already relative offsets)
        # Ensure count matches array length
        if bin_node.trimesh.indices_offsets:
            bin_node.trimesh.indices_offsets_count = bin_node.trimesh.indices_offsets_count2 = len(bin_node.trimesh.indices_offsets)

        bin_node.trimesh.offset_to_faces = node_offset + bin_node.faces_offset(self.game)
        bin_node.trimesh.vertices_offset = node_offset + bin_node.vertices_offset(self.game)

    def _node_type(
        self,
        node: MDLNode,
    ) -> int:
        type_id: int = 1
        # Check for mesh - either explicit mesh object or node_type indicates mesh
        # This ensures we preserve mesh flags even if mesh object is missing
        # Emitter, Light, AABB, and Skin nodes can also have mesh data
        if node.mesh is not None or node.node_type in (
            MDLNodeType.TRIMESH,
            MDLNodeType.DANGLYMESH,
            MDLNodeType.EMITTER,
            MDLNodeType.LIGHT,
            MDLNodeType.AABB,
            MDLNodeType.SKIN,
        ):
            type_id = type_id | MDLNodeFlags.MESH
        if node.skin is not None:
            type_id = type_id | MDLNodeFlags.SKIN
        if node.dangly is not None:
            type_id = type_id | MDLNodeFlags.DANGLY
        if node.saber is not None:
            type_id = type_id | MDLNodeFlags.SABER
        if node.aabb is not None:
            type_id = type_id | MDLNodeFlags.AABB
        if node.emitter is not None or node.node_type == MDLNodeType.EMITTER:
            type_id = type_id | MDLNodeFlags.EMITTER
        if node.light is not None:
            type_id = type_id | MDLNodeFlags.LIGHT
        if node.reference is not None:
            type_id = type_id | MDLNodeFlags.REFERENCE
        return type_id

    def _write_all(self):
        # CRITICAL: MDX data must be written in node_id order to match the original binary file structure.
        # The all_nodes() traversal returns nodes in a different order than they appear in the binary,
        # so we need to sort by node_id before writing MDX data.
        # Create a list of (bin_node, mdl_node, original_index) tuples sorted by node_id
        node_pairs: list[tuple[_Node, MDLNode, int, int]] = [
            (self._bin_nodes[i], self._mdl_nodes[i], i, self._mdl_nodes[i].node_id)
            for i in range(len(self._bin_nodes))
        ]

        # Write MDX data in node_id order
        for bin_node, mdl_node, orig_idx, node_id in sorted(node_pairs, key=lambda x: x[3]):   # Sort by node_id
            if bin_node.trimesh is not None:
                if _DEBUG_MDL:
                    print(f"DEBUG _write_all: Calling _update_mdx for node {mdl_node.name} (node_id={node_id}, orig_idx={orig_idx}, bin_node_id={id(bin_node)}, trimesh_id={id(bin_node.trimesh)})")
                self._update_mdx(bin_node, mdl_node)
                if _DEBUG_MDL and bin_node.trimesh.texture1:
                    print(f"DEBUG _write_all: After _update_mdx, node {mdl_node.name} has tex1_off={bin_node.trimesh.mdx_texture1_offset} (trimesh_id={id(bin_node.trimesh)})")

        # Set function pointers based on game version
        if self.game == Game.K2:
            self._file_header.geometry.function_pointer0 = _GeometryHeader.K2_FUNCTION_POINTER0
            self._file_header.geometry.function_pointer1 = _GeometryHeader.K2_FUNCTION_POINTER1
        else:
            self._file_header.geometry.function_pointer0 = _GeometryHeader.K1_FUNCTION_POINTER0
            self._file_header.geometry.function_pointer1 = _GeometryHeader.K1_FUNCTION_POINTER1
        self._file_header.geometry.model_name = self._mdl.name
        # node_count must include ALL nodes: geometry nodes + animation nodes
        # Reference: MDLOps includes all nodes in geometry header's node_count
        geom_node_count: int = len(self._mdl_nodes)
        anim_node_count: int = sum(len(list(anim.all_nodes())) for anim in self._mdl.anims)
        node_count_actual: int = geom_node_count + anim_node_count
        self._file_header.geometry.node_count = min(node_count_actual, 0x7FFFFFFF)
        self._file_header.geometry.geometry_type = 2

        # Handle headlink: for head models, offset_to_super_root points to neck_g node
        #
        if (self._mdl.headlink or "").strip():
            neck_g_node_offset: int | None = None
            for i, mdl_node in enumerate(self._mdl_nodes):
                if mdl_node.name == "neck_g":
                    neck_g_node_offset = self._node_offsets[i]
                    break
            if neck_g_node_offset is not None:
                self._file_header.offset_to_super_root = neck_g_node_offset
            else:
                # neck_g not found, fall back to root_node_offset
                self._file_header.offset_to_super_root = self._file_header.geometry.root_node_offset
        else:
            self._file_header.offset_to_super_root = self._file_header.geometry.root_node_offset

        self._file_header.mdx_size = self._writer_ext.size()
        self._file_header.mdx_offset = 0

        # Write model header fields exactly as mdlops does ()
        # Classification mapping: mdlops uses hash %classification (Effect=>0x01, Tile=>0x02, Character=>0x04,
        # Door=>0x08, Lightsaber=>0x10, Placeable=>0x20, Flyer=>0x40, Other=>0x00)
        #
        classification_map = {
            MDLClassification.EFFECT: 0x01,
            MDLClassification.TILE: 0x02,
            MDLClassification.CHARACTER: 0x04,
            MDLClassification.DOOR: 0x08,
            MDLClassification.LIGHTSABER: 0x10,
            MDLClassification.PLACEABLE: 0x20,
            MDLClassification.OTHER: 0x00,
        }
        # Default to 0x00 (Other) if classification not in map
        self._file_header.model_type = classification_map.get(self._mdl.classification, 0x00)
        
        # classification_unk1: defaults to 4 for Placeable, 0 otherwise (mdlops:6142-6144)
        if self._mdl.classification_unk1 is not None:
            self._file_header.subclassification = self._mdl.classification_unk1
        else:
            self._file_header.subclassification = 4 if self._mdl.classification == MDLClassification.PLACEABLE else 0
        
        # fog: mdlops uses ignorefog (inverted), writes as "affectedByFog" (mdlops:6147)
        # ignorefog ? 0 : 1 means: if ignorefog is true, fog_byte=0; if false, fog_byte=1
        # Our fog=True means fog affects model (ignorefog=False), so write 1
        # Our fog=False means fog doesn't affect model (ignorefog=True), so write 0
        self._file_header.fog = 1 if self._mdl.fog else 0
        
        animation_count_actual = len(self._mdl.anims)
        animation_count_clamped = min(animation_count_actual, 0x7FFFFFFF)
        self._file_header.animation_count = self._file_header.animation_count2 = animation_count_clamped
        self._file_header.bounding_box_min = self._mdl.bmin
        self._file_header.bounding_box_max = self._mdl.bmax
        self._file_header.radius = self._mdl.radius
        self._file_header.anim_scale = float(self._mdl.animation_scale)
        
        # supermodel: special handling for "mdlops" -> "NULL" (mdlops:6156-6160)
        if self._mdl.supermodel == "mdlops":
            self._file_header.supermodel = "NULL"
        else:
            self._file_header.supermodel = self._mdl.supermodel
        name_offsets_count_actual = len(self._names)
        name_offsets_count_clamped = min(name_offsets_count_actual, 0x7FFFFFFF)
        self._file_header.name_offsets_count = self._file_header.name_offsets_count2 = name_offsets_count_clamped

        self._file_header.write(self._writer)

        for name_offset in self._name_offsets:
            self._writer.write_uint32(name_offset)

        for name in self._names:
            self._writer.write_string(name + "\0", encoding="ascii")

        for anim_offset in self._anim_offsets:
            self._writer.write_uint32(anim_offset)

        for bin_anim in self._bin_anims:
            bin_anim.write(self._writer, self.game)
        for i, bin_node in enumerate(self._bin_nodes):
            if _DEBUG_MDL and bin_node.trimesh and bin_node.trimesh.texture1:
                print(f"DEBUG _write_all: About to write node {i} (name_id={bin_node.header.name_id if bin_node.header else '?'}) texture1={bin_node.trimesh.texture1} bitmap=0x{bin_node.trimesh.mdx_data_bitmap:08X} texture1_offset={bin_node.trimesh.mdx_texture1_offset}")
            bin_node.write(self._writer, self.game)
            if _DEBUG_MDL and bin_node.trimesh and bin_node.trimesh.texture1:
                print(f"DEBUG _write_all: After writing node {i}, texture1_offset={bin_node.trimesh.mdx_texture1_offset}")

        # Write to MDL
        mdl_writer = BinaryWriter.to_auto(self._target)
        mdl_writer.write_uint32(0)
        mdl_writer.write_uint32(self._writer.size())
        mdl_writer.write_uint32(self._writer_ext.size())
        writer_data = self._writer.data()

        mdl_writer.write_bytes(writer_data)

        # Write to MDX
        if self._target_ext is not None:
            BinaryWriter.to_auto(self._target_ext).write_bytes(self._writer_ext.data())
