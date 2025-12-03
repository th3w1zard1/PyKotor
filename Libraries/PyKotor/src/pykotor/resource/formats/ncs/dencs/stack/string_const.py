from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]


class StringConst(Const):
    def __init__(self, value: object):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        self._type = Type(5)
        if isinstance(value, str):
            if value.startswith('"') and value.endswith('"'):
                self._value: str = value[1:-1]
            else:
                self._value = value
        else:
            self._value = str(value)
        self._size = 1

    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return str(self._value)

