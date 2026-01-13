# KOTOR Entry Point and Initialization Sequence - Exhaustive Low-Level Analysis

## Overview

This document provides a complete, step-by-step analysis of the entry point function and initialization sequence for Star Wars: Knights of the Old Republic (K1) and Knights of the Old Republic II: The Sith Lords (K2). Every operation is explained at the assembly and C level without metaphors, suitable for understanding by someone with basic programming knowledge.

## Entry Point Function

### Function Signature

**K1 (`swkotor.exe`)**: `UINT entry(void) @ 0x006fb38d`  
**K2 (`swkotor2.exe`)**: `UINT entry(void) @ 0x0076e2dd`

Both functions perform identical initialization sequences with minor address differences. The analysis below uses K1 addresses, with K2 equivalents noted where applicable.

### Purpose

The entry point function is the first code executed when Windows loads the executable. It performs all runtime initialization before calling the game's main function (`WinMain`). This includes setting up memory management, thread-local storage, file I/O, command-line parsing, and static variable initialization.

## Complete Step-by-Step Execution Flow

### Step 1: Stack Frame Setup and Exception Handling

**Assembly Instructions** (K1: `0x006fb38d` - `0x006fb399`):
```
0x006fb38d: PUSH 0x60              ; Push exception handler registration size (96 bytes)
0x006fb38f: PUSH 0x75a040          ; Push exception handler registration structure address
0x006fb394: CALL 0x006ff00c        ; Call __SEH_prolog (Structured Exception Handling prologue)
0x006fb399: MOV EDI, 0x94          ; Set EDI to 148 (size of OSVERSIONINFOA structure)
```

**What Happens**:
1. The function sets up Structured Exception Handling (SEH). SEH allows the program to catch and handle exceptions like access violations.
2. `__SEH_prolog` creates an exception handler registration on the stack. This registration contains:
   - A pointer to the exception handler function
   - The previous exception handler registration (forms a linked list)
   - The address to return to if an exception occurs
3. The function allocates space on the stack for local variables. The `0x60` (96 bytes) is the size needed for exception handler data.
4. `EDI` is set to `0x94` (148 decimal), which is the size in bytes of the `OSVERSIONINFOA` structure used in the next step.

**Why This Matters**: If the program crashes or encounters an error during initialization, the exception handler can catch it and display an error message instead of just terminating.

### Step 2: Windows Version Detection

**Assembly Instructions** (K1: `0x006fb39e` - `0x006fb3f2`):
```
0x006fb39e: MOV EAX, EDI           ; Copy structure size to EAX
0x006fb3a0: CALL 0x006fc090        ; Call __chkstk (stack overflow check)
0x006fb3a5: MOV dword ptr [EBP-0x18], ESP  ; Save stack pointer
0x006fb3a8: MOV ESI, ESP           ; ESI points to local variable area
0x006fb3aa: MOV dword ptr [ESI], EDI  ; Set dwOSVersionInfoSize = 148
0x006fb3ac: PUSH ESI               ; Push address of OSVERSIONINFOA structure
0x006fb3ad: CALL dword ptr [0x0073d060]  ; Call GetVersionExA (imported function)
```

**Decompiled C Code**:
```c
_OSVERSIONINFOA local_114;  // Local variable on stack (148 bytes)
local_114.dwOSVersionInfoSize = 0x94;  // Set structure size to 148 bytes
GetVersionExA(&local_114);  // Call Windows API to get OS version
```

**What Happens**:
1. `__chkstk` checks if there's enough stack space. If the stack would overflow, it allocates more stack pages.
2. The function creates a local variable `local_114` of type `OSVERSIONINFOA` on the stack. This structure holds Windows version information.
3. The structure's `dwOSVersionInfoSize` field is set to `0x94` (148). This tells Windows how large the structure is.
4. `GetVersionExA` is called, which fills the structure with:
   - `dwPlatformId`: Platform identifier (2 = Windows NT/2000/XP, 1 = Windows 95/98/ME)
   - `dwMajorVersion`: Major version number (e.g., 5 for Windows XP)
   - `dwMinorVersion`: Minor version number (e.g., 1 for Windows XP)
   - `dwBuildNumber`: Build number
   - `szCSDVersion`: Service pack string (e.g., "Service Pack 3")

**Why This Matters**: The game needs to know which version of Windows it's running on to use appropriate APIs and avoid compatibility issues.

### Step 3: Store OS Version Information in Global Variables

**Assembly Instructions** (K1: `0x006fb3b3` - `0x006fb3f2`):
```
0x006fb3b3: MOV ECX, dword ptr [ESI+0x10]  ; Load dwPlatformId
0x006fb3b6: MOV dword ptr [0x00833be8], ECX  ; Store in osPlatformID global variable
0x006fb3bc: MOV EAX, dword ptr [ESI+0x4]   ; Load dwMajorVersion
0x006fb3bf: MOV [0x00833bf4], EAX          ; Store in osVersionMajor global variable
0x006fb3c4: MOV EDX, dword ptr [ESI+0x8]  ; Load dwMinorVersion
0x006fb3c7: MOV dword ptr [0x00833bf8], EDX  ; Store in osVersionMinor global variable
0x006fb3cd: MOV ESI, dword ptr [ESI+0xc]   ; Load dwBuildNumber
0x006fb3d0: AND ESI, 0x7fff                ; Mask lower 15 bits (remove high bit flag)
0x006fb3d6: MOV dword ptr [0x00833bec], ESI  ; Store in osBuildNumber global variable
0x006fb3dc: CMP ECX, 0x2                   ; Compare dwPlatformId with 2 (Windows NT)
0x006fb3df: JZ 0x006fb3ed                  ; Jump if equal (skip next instruction)
0x006fb3e1: OR ESI, 0x8000                 ; Set high bit flag (non-NT platform)
0x006fb3e7: MOV dword ptr [0x00833bec], ESI  ; Update osBuildNumber with flag
0x006fb3ed: SHL EAX, 0x8                   ; Shift major version left 8 bits
0x006fb3f0: ADD EAX, EDX                   ; Add minor version
0x006fb3f2: MOV [0x00833bf0], EAX          ; Store combined version in osVersionCombined
```

**Decompiled C Code**:
```c
osPlatformID = local_114.dwPlatformId;           // Store platform ID
osVersionMajor = local_114.dwMajorVersion;        // Store major version
osVersionMinor = local_114.dwMinorVersion;        // Store minor version
osBuildNumber = local_114.dwBuildNumber & 0x7fff; // Store build number (masked)

// If not Windows NT platform, set high bit flag
if (local_114.dwPlatformId != 2) {
    osBuildNumber = osBuildNumber | 0x8000;  // Set bit 15 to indicate non-NT
}

// Combine major and minor version into single value
osVersionCombined = local_114.dwMajorVersion * 0x100 + local_114.dwMinorVersion;
// Example: Windows XP (5.1) becomes 0x0501
```

**What Happens**:
1. The OS version information is copied from the local structure to global variables. These globals are used throughout the program to check Windows version.
2. The build number is masked with `0x7fff` to keep only the lower 15 bits. The high bit is used as a flag.
3. If the platform is not Windows NT (platform ID != 2), the high bit of the build number is set. This flag indicates the game is running on Windows 95/98/ME.
4. The major and minor versions are combined into a single 16-bit value. For example:
   - Windows XP (5.1) → `0x0501`
   - Windows 2000 (5.0) → `0x0500`
   - Windows 98 (4.1) → `0x0401`

**Why This Matters**: The game uses these values to determine which Windows APIs are available and to handle platform-specific behavior.

### Step 4: Check if Executable is a DLL

