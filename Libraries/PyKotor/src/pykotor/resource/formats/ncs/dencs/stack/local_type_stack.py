from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.stack.local_stack import LocalStack  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]

class LocalTypeStack(LocalStack):
    def __init__(self):
        super().__init__()

    def push(self, type: Type):
        self.stack.insert(0, type)

    def get(self, offset: int, state: SubroutineState | None = None) -> Type:
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        pos = 0
        for type_val in self.stack:
            pos += type_val.size()
            if pos > offset:
                return type_val.get_element(pos - offset + 1)
            if pos == offset:
                return type_val.get_element(1)
        if state is not None and state.is_prototyped():
            type_val = state.get_param_type(offset - pos)
            if not type_val.equals(0):
                return type_val
        return Type(-1)

    def remove(self, count: int = 1, start: int = -1):
        if start >= 0:
            # Remove from specific start position
            loc = start - 1
            for _ in range(count):
                if loc < len(self.stack):
                    self.stack.pop(loc)
        else:
            # Remove from front (count items)
            for _ in range(count):
                if self.stack:
                    self.stack.pop(0)

    def remove_params(self, count: int, state: SubroutineState):
        params = []
        for _ in range(count):
            if self.stack:
                type_val = self.stack.pop(0)
                params.insert(0, type_val)
        state.update_params(params)

    def remove_prototyping(self, count: int) -> int:
        params = 0
        i = 0
        while i < count:
            if not self.stack:
                params += 1
                i += 1
            else:
                type_val = self.stack.pop(0)
                i += type_val.size()
        return params

    def clone(self):
        from pykotor.resource.formats.ncs.dencs.stack.local_type_stack import LocalTypeStack  # pyright: ignore[reportMissingImports]
        new_stack = LocalTypeStack()
        new_stack.stack = list(self.stack)
        return new_stack

