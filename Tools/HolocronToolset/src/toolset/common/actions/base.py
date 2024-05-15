from __future__ import annotations

import dataclasses

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Set, TypeVar, cast

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QMenu, QMessageBox

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.extract.file import FileResource
    from utility.system.path import Path


class MenuActionType(IntEnum):
    GENERAL = 0
    COPY = 1
    INSERT = 2
    REMOVE = 3
    DELETE = 4
    SELECT = 5


class SelectionType(IntEnum):
    ALL = 0
    UNDER_MOUSE = 1
    HIGHLIGHTED = 2
    CHECKED = 3


class ItemType(IntEnum):
    FILE = 0
    RESOURCE = 1
    OTHER = 2


# Define a generic type for the class to ensure it can accept any callable correctly
F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class MenuActionWrapper(Generic[F]):
    func: F
    menu_info: MenuActionInfo

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the stored function with the passed arguments."""
        return self.func(*args, **kwargs)


@dataclass
class ActionContext:
    """Information about this action, used for setting up signals based on what action executed."""
    info: MenuActionInfo  # Name of the action, what items will be chosen
    method: Callable[..., Any]  # The method that'll be called, can be overridden in the prehook signal
    widget: QWidget  # The widget we're creating the menu for.
    type: MenuActionType  # e.g. insert, select, basic context of what the action attempts. useful for if things like QTableWidget need to know if its removing a cell/row.

    parentMenu: QMenu | None = None  # If the action is in a submenu, otherwise None.
    item_type: ItemType = ItemType.OTHER  # was a file, resource, or various other item chosen for an action.
    filepaths: list[Path] = field(default_factory=list)
    resources: list[FileResource] = field(default_factory=list)


@dataclass
class MenuActionInfo:
    """For use with the decorator to eventually define BaseAction."""
    name: str
    menu_type: MenuActionType
    selection_type: SelectionType = SelectionType.HIGHLIGHTED
    confirm: bool = False
    enabled: bool = True
    visible: bool = True


class CommonActions:
    pre_call_signal = Signal(str, object)   # action menu name, ActionContext instance
    post_call_signal = Signal(str, object)  # action menu name, ActionContext instance
    _action_registry: ClassVar[dict[str, MenuActionWrapper]] = {}

    def __init__(self):
        self._actions: dict[str, MenuActionWrapper] = {}
        for name, action in self._action_registry.items():
            self._actions[name] = action

    @classmethod
    def action(
        cls,
        menu_info: MenuActionInfo,
    ) -> Callable[[F], MenuActionWrapper[F]]:
        def decorator(func: F) -> MenuActionWrapper[F]:
            action = MenuActionWrapper(func, menu_info)
            cls._action_registry[func.__name__] = action
            return action

        return decorator

    def setActionRequiresConfirmation(
        self,
        action_name: str,
        *,
        state: bool,
    ):
        """Should we prompt the user for this action?"""
        action = self._actions[action_name]
        action.menu_info = dataclasses.replace(action.menu_info, confirm=state)

    def setActionState(
        self,
        action_name: str,
        *,
        state: bool,
    ):
        """Enable or disable a specific action."""
        action = self._actions[action_name]
        action.menu_info = dataclasses.replace(action.menu_info, enabled=state)

    def setActionVisibility(
        self,
        action_name: str,
        *,
        state: bool,
    ):
        """Set the visibility of a specific action."""
        action = self._actions[action_name]
        action.menu_info = dataclasses.replace(action.menu_info, visible=state)

    def buildActionMenu(
        self,
        menu: QMenu | None = None,
    ) -> QMenu:
        if menu is None:
            menu = QMenu()
        else:
            menu.addSeparator()

        for action_name, action in self._actions.items():
            qAction = menu.addAction(action_name)
            qAction.setEnabled(action.menu_info.enabled)
            qAction.setVisible(action.menu_info.visible)
            qAction.triggered.connect(action)

        return menu

    def show_confirmation_dialog(
        self,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
        buttons: QMessageBox.StandardButton | QMessageBox.StandardButtons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.No,
        detailedMsg: str | None = None,
    ) -> int | QMessageBox.StandardButton:
        if not detailedMsg or not detailedMsg.strip():
            selected = cast(Set[FileTableWidgetItem], {*self.selectedItems()})
            detailedMsg = ""
            for selection in selected:
                file_path = selection.filepath
                detailedMsg += f"{file_path}\n" if detailedMsg else file_path

        reply = QMessageBox(
            QMessageBox.Icon.Question,
            title + (" " * 1000),
            text + (" " * 1000),
            buttons,
            flags=Qt.WindowType.Dialog | Qt.WindowType.WindowDoesNotAcceptFocus | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
        )
        reply.setDefaultButton(default_button)
        if detailedMsg and detailedMsg.strip():
            reply.setDetailedText(detailedMsg.strip())
        return reply.exec_()