**Assembly Instructions** (K1: `0x006fb3f7` - `0x006fb451`):
```
0x006fb3f7: XOR ESI, ESI                    ; Clear ESI (set to 0)
0x006fb3f9: PUSH ESI                       ; Push NULL (0)
0x006fb3fa: MOV EDI, dword ptr [0x0073d1d0]  ; Load GetModuleHandleA address
0x006fb400: CALL EDI                       ; Call GetModuleHandleA(NULL)
0x006fb402: CMP word ptr [EAX], 0x5a4d     ; Check DOS header signature ("MZ")
0x006fb407: JNZ 0x006fb428                  ; Jump if not valid PE
0x006fb409: MOV ECX, dword ptr [EAX+0x3c]  ; Load PE header offset
0x006fb40c: ADD ECX, EAX                   ; Calculate PE header address
0x006fb40e: CMP dword ptr [ECX], 0x4550     ; Check PE signature ("PE\0\0")
0x006fb414: JNZ 0x006fb428                  ; Jump if not valid PE
0x006fb416: MOVZX EAX, word ptr [ECX+0x18]  ; Load Magic field (0x10b = PE32, 0x20b = PE32+)
0x006fb41a: CMP EAX, 0x10b                  ; Compare with PE32 magic
0x006fb41f: JZ 0x006fb440                  ; Jump if PE32
0x006fb421: CMP EAX, 0x20b                  ; Compare with PE32+ magic
0x006fb426: JZ 0x006fb42d                  ; Jump if PE32+
0x006fb428: MOV dword ptr [EBP-0x1c], ESI  ; Set isDll = 0 (not a DLL)
0x006fb42b: JMP 0x006fb454                  ; Jump to next section
0x006fb42d: CMP dword ptr [ECX+0x84], 0xe   ; Check if OptionalHeader64.Size >= 14
0x006fb434: JBE 0x006fb428                  ; Jump if too small
0x006fb436: XOR EAX, EAX                   ; Clear EAX
0x006fb438: CMP dword ptr [ECX+0xf8], ESI   ; Check DLLCharacteristics field
0x006fb43e: JMP 0x006fb44e                  ; Jump to set flag
0x006fb440: CMP dword ptr [ECX+0x74], 0xe   ; Check if OptionalHeader.Size >= 14
0x006fb444: JBE 0x006fb428                  ; Jump if too small
0x006fb446: XOR EAX, EAX                   ; Clear EAX
0x006fb448: CMP dword ptr [ECX+0xE8], ESI   ; Check DLLCharacteristics field
0x006fb44e: SETNZ AL                       ; Set AL to 1 if DLL flag is set
0x006fb451: MOV dword ptr [EBP-0x1c], EAX  ; Store isDll flag
```

**Decompiled C Code**:
```c
HMODULE hModule = GetModuleHandleA(NULL);  // Get handle to current executable
int isDll = 0;  // Default to not a DLL

// Verify PE structure
if ((short)hModule->unused == 0x5a4d) {  // Check DOS header "MZ" signature
    int *peHeader = (int *)((int)&hModule->unused + hModule[0xf].unused);  // Get PE header offset
    
    if (*peHeader == 0x4550) {  // Check PE signature "PE\0\0"
        if ((short)peHeader[6] == 0x10b) {  // PE32 format
            if (0xe < (uint)peHeader[0x1d]) {  // Check OptionalHeader.Size >= 14
                // Check DLLCharacteristics field (offset 0xE8 in PE32)
                isDll = (peHeader[0x3a] != 0);  // DLLCharacteristics field
            }
        }
        else if ((short)peHeader[6] == 0x20b) {  // PE32+ format
            if (0xe < (uint)peHeader[0x21]) {  // Check OptionalHeader64.Size >= 14
                // Check DLLCharacteristics field (offset 0xF8 in PE32+)
                isDll = (peHeader[0x3e] != 0);  // DLLCharacteristics field
            }
        }
    }
}
```

**What Happens**:
1. `GetModuleHandleA(NULL)` returns a handle to the current executable module. This is actually a pointer to the DOS header in memory.
2. The code verifies the PE (Portable Executable) structure:
   - Checks for DOS header signature `0x5a4d` ("MZ")
   - Reads the PE header offset from the DOS header (offset 0x3C)
   - Calculates the PE header address
   - Checks for PE signature `0x4550` ("PE\0\0")
3. The code determines if the executable is PE32 (32-bit) or PE32+ (64-bit) by checking the `Magic` field.
4. It reads the `DLLCharacteristics` field from the Optional Header:
   - PE32: Offset 0xE8 (232 decimal)
   - PE32+: Offset 0xF8 (248 decimal)
5. If the `DLLCharacteristics` field has the DLL flag set, `isDll` is set to 1, otherwise 0.

**Why This Matters**: DLLs and executables have different exit behavior. DLLs should not call `ExitProcess` directly, while executables can. This check determines the proper cleanup method.

### Step 5: Initialize Heap Memory Manager

**Assembly Instructions** (K1: `0x006fb454` - `0x006fb467`):
```
0x006fb454: PUSH 0x1               ; Push argument (1 = success)
0x006fb456: CALL 0x007026dc        ; Call __heap_init()
0x006fb45b: POP ECX                ; Remove argument from stack
0x006fb45c: TEST EAX, EAX          ; Test return value
0x006fb45e: JNZ 0x006fb468         ; Jump if successful (non-zero)
0x006fb460: PUSH 0x1c              ; Push error code (28)
0x006fb462: CALL 0x006fb369        ; Call _fast_error_exit(0x1c)
0x006fb467: POP ECX                ; Remove argument from stack
```

**Decompiled C Code**:
```c
int result = __heap_init();
if (result == 0) {
    _fast_error_exit(0x1c);  // Exit with error code 28 if heap init fails
}
```

**Function: `__heap_init()` @ 0x007026dc**

**What This Function Does**:
```c
int __heap_init(void)
{
    // Create a private heap for the process
    DAT_00834338 = HeapCreate(0, 0x1000, 0);
    // Parameters:
    //   0 = No special flags (normal heap)
    //   0x1000 = Initial size (4096 bytes)
    //   0 = Maximum size (0 = growable, no limit)
    
    if (DAT_00834338 == NULL) {
        return 0;  // Failure
    }
    
    // Select heap allocation mode
    heapMode = ___heap_select();
    
    // If using Small Block Heap (mode 3), initialize it
    if ((heapMode == 3) && (___sbh_heap_init(0x3f8) == 0)) {
        HeapDestroy(DAT_00834338);  // Clean up on failure
        return 0;  // Failure
    }
    
    return 1;  // Success
}
```

**What Happens**:
1. `HeapCreate` creates a private heap for the process. A heap is a memory pool used for dynamic allocation (`malloc`, `new`, etc.).
2. The heap starts at 4KB (0x1000 bytes) and can grow as needed.
3. `___heap_select()` determines which heap allocation strategy to use:
   - Mode 1: Standard Windows heap
   - Mode 2: Low-fragmentation heap
   - Mode 3: Small Block Heap (SBH) - optimized for small allocations
4. If SBH mode is selected, `___sbh_heap_init` initializes the Small Block Heap with a block size of `0x3f8` (1016 bytes).
5. If initialization fails, the function returns 0, and the entry point calls `_fast_error_exit(0x1c)` to terminate the process.

**Why This Matters**: All dynamic memory allocation in the program uses this heap. Without it, the program cannot allocate memory and will crash.

### Step 6: Initialize Thread-Local Storage (TLS)

**Assembly Instructions** (K1: `0x006fb468` - `0x006fb478`):
```
0x006fb468: CALL 0x006fef50        ; Call __tls_init()
0x006fb46d: TEST EAX, EAX          ; Test return value
0x006fb46f: JNZ 0x006fb479         ; Jump if successful
0x006fb471: PUSH 0x10              ; Push error code (16)
0x006fb473: CALL 0x006fb369        ; Call _fast_error_exit(0x10)
0x006fb478: POP ECX                ; Remove argument from stack
```

