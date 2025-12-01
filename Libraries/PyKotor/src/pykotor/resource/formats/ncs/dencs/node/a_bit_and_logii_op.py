from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_logii_op import PLogiiOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_boolandii import TBoolandii  # pyright: ignore[reportMissingImports]


class ABitAndLogiiOp(PLogiiOp):
    """Port of ABitAndLogiiOp.java from DeNCS."""

    def __init__(self, boolandii: TBoolandii | None = None):
        super().__init__()
        self._boolandii: TBoolandii | None = None

        if boolandii is not None:
            self.set_boolandii(boolandii)

    def clone(self):
        return ABitAndLogiiOp(self.clone_node(self._boolandii))

    def apply(self, sw: Analysis):
        sw.case_a_bit_and_logii_op(self)

    def get_boolandii(self) -> TBoolandii | None:
        return self._boolandii

    def set_boolandii(self, node: TBoolandii | None):
        if self._boolandii is not None:
            self._boolandii.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._boolandii = node

    def __str__(self) -> str:
        return self.to_string(self._boolandii)

    def remove_child(self, child: Node):
        if self._boolandii == child:
            self._boolandii = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._boolandii == old_child:
            self.set_boolandii(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
