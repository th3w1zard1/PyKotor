from __future__ import annotations

import os
import re
import sys

from abc import abstractmethod
from enum import IntEnum, IntFlag
from typing import Iterable, TYPE_CHECKING

from qtpy.QtCore import QObject, QUrl, Qt, Signal  # pyright: ignore[reportPrivateImportUsage]
from qtpy.QtGui import QColor, QFont
from qtpy.QtWidgets import QFileDialog, QMessageBox, QStyle

from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qfiledialogoptions import QFileDialogOptions

if TYPE_CHECKING:
    from typing_extensions import Self


class StyleHint(IntEnum):
    DialogIsQtWindow = 0


class DialogCode(IntEnum):
    Rejected = 0
    Accepted = 1


class StandardButton(IntFlag):
    NoButton = 0x00000000
    Ok = 0x00000400
    Save = 0x00000800
    SaveAll = 0x00001000
    Open = 0x00002000
    Yes = 0x00004000
    YesToAll = 0x00008000
    No = 0x00010000
    NoToAll = 0x00020000
    Abort = 0x00040000
    Retry = 0x00080000
    Ignore = 0x00100000
    Close = 0x00200000
    Cancel = 0x00400000
    Discard = 0x00800000
    Help = 0x01000000
    Apply = 0x02000000
    Reset = 0x04000000
    RestoreDefaults = 0x08000000


class ButtonRole(IntFlag):
    InvalidRole = -1
    AcceptRole = 0
    RejectRole = 1
    DestructiveRole = 2
    ActionRole = 3
    HelpRole = 4
    YesRole = 5
    NoRole = 6
    ResetRole = 7
    ApplyRole = 8
    RoleMask = 0x0FFFFFFF
    AlternateRole = 0x10000000
    Stretch = 0x20000000
    Reverse = 0x40000000
    EOL = InvalidRole


class ButtonLayout(IntEnum):
    UnknownLayout = -1
    WinLayout = 0
    MacLayout = 1
    KdeLayout = 2
    GnomeLayout = 3
    AndroidLayout = 4


