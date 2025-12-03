from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression
from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]

class AActionArgExp(ScriptRootNode, AExpression):
    def __init__(self, start: int = 0, end: int = 0):
        super().__init__(start, end)
        self.start = start
        self.end = end

    def stackentry(self) -> StackEntry | None:
        return None

    def set_stackentry(self, stackentry: StackEntry):
        pass

