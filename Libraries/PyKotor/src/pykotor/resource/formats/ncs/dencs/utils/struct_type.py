from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class StructType(Type):
    def __init__(self):
        super().__init__(-15)
        self.types: list[Type] = []
        self.alltyped: bool = True
        self.size: int = 0
        self.typename: str | None = None
        self.elements: list[str] | None = None

    def close(self):
        if self.types is not None:
            for type_val in self.types:
                type_val.close()
            self.types = None
        self.elements = None

    def print(self):
        print(f"Struct has {len(self.types)} entries.")
        if self.alltyped:
            print("They have all been typed")
        else:
            print("They have not all been typed")
        for i in range(len(self.types)):
            print(f"  Type: {self.types[i]}")

    def add_type(self, type_val: Type):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self.types.append(type_val)
        if type_val.equals(Type(-1)):
            self.alltyped = False
        self.size += type_val.size()

    def add_type_stack_order(self, type_val: Type):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self.types.insert(0, type_val)
        if type_val.equals(Type(-1)):
            self.alltyped = False
        self.size += type_val.size()

    def is_vector(self) -> bool:
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if self.size != 3:
            return False
        for i in range(3):
            if not self.types[i].equals(Type(4)):
                return False
        return True

    def is_typed(self) -> bool:
        return self.alltyped

    def update_type(self, pos: int, type_val: Type):
        self.types[pos] = type_val
        self.update_typed()

    def types(self) -> list[Type]:
        return self.types

    def update_typed(self):
        self.alltyped = True
        for i in range(len(self.types)):
            if not self.types[i].is_typed():
                self.alltyped = False
                return

    def equals(self, obj) -> bool:
        return isinstance(obj, StructType) and self.types == obj.types()

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
        return self.elements[i]

    def get_element(self, pos: int) -> Type:
        curpos = 0
        if len(self.types) == 0:
            raise RuntimeError("Pos was greater than struct size")
        for entry in self.types:
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
            for i in range(len(self.types)):
                type_val = self.types[i]
                typecount = typecounts.get(type_val, 0)
                count = typecount + 1
                self.elements.append(str(type_val) + str(count))
                typecounts[type_val] = count + 1

