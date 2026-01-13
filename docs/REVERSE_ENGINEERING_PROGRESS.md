# KOTOR II Reverse Engineering Progress

## Overview

This document tracks the reverse engineering progress for `swkotor2_aspyr.exe` using Ghidra and REVA MCP tools. Functions are being analyzed, labeled, and documented to build a comprehensive understanding of the game engine.

## Analysis Status

**Total Functions**: 15,313  
**Functions Labeled**: 10  
**Functions Documented**: 10  
**Progress**: 0.07%

**Symbol Statistics** (via `manage-symbols`):
- **Total Symbols**: 45,800 (default names filtered)
- **Namespaces**: 1,084 identified
- **Classes**: 0 (C++ classes not detected as separate entities)
- **Exports**: 1 (`entry` function)

## Labeled Functions

### Initialization Functions

#### `entry` @ `0x0091d5a2`
- **Type**: Entry Point
- **Description**: Standard Windows executable entry point. Calls C runtime initialization.
- **Calls**: `___security_init_cookie()`, `___tmainCRTStartup()`

#### `GameMain_Initialize` @ `0x00407920`
- **Type**: Main Game Initialization
- **Signature**: `void GameMain_Initialize(HINSTANCE hInstance)`
- **Description**: Main game initialization function. Creates singleton mutex ("swkotor2"), initializes COM, loads configuration files (config.txt, swKotor2.ini), creates main window, and initializes game subsystems.
- **Key Operations**:
  - Creates mutex to prevent multiple instances
  - Initializes COM (CoInitialize)
  - Executes config.txt
  - Loads swKotor2.ini configuration
  - Creates main game window
  - Initializes Steam API
  - Sets up sound system
  - Initializes graphics subsystem

#### `InitializeGameState` @ `0x00402510`
- **Type**: Game State Initialization
- **Signature**: `void InitializeGameState(void)`
- **Description**: Initializes game state variables and subsystems. Sets up initial state flags and calls subsystem initialization functions.
- **Operations**:
  - Initializes state variables at `0x00a13c28`, `0x00a13c2c`, `0x00a13c30`
  - Calls `InitializeSubsystem1()` @ `0x00402240` and `InitializeSubsystem2()` @ `0x00401e00`

#### `InitializeGameFlags` @ `0x00401000`
- **Type**: Flag Initialization
- **Signature**: `void InitializeGameFlags(void)`
- **Description**: Initializes game state flags at `0x00a13c20-0x00a13c24`. These appear to be boolean flags used for game state tracking. Called during initialization and from game logic.
- **Operations**:
  - Sets `g_gameFlag1` through `g_gameFlag5` to 0

### Configuration Functions

