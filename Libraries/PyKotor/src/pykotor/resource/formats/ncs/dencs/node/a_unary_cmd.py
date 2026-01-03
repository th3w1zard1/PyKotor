from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_unary_command import PUnaryCommand  # pyright: ignore[reportMissingImports]

class AUnaryCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._unary_command: PUnaryCommand | None = None

    def clone(self):
        return AUnaryCmd(self.clone_node(self._unary_command))

    def apply(self, sw: Analysis):
        sw.case_a_unary_cmd(self)

    def get_unary_command(self) -> PUnaryCommand | None:
        return self._unary_command

    def set_unary_command(self, node: PUnaryCommand | None):
        if self._unary_command is not None:
            self._unary_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._unary_command = node

    def remove_child(self, child: Node):
        if self._unary_command == child:
            self._unary_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._unary_command == old_child:
            self.set_unary_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
