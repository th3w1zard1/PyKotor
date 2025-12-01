from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_equal import TEqual  # pyright: ignore[reportMissingImports]


class AEqualBinaryOp(PBinaryOp):
    """Port of AEqualBinaryOp.java from DeNCS."""

    def __init__(self, equal: TEqual | None = None):
        super().__init__()
        self._equal: TEqual | None = None

        if equal is not None:
            self.set_equal(equal)

    def clone(self):
        return AEqualBinaryOp(self.clone_node(self._equal))

    def apply(self, sw: Analysis):
        sw.case_a_equal_binary_op(self)

    def get_equal(self) -> TEqual | None:
        return self._equal

    def set_equal(self, node: TEqual | None):
        if self._equal is not None:
            self._equal.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._equal = node

    def __str__(self) -> str:
        return self.to_string(self._equal)

    def remove_child(self, child: Node):
        if self._equal == child:
            self._equal = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._equal == old_child:
            self.set_equal(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
