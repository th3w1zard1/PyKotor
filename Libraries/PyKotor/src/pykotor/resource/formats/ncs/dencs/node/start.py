from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.node import Node

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.eof import EOF  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_program import PProgram  # pyright: ignore[reportMissingImports]

class Start(Node):
    def __init__(self, p_program: PProgram | None = None, eof: EOF | None = None):
        super().__init__()
        self._p_program: PProgram | None = None
        self._eof: EOF | None = None
        if p_program is not None:
            self.set_p_program(p_program)
        if eof is not None:
            self.set_eof(eof)
        else:
            from pykotor.resource.formats.ncs.dencs.node.eof import EOF  # pyright: ignore[reportMissingImports]
            self.set_eof(EOF())

    def clone(self) -> Start:
        p_program_clone = None
        if self._p_program is not None:
            p_program_clone = self._p_program.clone()  # type: ignore[assignment]
        eof_clone = None
        if self._eof is not None:
            eof_clone = self._eof.clone()
        return Start(p_program_clone, eof_clone)

    def apply(self, sw: Analysis):
        if hasattr(sw, 'case_start'):
            sw.case_start(self)
        else:
            sw.default_case(self)

    def get_p_program(self) -> PProgram | None:
        return self._p_program

    def set_p_program(self, node: PProgram | None):
        if self._p_program is not None:
            self._p_program.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._p_program = node

    def get_eof(self) -> EOF | None:
        return self._eof

    def set_eof(self, node: EOF | None):
        if self._eof is not None:
            self._eof.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._eof = node

    def remove_child(self, child: Node):
        if self._p_program == child:
            self._p_program = None
            return
        if self._eof == child:
            self._eof = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._p_program == old_child:
            self.set_p_program(new_child)  # type: ignore[arg-type]
            return
        if self._eof == old_child:
            self.set_eof(new_child)  # type: ignore[arg-type]

    def __str__(self) -> str:
        result = ""
        if self._p_program is not None:
            result += str(self._p_program)
        if self._eof is not None:
            result += str(self._eof)
        return result