BUTTON_ROLE_LAYOUTS = (
    (
        (
            ButtonRole.ResetRole,
            ButtonRole.Stretch,
            ButtonRole.YesRole,
            ButtonRole.AcceptRole,
            ButtonRole.AlternateRole,
            ButtonRole.DestructiveRole,
            ButtonRole.NoRole,
            ButtonRole.ActionRole,
            ButtonRole.RejectRole,
            ButtonRole.ApplyRole,
            ButtonRole.HelpRole,
            ButtonRole.EOL,
            ButtonRole.EOL,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.HelpRole,
            ButtonRole.ResetRole,
            ButtonRole.ApplyRole,
            ButtonRole.ActionRole,
            ButtonRole.Stretch,
            ButtonRole.DestructiveRole | ButtonRole.Reverse,
            ButtonRole.AlternateRole | ButtonRole.Reverse,
            ButtonRole.RejectRole | ButtonRole.Reverse,
            ButtonRole.AcceptRole | ButtonRole.Reverse,
            ButtonRole.NoRole | ButtonRole.Reverse,
            ButtonRole.YesRole | ButtonRole.Reverse,
            ButtonRole.EOL,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.HelpRole,
            ButtonRole.ResetRole,
            ButtonRole.Stretch,
            ButtonRole.YesRole,
            ButtonRole.NoRole,
            ButtonRole.ActionRole,
            ButtonRole.AcceptRole,
            ButtonRole.AlternateRole,
            ButtonRole.ApplyRole,
            ButtonRole.DestructiveRole,
            ButtonRole.RejectRole,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.HelpRole,
            ButtonRole.ResetRole,
            ButtonRole.Stretch,
            ButtonRole.ActionRole,
            ButtonRole.ApplyRole | ButtonRole.Reverse,
            ButtonRole.DestructiveRole | ButtonRole.Reverse,
            ButtonRole.AlternateRole | ButtonRole.Reverse,
            ButtonRole.RejectRole | ButtonRole.Reverse,
            ButtonRole.AcceptRole | ButtonRole.Reverse,
            ButtonRole.NoRole | ButtonRole.Reverse,
            ButtonRole.YesRole | ButtonRole.Reverse,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.HelpRole,
            ButtonRole.ResetRole,
            ButtonRole.ApplyRole,
            ButtonRole.ActionRole,
            ButtonRole.Stretch,
            ButtonRole.RejectRole | ButtonRole.Reverse,
            ButtonRole.NoRole | ButtonRole.Reverse,
            ButtonRole.DestructiveRole | ButtonRole.Reverse,
            ButtonRole.AlternateRole | ButtonRole.Reverse,
            ButtonRole.AcceptRole | ButtonRole.Reverse,
            ButtonRole.YesRole | ButtonRole.Reverse,
            ButtonRole.EOL,
            ButtonRole.EOL,
        ),
    ),
    (
        (
            ButtonRole.ActionRole,
            ButtonRole.YesRole,
            ButtonRole.AcceptRole,
            ButtonRole.AlternateRole,
            ButtonRole.DestructiveRole,
            ButtonRole.NoRole,
            ButtonRole.RejectRole,
            ButtonRole.ApplyRole,
            ButtonRole.ResetRole,
            ButtonRole.HelpRole,
            ButtonRole.Stretch,
            ButtonRole.EOL,
            ButtonRole.EOL,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.YesRole,
            ButtonRole.NoRole,
            ButtonRole.AcceptRole,
            ButtonRole.RejectRole,
            ButtonRole.AlternateRole,
            ButtonRole.DestructiveRole,
            ButtonRole.Stretch,
            ButtonRole.ActionRole,
            ButtonRole.ApplyRole,
            ButtonRole.ResetRole,
            ButtonRole.HelpRole,
            ButtonRole.EOL,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.AcceptRole,
            ButtonRole.AlternateRole,
            ButtonRole.ApplyRole,
            ButtonRole.ActionRole,
            ButtonRole.YesRole,
            ButtonRole.NoRole,
            ButtonRole.Stretch,
            ButtonRole.ResetRole,
            ButtonRole.DestructiveRole,
            ButtonRole.RejectRole,
            ButtonRole.HelpRole,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.YesRole,
            ButtonRole.NoRole,
            ButtonRole.AcceptRole,
            ButtonRole.RejectRole,
            ButtonRole.AlternateRole,
            ButtonRole.DestructiveRole,
            ButtonRole.ApplyRole,
            ButtonRole.ActionRole,
            ButtonRole.Stretch,
            ButtonRole.ResetRole,
            ButtonRole.HelpRole,
            ButtonRole.EOL,
            ButtonRole.EOL,
            ButtonRole.EOL,
        ),
        (
            ButtonRole.YesRole,
            ButtonRole.AcceptRole,
            ButtonRole.AlternateRole,
            ButtonRole.DestructiveRole,
            ButtonRole.NoRole,
            ButtonRole.RejectRole,
            ButtonRole.Stretch,
            ButtonRole.ActionRole,
            ButtonRole.ApplyRole,
            ButtonRole.ResetRole,
            ButtonRole.HelpRole,
            ButtonRole.EOL,
            ButtonRole.EOL,
        ),
    ),
)


