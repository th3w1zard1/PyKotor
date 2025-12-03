from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class AUnkLoopControl(ScriptNode):
    def __init__(self, dest: int):
        super().__init__()
        self.dest: int = dest

    def get_destination(self) -> int:
        return self.dest

    def __str__(self) -> str:
        return "BREAK or CONTINUE undetermined"

