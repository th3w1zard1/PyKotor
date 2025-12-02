"""Blender installation detection for Windows, macOS, and Linux.

This module provides functionality to:
- Detect Blender installations from registry, common paths, and PATH
- Get Blender version information
- Install kotorblender addon
- Launch Blender with IPC server script

References:
    vendor/kotorblender/README.md (installation instructions)
    Libraries/PyKotor/src/pykotor/tools/path.py (find_kotor_paths_from_default pattern)
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from collections.abc import Iterator


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


def _get_default_blender_paths() -> dict[str, list[str]]:
    """Get default Blender installation paths by OS.
    
    Similar to find_kotor_paths_from_default pattern in pykotor.tools.path.
    """
    return {
        "Windows": [
            # Blender Foundation standard paths
            r"{ProgramFiles}\Blender Foundation\Blender *\blender.exe",
            r"{ProgramFiles(x86)}\Blender Foundation\Blender *\blender.exe",
            r"{LOCALAPPDATA}\Blender Foundation\Blender *\blender.exe",
            # Steam
            r"{ProgramFiles}\Steam\steamapps\common\Blender\blender.exe",
            r"{ProgramFiles(x86)}\Steam\steamapps\common\Blender\blender.exe",
            r"~\Steam\steamapps\common\Blender\blender.exe",
            # Chocolatey
            r"C:\ProgramData\chocolatey\lib\blender\tools\blender.exe",
            # Portable/custom
            r"C:\Blender\blender.exe",
            r"~\Blender\blender.exe",
        ],
        "Darwin": [
            # Standard macOS installation
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "~/Applications/Blender.app/Contents/MacOS/Blender",
            # Versioned installations
            "/Applications/Blender*.app/Contents/MacOS/Blender",
            "~/Applications/Blender*.app/Contents/MacOS/Blender",
            # Homebrew
            "/opt/homebrew/bin/blender",
            "/usr/local/bin/blender",
        ],
        "Linux": [
            # Package manager installations
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            # Snap
            "/snap/bin/blender",
            "/var/lib/snapd/snap/bin/blender",
            # Flatpak
            "~/.local/share/flatpak/exports/bin/org.blender.Blender",
            "/var/lib/flatpak/exports/bin/org.blender.Blender",
            # Manual/portable installations
            "~/.local/bin/blender",
            "/opt/blender/blender",
            "/opt/blender*/blender",
            "~/blender*/blender",
            # Steam (Proton/Linux native)
            "~/.steam/steam/steamapps/common/Blender/blender",
            "~/.local/share/Steam/steamapps/common/Blender/blender",
        ],
    }


def _expand_path_pattern(pattern: str) -> Iterator[Path]:
    """Expand a path pattern with environment variables and globs.
    
    Supports:
    - {EnvVar} syntax for environment variables
    - ~ for home directory
    - * wildcards for glob matching
    """
    # Expand environment variables in {VAR} format
    def expand_env(m: re.Match) -> str:
        return os.environ.get(m.group(1), m.group(0))
    
    expanded = re.sub(r"\{(\w+)\}", expand_env, pattern)
    
    # Expand ~ to home directory
    expanded = os.path.expanduser(expanded)
    
    # If pattern contains wildcards, use glob
    if "*" in expanded:
        from glob import glob
        for match in glob(expanded):
            yield Path(match)
    else:
        path = Path(expanded)
        if path.exists():
            yield path


def _get_common_blender_paths() -> list[Path]:
    """Get common Blender installation paths based on OS."""
    paths: list[Path] = []
    system = platform.system()

    # Get paths from default patterns
    default_paths = _get_default_blender_paths()
    patterns = default_paths.get(system, [])
    
    for pattern in patterns:
        for path in _expand_path_pattern(pattern):
            if path.is_file():
                paths.append(path)
            elif path.is_dir():
                # Check for blender executable in directory
                for name in ["blender", "blender.exe", "Blender"]:
                    exe = path / name
                    if exe.is_file():
                        paths.append(exe)
                        break

    # Additional directory scanning for versioned installations
    if system == "Windows":
        for base_env in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"]:
            base = os.environ.get(base_env, "")
            if not base:
                continue
            bf_path = Path(base) / "Blender Foundation"
            if bf_path.is_dir():
                for item in bf_path.iterdir():
                    if item.is_dir() and item.name.lower().startswith("blender"):
                        exe = item / "blender.exe"
                        if exe.is_file() and exe not in paths:
                            paths.append(exe)
    
    elif system == "Darwin":
        for apps_dir in [Path("/Applications"), Path.home() / "Applications"]:
            if apps_dir.is_dir():
                for item in apps_dir.iterdir():
                    if item.name.startswith("Blender") and item.suffix == ".app":
                        exe = item / "Contents" / "MacOS" / "Blender"
                        if exe.is_file() and exe not in paths:
                            paths.append(exe)
    
    elif system == "Linux":
        for opt_dir in [Path("/opt"), Path.home()]:
            if opt_dir.is_dir():
                for item in opt_dir.iterdir():
                    if item.is_dir() and item.name.lower().startswith("blender"):
                        exe = item / "blender"
                        if exe.is_file() and exe not in paths:
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
        kwargs: dict = {"capture_output": True, "text": True, "timeout": 10}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(
            [str(executable), "--version"],
            **kwargs,
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


def check_kotorblender_installed(info: BlenderInfo) -> bool:
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


def find_all_blender_installations(
    min_version: tuple[int, int, int] = (3, 6, 0),
) -> list[BlenderInfo]:
    """Find ALL valid Blender installations on the system.
    
    Similar to find_kotor_paths_from_default pattern.

    Args:
        min_version: Minimum required Blender version (default 3.6.0)

    Returns:
        List of BlenderInfo for all found installations, sorted by version (newest first)
    """
    candidates: list[Path] = []

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
        try:
            resolved = c.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique_candidates.append(c)
        except (OSError, RuntimeError):
            continue

    # Build info for each valid installation
    installations: list[BlenderInfo] = []
    
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

        info.has_kotorblender = check_kotorblender_installed(info)
        installations.append(info)

    # Sort by version (newest first), then by kotorblender status
    installations.sort(key=lambda x: (x.has_kotorblender, x.version or (0, 0, 0)), reverse=True)
    
    return installations


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
    # Custom path takes priority
    if custom_path:
        custom = Path(custom_path)
        executable: Path | None = None
        
        if custom.is_file():
            executable = custom
        elif custom.is_dir():
            # Check for blender executable in directory
            for name in ["blender", "blender.exe", "Blender"]:
                exe = custom / name
                if exe.is_file():
                    executable = exe
                    break
            # macOS .app bundle
            if executable is None and custom.suffix == ".app":
                exe = custom / "Contents" / "MacOS" / "Blender"
                if exe.is_file():
                    executable = exe
        
        if executable:
            version = get_blender_version(executable)
            if version and version >= min_version:
                addons_path, extensions_path = _get_blender_config_paths(version)
                info = BlenderInfo(
                    executable=executable,
                    version=version,
                    addons_path=addons_path,
                    extensions_path=extensions_path,
                    is_valid=True,
                )
                info.has_kotorblender = check_kotorblender_installed(info)
                return info

    # Find all installations and return the best one
    installations = find_all_blender_installations(min_version)
    return installations[0] if installations else None


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
            "Click 'Install kotorblender' to install it automatically."
        )

    return info


def _get_kotorblender_source_path() -> Path | None:
    """Find the kotorblender source directory.
    
    Works for both:
    - Running from source: vendor/kotorblender/io_scene_kotor
    - PyInstaller builds: bundled in _MEIPASS/kotorblender/io_scene_kotor
    
    Returns:
        Path to io_scene_kotor directory, or None if not found
    """
    # Check for PyInstaller frozen build
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        
        # Check bundled location
        bundled_path = bundle_dir / "kotorblender" / "io_scene_kotor"
        if bundled_path.is_dir() and (bundled_path / "__init__.py").is_file():
            return bundled_path
        
        # Alternative bundled location
        bundled_path2 = bundle_dir / "io_scene_kotor"
        if bundled_path2.is_dir() and (bundled_path2 / "__init__.py").is_file():
            return bundled_path2
    
    # Running from source - find repo root
    current_file = Path(__file__).resolve()
    
    # Go up from Tools/HolocronToolset/src/toolset/blender/detection.py to repo root
    for parent in current_file.parents:
        vendor_path = parent / "vendor" / "kotorblender" / "io_scene_kotor"
        if vendor_path.is_dir() and (vendor_path / "__init__.py").is_file():
            return vendor_path
    
    return None


def install_kotorblender(
    info: BlenderInfo,
    source_path: Path | str | None = None,
) -> tuple[bool, str]:
    """Install kotorblender addon to Blender's addons/extensions directory.
    
    Works for both source installations and PyInstaller builds.
    Installation is idempotent - safe to call multiple times.

    Args:
        info: BlenderInfo with valid Blender installation
        source_path: Optional custom path to kotorblender source (io_scene_kotor dir)

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not info.is_valid:
        return False, "Invalid Blender installation"

    kotorblender_dest = info.kotorblender_path
    if kotorblender_dest is None:
        return False, "Cannot determine kotorblender installation path for this Blender version"

    # Find kotorblender source
    if source_path:
        kotorblender_src = Path(source_path)
    else:
        kotorblender_src = _get_kotorblender_source_path()
    
    if kotorblender_src is None or not kotorblender_src.is_dir():
        return False, (
            "kotorblender source not found.\n\n"
            "Please download kotorblender manually from:\n"
            "https://deadlystream.com/files/file/1853-kotorblender/\n\n"
            "Then extract and select the io_scene_kotor folder."
        )
    
    init_file = kotorblender_src / "__init__.py"
    if not init_file.is_file():
        return False, f"Invalid kotorblender source: {kotorblender_src} (missing __init__.py)"

    try:
        # Create parent directory if needed
        kotorblender_dest.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing installation if present (idempotent)
        if kotorblender_dest.exists():
            shutil.rmtree(kotorblender_dest)

        # Copy kotorblender to Blender directory
        shutil.copytree(kotorblender_src, kotorblender_dest)

        # Verify installation
        info.has_kotorblender = check_kotorblender_installed(info)
        
        if info.has_kotorblender:
            version_msg = f" (v{info.kotorblender_version})" if info.kotorblender_version else ""
            return True, f"kotorblender{version_msg} installed successfully to:\n{kotorblender_dest}"
        else:
            return False, f"Installation completed but verification failed at:\n{kotorblender_dest}"

    except PermissionError as e:
        return False, f"Permission denied: {e}\n\nTry running as administrator."
    except OSError as e:
        return False, f"Installation failed: {e}"