class QPlatformDialogHelper(QObject):
    accept: Signal = Signal()
    reject: Signal = Signal()

    StyleHint = StyleHint
    DialogCode = DialogCode
    StandardButton = StandardButton
    ButtonRole = ButtonRole
    ButtonLayout = ButtonLayout

    def __new__(cls, *args, **kwargs) -> Self:  # type: ignore[name-defined]
        new_cls = cls
        if cls is QPlatformDialogHelper:
            if sys.platform in ("win32", "cygwin"):
                from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qwindowsdialoghelpers import QWindowsDialogHelper

                new_cls = QWindowsDialogHelper
            elif sys.platform == "linux":
                from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qlinuxdialoghelpers import LinuxFileDialogHelper

                new_cls = LinuxFileDialogHelper
            elif sys.platform == "darwin":
                from utility.ui_libraries.qt.adapters.kernel.qplatformdialoghelper.qmacdialoghelpers import QMacDialogHelper

                new_cls = QMacDialogHelper
            else:
                raise NotImplementedError(f"No dialog helper implemented for {sys.platform}")
        return super().__new__(new_cls)

    def exec(self) -> DialogCode:
        raise NotImplementedError()

    def show(self, window_flags: Qt.WindowFlags, window_state: Qt.WindowState, parent: QObject | None):
        raise NotImplementedError()

    def hide(self):
        raise NotImplementedError()

    def selectMimeTypeFilter(self, filter: str) -> None:
        self._selected_mime_type_filter = filter

    def selectedMimeTypeFilter(self) -> str:
        return getattr(self, "_selected_mime_type_filter", "")

    def isSupportedUrl(self, url: QUrl) -> bool:
        return url.isLocalFile()

    def defaultStyleHint(self) -> StyleHint:
        return StyleHint.DialogIsQtWindow

    def styleHint(self) -> StyleHint:
        return self.defaultStyleHint()

    @staticmethod
    def buttonRole(button: StandardButton) -> ButtonRole:
        if button in (
            StandardButton.Ok,
            StandardButton.Save,
            StandardButton.Open,
            StandardButton.SaveAll,
            StandardButton.Retry,
            StandardButton.Ignore,
        ):
            return ButtonRole.AcceptRole
        if button in (StandardButton.Cancel, StandardButton.Close, StandardButton.Abort):
            return ButtonRole.RejectRole
        if button is StandardButton.Discard:
            return ButtonRole.DestructiveRole
        if button is StandardButton.Help:
            return ButtonRole.HelpRole
        if button is StandardButton.Apply:
            return ButtonRole.ApplyRole
        if button in (StandardButton.Yes, StandardButton.YesToAll):
            return ButtonRole.YesRole
        if button in (StandardButton.No, StandardButton.NoToAll):
            return ButtonRole.NoRole
        if button in (StandardButton.RestoreDefaults, StandardButton.Reset):
            return ButtonRole.ResetRole
        return ButtonRole.InvalidRole

    @staticmethod
    def buttonLayout(orientation: Qt.Orientation = Qt.Orientation.Horizontal, policy: ButtonLayout = ButtonLayout.UnknownLayout) -> tuple[ButtonRole, ...]:
        layout_policy = policy
        if layout_policy == ButtonLayout.UnknownLayout:
            if sys.platform == "darwin":
                layout_policy = ButtonLayout.MacLayout
            elif sys.platform.startswith("linux") or os.name == "posix":
                layout_policy = ButtonLayout.KdeLayout
            elif sys.platform.startswith("android"):
                layout_policy = ButtonLayout.AndroidLayout
            else:
                layout_policy = ButtonLayout.WinLayout
        orientation_index = 1 if orientation == Qt.Orientation.Vertical else 0
        return BUTTON_ROLE_LAYOUTS[orientation_index][layout_policy]


class QPlatformColorDialogHelper(QPlatformDialogHelper):
    currentColorChanged: Signal = Signal(QColor)

    @abstractmethod
    def setCurrentColor(self, color: QColor):
        ...

    @abstractmethod
    def currentColor(self) -> QColor:
        ...


class QPlatformFileDialogHelper(QPlatformDialogHelper):
    filterRegExp = r"^(.+)\s*\((.*)\)$"

    FileMode = QFileDialog.FileMode
    AcceptMode = QFileDialog.AcceptMode
    Option = QFileDialog.Option

    fileSelected = Signal(QUrl)
    filesSelected = Signal(list)
    currentChanged = Signal(QUrl)
    directoryEntered = Signal(QUrl)
    filterSelected = Signal(str)

    def __init__(self, options: QFileDialogOptions | None = None):
        super().__init__()
        self._options: QFileDialogOptions = options or QFileDialogOptions()
        self._directory: str = ""
        self._selected_files: list[str] = []
        self._selected_name_filter: str = ""

    @staticmethod
    def cleanFilterList(filter: str) -> list[str]:
        if not filter:
            return []

        match = re.match(QPlatformFileDialogHelper.filterRegExp, filter.strip())
        if not match:
            return [filter.strip()]

        pattern_section = match.group(2).strip()
        if not pattern_section:
            return []

        return [pattern for pattern in pattern_section.split() if pattern]

    def options(self) -> QFileDialogOptions:
        return self._options

    def setOptions(self, options: QFileDialogOptions) -> None:
        self._options = options

    def isSupportedUrl(self, url: QUrl) -> bool:
        scheme = url.scheme()
        return scheme in self._options.supportedSchemes() and (url.isLocalFile() or url.isValid())

    def setDirectory(self, directory: str) -> None:
        self._directory = directory
        self._options.setInitialDirectory(QUrl.fromLocalFile(directory))

    def directory(self) -> str:
        return self._directory

    def selectFile(self, filename: QUrl) -> None:
        if filename.isLocalFile():
            self._selected_files = [filename.toLocalFile()]
        else:
            self._selected_files = [filename.toString()]

    def selectedFiles(self) -> list[str]:
        return list(self._selected_files)

    def setFilter(self) -> None:
        pass

    def selectNameFilter(self, filter: str) -> None:  # noqa: A002
        self._selected_name_filter = filter
        self._options.selectNameFilter(filter)

    def selectedNameFilter(self) -> str:
        if self._options.selectedNameFilter():
            return self._options.selectedNameFilter()
        return self._selected_name_filter

    def selectedMimeTypeFilter(self) -> str:
        return self._options.selectedMimeTypeFilter()

    def selectMimeTypeFilter(self, filter: str) -> None:  # noqa: A002
        self._options.selectMimeTypeFilter(filter)

    def defaultNameFilterString(self) -> str:
        return self._options.defaultNameFilterString()


