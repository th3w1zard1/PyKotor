from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression
from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]

class AUnaryModExp(ScriptNode, AExpression):
    def __init__(self, varref: AVarRef, op: str, prefix: bool):
        super().__init__()
        self.set_var_ref(varref)
        self.op: str = op
        self.prefix: bool = prefix
        self._stackentry: StackEntry | None = None

    def set_var_ref(self, varref: AVarRef):
        self.varref = varref
        varref.parent(self)  # type: ignore

    def var_ref(self) -> AVarRef:
        return self.varref

    def __str__(self) -> str:
        if self.prefix:
            return "(" + self.op + str(self.varref) + ")"
        return "(" + str(self.varref) + self.op + ")"

    def stackentry(self) -> StackEntry:
        return self._stackentry

    def set_stackentry(self, stackentry: StackEntry):
        self._stackentry = stackentry

    def close(self):
        super().close()
        if self.varref is not None:
            self.varref.close()
        self.varref = None
        if self._stackentry is not None:
            self._stackentry.close()
        self._stackentry = None

