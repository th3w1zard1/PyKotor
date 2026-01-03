from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_mod import TMod  # pyright: ignore[reportMissingImports]


class AModBinaryOp(PBinaryOp):
    """Port of AModBinaryOp.java from DeNCS."""

    def __init__(self, mod: TMod | None = None):
        super().__init__()
        self._mod: TMod | None = None

        if mod is not None:
            self.set_mod(mod)

    def clone(self):
        return AModBinaryOp(self.clone_node(self._mod))

    def apply(self, sw: Analysis):
        sw.case_a_mod_binary_op(self)

    def get_mod(self) -> TMod | None:
        return self._mod

    def set_mod(self, node: TMod | None):
        if self._mod is not None:
            self._mod.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._mod = node

    def __str__(self) -> str:
        return self.to_string(self._mod)

    def remove_child(self, child: Node):
        if self._mod == child:
            self._mod = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._mod == old_child:
            self.set_mod(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
