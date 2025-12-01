from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_unary_op import PUnaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_comp import TComp  # pyright: ignore[reportMissingImports]


class ACompUnaryOp(PUnaryOp):
    """Port of ACompUnaryOp.java from DeNCS."""

    def __init__(self, comp: TComp | None = None):
        super().__init__()
        self._comp: TComp | None = None

        if comp is not None:
            self.set_comp(comp)

    def clone(self):
        return ACompUnaryOp(self.clone_node(self._comp))

    def apply(self, sw: Analysis):
        sw.case_a_comp_unary_op(self)

    def get_comp(self) -> TComp | None:
        return self._comp

    def set_comp(self, node: TComp | None):
        if self._comp is not None:
            self._comp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._comp = node

    def __str__(self) -> str:
        return self.to_string(self._comp)

    def remove_child(self, child: Node):
        if self._comp == child:
            self._comp = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._comp == old_child:
            self.set_comp(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
