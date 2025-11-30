from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_store_state_command import PStoreStateCommand  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_storestate import TStorestate  # pyright: ignore[reportMissingImports]

class AStoreStateCommand(PStoreStateCommand):
    def __init__(self):
        super().__init__()
        self._storestate: TStorestate | None = None
        self._pos: TIntegerConstant | None = None
        self._offset: TIntegerConstant | None = None
        self._size_bp: TIntegerConstant | None = None
        self._size_sp: TIntegerConstant | None = None
        self._semi: TSemi | None = None

    def clone(self):
        return AStoreStateCommand(
            self.clone_node(self._storestate),  # type: ignore
            self.clone_node(self._pos),  # type: ignore
            self.clone_node(self._offset),  # type: ignore
            self.clone_node(self._size_bp),  # type: ignore
            self.clone_node(self._size_sp),  # type: ignore
            self.clone_node(self._semi)  # type: ignore
        )

    def apply(self, sw: Analysis):
        sw.case_a_store_state_command(self)

    def get_storestate(self) -> TStorestate | None:
        return self._storestate

    def set_storestate(self, node: TStorestate | None):
        if self._storestate is not None:
            self._storestate.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._storestate = node

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

    def get_size_bp(self) -> TIntegerConstant | None:
        return self._size_bp

    def set_size_bp(self, node: TIntegerConstant | None):
        if self._size_bp is not None:
            self._size_bp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._size_bp = node

    def get_size_sp(self) -> TIntegerConstant | None:
        return self._size_sp

    def set_size_sp(self, node: TIntegerConstant | None):
        if self._size_sp is not None:
            self._size_sp.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._size_sp = node

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
        if self._storestate == child:
            self._storestate = None
            return
        if self._pos == child:
            self._pos = None
            return
        if self._offset == child:
            self._offset = None
            return
        if self._size_bp == child:
            self._size_bp = None
            return
        if self._size_sp == child:
            self._size_sp = None
            return
        if self._semi == child:
            self._semi = None

    def replace_child(self, old_child: Node, new_child: Node):
        if self._storestate == old_child:
            self.set_storestate(new_child)  # type: ignore
            return
        if self._pos == old_child:
            self.set_pos(new_child)  # type: ignore
            return
        if self._offset == old_child:
            self.set_offset(new_child)  # type: ignore
            return
        if self._size_bp == old_child:
            self.set_size_bp(new_child)  # type: ignore
            return
        if self._size_sp == old_child:
            self.set_size_sp(new_child)  # type: ignore
            return
        if self._semi == old_child:
            self.set_semi(new_child)  # type: ignore

    def clone_node(self, node: Node | None) -> Node | None:
        if node is not None:
            return node.clone()
        return None
