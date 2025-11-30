from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_conditional_jump_command import PConditionalJumpCommand  # pyright: ignore[reportMissingImports]

class ACondJumpCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._conditional_jump_command: PConditionalJumpCommand | None = None

    def clone(self):
        return ACondJumpCmd(self.clone_node(self._conditional_jump_command))

    def apply(self, sw: Analysis):
        sw.case_a_cond_jump_cmd(self)

    def get_conditional_jump_command(self) -> PConditionalJumpCommand | None:
        return self._conditional_jump_command

    def set_conditional_jump_command(self, node: PConditionalJumpCommand | None):
        if self._conditional_jump_command is not None:
            self._conditional_jump_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._conditional_jump_command = node

    def remove_child(self, child: Node):
        if self._conditional_jump_command == child:
            self._conditional_jump_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._conditional_jump_command == old_child:
            self.set_conditional_jump_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

