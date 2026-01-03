from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_conditional_jump_command import PConditionalJumpCommand  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_jump_if import PJumpIf  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

class AConditionalJumpCommand(PConditionalJumpCommand):
    def __init__(self):
        super().__init__()
        self._jump_if: PJumpIf | None = None
        self._pos: TIntegerConstant | None = None
        self._type: TIntegerConstant | None = None
        self._offset: TIntegerConstant | None = None
        self._semi: TSemi | None = None

    def clone(self):
        return AConditionalJumpCommand(
            self.clone_node(self._jump_if),
            self.clone_node(self._pos),
            self.clone_node(self._type),
            self.clone_node(self._offset),
            self.clone_node(self._semi)
        )

    def apply(self, sw: Analysis):
        sw.case_a_conditional_jump_command(self)

    def get_jump_if(self) -> PJumpIf | None:
        return self._jump_if

    def set_jump_if(self, node: PJumpIf | None):
        if self._jump_if is not None:
            self._jump_if.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._jump_if = node

    def get_pos(self) -> TIntegerConstant | None:
        return self._pos

    def set_pos(self, node: TIntegerConstant | None):
        if self._pos is not None:
            self._pos.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._pos = node

    def get_type(self) -> TIntegerConstant | None:
        return self._type

    def set_type(self, node: TIntegerConstant | None):
        if self._type is not None:
            self._type.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._type = node

    def get_offset(self) -> TIntegerConstant | None:
        return self._offset

    def set_offset(self, node: TIntegerConstant | None):
        if self._offset is not None:
            self._offset.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._offset = node

    def get_semi(self) -> TSemi | None:
        return self._semi

    def set_semi(self, node: TSemi | None):
        if self._semi is not None:
            self._semi.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._semi = node

    def remove_child(self, child: Node):
        if self._jump_if == child:
            self._jump_if = None
            return
        if self._pos == child:
            self._pos = None
            return
        if self._type == child:
            self._type = None
            return
        if self._offset == child:
            self._offset = None
            return
        if self._semi == child:
            self._semi = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._jump_if == old_child:
            self.set_jump_if(new_child)  # type: ignore
            return
        if self._pos == old_child:
            self.set_pos(new_child)  # type: ignore
            return
        if self._type == old_child:
            self.set_type(new_child)  # type: ignore
            return
        if self._offset == old_child:
            self.set_offset(new_child)  # type: ignore
            return
        if self._semi == old_child:
            self.set_semi(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None

