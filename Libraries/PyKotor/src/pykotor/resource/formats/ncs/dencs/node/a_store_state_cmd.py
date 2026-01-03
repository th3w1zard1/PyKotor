from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_store_state_command import PStoreStateCommand  # pyright: ignore[reportMissingImports]

class AStoreStateCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._store_state_command: PStoreStateCommand | None = None

    def clone(self):
        return AStoreStateCmd(self.clone_node(self._store_state_command))

    def apply(self, sw: Analysis):
        sw.case_a_store_state_cmd(self)

    def get_store_state_command(self) -> PStoreStateCommand | None:
        return self._store_state_command

    def set_store_state_command(self, node: PStoreStateCommand | None):
        if self._store_state_command is not None:
            self._store_state_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._store_state_command = node

    def remove_child(self, child: Node):
        if self._store_state_command == child:
            self._store_state_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._store_state_command == old_child:
            self.set_store_state_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
