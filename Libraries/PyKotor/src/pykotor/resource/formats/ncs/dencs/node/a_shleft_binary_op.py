from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_shleft import TShleft  # pyright: ignore[reportMissingImports]


class AShleftBinaryOp(PBinaryOp):
    """Port of AShleftBinaryOp.java from DeNCS."""

    def __init__(self, shleft: TShleft | None = None):
        super().__init__()
        self._shleft: TShleft | None = None

        if shleft is not None:
            self.set_shleft(shleft)

    def clone(self):
        return AShleftBinaryOp(self.clone_node(self._shleft))

    def apply(self, sw: Analysis):
        sw.case_a_shleft_binary_op(self)

    def get_shleft(self) -> TShleft | None:
        return self._shleft

    def set_shleft(self, node: TShleft | None):
        if self._shleft is not None:
            self._shleft.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._shleft = node

    def __str__(self) -> str:
        return self.to_string(self._shleft)

    def remove_child(self, child: Node):
        if self._shleft == child:
            self._shleft = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._shleft == old_child:
            self.set_shleft(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
