from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.node.p_size import PSize  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.t_t import TT  # pyright: ignore[reportMissingImports]

    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]


class ASize(PSize):
    """Port of ASize.java from DeNCS."""

    def __init__(self, t: TT | None = None, pos: TIntegerConstant | None = None, integerConstant: TIntegerConstant | None = None, semi: TSemi | None = None):
        super().__init__()
        self._t: TT | None = None
        self._pos: TIntegerConstant | None = None
        self._integerConstant: TIntegerConstant | None = None
        self._semi: TSemi | None = None

        if t is not None:
            self.set_t(t)
        if pos is not None:
            self.set_pos(pos)
        if integerConstant is not None:
            self.set_integerConstant(integerConstant)
        if semi is not None:
            self.set_semi(semi)

    def clone(self):
        return ASize(self.clone_node(self._t), self.clone_node(self._pos), self.clone_node(self._integerConstant), self.clone_node(self._semi))

    def apply(self, sw: Analysis):
        sw.case_a_size(self)

    def get_t(self) -> TT | None:
        return self._t

    def set_t(self, node: TT | None):
        if self._t is not None:
            self._t.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._t = node

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

    def get_integerConstant(self) -> TIntegerConstant | None:
        return self._integerConstant

    def set_integerConstant(self, node: TIntegerConstant | None):
        if self._integerConstant is not None:
            self._integerConstant.set_parent(None)
        if node is not None:
            if node.parent() is not None:
                node.parent().remove_child(node)
            node.set_parent(self)
        self._integerConstant = node

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
        return self.to_string(self._t) + self.to_string(self._pos) + self.to_string(self._integerConstant) + self.to_string(self._semi)

    def remove_child(self, child: Node):
        if self._t == child:
            self._t = None
            return
        if self._pos == child:
            self._pos = None
            return
        if self._integerConstant == child:
            self._integerConstant = None
            return
        if self._semi == child:
            self._semi = None
            return

    def replace_child(self, old_child: Node, new_child: Node):
        if self._t == old_child:
            self.set_t(new_child)  # type: ignore
            return
        if self._pos == old_child:
            self.set_pos(new_child)  # type: ignore
            return
        if self._integerConstant == old_child:
            self.set_integerConstant(new_child)  # type: ignore
            return
        if self._semi == old_child:
            self.set_semi(new_child)  # type: ignore
            return

    def clone_node(self, node):
        if node is not None:
            return node.clone()
        return None

    def to_string(self, node):
        if node is not None:
            return str(node)
        return ""
