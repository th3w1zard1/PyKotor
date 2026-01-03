from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]

class AVarDecl(ScriptNode):
    def __init__(self, var: Variable):
        super().__init__()
        self.set_var_var(var)
        self._exp: AExpression | None = None
        self._is_fcn_return: bool = False

    def set_var_var(self, var: Variable):
        self._var = var

    def var_var(self) -> Variable:
        return self._var

    def set_is_fcn_return(self, is_val: bool):
        self._is_fcn_return = is_val

    def is_fcn_return(self) -> bool:
        return self._is_fcn_return

    def type(self) -> Type:
        return self._var.type()

    def initialize_exp(self, exp: AExpression):
        exp.parent(self)  # type: ignore
        self._exp = exp

    def remove_exp(self) -> AExpression | None:
        aexp = self._exp
        if self._exp is not None:
            self._exp.parent(None)  # type: ignore
        self._exp = None
        return aexp

    def exp(self) -> AExpression | None:
        return self._exp

    def __str__(self) -> str:
        if self._exp is None:
            return self.tabs + self._var.to_decl_string() + ";" + self.newline
        return self.tabs + self._var.to_decl_string() + " = " + str(self._exp) + ";" + self.newline

    def close(self):
        super().close()
        if self._exp is not None:
            self._exp.close()  # type: ignore
        self._exp = None
        if self._var is not None:
            self._var.close()
        self._var = None

