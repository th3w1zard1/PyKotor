from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_logii_command import PLogiiCommand  # pyright: ignore[reportMissingImports]

class ALogiiCmd(PCmd):
    def __init__(self):
        super().__init__()
        self._logii_command: PLogiiCommand | None = None

    def clone(self):
        return ALogiiCmd(self.clone_node(self._logii_command))

    def apply(self, sw: Analysis):
        sw.case_a_logii_cmd(self)

    def get_logii_command(self) -> PLogiiCommand | None:
        return self._logii_command

    def set_logii_command(self, node: PLogiiCommand | None):
        if self._logii_command is not None:
            self._logii_command.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._logii_command = node

    def remove_child(self, child: Node):
        if self._logii_command == child:
            self._logii_command = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._logii_command == old_child:
            self.set_logii_command(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