**Decompiled C Code**:
```c
int result = __tls_init();
if (result == 0) {
    _fast_error_exit(0x10);  // Exit with error code 16 if TLS init fails
}
```

**Function: `__tls_init()` @ 0x006fef50**

**What This Function Does**:
```c
undefined4 __tls_init(void)
{
    int lockResult;
    DWORD *tlsData;
    BOOL setResult;
    DWORD threadId;
    
    // Initialize multi-threaded locks
    lockResult = __mtinitlocks();
    if (lockResult != 0) {
        // Allocate a TLS index (Thread-Local Storage slot)
        threadLocalStorageIndex = TlsAlloc();
        if (threadLocalStorageIndex != 0xffffffff) {  // Success
            // Allocate 136 bytes (0x88) for TLS data
            tlsData = _calloc(1, 0x88);
            if (tlsData != NULL) {
                // Store TLS data pointer in the TLS slot
                setResult = TlsSetValue(threadLocalStorageIndex, tlsData);
                if (setResult != 0) {
                    // Initialize TLS data structure
                    tlsData[0x15] = (DWORD)&DAT_007a2f78;  // Set pointer to some data
                    tlsData[5] = 1;                        // Set flag
                    threadId = GetCurrentThreadId();       // Get current thread ID
                    tlsData[1] = 0xffffffff;              // Set to -1
                    tlsData[0] = threadId;                // Store thread ID
                    return 1;  // Success
                }
            }
            // Cleanup on failure
            __tls_cleanup();
            return 0;
        }
    }
    // Cleanup on failure
    __tls_cleanup();
    return 0;
}
```

**What Happens**:
1. `__mtinitlocks()` initializes critical sections (locks) used for thread synchronization.
2. `TlsAlloc()` allocates a TLS index. Each thread can store a pointer in this index that is unique to that thread.
3. `_calloc(1, 0x88)` allocates 136 bytes of zero-initialized memory for TLS data. This data structure contains:
   - Thread ID
   - Error number (`errno`)
   - Per-thread heap pointers
   - Other thread-specific data
4. `TlsSetValue` stores the TLS data pointer in the TLS slot for the current thread.
5. The TLS data structure is initialized with:
   - A pointer to a global data structure
   - A flag set to 1
   - The current thread ID
   - A field set to -1 (0xffffffff)

**Why This Matters**: Thread-Local Storage allows each thread to have its own copy of global variables. This is essential for multi-threaded programs to avoid data races. For example, `errno` (error number) must be per-thread so one thread's error doesn't affect another.

### Step 7: Run Static Initializers

**Assembly Instructions** (K1: `0x006fb479`):
```
0x006fb479: CALL 0x00701aa5        ; Call __UNUSED_run_initializers()
```

**Decompiled C Code**:
```c
__UNUSED_run_initializers();
```

**What Happens**:
This function runs constructors for global C++ objects. In C++, global objects have their constructors called before `main()`. This function iterates through a table of constructor function pointers and calls each one.

**Why This Matters**: Global C++ objects (like `std::cout`, static class instances) need to be initialized before the program starts using them.

### Step 8: Initialize File I/O System

**Assembly Instructions** (K1: `0x006fb47e` - `0x006fb491`):
```
0x006fb47e: MOV dword ptr [EBP-0x4], ESI  ; Set local variable to 0
0x006fb481: CALL 0x007024c4                ; Call __file_io_init()
0x006fb486: TEST EAX, EAX                  ; Test return value (signed)
0x006fb488: JGE 0x006fb492                 ; Jump if >= 0 (success)
0x006fb48a: PUSH 0x1b                      ; Push error code (27)
0x006fb48c: CALL 0x006fb344                ; Call __amsg_exit(0x1b)
0x006fb491: POP ECX                        ; Remove argument from stack
```

**Decompiled C Code**:
```c
local_8 = (undefined *)0x0;  // Clear local variable
int result = __file_io_init();
if (result < 0) {
    __amsg_exit(0x1b);  // Exit with error code 27 if file I/O init fails
}
```

**Function: `__file_io_init()` @ 0x007024c4**

**What This Function Does** (simplified):
```c
undefined4 __file_io_init(void)
{
    // Allocate file descriptor table (1152 bytes = 0x480)
    undefined4 *fdTable = _malloc(0x480);
    if (fdTable == NULL) {
        return 0xffffffff;  // Failure
    }
    
    // Initialize file descriptor table
    maxFileHandles_ = 0x20;  // Start with 32 file handles
    fileDescriptorTable = fdTable;
    
    // Initialize each file descriptor entry
    for (int i = 0; i < 32; i++) {
        fdTable[i * 9 + 0] = 0xffffffff;      // Invalid handle
        fdTable[i * 9 + 1] = 0;               // Flags
        fdTable[i * 9 + 2] = 0;               // File position
        fdTable[i * 9 + 4] = 10;              // Buffer mode (line buffered)
    }
    
    // Get startup information
    _STARTUPINFOA startupInfo;
    GetStartupInfoA(&startupInfo);
    
    // If parent process passed file handles, extend the table
    if (startupInfo.cbReserved2 != 0 && startupInfo.lpReserved2 != NULL) {
        // Parse inherited file handles and add them to the table
        // ... (complex logic to extend file descriptor table)
    }
    
    // Map standard handles (stdin, stdout, stderr)
    // ... (code to set up stdin/stdout/stderr)
    
    return 0;  // Success
}
```

**What Happens**:
1. The function allocates a file descriptor table. This table maps file descriptor numbers (0, 1, 2, etc.) to Windows file handles.
2. It initializes 32 file descriptor slots. Each slot contains:
   - Windows file handle (or 0xffffffff if unused)
   - Flags (read/write mode, etc.)
   - File position
   - Buffer mode
3. It checks if the parent process passed file handles via `STARTUPINFO`. This allows processes to inherit open files.
4. It maps standard file descriptors:
   - 0 = stdin (standard input)
   - 1 = stdout (standard output)
   - 2 = stderr (standard error)
5. If the table needs more than 32 handles, it allocates extension blocks.

**Why This Matters**: The C runtime library uses file descriptors (like `FILE *` in `fopen`). This function sets up the mapping between C file descriptors and Windows file handles.

### Step 9: Get Command Line and Environment Variables

**Assembly Instructions** (K1: `0x006fb492` - `0x006fb4a7`):
```
0x006fb492: CALL dword ptr [0x0073d154]  ; Call GetCommandLineA()
0x006fb498: MOV [0x00835484], EAX        ; Store in commandLineRaw global
0x006fb49d: CALL 0x007023a2              ; Call __get_env_vars()
0x006fb4a2: MOV [0x00833c2c], EAX         ; Store in environmentVariablesRaw global
0x006fb4a7: CALL 0x00702300               ; Call __init_cmdline_args(this)
0x006fb4ac: TEST EAX, EAX                 ; Test return value (signed)
0x006fb4ae: JGE 0x006fb4b8                ; Jump if >= 0 (success)
0x006fb4b0: PUSH 0x8                      ; Push error code (8)
0x006fb4b2: CALL 0x006fb344               ; Call __amsg_exit(0x8)
0x006fb4b7: POP ECX                       ; Remove argument from stack
```

**Decompiled C Code**:
```c
commandLineRaw = GetCommandLineA();           // Get raw command line string
environmentVariablesRaw = __get_env_vars();  // Get environment variable block
int result = __init_cmdline_args(this);
if (result < 0) {
    __amsg_exit(8);  // Exit with error code 8 if command line parsing fails
}
```

**Function: `GetCommandLineA()`**

**What This Does**:
Returns a pointer to the command line string passed to the program. For example, if you run `swkotor.exe -fullscreen`, it returns `"swkotor.exe -fullscreen"`.

