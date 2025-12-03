from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_bp_command import PBpCommand  # pyright: ignore[reportMissingImports]

class ABpCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._bp_command: PBpCommand | None = None

    def clone(self):
        return ABpCmd(self.clone_node(self._bp_command))

    def apply(self, sw: Analysis):
        sw.case_a_bp_cmd(self)

    def get_bp_command(self) -> PBpCommand | None:
        return self._bp_command

    def set_bp_command(self, node: PBpCommand | None):
        if self._bp_command is not None:
            self._bp_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._bp_command = node

    def remove_child(self, child: Node):
        if self._bp_command == child:
            self._bp_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._bp_command == old_child:
            self.set_bp_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
