from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.local_stack import LocalStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]

class Variable(StackEntry):
    FCN_NORMAL = 0
    FCN_RETURN = 1
    FCN_PARAM = 2

    def __init__(self, var_type: Type | int):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        if isinstance(var_type, int):
            self._type = Type(var_type)
        else:
            self._type = var_type
        self._varstruct: VarStruct | None = None
        self._assigned: bool = False
        self._size = 1
        self.function: int = 0
        self.stackcounts: dict[LocalStack, int] = {}
        self._name: str | None = None

    def close(self):
        super().close()
        self.stackcounts = None
        self._varstruct = None

    def done_parse(self):
        self.stackcounts = None

    def done_with_stack(self, stack: LocalVarStack):
        if stack in self.stackcounts:
            del self.stackcounts[stack]

    def set_return(self, isreturn: bool):
        if isreturn:
            self.function = 1
        else:
            self.function = 0

    def set_param(self, isparam: bool):
        if isparam:
            self.function = 2
        else:
            self.function = 0

    def is_return(self) -> bool:
        return self.function == 1

    def is_param(self) -> bool:
        return self.function == 2

    def assign(self):
        self._assigned = True

    def is_assigned(self) -> bool:
        return self._assigned

    def is_struct(self) -> bool:
        return self._varstruct is not None

    def set_varstruct(self, varstruct: VarStruct):
        self._varstruct = varstruct

    def varstruct(self) -> VarStruct | None:
        return self._varstruct

    def added_to_stack(self, stack: LocalStack):
        count = self.stackcounts.get(stack, 0)
        self.stackcounts[stack] = count + 1

    def removed_from_stack(self, stack: LocalStack):
        count = self.stackcounts.get(stack, 0)
        if count == 0:
            if stack in self.stackcounts:
                del self.stackcounts[stack]
        else:
            self.stackcounts[stack] = count - 1

    def is_placeholder(self, stack: LocalStack) -> bool:
        count = self.stackcounts.get(stack, 0)
        return count == 0 and not self._assigned

    def is_on_stack(self, stack: LocalStack) -> bool:
        count = self.stackcounts.get(stack, 0)
        return count > 0

    def set_name(self, name: str):
        self._name = name

    def set_name_with_hint(self, prefix: str, hint: int):
        self._name = prefix + str(self._type) + str(hint)

    def name(self) -> str | None:
        return self._name

    def get_element(self, stackpos: int) -> StackEntry:
        if stackpos != 1:
            raise RuntimeError("Position > 1 for var, not struct")
        return self

    def to_debug_string(self) -> str:
        return "type: " + str(self._type) + " name: " + str(self._name) + " assigned: " + str(self._assigned)

    def __str__(self) -> str:
        if self._varstruct is not None:
            self._varstruct.update_names()
            return str(self._varstruct.name()) + "." + str(self._name)
        return str(self._name) if self._name is not None else ""

    def to_decl_string(self) -> str:
        return str(self._type) + " " + str(self._name)

    def stack_was_cloned(self, oldstack: LocalStack, newstack: LocalStack):
        count = self.stackcounts.get(oldstack, 0)
        if count > 0:
            self.stackcounts[newstack] = count

