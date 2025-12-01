from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_logii_op import PLogiiOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_incorii import TIncorii  # pyright: ignore[reportMissingImports]


class AInclOrLogiiOp(PLogiiOp):
    """Port of AInclOrLogiiOp.java from DeNCS."""

    def __init__(self, incorii: TIncorii | None = None):
        super().__init__()
        self._incorii: TIncorii | None = None

        if incorii is not None:
            self.set_incorii(incorii)

    def clone(self):
        return AInclOrLogiiOp(self.clone_node(self._incorii))

    def apply(self, sw: Analysis):
        sw.case_a_incl_or_logii_op(self)

    def get_incorii(self) -> TIncorii | None:
        return self._incorii

    def set_incorii(self, node: TIncorii | None):
        if self._incorii is not None:
            self._incorii.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._incorii = node

    def __str__(self) -> str:
        return self.to_string(self._incorii)

    def remove_child(self, child: Node):
        if self._incorii == child:
            self._incorii = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._incorii == old_child:
            self.set_incorii(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
