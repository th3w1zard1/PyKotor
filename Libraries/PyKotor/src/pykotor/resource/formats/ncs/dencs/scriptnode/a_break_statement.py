from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class ABreakStatement(ScriptNode):
    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return self.tabs + "break;" + self.newline

