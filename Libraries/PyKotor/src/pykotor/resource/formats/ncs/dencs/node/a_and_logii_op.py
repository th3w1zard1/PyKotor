from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_logii_op import PLogiiOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_logandii import TLogandii  # pyright: ignore[reportMissingImports]


class AAndLogiiOp(PLogiiOp):
    """Port of AAndLogiiOp.java from DeNCS."""

    def __init__(self, logandii: TLogandii | None = None):
        super().__init__()
        self._logandii: TLogandii | None = None

        if logandii is not None:
            self.set_logandii(logandii)

    def clone(self):
        return AAndLogiiOp(self.clone_node(self._logandii))

    def apply(self, sw: Analysis):
        sw.case_a_and_logii_op(self)

    def get_logandii(self) -> TLogandii | None:
        return self._logandii

    def set_logandii(self, node: TLogandii | None):
        if self._logandii is not None:
            self._logandii.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._logandii = node

    def __str__(self) -> str:
        return self.to_string(self._logandii)

    def remove_child(self, child: Node):
        if self._logandii == child:
            self._logandii = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._logandii == old_child:
            self.set_logandii(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