class QPlatformFontDialogHelper(QPlatformDialogHelper):
    currentFontChanged = Signal(QFont)

    @abstractmethod
    def setCurrentFont(self, font: QFont):
        ...

    @abstractmethod
    def currentFont(self) -> QFont:
        ...


class QPlatformMessageDialogHelper(QPlatformDialogHelper):
    """Abstract base class for platform-specific message dialog helpers.
    This class defines the interface for creating and managing message dialogs across different platforms.
    """

    StandardButton: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok
    StandardButtons = QMessageBox.StandardButton(0)

    class ButtonRole(Flag):
        """Enum defining the roles of buttons in a message dialog.
        These roles determine the semantic meaning and behavior of buttons.
        """
        InvalidRole = -1  # Invalid button role
        AcceptRole = 0    # Accepting or "OK" role
        RejectRole = 1    # Rejecting or "Cancel" role
        DestructiveRole = 2  # Destructive or dangerous action role
        ActionRole = 3    # Action button role
        HelpRole = 4      # Help button role
        YesRole = 5       # "Yes" button role
        NoRole = 6        # "No" button role
        ResetRole = 7     # Reset to default values role
        ApplyRole = 8     # Apply changes role

    class Icon(Flag):
        """Enum defining the standard icons that can be displayed in a message dialog."""
        NoIcon = 0        # No icon
        Information = 1   # Information icon
        Warning = 2       # Warning icon
        Critical = 3      # Critical or error icon
        Question = 4      # Question icon

    clickedButton = Signal(int)  # Signal emitted when a button is clicked, passing the button's ID

    @abstractmethod
    def setButtons(self, buttons: QMessageBox.StandardButton):
        """Set the standard buttons to be displayed in the dialog.

        :param buttons: A combination of StandardButtons flags
        """
        ...

    @abstractmethod
    def buttons(self) -> QMessageBox.StandardButton:
        """Get the current standard buttons set for the dialog.

        :return: The current StandardButtons flags
        """
        ...

    @abstractmethod
    def setButtonText(self, button: QMessageBox.StandardButton, text: str):
        """Set custom text for a standard button.

        :param button: The StandardButton to modify
        :param text: The new text for the button
        """
        ...

    @abstractmethod
    def buttonText(self, button: QMessageBox.StandardButton) -> str:
        """Get the current text of a standard button.

        :param button: The StandardButton to query
        :return: The current text of the button
        """
        ...

    @abstractmethod
    def setIcon(self, icon: Icon):
        """Set the icon to be displayed in the dialog.

        :param icon: The Icon enum value to set
        """
        ...

    @abstractmethod
    def icon(self) -> Icon:
        """Get the current icon set for the dialog.

        :return: The current Icon enum value
        """
        ...

    @abstractmethod
    def setText(self, text: str):
        """Set the main text of the message dialog.

        :param text: The main message text
        """
        ...

    @abstractmethod
    def text(self) -> str:
        """Get the current main text of the message dialog.

        :return: The current main message text
        """
        ...

    @abstractmethod
    def setInformativeText(self, text: str):
        """Set additional informative text for the dialog.

        :param text: The informative text to set
        """
        ...

    @abstractmethod
    def informativeText(self) -> str:
        """Get the current informative text of the dialog.

        :return: The current informative text
        """
        ...

    @abstractmethod
    def setDetailedText(self, text: str):
        """Set detailed text for the dialog, typically shown in an expandable section.

        :param text: The detailed text to set
        """
        ...

    @abstractmethod
    def detailedText(self) -> str:
        """Get the current detailed text of the dialog.

        :return: The current detailed text
        """
        ...
