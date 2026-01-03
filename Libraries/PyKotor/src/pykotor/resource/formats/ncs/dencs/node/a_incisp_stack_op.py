from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_stack_op import PStackOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_incisp import TIncisp  # pyright: ignore[reportMissingImports]


class AIncispStackOp(PStackOp):
    """Port of AIncispStackOp.java from DeNCS."""

    def __init__(self, incisp: TIncisp | None = None):
        super().__init__()
        self._incisp: TIncisp | None = None

        if incisp is not None:
            self.set_incisp(incisp)

    def clone(self):
        return AIncispStackOp(self.clone_node(self._incisp))

    def apply(self, sw: Analysis):
        sw.case_a_incisp_stack_op(self)

    def get_incisp(self) -> TIncisp | None:
        return self._incisp

    def set_incisp(self, node: TIncisp | None):
        if self._incisp is not None:
            self._incisp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._incisp = node

    def __str__(self) -> str:
        return self.to_string(self._incisp)

    def remove_child(self, child: Node):
        if self._incisp == child:
            self._incisp = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._incisp == old_child:
            self.set_incisp(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
