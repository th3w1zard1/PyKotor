from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Callable

from PyQt5.QtWidgets import QMenu

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource
    from utility.system.path import Path


class ActionType(IntEnum):
    General = auto()
    Copy = auto()
    Insert = auto()
    Remove = auto()
    Delete = auto()
    Selection = auto()


@dataclass
class BaseAction:
    name: str
    method: Callable
    parentMenu: QMenu
    type: ActionType


@dataclass
class SelectionAction(BaseAction): ...


@dataclass
class FileAction(BaseAction):
    filepaths: list[Path] = field(default_factory=list)


@dataclass
class ResourceAction(FileAction):
    resources: list[FileResource] = field(default_factory=list)


# Usage Example
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow

    def sample_method():
        print("Action executed.")

    app = QApplication([])
    main_win = QMainWindow()
    main_menu = QMenu("Main Menu", main_win)

    actions = [
        CopySelectionAction("Copy to Clipboard", sample_method, main_menu),
        FileCopySelectionAction("Copy File Selection", sample_method, main_menu, []),
        ResourceCopySelectionAction("Copy Resource Selection", sample_method, main_menu, []),
    ]

    for action in actions:
        action.register()

    main_win.setMenuWidget(main_menu)
    main_win.show()
    app.exec_()
