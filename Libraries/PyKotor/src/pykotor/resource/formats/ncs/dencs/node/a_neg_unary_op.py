from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_unary_op import PUnaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_neg import TNeg  # pyright: ignore[reportMissingImports]


class ANegUnaryOp(PUnaryOp):
    """Port of ANegUnaryOp.java from DeNCS."""

    def __init__(self, neg: TNeg | None = None):
        super().__init__()
        self._neg: TNeg | None = None

        if neg is not None:
            self.set_neg(neg)

    def clone(self):
        return ANegUnaryOp(self.clone_node(self._neg))

    def apply(self, sw: Analysis):
        sw.case_a_neg_unary_op(self)

    def get_neg(self) -> TNeg | None:
        return self._neg

    def set_neg(self, node: TNeg | None):
        if self._neg is not None:
            self._neg.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._neg = node

    def __str__(self) -> str:
        return self.to_string(self._neg)

    def remove_child(self, child: Node):
        if self._neg == child:
            self._neg = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._neg == old_child:
            self.set_neg(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
