from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_bp_command import PBpCommand  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.p_bp_op import PBpOp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

class ABpCommand(PBpCommand):
    def __init__(self):
        super().__init__()
        self._bp_op: PBpOp | None = None
        self._pos: TIntegerConstant | None = None
        self._type: TIntegerConstant | None = None
        self._semi: TSemi | None = None

    def clone(self):
        return ABpCommand(
            self.clone_node(self._bp_op),  # type: ignore
            self.clone_node(self._pos),  # type: ignore
            self.clone_node(self._type),  # type: ignore
            self.clone_node(self._semi)  # type: ignore
        )

    def apply(self, sw: Analysis):
        sw.case_a_bp_command(self)

    def get_bp_op(self) -> PBpOp | None:
        return self._bp_op

    def set_bp_op(self, node: PBpOp | None):
        if self._bp_op is not None:
            self._bp_op.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._bp_op = node

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
        if self._bp_op == child:
            self._bp_op = None
            return
        if self._pos == child:
            self._pos = None
            return
        if self._type == child:
            self._type = None
            return
        if self._semi == child:
            self._semi = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._bp_op == old_child:
            self.set_bp_op(new_child)  # type: ignore
            return
        if self._pos == old_child:
            self.set_pos(new_child)  # type: ignore
            return
        if self._type == old_child:
            self.set_type(new_child)  # type: ignore
            return
        if self._semi == old_child:
            self.set_semi(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
