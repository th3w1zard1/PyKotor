from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_sub import TSub  # pyright: ignore[reportMissingImports]


class ASubBinaryOp(PBinaryOp):
    """Port of ASubBinaryOp.java from DeNCS."""

    def __init__(self, sub: TSub | None = None):
        super().__init__()
        self._sub: TSub | None = None

        if sub is not None:
            self.set_sub(sub)

    def clone(self):
        return ASubBinaryOp(self.clone_node(self._sub))

    def apply(self, sw: Analysis):
        sw.case_a_sub_binary_op(self)

    def get_sub(self) -> TSub | None:
        return self._sub

    def set_sub(self, node: TSub | None):
        if self._sub is not None:
            self._sub.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._sub = node

    def __str__(self) -> str:
        return self.to_string(self._sub)

    def remove_child(self, child: Node):
        if self._sub == child:
            self._sub = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._sub == old_child:
            self.set_sub(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
