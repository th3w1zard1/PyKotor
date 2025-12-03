from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_mul import TMul  # pyright: ignore[reportMissingImports]


class AMulBinaryOp(PBinaryOp):
    """Port of AMulBinaryOp.java from DeNCS."""

    def __init__(self, mul: TMul | None = None):
        super().__init__()
        self._mul: TMul | None = None

        if mul is not None:
            self.set_mul(mul)

    def clone(self):
        return AMulBinaryOp(self.clone_node(self._mul))

    def apply(self, sw: Analysis):
        sw.case_a_mul_binary_op(self)

    def get_mul(self) -> TMul | None:
        return self._mul

    def set_mul(self, node: TMul | None):
        if self._mul is not None:
            self._mul.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._mul = node

    def __str__(self) -> str:
        return self.to_string(self._mul)

    def remove_child(self, child: Node):
        if self._mul == child:
            self._mul = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._mul == old_child:
            self.set_mul(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
