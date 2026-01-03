from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_jump_if import PJumpIf  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jnz import TJnz  # pyright: ignore[reportMissingImports]

class ANonzeroJumpIf(PJumpIf):
    def __init__(self):
        super().__init__()
        self._jnz: TJnz | None = None

    def clone(self):
        return ANonzeroJumpIf(self.clone_node(self._jnz))

    def apply(self, sw: Analysis):
        sw.case_a_nonzero_jump_if(self)

    def get_jnz(self) -> TJnz | None:
        return self._jnz

    def set_jnz(self, node: TJnz | None):
        if self._jnz is not None:
            self._jnz.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._jnz = node

    def remove_child(self, child: Node):
        if self._jnz == child:
            self._jnz = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._jnz == old_child:
            self.set_jnz(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