**Function: `__get_env_vars()` @ 0x007023a2**

**What This Does**:
Calls `GetEnvironmentStrings()` which returns a block of environment variables in the format:
```
VAR1=value1\0VAR2=value2\0\0
```
The block is terminated by two null bytes.

**Function: `__init_cmdline_args()` @ 0x00702300**

**What This Function Does**:
```c
undefined4 __init_cmdline_args(void *this)
{
    // Initialize code page if not already done
    if (isCodePageInitialized == 0) {
        __init_codepage();
    }
    
    // Get executable path
    DAT_00833ebc = 0;
    GetModuleFileNameA(NULL, exePath, 0x104);  // Get full path to exe
    PTR_00833c18 = exePath;
    
    // First pass: count arguments
    int argCount = 0;
    __tonkenize_cmdline_args(NULL, NULL, &argCount);
    
    // Allocate array for argument pointers
    byte **argv = _malloc(argCount * 4 + 4);  // 4 bytes per pointer + null terminator
    if (argv == NULL) {
        return 0xffffffff;  // Failure
    }
    
    // Second pass: tokenize and store arguments
    __tonkenize_cmdline_args(argv + argCount, argv, &argCount);
    
    argc = argCount - 1;  // Subtract 1 (program name doesn't count)
    argv = (char **)argv;
    
    return 0;  // Success
}
```

**What Happens**:
1. The function initializes the code page (character encoding) if needed.
2. It gets the full path to the executable using `GetModuleFileNameA`.
3. It makes two passes over the command line:
   - First pass: Counts how many arguments there are
   - Second pass: Tokenizes the command line and stores pointers to each argument
4. It allocates an array of pointers (`argv`) and fills it with pointers to each argument string.
5. It sets `argc` to the number of arguments (minus 1 for the program name).

**Example**: If command line is `"swkotor.exe -fullscreen -width 1920"`:
- `argc = 3`
- `argv[0] = "swkotor.exe"`
- `argv[1] = "-fullscreen"`
- `argv[2] = "-width"`
- `argv[3] = "1920"`
- `argv[4] = NULL` (terminator)

**Why This Matters**: The program needs to parse command-line arguments to configure behavior (windowed vs fullscreen, resolution, etc.).

### Step 10: Parse Environment Variables

**Assembly Instructions** (K1: `0x006fb4b8` - `0x006fb4c8`):
```
0x006fb4b8: CALL 0x007020cd        ; Call __parse_env_vars()
0x006fb4bd: TEST EAX, EAX          ; Test return value (signed)
0x006fb4bf: JGE 0x006fb4c9         ; Jump if >= 0 (success)
0x006fb4c1: PUSH 0x9               ; Push error code (9)
0x006fb4c3: CALL 0x006fb344        ; Call __amsg_exit(0x9)
0x006fb4c8: POP ECX                ; Remove argument from stack
```

**Decompiled C Code**:
```c
int result = __parse_env_vars();
if (result < 0) {
    __amsg_exit(9);  // Exit with error code 9 if env var parsing fails
}
```

**Function: `__parse_env_vars()` @ 0x007020cd**

**What This Function Does**:
```c
undefined4 __parse_env_vars(void)
{
    // Initialize code page if needed
    if (isCodePageInitialized == 0) {
        __init_codepage();
    }
    
    // First pass: count environment variables
    int varCount = 0;
    char *envPtr = environmentVariablesRaw;
    if (envPtr != NULL) {
        while (*envPtr != '\0') {
            if (*envPtr != '=') {  // Skip entries that start with '='
                varCount++;
            }
            envPtr += strlen(envPtr) + 1;  // Move to next variable
        }
    }
    
    // Allocate array for environment variable pointers
    char **envArray = _malloc(varCount * 4 + 4);  // 4 bytes per pointer + null terminator
    environmentVariables = envArray;
    
    if (envArray == NULL) {
        return 0xffffffff;  // Failure
    }
    
    // Second pass: copy environment variables
    envPtr = environmentVariablesRaw;
    char **envArrayPtr = envArray;
    
    while (true) {
        if (*envPtr == '\0') {  // End of environment block
            _free(environmentVariablesRaw);
            environmentVariablesRaw = NULL;
            *envArrayPtr = NULL;  // Null terminator
            _DAT_00835488 = 1;    // Set flag
            return 0;  // Success
        }
        
        size_t varLen = strlen(envPtr);
        
        if (*envPtr != '=') {  // Valid variable (not internal Windows entry)
            // Allocate memory for this variable
            char *varCopy = _malloc(varLen + 1);
            *envArrayPtr = varCopy;
            
            if (varCopy == NULL) {
                // Cleanup on failure
                _free(environmentVariables);
                environmentVariables = NULL;
                return 0xffffffff;  // Failure
            }
            
            // Copy variable string
            strcpy(varCopy, envPtr);
            envArrayPtr++;  // Move to next slot
        }
        
        envPtr += varLen + 1;  // Move to next variable
    }
}
```

**What Happens**:
1. The function parses the environment variable block returned by `GetEnvironmentStrings()`.
2. It makes two passes:
   - First pass: Counts valid environment variables (skips entries starting with '=' which are internal Windows entries)
   - Second pass: Allocates memory for each variable and copies it
3. It creates an array of pointers (`environmentVariables`) similar to `argv`, terminated by NULL.
4. It frees the original environment block and sets a flag indicating parsing is complete.

**Example**: If environment contains `PATH=C:\Windows\System32\0TEMP=C:\Temp\0\0`:
- `environmentVariables[0] = "PATH=C:\Windows\System32"`
- `environmentVariables[1] = "TEMP=C:\Temp"`
- `environmentVariables[2] = NULL`

**Why This Matters**: Programs often read environment variables for configuration (like `PATH`, `TEMP`, custom game settings, etc.).

### Step 11: Run Static Initializations

**Assembly Instructions** (K1: `0x006fb4c9` - `0x006fb4dc`):
```
0x006fb4c9: CALL 0x006fb0da        ; Call runStaticInitializations()
0x006fb4ce: MOV dword ptr [EBP-0x20], EAX  ; Store return value
0x006fb4d1: CMP EAX, ESI           ; Compare with 0
0x006fb4d3: JZ 0x006fb4dc           ; Jump if zero (success)
0x006fb4d5: PUSH EAX                ; Push error code
0x006fb4d6: CALL 0x006fb344        ; Call __amsg_exit(errorCode)
0x006fb4db: POP ECX                 ; Remove argument from stack
```

**Decompiled C Code**:
```c
int initResult = runStaticInitializations();
if (initResult != 0) {
    __amsg_exit(initResult);  // Exit with error code if initialization fails
}
```

**Function: `runStaticInitializations()` @ 0x006fb0da**

**What This Function Does**:
```c
int runStaticInitializations(void)
{
    int errorCode;
    undefined4 *initTablePtr;
    
    // Initialize floating point system if pointer is set
    if (PTR_staticInitFloatingPointSystem_007a2748 != NULL) {
        (*(code *)PTR_staticInitFloatingPointSystem_007a2748)();
    }
    
    errorCode = 0;
    initTablePtr = &staticInitTable1;  // First initialization table
    
    // Run initializers from first table
    do {
        if (errorCode != 0) {
            return errorCode;  // Return error if any initializer failed
        }
        
        if ((code *)*initTablePtr != NULL) {
            errorCode = (*(code *)*initTablePtr)();  // Call initializer function
        }
        
        initTablePtr++;
    } while (initTablePtr < &staticInitTable1End);
    
    // If all succeeded, register cleanup function and run second table
    if (errorCode == 0) {
        _atexit(EmptyStaticDispose);  // Register cleanup function
        initTablePtr = &staticInitTable2;  // Second initialization table
        
        // Run initializers from second table (no error checking)
        do {
            if ((code *)*initTablePtr != NULL) {
                (*(code *)*initTablePtr)();  // Call initializer function
            }
            initTablePtr++;
        } while (initTablePtr < &staticInitTable2End);
        
        errorCode = 0;
    }
    
    return errorCode;
}
```

