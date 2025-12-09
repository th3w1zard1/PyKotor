from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


class StructType(Type):
    def __init__(self):
        super().__init__(-15)
        self._types: list[Self] = []
        self._all_typed: bool = True
        self._total_size: int = 0
        self.typename: str | None = None
        self.elements: list[str] | None = None

    def close(self):
        if self._types is not None:
            for type_val in self._types:
                type_val.close()
            self._types = []
        self.elements = None

    def print(self):
        print(f"Struct has {len(self._types)} entries.")
        if self._all_typed:
            print("They have all been typed")
        else:
            print("They have not all been typed")
        for i in range(len(self._types)):
            print(f"  Type: {self._types[i]}")

    def add_type(self, type_val: Type):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self._types.append(type_val)
        if type_val.equals(Type(-1)):
            self._all_typed = False
        self._total_size += type_val.size()

    def add_type_stack_order(self, type_val: Type):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self._types.insert(0, type_val)
        if type_val.equals(Type(-1)):
            self._all_typed = False
        self._total_size += type_val.size()

    def is_vector(self) -> bool:
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if self._total_size != 3:
            return False
        for i in range(3):
            if not self._types[i].equals(Type(4)):
                return False
        return True

    def is_typed(self) -> bool:
        return self._all_typed

    def update_type(self, pos: int, type_val: Type):
        self._types[pos] = type_val
        self.update_typed()

    def types(self) -> list[Type]:
        return list(self._types)

    def update_typed(self):
        self._all_typed = True
        for type_val in self._types:
            if not type_val.is_typed():
                self._all_typed = False
                return

    def equals(self, obj) -> bool:
        return isinstance(obj, StructType) and self._types == obj.types()

    def type_name(self, name: str | None = None) -> str | None:
        if name is not None:
            self.typename = name
        return self.typename

    def to_decl_string(self) -> str:
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if self.is_vector():
            return Type.to_string_static(-16)
        return str(self) + " " + (self.typename or "")

    def element_name(self, i: int) -> str:
        if self.elements is None:
            self.set_element_names()
        if self.elements is None:
            raise RuntimeError("Element names are unavailable.")
        return self.elements[i]

    def get_element(self, pos: int) -> Type:
        curpos = 0
        if len(self._types) == 0:
            raise RuntimeError("Pos was greater than struct size")
        for entry in self._types:
            oldpos = pos
            pos -= entry.size()
            if pos <= 0:
                return entry.get_element(curpos - pos + 1)
            curpos += entry.size()
        raise RuntimeError("Pos was greater than struct size")

    def set_element_names(self):
        self.elements = []
        typecounts: dict[Type, int] = {}
        if self.is_vector():
            self.elements.append("x")
            self.elements.append("y")
            self.elements.append("z")
        else:
            for type_val in self._types:
                typecount = typecounts.get(type_val, 0)
                count = typecount + 1
                self.elements.append(str(type_val) + str(count))
                typecounts[type_val] = count + 1

    def size(self) -> int:
        """Override to report struct total size."""
        return self._total_size
