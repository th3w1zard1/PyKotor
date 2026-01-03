from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.token import Token

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis

class TLogandii(Token):
    def __init__(self, line: int = 0, pos: int = 0):
        super().__init__("LOGANDII")
        self.line = line
        self.pos = pos

    def clone(self) -> Token:
        return TLogandii(self.get_line(), self.get_pos())

    def apply(self, sw: Analysis):
        sw.case_t_logandii(self)

    def set_text(self, text: str):
        raise RuntimeError("Cannot change TLogandii text.")