**What Happens**:
1. The function first initializes the floating-point system if a pointer is set. This sets up the FPU (Floating-Point Unit) control word.
2. It iterates through `staticInitTable1`, calling each function pointer. These are C++ global object constructors and C static initializers.
3. If any initializer returns a non-zero error code, the function returns immediately.
4. If all initializers succeed, it registers `EmptyStaticDispose` as an exit handler (called when program exits).
5. It then iterates through `staticInitTable2`, calling each function pointer. These are typically less critical initializers.

**Why This Matters**: C++ global objects and C static variables with initializers need their constructors/initializers called before the program starts. This function ensures all static initialization happens in the correct order.

### Step 12: Get Startup Information

**Assembly Instructions** (K1: `0x006fb4dc` - `0x006fb4e9`):
```
0x006fb4dc: MOV dword ptr [EBP-0x38], ESI  ; Clear local variable
0x006fb4df: LEA EAX, [EBP-0x64]            ; Load address of startupInfo structure
0x006fb4e2: PUSH EAX                       ; Push address
0x006fb4e3: CALL dword ptr [0x0073d158]    ; Call GetStartupInfoA()
0x006fb4e9: CALL 0x00702064                ; Call FUN_00702064() (skip executable name in command line)
```

**Decompiled C Code**:
```c
local_68.dwFlags = 0;  // Clear flags
GetStartupInfoA(&local_68);  // Get startup information from parent process
FUN_00702064();  // Skip executable name in command line, return pointer to first argument
```

**Function: `GetStartupInfoA()`**

**What This Does**:
Fills a `STARTUPINFOA` structure with information about how the process was started:
- Window position and size
- Standard input/output handles
- Whether the process was started in a window or console
- Title of the window/console

**Function: `FUN_00702064()` @ 0x00702064**

**What This Function Does**:
```c
char * FUN_00702064(void)
{
    // Initialize code page if needed
    if (isCodePageInitialized == 0) {
        __init_codepage();
    }
    
    if (commandLineRaw == NULL) {
        return "";  // Empty string if no command line
    }
    
    char *cmdPtr = commandLineRaw;
    char firstChar = *cmdPtr;
    
    // If command line doesn't start with quote, skip to first non-whitespace
    if (firstChar != '"') {
        // Skip whitespace
        while ((byte)firstChar >= 0x21) {  // 0x21 = '!' (first printable ASCII)
            firstChar = cmdPtr[1];
            cmdPtr++;
        }
    }
    else {
        // Command line starts with quote, skip quoted executable name
        cmdPtr = commandLineRaw + 1;
        char currentChar = *cmdPtr;
        
        if (currentChar != '"') {
            // Skip until closing quote (handling multi-byte characters)
            while (currentChar != '\0') {
                if (FUN_00709408(currentChar) != 0) {  // Check if multi-byte character
                    cmdPtr++;  // Skip second byte
                }
                cmdPtr++;
                currentChar = *cmdPtr;
                if (currentChar == '"') {
                    break;
                }
            }
        }
        
        // Skip closing quote and whitespace
        do {
            cmdPtr++;
        } while ((*cmdPtr != 0) && ((byte)*cmdPtr < 0x21));
    }
    
    return cmdPtr;  // Return pointer to first argument (after executable name)
}
```

**What Happens**:
1. The function skips the executable name in the command line string.
2. If the command line starts with a quote (`"`), it finds the closing quote and skips it.
3. It handles multi-byte characters (like Japanese/Chinese characters that take 2 bytes).
4. It skips any whitespace after the executable name.
5. It returns a pointer to the first actual argument.

**Example**: 
- Input: `"C:\Program Files\swkotor.exe" -fullscreen`
- Output: Pointer to `"-fullscreen"`

**Why This Matters**: The `argv` array already has the executable name separated, but sometimes the program needs a pointer to the raw command line starting from the first argument.

### Step 13: Call WinMain (Game Entry Point)

**Assembly Instructions** (K1: `0x006fb4e9` - `0x006fb523`):
```
0x006fb4e9: CALL 0x00702064        ; Call FUN_00702064() (already done above)
0x006fb4ee: MOV dword ptr [EBP-0x68], EAX  ; Store result
0x006fb4f1: TEST byte ptr [EBP-0x38], 0x1  ; Test startupInfo.dwFlags bit 0
0x006fb4f5: JZ 0x006fb4fd          ; Jump if bit not set
0x006fb4f7: MOVZX EAX, word ptr [EBP-0x34]  ; Load startupInfo.wShowWindow
0x006fb4fb: JMP 0x006fb500         ; Jump to push
0x006fb4fd: PUSH 0xa               ; Push SW_SHOWDEFAULT (10)
0x006fb4ff: POP EAX                ; Load into EAX
0x006fb500: PUSH EAX               ; Push nCmdShow parameter
0x006fb501: PUSH dword ptr [EBP-0x68]  ; Push command line pointer
0x006fb504: PUSH ESI               ; Push 0 (hPrevInstance)
0x006fb505: PUSH ESI               ; Push 0 (hInstance - will be replaced)
0x006fb506: CALL EDI               ; Call GetModuleHandleA(NULL)
0x006fb508: PUSH EAX               ; Push hInstance
0x006fb509: CALL 0x004041f0        ; Call WinMain(hInstance, hPrevInstance, cmdLine, nCmdShow)
0x006fb50e: MOV EDI, EAX           ; Store return value (exit code)
0x006fb510: MOV dword ptr [EBP-0x6c], EDI  ; Store in local variable
```

**Decompiled C Code**:
```c
char *cmdLine = FUN_00702064();  // Get pointer to first argument
HMODULE hInstance = GetModuleHandleA(NULL);  // Get instance handle

// Determine window show command
int nCmdShow;
if (local_68.dwFlags & 0x1) {  // If STARTF_USESHOWWINDOW flag is set
    nCmdShow = local_68.wShowWindow;  // Use specified show command
}
else {
    nCmdShow = SW_SHOWDEFAULT;  // Use default (10)
}

// Call game's main function
UINT exitCode = WinMain(hInstance, NULL, cmdLine, nCmdShow);
```

**Function: `WinMain()` @ 0x004041f0**

**Parameters**:
- `hInstance`: Handle to the current instance of the application
- `hPrevInstance`: Always NULL in Win32 (legacy from Win16)
- `lpCmdLine`: Pointer to command line string (without executable name)
- `nCmdShow`: How to show the window (SW_SHOW, SW_HIDE, etc.)

**What Happens**:
1. The function gets the instance handle (pointer to the executable in memory).
2. It determines how to show the window based on startup information.
3. It calls `WinMain`, which is the game's actual entry point. This function:
   - Creates the game window
   - Initializes the game engine
   - Runs the main game loop
   - Returns an exit code when the game exits

**Why This Matters**: This is where the actual game code starts executing. All the initialization above was just setting up the runtime environment.

### Step 14: Exit the Process

**Assembly Instructions** (K1: `0x006fb513` - `0x006fb55e`):
```
0x006fb513: CMP dword ptr [EBP-0x1c], ESI  ; Compare isDll with 0
0x006fb516: JNZ 0x006fb51e                 ; Jump if DLL (skip ExitProcess)
0x006fb518: PUSH EDI                       ; Push exit code
0x006fb519: CALL 0x006fb212                ; Call _internal_exit(exitCode, 0, 0)
0x006fb51e: CALL 0x006fb234               ; Call _internal_exit(0, 0, 1)
0x006fb523: JMP 0x006fb550                 ; Jump to cleanup
0x006fb550: OR dword ptr [EBP-0x4], 0xffffffff  ; Set exception handler flag to -1
0x006fb554: MOV EAX, EDI                   ; Move exit code to EAX (return value)
0x006fb556: LEA ESP, [EBP-0x7c]            ; Restore stack pointer
0x006fb559: CALL 0x006ff047                ; Call __SEH_epilog (exception handler cleanup)
0x006fb55e: RET                            ; Return (should never reach here)
```