def uninstall_kotorblender(info: BlenderInfo) -> tuple[bool, str]:
    """Uninstall kotorblender addon from Blender.

    Args:
        info: BlenderInfo with valid Blender installation

    Returns:
        Tuple of (success: bool, message: str)
    """
    if not info.is_valid:
        return False, "Invalid Blender installation"

    kotorblender_path = info.kotorblender_path
    if kotorblender_path is None:
        return False, "Cannot determine kotorblender path"

    if not kotorblender_path.exists():
        return True, "kotorblender is not installed"

    try:
        shutil.rmtree(kotorblender_path)
        info.has_kotorblender = False
        info.kotorblender_version = ""
        return True, f"kotorblender uninstalled from:\n{kotorblender_path}"
    except PermissionError as e:
        return False, f"Permission denied: {e}\n\nTry running as administrator."
    except OSError as e:
        return False, f"Uninstall failed: {e}"


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
    capture_output: bool = False,
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
        if capture_output:
            kwargs["stdout"] = subprocess.PIPE
            kwargs["stderr"] = subprocess.STDOUT
            kwargs["text"] = True
            kwargs["encoding"] = "utf-8"
            kwargs["errors"] = "replace"

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

def _holocron_enable_kotor_addon():
    try:
        import addon_utils
        addon_utils.enable("io_scene_kotor", default_set=True, persistent=True)
        print("[HolocronToolset] io_scene_kotor add-on enabled")
        return True
    except Exception as exc:
        print(f"[HolocronToolset] Failed to enable io_scene_kotor add-on: {{exc}}")
        traceback.print_exc()
        return False

