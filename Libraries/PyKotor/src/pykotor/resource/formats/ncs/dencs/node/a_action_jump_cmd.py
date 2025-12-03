from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_cmd import PCmd  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_command_block import PCommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_jump_command import PJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_return import PReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_store_state_command import PStoreStateCommand  # pyright: ignore[reportMissingImports]


class AActionJumpCmd(PCmd):
    """Port of AActionJumpCmd.java from DeNCS."""

    def __init__(
        self,
        storeStateCommand: PStoreStateCommand | None = None,
        jumpCommand: PJumpCommand | None = None,
        commandBlock: PCommandBlock | None = None,
        return_node: PReturn | None = None,
    ):
        super().__init__()
        self._storeStateCommand: PStoreStateCommand | None = None
        self._jumpCommand: PJumpCommand | None = None
        self._commandBlock: PCommandBlock | None = None
        self._return: PReturn | None = None

        if storeStateCommand is not None:
            self.set_storeStateCommand(storeStateCommand)
        if jumpCommand is not None:
            self.set_jumpCommand(jumpCommand)
        if commandBlock is not None:
            self.set_commandBlock(commandBlock)
        if return_node is not None:
            self.set_return(return_node)

    def clone(self):
        return AActionJumpCmd(
            self.clone_node(self._storeStateCommand),
            self.clone_node(self._jumpCommand),
            self.clone_node(self._commandBlock),
            self.clone_node(self._return),
        )

    def apply(self, sw: Analysis):
        sw.case_a_action_jump_cmd(self)

    def get_storeStateCommand(self) -> PStoreStateCommand | None:
        return self._storeStateCommand

    def set_storeStateCommand(self, node: PStoreStateCommand | None):
        if self._storeStateCommand is not None:
            self._storeStateCommand.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._storeStateCommand = node

    def get_jumpCommand(self) -> PJumpCommand | None:
        return self._jumpCommand

    def set_jumpCommand(self, node: PJumpCommand | None):
        if self._jumpCommand is not None:
            self._jumpCommand.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._jumpCommand = node

    def get_commandBlock(self) -> PCommandBlock | None:
        return self._commandBlock

    def set_commandBlock(self, node: PCommandBlock | None):
        if self._commandBlock is not None:
            self._commandBlock.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._commandBlock = node

    def get_return(self) -> PReturn | None:
        return self._return

    def set_return(self, node: PReturn | None):
        if self._return is not None:
            self._return.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._return = node

    def __str__(self) -> str:
        return (
            self.to_string(self._storeStateCommand)
            + self.to_string(self._jumpCommand)
            + self.to_string(self._commandBlock)
            + self.to_string(self._return)
        )

    def remove_child(self, child: Node):
        if self._storeStateCommand == child:
            self._storeStateCommand = None
            return
        if self._jumpCommand == child:
            self._jumpCommand = None
            return
        if self._commandBlock == child:
            self._commandBlock = None
            return
        if self._return == child:
            self._return = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._storeStateCommand == old_child:
            self.set_storeStateCommand(new_child)  # type: ignore
            return
        if self._jumpCommand == old_child:
            self.set_jumpCommand(new_child)  # type: ignore
            return
        if self._commandBlock == old_child:
            self.set_commandBlock(new_child)  # type: ignore
            return
        if self._return == old_child:
            self.set_return(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
