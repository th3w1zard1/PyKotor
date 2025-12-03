from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_logii_op import PLogiiOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_logorii import TLogorii  # pyright: ignore[reportMissingImports]


class AOrLogiiOp(PLogiiOp):
    """Port of AOrLogiiOp.java from DeNCS."""

    def __init__(self, logorii: TLogorii | None = None):
        super().__init__()
        self._logorii: TLogorii | None = None

        if logorii is not None:
            self.set_logorii(logorii)

    def clone(self):
        return AOrLogiiOp(self.clone_node(self._logorii))

    def apply(self, sw: Analysis):
        sw.case_a_or_logii_op(self)

    def get_logorii(self) -> TLogorii | None:
        return self._logorii

    def set_logorii(self, node: TLogorii | None):
        if self._logorii is not None:
            self._logorii.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._logorii = node

    def __str__(self) -> str:
        return self.to_string(self._logorii)

    def remove_child(self, child: Node):
        if self._logorii == child:
            self._logorii = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._logorii == old_child:
            self.set_logorii(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
