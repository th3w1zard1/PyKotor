"""Blender installation detection for Windows, macOS, and Linux.

This module provides functionality to:
- Detect Blender installations from registry, common paths, and PATH
- Get Blender version information
- Launch Blender with IPC server script
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class BlenderInfo:
    """Information about a detected Blender installation."""

    executable: Path
    version: tuple[int, int, int] | None = None
    version_string: str = ""
    addons_path: Path | None = None
    extensions_path: Path | None = None
    is_valid: bool = False
    has_kotorblender: bool = False
    kotorblender_version: str = ""
    error: str = ""

    def __post_init__(self):
        if self.version:
            self.version_string = f"{self.version[0]}.{self.version[1]}.{self.version[2]}"

    @property
    def supports_extensions(self) -> bool:
        """Check if Blender version supports extensions (4.2+)."""
        if self.version is None:
            return False
        return self.version >= (4, 2, 0)

    @property
    def kotorblender_path(self) -> Path | None:
        """Get the path where kotorblender should be installed."""
        if self.supports_extensions and self.extensions_path:
            return self.extensions_path / "user_default" / "io_scene_kotor"
        if self.addons_path:
            return self.addons_path / "io_scene_kotor"
        return None


def _get_windows_registry_blender_paths() -> list[Path]:
    """Get Blender paths from Windows registry."""
    paths: list[Path] = []

    if sys.platform != "win32":
        return paths

    try:
        import winreg

        # Check HKEY_LOCAL_MACHINE for system-wide installations
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BlenderFoundation\Blender"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\BlenderFoundation\Blender"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\BlenderFoundation\Blender"),
        ]

        for hkey, key_path in registry_keys:
            try:
                with winreg.OpenKey(hkey, key_path) as key:
                    # Enumerate subkeys (version numbers like "4.2", "3.6")
                    i = 0
                    while True:
                        try:
                            version_key = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, version_key) as ver_key:
                                try:
                                    install_path, _ = winreg.QueryValueEx(ver_key, "")
                                    if install_path:
                                        exe_path = Path(install_path) / "blender.exe"
                                        if exe_path.is_file():
                                            paths.append(exe_path)
                                except FileNotFoundError:
                                    pass
                            i += 1
                        except OSError:
                            break
            except FileNotFoundError:
                continue
    except ImportError:
        pass

    return paths


def _get_common_blender_paths() -> list[Path]:
    """Get common Blender installation paths based on OS."""
    paths: list[Path] = []
    system = platform.system()

    if system == "Windows":
        # Common Windows installation paths
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_appdata = os.environ.get("LOCALAPPDATA", "")

        common_dirs = [
            Path(program_files) / "Blender Foundation",
            Path(program_files_x86) / "Blender Foundation",
            Path.home() / "AppData" / "Local" / "Blender Foundation",
        ]

        # Steam installation
        steam_paths = [
            Path(program_files_x86) / "Steam" / "steamapps" / "common" / "Blender",
            Path(program_files) / "Steam" / "steamapps" / "common" / "Blender",
            Path.home() / "Steam" / "steamapps" / "common" / "Blender",
        ]
        common_dirs.extend(steam_paths)

        for base_dir in common_dirs:
            if base_dir.is_dir():
                # Look for version subdirectories
                for item in base_dir.iterdir():
                    if item.is_dir():
                        exe = item / "blender.exe"
                        if exe.is_file():
                            paths.append(exe)
                # Also check directly in base
                exe = base_dir / "blender.exe"
                if exe.is_file():
                    paths.append(exe)

    elif system == "Darwin":  # macOS
        # Standard macOS installation paths
        app_paths = [
            Path("/Applications/Blender.app/Contents/MacOS/Blender"),
            Path.home() / "Applications" / "Blender.app" / "Contents" / "MacOS" / "Blender",
        ]

        # Check for versioned installations
        for apps_dir in [Path("/Applications"), Path.home() / "Applications"]:
            if apps_dir.is_dir():
                for item in apps_dir.iterdir():
                    if item.name.startswith("Blender") and item.suffix == ".app":
                        exe = item / "Contents" / "MacOS" / "Blender"
                        if exe.is_file():
                            paths.append(exe)

        paths.extend([p for p in app_paths if p.is_file()])

    else:  # Linux
        # Standard Linux installation paths
        linux_paths = [
            Path("/usr/bin/blender"),
            Path("/usr/local/bin/blender"),
            Path("/snap/bin/blender"),
            Path.home() / ".local" / "bin" / "blender",
            Path("/opt/blender/blender"),
        ]

        # Flatpak
        flatpak_path = Path.home() / ".local" / "share" / "flatpak" / "exports" / "bin" / "org.blender.Blender"
        if flatpak_path.is_file():
            paths.append(flatpak_path)

        # Check common locations
        for p in linux_paths:
            if p.is_file():
                paths.append(p)

        # Check for extracted tar.gz installations
        opt_blender = Path("/opt")
        if opt_blender.is_dir():
            for item in opt_blender.iterdir():
                if item.is_dir() and item.name.lower().startswith("blender"):
                    exe = item / "blender"
                    if exe.is_file():
                        paths.append(exe)

    return paths


def _get_blender_from_path() -> Path | None:
    """Get Blender from system PATH."""
    blender_exe = shutil.which("blender")
    if blender_exe:
        return Path(blender_exe)
    return None


def get_blender_version(executable: Path) -> tuple[int, int, int] | None:
    """Get Blender version from executable.

    Args:
        executable: Path to Blender executable

    Returns:
        Tuple of (major, minor, patch) version numbers, or None if failed
    """
    try:
        result = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        # Parse version from output like "Blender 4.2.0"
        match = re.search(r"Blender\s+(\d+)\.(\d+)\.(\d+)", result.stdout)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
        RobustLogger().warning(f"Failed to get Blender version: {e}")

    return None


def _get_blender_config_paths(version: tuple[int, int, int]) -> tuple[Path | None, Path | None]:
    """Get Blender addons and extensions paths for a given version.

    Args:
        version: Blender version tuple (major, minor, patch)

    Returns:
        Tuple of (addons_path, extensions_path)
    """
    version_str = f"{version[0]}.{version[1]}"
    system = platform.system()

    addons_path: Path | None = None
    extensions_path: Path | None = None

    if system == "Windows":
        base = Path(os.environ.get("APPDATA", "")) / "Blender Foundation" / "Blender" / version_str
        addons_path = base / "scripts" / "addons"
        extensions_path = base / "extensions"

    elif system == "Darwin":  # macOS
        base = Path.home() / "Library" / "Application Support" / "Blender" / version_str
        addons_path = base / "scripts" / "addons"
        extensions_path = base / "extensions"

    else:  # Linux
        base = Path.home() / ".config" / "blender" / version_str
        addons_path = base / "scripts" / "addons"
        extensions_path = base / "extensions"

    return addons_path, extensions_path


def _check_kotorblender_installed(info: BlenderInfo) -> bool:
    """Check if kotorblender is installed and get its version.

    Args:
        info: BlenderInfo to update with kotorblender status

    Returns:
        True if kotorblender is installed
    """
    kotorblender_path = info.kotorblender_path
    if kotorblender_path is None:
        return False

    init_file = kotorblender_path / "__init__.py"
    if not init_file.is_file():
        return False

    # Try to extract version from __init__.py
    try:
        content = init_file.read_text(encoding="utf-8")
        # Look for bl_info version
        match = re.search(r'"version"\s*:\s*\((\d+),\s*(\d+),\s*(\d+)\)', content)
        if match:
            info.kotorblender_version = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
            return True
    except OSError:
        pass

    # File exists but couldn't parse version
    return True


def find_blender_executable(
    custom_path: Path | str | None = None,
    min_version: tuple[int, int, int] = (3, 6, 0),
) -> BlenderInfo | None:
    """Find a valid Blender installation.

    Args:
        custom_path: Optional custom path to Blender executable
        min_version: Minimum required Blender version (default 3.6.0)

    Returns:
        BlenderInfo if found, None otherwise
    """
    candidates: list[Path] = []

    # Custom path takes priority
    if custom_path:
        custom = Path(custom_path)
        if custom.is_file():
            candidates.append(custom)
        elif custom.is_dir():
            # Check for blender executable in directory
            for name in ["blender", "blender.exe", "Blender"]:
                exe = custom / name
                if exe.is_file():
                    candidates.append(exe)
                    break

    # Check PATH
    path_blender = _get_blender_from_path()
    if path_blender:
        candidates.append(path_blender)

    # Windows registry
    if sys.platform == "win32":
        candidates.extend(_get_windows_registry_blender_paths())

    # Common paths
    candidates.extend(_get_common_blender_paths())

    # Remove duplicates while preserving order
    seen: set[Path] = set()
    unique_candidates: list[Path] = []
    for c in candidates:
        resolved = c.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_candidates.append(c)

    # Find best candidate
    best_info: BlenderInfo | None = None
    best_version: tuple[int, int, int] = (0, 0, 0)

    for candidate in unique_candidates:
        version = get_blender_version(candidate)
        if version is None:
            continue

        if version < min_version:
            RobustLogger().debug(f"Blender {version} at {candidate} is below minimum {min_version}")
            continue

        addons_path, extensions_path = _get_blender_config_paths(version)

        info = BlenderInfo(
            executable=candidate,
            version=version,
            addons_path=addons_path,
            extensions_path=extensions_path,
            is_valid=True,
        )

        info.has_kotorblender = _check_kotorblender_installed(info)

        # Prefer installations with kotorblender, then by version
        if info.has_kotorblender and (best_info is None or not best_info.has_kotorblender):
            best_info = info
            best_version = version
        elif info.has_kotorblender == (best_info.has_kotorblender if best_info else False):
            if version > best_version:
                best_info = info
                best_version = version
        elif best_info is None:
            best_info = info
            best_version = version

    return best_info


def detect_blender(
    custom_path: Path | str | None = None,
    min_version: tuple[int, int, int] = (3, 6, 0),
) -> BlenderInfo:
    """Detect Blender installation with full status information.

    Args:
        custom_path: Optional custom path to Blender executable
        min_version: Minimum required Blender version

    Returns:
        BlenderInfo with detection results (check is_valid for success)
    """
    info = find_blender_executable(custom_path, min_version)

    if info is None:
        return BlenderInfo(
            executable=Path(""),
            is_valid=False,
            error="No valid Blender installation found. Please install Blender 3.6 or later.",
        )

    if not info.has_kotorblender:
        info.error = (
            f"Blender {info.version_string} found but kotorblender add-on is not installed. "
            "Please install kotorblender from https://deadlystream.com/files/file/1853-kotorblender/"
        )

    return info


def is_blender_available(
    custom_path: Path | str | None = None,
    min_version: tuple[int, int, int] = (3, 6, 0),
) -> bool:
    """Quick check if a valid Blender with kotorblender is available.

    Args:
        custom_path: Optional custom path to Blender executable
        min_version: Minimum required Blender version

    Returns:
        True if Blender with kotorblender is available
    """
    info = detect_blender(custom_path, min_version)
    return info.is_valid and info.has_kotorblender


def launch_blender_with_ipc(
    blender_info: BlenderInfo,
    *,
    ipc_port: int = 7531,
    installation_path: Path | str | None = None,
    module_path: Path | str | None = None,
    blend_file: Path | str | None = None,
    background: bool = False,
) -> subprocess.Popen | None:
    """Launch Blender with IPC server enabled.

    Args:
        blender_info: BlenderInfo from detect_blender()
        ipc_port: Port for IPC server (default 7531)
        installation_path: Path to KotOR installation for resource lookup
        module_path: Path to module file to open
        blend_file: Optional .blend file to open
        background: Run Blender in background mode (no UI)

    Returns:
        Popen object for the Blender process, or None if launch failed
    """
    if not blender_info.is_valid:
        RobustLogger().error(f"Cannot launch invalid Blender: {blender_info.error}")
        return None

    # Build startup script that initializes IPC server
    startup_script = _generate_ipc_startup_script(ipc_port, installation_path, module_path)

    # Build command line
    cmd: list[str] = [str(blender_info.executable)]

    if background:
        cmd.append("--background")

    if blend_file:
        cmd.append(str(blend_file))

    # Execute Python script on startup
    cmd.extend(["--python-expr", startup_script])

    try:
        # Don't create console window on Windows
        kwargs: dict = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        process = subprocess.Popen(cmd, **kwargs)
        RobustLogger().info(f"Launched Blender (PID: {process.pid}) with IPC on port {ipc_port}")
        return process

    except OSError as e:
        RobustLogger().error(f"Failed to launch Blender: {e}")
        return None


def _generate_ipc_startup_script(
    port: int,
    installation_path: Path | str | None,
    module_path: Path | str | None,
) -> str:
    """Generate Python script to run on Blender startup.

    This script starts the IPC server and optionally loads a module.
    """
    # Escape paths for Python string
    def escape_path(p: Path | str | None) -> str:
        if p is None:
            return "None"
        return repr(str(p))

    script = f'''
import sys
import traceback

# Try to import and start IPC server
try:
    from io_scene_kotor.ipc import start_ipc_server
    start_ipc_server(port={port}, installation_path={escape_path(installation_path)})
    print(f"[HolocronToolset] IPC server started on port {port}")
except ImportError as e:
    print(f"[HolocronToolset] Warning: Could not start IPC server: {{e}}")
    print("[HolocronToolset] kotorblender IPC module not found. Make sure kotorblender is properly installed.")
except Exception as e:
    print(f"[HolocronToolset] Error starting IPC server: {{e}}")
    traceback.print_exc()
'''

    return script


# Settings integration
class BlenderSettings:
    """Settings for Blender integration."""

    def __init__(self):
        self._custom_path: str = ""
        self._auto_launch: bool = True
        self._ipc_port: int = 7531
        self._prefer_blender: bool = False
        self._remember_choice: bool = False

    @property
    def custom_path(self) -> str:
        """Custom Blender executable path."""
        return self._custom_path

    @custom_path.setter
    def custom_path(self, value: str):
        self._custom_path = value

    @property
    def auto_launch(self) -> bool:
        """Automatically launch Blender when needed."""
        return self._auto_launch

    @auto_launch.setter
    def auto_launch(self, value: bool):
        self._auto_launch = value

    @property
    def ipc_port(self) -> int:
        """Port for IPC communication."""
        return self._ipc_port

    @ipc_port.setter
    def ipc_port(self, value: int):
        self._ipc_port = value

    @property
    def prefer_blender(self) -> bool:
        """Prefer Blender over built-in editor when available."""
        return self._prefer_blender

    @prefer_blender.setter
    def prefer_blender(self, value: bool):
        self._prefer_blender = value

    @property
    def remember_choice(self) -> bool:
        """Remember editor choice and don't ask again."""
        return self._remember_choice

    @remember_choice.setter
    def remember_choice(self, value: bool):
        self._remember_choice = value

    def get_blender_info(self) -> BlenderInfo:
        """Get BlenderInfo using current settings."""
        custom = Path(self._custom_path) if self._custom_path else None
        return detect_blender(custom)


# Global settings instance
_blender_settings: BlenderSettings | None = None


def get_blender_settings() -> BlenderSettings:
    """Get global Blender settings instance."""
    global _blender_settings
    if _blender_settings is None:
        _blender_settings = BlenderSettings()
    return _blender_settings

