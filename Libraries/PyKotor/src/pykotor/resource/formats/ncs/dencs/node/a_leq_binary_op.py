from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_leq import TLeq  # pyright: ignore[reportMissingImports]


class ALeqBinaryOp(PBinaryOp):
    """Port of ALeqBinaryOp.java from DeNCS."""

    def __init__(self, leq: TLeq | None = None):
        super().__init__()
        self._leq: TLeq | None = None

        if leq is not None:
            self.set_leq(leq)

    def clone(self):
        return ALeqBinaryOp(self.clone_node(self._leq))

    def apply(self, sw: Analysis):
        sw.case_a_leq_binary_op(self)

    def get_leq(self) -> TLeq | None:
        return self._leq

    def set_leq(self, node: TLeq | None):
        if self._leq is not None:
            self._leq.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._leq = node

    def __str__(self) -> str:
        return self.to_string(self._leq)

    def remove_child(self, child: Node):
        if self._leq == child:
            self._leq = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._leq == old_child:
            self.set_leq(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
