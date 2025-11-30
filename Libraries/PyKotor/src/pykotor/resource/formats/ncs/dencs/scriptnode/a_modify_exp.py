from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression
from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]

class AModifyExp(ScriptNode, AExpression):
    def __init__(self, varref: AVarRef, exp: AExpression):
        super().__init__()
        self.set_var_ref(varref)
        self.set_expression(exp)

    def set_var_ref(self, varref: AVarRef):
        self.varref = varref
        varref.parent(self)  # type: ignore

    def set_expression(self, exp: AExpression):
        self._exp = exp
        exp.parent(self)  # type: ignore

    def expression(self) -> AExpression:
        return self._exp

    def var_ref(self) -> AVarRef:
        return self.varref

    def __str__(self) -> str:
        return str(self.varref) + " = " + str(self._exp)

    def stackentry(self) -> StackEntry:
        return self.varref.var()

    def set_stackentry(self, stackentry: StackEntry):
        pass

    def close(self):
        super().close()
        if self._exp is not None:
            self._exp.close()  # type: ignore
        self._exp = None
        if self.varref is not None:
            self.varref.close()
        self.varref = None

