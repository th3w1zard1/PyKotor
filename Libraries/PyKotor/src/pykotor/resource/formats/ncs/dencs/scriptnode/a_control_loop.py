from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]

class AControlLoop(ScriptRootNode):
    def __init__(self, start: int = 0, end: int = 0):
        super().__init__(start, end)
        self._condition: AExpression | None = None

    def end(self, end: int):
        self.end = end

    @property
    def condition(self) -> AExpression | None:
        return self._condition

    @condition.setter
    def condition(self, condition: AExpression):
        condition.parent(self)  # type: ignore
        self._condition = condition

    def close(self):
        super().close()
        if self._condition is not None:
            self._condition.close()  # type: ignore
            self._condition = None