# Try to import and start IPC server
try:
    if _holocron_enable_kotor_addon():
        from io_scene_kotor.ipc import start_ipc_server
        server = start_ipc_server(port={port}, installation_path={escape_path(installation_path)})
        try:
            from io_scene_kotor.ipc.sync import start_scene_monitor
            start_scene_monitor(server)
        except Exception as monitor_exc:
            print(f"[HolocronToolset] Failed to start Blender scene monitor: {{monitor_exc}}")
            traceback.print_exc()
        print(f"[HolocronToolset] IPC server started on port {port}")
    else:
        print("[HolocronToolset] IPC server was not started because the add-on could not be enabled.")
except ImportError as e:
    print(f"[HolocronToolset] Warning: Could not start IPC server: {{e}}")
    print("[HolocronToolset] kotorblender IPC module not found. Make sure kotorblender is properly installed.")
except Exception as e:
    print(f"[HolocronToolset] Error starting IPC server: {{e}}")
    traceback.print_exc()
'''

    return script


# Settings integration
@dataclass
class BlenderSettings:
    """Settings for Blender integration."""

    custom_path: str = ""
    auto_launch: bool = True
    ipc_port: int = 7531
    prefer_blender: bool = False
    remember_choice: bool = False

    def get_blender_info(self) -> BlenderInfo:
        """Get BlenderInfo using current settings."""
        custom = Path(self.custom_path) if self.custom_path else None
        return detect_blender(custom)

    def get_all_installations(self) -> list[BlenderInfo]:
        """Get all Blender installations found on system."""
        return find_all_blender_installations()


# Global settings instance
_blender_settings: BlenderSettings | None = None


def get_blender_settings() -> BlenderSettings:
    """Get global Blender settings instance."""
    global _blender_settings
    if _blender_settings is None:
        _blender_settings = BlenderSettings()
    return _blender_settings
