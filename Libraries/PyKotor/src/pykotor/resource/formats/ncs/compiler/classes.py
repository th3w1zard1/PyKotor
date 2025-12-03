from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, cast

from pykotor.common.script import DataType
from pykotor.resource.formats.ncs import NCS, NCSInstruction, NCSInstructionType
from pykotor.tools.path import CaseAwarePath

if TYPE_CHECKING:
    from pykotor.common.script import ScriptConstant, ScriptFunction


def get_logical_equality_instruction(
    type1: DynamicDataType,
    type2: DynamicDataType,
) -> NCSInstructionType:
    if type1 == DataType.INT and type2 == DataType.INT:
        return NCSInstructionType.EQUALII
    if type1 == DataType.FLOAT and type2 == DataType.FLOAT:
        return NCSInstructionType.EQUALFF
    msg = f"Tried an unsupported comparison between '{type1}' '{type2}'."
    raise CompileError(msg)


class CompileError(Exception):
    """Base exception for NSS compilation errors.

    Provides detailed error messages to help debug script issues.
    
    References:
    ----------
        vendor/HoloLSP/server/src/nwscript-parser.ts (NSS parser error handling)
        vendor/xoreos-tools/src/nwscript/compiler.cpp (NSS compiler error handling)
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (TypeScript compiler errors)
    """

    def __init__(self, message: str, line_num: int | None = None, context: str | None = None):
        full_message = message
        if line_num is not None:
            full_message = f"Line {line_num}: {message}"
        if context:
            full_message = f"{full_message}\n  Context: {context}"
        super().__init__(full_message)
        self.line_num = line_num
        self.context = context


class EntryPointError(CompileError):
    """Raised when script has no valid entry point (main or StartingConditional)."""


class MissingIncludeError(CompileError):
    """Raised when a #include file cannot be found."""


class TopLevelObject(ABC):
    @abstractmethod
    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        ...


class GlobalVariableInitialization(TopLevelObject):
    def __init__(
        self,
        identifier: Identifier,
        data_type: DynamicDataType,
        value: Expression,
        is_const: bool = False,
    ):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type
        self.expression: Expression = value
        self.is_const: bool = is_const

    def compile(self, ncs: NCS, root: CodeRoot):
        # Allocate storage for the global variable (this also registers it in the global scope)
        declaration = GlobalVariableDeclaration(self.identifier, self.data_type, self.is_const)
        declaration.compile(ncs, root)

        block = CodeBlock()
        expression_type = self.expression.compile(ncs, root, block)
        if expression_type != self.data_type:
            msg = (
                f"Type mismatch in initialization of global variable '{self.identifier}'\n"
                f"  Declared type: {self.data_type.builtin.name}\n"
                f"  Initializer type: {expression_type.builtin.name}"
            )
            raise CompileError(msg)

        scoped = root.get_scoped(self.identifier, root)
        # Global storage resides on the stack before base pointer is saved, so use stack-pointer-relative copy.
        stack_index = scoped.offset - scoped.datatype.size(root)
        ncs.instructions.append(
            NCSInstruction(
                NCSInstructionType.CPDOWNSP,
                [stack_index, scoped.datatype.size(root)],
            ),
        )
        # Remove the initializer value from the stack
        ncs.add(NCSInstructionType.MOVSP, args=[-scoped.datatype.size(root)])


class GlobalVariableDeclaration(TopLevelObject):
    def __init__(self, identifier: Identifier, data_type: DynamicDataType, is_const: bool = False):
        super().__init__()
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type
        self.is_const: bool = is_const

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        if self.data_type.builtin == DataType.INT:
            ncs.add(NCSInstructionType.RSADDI)
        elif self.data_type.builtin == DataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF)
        elif self.data_type.builtin == DataType.STRING:
            ncs.add(NCSInstructionType.RSADDS)
        elif self.data_type.builtin == DataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO)
        elif self.data_type.builtin == DataType.EVENT:
            ncs.add(NCSInstructionType.RSADDEVT)
        elif self.data_type.builtin == DataType.LOCATION:
            ncs.add(NCSInstructionType.RSADDLOC)
        elif self.data_type.builtin == DataType.TALENT:
            ncs.add(NCSInstructionType.RSADDTAL)
        elif self.data_type.builtin == DataType.EFFECT:
            ncs.add(NCSInstructionType.RSADDEFF)
        elif self.data_type.builtin == DataType.VECTOR:
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
        elif self.data_type.builtin == DataType.STRUCT:
            struct_name = self.data_type._struct  # noqa: SLF001
            if struct_name is not None and struct_name in root.struct_map:
                root.struct_map[struct_name].initialize(ncs, root)
            else:
                msg = f"Unknown struct type for variable '{self.identifier}'"
                raise CompileError(msg)
        elif self.data_type.builtin == DataType.VOID:
            msg = (
                f"Cannot declare variable '{self.identifier}' with void type\n"
                f"  void can only be used as a function return type"
            )
            raise CompileError(msg)
        else:
            msg = (
                f"Unsupported type '{self.data_type.builtin.name}' for global variable '{self.identifier}'\n"
                f"  This may indicate a compiler bug or unsupported type"
            )
            raise CompileError(msg)

        root.add_scoped(self.identifier, self.data_type, is_const=self.is_const)


class Identifier:
    def __init__(self, label: str):
        self.label: str = label

    def __eq__(self, other: object) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if self is other:
            return True
        if isinstance(other, Identifier):
            return self.label == other.label
        if isinstance(other, str):
            return self.label == other
        return NotImplemented

    def __str__(self):
        return self.label

    def __hash__(self):
        return hash(self.label)


class ControlKeyword(Enum):
    BREAK = "break"
    CASE = "control"
    DEFAULT = "default"
    DO = "do"
    ELSE = "else"
    SWITCH = "switch"
    WHILE = "while"
    FOR = "for"
    IF = "if"
    RETURN = "return"


class Operator(Enum):
    ADDITION = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULUS = "%"
    NOT = "!"
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    AND = "&&"
    OR = "||"
    BITWISE_AND = "&"
    BITWISE_OR = "|"
    BITWISE_XOR = "^"
    BITWISE_LEFT = "<<"
    BITWISE_RIGHT = ">>"
    ONES_COMPLEMENT = "~"


class OperatorMapping(NamedTuple):
    unary: list[UnaryOperatorMapping]
    binary: list[BinaryOperatorMapping]


class BinaryOperatorMapping:
    def __init__(
        self,
        instruction: NCSInstructionType,
        result: DataType,
        lhs: DataType,
        rhs: DataType,
    ):
        self.instruction: NCSInstructionType = instruction
        self.result: DataType = result
        self.lhs: DataType = lhs
        self.rhs: DataType = rhs

    def __repr__(self):
        return f"{self.__class__.__name__}(instruction={self.instruction!r}, result={self.result!r}, lhs={self.lhs!r}, rhs={self.rhs!r})"


class UnaryOperatorMapping:
    def __init__(self, instruction: NCSInstructionType, rhs: DataType):
        self.instruction: NCSInstructionType = instruction
        self.rhs: DataType = rhs


class FunctionReference(NamedTuple):
    instruction: NCSInstruction
    definition: FunctionForwardDeclaration | FunctionDefinition

    def is_prototype(self) -> bool:
        return isinstance(self.definition, FunctionForwardDeclaration)


class GetScopedResult(NamedTuple):
    is_global: bool
    datatype: DynamicDataType
    offset: int
    is_const: bool = False


class Struct:
    def __init__(self, identifier: Identifier, members: list[StructMember]):
        self.identifier: Identifier = identifier
        self.members: list[StructMember] = members
        self._cached_size: int | None = None  # Cache size for performance

    def initialize(self, ncs: NCS, root: CodeRoot):
        for member in self.members:
            member.initialize(ncs, root)

    def size(self, root: CodeRoot) -> int:
        """Calculate struct size with caching for performance."""
        if self._cached_size is None:
            self._cached_size = sum(member.size(root) for member in self.members)
        return self._cached_size

    def child_offset(self, root: CodeRoot, identifier: Identifier) -> int:
        size = 0
        for member in self.members:
            if member.identifier == identifier:
                break
            size += member.size(root)
        else:
            # Provide helpful error with available members
            available = [m.identifier.label for m in self.members]
            msg = (
                f"Unknown member '{identifier}' in struct '{self.identifier}'\n"
                f"  Available members: {', '.join(available)}"
            )
            raise CompileError(msg)
        return size

    def child_type(self, root: CodeRoot, identifier: Identifier) -> DynamicDataType:
        for member in self.members:
            if member.identifier == identifier:
                return member.datatype
        available = [m.identifier.label for m in self.members]
        msg = (
            f"Member '{identifier}' not found in struct '{self.identifier}'\n"
            f"  Available members: {', '.join(available)}"
        )
        raise CompileError(msg)


class StructMember:
    def __init__(self, datatype: DynamicDataType, identifier: Identifier):
        self.datatype: DynamicDataType = datatype
        self.identifier: Identifier = identifier

    def initialize(self, ncs: NCS, root: CodeRoot):
        if self.datatype.builtin == DataType.INT:
            ncs.add(NCSInstructionType.RSADDI, args=[])
        elif self.datatype.builtin == DataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF, args=[])
        elif self.datatype.builtin == DataType.STRING:
            ncs.add(NCSInstructionType.RSADDS, args=[])
        elif self.datatype.builtin == DataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO, args=[])
        elif self.datatype.builtin == DataType.STRUCT:
            # Use the struct type name from datatype, not the member name
            struct_type_name = self.datatype._struct
            if struct_type_name is None:
                msg = f"Struct member '{self.identifier.label}' has no struct type name"
                raise CompileError(msg)
            if struct_type_name not in root.struct_map:
                msg = f"Unknown struct type '{struct_type_name}' for member '{self.identifier.label}'"
                raise CompileError(msg)
            root.struct_map[struct_type_name].initialize(ncs, root)
        else:
            msg = (
                f"Unsupported struct member type: {self.datatype.builtin.name}\n"
                f"  Member: {self.identifier}\n"
                f"  Supported types: int, float, string, object, event, effect, location, talent, struct"
            )
            raise CompileError(msg)

    def size(self, root: CodeRoot) -> int:
        return self.datatype.size(root)


