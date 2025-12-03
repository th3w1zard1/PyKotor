from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_geq import TGeq  # pyright: ignore[reportMissingImports]


class AGeqBinaryOp(PBinaryOp):
    """Port of AGeqBinaryOp.java from DeNCS."""

    def __init__(self, geq: TGeq | None = None):
        super().__init__()
        self._geq: TGeq | None = None

        if geq is not None:
            self.set_geq(geq)

    def clone(self):
        return AGeqBinaryOp(self.clone_node(self._geq))

    def apply(self, sw: Analysis):
        sw.case_a_geq_binary_op(self)

    def get_geq(self) -> TGeq | None:
        return self._geq

    def set_geq(self, node: TGeq | None):
        if self._geq is not None:
            self._geq.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._geq = node

    def __str__(self) -> str:
        return self.to_string(self._geq)

    def remove_child(self, child: Node):
        if self._geq == child:
            self._geq = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._geq == old_child:
            self.set_geq(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