**Decompiled C Code**:
```c
if (isDll == 0) {
    // Executable: exit with game's exit code
    _internal_exit(exitCode, 0, 0);
}
else {
    // DLL: exit with code 0
    _internal_exit(0, 0, 1);
}
// Function should never return (process terminates)
return exitCode;
```

**Function: `_internal_exit()` @ 0x006fb212 / 0x006fb234**

**What This Does**:
```c
void _internal_exit(UINT exitCode, int doExit, int isDll)
{
    // Call registered exit handlers (atexit functions)
    // Clean up TLS
    // Close file handles
    // Free heap
    // Call ExitProcess(exitCode) if doExit != 0
}
```

**What Happens**:
1. If the executable is not a DLL, it calls `_internal_exit` with the game's exit code.
2. If it is a DLL, it calls `_internal_exit` with exit code 0.
3. `_internal_exit` performs cleanup:
   - Calls all functions registered with `atexit()`
   - Cleans up thread-local storage
   - Closes all open file handles
   - Frees the heap
   - Calls `ExitProcess(exitCode)` to terminate the process
4. The function should never return because `ExitProcess` terminates the process.

**Why This Matters**: Proper cleanup ensures resources are freed and the process terminates cleanly.

## Global Variables Used

### OS Version Information

**K1 Addresses**:
- `osPlatformID @ 0x00833be8`: Platform identifier (2 = Windows NT)
- `osVersionMajor @ 0x00833bf4`: Major version number
- `osVersionMinor @ 0x00833bf8`: Minor version number
- `osBuildNumber @ 0x00833bec`: Build number (with platform flag in high bit)
- `osVersionCombined @ 0x00833bf0`: Combined major.minor version (e.g., 0x0501 for 5.1)

**K2 Addresses**:
- `osPlatformID @ 0x008b879c`
- `osVersionMajor @ 0x008b87a8`
- `osVersionMinor @ 0x008b87ac`
- `osBuildNumber @ 0x008b87a0`
- `osVersionCombined @ 0x008b87a4`

### Command Line and Environment

**K1 Addresses**:
- `commandLineRaw @ 0x00835484`: Raw command line string from Windows
- `environmentVariablesRaw @ 0x00833c2c`: Raw environment variable block
- `argc @ 0x00833c20`: Number of command-line arguments
- `argv @ 0x00833c24`: Array of argument string pointers
- `environmentVariables @ 0x00833c28`: Array of environment variable string pointers

**K2 Addresses**:
- `commandLineRaw @ 0x008ba024`
- `environmentVariablesRaw @ 0x008b87e0`

### Heap and TLS

**K1 Addresses**:
- `DAT_00834338`: Heap handle (from `HeapCreate`)
- `threadLocalStorageIndex`: TLS index (from `TlsAlloc`)
- `heapMode`: Heap allocation mode (1, 2, or 3)

## Function Naming Conventions

### Standard C Runtime Functions

These functions follow Microsoft C Runtime Library naming:
- `__heap_init`: Initialize heap
- `__tls_init`: Initialize thread-local storage
- `__file_io_init`: Initialize file I/O
- `__init_cmdline_args`: Initialize command-line arguments
- `__parse_env_vars`: Parse environment variables
- `runStaticInitializations`: Run C++ static constructors

### Game-Specific Functions

- `WinMain`: Game's main entry point (standard Windows application entry point)
- `entry`: Program entry point (called by Windows loader)

## Error Handling

### Error Codes

The initialization functions use specific error codes:
- `0x1c` (28): Heap initialization failed
- `0x10` (16): TLS initialization failed
- `0x1b` (27): File I/O initialization failed
- `0x8` (8): Command-line argument parsing failed
- `0x9` (9): Environment variable parsing failed
- Other codes: Returned by static initializers

### Error Exit Functions

- `_fast_error_exit(errorCode)`: Displays error message and exits immediately
- `__amsg_exit(errorCode)`: Displays error message with more details and exits

## Memory Layout During Initialization

### Stack Layout (Entry Function)

```
EBP-0x7c: Exception handler registration
EBP-0x1c: isDll flag (4 bytes)
EBP-0x20: Static init result (4 bytes)
EBP-0x24: Command line init result (4 bytes)
EBP-0x38: StartupInfo.dwFlags (4 bytes)
EBP-0x64: StartupInfo structure (68 bytes)
EBP-0x68: Command line pointer (4 bytes)
EBP-0x6c: Exit code (4 bytes)
EBP-0x114: OSVERSIONINFOA structure (148 bytes)
```

### Heap Layout

After `__heap_init()`:
- Private heap created at address returned by `HeapCreate`
- Initial size: 4KB (0x1000 bytes)
- Grows as needed (no maximum limit)
- Used for all `malloc`/`new` allocations

### TLS Layout

After `__tls_init()`:
- TLS index allocated via `TlsAlloc()`
- 136 bytes (0x88) allocated per thread for TLS data
- Structure contains:
  - Thread ID (offset 0x0)
  - Error number (offset 0x4)
  - Heap pointers (various offsets)
  - Other thread-specific data

## Comparison: K1 vs K2

### Address Differences

| Function/Variable | K1 Address | K2 Address | Notes |
|-------------------|-----------|------------|-------|
| `entry` | `0x006fb38d` | `0x0076e2dd` | Different due to code size differences |
| `__heap_init` | `0x007026dc` | Similar | Same function, different address |
| `__tls_init` | `0x006fef50` | `0x00772273` | K2 uses different name: `FUN_00772273` |
| `WinMain` | `0x004041f0` | `0x00404250` | Slightly different address |

### Functional Differences

- **K1**: Uses `__tls_init()` directly
- **K2**: Uses `FUN_00772273()` which is equivalent to `__tls_init()` but may have minor differences

- **K1**: Uses `__UNUSED_run_initializers()`
- **K2**: Uses `FUN_007744ee()` which is equivalent

- **K1**: Uses `FUN_00702064()` to skip executable name
- **K2**: Uses `FUN_00774aad()` which is equivalent

### Naming Unification

To unify naming between K1 and K2, the following mappings should be used:

**K2 → K1 Naming**:
- `FUN_00772273` → `__tls_init`
- `FUN_007744ee` → `__UNUSED_run_initializers`
- `FUN_00774f0d` → `__file_io_init`
- `FUN_00774deb` → `__get_env_vars`
- `FUN_00774d49` → `__init_cmdline_args`
- `FUN_00774b16` → `__parse_env_vars`
- `FUN_0076e02a` → `runStaticInitializations`
- `FUN_00774aad` → `FUN_00702064` (skip executable name)
- `FUN_00404250` → `WinMain`
- `FUN_0076e162` → `_internal_exit`
- `FUN_0076e184` → `_internal_exit` (second call)

## Assembly Instruction Reference

### Common Patterns

**Function Prologue**:
```
PUSH EBP           ; Save old frame pointer
MOV EBP, ESP       ; Set new frame pointer
SUB ESP, 0xXX      ; Allocate local variables
```

**Function Epilogue**:
```
MOV ESP, EBP       ; Restore stack pointer
POP EBP            ; Restore old frame pointer
RET                ; Return
```

**Calling Convention (__stdcall)**:
```
PUSH arg3          ; Push arguments right-to-left
PUSH arg2
PUSH arg1
CALL function      ; Call function
ADD ESP, 0xC       ; Clean up stack (if __cdecl, not needed for __stdcall)
```

