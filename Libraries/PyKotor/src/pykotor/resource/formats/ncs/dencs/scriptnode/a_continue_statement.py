from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class AContinueStatement(ScriptNode):
    def __init__(self):
        super().__init__()

    def __str__(self) -> str:
        return self.tabs + "continue;" + self.newline

