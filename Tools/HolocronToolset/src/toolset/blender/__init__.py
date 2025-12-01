"""Blender integration module for HolocronToolset.

This module provides functionality to use Blender as an alternative 3D editor
for the Module Designer, Indoor Map Builder, and GIT Editor, replacing the
built-in PyKotorGL Scene renderer.

Architecture:
- detection.py: Blender installation detection
- ipc_client.py: JSON-RPC IPC client for communicating with Blender
- serializers.py: Serialize GIT, LYT, Module data for IPC
- commands.py: Command definitions for Blender operations
- integration.py: Mixin classes for editor integration
"""

from __future__ import annotations

from toolset.blender.detection import (
    BlenderInfo,
    BlenderSettings,
    check_kotorblender_installed,
    detect_blender,
    find_all_blender_installations,
    find_blender_executable,
    get_blender_settings,
    get_blender_version,
    install_kotorblender,
    is_blender_available,
    launch_blender_with_ipc,
    uninstall_kotorblender,
)
from toolset.blender.integration import (
    BlenderEditorMixin,
    check_blender_and_ask,
)
from toolset.blender.commands import (
    BlenderEditorController,
    BlenderEditorMode,
    BlenderSession,
    get_blender_controller,
)
from toolset.blender.ipc_client import (
    BlenderCommands,
    BlenderIPCClient,
    ConnectionState,
    get_ipc_client,
)

__all__ = [
    # Detection
    "BlenderInfo",
    "BlenderSettings",
    "check_kotorblender_installed",
    "detect_blender",
    "find_all_blender_installations",
    "find_blender_executable",
    "get_blender_settings",
    "get_blender_version",
    "install_kotorblender",
    "is_blender_available",
    "launch_blender_with_ipc",
    "uninstall_kotorblender",
    # Integration
    "BlenderEditorMixin",
    "check_blender_and_ask",
    # Commands
    "BlenderEditorController",
    "BlenderEditorMode",
    "BlenderSession",
    "get_blender_controller",
    # IPC
    "BlenderCommands",
    "BlenderIPCClient",
    "ConnectionState",
    "get_ipc_client",
]

