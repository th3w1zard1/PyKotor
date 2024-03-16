from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2 import QtCore
from PySide2.QtWidgets import QPlainTextEdit

if TYPE_CHECKING:
    from PySide2.QtGui import QKeyEvent, QMouseEvent


class HTPlainTextEdit(QPlainTextEdit):
    keyReleased = QtCore.Signal()
    doubleClicked = QtCore.Signal()

    def keyReleaseEvent(self, e: QKeyEvent):
        super().keyReleaseEvent(e)
        self.keyReleased.emit()

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        super().mouseDoubleClickEvent(e)
        self.doubleClicked.emit()