class CodeRoot:
    """Root compilation context for NSS compilation.
    
    Manages global scope, function definitions, constants, and compilation state.
    Provides symbol resolution and type checking during NSS to NCS compilation.
    
    References:
    ----------
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (TypeScript compiler architecture)
        vendor/xoreos-tools/src/nwscript/decompiler.cpp (NCS decompiler, reverse reference for compilation)
        vendor/HoloLSP/server/src/nwscript-parser.ts (NSS parser and AST generation)
        vendor/HoloLSP/server/src/nwscript-lexer.ts (NSS lexer/tokenizer)
        vendor/DeNCS/ (NCS decompiler, reverse reference for compilation)
    """
    def __init__(
        self,
        constants: list[ScriptConstant],
        functions: list[ScriptFunction],
        library_lookup: list[str] | list[Path] | list[Path | str] | str | Path | None,
        library: dict[str, bytes],
    ):
        self.objects: list[TopLevelObject] = []

        self.library: dict[str, bytes] = library
        self.functions: list[ScriptFunction] = functions
        self.constants: list[ScriptConstant] = constants
        self.library_lookup: list[Path] = []
        if library_lookup:
            if not isinstance(library_lookup, list):
                library_lookup = [library_lookup]
            normalized: list[Path] = []
            for item in library_lookup:
                path_obj = CaseAwarePath(item)
                normalized.append(path_obj)
            self.library_lookup = normalized

        self.function_map: dict[str, FunctionReference] = {}
        self._global_scope: list[ScopedValue] = []
        self.struct_map: dict[str, Struct] = {}

    def compile(self, ncs: NCS):  # noqa: A003
        # nwnnsscomp processes the includes and global variable declarations before functions regardless if they are
        # placed before or after function definitions. We will replicate this behavior.

        included: list[IncludeScript] = []
        while [obj for obj in self.objects if isinstance(obj, IncludeScript)]:
            includes: list[IncludeScript] = [obj for obj in self.objects if isinstance(obj, IncludeScript)]
            include: IncludeScript = includes.pop()
            self.objects.remove(include)
            included.append(include)
            include.compile(ncs, self)

        script_globals: list[GlobalVariableDeclaration | GlobalVariableInitialization | StructDefinition] = [
            obj
            for obj in self.objects
            if isinstance(
                obj,
                (GlobalVariableDeclaration, GlobalVariableInitialization, StructDefinition),
            )
        ]
        others: list[TopLevelObject] = [obj for obj in self.objects if obj not in included and obj not in script_globals]

        if script_globals:
            for global_def in script_globals:
                global_def.compile(ncs, self)
            ncs.add(NCSInstructionType.SAVEBP, args=[])
        entry_index: int = len(ncs.instructions)

        for obj in others:
            obj.compile(ncs, self)

        if "main" in self.function_map:
            ncs.add(NCSInstructionType.RETN, args=[], index=entry_index)
            ncs.add(
                NCSInstructionType.JSR,
                jump=self.function_map["main"][0],
                index=entry_index,
            )
        elif "StartingConditional" in self.function_map:
            ncs.add(NCSInstructionType.RETN, args=[], index=entry_index)
            ncs.add(
                NCSInstructionType.JSR,
                jump=self.function_map["StartingConditional"][0],
                index=entry_index,
            )
            ncs.add(NCSInstructionType.RSADDI, args=[], index=entry_index)
        else:
            msg = "This file has no entry point and cannot be compiled (Most likely an include file)."
            raise EntryPointError(msg)

    def compile_jsr(
        self,
        ncs: NCS,
        block: CodeBlock,
        name: str,
        *args: Expression,
    ) -> DynamicDataType:
        args_list = list(args)

        func_map: FunctionReference = self.function_map[name]
        definition: FunctionForwardDeclaration | FunctionDefinition = func_map.definition
        start_instruction: NCSInstruction = func_map.instruction

        # Reserve stack space for return value and track it in temp_stack
        return_type_size = 0
        if definition.return_type == DynamicDataType.INT:
            ncs.add(NCSInstructionType.RSADDI, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.STRING:
            ncs.add(NCSInstructionType.RSADDS, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.VECTOR:
            # Vectors are 3 floats (x, y, z components)
            # Reserve stack space for all 3 components
            ncs.add(NCSInstructionType.RSADDF, args=[])
            ncs.add(NCSInstructionType.RSADDF, args=[])
            ncs.add(NCSInstructionType.RSADDF, args=[])
            return_type_size = 12
        elif definition.return_type == DynamicDataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.TALENT:
            ncs.add(NCSInstructionType.RSADDTAL, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.EVENT:
            ncs.add(NCSInstructionType.RSADDEVT, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.LOCATION:
            ncs.add(NCSInstructionType.RSADDLOC, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.EFFECT:
            ncs.add(NCSInstructionType.RSADDEFF, args=[])
            return_type_size = 4
        elif definition.return_type == DynamicDataType.VOID:
            return_type_size = 0
        elif definition.return_type.builtin == DataType.STRUCT:
            # For struct return types, initialize the struct on the stack
            struct_name = definition.return_type._struct  # noqa: SLF001
            if struct_name is not None and struct_name in self.struct_map:
                self.struct_map[struct_name].initialize(ncs, self)
                return_type_size = definition.return_type.size(self)
            else:
                msg = "Unknown struct type for return value"
                raise CompileError(msg)
        else:
            msg = f"Trying to return unsupported type '{definition.return_type.builtin.name}'"
            raise CompileError(msg)
        
        # Track return value space in temp_stack
        block.temp_stack += return_type_size

        required_params = [param for param in definition.parameters if param.default is None]

        # Make sure the minimal number of arguments were passed through
        if len(required_params) > len(args_list):
            required_names = [p.identifier.label for p in required_params]
            msg = (
                f"Missing required parameters in call to '{name}'\n"
                f"  Required: {', '.join(required_names)}\n"
                f"  Provided {len(args_list)} of {len(definition.parameters)} parameters"
            )
            raise CompileError(msg)

        # If some optional parameters were not specified, add the defaults to the arguments list
        while len(definition.parameters) > len(args_list):
            param_index = len(args_list)
            default_expr = definition.parameters[param_index].default
            if default_expr is None:
                # Should not happen as required_params already checked, but be safe
                msg = f"Missing default value for parameter {param_index} in '{name}'"
                raise CompileError(msg)
            args_list.append(default_expr)

        offset = 0
        for param, arg in zip(definition.parameters, args_list):
            temp_stack_before = block.temp_stack
            arg_datatype: DynamicDataType = arg.compile(ncs, self, block)
            temp_stack_after = block.temp_stack
            offset += arg_datatype.size(self)
            # Only add to temp_stack if the argument's compile method didn't already add it
            # (FunctionCallExpression and EngineCallExpression already add their return values)
            if temp_stack_after == temp_stack_before:
                block.temp_stack += arg_datatype.size(self)
            if param.data_type != arg_datatype:
                msg = (
                    f"Parameter type mismatch in call to '{definition.identifier}'\n"
                    f"  Parameter '{param.identifier}' expects: {param.data_type.builtin.name}\n"
                    f"  Got: {arg_datatype.builtin.name}"
                )
                raise CompileError(msg)
        # JSR consumes all arguments, so subtract their total size
        block.temp_stack -= offset
        ncs.add(NCSInstructionType.JSR, jump=start_instruction)

        return definition.return_type

    def add_scoped(self, identifier: Identifier, datatype: DynamicDataType, is_const: bool = False):
        self._global_scope.insert(0, ScopedValue(identifier, datatype, is_const))

    def get_scoped(self, identifier: Identifier, root: CodeRoot) -> GetScopedResult:
        offset = 0
        for scoped in self._global_scope:
            offset -= scoped.data_type.size(root)
            if scoped.identifier == identifier:
                break
        else:
            # Provide helpful error with available globals
            available = [s.identifier.label for s in self._global_scope[:10]]  # Show first 10
            more = len(self._global_scope) - 10
            more_text = f" (and {more} more)" if more > 0 else ""
            msg = (
                f"Undefined variable '{identifier}'\n"
                f"  Available globals: {', '.join(available)}{more_text}"
            )
            raise CompileError(msg)
        return GetScopedResult(is_global=True, datatype=scoped.data_type, offset=offset, is_const=scoped.is_const)

    def scope_size(self):
        return 0 - sum(scoped.data_type.size(self) for scoped in self._global_scope)


class CodeBlock:
    def __init__(self):
        self.scope: list[ScopedValue] = []
        self._parent: CodeBlock | None = None
        self._statements: list[Statement] = []
        self._break_scope: bool = False
        self.temp_stack: int = 0

    def add(self, statement: Statement):
        self._statements.append(statement)

    def compile(  # noqa: A003
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock | None,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        self._parent = block
        # Reset temp_stack at the start of block compilation
        # Each block tracks its own temporary stack independently
        self.temp_stack = 0

        for statement in self._statements:
            if not isinstance(statement, ReturnStatement):
                statement.compile(
                    ncs,
                    root,
                    self,
                    return_instruction,
                    break_instruction,
                    continue_instruction,
                )
            else:
                scope_size = self.full_scope_size(root)

                return_type: DynamicDataType = statement.compile(
                    ncs,
                    root,
                    self,
                    return_instruction,
                    break_instruction=None,
                    continue_instruction=None,
                )
                if return_type != DynamicDataType.VOID:
                    ncs.add(
                        NCSInstructionType.CPDOWNSP,
                        args=[-scope_size - return_type.size(root) * 2, 4],
                    )
                    ncs.add(NCSInstructionType.MOVSP, args=[-return_type.size(root)])

                ncs.add(NCSInstructionType.MOVSP, args=[-scope_size])
                ncs.add(NCSInstructionType.JMP, jump=return_instruction)
                return
        ncs.instructions.append(
            NCSInstruction(NCSInstructionType.MOVSP, [-self.scope_size(root)]),
        )

        if self.temp_stack != 0:
            # If the temp stack is 0 after the whole block has compiled there must be a logic error
            # in the implementation of one of the expression/statement classes
            msg = (
                f"Internal compiler error: Temporary stack not cleared after block compilation\n"
                f"  Temp stack size: {self.temp_stack}\n"
                f"  This indicates a bug in one of the expression/statement compile methods"
            )
            raise ValueError(msg)

    def add_scoped(self, identifier: Identifier, data_type: DynamicDataType, is_const: bool = False):
        self.scope.insert(0, ScopedValue(identifier, data_type, is_const))

    def get_scoped(
        self,
        identifier: Identifier,
        root: CodeRoot,
        offset: int | None = None,
    ) -> GetScopedResult:
        offset = -self.temp_stack if offset is None else offset - self.temp_stack
        for scoped in self.scope:
            offset -= scoped.data_type.size(root)
            if scoped.identifier == identifier:
                break
        else:
            if self._parent is not None:
                return self._parent.get_scoped(identifier, root, offset)
            return root.get_scoped(identifier, root)
        return GetScopedResult(is_global=False, datatype=scoped.data_type, offset=offset, is_const=scoped.is_const)

    def scope_size(self, root: CodeRoot) -> int:
        """Returns size of local scope."""
        return sum(scoped.data_type.size(root) for scoped in self.scope)

    def full_scope_size(self, root: CodeRoot) -> int:
        """Returns size of scope, including outer blocks."""
        size = 0
        size += self.scope_size(root)
        if self._parent is not None:
            size += self._parent.full_scope_size(root)
        return size

    def break_scope_size(self, root: CodeRoot) -> int:
        """Returns size of scope up to the nearest loop/switch statement."""
        size = 0
        size += self.scope_size(root)
        if self._parent is not None and not self._parent._break_scope:  # noqa: SLF001
            size += self._parent.break_scope_size(root)
        return size

    def mark_break_scope(self):
        self._break_scope = True


class ScopedValue:
    def __init__(self, identifier: Identifier, data_type: DynamicDataType, is_const: bool = False):
        self.identifier: Identifier = identifier
        self.data_type: DynamicDataType = data_type
        self.is_const: bool = is_const


class FunctionForwardDeclaration(TopLevelObject):
    def __init__(
        self,
        return_type: DynamicDataType,
        identifier: Identifier,
        parameters: list[FunctionDefinitionParam],
    ):
        self.return_type: DynamicDataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: list[FunctionDefinitionParam] = parameters

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        function_name = self.identifier.label

        if self.identifier.label in root.function_map:
            msg = f"Function '{function_name}' already has a prototype or been defined."
            raise CompileError(msg)

        root.function_map[self.identifier.label] = FunctionReference(
            ncs.add(NCSInstructionType.NOP, args=[]),
            self,
        )


class FunctionDefinition(TopLevelObject):
    """Represents a function definition with implementation.

    Contains the function signature (return type, parameters) and the code block
    that implements the function body.

    Note: Signature and block are currently coupled in this class. Future refactoring
    could split these into separate FunctionSignature and CodeBlock for better reusability.
    """

    def __init__(
        self,
        return_type: DynamicDataType,
        identifier: Identifier,
        parameters: list[FunctionDefinitionParam],
        block: CodeBlock,
        line_num: int,
    ):
        self.return_type: DynamicDataType = return_type
        self.identifier: Identifier = identifier
        self.parameters: list[FunctionDefinitionParam] = parameters
        self.block: CodeBlock = block
        self.line_num: int = line_num

        for param in parameters:
            block.add_scoped(param.identifier, param.data_type)

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        name = self.identifier.label

        # Make sure all default parameters appear after the required parameters
        previous_is_default = False
        for param in self.parameters:
            is_default = param.default is not None
            if previous_is_default and not is_default:
                msg = "Function parameter without a default value can't follow one with a default value."
                raise CompileError(msg)
            previous_is_default = is_default

        # Make sure params are all constant values
        for param in self.parameters:
            if isinstance(param.default, IdentifierExpression) and not param.default.is_constant(root):
                msg = f"Non-constant default value specified for function prototype parameter '{param.identifier}'."
                raise CompileError(msg)

        if name in root.function_map and not root.function_map[name].is_prototype():
            msg = (
                f"Function '{name}' is already defined\n"
                f"  Cannot redefine a function that already has an implementation"
            )
            raise CompileError(msg)
        if name in root.function_map and root.function_map[name].is_prototype():
            self._compile_function(root, name, ncs)
        else:
            retn = NCSInstruction(NCSInstructionType.RETN)

            function_start = ncs.add(NCSInstructionType.NOP, args=[])
            self.block.compile(ncs, root, None, retn, None, None)
            ncs.instructions.append(retn)

            root.function_map[name] = FunctionReference(function_start, self)

    def _compile_function(self, root: CodeRoot, name: str, ncs: NCS):  # noqa: D417
        if not self.is_matching_signature(root.function_map[name].definition):
            prototype = root.function_map[name].definition
            # Build detailed error message
            details = []
            if self.return_type != prototype.return_type:
                details.append(
                    f"Return type mismatch: prototype has {prototype.return_type.builtin.name}, "
                    f"definition has {self.return_type.builtin.name}"
                )
            if len(self.parameters) != len(prototype.parameters):
                details.append(
                    f"Parameter count mismatch: prototype has {len(prototype.parameters)}, "
                    f"definition has {len(self.parameters)}"
                )
            else:
                for i, (def_param, proto_param) in enumerate(zip(self.parameters, prototype.parameters)):
                    if def_param.data_type != proto_param.data_type:
                        details.append(
                            f"Parameter {i+1} type mismatch: prototype has {proto_param.data_type.builtin.name}, "
                            f"definition has {def_param.data_type.builtin.name}"
                        )

            msg = (
                f"Function '{name}' definition does not match its prototype\n"
                f"  " + "\n  ".join(details)
            )
            raise CompileError(msg)

        # Function has forward declaration, insert the compiled definition after the stub
        temp = NCS()
        retn = NCSInstruction(NCSInstructionType.RETN)
        self.block.compile(temp, root, None, retn, None, None)
        temp.instructions.append(retn)

        stub_index: int = ncs.instructions.index(root.function_map[name].instruction)
        ncs.instructions[stub_index + 1 : stub_index + 1] = temp.instructions

    def is_matching_signature(self, prototype: FunctionForwardDeclaration | FunctionDefinition) -> bool:
        if self.return_type != prototype.return_type:
            return False
        if len(self.parameters) != len(prototype.parameters):
            return False
        return all(
            these_parameters.data_type == prototype.parameters[i].data_type
            for i, these_parameters in enumerate(self.parameters)
        )


class FunctionDefinitionParam:
    def __init__(
        self,
        data_type: DynamicDataType,
        identifier: Identifier,
        default: Expression | None = None,
    ):
        self.data_type: DynamicDataType = data_type
        self.identifier: Identifier = identifier
        self.default: Expression | None = default


class IncludeScript(TopLevelObject):
    def __init__(
        self,
        file: StringExpression,
        library: dict[str, bytes] | None = None,
    ):
        self.file: StringExpression = file
        self.library: dict[str, bytes] = {} if library is None else library

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        from pykotor.resource.formats.ncs.compiler.parser import NssParser  # noqa: PLC0415

        lookup_paths = cast(
            "list[str] | None",
            [str(path) for path in root.library_lookup] if root.library_lookup else None,
        )

        nss_parser = NssParser(
            root.functions,
            root.constants,
            root.library,
            lookup_paths,
        )
        nss_parser.library = self.library
        nss_parser.constants = root.constants
        source: str = self._get_script(root)
        t: CodeRoot = nss_parser.parser.parse(source, tracking=True)
        root.objects = t.objects + root.objects

    def _get_script(self, root: CodeRoot) -> str:
        """Load included script from filesystem or library.

        Args:
        ----
            root: Code root containing library lookup paths

        Returns:
        -------
            str: Source code of the included script

        Raises:
        ------
            MissingIncludeError: If included file cannot be found
        """
        # Try to find in filesystem first
        for folder in root.library_lookup:
            filepath: Path = folder / f"{self.file.value}.nss"
            if filepath.is_file():
                try:
                    source_bytes = filepath.read_bytes()
                    source = source_bytes.decode(errors="ignore")
                    break
                except Exception as e:
                    msg = f"Failed to read include file '{filepath}': {e}"
                    raise MissingIncludeError(msg) from e
        else:
            # Not found in filesystem, try library
            case_sensitive: bool = not root.library_lookup or all(
                lookup_path
                for lookup_path in root.library_lookup
                if isinstance(lookup_path, Path)
            )
            include_filename: str = self.file.value if case_sensitive else self.file.value.lower()
            if include_filename in self.library:
                source = self.library[include_filename].decode(errors="ignore")
            else:
                # Build helpful error message with search paths
                search_paths = [str(folder) for folder in root.library_lookup]
                msg = (
                    f"Could not find included script '{include_filename}.nss'\n"
                    f"  Searched in {len(search_paths)} path(s): {', '.join(search_paths[:3])}"
                    f"{'...' if len(search_paths) > 3 else ''}\n"
                    f"  Also checked {len(self.library)} library file(s)"
                )
                raise MissingIncludeError(msg)
        return source


class StructDefinition(TopLevelObject):
    def __init__(self, identifier: Identifier, members: list[StructMember]):
        self.identifier: Identifier = identifier
        self.members: list[StructMember] = members

    def compile(self, ncs: NCS, root: CodeRoot):  # noqa: A003
        if len(self.members) == 0:
            msg = (
                f"Struct '{self.identifier}' cannot be empty\n"
                f"  Structs must have at least one member"
            )
            raise CompileError(msg)
        root.struct_map[self.identifier.label] = Struct(self.identifier, self.members)


class Expression(ABC):
    """Abstract base class for NSS expressions.
    
    Expressions compile to NCS bytecode instructions that evaluate to values.
    All expression types (literals, operators, function calls, etc.) inherit from this.
    
    References:
    ----------
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (Expression compilation)
        vendor/HoloLSP/server/src/nwscript-ast.ts (Expression AST nodes)
    """
    @abstractmethod
    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
    ) -> DynamicDataType: ...


class Statement(ABC):
    """Abstract base class for NSS statements.
    
    Statements compile to NCS bytecode instructions that perform actions (control flow,
    assignments, declarations, etc.). All statement types inherit from this.
    
    References:
    ----------
        vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts (Statement compilation)
        vendor/HoloLSP/server/src/nwscript-ast.ts (Statement AST nodes)
    """
    def __init__(self):
        self.line_num: None = None

    @abstractmethod
    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> object: ...


class FieldAccess:
    def __init__(self, identifiers: list[Identifier]):
        super().__init__()
        self.identifiers: list[Identifier] = identifiers

    def get_scoped(self, block: CodeBlock, root: CodeRoot) -> GetScopedResult:
        """Get scoped variable information for field access.

        Args:
        ----
            block: Current code block
            root: Code root context

        Returns:
        -------
            GetScopedResult: Variable scope information

        Raises:
        ------
            CompileError: If field access is invalid
        """
        if len(self.identifiers) == 0:
            msg = "Internal error: FieldAccess has no identifiers"
            raise CompileError(msg)

        first_ident: Identifier = self.identifiers[0]
        scoped: GetScopedResult = block.get_scoped(first_ident, root)

        is_global: bool = scoped.is_global
        offset: int = scoped.offset
        datatype: DynamicDataType = scoped.datatype
        is_const: bool = scoped.is_const  # Get is_const from the first call

        for next_ident in self.identifiers[1:]:
            # Check previous datatype to see what members are accessible
            if datatype.builtin == DataType.VECTOR:
                datatype = DynamicDataType.FLOAT
                if next_ident.label == "x":
                    offset += 0
                elif next_ident.label == "y":
                    offset += 4
                elif next_ident.label == "z":
                    offset += 8
                else:
                    msg = f"Attempting to access unknown member '{next_ident}' on datatype '{datatype}'."
                    raise CompileError(msg)
            elif datatype.builtin == DataType.STRUCT:
                assert datatype._struct is not None, "datatype._struct cannot be None in FieldAccess.get_scoped()"  # noqa: SLF001
                offset += root.struct_map[datatype._struct].child_offset(  # noqa: SLF001
                    root,
                    next_ident,
                )
                datatype = root.struct_map[datatype._struct].child_type(  # noqa: SLF001
                    root,
                    next_ident,
                )
            else:
                msg = f"Attempting to access unknown member '{next_ident}' on datatype '{datatype}'."
                raise CompileError(msg)
        
        return GetScopedResult(is_global, datatype, offset, is_const)

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        is_global, variable_type, stack_index, _is_const = self.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        return variable_type


# region Expressions: Simple
class IdentifierExpression(Expression):
    def __init__(self, value: Identifier):
        super().__init__()
        self.identifier: Identifier = value

    def __eq__(self, other: IdentifierExpression | object) -> bool:
        if self is other:
            return True
        if isinstance(other, IdentifierExpression):
            return self.identifier == other.identifier
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.identifier)

    def __repr__(self) -> str:
        return f"IdentifierExpression(identifier={self.identifier})"

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        # Scan for any constants that are stored as part of the compiler (from nwscript).
        constant: ScriptConstant | None = self.get_constant(root)
        if constant is not None:
            if constant.datatype == DataType.INT:
                ncs.add(NCSInstructionType.CONSTI, args=[int(constant.value)])
            elif constant.datatype == DataType.FLOAT:
                ncs.add(NCSInstructionType.CONSTF, args=[float(constant.value)])
            elif constant.datatype == DataType.STRING:
                ncs.add(NCSInstructionType.CONSTS, args=[str(constant.value)])
            return DynamicDataType(constant.datatype)

        is_global, datatype, stack_index, _is_const = block.get_scoped(self.identifier, root)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, datatype.size(root)])
        return datatype

    def get_constant(self, root: CodeRoot) -> ScriptConstant | None:
        return next(
            (constant for constant in root.constants if constant.name == self.identifier.label),
            None,
        )

    def is_constant(self, root: CodeRoot) -> bool:
        return self.get_constant(root) is not None


class FieldAccessExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        super().__init__()
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        scoped = self.field_access.get_scoped(block, root)
        instruction_type = NCSInstructionType.CPTOPBP if scoped.is_global else NCSInstructionType.CPTOPSP
        ncs.instructions.append(
            NCSInstruction(
                instruction_type,
                [scoped.offset, scoped.datatype.size(root)],
            ),
        )
        return scoped.datatype


class StringExpression(Expression):
    def __init__(self, value: str):
        super().__init__()
        self.value: str = value

    def __eq__(self, other: StringExpression | object):
        if self is other:
            return True
        if isinstance(other, StringExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"StringExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.STRING

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTS, [self.value]))
        return DynamicDataType.STRING


class IntExpression(Expression):
    def __init__(self, value: int):
        super().__init__()
        self.value: int = value

    def __eq__(self, other: IntExpression | object):
        if self is other:
            return True
        if isinstance(other, IntExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"IntExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.INT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTI, [self.value]))
        # Note: Caller is responsible for updating temp_stack
        return DynamicDataType.INT


class ObjectExpression(Expression):
    def __init__(self, value: int):
        super().__init__()
        self.value: int = value

    def __eq__(self, other: ObjectExpression | object):
        if self is other:
            return True
        if isinstance(other, ObjectExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"ObjectExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.OBJECT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTO, [self.value]))
        return DynamicDataType.OBJECT


class FloatExpression(Expression):
    def __init__(self, value: float):
        super().__init__()
        self.value: float = value

    def __eq__(self, other: FloatExpression | object):
        if self is other:
            return True
        if isinstance(other, FloatExpression):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"FloatExpression(value={self.value})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.FLOAT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        ncs.instructions.append(NCSInstruction(NCSInstructionType.CONSTF, [self.value]))
        return DynamicDataType.FLOAT


class VectorExpression(Expression):
    def __init__(self, x: FloatExpression, y: FloatExpression, z: FloatExpression):
        super().__init__()
        self.x: FloatExpression = x
        self.y: FloatExpression = y
        self.z: FloatExpression = z

    def __eq__(self, other: VectorExpression | object):
        if self is other:
            return True
        if isinstance(other, VectorExpression):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.x) ^ hash(self.y) ^ hash(self.z)

    def __repr__(self) -> str:
        return f"VectorExpression(x={self.x}, y={self.y}, z={self.z})"

    def data_type(self) -> DynamicDataType:
        return DynamicDataType.FLOAT

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        self.x.compile(ncs, root, block)
        self.y.compile(ncs, root, block)
        self.z.compile(ncs, root, block)
        return DynamicDataType.VECTOR


class EngineCallExpression(Expression):
    def __init__(
        self,
        function: ScriptFunction,
        routine_id: int,
        data_type: DynamicDataType,
        args: list[Expression],
    ):
        super().__init__()
        self._function: ScriptFunction = function
        self._routine_id: int = routine_id
        self._args: list[Expression] = args

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
    ) -> DynamicDataType:  # noqa: A003
        arg_count = len(self._args)

        if arg_count > len(self._function.params):
            msg = (
                f"Too many arguments for '{self._function.name}'\n"
                f"  Expected: {len(self._function.params)}, Got: {arg_count}"
            )
            raise CompileError(msg)

        for i, param in enumerate(self._function.params):
            if i >= arg_count:
                if param.default is None:
                    required_params = [p.name for p in self._function.params if p.default is None]
                    msg = (
                        f"Missing required arguments for '{self._function.name}'\n"
                        f"  Required parameters: {', '.join(required_params)}\n"
                        f"  Provided: {arg_count} argument(s)"
                    )
                    raise CompileError(msg)
                constant: ScriptConstant | None = next(
                    (constant for constant in root.constants if constant.name == param.default),
                    None,
                )
                if constant is None:
                    if param.datatype == DataType.INT:
                        self._args.append(IntExpression(int(param.default)))
                    elif param.datatype == DataType.FLOAT:
                        self._args.append(FloatExpression(float(param.default)))
                    elif param.datatype == DataType.STRING:
                        self._args.append(StringExpression(param.default))
                    elif param.datatype == DataType.VECTOR:
                        x = FloatExpression(param.default.x)
                        y = FloatExpression(param.default.y)
                        z = FloatExpression(param.default.z)
                        self._args.append(VectorExpression(x, y, z))
                    elif param.datatype == DataType.OBJECT:
                        self._args.append(ObjectExpression(int(param.default)))
                    else:
                        msg = (
                            f"Unsupported default parameter type '{param.datatype.name}' for '{param.name}' in '{self._function.name}'\n"
                            f"  This may indicate a compiler limitation"
                        )
                        raise CompileError(msg)

                elif constant.datatype == DataType.INT:
                    self._args.append(IntExpression(int(constant.value)))
                elif constant.datatype == DataType.FLOAT:
                    self._args.append(FloatExpression(float(constant.value)))
                elif constant.datatype == DataType.STRING:
                    self._args.append(StringExpression(str(constant.value)))
                elif constant.datatype == DataType.OBJECT:
                    self._args.append(ObjectExpression(int(constant.value)))
        this_stack = 0
        # DEBUG: Log arguments before compilation
        
        # Compile arguments in FORWARD order (left to right, first argument first)
        # NCS bytecode pushes arguments left-to-right, so when the interpreter
        # pops them (last-in-first-out), args_snap has them in reverse order.
        # The interpreter then reverses args_snap to match function.params order.
        # - Compile in forward: push fFloat (first param, bottom), push nWidth, push nDecimals (last param, top)
        # - Stack: [fFloat, nWidth, nDecimals] (nDecimals on top)
        # - Interpreter pops: nDecimals -> args_snap[0], nWidth -> args_snap[1], fFloat -> args_snap[2]
        # - Before reverse: args_snap = [nDecimals, nWidth, fFloat]
        # - After reverse: args_snap = [fFloat, nWidth, nDecimals] - CORRECT!
        for i in range(len(self._args)):  # Iterate in forward order
            arg = self._args[i]
            param_index = i  # Parameter index in forward order
            param_type = DynamicDataType(self._function.params[param_index].datatype)
            if param_type == DataType.ACTION:
                after_command = NCSInstruction()
                ncs.add(
                    NCSInstructionType.STORE_STATE,
                    args=[-root.scope_size(), block.full_scope_size(root)],
                )
                ncs.add(NCSInstructionType.JMP, jump=after_command)
                arg.compile(ncs, root, block)
                ncs.add(NCSInstructionType.RETN)

                ncs.instructions.append(after_command)
            else:
                temp_stack_before_arg = block.temp_stack
                added = arg.compile(ncs, root, block)
                # Only add to temp_stack if the expression didn't already add it
                # (nested EngineCallExpression/FunctionCallExpression already add their return values)
                if block.temp_stack == temp_stack_before_arg:
                    block.temp_stack += added.size(root)
                this_stack += added.size(root)

                if added != param_type:
                    param = self._function.params[param_index]
                    # Get type names safely
                    if isinstance(param_type, DataType):
                        param_type_name = param_type.name
                    else:
                        param_type_name = str(param_type)
                    msg = (
                        f"Type mismatch for parameter '{param.name}' in call to '{self._function.name}'\n"
                        f"  Expected: {param_type_name.lower()}\n"
                        f"  Got: {added.builtin.name.lower()}"
                    )
                    raise CompileError(msg)

        ncs.instructions.append(
            NCSInstruction(
                NCSInstructionType.ACTION,
                [self._routine_id, len(self._args)],
            ),
        )
        # ACTION consumes all arguments, so subtract their total size
        block.temp_stack -= this_stack
        # For non-void functions, the return value is left on the stack
        # Add it to temp_stack so ExpressionStatement knows to pop it
        return_type = DynamicDataType(self._function.returntype)
        if return_type != DynamicDataType.VOID:
            block.temp_stack += return_type.size(root)
        return return_type


class FunctionCallExpression(Expression):
    def __init__(self, function: Identifier, args: list[Expression]):
        super().__init__()
        self._function: Identifier = function
        self._args: list[Expression] = args

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        if self._function.label not in root.function_map:
            # Provide helpful error with similar function names
            available_funcs = list(root.function_map.keys())[:10]
            msg = (
                f"Undefined function '{self._function.label}'\n"
                f"  Available functions: {', '.join(available_funcs)}"
                f"{'...' if len(root.function_map) > 10 else ''}"
            )
            raise CompileError(msg)

        # compile_jsr handles return value space reservation and temp_stack tracking
        # After JSR, the return value is on the stack and tracked in temp_stack
        return root.compile_jsr(ncs, block, self._function.label, *self._args)


# endregion


class BinaryOperatorExpression(Expression):
    def __init__(
        self,
        expression1: Expression,
        expression2: Expression,
        mapping: list[BinaryOperatorMapping],
    ):
        self.expression1: Expression = expression1
        self.expression2: Expression = expression2
        self.compatibility: list[BinaryOperatorMapping] = mapping

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        temp_stack_before_expr1 = block.temp_stack
        type1 = self.expression1.compile(ncs, root, block)
        type1_size = type1.size(root)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr1:
            block.temp_stack += type1_size
        temp_stack_before_expr2 = block.temp_stack
        type2 = self.expression2.compile(ncs, root, block)
        type2_size = type2.size(root)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr2:
            block.temp_stack += type2_size

        for x in self.compatibility:
            if type1 == x.lhs and type2 == x.rhs:
                ncs.add(x.instruction)
                break
        else:
            # Build helpful error showing what operations are supported
            supported = [f"{m.lhs.name.lower()} {m.instruction.name} {m.rhs.name.lower()}"
                        for m in self.compatibility[:3]]
            msg = (
                f"Incompatible types for binary operation: {type1.builtin.name.lower()} and {type2.builtin.name.lower()}\n"
                f"  Supported combinations: {', '.join(supported)}"
                f"{'...' if len(self.compatibility) > 3 else ''}"
            )
            raise CompileError(msg)

        result_type = DynamicDataType(x.result)
        result_size = result_type.size(root)
        # Binary operation consumed both operands and left result on stack
        block.temp_stack -= (type1_size + type2_size - result_size)
        return result_type


class TernaryConditionalExpression(Expression):
    def __init__(self, condition: Expression, true_expr: Expression, false_expr: Expression):
        super().__init__()
        self.condition: Expression = condition
        self.true_expr: Expression = true_expr
        self.false_expr: Expression = false_expr

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Save initial stack state
        initial_stack = block.temp_stack
        
        # Compile condition (leaves value on stack)
        condition_type = self.condition.compile(ncs, root, block)
        if condition_type != DynamicDataType.INT:
            msg = (
                f"Ternary condition must be integer type, got {condition_type.builtin.name}\n"
                f"  Note: Conditions must evaluate to int (0 = false, non-zero = true)"
            )
            raise CompileError(msg)

        # Jump to false branch if condition is zero (JZ consumes the condition from stack)
        false_label = NCSInstruction(NCSInstructionType.NOP, args=[])
        ncs.add(NCSInstructionType.JZ, jump=false_label)
        # JZ consumed the condition, so update stack tracking
        block.temp_stack = initial_stack

        # Compile true expression
        true_type = self.true_expr.compile(ncs, root, block)
        block.temp_stack += true_type.size(root)

        # Jump to end after true expression
        end_label = NCSInstruction(NCSInstructionType.NOP, args=[])
        ncs.add(NCSInstructionType.JMP, jump=end_label)

        # False branch
        # Stack state: same as after condition (condition was popped by JZ)
        ncs.instructions.append(false_label)
        # Reset temp_stack to state after condition was popped
        block.temp_stack = initial_stack
        false_type = self.false_expr.compile(ncs, root, block)
        # Explicitly track that false branch result is on the stack
        block.temp_stack += false_type.size(root)
        
        # Type check - both branches must have same type
        if true_type != false_type:
            msg = (
                f"Type mismatch in ternary operator\n"
                f"  True branch type: {true_type.builtin.name}\n"
                f"  False branch type: {false_type.builtin.name}\n"
                f"  Both branches must have the same type"
            )
            raise CompileError(msg)
        
        # False branch leaves result on stack at same position as true branch
        # Both branches: initial_stack + result_size (already set above)

        # End label
        ncs.instructions.append(end_label)
        # At end, stack has result from one branch at position initial_stack + result_size
        block.temp_stack = initial_stack + true_type.size(root)

        return true_type


class UnaryOperatorExpression(Expression):
    def __init__(self, expression1: Expression, mapping: list[UnaryOperatorMapping]):
        super().__init__()
        self.expression1: Expression = expression1
        self.compatibility: list[UnaryOperatorMapping] = mapping

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:  # noqa: A003
        type1 = self.expression1.compile(ncs, root, block)

        block.temp_stack += 4

        for x in self.compatibility:
            if type1 == x.rhs:
                ncs.add(x.instruction)
                break
        else:
            supported_types = [m.rhs.name.lower() for m in self.compatibility]
            msg = (
                f"Incompatible type for unary operation: {type1.builtin.name.lower()}\n"
                f"  Supported types: {', '.join(supported_types)}"
            )
            raise CompileError(msg)

        block.temp_stack -= 4
        return type1


class LogicalNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.temp_stack += 4

        if type1 == DynamicDataType.INT:
            ncs.add(NCSInstructionType.NOTI)
        else:
            msg = (
                f"Logical NOT requires integer operand, got {type1.builtin.name.lower()}\n"
                f"  Note: In NWScript, only int types can be used in logical operations"
            )
            raise CompileError(msg)

        block.temp_stack -= 4
        return DynamicDataType.INT


class BitwiseNotExpression(Expression):
    def __init__(self, expression1: Expression):
        super().__init__()
        self.expression1: Expression = expression1

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        type1 = self.expression1.compile(ncs, root, block)
        block.temp_stack += 4

        if type1 == DynamicDataType.INT:
            ncs.add(NCSInstructionType.COMPI)
        else:
            msg = (
                f"Bitwise NOT (~) requires integer operand, got {type1.builtin.name.lower()}\n"
                f"  Note: Bitwise operations only work on int types"
            )
            raise CompileError(msg)

        block.temp_stack -= 4
        return type1


# region Expressions: Assignment
class Assignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock, allow_const: bool = False) -> DynamicDataType:
        # Save temp_stack before compiling expression to check if expression already added to it
        temp_stack_before = block.temp_stack
        # Compile expression - expressions may or may not add to temp_stack themselves
        variable_type = self.expression.compile(ncs, root, block)
        temp_stack_after = block.temp_stack
        
        # Only add to temp_stack if the expression didn't already add it
        # (FunctionCallExpression and EngineCallExpression already add their return values)
        if temp_stack_after == temp_stack_before:
            # Expression didn't add to temp_stack, so we need to add it
            block.temp_stack += variable_type.size(root)
        
        # Get variable location - get_scoped uses temp_stack (including expression result) in its calculation
        is_global, expression_type, stack_index, is_const = self.field_access.get_scoped(
            block,
            root,
        )
        
        if is_const and not allow_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        
        instruction_type = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # get_scoped() already accounts for temp_stack (which includes the expression result),
        # so stack_index points to the correct variable location

        if variable_type != expression_type:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in assignment to '{var_name}'\n"
                f"  Variable type: {expression_type.builtin.name}\n"
                f"  Expression type: {variable_type.builtin.name}"
            )
            raise CompileError(msg)

        # Copy the value that the expression has already been placed on the stack to where the identifiers position is
        ncs.instructions.append(
            NCSInstruction(instruction_type, [stack_index, expression_type.size(root)]),
        )

        # Don't remove the expression result from the stack - leave it for ExpressionStatement to clean up
        # This matches the behavior of other assignment operations (+=, -=, etc.)
        # The result is copied to the variable location but remains on top of stack
        # ExpressionStatement will remove it based on temp_stack tracking

        return variable_type


class AdditionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
    ) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index, is_const = self.field_access.get_scoped(
            block,
            root,
        )
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expresion_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        # (FunctionCallExpression and EngineCallExpression already add their return values)
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.ADDII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.ADDIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.ADDFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.ADDFI
        elif variable_type == DynamicDataType.STRING and expresion_type == DynamicDataType.STRING:
            arthimetic_instruction = NCSInstructionType.ADDSS
        elif variable_type == DynamicDataType.VECTOR and expresion_type == DynamicDataType.VECTOR:
            arthimetic_instruction = NCSInstructionType.ADDVV
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in += operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int+=int, float+=float/int, string+=string, vector+=vector"
            )
            raise CompileError(msg)

        # Add the expression and our temp variable copy together
        ncs.add(arthimetic_instruction, args=[])

        # Copy the result to the original variable in the stack
        # The arithmetic operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if is_global else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Arithmetic operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack (copied to variable location but also remains on top for ExpressionStatement)
        # temp_stack currently = variable_size + expression_size
        # After operation: stack has 1 result of variable_type size
        # Net change: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expresion_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class SubtractionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expresion_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        # (FunctionCallExpression and EngineCallExpression already add their return values)
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.SUBII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.SUBIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.SUBFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.SUBFI
        elif variable_type == DynamicDataType.VECTOR and expresion_type == DynamicDataType.VECTOR:
            arthimetic_instruction = NCSInstructionType.SUBVV
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in -= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int-=int, float-=float/int, vector-=vector"
            )
            raise CompileError(msg)

        # Subtract the expression from our temp variable copy
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        # The arithmetic operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if isglobal else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Arithmetic operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack (copied to variable location but also remains on top for ExpressionStatement)
        # temp_stack currently = variable_size + expression_size
        # After operation: stack has 1 result of variable_type size
        # Net change: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expresion_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class MultiplicationAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expresion_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.MULII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.MULIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.MULFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.MULFI
        elif variable_type == DynamicDataType.VECTOR and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.MULVF
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in *= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int*=int, float*=float/int, vector*=float"
            )
            raise CompileError(msg)

        # Multiply the temp variable copy by the expression
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        # The arithmetic operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if isglobal else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Arithmetic operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack (copied to variable location but also remains on top for ExpressionStatement)
        # temp_stack currently = variable_size + expression_size
        # After operation: stack has 1 result of variable_type size
        # Net change: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expresion_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class DivisionAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expresion_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.DIVII
        elif variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.DIVIF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.DIVFF
        elif variable_type == DynamicDataType.FLOAT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.DIVFI
        elif variable_type == DynamicDataType.VECTOR and expresion_type == DynamicDataType.FLOAT:
            arthimetic_instruction = NCSInstructionType.DIVVF
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in /= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int/=int, float/=float/int, vector/=float"
            )
            raise CompileError(msg)

        # Divide the temp variable copy by the expression
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        # The arithmetic operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if isglobal else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Arithmetic operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack (copied to variable location but also remains on top for ExpressionStatement)
        # temp_stack currently = variable_size + expression_size
        # After operation: stack has 1 result of variable_type size
        # Net change: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expresion_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class ModuloAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if isglobal else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expresion_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expresion_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expresion_type == DynamicDataType.INT:
            arthimetic_instruction = NCSInstructionType.MODII
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in %= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expresion_type.builtin.name}\n"
                f"  Supported: int%=int"
            )
            raise CompileError(msg)

        # Apply modulo operation
        ncs.add(arthimetic_instruction)

        # Copy the result to the original variable in the stack
        # The arithmetic operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if isglobal else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if isglobal else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Arithmetic operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack (copied to variable location but also remains on top for ExpressionStatement)
        # temp_stack currently = variable_size + expression_size
        # After operation: stack has 1 result of variable_type size
        # Net change: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expresion_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class BitwiseAndAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expression_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expression_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expression_type == DynamicDataType.INT:
            bitwise_instruction = NCSInstructionType.BOOLANDII
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in &= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expression_type.builtin.name}\n"
                f"  Supported: int&=int"
            )
            raise CompileError(msg)

        # Apply the bitwise AND operation
        ncs.add(bitwise_instruction, args=[])

        # Copy the result to the original variable in the stack
        # The bitwise operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if is_global else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Bitwise operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack, temp_stack: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expression_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class BitwiseOrAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expression_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expression_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expression_type == DynamicDataType.INT:
            bitwise_instruction = NCSInstructionType.INCORII
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in |= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expression_type.builtin.name}\n"
                f"  Supported: int|=int"
            )
            raise CompileError(msg)

        # Apply the bitwise OR operation
        ncs.add(bitwise_instruction, args=[])

        # Copy the result to the original variable in the stack
        # The bitwise operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if is_global else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Bitwise operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack, temp_stack: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expression_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class BitwiseXorAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expression_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expression_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expression_type == DynamicDataType.INT:
            bitwise_instruction = NCSInstructionType.EXCORII
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in ^= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expression_type.builtin.name}\n"
                f"  Supported: int^=int"
            )
            raise CompileError(msg)

        # Apply the bitwise XOR operation
        ncs.add(bitwise_instruction, args=[])

        # Copy the result to the original variable in the stack
        # The bitwise operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if is_global else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Bitwise operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack, temp_stack: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expression_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class BitwiseLeftAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expression_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expression_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expression_type == DynamicDataType.INT:
            bitwise_instruction = NCSInstructionType.SHLEFTII
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in <<= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expression_type.builtin.name}\n"
                f"  Supported: int<<=int"
            )
            raise CompileError(msg)

        # Apply the bitwise left shift operation
        ncs.add(bitwise_instruction, args=[])

        # Copy the result to the original variable in the stack
        # The bitwise operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if is_global else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Bitwise operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack, temp_stack: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expression_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class BitwiseRightAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expression_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expression_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expression_type == DynamicDataType.INT:
            bitwise_instruction = NCSInstructionType.SHRIGHTII
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in >>= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expression_type.builtin.name}\n"
                f"  Supported: int>>=int"
            )
            raise CompileError(msg)

        # Apply the bitwise right shift operation
        ncs.add(bitwise_instruction, args=[])

        # Copy the result to the original variable in the stack
        # The bitwise operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if is_global else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Bitwise operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack, temp_stack: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expression_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


