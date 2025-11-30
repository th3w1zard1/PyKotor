from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_bp_op import PBpOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_savebp import TSavebp  # pyright: ignore[reportMissingImports]

class ASavebpBpOp(PBpOp):
    def __init__(self):
        super().__init__()
        self._savebp: TSavebp | None = None

    def clone(self):
        return ASavebpBpOp(self.clone_node(self._savebp))

    def apply(self, sw: Analysis):
        sw.case_a_savebp_bp_op(self)

    def get_savebp(self) -> TSavebp | None:
        return self._savebp

    def set_savebp(self, node: TSavebp | None):
        if self._savebp is not None:
            self._savebp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._savebp = node

    def remove_child(self, child: Node):
        if self._savebp == child:
            self._savebp = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._savebp == old_child:
            self.set_savebp(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
