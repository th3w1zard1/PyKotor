from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.scriptnode.a_control_loop import AControlLoop  # pyright: ignore[reportMissingImports]


class ADoLoop(AControlLoop):
    def __init__(self, start: int = 0, end: int = 0):
        super().__init__(start, end)

    def __str__(self) -> str:
        buff = []
        buff.append(self.tabs)
        buff.append("do {" + self.newline)
        for child in self.children:
            buff.append(str(child))
        buff.append(self.tabs + "} while (" + str(self.condition) + ");" + self.newline)
        return "".join(buff)

