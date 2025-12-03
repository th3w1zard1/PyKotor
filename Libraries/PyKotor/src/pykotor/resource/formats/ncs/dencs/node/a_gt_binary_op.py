from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_gt import TGt  # pyright: ignore[reportMissingImports]


class AGtBinaryOp(PBinaryOp):
    """Port of AGtBinaryOp.java from DeNCS."""

    def __init__(self, gt: TGt | None = None):
        super().__init__()
        self._gt: TGt | None = None

        if gt is not None:
            self.set_gt(gt)

    def clone(self):
        return AGtBinaryOp(self.clone_node(self._gt))

    def apply(self, sw: Analysis):
        sw.case_a_gt_binary_op(self)

    def get_gt(self) -> TGt | None:
        return self._gt

    def set_gt(self, node: TGt | None):
        if self._gt is not None:
            self._gt.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._gt = node

    def __str__(self) -> str:
        return self.to_string(self._gt)

    def remove_child(self, child: Node):
        if self._gt == child:
            self._gt = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._gt == old_child:
            self.set_gt(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
