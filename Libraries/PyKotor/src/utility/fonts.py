"""Font path utilities for cross-platform font discovery.

This module provides functions for finding TTF font files on different operating systems.
These are general utility functions, not specific to KOTOR.
"""
from __future__ import annotations

import platform
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def get_font_paths_linux() -> list[Path]:
    """Get list of TTF font paths on Linux.

    Returns:
    -------
        List of Path objects to TTF font files
    """
    font_dirs: list[Path] = [Path("/usr/share/fonts/"), Path("/usr/local/share/fonts/"), Path.home() / ".fonts"]
    return [font for font_dir in font_dirs for font in font_dir.glob("**/*.ttf")]


def get_font_paths_macos() -> list[Path]:
    """Get list of TTF font paths on macOS.

    Returns:
    -------
        List of Path objects to TTF font files
    """
    font_dirs: list[Path] = [Path("/Library/Fonts/"), Path("/System/Library/Fonts/"), Path.home() / "Library/Fonts"]
    return [font for font_dir in font_dirs for font in font_dir.glob("**/*.ttf")]


def get_font_paths_windows() -> list[Path]:
    """Get list of TTF font paths on Windows.

    Returns:
    -------
        List of Path objects to TTF font files
    """
    import winreg

    font_registry_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
    fonts_dir = Path("C:/Windows/Fonts")
    font_paths: set[Path] = set()

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, font_registry_path) as key:
            for i in range(winreg.QueryInfoKey(key)[1]):  # Number of values in the key
                value: tuple[str, Any, int] = winreg.EnumValue(key, i)
                font_path: Path = fonts_dir / value[1]
                if font_path.suffix.lower() == ".ttf":  # Filtering for .ttf files
                    font_paths.add(font_path)
    except Exception:  # pylint: disable=W0718  # noqa: BLE001
        pass

    for file in fonts_dir.rglob("*"):
        if file.suffix.lower() == ".ttf" and file.is_file():
            font_paths.add(file)

    return list(font_paths)


def get_font_paths() -> list[Path]:
    """Get list of TTF font paths for the current operating system.

    Returns:
    -------
        List of Path objects to TTF font files

    Raises:
    ------
        NotImplementedError: If operating system is not supported
    """
    with suppress(Exception):
        os_str = platform.system()
        if os_str == "Linux":
            return get_font_paths_linux()
        if os_str == "Darwin":
            return get_font_paths_macos()
        if os_str == "Windows":
            return get_font_paths_windows()
    msg = "Unsupported operating system"
    raise NotImplementedError(msg)

