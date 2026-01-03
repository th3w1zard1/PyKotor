from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression
from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]

class AVectorConstExp(ScriptNode, AExpression):
    def __init__(self, exp1: AExpression, exp2: AExpression, exp3: AExpression):
        super().__init__()
        self.set_exp1(exp1)
        self.set_exp2(exp2)
        self.set_exp3(exp3)

    def set_exp1(self, exp1: AExpression):
        self._exp1 = exp1
        exp1.parent(self)  # type: ignore

    def set_exp2(self, exp2: AExpression):
        self._exp2 = exp2
        exp2.parent(self)  # type: ignore

    def set_exp3(self, exp3: AExpression):
        self._exp3 = exp3
        exp3.parent(self)  # type: ignore

    def exp1(self) -> AExpression:
        return self._exp1

    def exp2(self) -> AExpression:
        return self._exp2

    def exp3(self) -> AExpression:
        return self._exp3

    def __str__(self) -> str:
        return "[" + str(self._exp1) + "," + str(self._exp2) + "," + str(self._exp3) + "]"

    def stackentry(self) -> StackEntry | None:
        return None

    def set_stackentry(self, stackentry: StackEntry):
        pass

    def close(self):
        super().close()
        if self._exp1 is not None:
            self._exp1.close()  # type: ignore
        self._exp1 = None
        if self._exp2 is not None:
            self._exp2.close()  # type: ignore
        self._exp2 = None
        if self._exp3 is not None:
            self._exp3.close()  # type: ignore
        self._exp3 = None

