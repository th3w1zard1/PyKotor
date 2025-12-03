from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_stack_op import PStackOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_incibp import TIncibp  # pyright: ignore[reportMissingImports]


class AIncibpStackOp(PStackOp):
    """Port of AIncibpStackOp.java from DeNCS."""

    def __init__(self, incibp: TIncibp | None = None):
        super().__init__()
        self._incibp: TIncibp | None = None

        if incibp is not None:
            self.set_incibp(incibp)

    def clone(self):
        return AIncibpStackOp(self.clone_node(self._incibp))

    def apply(self, sw: Analysis):
        sw.case_a_incibp_stack_op(self)

    def get_incibp(self) -> TIncibp | None:
        return self._incibp

    def set_incibp(self, node: TIncibp | None):
        if self._incibp is not None:
            self._incibp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._incibp = node

    def __str__(self) -> str:
        return self.to_string(self._incibp)

    def remove_child(self, child: Node):
        if self._incibp == child:
            self._incibp = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._incibp == old_child:
            self.set_incibp(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