**Conditional Jumps**:
```
CMP EAX, 0         ; Compare EAX with 0
JZ label           ; Jump if zero (equal)
JNZ label          ; Jump if not zero (not equal)
JG label           ; Jump if greater (signed)
JL label           ; Jump if less (signed)
```

## Conclusion

The entry point function performs a complete runtime initialization sequence:

1. **Exception Handling Setup**: Enables crash handling
2. **OS Version Detection**: Determines Windows version
3. **DLL Check**: Determines if running as DLL or executable
4. **Heap Initialization**: Sets up memory management
5. **TLS Initialization**: Sets up thread-local storage
6. **Static Initialization**: Runs C++ constructors
7. **File I/O Setup**: Initializes file descriptor table
8. **Command Line Parsing**: Parses arguments into `argc`/`argv`
9. **Environment Parsing**: Parses environment variables
10. **Static Initializers**: Runs additional initializers
11. **Startup Info**: Gets process startup information
12. **WinMain Call**: Calls game's main function
13. **Exit**: Cleans up and terminates process

Each step is essential for the program to run correctly. Failure at any step results in immediate termination with an error code.

## Error Handling Functions

### `_fast_error_exit()` @ 0x006fb369

**Purpose**: Terminates the process immediately with an error message when critical initialization fails.

**Function Signature**:
```c
void _fast_error_exit(DWORD errorCode);
```

**What This Function Does**:
```c
void _fast_error_exit(DWORD errorCode)
{
    // Display error message banner if enabled
    if (DAT_00833c34 == 1) {
        __FF_MSGBANNER();  // Display "Microsoft Visual C++ Runtime Library" banner
    }
    
    // Display specific error message
    __displayRuntimeError(errorCode);
    
    // Terminate process immediately (no cleanup)
    ___crtExitProcess(0xff);  // Exit with code 255
}
```

**What Happens**:
1. If error display is enabled, it shows the Visual C++ runtime library banner.
2. It displays a specific error message based on the error code.
3. It calls `___crtExitProcess(0xff)` which terminates the process immediately without cleanup.

**When It's Called**:
- Heap initialization fails (error code 0x1c / 28)
- TLS initialization fails (error code 0x10 / 16)

**Why This Matters**: These are critical failures that prevent the program from running. Immediate termination is appropriate because the runtime environment cannot be set up.

### `__amsg_exit()` @ 0x006fb344

**Purpose**: Terminates the process with an error message after displaying runtime error information.

**Function Signature**:
```c
void __amsg_exit(int errorCode);
```

**What This Function Does**:
```c
void __amsg_exit(int errorCode)
{
    // Display error message banner if enabled
    if (DAT_00833c34 == 1) {
        __FF_MSGBANNER();  // Display "Microsoft Visual C++ Runtime Library" banner
    }
    
    // Display specific error message
    __displayRuntimeError(errorCode);
    
    // Call exit handler (which will call ExitProcess)
    (*(code *)PTR___exit_007a2760)(0xff);  // Call __exit(255)
}
```

**What Happens**:
1. If error display is enabled, it shows the Visual C++ runtime library banner.
2. It displays a specific error message based on the error code.
3. It calls the exit handler which performs cleanup before calling `ExitProcess`.

**When It's Called**:
- File I/O initialization fails (error code 0x1b / 27)
- Command-line argument parsing fails (error code 0x8 / 8)
- Environment variable parsing fails (error code 0x9 / 9)
- Static initialization fails (error code from initializer)

**Why This Matters**: These errors occur after some initialization has completed, so cleanup is performed before termination.

### `__displayRuntimeError()` @ 0x00701d50

**Purpose**: Displays a runtime error message to the user.

**Function Signature**:
```c
void __displayRuntimeError(DWORD errorCode);
```

**What This Function Does** (simplified):
```c
void __displayRuntimeError(DWORD errorCode)
{
    // Look up error message in error table
    uint index = 0;
    while (index < 0x12) {  // 18 error codes
        if (errorCode == errorCodeTable[index * 2]) {
            break;
        }
        index++;
    }
    
    // If error code found in table
    if (errorCode == errorCodeTable[index * 2]) {
        if (errorDisplayEnabled) {
            // Get error message string
            char *errorMsg = errorMessageTable[index];
            size_t msgLen = strlen(errorMsg);
            
            // Write to stderr
            HANDLE stderr = GetStdHandle(STD_ERROR_HANDLE);
            WriteFile(stderr, errorMsg, msgLen, &bytesWritten, NULL);
        }
        else if (errorCode != 0xfc) {
            // Show message box for non-banner errors
            // ... (message box code)
        }
    }
    else {
        // Error code not found, show generic message
        // ... (generic error message)
    }
}
```

**Error Codes**:
- `0x1c` (28): "R6002 - floating point not loaded"
- `0x10` (16): "R6010 - abort() has been called"
- `0x1b` (27): "R6027 - not enough space for lowio initialization"
- `0x8` (8): "R6008 - not enough space for arguments"
- `0x9` (9): "R6009 - not enough space for environment"
- `0xfc` (252): Banner message
- `0xff` (255): Generic error message

**What Happens**:
1. The function looks up the error code in an internal error table.
2. If found, it retrieves the corresponding error message string.
3. If error display is enabled, it writes the message to stderr.
4. If error display is disabled and it's not a banner message, it shows a message box.

**Why This Matters**: Users need to know why the program failed to start. Error messages help diagnose initialization problems.

### `__FF_MSGBANNER()` @ 0x00701ec7

**Purpose**: Displays the Visual C++ runtime library banner.

**Function Signature**:
```c
void __FF_MSGBANNER(void);
```

**What This Function Does**:
```c
void __FF_MSGBANNER(void)
{
    if (errorDisplayEnabled || (errorDisplayEnabled == 0 && bannerEnabled == 1)) {
        // Display banner message (error code 0xfc)
        __displayRuntimeError(0xfc);
        
        // Call custom banner callback if set
        if (bannerCallback != NULL) {
            (*bannerCallback)();
        }
        
        // Display separator message (error code 0xff)
        __displayRuntimeError(0xff);
    }
}
```

**What Happens**:
1. If error display is enabled, it displays the banner.
2. It shows the "Microsoft Visual C++ Runtime Library" banner message.
3. If a custom banner callback is registered, it calls it.
4. It shows a separator line.

**Why This Matters**: The banner identifies the runtime library and provides context for error messages.

### `_internal_exit()` @ 0x006fb13f

**Purpose**: Performs cleanup and terminates the process.

**Function Signature**:
```c
void _internal_exit(UINT exitCode, int doCleanup, int isDll);
```

**Parameters**:
- `exitCode`: Process exit code
- `doCleanup`: If 0, runs exit handlers; if non-zero, skips them
- `isDll`: If 0, calls ExitProcess; if non-zero, doesn't call ExitProcess (for DLLs)

**What This Function Does**:
```c
void _internal_exit(UINT exitCode, int doCleanup, int isDll)
{
    // Acquire exit lock
    __lock(8);
    
    // If already exiting, force terminate
    if (INT_00833c28 == 1) {
        HANDLE hProcess = GetCurrentProcess();
        TerminateProcess(hProcess, exitCode);  // Force terminate
        return;  // Never returns
    }
    
    // Set exit flag
    _DAT_00833c24 = 1;
    DAT_00833c20 = (undefined1)isDll;
    
    // Run exit handlers if requested
    if (doCleanup == 0) {
        // Run atexit handlers in reverse order
        if (atexitTable != NULL) {
            void **handlerPtr = atexitTableEnd - 1;
            while (handlerPtr >= atexitTable) {
                if (*handlerPtr != NULL) {
                    (*(code *)*handlerPtr)();  // Call exit handler
                }
                handlerPtr--;
            }
        }
        
        // Run other cleanup functions
        // ... (additional cleanup)
    }
    
    // Run final cleanup functions
    // ... (final cleanup)
    
    // If not a DLL, terminate process
    if (isDll == 0) {
        INT_00833c28 = 1;  // Set exit flag
        ___crtExitProcess(exitCode);  // Terminate process
    }
    // If DLL, return (don't terminate)
}
```

