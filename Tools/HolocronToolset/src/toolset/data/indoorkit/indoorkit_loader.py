from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtGui import QImage

from pykotor.common.indoorkit import Kit
from pykotor.tools import indoorkit as indoorkit_tools
from pykotor.common.indoorkit.qt_preview import ensure_component_image

if TYPE_CHECKING:
    import os


def load_kits(path: "os.PathLike | str") -> tuple[list[Kit], list[tuple[str, Path, str]]]:
    """Toolset compatibility wrapper for loading kits.

    Core parsing + missing-file reporting is implemented in `pykotor.tools.indoorkit`.
    Toolset-specific behavior here:
    - Optionally load component `.png` previews when present (Qt-only).
    - Otherwise previews can be generated from BWM via `ensure_component_image()`.
    """
    kits, missing_files = indoorkit_tools.load_kits_with_missing_files(path)

    base = Path(path).absolute()
    for kit in kits:
        kit_dir = base / kit.id
        for comp in kit.components:
            png_path = kit_dir / f"{comp.id}.png"
            if png_path.is_file():
                try:
                    comp.image = QImage(str(png_path)).mirrored()
                except Exception:
                    # Keep missing list stable-ish, but treat previews as optional.
                    missing_files.append((kit.name, png_path, "component image (read error)"))
            # Ensure some preview exists for UI, even if PNG is missing.
            try:
                ensure_component_image(comp)
            except Exception:
                # Preview generation failure should not prevent kit usage.
                pass

    return kits, missing_files
