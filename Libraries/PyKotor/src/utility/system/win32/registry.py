from __future__ import annotations

import winreg
from typing import cast


def resolve_reg_key_to_path(reg_key: str, keystr: str) -> str | None:
    r"""Resolves a registry key to a file system path.

    Args:
    ----
        reg_key: Registry key to resolve in format "HKEY_CURRENT_USER\\Software\\Company\\Product".
        keystr: Name of value containing path under the key.

    Returns:
    -------
        resolved_path: File system path resolved from registry key/value or None.

    Processing Logic:
    ----------------
        - Opens the registry key using the root and subkey
        - Queries the key for the value specified by keystr
        - Returns the path if found, otherwise returns None.
    """
    try:
        root, subkey = reg_key.split("\\", 1)
        # Access winreg module attribute dynamically using try/except for strict type checking
        try:
            root_key = object.__getattribute__(winreg, root)
        except AttributeError:
            return None
        with winreg.OpenKey(root_key, subkey) as key:
            resolved_path, _ = winreg.QueryValueEx(key, keystr)
            return cast(str, resolved_path)
    except (FileNotFoundError, PermissionError):
        return None