class BitwiseUnsignedRightAssignment(Expression):
    def __init__(self, field_access: FieldAccess, value: Expression):
        super().__init__()
        self.field_access: FieldAccess = field_access
        self.expression: Expression = value

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        # Copy the variable to the top of the stack
        is_global, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot assign to const variable '{var_name}'"
            raise CompileError(msg)
        instruction_type = NCSInstructionType.CPTOPBP if is_global else NCSInstructionType.CPTOPSP
        ncs.add(instruction_type, args=[stack_index, variable_type.size(root)])
        block.temp_stack += variable_type.size(root)

        # Add the result of the expression to the stack
        temp_stack_before_expr = block.temp_stack
        expression_type = self.expression.compile(ncs, root, block)
        # Only add to temp_stack if the expression didn't already add it
        if block.temp_stack == temp_stack_before_expr:
            block.temp_stack += expression_type.size(root)

        # Determine what instruction to apply to the two values
        if variable_type == DynamicDataType.INT and expression_type == DynamicDataType.INT:
            bitwise_instruction = NCSInstructionType.USHRIGHTII
        else:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Type mismatch in >>>= operation on '{var_name}'\n"
                f"  Variable type: {variable_type.builtin.name}\n"
                f"  Expression type: {expression_type.builtin.name}\n"
                f"  Supported: int>>>=int"
            )
            raise CompileError(msg)

        # Apply the unsigned bitwise right shift operation
        ncs.add(bitwise_instruction, args=[])

        # Copy the result to the original variable in the stack
        # The bitwise operation consumed both operands and left the result on stack
        # After CPDOWNSP, the result is still on stack (for ExpressionStatement to clean up)
        ins_cpdown = NCSInstructionType.CPDOWNBP if is_global else NCSInstructionType.CPDOWNSP
        # Result (variable_type size) is on stack; offset to original variable accounts for this
        offset_cpdown = stack_index if is_global else stack_index - variable_type.size(root)
        ncs.add(ins_cpdown, args=[offset_cpdown, variable_type.size(root)])

        # Bitwise operation consumed variable copy and expression (2 values), left result (1 value)
        # Result is still on stack, temp_stack: both operands consumed, result pushed
        block.temp_stack = block.temp_stack - variable_type.size(root) - expression_type.size(root) + variable_type.size(root)
        # Return variable_type (the result type) so ExpressionStatement knows what size to clean up
        return variable_type


