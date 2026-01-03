from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.token import Token

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]

class EOF(Token):
    def __init__(self, line: int = 0, pos: int = 0):
        super().__init__("")
        self.set_line(line)
        self.set_pos(pos)

    def clone(self) -> EOF:
        return EOF(self.get_line(), self.get_pos())

    def apply(self, sw: Analysis):
        if hasattr(sw, 'case_eof'):
            sw.case_eof(self)
        else:
            sw.default_case(self)

