from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression
from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]

class AUnaryExp(ScriptNode, AExpression):
    def __init__(self, exp: AExpression, op: str):
        super().__init__()
        self.set_exp(exp)
        self.op: str = op
        self._stackentry: StackEntry | None = None

    def set_exp(self, exp: AExpression):
        self._exp = exp
        exp.parent(self)  # type: ignore

    def exp(self) -> AExpression:
        return self._exp

    def __str__(self) -> str:
        return "(" + self.op + str(self._exp) + ")"

    def stackentry(self) -> StackEntry:
        return self._stackentry

    def set_stackentry(self, stackentry: StackEntry):
        self._stackentry = stackentry

    def close(self):
        super().close()
        if self._exp is not None:
            self._exp.close()  # type: ignore
        self._exp = None
        if self._stackentry is not None:
            self._stackentry.close()
        self._stackentry = None

