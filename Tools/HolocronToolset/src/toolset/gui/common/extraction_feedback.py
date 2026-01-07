"""Shared utilities for extraction feedback dialogs."""

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox, QWidget

from loggerplus import RobustLogger

if TYPE_CHECKING:
    pass


def show_extraction_results(
    parent: QWidget | None,
    successful_paths: dict[object, Path],
    failed_extractions: dict[Path, Exception] | None = None,
    folder_path: Path | None = None,
) -> None:
    """Show a dialog with extraction results.

    Args:
    ----
        parent: Parent widget for the dialog
        successful_paths: Dictionary mapping resources to successfully saved paths
        failed_extractions: Dictionary mapping paths to exceptions for failed extractions
        folder_path: The folder path where files were extracted (for display)
    """
    if failed_extractions is None:
        failed_extractions = {}

    num_errors = len(failed_extractions)
    num_successes = len(successful_paths)

    # Don't show dialog if nothing happened
    if num_errors == 0 and num_successes == 0:
        RobustLogger().debug("No extraction results to show")
        return

    from toolset.gui.common.localization import translate as tr, trf

    # Determine dialog content based on results
    if num_errors and num_successes > 0:
        title = tr("Extraction completed with some errors.")
        summary = trf(
            "Saved {success_count} files to {path}.\nFailed to save {error_count} files.",
            success_count=num_successes,
            error_count=num_errors,
            path=folder_path or "selected location",
        )
    elif num_errors:
        title = tr("Failed to extract all items.")
        summary = trf("Failed to save all {count} files!", count=num_errors)
    else:
        title = tr("Extraction successful.")
        summary = trf(
            "Successfully saved {count} files to {path}",
            count=num_successes,
            path=folder_path or "selected location",
        )

    msg_box = QMessageBox(
        QMessageBox.Icon.Information,
        title,
        summary,
        flags=(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        ),
    )

    # Add detailed information
    details_lines: list[str] = []
    if num_successes > 0:
        details_lines.append(tr("Saved files:"))
        for path in successful_paths.values():
            details_lines.append(f"   {path}")
    if num_errors:
        if details_lines:
            details_lines.append("")  # blank line
        details_lines.append(tr("Errors:"))
        for file_path, exc in failed_extractions.items():
            details_lines.append(f"   {file_path}: {exc.__class__.__name__}: {exc}")

    if details_lines:
        msg_box.setDetailedText("\n".join(details_lines))

    msg_box.exec()