# endregion


# region Statements
class EmptyStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> DynamicDataType:
        return DynamicDataType.VOID


class NopStatement(Statement):
    def __init__(self, string: str):
        super().__init__()
        self.string = string

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> DynamicDataType:
        ncs.add(NCSInstructionType.NOP, args=[self.string])
        return DynamicDataType.VOID


class ExpressionStatement(Statement):
    def __init__(self, expression: Expression):
        super().__init__()
        self.expression: Expression = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        temp_stack_before = block.temp_stack
        expression_type = self.expression.compile(ncs, root, block)
        temp_stack_after = block.temp_stack
        # Expression compiled, remove its result from stack and temp_stack tracking
        # Note: Some expressions (like Assignment) already remove their result from the stack,
        # so we only need to remove it from temp_stack if it's still on the stack.
        # We check temp_stack to see if the result is still tracked.
        # For void expressions, we still need to check if temp_stack increased (e.g., from nested function calls)
        if expression_type != DynamicDataType.VOID:
            expression_size = expression_type.size(root)
            # Check if expression added to temp_stack
            if temp_stack_after > temp_stack_before:
                # Expression added to temp_stack, so result is on the stack - remove it
                ncs.add(NCSInstructionType.MOVSP, args=[-expression_size])
                block.temp_stack -= expression_size
            elif temp_stack_after == temp_stack_before:
                # Expression didn't add to temp_stack, but result is still on the stack (e.g., StringExpression, IntExpression)
                # We need to remove it from the stack (but don't update temp_stack since it wasn't tracking it)
                ncs.add(NCSInstructionType.MOVSP, args=[-expression_size])
            else:
                # temp_stack decreased, which means the expression already removed its result
                pass
        else:
            # Void expression - check if temp_stack increased (shouldn't happen, but clean up if it did)
            if temp_stack_after > temp_stack_before:
                # Something was left on the stack (e.g., from nested function call arguments)
                cleanup_size = temp_stack_after - temp_stack_before
                ncs.add(NCSInstructionType.MOVSP, args=[-cleanup_size])
                block.temp_stack -= cleanup_size
            # else: no cleanup needed - void expression with balanced stack


