from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_stack_op import PStackOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_decisp import TDecisp  # pyright: ignore[reportMissingImports]


class ADecispStackOp(PStackOp):
    """Port of ADecispStackOp.java from DeNCS."""

    def __init__(self, decisp: TDecisp | None = None):
        super().__init__()
        self._decisp: TDecisp | None = None

        if decisp is not None:
            self.set_decisp(decisp)

    def clone(self):
        return ADecispStackOp(self.clone_node(self._decisp))

    def apply(self, sw: Analysis):
        sw.case_a_decisp_stack_op(self)

    def get_decisp(self) -> TDecisp | None:
        return self._decisp

    def set_decisp(self, node: TDecisp | None):
        if self._decisp is not None:
            self._decisp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._decisp = node

    def __str__(self) -> str:
        return self.to_string(self._decisp)

    def remove_child(self, child: Node):
        if self._decisp == child:
            self._decisp = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._decisp == old_child:
            self.set_decisp(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
