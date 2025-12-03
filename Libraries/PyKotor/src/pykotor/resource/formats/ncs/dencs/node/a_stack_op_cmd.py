from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_stack_command import PStackCommand  # pyright: ignore[reportMissingImports]


class AStackOpCmd(PCmd):
    """Port of AStackOpCmd.java from DeNCS."""

    def __init__(self, stackCommand: PStackCommand | None = None):
        super().__init__()
        self._stackCommand: PStackCommand | None = None

        if stackCommand is not None:
            self.set_stackCommand(stackCommand)

    def clone(self):
        return AStackOpCmd(self.clone_node(self._stackCommand))

    def apply(self, sw: Analysis):
        sw.case_a_stack_op_cmd(self)

    def get_stackCommand(self) -> PStackCommand | None:
        return self._stackCommand

    def set_stackCommand(self, node: PStackCommand | None):
        if self._stackCommand is not None:
            self._stackCommand.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._stackCommand = node

    def __str__(self) -> str:
        return self.to_string(self._stackCommand)

    def remove_child(self, child: Node):
        if self._stackCommand == child:
            self._stackCommand = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._stackCommand == old_child:
            self.set_stackCommand(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
