from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_lt import TLt  # pyright: ignore[reportMissingImports]


class ALtBinaryOp(PBinaryOp):
    """Port of ALtBinaryOp.java from DeNCS."""

    def __init__(self, lt: TLt | None = None):
        super().__init__()
        self._lt: TLt | None = None

        if lt is not None:
            self.set_lt(lt)

    def clone(self):
        return ALtBinaryOp(self.clone_node(self._lt))

    def apply(self, sw: Analysis):
        sw.case_a_lt_binary_op(self)

    def get_lt(self) -> TLt | None:
        return self._lt

    def set_lt(self, node: TLt | None):
        if self._lt is not None:
            self._lt.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._lt = node

    def __str__(self) -> str:
        return self.to_string(self._lt)

    def remove_child(self, child: Node):
        if self._lt == child:
            self._lt = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._lt == old_child:
            self.set_lt(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
