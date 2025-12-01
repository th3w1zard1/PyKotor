from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_binary_op import PBinaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_shright import TShright  # pyright: ignore[reportMissingImports]


class AShrightBinaryOp(PBinaryOp):
    """Port of AShrightBinaryOp.java from DeNCS."""

    def __init__(self, shright: TShright | None = None):
        super().__init__()
        self._shright: TShright | None = None

        if shright is not None:
            self.set_shright(shright)

    def clone(self):
        return AShrightBinaryOp(self.clone_node(self._shright))

    def apply(self, sw: Analysis):
        sw.case_a_shright_binary_op(self)

    def get_shright(self) -> TShright | None:
        return self._shright

    def set_shright(self, node: TShright | None):
        if self._shright is not None:
            self._shright.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._shright = node

    def __str__(self) -> str:
        return self.to_string(self._shright)

    def remove_child(self, child: Node):
        if self._shright == child:
            self._shright = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._shright == old_child:
            self.set_shright(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
