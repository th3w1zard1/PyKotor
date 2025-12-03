from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_jump_if import PJumpIf  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jz import TJz  # pyright: ignore[reportMissingImports]

class AZeroJumpIf(PJumpIf):
    def __init__(self):
        super().__init__()
        self._jz: TJz | None = None

    def clone(self):
        return AZeroJumpIf(self.clone_node(self._jz))

    def apply(self, sw: Analysis):
        sw.case_a_zero_jump_if(self)

    def get_jz(self) -> TJz | None:
        return self._jz

    def set_jz(self, node: TJz | None):
        if self._jz is not None:
            self._jz.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._jz = node

    def remove_child(self, child: Node):
        if self._jz == child:
            self._jz = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._jz == old_child:
            self.set_jz(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

