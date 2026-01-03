from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_unary_command import PUnaryCommand  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.p_unary_op import PUnaryOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

class AUnaryCommand(PUnaryCommand):
    def __init__(self, unary_op: PUnaryOp | None = None, pos: TIntegerConstant | None = None, type_val: TIntegerConstant | None = None, semi: TSemi | None = None):
        super().__init__()
        
        self._unary_op_: PUnaryOp | None = None
        self._pos_: TIntegerConstant | None = None
        self._type_: TIntegerConstant | None = None
        self._semi_: TSemi | None = None
        
        if unary_op is not None:
            self.set_unary_op(unary_op)
        if pos is not None:
            self.set_pos(pos)
        if type_val is not None:
            self.set_type(type_val)
        if semi is not None:
            self.set_semi(semi)

    def apply(self, sw):
        sw.case_a_unary_command(self)

    def get_unary_op(self) -> PUnaryOp:
        return self._unary_op_

    def set_unary_op(self, node: PUnaryOp):
        if self._unary_op_ is not None:
            self._unary_op_.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._unary_op_ = node

    def get_pos(self) -> TIntegerConstant:
        return self._pos_

    def set_pos(self, node: TIntegerConstant):
        if self._pos_ is not None:
            self._pos_.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._pos_ = node

    def get_type(self) -> TIntegerConstant:
        return self._type_

    def set_type(self, node: TIntegerConstant):
        if self._type_ is not None:
            self._type_.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._type_ = node

    def get_semi(self) -> TSemi:
        return self._semi_

    def set_semi(self, node: TSemi):
        if self._semi_ is not None:
            self._semi_.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._semi_ = node

    def __str__(self) -> str:
        result = []
        if self._unary_op_ is not None:
            result.append(str(self._unary_op_))
        if self._pos_ is not None:
            result.append(str(self._pos_))
        if self._type_ is not None:
            result.append(str(self._type_))
        if self._semi_ is not None:
            result.append(str(self._semi_))
        return "".join(result)

    def remove_child(self, child):
        if self._unary_op_ == child:
            self._unary_op_ = None
            return
        if self._pos_ == child:
            self._pos_ = None
            return
        if self._type_ == child:
            self._type_ = None
            return
        if self._semi_ == child:
            self._semi_ = None

    def replace_child(self, old_child, new_child):
        if self._unary_op_ == old_child:
            self.set_unary_op(new_child)
            return
        if self._pos_ == old_child:
            self.set_pos(new_child)
            return
        if self._type_ == old_child:
            self.set_type(new_child)
            return
        if self._semi_ == old_child:
            self.set_semi(new_child)
