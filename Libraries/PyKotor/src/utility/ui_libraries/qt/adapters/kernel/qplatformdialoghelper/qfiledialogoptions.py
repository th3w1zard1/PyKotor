from __future__ import annotations

from typing import Iterable

from qtpy.QtCore import QDir, QUrl
from qtpy.QtWidgets import QFileDialog


class QFileDialogOptions:
    def __init__(self):
        self._mime_type_filters: list[str] = []
        self._name_filters: list[str] = []
        self._selected_name_filter: str = ""
        self._selected_mime_type_filter: str = ""
        self._file_mode: QFileDialog.FileMode = QFileDialog.FileMode.AnyFile
        self._accept_mode: QFileDialog.AcceptMode = QFileDialog.AcceptMode.AcceptOpen
        self._view_mode: QFileDialog.ViewMode = QFileDialog.ViewMode.Detail
        self._sidebar_urls: list[QUrl] = []
        self._supported_schemes: list[str] = ["file"]
        self._default_suffix: str = ""
        self._filter: int | QDir.Filters = 0  # pyright: ignore[reportAttributeAccessIssue]  # type: ignore[attr-defined]
        self._history: list[str] = []
        self._label_texts: dict[QFileDialog.DialogLabel, str] = {}
        self._explicit_labels: list[QFileDialog.DialogLabel] = []
        self._initial_directory: QUrl | None = None
        self._initially_selected_files: list[QUrl] = []
        self._initially_selected_name_filter: str = ""
        self._initially_selected_mime_type_filter: str = ""
        self._use_default_name_filters: bool = True

    def setMimeTypeFilters(self, filters: Iterable[str]) -> None:
        self._mime_type_filters = list(filters)

    def mimeTypeFilters(self) -> list[str]:
        return list(self._mime_type_filters)

    def setNameFilters(self, filters: Iterable[str]) -> None:
        self._name_filters = list(filters)

    def nameFilters(self) -> list[str]:
        return list(self._name_filters)

    def selectNameFilter(self, filter: str) -> None:  # noqa: A002
        if filter in self._name_filters:
            self._selected_name_filter = filter

    def selectedNameFilter(self) -> str:
        return self._selected_name_filter

    def selectMimeTypeFilter(self, filter: str) -> None:  # noqa: A002
        if filter in self._mime_type_filters:
            self._selected_mime_type_filter = filter

    def selectedMimeTypeFilter(self) -> str:
        return self._selected_mime_type_filter

    def setFileMode(self, mode: QFileDialog.FileMode) -> None:
        self._file_mode = mode

    def fileMode(self) -> QFileDialog.FileMode:
        return self._file_mode

    def setAcceptMode(self, mode: QFileDialog.AcceptMode) -> None:
        self._accept_mode = mode

    def acceptMode(self) -> QFileDialog.AcceptMode:
        return self._accept_mode

    def setViewMode(self, mode: QFileDialog.ViewMode) -> None:
        self._view_mode = mode

    def viewMode(self) -> QFileDialog.ViewMode:
        return self._view_mode

    def setSidebarUrls(self, urls: Iterable[QUrl]) -> None:
        self._sidebar_urls = list(urls)

    def sidebarUrls(self) -> list[QUrl]:
        return list(self._sidebar_urls)

    def setSupportedSchemes(self, schemes: Iterable[str]) -> None:
        self._supported_schemes = list(schemes)

    def supportedSchemes(self) -> list[str]:
        return list(self._supported_schemes)

    def setDefaultSuffix(self, suffix: str) -> None:
        self._default_suffix = suffix

    def defaultSuffix(self) -> str:
        return self._default_suffix

    def setFilter(self, filter: int | QDir.Filters) -> None:  # noqa: A002  # pyright: ignore[reportAttributeAccessIssue]  # type: ignore[attr-defined]
        self._filter = filter

    def filter(self) -> int:
        return self._filter

    def setHistory(self, paths: Iterable[str]) -> None:
        self._history = list(paths)

    def history(self) -> list[str]:
        return list(self._history)

    def setLabelText(self, label: QFileDialog.DialogLabel, text: str) -> None:
        self._label_texts[label] = text
        if label not in self._explicit_labels:
            self._explicit_labels.append(label)

    def labelText(self, label: QFileDialog.DialogLabel) -> str:
        return self._label_texts.get(label, "")

    def isLabelExplicitlySet(self, label: QFileDialog.DialogLabel) -> bool:
        return label in self._explicit_labels

    def setInitialDirectory(self, directory: QUrl) -> None:
        self._initial_directory = directory

    def initialDirectory(self) -> QUrl | None:
        return self._initial_directory

    def setInitiallySelectedFiles(self, files: Iterable[QUrl]) -> None:
        self._initially_selected_files = list(files)

    def initiallySelectedFiles(self) -> list[QUrl]:
        return list(self._initially_selected_files)

    def setInitiallySelectedNameFilter(self, filter: str) -> None:
        self._initially_selected_name_filter = filter

    def initiallySelectedNameFilter(self) -> str:
        return self._initially_selected_name_filter

    def setInitiallySelectedMimeTypeFilter(self, filter: str) -> None:
        self._initially_selected_mime_type_filter = filter

    def initiallySelectedMimeTypeFilter(self) -> str:
        return self._initially_selected_mime_type_filter

    def setUseDefaultNameFilters(self, value: bool) -> None:
        self._use_default_name_filters = value

    def useDefaultNameFilters(self) -> bool:
        return self._use_default_name_filters

    @staticmethod
    def defaultNameFilterString() -> str:
        return "All Files (*.*)"