#### `ExecuteConfigFile` @ `0x004763b0`
- **Type**: Configuration Parser
- **Signature**: `void ExecuteConfigFile(char *filename)`
- **Description**: Executes a configuration file (e.g., config.txt, startup.txt). Parses file line by line, strips whitespace, skips comments (#), and executes each command via `ExecuteConfigCommand()` @ `0x004752a0`. Used for game configuration and startup scripts.
- **Features**:
  - Line-by-line parsing
  - Whitespace trimming
  - Comment support (#)
  - Command execution
- **Called From**: `GameMain_Initialize` (config.txt, startup.txt)

### Window Management Functions

#### `CreateMainWindow` @ `0x004087a0`
- **Type**: Window Creation
- **Signature**: `HWND CreateMainWindow(HINSTANCE hInstance)`
- **Description**: Creates and registers the main game window. Handles window class registration, monitor detection, window positioning, and returns the HWND handle. Called during game initialization.
- **Returns**: HWND of created window

#### `SetDPIAwareness` @ `0x004072b0`
- **Type**: DPI Configuration
- **Signature**: `void SetDPIAwareness(void)`
- **Description**: Sets DPI awareness for the process by dynamically loading and calling `SetProcessDPIAware` from user32.dll. This ensures proper scaling on high-DPI displays.

### Platform Integration Functions

#### `InitializeSteamAPI` @ `0x004072f0`
- **Type**: Steam Integration
- **Signature**: `uint InitializeSteamAPI(void)`
- **Description**: Initializes Steam API and verifies game ownership. Returns non-zero if Steam is initialized and game is owned. Shows error messages if Steam initialization fails or game is not owned.
- **Returns**: Non-zero on success, 0 on failure

#### `LoadSteamWorkshopItems` @ `0x004076f0`
- **Type**: Steam Workshop Integration
- **Signature**: `void LoadSteamWorkshopItems(void)`
- **Description**: Loads Steam Workshop (UGC) items. Retrieves up to 30 subscribed items and processes them via `ProcessSteamWorkshopItem()` @ `0x004073b0`. Called after Steam API initialization if Steam is available.

### System Configuration Functions

#### `DisableScreenSaver` @ `0x0040c090`
- **Type**: System Configuration
- **Signature**: `void DisableScreenSaver(void)`
- **Description**: Disables screen saver during gameplay. Uses `SystemParametersInfoA` with `SPI_GETSCREENSAVETIMEOUT` (0x5E) to get current timeout, stores it, then disables with `SPI_SETSCREENSAVETIMEOUT` (0x5D). Prevents screen saver from activating during gameplay.

#### `DisableMonitorPowerSave` @ `0x0040c100`
- **Type**: System Configuration
- **Signature**: `void DisableMonitorPowerSave(void)`
- **Description**: Disables monitor power save mode during gameplay. Uses `SystemParametersInfoA` with `SPI_GETPOWEROFFTIMEOUT` (0x10) to get current timeout, stores it, then disables with `SPI_SETPOWEROFFTIMEOUT` (0x11). Prevents monitor from sleeping during gameplay.

## Global Variables

### Game State Flags

| Address | Name | Type | Description | Status |
|---------|------|------|-------------|-------|
| `0x00a13c20` | `g_gameFlag1` | `byte` | Game state flag 1 | ✅ Labeled |
| `0x00a13c21` | `g_gameFlag2` | `byte` | Game state flag 2 | ✅ Labeled |
| `0x00a13c22` | `g_gameFlag3` | `byte` | Game state flag 3 | ✅ Labeled |
| `0x00a13c23` | `g_gameFlag4` | `byte` | Game state flag 4 | ✅ Labeled |
| `0x00a13c24` | `g_gameFlag5` | `byte` | Game state flag 5 | ✅ Labeled |

### Game State Variables

| Address | Name | Type | Description | Status |
|---------|------|------|-------------|-------|
| `0x00a13c28` | `g_gameStateVar1` | `dword` | Game state variable 1 (initialized to 0) | ✅ Labeled |
| `0x00a13c2c` | `g_gameStateVar2` | `dword` | Game state variable 2 (initialized to 0) | ✅ Labeled |
| `0x00a13c30` | `g_gameStateVar3` | `dword` | Game state variable 3 (initialized to 0xFFFFFFFF) | ✅ Labeled |

### Global Pointers

| Address | Name | Type | Description | Status |
|---------|------|------|-------------|-------|
| `0x00a1b488` | `g_configObject` | `int*` | Pointer to configuration object (set from `SetConfigObject()` @ `0x00735c60`) | ✅ Labeled |
| `0x00a1b4a4` | `g_gameObject` | `COleDispParams*` | Pointer to game object (set from `SetGameObject()` @ `0x00401730`) | ✅ Labeled |

### System Configuration Variables

| Address | Name | Type | Description | Status |
|---------|------|------|-------------|-------|
| `0x00a1b754` | `g_screenSaverTimeout` | `int` | Stored screen saver timeout value (saved before disabling) | ✅ Labeled |
| `0x00a1b758` | `g_monitorPowerSaveTimeout` | `int` | Stored monitor power save timeout value (saved before disabling) | ✅ Labeled |

## Function Call Hierarchy

### Initialization Flow

```
entry (0x0091d5a2)
  └─> ___tmainCRTStartup (0x0091d424)
      └─> GameMain_Initialize (0x00407920)
          ├─> InitializeGameState (0x00402510)
          ├─> ExecuteConfigFile("config.txt") (0x004763b0)
          ├─> CreateMainWindow (0x004087a0)
          ├─> SetDPIAwareness (0x004072b0)
          ├─> InitializeSteamAPI (0x004072f0)
          ├─> LoadSteamWorkshopItems (0x004076f0) [if Steam initialized]
          ├─> DisableScreenSaver (0x0040c090)
          ├─> DisableMonitorPowerSave (0x0040c100)
          └─> [Other subsystem initializations]
```

## Bookmarks

### Analysis Bookmarks

- **0x00407920** (Analysis): Main game initialization entry point
- **0x00401000** (Note): Game flag initialization

## Next Steps

1. **Continue Function Analysis**:
   - Analyze `ExecuteConfigCommand()` @ `0x004752a0` (config command executor) ✅ Labeled
   - Analyze `InitializeSubsystem1()` @ `0x00402240` and `InitializeSubsystem2()` @ `0x00401e00` ✅ Labeled
   - Analyze `ProcessSteamWorkshopItem()` @ `0x004073b0` (Steam Workshop item processor) ✅ Labeled
   - Analyze `SetConfigObject()` @ `0x00735c60` and `SetGameObject()` @ `0x00401730` ✅ Labeled
   - Analyze `LargeFunction_00531c50()` @ `0x00531c50` (large function, needs investigation) ✅ Labeled

2. **Identify Game Engine Systems**:
   - Resource loading system
   - Rendering system
   - Audio system
   - Scripting system
   - Save/load system

3. **Document Data Structures**:
   - Configuration structures
   - Game object structures
   - Resource structures

4. **Create Function Tags**:
   - Tag functions by system (Graphics, Audio, Resource, etc.)
   - Tag initialization functions
   - Tag utility functions

## Notes

- The executable is completely unpacked, allowing direct analysis
- Entry point follows standard Windows PE structure
- Game uses Steam API for DRM/ownership verification
- Configuration system uses text files (config.txt, startup.txt) with command-based syntax
- Multiple subsystems are initialized during startup

## Tools Used

- **Ghidra**: Static analysis and reverse engineering
- **REVA MCP Server**: Function management, labeling, commenting, bookmarking
  - `manage-symbols`: Symbol analysis, import/export listing, namespace enumeration, data label renaming
  - `manage-functions`: Function renaming, tagging, analysis
  - `manage-comments`: Code annotation and documentation
  - `manage-bookmarks`: Analysis markers and notes
- **Analysis Method**: Static analysis of decompiled code

## Symbol Analysis

### Key Namespaces Identified

The executable contains 1,084 namespaces, indicating extensive use of C++ classes and namespaces. Key namespaces include:

**Aurora Engine (Rendering)**:
- `CAurora`, `CAuroraModel`, `CAuroraTexture`, `CAuroraModelX`
- `CAurObject`, `CAurScene`, `CAurCamera`, `CAurBehavior`
- `CAurInternal`, `CAurInternalGL`, `CAurGUIDraw`

**Exo Engine (Core Systems)**:
- `CExoInput`, `CExoPackedFile`, `CExoResFile`, `CExoSoundSource`
- `CExoResourceImageFile`, `CExoEncapsulatedFile`

**Game Systems**:
- `CGameObject`, `CGameEffectApplierRemover`, `CItemPropertyApplierRemover`
- `CClientExoApp`, `CBaseExoApp`

**Resource Management**:
- `CRes`, `CRes2DA`, `CRes4PC`, `CResARE`, `CResBWM`, `CResDDS`, `CResGFF`
- `CResHelper` (template class for various resource types)

**Steam Integration**:
- `CCallback`, `CCallbackBase`, `CCallResult` (Steam callback system)

**MFC Framework** (UI):
- `CFrameWnd`, `CMFCRibbonCategory`, `CMFCToolBarButtonsListButton`
- `CMFCVisualManagerBitmapCache`, `CMFCWindowsManagerDialog`

**Concurrency**:
- `Concurrency::details::*` (Microsoft Concurrency Runtime)

### Symbol Count

- **Total Symbols**: 45,800 (with default Ghidra-generated names filtered)
- This includes functions, labels, data symbols, and imported symbols

## References

- See `ASPYR_KOTOR_ANALYSIS.md` for protection analysis
- See `STEAM_VS_GOG_KOTOR_DIFFERENCES.md` for version comparison
