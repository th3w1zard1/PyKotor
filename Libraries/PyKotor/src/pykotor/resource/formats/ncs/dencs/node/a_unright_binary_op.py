from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_unright import TUnright  # pyright: ignore[reportMissingImports]


class AUnrightBinaryOp(PBinaryOp):
    """Port of AUnrightBinaryOp.java from DeNCS."""

    def __init__(self, unright: TUnright | None = None):
        super().__init__()
        self._unright: TUnright | None = None

        if unright is not None:
            self.set_unright(unright)

    def clone(self):
        return AUnrightBinaryOp(self.clone_node(self._unright))

    def apply(self, sw: Analysis):
        sw.case_a_unright_binary_op(self)

    def get_unright(self) -> TUnright | None:
        return self._unright

    def set_unright(self, node: TUnright | None):
        if self._unright is not None:
            self._unright.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._unright = node

    def __str__(self) -> str:
        return self.to_string(self._unright)

    def remove_child(self, child: Node):
        if self._unright == child:
            self._unright = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._unright == old_child:
            self.set_unright(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
