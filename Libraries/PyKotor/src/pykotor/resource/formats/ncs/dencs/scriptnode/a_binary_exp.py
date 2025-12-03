from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression
from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]

class ABinaryExp(ScriptNode, AExpression):
    def __init__(self, left: AExpression, right: AExpression, op: str):
        super().__init__()
        self.set_left(left)
        self.set_right(right)
        self.op: str = op
        self._stackentry: StackEntry | None = None

    def set_left(self, left: AExpression):
        self._left = left
        left.parent(self)  # type: ignore

    def left(self) -> AExpression:
        return self._left

    def set_right(self, right: AExpression):
        self._right = right
        right.parent(self)  # type: ignore

    def right(self) -> AExpression:
        return self._right

    def __str__(self) -> str:
        return "(" + str(self._left) + " " + self.op + " " + str(self._right) + ")"

    def stackentry(self) -> StackEntry:
        return self._stackentry

    def set_stackentry(self, stackentry: StackEntry):
        self._stackentry = stackentry

    def close(self):
        super().close()
        if self._left is not None:
            self._left.close()  # type: ignore
            self._left = None
        if self._right is not None:
            self._right.close()  # type: ignore
            self._right = None
        if self._stackentry is not None:
            self._stackentry.close()
        self._stackentry = None

