from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_stack_command import PStackCommand

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_stack_op import PStackOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]


class AStackCommand(PStackCommand):
    """Port of AStackCommand.java from DeNCS."""

    def __init__(
        self,
        stack_op: PStackOp | None = None,
        pos: TIntegerConstant | None = None,
        type_: TIntegerConstant | None = None,
        offset: TIntegerConstant | None = None,
        semi: TSemi | None = None,
    ):
        super().__init__()
        self._stack_op: PStackOp | None = None
        self._pos: TIntegerConstant | None = None
        self._type: TIntegerConstant | None = None
        self._offset: TIntegerConstant | None = None
        self._semi: TSemi | None = None

        if stack_op is not None:
            self.set_stack_op(stack_op)
        if pos is not None:
            self.set_pos(pos)
        if type_ is not None:
            self.set_type(type_)
        if offset is not None:
            self.set_offset(offset)
        if semi is not None:
            self.set_semi(semi)

    def clone(self):
        return AStackCommand(
            self.clone_node(self._stack_op),
            self.clone_node(self._pos),
            self.clone_node(self._type),
            self.clone_node(self._offset),
            self.clone_node(self._semi),
        )

    def apply(self, sw: Analysis):
        sw.case_a_stack_command(self)

    def get_stack_op(self) -> PStackOp | None:
        return self._stack_op

    def set_stack_op(self, node: PStackOp | None):
        if self._stack_op is not None:
            self._stack_op.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._stack_op = node

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

    def __str__(self) -> str:
        return (
            self.to_string(self._stack_op)
            + self.to_string(self._pos)
            + self.to_string(self._type)
            + self.to_string(self._offset)
            + self.to_string(self._semi)
        )

    def remove_child(self, child: Node):
        if self._stack_op == child:
            self._stack_op = None
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
        if self._stack_op == old_child:
            self.set_stack_op(new_child)  # type: ignore
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

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