class DeclarationStatement(Statement):
    def __init__(
        self,
        data_type: DynamicDataType,
        declarators: list[VariableDeclarator],
        is_const: bool = False,
    ):
        super().__init__()
        self.data_type: DynamicDataType = data_type
        self.declarators: list[VariableDeclarator] = declarators
        self.is_const: bool = is_const

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        for declarator in self.declarators:
            declarator.compile(ncs, root, block, self.data_type, self.is_const)


class VariableDeclarator:
    def __init__(self, identifier: Identifier):
        self.identifier: Identifier = identifier

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        data_type: DynamicDataType,
        is_const: bool = False,
    ):
        if data_type.builtin == DataType.INT:
            ncs.add(NCSInstructionType.RSADDI)
        elif data_type.builtin == DataType.FLOAT:
            ncs.add(NCSInstructionType.RSADDF)
        elif data_type.builtin == DataType.STRING:
            ncs.add(NCSInstructionType.RSADDS)
        elif data_type.builtin == DataType.OBJECT:
            ncs.add(NCSInstructionType.RSADDO)
        elif data_type.builtin == DataType.EVENT:
            ncs.add(NCSInstructionType.RSADDEVT)
        elif data_type.builtin == DataType.LOCATION:
            ncs.add(NCSInstructionType.RSADDLOC)
        elif data_type.builtin == DataType.TALENT:
            ncs.add(NCSInstructionType.RSADDTAL)
        elif data_type.builtin == DataType.EFFECT:
            ncs.add(NCSInstructionType.RSADDEFF)
        elif data_type.builtin == DataType.VECTOR:
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
            ncs.add(NCSInstructionType.RSADDF)
        elif data_type.builtin == DataType.STRUCT:
            struct_name = data_type._struct  # noqa: SLF001
            if struct_name is not None and struct_name in root.struct_map:
                root.struct_map[struct_name].initialize(ncs, root)
            else:
                msg = f"Unknown struct type for variable '{self.identifier}'"
                raise CompileError(msg)
        elif data_type.builtin == DataType.VOID:
            msg = (
                f"Cannot declare variable '{self.identifier}' with void type\n"
                f"  void can only be used as a function return type"
            )
            raise CompileError(msg)
        else:
            msg = (
                f"Unsupported type '{data_type.builtin.name}' for variable '{self.identifier}'\n"
                f"  Supported types: int, float, string, object, vector, effect, event, location, talent, struct"
            )
            raise CompileError(msg)

        block.add_scoped(self.identifier, data_type, is_const)