**What Happens**:
1. It acquires a lock to prevent multiple threads from exiting simultaneously.
2. If already exiting, it force-terminates the process.
3. It sets exit flags.
4. If `doCleanup` is 0, it runs all functions registered with `atexit()` in reverse order.
5. It runs additional cleanup functions.
6. If not a DLL (`isDll == 0`), it calls `___crtExitProcess(exitCode)` to terminate the process.
7. If a DLL (`isDll != 0`), it returns without terminating (DLLs shouldn't call ExitProcess).

**Why This Matters**: Proper cleanup ensures:
- File handles are closed
- Memory is freed
- Static destructors are called
- Resources are released

### `___crtExitProcess()` @ 0x006fb098

**Purpose**: Terminates the process, handling .NET runtime if present.

**Function Signature**:
```c
void ___crtExitProcess(int exitCode);
```

**What This Function Does**:
```c
void ___crtExitProcess(int exitCode)
{
    HMODULE hModule;
    FARPROC pFunction;
    
    // Check if .NET runtime is loaded
    hModule = GetModuleHandleA("mscoree.dll");
    if (hModule != NULL) {
        // Get CorExitProcess function
        pFunction = GetProcAddress(hModule, "CorExitProcess");
        if (pFunction != NULL) {
            // Call .NET exit function (allows .NET cleanup)
            (*pFunction)(exitCode);
        }
    }
    
    // Terminate process (never returns)
    ExitProcess(exitCode);
}
```

**What Happens**:
1. It checks if the .NET runtime (`mscoree.dll`) is loaded.
2. If .NET is present, it calls `CorExitProcess` to allow .NET cleanup.
3. It calls `ExitProcess(exitCode)` which terminates the process immediately.

**Why This Matters**: If the program uses .NET (mixed-mode C++/CLI), the .NET runtime needs to clean up before the process terminates.

## Additional Initialization Functions

### `__get_env_vars()` @ 0x007023a2

**Purpose**: Retrieves environment variables from Windows.

**Function Signature**:
```c
LPSTR __get_env_vars(void);
```

**What This Function Does** (simplified):
```c
LPSTR __get_env_vars(void)
{
    LPWCH wideEnv = NULL;
    
    // Try to get wide-character environment strings first
    if (envVarsStringType == 0) {
        wideEnv = GetEnvironmentStringsW();
        if (wideEnv != NULL) {
            envVarsStringType = 1;  // Wide-character mode
            // Convert to ANSI and return
            // ... (conversion code)
        }
        else {
            DWORD error = GetLastError();
            if (error == 0x78) {  // ERROR_CALL_NOT_IMPLEMENTED
                envVarsStringType = 2;  // ANSI mode
            }
        }
    }
    
    // If not wide-character mode, use ANSI
    if (envVarsStringType != 1) {
        LPCH ansiEnv = GetEnvironmentStrings();
        if (ansiEnv == NULL) {
            return NULL;
        }
        
        // Calculate size needed
        char *ptr = ansiEnv;
        while (*ptr != '\0') {
            // Skip to end of variable
            while (*ptr != '\0') {
                ptr++;
            }
            ptr++;  // Skip null terminator
        }
        
        // Allocate buffer and copy
        size_t size = ptr - ansiEnv + 1;
        LPSTR buffer = _malloc(size);
        if (buffer == NULL) {
            return NULL;
        }
        
        memcpy(buffer, ansiEnv, size);
        return buffer;
    }
    
    // ... (wide-character conversion code)
}
```

**What Happens**:
1. It first tries to get wide-character (Unicode) environment strings.
2. If that fails or isn't supported, it falls back to ANSI strings.
3. It allocates a buffer and copies the environment block.
4. The environment block format is: `VAR1=value1\0VAR2=value2\0\0` (double null-terminated).

**Why This Matters**: Environment variables are needed for configuration and system information. The function handles both Unicode and ANSI systems.

### `__UNUSED_run_initializers()` @ 0x00701aa5

**Purpose**: Runs unused/optional static initializers.

**Function Signature**:
```c
void __UNUSED_run_initializers(void);
```

**What This Function Does**:
```c
void __UNUSED_run_initializers(void)
{
    undefined4 *initPtr;
    
    // Iterate through unused initializer table
    for (initPtr = &UNUSED_init_functions; 
         initPtr < &UNUSED_init_functions_end; 
         initPtr++) {
        if ((code *)*initPtr != NULL) {
            (*(code *)*initPtr)();  // Call initializer
        }
    }
}
```

**What Happens**:
1. It iterates through a table of function pointers.
2. For each non-NULL pointer, it calls the function.
3. These are typically optional initializers that don't need error checking.

**Why This Matters**: Some static initializers are optional and don't need to block program startup if they fail.

## Memory Management Details

### Heap Allocation Modes

The heap initialization selects one of three allocation modes:

**Mode 1: Standard Windows Heap**
- Uses Windows `HeapAlloc`/`HeapFree` directly
- Simple but may fragment over time
- Good for large allocations

**Mode 2: Low-Fragmentation Heap**
- Uses Windows LFH (Low-Fragmentation Heap)
- Reduces fragmentation
- Better for mixed allocation sizes

**Mode 3: Small Block Heap (SBH)**
- Custom allocator optimized for small blocks (< 1016 bytes)
- Reduces overhead for small allocations
- Better performance for many small allocations

The mode is selected based on system capabilities and configuration.

### Thread-Local Storage Structure

The TLS data structure (136 bytes / 0x88) contains:

```
Offset  Size  Field
------  ----  -----
0x00    4     Thread ID
0x04    4     Error number (errno)
0x08    4     Reserved
0x0C    4     Reserved
0x10    4     Reserved
0x14    4     Reserved
0x18    4     Reserved
0x1C    4     Reserved
0x20    4     Reserved
0x24    4     Reserved
0x28    4     Reserved
0x2C    4     Reserved
0x30    4     Reserved
0x34    4     Reserved
0x38    4     Reserved
0x3C    4     Reserved
0x40    4     Reserved
0x44    4     Reserved
0x48    4     Reserved
0x4C    4     Reserved
0x50    4     Reserved
0x54    4     Pointer to global data (offset 0x54 = 0x15 * 4)
0x58    4     Flag (set to 1)
...     ...   Additional fields
```

The exact layout varies, but key fields include:
- Thread ID for identification
- Error number for per-thread `errno`
- Heap pointers for per-thread memory management
- Other thread-specific runtime data

## Conclusion

The entry point and initialization sequence form a complete runtime environment setup:

1. **Exception Handling**: Enables crash recovery
2. **OS Detection**: Determines Windows version and capabilities
3. **Module Type Check**: Determines if running as DLL or executable
4. **Memory Management**: Sets up heap for dynamic allocation
5. **Thread Support**: Initializes TLS for multi-threading
6. **Static Initialization**: Runs C++ constructors and C initializers
7. **File I/O**: Sets up file descriptor table
8. **Command Line**: Parses arguments into `argc`/`argv`
9. **Environment**: Parses environment variables
10. **Error Handling**: Sets up error display and exit handlers
11. **Game Launch**: Calls `WinMain` to start the game
12. **Cleanup**: Performs proper shutdown on exit

Each component is essential, and failure at any critical step results in immediate termination with an appropriate error message. The unified naming between K1 and K2 allows for easier cross-game analysis and understanding.
