from __future__ import annotations

from pathlib import PurePath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os


def normalize_ext(
    str_repr: os.PathLike | str,
) -> os.PathLike | str:
    if isinstance(str_repr, str):
        if not str_repr:
            return ""
        if str_repr[0] == ".":
            return f"stem{str_repr}"
        if "." not in str_repr:
            return f"stem.{str_repr}"
    return str_repr


def normalize_stem(
    str_repr: os.PathLike | str,
) -> os.PathLike | str:
    if isinstance(str_repr, str):
        if not str_repr:
            return ""
        if str_repr[-1:] == ".":
            return f"{str_repr}ext"
        if "." not in str_repr:
            return f"{str_repr}.ext"
    return str_repr


def is_nss_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has a NSS file extension."""
    return PurePath(normalize_ext(filepath)).suffix.lower() == ".nss"


def is_mod_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has a MOD file extension."""
    return PurePath(normalize_ext(filepath)).suffix.lower() == ".mod"


def is_erf_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has a ERF file extension."""
    return PurePath(normalize_ext(filepath)).suffix.lower() == ".erf"


def is_sav_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has a SAV file extension."""
    return PurePath(normalize_ext(filepath)).suffix.lower() == ".sav"


def is_any_erf_type_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has either an ERF, MOD, or SAV file extension."""
    return PurePath(normalize_ext(filepath)).suffix.lower() in (".erf", ".mod", ".sav")


def is_rim_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has a RIM file extension."""
    return PurePath(normalize_ext(filepath)).suffix.lower() == ".rim"


def is_bif_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has a BIF file extension."""
    # Fast path: use string operations instead of PurePath for better performance
    if isinstance(filepath, str):
        lower_path = filepath.lower()
        return lower_path.endswith(".bif")
    # For Path objects, use the suffix property directly (already optimized)
    return str(filepath).lower().endswith(".bif")


def is_bzf_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has a BZF file extension (lzma-compressed bif archive usually used on iOS)."""
    # Fast path: use string operations instead of PurePath for better performance
    if isinstance(filepath, str):
        return filepath.lower().endswith(".bzf")
    return str(filepath).lower().endswith(".bzf")


def is_capsule_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has either an ERF, MOD, SAV, or RIM file extension."""
    # Fast path: use string operations instead of PurePath for better performance
    # Check common extensions directly without creating path objects
    if isinstance(filepath, str):
        lower_path = filepath.lower()
        return lower_path.endswith((".erf", ".mod", ".rim", ".sav"))
    # For Path objects, use string conversion (faster than PurePath)
    lower_path = str(filepath).lower()
    return lower_path.endswith((".erf", ".mod", ".rim", ".sav"))


def is_storage_file(
    filepath: os.PathLike | str,
) -> bool:
    """Returns true if the given filename has either an ERF, MOD, SAV, RIM, or BIF file extension."""
    return PurePath(normalize_ext(filepath)).suffix.lower() in {".erf", ".mod", ".sav", ".rim", ".bif"}
