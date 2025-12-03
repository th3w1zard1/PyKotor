from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_stack_op import PStackOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_decibp import TDecibp  # pyright: ignore[reportMissingImports]


class ADecibpStackOp(PStackOp):
    """Port of ADecibpStackOp.java from DeNCS."""

    def __init__(self, decibp: TDecibp | None = None):
        super().__init__()
        self._decibp: TDecibp | None = None

        if decibp is not None:
            self.set_decibp(decibp)

    def clone(self):
        return ADecibpStackOp(self.clone_node(self._decibp))

    def apply(self, sw: Analysis):
        sw.case_a_decibp_stack_op(self)

    def get_decibp(self) -> TDecibp | None:
        return self._decibp

    def set_decibp(self, node: TDecibp | None):
        if self._decibp is not None:
            self._decibp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._decibp = node

    def __str__(self) -> str:
        return self.to_string(self._decibp)

    def remove_child(self, child: Node):
        if self._decibp == child:
            self._decibp = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._decibp == old_child:
            self.set_decibp(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
