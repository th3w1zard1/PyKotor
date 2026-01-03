"""Shared helpers for kit generation inside KotorCLI.

Extraction is delegated to :func:`pykotor.tools.kit.extract_kit`
(see `Libraries/PyKotor/src/pykotor/tools/kit.py`, around the extract_kit
implementation) so behavior stays aligned with the library implementation.
"""
from __future__ import annotations

from pathlib import Path

from loggerplus import RobustLogger
from pykotor.extract.installation import Installation
from pykotor.tools.kit import extract_kit as _extract_kit
from pykotor.tools.path import CaseAwarePath


def normalize_module_name(raw_module: str) -> str:
    """Normalize a module argument to the expected stem."""
    return Path(raw_module).stem.lower()


def generate_kit(
    installation_path: Path,
    module_name: str,
    output_path: Path,
    *,
    kit_id: str | None,
    logger: RobustLogger | None,
) -> None:
    """Run kit extraction with shared validation.

    Args:
    ----
        installation_path: Path to a validated installation root.
        module_name: Module name or filename; stem is used.
        output_path: Destination directory for kit contents.
        kit_id: Optional explicit kit id; defaults to module name when None.
        logger: Logger for progress/errors (may be None when silent).

    Raises:
    ------
        FileNotFoundError: Installation path is missing.
        Exception: Bubble-up from the underlying extraction routine.
    """
    normalized_module = normalize_module_name(module_name)
    case_installation = CaseAwarePath(installation_path)
    if not case_installation.exists():
        msg = f"Installation path does not exist: {case_installation}"
        raise FileNotFoundError(msg)

    installation = Installation(case_installation)

    case_output = CaseAwarePath(output_path)
    case_output.mkdir(parents=True, exist_ok=True)

    _extract_kit(
        installation=installation,
        module_name=normalized_module,
        output_path=case_output,
        kit_id=kit_id,
        logger=logger,
    )

