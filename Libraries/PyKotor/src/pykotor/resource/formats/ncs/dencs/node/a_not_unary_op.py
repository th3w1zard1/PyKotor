from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_unary_op import PUnaryOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_not import TNot  # pyright: ignore[reportMissingImports]


class ANotUnaryOp(PUnaryOp):
    """Port of ANotUnaryOp.java from DeNCS."""

    def __init__(self, not_token: TNot | None = None):
        super().__init__()
        self._not: TNot | None = None

        if not_token is not None:
            self.set_not(not_token)

    def clone(self):
        return ANotUnaryOp(self.clone_node(self._not))

    def apply(self, sw: Analysis):
        sw.case_a_not_unary_op(self)

    def get_not(self) -> TNot | None:
        return self._not

    def set_not(self, node: TNot | None):
        if self._not is not None:
            self._not.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._not = node

    def __str__(self) -> str:
        return self.to_string(self._not)

    def remove_child(self, child: Node):
        if self._not == child:
            self._not = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._not == old_child:
            self.set_not(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
