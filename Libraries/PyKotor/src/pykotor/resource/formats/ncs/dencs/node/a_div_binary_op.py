from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_div import TDiv  # pyright: ignore[reportMissingImports]


class ADivBinaryOp(PBinaryOp):
    """Port of ADivBinaryOp.java from DeNCS."""

    def __init__(self, div: TDiv | None = None):
        super().__init__()
        self._div: TDiv | None = None

        if div is not None:
            self.set_div(div)

    def clone(self):
        return ADivBinaryOp(self.clone_node(self._div))

    def apply(self, sw: Analysis):
        sw.case_a_div_binary_op(self)

    def get_div(self) -> TDiv | None:
        return self._div

    def set_div(self, node: TDiv | None):
        if self._div is not None:
            self._div.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._div = node

    def __str__(self) -> str:
        return self.to_string(self._div)

    def remove_child(self, child: Node):
        if self._div == child:
            self._div = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._div == old_child:
            self.set_div(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
