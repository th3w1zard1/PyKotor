from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_logii_op import PLogiiOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_excorii import TExcorii  # pyright: ignore[reportMissingImports]


class AExclOrLogiiOp(PLogiiOp):
    """Port of AExclOrLogiiOp.java from DeNCS."""

    def __init__(self, excorii: TExcorii | None = None):
        super().__init__()
        self._excorii: TExcorii | None = None

        if excorii is not None:
            self.set_excorii(excorii)

    def clone(self):
        return AExclOrLogiiOp(self.clone_node(self._excorii))

    def apply(self, sw: Analysis):
        sw.case_a_excl_or_logii_op(self)

    def get_excorii(self) -> TExcorii | None:
        return self._excorii

    def set_excorii(self, node: TExcorii | None):
        if self._excorii is not None:
            self._excorii.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._excorii = node

    def __str__(self) -> str:
        return self.to_string(self._excorii)

    def remove_child(self, child: Node):
        if self._excorii == child:
            self._excorii = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._excorii == old_child:
            self.set_excorii(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
