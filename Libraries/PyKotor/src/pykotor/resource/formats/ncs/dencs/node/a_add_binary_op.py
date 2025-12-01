from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_add import TAdd  # pyright: ignore[reportMissingImports]


class AAddBinaryOp(PBinaryOp):
    """Port of AAddBinaryOp.java from DeNCS."""

    def __init__(self, add: TAdd | None = None):
        super().__init__()
        self._add: TAdd | None = None

        if add is not None:
            self.set_add(add)

    def clone(self):
        return AAddBinaryOp(self.clone_node(self._add))

    def apply(self, sw: Analysis):
        sw.case_a_add_binary_op(self)

    def get_add(self) -> TAdd | None:
        return self._add

    def set_add(self, node: TAdd | None):
        if self._add is not None:
            self._add.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._add = node

    def __str__(self) -> str:
        return self.to_string(self._add)

    def remove_child(self, child: Node):
        if self._add == child:
            self._add = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._add == old_child:
            self.set_add(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
