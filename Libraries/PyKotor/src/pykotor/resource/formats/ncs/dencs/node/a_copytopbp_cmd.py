from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_copy_top_bp_command import PCopyTopBpCommand  # pyright: ignore[reportMissingImports]

class ACopytopbpCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._copy_top_bp_command: PCopyTopBpCommand | None = None

    def clone(self):
        return ACopytopbpCmd(self.clone_node(self._copy_top_bp_command))

    def apply(self, sw: Analysis):
        sw.case_a_copytopbp_cmd(self)

    def get_copy_top_bp_command(self) -> PCopyTopBpCommand | None:
        return self._copy_top_bp_command

    def set_copy_top_bp_command(self, node: PCopyTopBpCommand | None):
        if self._copy_top_bp_command is not None:
            self._copy_top_bp_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._copy_top_bp_command = node

    def remove_child(self, child: Node):
        if self._copy_top_bp_command == child:
            self._copy_top_bp_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._copy_top_bp_command == old_child:
            self.set_copy_top_bp_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