class VariableInitializer:
    def __init__(self, identifier: Identifier, expression: Expression):
        self.identifier: Identifier = identifier
        self.expression: Expression = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        data_type: DynamicDataType,
        is_const: bool = False,
    ):
        initial_temp_stack = block.temp_stack

        # Reuse existing declarator logic for allocation
        declarator = VariableDeclarator(self.identifier)
        declarator.compile(ncs, root, block, data_type, is_const)

        # Emit assignment using existing machinery (keeps stack bookkeeping consistent)
        # Allow const variables to be initialized (but not reassigned)
        assignment = Assignment(FieldAccess([self.identifier]), self.expression)
        result_type = assignment.compile(ncs, root, block, allow_const=True)
        
        # Assignment leaves result on stack for ExpressionStatement to clean up,
        # but VariableInitializer is NOT in an ExpressionStatement, so we need to clean it up ourselves
        result_size = result_type.size(root)
        if block.temp_stack > initial_temp_stack:
            # Assignment left result on stack, remove it
            ncs.add(NCSInstructionType.MOVSP, args=[-result_size])
            block.temp_stack -= result_size
        # else: no cleanup needed - assignment already handled stack


class ConditionalBlock(Statement):
    def __init__(
        self,
        if_block: ConditionAndBlock,
        else_if_blocks: list[ConditionAndBlock],
        else_block: CodeBlock,
    ):
        super().__init__()
        self.if_blocks: list[ConditionAndBlock] = [if_block, *else_if_blocks]
        self.else_block: CodeBlock | None = else_block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        jump_count: int = 1 + len(self.if_blocks)
        jump_tos: list[NCSInstruction] = [NCSInstruction(NCSInstructionType.NOP, args=[]) for _ in range(jump_count)]

        for i, else_if in enumerate(self.if_blocks):
            # Save temp_stack state before condition
            initial_temp_stack = block.temp_stack
            else_if.condition.compile(ncs, root, block)
            condition_type = DynamicDataType.INT  # Conditions are always int
            # JZ consumes the condition value from stack
            ncs.add(NCSInstructionType.JZ, jump=jump_tos[i])
            # Decrement temp_stack since JZ consumed the condition
            block.temp_stack = initial_temp_stack

            # Save temp_stack before compiling block
            block_temp_stack_before = block.temp_stack
            else_if.block.compile(
                ncs,
                root,
                block,
                return_instruction,
                break_instruction,
                continue_instruction,
            )
            # Block should clear its own temp_stack, restore parent's temp_stack
            block.temp_stack = block_temp_stack_before
            ncs.add(NCSInstructionType.JMP, jump=jump_tos[-1])

            ncs.instructions.append(jump_tos[i])

        if self.else_block is not None:
            # Save temp_stack before compiling else block
            else_temp_stack_before = block.temp_stack
            self.else_block.compile(
                ncs,
                root,
                block,
                return_instruction,
                break_instruction,
                continue_instruction,
            )
            # Else block should clear its own temp_stack, restore parent's temp_stack
            block.temp_stack = else_temp_stack_before

        ncs.instructions.append(jump_tos[-1])


class ConditionAndBlock:
    def __init__(self, condition: Expression, block: CodeBlock):
        self.condition: Expression = condition
        self.block: CodeBlock = block


class ReturnStatement(Statement):
    def __init__(self, expression: Expression | None = None):
        super().__init__()
        self.expression: Expression | None = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ) -> DynamicDataType:
        if self.expression is not None:
            return self.expression.compile(ncs, root, block)
        return DynamicDataType.VOID


class WhileLoopBlock(Statement):
    def __init__(self, condition: Expression, block: CodeBlock):
        super().__init__()
        self.condition: Expression = condition
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])
        
        # Save temp_stack before condition (condition pushes a value, JZ consumes it)
        initial_temp_stack = block.temp_stack
        condition_type = self.condition.compile(ncs, root, block)

        if condition_type != DynamicDataType.INT:
            msg = (
                f"Loop condition must be integer type, got {condition_type.builtin.name.lower()}\n"
                f"  Note: Conditions must evaluate to int (0 = false, non-zero = true)"
            )
            raise CompileError(msg)

        # JZ consumes the condition value from stack
        ncs.add(NCSInstructionType.JZ, jump=loopend)
        # Restore temp_stack since JZ consumed the condition
        block.temp_stack = initial_temp_stack
        
        self.block.compile(ncs, root, block, return_instruction, loopend, loopstart)
        ncs.add(NCSInstructionType.JMP, jump=loopstart)

        ncs.instructions.append(loopend)


class DoWhileLoopBlock(Statement):
    def __init__(self, condition: Expression, block: CodeBlock):
        super().__init__()
        self.condition: Expression = condition
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        conditionstart = NCSInstruction(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])

        self.block.compile(
            ncs,
            root,
            block,
            return_instruction,
            loopend,
            conditionstart,
        )

        ncs.instructions.append(conditionstart)
        
        # Save temp_stack before condition (condition pushes a value, JZ consumes it)
        initial_temp_stack = block.temp_stack
        condition_type = self.condition.compile(ncs, root, block)
        if condition_type != DynamicDataType.INT:
            msg = (
                f"do-while condition must be integer type, got {condition_type.builtin.name.lower()}\n"
                f"  Note: Conditions must evaluate to int (0 = false, non-zero = true)"
            )
            raise CompileError(msg)

        # JZ consumes the condition value from stack
        ncs.add(NCSInstructionType.JZ, jump=loopend)
        # Restore temp_stack since JZ consumed the condition
        block.temp_stack = initial_temp_stack
        
        ncs.add(NCSInstructionType.JMP, jump=loopstart)
        ncs.instructions.append(loopend)


class ForLoopBlock(Statement):
    def __init__(
        self,
        initial: Expression | Statement | None,
        condition: Expression,
        iteration: Expression,
        block: CodeBlock,
    ):
        super().__init__()
        self.initial: Expression | Statement | None = initial
        self.condition: Expression = condition
        self.iteration: Expression = iteration
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        # Tell break/continue statements to stop here when getting scope size
        block.mark_break_scope()

        if self.initial is not None:
            if isinstance(self.initial, Statement):
                # For declaration statements, compile them directly
                self.initial.compile(ncs, root, block, return_instruction, break_instruction, continue_instruction)
            else:
                # For expressions, compile and clean up stack
                temp_stack_before = block.temp_stack
                initial_type = self.initial.compile(ncs, root, block)
                # Check if expression added to temp_stack
                if block.temp_stack == temp_stack_before:
                    # Expression didn't add to temp_stack, so we need to add it
                    block.temp_stack += initial_type.size(root)
                # Clean up the result from stack
                ncs.add(NCSInstructionType.MOVSP, args=[-initial_type.size(root)])
                block.temp_stack -= initial_type.size(root)

        loopstart = ncs.add(NCSInstructionType.NOP, args=[])
        updatestart = NCSInstruction(NCSInstructionType.NOP, args=[])
        loopend = NCSInstruction(NCSInstructionType.NOP, args=[])

        # Save temp_stack before condition (condition pushes a value, JZ consumes it)
        initial_temp_stack = block.temp_stack
        condition_type = self.condition.compile(ncs, root, block)
        if condition_type != DynamicDataType.INT:
            msg = (
                f"for loop condition must be integer type, got {condition_type.builtin.name.lower()}\n"
                f"  Note: Conditions must evaluate to int (0 = false, non-zero = true)"
            )
            raise CompileError(msg)

        # JZ consumes the condition value from stack
        ncs.add(NCSInstructionType.JZ, jump=loopend)
        # Restore temp_stack since JZ consumed the condition
        block.temp_stack = initial_temp_stack
        
        self.block.compile(ncs, root, block, return_instruction, loopend, updatestart)

        ncs.instructions.append(updatestart)
        temp_stack_before_iteration = block.temp_stack
        iteration_type = self.iteration.compile(ncs, root, block)
        temp_stack_after_iteration = block.temp_stack
        # Check if expression already added to temp_stack
        if temp_stack_after_iteration == temp_stack_before_iteration:
            # Expression didn't add to temp_stack, so we need to add it
            block.temp_stack += iteration_type.size(root)
        ncs.add(NCSInstructionType.MOVSP, args=[-iteration_type.size(root)])
        block.temp_stack -= iteration_type.size(root)

        ncs.add(NCSInstructionType.JMP, jump=loopstart)
        ncs.instructions.append(loopend)


