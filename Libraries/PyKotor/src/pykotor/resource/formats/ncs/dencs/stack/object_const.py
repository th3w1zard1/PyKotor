from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]


class ObjectConst(Const):
    def __init__(self, value: object):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._type = Type(6)
        self._value: int = int(value) if isinstance(value, (int, str)) else 0
        self._size = 1

    def value(self) -> int:
        return self._value

    def __str__(self) -> str:
        if self._value == 0:
            return "OBJECT_SELF"
        if self._value == 1:
            return "OBJECT_INVALID"
        return str(self._value)

