from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_binary_command import PBinaryCommand  # pyright: ignore[reportMissingImports]

class ABinaryCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._binary_command: PBinaryCommand | None = None

    def clone(self):
        return ABinaryCmd(self.clone_node(self._binary_command))

    def apply(self, sw: Analysis):
        sw.case_a_binary_cmd(self)

    def get_binary_command(self) -> PBinaryCommand | None:
        return self._binary_command

    def set_binary_command(self, node: PBinaryCommand | None):
        if self._binary_command is not None:
            self._binary_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._binary_command = node

    def remove_child(self, child: Node):
        if self._binary_command == child:
            self._binary_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._binary_command == old_child:
            self.set_binary_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
