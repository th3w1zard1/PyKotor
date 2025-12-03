from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_bp_op import PBpOp  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_restorebp import TRestorebp  # pyright: ignore[reportMissingImports]

class ARestorebpBpOp(PBpOp):
    def __init__(self):
        super().__init__()
        self._restorebp: TRestorebp | None = None

    def clone(self):
        return ARestorebpBpOp(self.clone_node(self._restorebp))

    def apply(self, sw: Analysis):
        sw.case_a_restorebp_bp_op(self)

    def get_restorebp(self) -> TRestorebp | None:
        return self._restorebp

    def set_restorebp(self, node: TRestorebp | None):
        if self._restorebp is not None:
            self._restorebp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._restorebp = node

    def remove_child(self, child: Node):
        if self._restorebp == child:
            self._restorebp = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._restorebp == old_child:
            self.set_restorebp(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
