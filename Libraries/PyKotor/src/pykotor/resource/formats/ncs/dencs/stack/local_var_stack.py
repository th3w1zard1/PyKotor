from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.stack.local_stack import LocalStack  # pyright: ignore[reportMissingImports]
from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]

class LocalVarStack(LocalStack):
    def __init__(self):
        super().__init__()
        # Use list like LocalStack, but we'll use insert(0, ...) and pop(0) for addFirst/removeFirst semantics
        self.stack = []

    def close(self):
        if self.stack is not None:
            for entry in self.stack:
                entry.close()
        super().close()

    def done_parse(self):
        if self.stack is not None:
            for entry in self.stack:
                entry.done_parse()
            self.stack = None

    def done_with_stack(self):
        if self.stack is not None:
            for entry in self.stack:
                entry.done_with_stack(self)
            self.stack = None

    def size(self) -> int:
        size = 0
        for entry in self.stack:
            size += entry.size()
        return size

    def push(self, entry: StackEntry):
        self.stack.insert(0, entry)
        entry.added_to_stack(self)

    def get(self, offset: int) -> StackEntry:
        pos = 0
        for entry in self.stack:
            pos += entry.size()
            if pos > offset:
                return entry.get_element(pos - offset + 1)
            if pos == offset:
                return entry.get_element(1)
        raise RuntimeError(f"offset {offset} was greater than stack size {pos}")

    def get_type(self, offset: int) -> Type:
        return self.get(offset).type()

    def remove(self) -> StackEntry:
        if not self.stack:
            raise RuntimeError("Cannot remove from empty stack")
        entry = self.stack.pop(0)
        entry.removed_from_stack(self)
        return entry

    def destruct(self, removesize: int, savestart: int, savesize: int, subdata: SubroutineAnalysisData):
        self.structify(1, removesize, subdata)
        if savesize > 1:
            self.structify(removesize - (savestart + savesize) + 1, savesize, subdata)
        struct = self.stack[0]
        element = struct.get_element(removesize - (savestart + savesize) + 1)
        self.stack[0] = element

    def structify(self, firstelement: int, count: int, subdata: SubroutineAnalysisData) -> VarStruct | None:
        pos = 0
        stack_list = list(self.stack)
        for i, entry in enumerate(stack_list):
            pos += entry.size()
            if pos == firstelement:
                varstruct = VarStruct()
                varstruct.add_var_stack_order(entry)  # type: ignore
                stack_list[i] = varstruct
                j = i + 1
                while j < len(stack_list) and pos <= firstelement + count - 1:
                    entry = stack_list[j]
                    pos += entry.size()
                    if pos <= firstelement + count - 1:
                        varstruct.add_var_stack_order(entry)  # type: ignore
                        stack_list.pop(j)
                    else:
                        break
                self.stack = stack_list
                subdata.add_struct(varstruct)
                return varstruct
            if pos == firstelement + count - 1:
                return entry  # type: ignore
            if pos > firstelement + count - 1:
                return entry.structify(firstelement - (pos - entry.size()), count, subdata)  # type: ignore
        return None

    def clone(self):
        from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        new_stack = LocalVarStack()
        new_stack.stack = list(self.stack)
        for entry in self.stack:
            if isinstance(entry, Variable):
                entry.stack_was_cloned(self, new_stack)
        return new_stack

