from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_nequal import TNequal  # pyright: ignore[reportMissingImports]


class ANequalBinaryOp(PBinaryOp):
    """Port of ANequalBinaryOp.java from DeNCS."""

    def __init__(self, nequal: TNequal | None = None):
        super().__init__()
        self._nequal: TNequal | None = None

        if nequal is not None:
            self.set_nequal(nequal)

    def clone(self):
        return ANequalBinaryOp(self.clone_node(self._nequal))

    def apply(self, sw: Analysis):
        sw.case_a_nequal_binary_op(self)

    def get_nequal(self) -> TNequal | None:
        return self._nequal

    def set_nequal(self, node: TNequal | None):
        if self._nequal is not None:
            self._nequal.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._nequal = node

    def __str__(self) -> str:
        return self.to_string(self._nequal)

    def remove_child(self, child: Node):
        if self._nequal == child:
            self._nequal = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._nequal == old_child:
            self.set_nequal(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
