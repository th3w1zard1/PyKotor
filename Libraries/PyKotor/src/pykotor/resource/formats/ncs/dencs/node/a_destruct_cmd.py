from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_destruct_command import PDestructCommand  # pyright: ignore[reportMissingImports]

class ADestructCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._destruct_command: PDestructCommand | None = None

    def clone(self):
        return ADestructCmd(self.clone_node(self._destruct_command))

    def apply(self, sw: Analysis):
        sw.case_a_destruct_cmd(self)

    def get_destruct_command(self) -> PDestructCommand | None:
        return self._destruct_command

    def set_destruct_command(self, node: PDestructCommand | None):
        if self._destruct_command is not None:
            self._destruct_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._destruct_command = node

    def remove_child(self, child: Node):
        if self._destruct_command == child:
            self._destruct_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._destruct_command == old_child:
            self.set_destruct_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