class ScopedBlock(Statement):
    def __init__(self, block: CodeBlock):
        super().__init__()
        self.block: CodeBlock = block

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        self.block.compile(
            ncs,
            root,
            block,
            return_instruction,
            break_instruction,
            continue_instruction,
        )


# endregion


class BreakStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        if break_instruction is None:
            msg = (
                "break statement not inside loop or switch\n"
                "  break can only be used inside while, do-while, for, or switch statements"
            )
            raise CompileError(msg)
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size(root)])
        ncs.add(NCSInstructionType.JMP, jump=break_instruction)


class ContinueStatement(Statement):
    def __init__(self):
        super().__init__()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        if continue_instruction is None:
            msg = (
                "continue statement not inside loop\n"
                "  continue can only be used inside while, do-while, or for loops"
            )
            raise CompileError(msg)
        ncs.add(NCSInstructionType.MOVSP, args=[-block.break_scope_size(root)])
        ncs.add(NCSInstructionType.JMP, jump=continue_instruction)


class PrefixIncrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Increment operator (++) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot increment const variable '{var_name}'"
            raise CompileError(msg)
        ncs.add(NCSInstructionType.INCxSP, args=[-4])

        if isglobal:
            ncs.add(
                NCSInstructionType.CPDOWNBP,
                args=[stack_index, variable_type.size(root)],
            )
        else:
            ncs.add(
                NCSInstructionType.CPDOWNSP,
                args=[stack_index - variable_type.size(root), variable_type.size(root)],
            )

        return variable_type


class PostfixIncrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)
        block.temp_stack += 4

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Increment operator (++) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot increment const variable '{var_name}'"
            raise CompileError(msg)
        if isglobal:
            ncs.add(NCSInstructionType.INCxBP, args=[stack_index])
        else:
            ncs.add(NCSInstructionType.INCxSP, args=[stack_index])

        block.temp_stack -= 4
        return variable_type


class PrefixDecrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Decrement operator (--) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot decrement const variable '{var_name}'"
            raise CompileError(msg)
        ncs.add(NCSInstructionType.DECxSP, args=[-4])

        if isglobal:
            ncs.add(
                NCSInstructionType.CPDOWNBP,
                args=[stack_index, variable_type.size(root)],
            )
        else:
            ncs.add(
                NCSInstructionType.CPDOWNSP,
                args=[stack_index - variable_type.size(root), variable_type.size(root)],
            )

        return variable_type


class PostfixDecrementExpression(Expression):
    def __init__(self, field_access: FieldAccess):
        self.field_access: FieldAccess = field_access

    def compile(self, ncs: NCS, root: CodeRoot, block: CodeBlock) -> DynamicDataType:
        variable_type = self.field_access.compile(ncs, root, block)
        block.temp_stack += 4

        if variable_type != DynamicDataType.INT:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = (
                f"Decrement operator (--) requires integer variable, got {variable_type.builtin.name.lower()}\n"
                f"  Variable: {var_name}"
            )
            raise CompileError(msg)

        isglobal, variable_type, stack_index, is_const = self.field_access.get_scoped(block, root)
        if is_const:
            var_name = ".".join(str(ident) for ident in self.field_access.identifiers)
            msg = f"Cannot decrement const variable '{var_name}'"
            raise CompileError(msg)
        if isglobal:
            ncs.add(NCSInstructionType.DECxBP, args=[stack_index])
        else:
            ncs.add(NCSInstructionType.DECxSP, args=[stack_index])

        block.temp_stack -= 4
        return variable_type


# region Switch
class SwitchStatement(Statement):
    def __init__(self, expression: Expression, blocks: list[SwitchBlock]):
        super().__init__()
        self.expression: Expression = expression
        self.blocks: list[SwitchBlock] = blocks

        self.real_block: CodeBlock = CodeBlock()

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        return_instruction: NCSInstruction,
        break_instruction: NCSInstruction | None,
        continue_instruction: NCSInstruction | None,
    ):
        self.real_block._parent = block  # noqa: SLF001
        block.mark_break_scope()

        block = self.real_block

        expression_type = self.expression.compile(ncs, root, block)
        block.temp_stack += expression_type.size(root)

        end_of_switch = NCSInstruction(NCSInstructionType.NOP, args=[])

        tempncs = NCS()
        switchblock_to_instruction = {}
        for switchblock in self.blocks:
            switchblock_start = tempncs.add(NCSInstructionType.NOP, args=[])
            switchblock_to_instruction[switchblock] = switchblock_start
            for statement in switchblock.block:
                statement.compile(
                    tempncs,
                    root,
                    block,
                    return_instruction,
                    end_of_switch,
                    None,
                )

        for switchblock in self.blocks:
            for label in switchblock.labels:
                # Do not want to run switch expression multiple times, execute it once and copy it to the top
                ncs.add(
                    NCSInstructionType.CPTOPSP,
                    args=[-expression_type.size(root), expression_type.size(root)],
                )
                label.compile(
                    ncs,
                    root,
                    block,
                    switchblock_to_instruction[switchblock],
                    expression_type,
                )
        # If none of the labels match, jump over the code block
        ncs.add(NCSInstructionType.JMP, jump=end_of_switch)

        ncs.merge(tempncs)
        ncs.instructions.append(end_of_switch)

        # Pop the Switch expression
        ncs.add(NCSInstructionType.MOVSP, args=[-4])
        block.temp_stack -= expression_type.size(root)


class SwitchBlock:
    def __init__(self, labels: list[SwitchLabel], block: list[Statement]):
        self.labels: list[SwitchLabel] = labels
        self.block: list[Statement] = block


class SwitchLabel(ABC):
    @abstractmethod
    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        jump_to: NCSInstruction,
        expression_type: DynamicDataType,
    ): ...


class ExpressionSwitchLabel:
    def __init__(self, expression: Expression):
        self.expression: Expression = expression

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        jump_to: NCSInstruction,
        expression_type: DynamicDataType,
    ):
        # Compare the copied Switch expression to the Label expression
        label_type = self.expression.compile(ncs, root, block)
        equality_instruction = get_logical_equality_instruction(
            expression_type,
            label_type,
        )
        ncs.add(equality_instruction, args=[])

        # If the expressions match, then we jump to the appropriate place, otherwise continue trying the
        # other Labels
        ncs.add(NCSInstructionType.JNZ, jump=jump_to)


class DefaultSwitchLabel:
    def __init__(self): ...

    def compile(
        self,
        ncs: NCS,
        root: CodeRoot,
        block: CodeBlock,
        jump_to: NCSInstruction,
        expression_type: DynamicDataType,
    ):
        ncs.add(NCSInstructionType.JMP, jump=jump_to)


# endregion


class DynamicDataType:
    INT: DynamicDataType
    STRING: DynamicDataType
    FLOAT: DynamicDataType
    OBJECT: DynamicDataType
    VECTOR: DynamicDataType
    EVENT: DynamicDataType
    TALENT: DynamicDataType
    LOCATION: DynamicDataType
    EFFECT: DynamicDataType
    VOID: DynamicDataType

    def __init__(self, datatype: DataType, struct_name: str | None = None):
        self.builtin: DataType = datatype
        self._struct: str | None = struct_name

    def __eq__(self, other: DynamicDataType | DataType | object) -> bool:
        if self is other:
            return True
        if isinstance(other, DynamicDataType):
            if self.builtin == other.builtin:
                return self.builtin != DataType.STRUCT or (self.builtin == DataType.STRUCT and self._struct == other._struct)
            return False
        if isinstance(other, DataType):
            return self.builtin == other and self.builtin != DataType.STRUCT
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.builtin) ^ hash(self._struct)

    def __repr__(self) -> str:
        return f"DynamicDataType(builtin={self.builtin}({self.builtin.name.lower()}), struct={self._struct})"

    def size(self, root: CodeRoot) -> int:
        if self.builtin == DataType.STRUCT:
            if self._struct is None:
                raise CompileError("Struct type has no name")  # noqa: B904
            return root.struct_map[self._struct].size(root)
        return self.builtin.size()


DynamicDataType.INT = DynamicDataType(DataType.INT)
DynamicDataType.STRING = DynamicDataType(DataType.STRING)
DynamicDataType.FLOAT = DynamicDataType(DataType.FLOAT)
DynamicDataType.OBJECT = DynamicDataType(DataType.OBJECT)
DynamicDataType.VECTOR = DynamicDataType(DataType.VECTOR)
DynamicDataType.VOID = DynamicDataType(DataType.VOID)
DynamicDataType.EVENT = DynamicDataType(DataType.EVENT)
DynamicDataType.TALENT = DynamicDataType(DataType.TALENT)
DynamicDataType.LOCATION = DynamicDataType(DataType.LOCATION)
DynamicDataType.EFFECT = DynamicDataType(DataType.EFFECT)
