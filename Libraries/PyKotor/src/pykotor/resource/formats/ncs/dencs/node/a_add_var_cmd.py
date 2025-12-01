from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_rsadd_command import PRsaddCommand  # pyright: ignore[reportMissingImports]


class AAddVarCmd(PCmd):
    """Port of AAddVarCmd.java from DeNCS."""

    def __init__(self, rsaddCommand: PRsaddCommand | None = None):
        super().__init__()
        self._rsaddCommand: PRsaddCommand | None = None

        if rsaddCommand is not None:
            self.set_rsaddCommand(rsaddCommand)

    def clone(self):
        return AAddVarCmd(self.clone_node(self._rsaddCommand))

    def apply(self, sw: Analysis):
        sw.case_a_add_var_cmd(self)

    def get_rsaddCommand(self) -> PRsaddCommand | None:
        return self._rsaddCommand

    def set_rsaddCommand(self, node: PRsaddCommand | None):
        if self._rsaddCommand is not None:
            self._rsaddCommand.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._rsaddCommand = node

    def __str__(self) -> str:
        return self.to_string(self._rsaddCommand)

    def remove_child(self, child: Node):
        if self._rsaddCommand == child:
            self._rsaddCommand = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._rsaddCommand == old_child:
            self.set_rsaddCommand(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
