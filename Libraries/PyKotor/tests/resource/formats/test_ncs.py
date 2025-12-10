from __future__ import annotations

import errno
import os
import pathlib
import sys
import tempfile
import textwrap
import traceback
import unittest
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import pytest

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[6].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path) -> None:
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from utility.common.geometry import Vector3
from pykotor.common.misc import Game
from pykotor.common.script import DataType
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs import NCS, NCSBinaryReader, NCSInstructionType
from pykotor.resource.formats.ncs.compiler.classes import CompileError
from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter, Stack
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.ncs_auto import (
    bytes_ncs,
    compile_nss,
    decompile_ncs,
    read_ncs,
    write_ncs,
)
from pykotor.resource.formats.ncs.optimizers import RemoveNopOptimizer

if TYPE_CHECKING:
    from pykotor.common.script import ScriptConstant, ScriptFunction
    KOTOR_CONSTANTS: list[ScriptConstant] = []
    KOTOR_FUNCTIONS: list[ScriptFunction] = []
    TSL_CONSTANTS: list[ScriptConstant] = []
    TSL_FUNCTIONS: list[ScriptFunction] = []
else:
    from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_CONSTANTS, TSL_FUNCTIONS

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

BINARY_TEST_FILE = str(THIS_SCRIPT_PATH.parent.parent.parent / "files" / "test.ncs")
EXPECTED_INSTRUCTION_COUNT = 1541


# ============================================================================
# Test Base Classes
# ============================================================================

class CompilerTestBase(unittest.TestCase):
    """Base class for compiler tests with shared compilation helper."""

    def compile(
        self,
        script: str,
        library: dict[str, bytes] | None = None,
        library_lookup: Sequence[str | Path] | None = None,
    ) -> NCS:
        """Compile NSS script to NCS bytecode."""
        if library is None:
            library = {}
        # Normalize library_lookup to list[str] | list[Path] | None for NssParser
        normalized_lookup: Sequence[str | Path] | None = None
        if library_lookup is not None:
            if isinstance(library_lookup, (str, Path)):
                normalized_lookup = [library_lookup]
            elif isinstance(library_lookup, list) and library_lookup:
                # Check if all items are the same type
                first_item = library_lookup[0]
                if isinstance(first_item, str):
                    normalized_lookup = [str(item) if isinstance(item, Path) else item for item in library_lookup]  # type: ignore[list-item]
                else:
                    normalized_lookup = library_lookup  # type: ignore[assignment]
        nssLexer = NssLexer()
        nssParser = NssParser(
            functions=KOTOR_FUNCTIONS,
            constants=KOTOR_CONSTANTS,
            library=library,
            library_lookup=normalized_lookup,
        )

        parser = nssParser.parser
        t = parser.parse(script, tracking=True)

        ncs = NCS()
        t.compile(ncs)
        return ncs


# ============================================================================
# Binary I/O Tests
# ============================================================================

class TestNCSBinaryIO(unittest.TestCase):
    """Tests for binary NCS file I/O operations."""

    def test_binary_io(self):
        """Ensure binary NCS IO produces byte-identical output."""
        ncs = NCSBinaryReader(BINARY_TEST_FILE).load()
        self.validate_io(ncs)

        user_profile_path = os.environ.get("USERPROFILE")
        file_path = Path(user_profile_path or "", "Documents", "ext", "output.ncs")

        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        write_ncs(ncs, file_path)
        data = bytes_ncs(ncs)
        ncs = read_ncs(data)
        self.validate_io(ncs)

    def validate_io(self, ncs: NCS) -> None:
        """Validate NCS structure and byte content."""
        self.assertEqual(EXPECTED_INSTRUCTION_COUNT, len(ncs.instructions))
        self.assertEqual(BinaryReader.load_file(BINARY_TEST_FILE), bytes_ncs(ncs))


# ============================================================================
# Compiler Tests
# ============================================================================

class TestNCSCompiler(CompilerTestBase):
    """Tests for NSS to NCS compilation."""

    # region Engine Call Tests
    def test_enginecall(self):
        """Test basic engine function call."""
        ncs = self.compile(
            """
            void main()
            {
                object oExisting = GetExitingObject();
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].function_name == "GetExitingObject"
        assert interpreter.action_snapshots[0].arg_values == []

    def test_enginecall_return_value(self):
        """Test engine function call with return value."""
        ncs = self.compile(
            """
            void main()
            {
                int inescapable = GetAreaUnescapable();
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("GetAreaUnescapable", lambda: 10)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 10

    def test_enginecall_with_params(self):
        """Test engine function call with parameters."""
        ncs = self.compile(
            """
            void main()
            {
                string tag = "something";
                int n = 15;
                object oSomething = GetObjectByTag(tag, n);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].function_name == "GetObjectByTag"
        assert interpreter.action_snapshots[0].arg_values == ["something", 15]

    def test_enginecall_with_default_params(self):
        """Test engine function call with default parameters."""
        ncs = self.compile(
            """
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag(tag);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_enginecall_with_missing_params(self):
        """Test engine function call with missing required parameters."""
        script = """
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag();
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_enginecall_with_too_many_params(self):
        """Test engine function call with too many parameters."""
        script = """
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag("", 0, "shouldnotbehere");
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_enginecall_delay_command_1(self):
        """Test DelayCommand with nested function call."""
        ncs = self.compile(
            """
            void main()
            {
                object oFirstPlayer = GetFirstPC();
                DelayCommand(1.0, GiveXPToCreature(oFirstPlayer, 9001));
            }
        """
        )

    def test_enginecall_GetFirstObjectInShape_defaults(self):
        """Test GetFirstObjectInShape with default parameters."""
        ncs = self.compile(
            """
            void main()
            {
                int nShape = SHAPE_CUBE;
                float fSize = 0.0;
                location lTarget;
                GetFirstObjectInShape(nShape, fSize, lTarget);
            }
        """
        )

    def test_enginecall_GetFactionEqual(self):
        """Test GetFactionEqual with default parameters."""
        ncs = self.compile(
            """
            void main()
            {
                object oFirst;
                GetFactionEqual(oFirst);
            }
        """
        )

    # endregion

    # region Arithmetic Operator Tests
    def test_addop_int_int(self):
        """Test integer addition."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 10 + 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 15

    def test_addop_float_float(self):
        """Test float addition."""
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0 + 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 15.0

    def test_addop_string_string(self):
        """Test string concatenation."""
        ncs = self.compile(
            """
            void main()
            {
                string value = "abc" + "def";
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == "abcdef"

    def test_subop_int_int(self):
        """Test integer subtraction."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 10 - 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 5

    def test_subop_float_float(self):
        """Test float subtraction."""
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0 - 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 5.0

    def test_mulop_int_int(self):
        """Test integer multiplication."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 * 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 50

    def test_mulop_float_float(self):
        """Test float multiplication."""
        ncs = self.compile(
            """
            void main()
            {
                float a = 10.0 * 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 50.0

    def test_divop_int_int(self):
        """Test integer division."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 / 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 2

    def test_divop_float_float(self):
        """Test float division."""
        ncs = self.compile(
            """
            void main()
            {
                float a = 10.0 / 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 2.0

    def test_modop_int_int(self):
        """Test integer modulo."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 % 3;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    def test_negop_int(self):
        """Test integer negation."""
        ncs = self.compile(
            """
            void main()
            {
                int a = -10;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == -10

    def test_negop_float(self):
        """Test float negation."""
        ncs = self.compile(
            """
            void main()
            {
                float a = -10.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == -10.0

    def test_bidmas(self):
        """Test operator precedence (BIDMAS)."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 2 + (5 * ((0)) + 5) * 3 + 2 - (2 + (2 * 4 - 12 / 2)) / 2;
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 17

    def test_op_with_variables(self):
        """Test operations with variables."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10;
                int b = 5;
                int c = a * b * a;
                int d = 10 * 5 * 10;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 500
        assert interpreter.stack_snapshots[-4].stack[-2].value == 500

    # endregion

    # region Logical Operator Tests
    def test_not_op(self):
        """Test logical NOT operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = !1;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_logical_and_op(self):
        """Test logical AND operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 0 && 0;
                int b = 1 && 0;
                int c = 1 && 1;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-3].value == 0
        assert interpreter.stack_snapshots[-4].stack[-2].value == 0
        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    def test_logical_or_op(self):
        """Test logical OR operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 0 || 0;
                int b = 1 || 0;
                int c = 1 || 1;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-3].value == 0
        assert interpreter.stack_snapshots[-4].stack[-2].value == 1
        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    def test_logical_equals(self):
        """Test equality operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1 == 1;
                int b = "a" == "b";
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-2].value == 1
        assert interpreter.stack_snapshots[-4].stack[-1].value == 0

    def test_logical_notequals_op(self):
        """Test inequality operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1 != 1;
                int b = 1 != 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-2].value == 0
        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    # endregion

    # region Relational Operator Tests
    def test_compare_greaterthan_op(self):
        """Test greater than operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 > 1;
                int b = 10 > 10;
                int c = 10 > 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_compare_greaterthanorequal_op(self):
        """Test greater than or equal operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 >= 1;
                int b = 10 >= 10;
                int c = 10 >= 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_compare_lessthan_op(self):
        """Test less than operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 < 1;
                int b = 10 < 10;
                int c = 10 < 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_compare_lessthanorequal_op(self):
        """Test less than or equal operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 <= 1;
                int b = 10 <= 10;
                int c = 10 <= 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    # endregion

    # region Bitwise Operator Tests
    def test_bitwise_or_op(self):
        """Test bitwise OR operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 5 | 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 7

    def test_bitwise_xor_op(self):
        """Test bitwise XOR operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 ^ 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 5

    def test_bitwise_not_int(self):
        """Test bitwise NOT operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = ~1;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == -2

    def test_bitwise_and_op(self):
        """Test bitwise AND operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 & 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 2

    def test_bitwise_shiftleft_op(self):
        """Test bitwise left shift operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 << 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 28

    def test_bitwise_shiftright_op(self):
        """Test bitwise right shift operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 >> 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    # endregion

    # region Assignment Tests
    def test_assignment(self):
        """Test basic assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                a = 4;

                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 4

    def test_assignment_complex(self):
        """Test complex assignment expression."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                a = a * 2 + 8;

                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 10

    def test_assignment_string_constant(self):
        """Test string constant assignment."""
        ncs = self.compile(
            """
            void main()
            {
                string a = "A";

                PrintString(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == "A"

    def test_assignment_string_enginecall(self):
        """Test string assignment from engine call."""
        ncs = self.compile(
            """
            void main()
            {
                string a = GetGlobalString("A");

                PrintString(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("GetGlobalString", lambda identifier: identifier)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == "A"

    def test_addition_assignment_int_int(self):
        """Test integer addition assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 1;
                value += 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values[0] == 3

    def test_addition_assignment_int_float(self):
        """Test integer addition assignment with float."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 1;
                value += 2.0;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values[0] == 3

    def test_addition_assignment_float_float(self):
        """Test float addition assignment."""
        ncs = self.compile(
            """
            void main()
            {
                float value = 1.0;
                value += 2.0;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 3.0

    def test_addition_assignment_float_int(self):
        """Test float addition assignment with integer."""
        ncs = self.compile(
            """
            void main()
            {
                float value = 1.0;
                value += 2;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintFloat"
        assert snap.arg_values[0] == 3.0

    def test_addition_assignment_string_string(self):
        """Test string concatenation assignment."""
        ncs = self.compile(
            """
            void main()
            {
                string value = "a";
                value += "b";

                PrintString(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintString"
        assert snap.arg_values[0] == "ab"

    def test_subtraction_assignment_int_int(self):
        """Test integer subtraction assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 10;
                value -= 2 * 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [6]

    def test_subtraction_assignment_int_float(self):
        """Test integer subtraction assignment with float."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 10;
                value -= 2.0;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values[0] == 8.0

    def test_subtraction_assignment_float_float(self):
        """Test float subtraction assignment."""
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0;
                value -= 2.0;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintFloat"
        assert snap.arg_values[0] == 8.0

    def test_subtraction_assignment_float_int(self):
        """Test float subtraction assignment with integer."""
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0;
                value -= 2;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 8.0

    def test_multiplication_assignment(self):
        """Test multiplication assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 10;
                value *= 2 * 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [40]

    def test_division_assignment(self):
        """Test division assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 12;
                value /= 2 * 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [3]

    def test_bitwise_and_assignment(self):
        """Test bitwise AND assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 0xFF;
                value &= 0x0F;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [15]  # 0xFF & 0x0F = 0x0F = 15

    def test_bitwise_or_assignment(self):
        """Test bitwise OR assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 0x0F;
                value |= 0xF0;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [255]  # 0x0F | 0xF0 = 0xFF = 255

    def test_bitwise_xor_assignment(self):
        """Test bitwise XOR assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 0xFF;
                value ^= 0x0F;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [240]  # 0xFF ^ 0x0F = 0xF0 = 240

    def test_bitwise_left_shift_assignment(self):
        """Test bitwise left shift assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 7;
                value <<= 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [28]  # 7 << 2 = 28

    def test_bitwise_right_shift_assignment(self):
        """Test bitwise right shift assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 28;
                value >>= 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [7]  # 28 >> 2 = 7

    def test_bitwise_unsigned_right_shift_assignment(self):
        """Test bitwise unsigned right shift assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 0x80000000;
                value >>>= 1;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        # 0x80000000 >>> 1 = 0x40000000 = 1073741824
        assert snap.arg_values == [1073741824]

    def test_bitwise_assignment_with_expression(self):
        """Test bitwise assignment with complex expression."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 0xFF;
                value &= 0x0F | 0x10;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [31]  # 0xFF & (0x0F | 0x10) = 0xFF & 0x1F = 0x1F = 31

    def test_global_bitwise_assignment(self):
        """Test global variable bitwise assignment."""
        ncs = self.compile(
            """
            int global1 = 0xFF;

            void main()
            {
                int local1 = 0x0F;
                global1 &= local1;

                PrintInteger(global1);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [15]  # 0xFF & 0x0F = 0x0F = 15

    def test_modulo_assignment(self):
        """Test modulo assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 17;
                value %= 5;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [2]  # 17 % 5 = 2

    def test_bitwise_unsigned_right_shift_op(self):
        """Test bitwise unsigned right shift operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 0x80000000 >>> 1;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 1073741824  # 0x40000000

    # endregion

    # region Const Keyword Tests
    def test_const_global_declaration(self):
        """Test const global variable declaration."""
        ncs = self.compile(
            """
            const int TEST_CONST = 42;

            void main()
            {
                PrintInteger(TEST_CONST);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 42

    def test_const_global_initialization(self):
        """Test const global variable initialization."""
        ncs = self.compile(
            """
            const float PI = 3.14159f;
            const string GREETING = "Hello";

            void main()
            {
                PrintFloat(PI);
                PrintString(GREETING);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert abs(interpreter.action_snapshots[-2].arg_values[0] - 3.141592) < 0.000001
        assert interpreter.action_snapshots[-1].arg_values[0] == "Hello"

    def test_const_local_declaration(self):
        """Test const local variable declaration."""
        ncs = self.compile(
            """
            void main()
            {
                const int local_const = 100;
                PrintInteger(local_const);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 100

    def test_const_local_initialization(self):
        """Test const local variable initialization with expression."""
        ncs = self.compile(
            """
            void main()
            {
                const int a = 10;
                const int b = a * 2;
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 20

    def test_const_assignment_error(self):
        """Test that assigning to const variable raises error."""
        script = """
            const int TEST_CONST = 42;

            void main()
            {
                TEST_CONST = 100;
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_const_compound_assignment_error(self):
        """Test that compound assignment to const variable raises error."""
        script = """
            const int TEST_CONST = 42;

            void main()
            {
                TEST_CONST += 10;
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_const_bitwise_assignment_error(self):
        """Test that bitwise assignment to const variable raises error."""
        script = """
            const int TEST_CONST = 0xFF;

            void main()
            {
                TEST_CONST &= 0x0F;
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_const_increment_error(self):
        """Test that incrementing const variable raises error."""
        script = """
            const int TEST_CONST = 42;

            void main()
            {
                TEST_CONST++;
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_const_multi_declaration(self):
        """Test multiple const variable declarations."""
        ncs = self.compile(
            """
            void main()
            {
                const int a = 1, b = 2, c = 3;
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 3

    # endregion

    # region Ternary Operator Tests
    def test_ternary_basic(self):
        """Test basic ternary operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1 > 0 ? 100 : 200;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 100

    def test_ternary_false_branch(self):
        """Test ternary operator false branch."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 0 > 1 ? 100 : 200;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 200

    def test_ternary_with_variables(self):
        """Test ternary operator with variables."""
        ncs = self.compile(
            """
            void main()
            {
                int b = 5;
                int c = (b > 3) ? 100 : 200;
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 100

    def test_ternary_nested(self):
        """Test nested ternary operator."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = 2;
                int result = (a > b) ? 10 : ((a < b) ? 20 : 30);
                PrintInteger(result);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 20

    def test_ternary_in_expression(self):
        """Test ternary operator in larger expression."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 5;
                int result = (a > 3 ? 10 : 5) + 20;
                PrintInteger(result);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 30

    def test_ternary_type_mismatch_error(self):
        """Test that ternary with mismatched types raises error."""
        script = """
            void main()
            {
                int result = 1 ? 100 : "string";
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_ternary_float_branches(self):
        """Test ternary operator with float branches."""
        ncs = self.compile(
            """
            void main()
            {
                float result = 1 ? 3.14f : 2.71f;
                PrintFloat(result);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 3.14

    def test_ternary_string_branches(self):
        """Test ternary operator with string branches."""
        ncs = self.compile(
            """
            void main()
            {
                string result = 1 ? "yes" : "no";
                PrintString(result);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == "yes"

    def test_ternary_with_function_calls(self):
        """Test ternary operator with function calls."""
        ncs = self.compile(
            """
            int GetValue(int x)
            {
                return x * 2;
            }

            void main()
            {
                int result = 1 ? GetValue(5) : GetValue(10);
                PrintInteger(result);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 10

    def test_ternary_assignment(self):
        """Test ternary operator result assigned to variable."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10;
                int b = 20;
                int max = (a > b) ? a : b;
                PrintInteger(max);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 20

    def test_ternary_precedence(self):
        """Test ternary operator precedence."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1 ? 2 : 3 ? 4 : 5;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        # Right-associative: 1 ? 2 : (3 ? 4 : 5) = 1 ? 2 : 4 = 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    # endregion

    # region Control Flow Tests
    def test_if(self):
        """Test if statement."""
        ncs = self.compile(
            """
            void main()
            {
                if(0)
                {
                    PrintInteger(0);
                }

                if(1)
                {
                    PrintInteger(1);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_if_multiple_conditions(self):
        """Test if statement with multiple conditions."""
        ncs = self.compile(
            """
            void main()
            {
                if(1 && 2 && 3)
                {
                    PrintInteger(0);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_if_else(self):
        """Test if-else statement."""
        ncs = self.compile(
            """
            void main()
            {
                if (0) {    PrintInteger(0); }
                else {      PrintInteger(1); }

                if (1) {    PrintInteger(2); }
                else {      PrintInteger(3); }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2

    def test_if_else_if(self):
        """Test if-else if statement."""
        ncs = self.compile(
            """
            void main()
            {
                if (0)      { PrintInteger(0); }
                else if (0) { PrintInteger(1); }

                if (1)      { PrintInteger(2); } // hit
                else if (1) { PrintInteger(3); }

                if (1)      { PrintInteger(4); } // hit
                else if (0) { PrintInteger(5); }

                if (0)      { PrintInteger(6); }
                else if (1) { PrintInteger(7); } // hit
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 2
        assert interpreter.action_snapshots[1].arg_values[0] == 4
        assert interpreter.action_snapshots[2].arg_values[0] == 7

    def test_if_else_if_else(self):
        """Test if-else if-else statement."""
        ncs = self.compile(
            """
            void main()
            {
                if (0)      { PrintInteger(0); }
                else if (0) { PrintInteger(1); }
                else        { PrintInteger(3); } // hit

                if (0)      { PrintInteger(4); }
                else if (1) { PrintInteger(5); } // hit
                else        { PrintInteger(6); }

                if (1)      { PrintInteger(7); } // hit
                else if (1) { PrintInteger(8); }
                else        { PrintInteger(9); }

                if (1)      { PrintInteger(10); } //hit
                else if (0) { PrintInteger(11); }
                else        { PrintInteger(12); }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 4
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 5
        assert interpreter.action_snapshots[2].arg_values[0] == 7
        assert interpreter.action_snapshots[3].arg_values[0] == 10

    def test_single_statement_if(self):
        """Test single statement if (no braces)."""
        ncs = self.compile(
            """
            void main()
            {
                if (1) PrintInteger(222);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 222

    def test_single_statement_else_if_else(self):
        """Test single statement else if-else."""
        ncs = self.compile(
            """
            void main()
            {
                if (0) PrintInteger(11);
                else if (0) PrintInteger(22);
                else PrintInteger(33);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 33

    def test_while_loop(self):
        """Test while loop."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value)
                {
                    PrintInteger(value);
                    value -= 1;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_while_loop_with_break(self):
        """Test while loop with break."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value)
                {
                    PrintInteger(value);
                    value -= 1;
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 3

    def test_while_loop_with_continue(self):
        """Test while loop with continue."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value)
                {
                    PrintInteger(value);
                    value -= 1;
                    continue;
                    PrintInteger(99);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_while_loop_scope(self):
        """Test while loop variable scope."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 11;
                int outer = 22;
                while (value)
                {
                    int inner = 33;
                    value = 0;
                    continue;
                    outer = 99;
                }

                PrintInteger(outer);
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 22
        assert interpreter.action_snapshots[1].arg_values[0] == 0

    def test_do_while_loop(self):
        """Test do-while loop."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                do
                {
                    PrintInteger(value);
                    value -= 1;
                } while (value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_do_while_loop_with_break(self):
        """Test do-while loop with break."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                do
                {
                    PrintInteger(value);
                    value -= 1;
                    break;
                } while (value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 3

    def test_do_while_loop_with_continue(self):
        """Test do-while loop with continue."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                do
                {
                    PrintInteger(value);
                    value -= 1;
                    continue;
                    PrintInteger(99);
                } while (value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_do_while_loop_scope(self):
        """Test do-while loop variable scope."""
        ncs = self.compile(
            """
            void main()
            {
                int outer = 11;
                int value = 22;
                do
                {
                    int inner = 33;
                    value = 0;
                } while (value);

                PrintInteger(outer);
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 11
        assert interpreter.action_snapshots[1].arg_values[0] == 0

    def test_for_loop(self):
        """Test for loop."""
        ncs = self.compile(
            """
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 3

    def test_for_loop_with_break(self):
        """Test for loop with break."""
        ncs = self.compile(
            """
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_for_loop_with_continue(self):
        """Test for loop with continue."""
        ncs = self.compile(
            """
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                    continue;
                    PrintInteger(99);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 3

    def test_for_loop_scope(self):
        """Test for loop variable scope."""
        ncs = self.compile(
            """
            void main()
            {
                int i = 11;
                int outer = 22;
                for (i = 0; i <= 5; i += 1)
                {
                    int inner = 33;
                    break;
                }

                PrintInteger(i);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_switch_no_breaks(self):
        """Test switch statement without breaks (fall-through)."""
        ncs = self.compile(
            """
            void main()
            {
                switch (2)
                {
                    case 1:
                        PrintInteger(1);
                    case 2:
                        PrintInteger(2);
                    case 3:
                        PrintInteger(3);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 2
        assert interpreter.action_snapshots[1].arg_values[0] == 3

    def test_switch_jump_over(self):
        """Test switch statement jumping over all cases."""
        ncs = self.compile(
            """
            void main()
            {
                switch (4)
                {
                    case 1:
                        PrintInteger(1);
                    case 2:
                        PrintInteger(2);
                    case 3:
                        PrintInteger(3);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 0

    def test_switch_with_breaks(self):
        """Test switch statement with breaks."""
        ncs = self.compile(
            """
            void main()
            {
                switch (3)
                {
                    case 1:
                        PrintInteger(1);
                        break;
                    case 2:
                        PrintInteger(2);
                        break;
                    case 3:
                        PrintInteger(3);
                        break;
                    case 4:
                        PrintInteger(4);
                        break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 3

    def test_switch_with_default(self):
        """Test switch statement with default case."""
        ncs = self.compile(
            """
            void main()
            {
                switch (4)
                {
                    case 1:
                        PrintInteger(1);
                        break;
                    case 2:
                        PrintInteger(2);
                        break;
                    case 3:
                        PrintInteger(3);
                        break;
                    default:
                        PrintInteger(4);
                        break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 4

    def test_switch_scoped_blocks(self):
        """Test switch statement with scoped blocks."""
        ncs = self.compile(
            """
            void main()
            {
                switch (2)
                {
                    case 1:
                    {
                        int inner = 10;
                        PrintInteger(inner);
                    }
                    break;

                    case 2:
                    {
                        int inner = 20;
                        PrintInteger(inner);
                    }
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 20

    def test_switch_scope_a(self):
        """Test switch statement scope handling."""
        ncs = self.compile(
            """
            int shape;
            int harmful;

            void main()
            {
                object oTarget = OBJECT_SELF;
                effect e1, e2;
                effect e3;

                shape = SHAPE_SPHERE;

                switch (1)
                {
                    case 1:
                        harmful = FALSE;
                        e1 = EffectMovementSpeedIncrease(99);

                        if (1 == 1)
                        {
                            e1 = EffectLinkEffects(e1, EffectVisualEffect(VFX_DUR_SPEED));
                        }

                        GiveXPToCreature(OBJECT_SELF, 100);
                        GetHasSpellEffect(FORCE_POWER_SPEED_BURST, oTarget);
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values == [8, 0]

    def test_switch_scope_b(self):
        """Test switch statement scope with function calls."""
        ncs = self.compile(
            """
            int Cort_XP(int abc)
            {
                GiveXPToCreature(GetFirstPC(), abc);
            }

            void main() {
                int abc = 2500;
                Cort_XP(abc);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    # endregion

    # region Variable and Scope Tests
    def test_scope(self):
        """Test basic variable scope."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 1;

                if (value == 1)
                {
                    value = 2;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_scoped_block(self):
        """Test scoped block."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;

                {
                    int b = 2;
                    PrintInteger(a);
                    PrintInteger(b);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    def test_multi_declarations(self):
        """Test multiple variable declarations."""
        ncs = self.compile(
            """
            void main()
            {
                int value1, value2 = 1, value3 = 2;

                PrintInteger(value1);
                PrintInteger(value2);
                PrintInteger(value3);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    def test_local_declarations(self):
        """Test local variable declarations."""
        ncs = self.compile(
            """
            void main()
            {
                int INT;
                float FLOAT;
                string STRING;
                location LOCATION;
                effect EFFECT;
                talent TALENT;
                event EVENT;
                vector VECTOR;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_global_declarations(self):
        """Test global variable declarations."""
        ncs = self.compile(
            """
            int INT;
            float FLOAT;
            string STRING;
            location LOCATION;
            effect EFFECT;
            talent TALENT;
            event EVENT;
            vector VECTOR;

            void main()
            {

            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert any(inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.SAVEBP)

    def test_global_initializations(self):
        """Test global variable initializations."""
        ncs = self.compile(
            """
            int INT = 0;
            float FLOAT = 0.0;
            string STRING = "";
            vector VECTOR = [0.0, 0.0, 0.0];

            void main()
            {
                PrintInteger(INT);
                PrintFloat(FLOAT);
                PrintString(STRING);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 0.0
        assert interpreter.action_snapshots[-1].arg_values[0] == ""
        assert any(inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.SAVEBP)

    def test_global_initialization_with_unary(self):
        """Test global variable initialization with unary operator."""
        ncs = self.compile(
            """
            int INT = -1;

            void main()
            {
                PrintInteger(INT);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == -1

    def test_global_int_addition_assignment(self):
        """Test global integer addition assignment."""
        ncs = self.compile(
            """
            int global1 = 1;
            int global2 = 2;

            void main()
            {
                int local1 = 3;
                int local2 = 4;

                global1 += local1;
                global2 = local2 + global1;

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 4
        assert interpreter.action_snapshots[-1].arg_values[0] == 8

    def test_global_int_subtraction_assignment(self):
        """Test global integer subtraction assignment."""
        ncs = self.compile(
            """
            int global1 = 1;
            int global2 = 10;

            void main()
            {
                int local1 = 100;
                int local2 = 1000;

                global1 -= local1;              // 1 - 100 = -99
                global2 = local2 - global1;     // 1000 - -99 = 1099

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == -99
        assert interpreter.action_snapshots[-1].arg_values[0] == 1099

    def test_global_int_multiplication_assignment(self):
        """Test global integer multiplication assignment."""
        ncs = self.compile(
            """
            int global1 = 1;
            int global2 = 10;

            void main()
            {
                int local1 = 100;
                int local2 = 1000;

                global1 *= local1;              // 1 * 100 = 100
                global2 = local2 * global1;     // 1000 * 100 = 100000

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 100
        assert interpreter.action_snapshots[-1].arg_values[0] == 100000

    def test_global_int_division_assignment(self):
        """Test global integer division assignment."""
        ncs = self.compile(
            """
            int global1 = 1000;
            int global2 = 100;

            void main()
            {
                int local1 = 10;
                int local2 = 1;

                global1 /= local1;              // 1000 / 10 = 100
                global2 = global1 / local2;     // 100 / 1 = 100

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 100
        assert interpreter.action_snapshots[-1].arg_values[0] == 100

    def test_declaration_int(self):
        """Test integer declaration without initialization."""
        ncs = self.compile(
            """
            void main()
            {
                int a;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_declaration_float(self):
        """Test float declaration without initialization."""
        ncs = self.compile(
            """
            void main()
            {
                float a;
                PrintFloat(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 0.0

    def test_declaration_string(self):
        """Test string declaration without initialization."""
        ncs = self.compile(
            """
            void main()
            {
                string a;
                PrintString(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == ""

    # endregion

    # region Data Type Tests
    def test_float_notations(self):
        """Test different float literal notations."""
        ncs = self.compile(
            """
            void main()
            {
                PrintFloat(1.0f);
                PrintFloat(2.0);
                PrintFloat(3f);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 3

    def test_vector(self):
        """Test vector creation and operations."""
        ncs = self.compile(
            """
            void main()
            {
                vector vec = Vector(2.0, 4.0, 4.0);
                float mag = VectorMagnitude(vec);
                PrintFloat(mag);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.set_mock("VectorMagnitude", lambda vec: vec.magnitude())
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 6.0

    def test_vector_notation(self):
        """Test vector literal notation."""
        ncs = self.compile(
            """
            void main()
            {
                vector vec = [1.0, 2.0, 3.0];
                PrintFloat(vec.x);
                PrintFloat(vec.y);
                PrintFloat(vec.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 2.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 3.0

    def test_vector_get_components(self):
        """Test vector component access."""
        ncs = self.compile(
            """
            void main()
            {
                vector vec = Vector(2.0, 4.0, 6.0);
                PrintFloat(vec.x);
                PrintFloat(vec.y);
                PrintFloat(vec.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 2.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 6.0

    def test_vector_set_components(self):
        """Test vector component assignment."""
        ncs = self.compile(
            """
            void main()
            {
                vector vec = Vector(0.0, 0.0, 0.0);
                vec.x = 2.0;
                vec.y = 4.0;
                vec.z = 6.0;
                PrintFloat(vec.x);
                PrintFloat(vec.y);
                PrintFloat(vec.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 2.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 6.0

    def test_struct_get_members(self):
        """Test struct member access."""
        ncs = self.compile(
            """
            struct ABC
            {
                int value1;
                string value2;
                float value3;
            };

            void main()
            {
                struct ABC abc;
                PrintInteger(abc.value1);
                PrintString(abc.value2);
                PrintFloat(abc.value3);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == ""
        assert interpreter.action_snapshots[-1].arg_values[0] == 0.0

    def test_struct_get_invalid_member(self):
        """Test accessing invalid struct member."""
        source = """
            struct ABC
            {
                int value1;
                string value2;
                float value3;
            };

            void main()
            {
                struct ABC abc;
                PrintFloat(abc.value4);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_struct_set_members(self):
        """Test struct member assignment."""
        ncs = self.compile(
            """
            struct ABC
            {
                int value1;
                string value2;
                float value3;
            };

            void main()
            {
                struct ABC abc;
                abc.value1 = 123;
                abc.value2 = "abc";
                abc.value3 = 3.14;
                PrintInteger(abc.value1);
                PrintString(abc.value2);
                PrintFloat(abc.value3);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 123
        assert interpreter.action_snapshots[-2].arg_values[0] == "abc"
        self.assertAlmostEqual(3.14, interpreter.action_snapshots[-1].arg_values[0])

    # endregion

    # region Increment/Decrement Tests
    def test_prefix_increment_sp_int(self):
        """Test prefix increment on stack pointer integer."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = ++a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    def test_prefix_increment_bp_int(self):
        """Test prefix increment on base pointer integer."""
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = ++a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    def test_postfix_increment_sp_int(self):
        """Test postfix increment on stack pointer integer."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = a++;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_postfix_increment_bp_int(self):
        """Test postfix increment on base pointer integer."""
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = a++;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_prefix_decrement_sp_int(self):
        """Test prefix decrement on stack pointer integer."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = --a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_prefix_decrement_bp_int(self):
        """Test prefix decrement on base pointer integer."""
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = --a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_postfix_decrement_sp_int(self):
        """Test postfix decrement on stack pointer integer."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = a--;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_postfix_decrement_bp_int(self):
        """Test postfix decrement on base pointer integer."""
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = a--;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    # endregion

    # region Function Tests
    def test_prototype_no_args(self):
        """Test function prototype with no arguments."""
        ncs = self.compile(
            """
            void test();

            void main()
            {
                test();
            }

            void test()
            {
                PrintInteger(56);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 56

    def test_prototype_with_arg(self):
        """Test function prototype with argument."""
        ncs = self.compile(
            """
            void test(int value);

            void main()
            {
                test(57);
            }

            void test(int value)
            {
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 57

    def test_prototype_with_three_args(self):
        """Test function prototype with three arguments."""
        ncs = self.compile(
            """
            void test(int a, int b, int c)
            {
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }

            void main()
            {
                int a = 1, b = 2, c = 3;
                test(a, b, c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 3

    def test_prototype_with_many_args(self):
        """Test function prototype with many arguments including defaults."""
        ncs = self.compile(
            """
            void test(int a, effect z, int b, int c, int d = 4)
            {
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
                PrintInteger(d);
            }

            void main()
            {
                int a = 1, b = 2, c = 3;
                effect z;

                test(a, z, b, c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-4].arg_values[0] == 1
        assert interpreter.action_snapshots[-3].arg_values[0] == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 3
        assert interpreter.action_snapshots[-1].arg_values[0] == 4

    def test_prototype_with_default_arg(self):
        """Test function prototype with default argument."""
        ncs = self.compile(
            """
            void test(int value = 57);

            void main()
            {
                test();
            }

            void test(int value = 57)
            {
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 57

    def test_prototype_with_default_constant_arg(self):
        """Test function prototype with default constant argument."""
        ncs = self.compile(
            """
            void test(int value = DAMAGE_TYPE_COLD);

            void main()
            {
                test();
            }

            void test(int value = DAMAGE_TYPE_COLD)
            {
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 32

    def test_prototype_missing_arg(self):
        """Test function call with missing required argument."""
        source = """
            void test(int value);

            void main()
            {
                test();
            }

            void test(int value)
            {
                PrintInteger(value);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_prototype_missing_arg_and_default(self):
        """Test function call missing required argument when optional exists."""
        source = """
            void test(int value1, int value2 = 123);

            void main()
            {
                test();
            }

            void test(int value1, int value2 = 123)
            {
                PrintInteger(value1);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_prototype_default_before_required(self):
        """Test function with default parameter before required (should error)."""
        source = """
            void test(int value1 = 123, int value2);

            void main()
            {
                test(123, 123);
            }

            void test(int value1 = 123, int value2)
            {
                PrintInteger(value1);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_redefine_function(self):
        """Test redefining a function (should error)."""
        script = """
            void test()
            {

            }

            void test()
            {

            }
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_double_prototype(self):
        """Test duplicate function prototype (should error)."""
        script = """
            void test();
            void test();
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_prototype_after_definition(self):
        """Test function prototype after definition (should error)."""
        script = """
            void test()
            {

            }

            void test();
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_prototype_and_definition_param_mismatch(self):
        """Test function prototype and definition parameter mismatch."""
        script = """
            void test(int a);

            void test()
            {

            }
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_prototype_and_definition_default_param_mismatch(self):
        """This test is disabled for now."""
        # script = """
        #     void test(int a = 1);
        #
        #     void test(int a = 2)
        #     {
        #
        #     }
        # """
        # self.assertRaises(CompileError, self.compile, script)

    def test_prototype_and_definition_return_mismatch(self):
        """Test function prototype and definition return type mismatch."""
        script = """
            void test(int a);

            int test(int a)
            {

            }
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_call_undefined(self):
        """Test calling undefined function (should error)."""
        script = """
            void main()
            {
                test(0);
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_call_void_with_no_args(self):
        """Test calling void function with no arguments."""
        ncs = self.compile(
            """
            void test()
            {
                PrintInteger(123);
            }

            void main()
            {
                test();
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 123

    def test_call_void_with_one_arg(self):
        """Test calling void function with one argument."""
        ncs = self.compile(
            """
            void test(int value)
            {
                PrintInteger(value);
            }

            void main()
            {
                test(123);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 123

    def test_call_void_with_two_args(self):
        """Test calling void function with two arguments."""
        ncs = self.compile(
            """
            void test(int value1, int value2)
            {
                PrintInteger(value1);
                PrintInteger(value2);
            }

            void main()
            {
                test(1, 2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2

    def test_call_int_with_no_args(self):
        """Test calling integer-returning function with no arguments."""
        ncs = self.compile(
            """
            int test()
            {
                return 5;
            }

            void main()
            {
                int x = test();
                PrintInteger(x);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 5

    def test_call_int_with_no_args_and_forward_declared(self):
        """Test calling forward-declared integer-returning function."""
        ncs = self.compile(
            """
            int test();

            int test()
            {
                return 5;
            }

            void main()
            {
                int x = test();
                PrintInteger(x);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 5

    def test_call_param_mismatch(self):
        """Test function call with parameter type mismatch."""
        source = """
            int test(int a)
            {
                return a;
            }

            void main()
            {
                test("123");
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    # endregion

    # region Return Statement Tests
    def test_return(self):
        """Test return statement."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;

                if (a == 1)
                {
                    PrintInteger(a);
                    return;
                }

                PrintInteger(0);
                return;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_return_parenthesis(self):
        """Test return statement with parentheses."""
        ncs = self.compile(
            """
            int test()
            {
                return(321);
            }

            void main()
            {
                int value = test();
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[0].arg_values[0] == 321

    def test_return_parenthesis_constant(self):
        """Test return statement with constant in parentheses."""
        ncs = self.compile(
            """
            int test()
            {
                return(TRUE);
            }

            void main()
            {
                int value = test();
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_int_parenthesis_declaration(self):
        """Test integer declaration with parentheses."""
        ncs = self.compile(
            """
            void main()
            {
                int value = (123);
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 123

    # endregion

    # region Include Tests
    def test_include_builtin(self):
        """Test #include directive with built-in library."""
        otherscript = """
            void TestFunc()
            {
                PrintInteger(123);
            }
        """.encode(encoding="windows-1252")

        ncs = self.compile(
            """
            #include "otherscript"

            void main()
            {
                TestFunc();
            }
        """,
            library={"otherscript": otherscript},
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_include_lookup(self):
        """Test #include directive with file lookup."""
        includetest_script_path: Path = Path("./Libraries/PyKotor/tests/test_files").resolve()
        if not includetest_script_path.is_dir():
            msg = "Could not find includetest.nss in the include folder!"
            raise FileNotFoundError(errno.ENOENT, msg, str(includetest_script_path))
        ncs: NCS = self.compile(
            """
            #include "includetest"

            void main()
            {
                TestFunc();
            }
        """,
            library_lookup=[includetest_script_path],
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_nested_include(self):
        """Test nested #include directives."""
        first_script: bytes = """
            int SOME_COST = 13;

            void TestFunc(int value)
            {
                PrintInteger(value);
            }
        """.encode(encoding="windows-1252")

        second_script: bytes = """
            #include "first_script"
        """.encode(encoding="windows-1252")

        ncs: NCS = self.compile(
            """
            #include "second_script"

            void main()
            {
                TestFunc(SOME_COST);
            }
        """,
            library={"first_script": first_script, "second_script": second_script},
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 13

    def test_missing_include(self):
        """Test missing #include file (should error)."""
        source = """
            #include "otherscript"

            void main()
            {
                TestFunc();
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_imported_global_variable(self):
        """Test using global variable from included file."""
        otherscript = """
            int iExperience = 55;
        """.encode(encoding="windows-1252")

        ncs = self.compile(
            """
            #include "otherscript"

            void main()
            {
                object oPlayer = GetPCSpeaker();
                GiveXPToCreature(oPlayer, iExperience);
            }
        """,
            library={"otherscript": otherscript},
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[1].arg_values[1] == 55

    # endregion

    # region Comment Tests
    def test_comment(self):
        """Test single-line comment."""
        ncs = self.compile(
            """
            void main()
            {
                // int a = "abc"; // [] /*
                int a = 0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_multiline_comment(self):
        """Test multi-line comment."""
        ncs = self.compile(
            """
            void main()
            {
                /* int
                abc =
                ;; 123
                */

                string aaa = "";
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    # endregion

    # region Expression Tests
    def test_assignmentless_expression(self):
        """Test expression without assignment."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 123;

                1;
                GetCheatCode(1);
                "abc";

                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 123

    def test_nop_statement(self):
        """Test NOP statement."""
        ncs = self.compile(
            """
            void main()
            {
                NOP "test message";
                PrintInteger(42);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 42

    # endregion

    # region Vector Arithmetic Tests
    def test_vector_addition(self):
        """Test vector addition."""
        ncs = self.compile(
            """
            void main()
            {
                vector v1 = Vector(1.0, 2.0, 3.0);
                vector v2 = Vector(4.0, 5.0, 6.0);
                vector result = v1 + v2;
                PrintFloat(result.x);
                PrintFloat(result.y);
                PrintFloat(result.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 5.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 7.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 9.0

    def test_vector_subtraction(self):
        """Test vector subtraction."""
        ncs = self.compile(
            """
            void main()
            {
                vector v1 = Vector(5.0, 7.0, 9.0);
                vector v2 = Vector(1.0, 2.0, 3.0);
                vector result = v1 - v2;
                PrintFloat(result.x);
                PrintFloat(result.y);
                PrintFloat(result.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 5.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 6.0

    def test_vector_multiplication_float(self):
        """Test vector multiplication by float."""
        ncs = self.compile(
            """
            void main()
            {
                vector v1 = Vector(2.0, 3.0, 4.0);
                vector result = v1 * 2.0;
                PrintFloat(result.x);
                PrintFloat(result.y);
                PrintFloat(result.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 6.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 8.0

    def test_vector_division_float(self):
        """Test vector division by float."""
        ncs = self.compile(
            """
            void main()
            {
                vector v1 = Vector(8.0, 6.0, 4.0);
                vector result = v1 / 2.0;
                PrintFloat(result.x);
                PrintFloat(result.y);
                PrintFloat(result.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 3.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 2.0

    def test_vector_compound_assignment_addition(self):
        """Test vector compound assignment with addition."""
        ncs = self.compile(
            """
            void main()
            {
                vector v = Vector(1.0, 2.0, 3.0);
                v += Vector(0.5, 0.5, 0.5);
                PrintFloat(v.x);
                PrintFloat(v.y);
                PrintFloat(v.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1.5
        assert interpreter.action_snapshots[-2].arg_values[0] == 2.5
        assert interpreter.action_snapshots[-1].arg_values[0] == 3.5

    def test_vector_compound_assignment_subtraction(self):
        """Test vector compound assignment with subtraction."""
        ncs = self.compile(
            """
            void main()
            {
                vector v = Vector(5.0, 5.0, 5.0);
                v -= Vector(1.0, 2.0, 3.0);
                PrintFloat(v.x);
                PrintFloat(v.y);
                PrintFloat(v.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 3.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 2.0

    def test_vector_compound_assignment_multiplication(self):
        """Test vector compound assignment with multiplication."""
        ncs = self.compile(
            """
            void main()
            {
                vector v = Vector(2.0, 3.0, 4.0);
                v *= 2.0;
                PrintFloat(v.x);
                PrintFloat(v.y);
                PrintFloat(v.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 6.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 8.0

    def test_vector_compound_assignment_division(self):
        """Test vector compound assignment with division."""
        ncs = self.compile(
            """
            void main()
            {
                vector v = Vector(8.0, 6.0, 4.0);
                v /= 2.0;
                PrintFloat(v.x);
                PrintFloat(v.y);
                PrintFloat(v.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 3.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 2.0

    # endregion

    # region Nested Struct Tests
    def test_nested_struct_access(self):
        """Test accessing nested struct members."""
        ncs = self.compile(
            """
            struct Inner
            {
                int value;
            };

            struct Outer
            {
                struct Inner inner;
                string name;
            };

            void main()
            {
                struct Outer outer;
                outer.inner.value = 42;
                outer.name = "test";
                PrintInteger(outer.inner.value);
                PrintString(outer.name);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 42
        assert interpreter.action_snapshots[-1].arg_values[0] == "test"

    # endregion

    # region Complex Expression Tests
    def test_complex_expression_precedence(self):
        """Test complex expression with multiple operators and precedence."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 1 + 2 * 3 - 4 / 2;
                int b = (1 + 2) * (3 - 4) / 2;
                int c = 1 > 0 ? 10 + 5 : 20 - 5;
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 5  # 1 + 6 - 2 = 5
        assert interpreter.action_snapshots[-2].arg_values[0] == -1  # 3 * -1 / 2 = -1 (integer division)
        assert interpreter.action_snapshots[-1].arg_values[0] == 15  # 1 > 0 ? 15 : 15 = 15

    def test_expression_with_all_operators(self):
        """Test expression combining all operator types."""
        ncs = self.compile(
            """
            void main()
            {
                int a = 10;
                int b = 5;
                int result = (a + b) * 2 - (a / b) % 3 & 0xFF | 0x0F ^ 0xAA << 1 >> 1;
                PrintInteger(result);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        # Complex expression evaluation
        assert interpreter.action_snapshots[-1].arg_values[0] is not None

    # endregion


# ============================================================================
# Interpreter Tests
# ============================================================================

class TestNCSInterpreter(unittest.TestCase):
    """Tests for NCS interpreter and stack operations."""

    def test_peek_past_vector(self):
        """Test peeking past vector on stack."""
        stack = Stack()
        stack.add(DataType.FLOAT, 1.0)  # -20
        stack.add(DataType.VECTOR, Vector3(2.0, 3.0, 4.0))  # -16
        stack.add(DataType.FLOAT, 5.0)  # -4
        print(stack.peek(-20))

    def test_move_negative(self):
        """Test stack move with negative offset."""
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.move(-12)
        snapshop = stack.state()
        assert len(snapshop) == 3
        assert snapshop.pop() == 3.0
        assert snapshop.pop() == 2.0
        assert snapshop.pop() == 1.0

    def test_move_zero(self):
        """Test stack move with zero offset."""
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.move(0)
        snapshop = stack.state()
        assert len(snapshop) == 6
        assert snapshop.pop() == 6.0
        assert snapshop.pop() == 5.0
        assert snapshop.pop() == 4.0
        assert snapshop.pop() == 3.0
        assert snapshop.pop() == 2.0
        assert snapshop.pop() == 1.0

    def test_copy_down_single(self):
        """Test copying down a single value on stack."""
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.copy_down(-12, 4)

        assert stack.peek(-12) == 6

    def test_copy_down_many(self):
        """Test copying down multiple values on stack."""
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.copy_down(-24, 12)
        print(stack.state())

        assert stack.peek(-24) == 4
        assert stack.peek(-20) == 5
        assert stack.peek(-16) == 6


# ============================================================================
# Optimizer Tests
# ============================================================================

class TestNCSOptimizer(CompilerTestBase):
    """Tests for NCS bytecode optimizers."""

    def test_no_op_optimizer(self):
        """Test RemoveNopOptimizer removes NOP instructions."""
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value > 0)
                {
                    if (value > 0)
                    {
                        PrintInteger(value);
                        value -= 1;
                    }
                }
            }
        """
        )

        ncs.optimize([RemoveNopOptimizer()])
        ncs.print()

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1


# ============================================================================
# Roundtrip Tests
# ============================================================================

class TestNCSRoundtrip(unittest.TestCase):
    """Tests for NSS to NCS to NSS roundtrip compilation."""

    DEFAULT_SAMPLE_SIZE = 10
    SAMPLE_LIMIT = int(os.environ.get("PYKOTOR_NCS_ROUNDTRIP_SAMPLE", DEFAULT_SAMPLE_SIZE))
    _ROUNDTRIP_CASES: list[tuple[Game, Path, list[Path]]] | None = None

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[4]
        cls.vanilla_root = cls.root / "vendor" / "Vanilla_KOTOR_Script_Source"
        cls.roundtrip_cases = cls._initialize_roundtrip_cases()

    def test_nss_roundtrip(self):
        """Test roundtrip compilation of vanilla game scripts."""
        if not self.roundtrip_cases:
            self.skipTest("Vanilla_KOTOR_Script_Source submodule not available or no scripts collected")

        for game, script_path, library_lookup in self.roundtrip_cases:
            with self.subTest(f"{game.name}_{script_path.relative_to(self.vanilla_root)}"):
                source = script_path.read_text(encoding="windows-1252", errors="ignore")
                original_ncs = compile_nss(source, game, library_lookup=library_lookup)

                decompiled_source = decompile_ncs(original_ncs, game)
                roundtrip_ncs = compile_nss(decompiled_source, game, library_lookup=library_lookup)
                roundtrip_source = decompile_ncs(roundtrip_ncs, game)
                roundtrip_ncs_second = compile_nss(roundtrip_source, game, library_lookup=library_lookup)

                self.assertEqual(
                    roundtrip_ncs,
                    roundtrip_ncs_second,
                    f"Roundtrip compilation not stable for {script_path}",
                )

    @classmethod
    def _iter_scripts(cls, root: Path) -> list[Path]:
        """Iterate over all .nss files in directory tree."""
        return sorted(root.rglob("*.nss"))

    @classmethod
    def _collect_sample(cls, game: Game, roots: list[Path], library_lookup: list[Path]) -> list[Path]:
        """Collect sample scripts for roundtrip testing."""
        sample: list[Path] = []
        for directory in roots:
            for script in cls._iter_scripts(directory):
                if script in sample:
                    print(f"Skipping duplicate script {script} for game {game}")
                    continue
                try:
                    source = script.read_text(encoding="windows-1252", errors="ignore")
                except FileNotFoundError:
                    print(f"Skipping missing script {script} for game {game}")
                    continue

                # Skip scripts that rely on external includes for now
                if "#include" in source:
                    print(f"Skipping script {script} for game {game} due to include directive")
                    continue

                try:
                    compile_nss(source, game, library_lookup=library_lookup)
                except Exception:
                    print(f"Compilation failed for script {script} for game {game}")
                    print(f"{traceback.format_exc()}\n")
                    continue

                sample.append(script)
                if cls.SAMPLE_LIMIT and len(sample) >= cls.SAMPLE_LIMIT:
                    print(
                        f"Reached sample limit {cls.SAMPLE_LIMIT} for game {game} with directory {directory}",
                    )
                    return sample
        return sample

    @classmethod
    def _game_config(cls) -> dict[Game, dict[str, list[Path]]]:
        """Get game configuration for script collection."""
        return {
            Game.K1: {
                "roots": [
                    cls.vanilla_root / "K1" / "Modules",
                    cls.vanilla_root / "K1" / "Rims",
                    cls.vanilla_root / "K1" / "Data" / "scripts.bif",
                ],
                "lookup": [
                    (cls.vanilla_root / "K1" / "Modules").resolve(),
                    (cls.vanilla_root / "K1" / "Rims").resolve(),
                    (cls.vanilla_root / "K1" / "Data" / "scripts.bif").resolve(),
                ],
            },
            Game.K2: {
                "roots": [
                    cls.vanilla_root / "TSL" / "Vanilla" / "Modules",
                    cls.vanilla_root / "TSL" / "Vanilla" / "Data" / "Scripts",
                ],
                "lookup": [
                    (cls.vanilla_root / "TSL" / "Vanilla" / "Modules").resolve(),
                    (cls.vanilla_root / "TSL" / "Vanilla" / "Data" / "Scripts").resolve(),
                    (cls.vanilla_root / "TSL" / "TSLRCM" / "Override").resolve(),
                ],
            },
        }

    @classmethod
    def _initialize_roundtrip_cases(cls) -> list[tuple[Game, Path, list[Path]]]:
        """Initialize roundtrip test cases from vanilla game scripts."""
        if cls._ROUNDTRIP_CASES is not None:
            print(f"Roundtrip cases already initialized with {len(cls._ROUNDTRIP_CASES)} entries")
            return cls._ROUNDTRIP_CASES

        roundtrip_cases: list[tuple[Game, Path, list[Path]]] = []
        if not cls.vanilla_root.exists():
            print(f"Skipping sample collection because VANILLA_ROOT {cls.vanilla_root} does not exist")
            cls._ROUNDTRIP_CASES = roundtrip_cases
            return roundtrip_cases

        print("Collecting sample scripts from Vanilla_KOTOR_Script_Source...")
        for game, config in cls._game_config().items():
            print(f"Collecting sample scripts for {game.name}...")
            roots = [path for path in config["roots"] if path.exists() and path.is_dir()]
            lookup = [path for path in config["lookup"] if path.exists()]
            print(f"Roots: {roots}")
            print(f"Lookup: {lookup}")
            if not roots or not lookup:
                print(f"No roots or lookup found for {game.name}, skipping...")
                continue
            sample = cls._collect_sample(game, roots, lookup)
            roundtrip_cases.extend(
                (game, script, lookup) for script in sample
            )

        cls._ROUNDTRIP_CASES = roundtrip_cases
        return roundtrip_cases


# ============================================================================
# Granular Roundtrip Tests
# ============================================================================

TESTS_ROOT = Path(__file__).resolve().parents[4]


def _canonical_bytes(ncs: NCS) -> bytes:
    """Return canonical byte representation for easy equality checks."""
    return bytes(bytes_ncs(ncs))


def _assert_bidirectional_roundtrip(
    source: str,
    game: Game,
    *,
    library_lookup: list[Path] | None = None,
) -> str:
    """
    Compile source to NCS, decompile it back, and ensure both NSS->NCS->NSS and
    NCS->NSS->NCS cycles are stable for the given game context.
    """
    compiled = compile_nss(source, game, library_lookup=library_lookup)
    decompiled = decompile_ncs(compiled, game)

    # NSS -> NCS -> NSS -> NCS
    recompiled = compile_nss(decompiled, game, library_lookup=library_lookup)
    assert _canonical_bytes(compiled) == _canonical_bytes(
        recompiled
    ), "Recompiled bytecode diverged from initial compile"

    # NCS -> NSS -> NCS using freshly parsed binary payload
    binary_blob = _canonical_bytes(compiled)
    reloaded = read_ncs(binary_blob)
    ncs_from_binary = compile_nss(
        decompile_ncs(reloaded, game),
        game,
        library_lookup=library_lookup,
    )
    assert _canonical_bytes(reloaded) == _canonical_bytes(
        ncs_from_binary
    ), "Roundtrip from binary payload not stable"

    return decompiled


def _dedent(script: str) -> str:
    """Dedent and strip script text."""
    return textwrap.dedent(script).strip() + "\n"


def _assert_substrings(source: str, substrings: list[str]) -> None:
    """Assert that all substrings are present in source."""
    for snippet in substrings:
        assert (
            snippet in source
        ), f"Expected snippet '{snippet}' to be present in decompiled script:\n{source}"


class TestNssNcsRoundtripGranular(unittest.TestCase):
    """Granular tests for NSS to NCS roundtrip compilation."""

    def test_roundtrip_primitives_and_structural_types(self):
        """Test roundtrip with primitive and structural data types."""
        source = _dedent(
            """
            void main()
            {
                int valueInt = 42;
                float valueFloat = 3.5;
                string valueString = "kotor";
                object valueObject = OBJECT_SELF;
                vector valueVector = Vector(1.0, 2.0, 3.0);
                location valueLocation = Location(valueVector, 180.0);
                effect valueEffect = GetFirstEffect(OBJECT_SELF);
                event valueEvent = EventUserDefined(12);
                talent valueTalent = TalentFeat(FEAT_POWER_ATTACK);

                if (GetIsEffectValid(valueEffect))
                {
                    RemoveEffect(OBJECT_SELF, valueEffect);
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int valueInt = 42;",
                "float valueFloat = 3.5;",
                "string valueString = \"kotor\";",
                "object valueObject = OBJECT_SELF;",
                "vector valueVector = Vector(1.0, 2.0, 3.0);",
                "location valueLocation = Location(valueVector, 180.0);",
                "event valueEvent = EventUserDefined(12);",
                "talent valueTalent = TalentFeat(FEAT_POWER_ATTACK);",
            ],
        )

    def test_roundtrip_arithmetic_operations(self):
        """Test roundtrip with arithmetic operations."""
        source = _dedent(
            """
            float CalculateAverage(int first, int second, float weight)
            {
                float total = IntToFloat(first + second);
                float average = total / 2.0;
                return (average * weight) - 1.5;
            }

            void main()
            {
                int a = 10;
                int b = 7;
                int sum = a + b;
                int difference = sum - 5;
                int product = difference * 3;
                int quotient = product / 4;
                int remainder = quotient % 2;
                float weighted = CalculateAverage(sum, difference, 4.5);
                float negated = -weighted;
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int sum = a + b;",
                "int difference = sum - 5;",
                "int product = difference * 3;",
                "int quotient = product / 4;",
                "int remainder = quotient % 2;",
                "float negated = -weighted;",
            ],
        )

    def test_roundtrip_bitwise_and_shift_operations(self):
        """Test roundtrip with bitwise and shift operations."""
        source = _dedent(
            """
            void main()
            {
                int mask = 0xFF;
                int value = 0x35;
                int andResult = mask & value;
                int orResult = mask | value;
                int xorResult = mask ^ value;
                int leftShift = value << 2;
                int rightShift = mask >> 3;
                int unsignedShift = mask >>> 1;
                int inverted = ~value;
                int combined = (andResult | xorResult) & ~leftShift;
                int logicalMix = (combined != 0) && (xorResult == 0xCA);
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int andResult = mask & value;",
                "int orResult = mask | value;",
                "int xorResult = mask ^ value;",
                "int leftShift = value << 2;",
                "int rightShift = mask >> 3;",
                "int unsignedShift = mask >>> 1;",
                "int inverted = ~value;",
            ],
        )

    def test_roundtrip_logical_and_relational_operations(self):
        """Test roundtrip with logical and relational operations."""
        source = _dedent(
            """
            int Evaluate(int a, int b, int c)
            {
                if ((a > b && b >= c) || (a == c))
                {
                    return 1;
                }
                else if (!(c < a) && (b != 0))
                {
                    return 2;
                }
                return 0;
            }

            void main()
            {
                int flag = Evaluate(5, 3, 4);
                if (flag == 1 || flag == 2)
                {
                    AssignCommand(OBJECT_SELF, PlayAnimation(ANIMATION_LOOPING_GET_LOW, 1.0, 0.5));
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "if ((a > b && b >= c) || (a == c))",
                "else if (!(c < a) && (b != 0))",
                "if (flag == 1 || flag == 2)",
            ],
        )

    def test_roundtrip_compound_assignments(self):
        """Test roundtrip with compound assignment operators."""
        source = _dedent(
            """
            void main()
            {
                int counter = 0;
                counter += 5;
                counter -= 2;
                counter *= 3;
                counter /= 2;
                counter %= 4;

                float distance = 10.0;
                distance += 2.5;
                distance -= 1.5;
                distance *= 1.25;
                distance /= 3.0;

                vector offset = Vector(1.0, 2.0, 3.0);
                offset += Vector(0.5, 0.5, 0.5);
                offset -= Vector(0.5, 1.0, 1.5);
                offset *= 2.0;
                offset /= 4.0;
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "counter += 5;",
                "counter -= 2;",
                "counter *= 3;",
                "counter /= 2;",
                "counter %= 4;",
                "distance += 2.5;",
                "offset += Vector(0.5, 0.5, 0.5);",
                "offset *= 2.0;",
            ],
        )

    def test_roundtrip_increment_and_decrement(self):
        """Test roundtrip with increment and decrement operators."""
        source = _dedent(
            """
            void main()
            {
                int i = 0;
                int first = i++;
                int second = ++i;
                int third = i--;
                int fourth = --i;
                if (first < second && third >= fourth)
                {
                    i += 1;
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int first = i++;",
                "int second = ++i;",
                "int third = i--;",
                "int fourth = --i;",
            ],
        )

    def test_roundtrip_if_else_nesting(self):
        """Test roundtrip with nested if-else statements."""
        source = _dedent(
            """
            int EvaluateState(int state)
            {
                if (state == 0)
                {
                    return 10;
                }
                else if (state == 1)
                {
                    if (GetIsNight())
                    {
                        return 20;
                    }
                    else
                    {
                        return 30;
                    }
                }
                else
                {
                    return -1;
                }
            }

            void main()
            {
                int result = EvaluateState(1);
                if (result == 20)
                {
                    ActionStartConversation(OBJECT_SELF, "result_20");
                }
                else
                {
                    ActionStartConversation(OBJECT_SELF, "other_result");
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "if (state == 0)",
                "else if (state == 1)",
                "if (GetIsNight())",
                "else",
                "ActionStartConversation(OBJECT_SELF, \"result_20\");",
            ],
        )

    def test_roundtrip_while_for_do_loops(self):
        """Test roundtrip with while, for, and do-while loops."""
        source = _dedent(
            """
            void main()
            {
                int total = 0;
                int i = 0;
                while (i < 5)
                {
                    total += i;
                    i++;
                }

                for (int j = 0; j < 3; j++)
                {
                    total += j * 2;
                }

                int k = 0;
                do
                {
                    total -= k;
                    k++;
                }
                while (k < 2);
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "while (i < 5)",
                "for (int j = 0; j < 3; j++)",
                "do",
                "while (k < 2);",
            ],
        )

    def test_roundtrip_switch_case(self):
        """Test roundtrip with switch-case statements."""
        source = _dedent(
            """
            void main()
            {
                int value = Random(3);
                switch (value)
                {
                    case 0:
                        value = 1;
                        break;
                    case 1:
                    case 2:
                        value = 3;
                        break;
                    default:
                        value = 0;
                        break;
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "switch (value)",
                "case 0:",
                "case 1:",
                "case 2:",
                "default:",
            ],
        )

    def test_roundtrip_struct_usage(self):
        """Test roundtrip with struct definitions and usage."""
        source = _dedent(
            """
            struct CombatStats
            {
                int attack;
                int defense;
                float multiplier;
                string label;
            };

            CombatStats BuildStats(int base)
            {
                CombatStats result;
                result.attack = base + 2;
                result.defense = base * 2;
                result.multiplier = IntToFloat(result.defense) / 3.0;
                result.label = \"stat_\" + IntToString(base);
                return result;
            }

            void main()
            {
                CombatStats stats = BuildStats(5);
                if (stats.attack > stats.defense)
                {
                    stats.label = \"attack_bias\";
                }
                else
                {
                    stats.label = \"defense_bias\";
                }
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "struct CombatStats",
                "result.attack = base + 2;",
                "result.defense = base * 2;",
                "stats.label = \"attack_bias\";",
            ],
        )

    def test_roundtrip_function_definitions_and_returns(self):
        """Test roundtrip with function definitions and return statements."""
        source = _dedent(
            """
            int CountPartyMembers()
            {
                int count = 0;
                object creature = GetFirstFactionMember(OBJECT_SELF, FALSE);
                while (GetIsObjectValid(creature))
                {
                    count++;
                    creature = GetNextFactionMember(OBJECT_SELF, FALSE);
                }
                return count;
            }

            void Announce(int members)
            {
                string message = "members:" + IntToString(members);
                SendMessageToPC(OBJECT_SELF, message);
            }

            void main()
            {
                int members = CountPartyMembers();
                Announce(members);
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "int CountPartyMembers()",
                "while (GetIsObjectValid(creature))",
                "void Announce(int members)",
                "Announce(members);",
            ],
        )

    def test_roundtrip_action_queue_and_delays(self):
        """Test roundtrip with action queue and delay commands."""
        source = _dedent(
            """
            void ApplyBuff(object target)
            {
                effect buff = EffectAbilityIncrease(ABILITY_STRENGTH, 2);
                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, buff, target, 6.0);
            }

            void main()
            {
                object player = GetFirstPC();
                DelayCommand(1.5, AssignCommand(player, ApplyBuff(player)));
                ClearAllActions();
                ActionDoCommand(AssignCommand(OBJECT_SELF, PlaySound("pc_action")));
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K1)
        _assert_substrings(
            decompiled,
            [
                "DelayCommand(1.5, AssignCommand(player, ApplyBuff(player)));",
                "ClearAllActions();",
                "ActionDoCommand(AssignCommand(OBJECT_SELF, PlaySound(\"pc_action\")));",
            ],
        )

    def test_roundtrip_include_resolution(self):
        """Test roundtrip with include directives."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            include_path = tmp_path / "rt_helper.nss"
            include_path.write_text(
                _dedent(
                    """
                    int HelperFunction(int value)
                    {
                        return value * 2;
                    }
                    """
                ),
                encoding="utf-8",
            )

            source = _dedent(
                """
                #include "rt_helper"

                void main()
                {
                    int result = HelperFunction(5);
                    SetLocalInt(OBJECT_SELF, "helper", result);
                }
                """
            )

            decompiled = _assert_bidirectional_roundtrip(
                source,
                Game.K1,
                library_lookup=[tmp_path],
            )
        _assert_substrings(
            decompiled,
            [
                "int HelperFunction(int value)",
                "SetLocalInt(OBJECT_SELF, \"helper\", result);",
            ],
        )

    def test_roundtrip_tsl_specific_functionality(self):
        """Test roundtrip with TSL-specific functionality."""
        source = _dedent(
            """
            void main()
            {
                object target = GetFirstPC();
                effect penalty = EffectAttackDecrease(2, ATTACK_BONUS_MISC);
                ApplyEffectToObject(DURATION_TYPE_TEMPORARY, penalty, target, 5.0);
                AssignCommand(target, ClearAllActions());
            }
            """
        )

        decompiled = _assert_bidirectional_roundtrip(source, Game.K2)
        _assert_substrings(
            decompiled,
            [
                "effect penalty = EffectAttackDecrease(2, ATTACK_BONUS_MISC);",
                "ApplyEffectToObject(DURATION_TYPE_TEMPORARY, penalty, target, 5.0);",
            ],
        )


# Convert to pytest function since unittest.TestCase doesn't support pytest.mark.parametrize
SAMPLE_FILES = [
    ("tests/files/test.ncs", Game.K1),
    ("Libraries/PyKotor/tests/test_files/test.ncs", Game.K1),
    ("tests/test_toolset/test_files/90sk99.ncs", Game.K2),
]


@pytest.mark.parametrize(("relative_path", "game"), SAMPLE_FILES)
def test_binary_roundtrip_samples(relative_path: str, game: Game):
    """Test roundtrip compilation of binary NCS sample files."""
    ncs_path = TESTS_ROOT.parent / relative_path
    assert ncs_path.is_file(), f"Sample NCS file '{ncs_path}' is missing"

    original = read_ncs(ncs_path)
    decompiled = decompile_ncs(original, game)
    recompilation = compile_nss(decompiled, game)

    assert _canonical_bytes(original) == _canonical_bytes(
        recompilation
    ), f"Roundtrip failed for {relative_path}"
    assert len(decompiled.strip()) > 0, "Decompiled source should not be empty"


# ============================================================================
# K1_NCS_Un-decompilable Roundtrip Tests (NCS -> NSS -> NCS)
# ============================================================================

K1_UNDECOMPILABLE_DIR = Path(__file__).resolve().parents[3] / "test_files" / "K1_NCS_Un-decompilable"


def _collect_k1_undecompilable_files() -> list[tuple[Path, str]]:
    """Collect all NCS files from K1_NCS_Un-decompilable directory."""
    if not K1_UNDECOMPILABLE_DIR.exists():
        return []
    
    files = []
    for ncs_file in K1_UNDECOMPILABLE_DIR.rglob("*.ncs"):
        # Create a test identifier from the relative path
        rel_path = ncs_file.relative_to(K1_UNDECOMPILABLE_DIR.parent)
        test_id = str(rel_path).replace("\\", "/")
        files.append((ncs_file, test_id))
    
    return sorted(files)


K1_UNDECOMPILABLE_FILES = _collect_k1_undecompilable_files()


@pytest.mark.parametrize(("ncs_path", "test_id"), K1_UNDECOMPILABLE_FILES)
def test_k1_undecompilable_roundtrip(ncs_path: Path, test_id: str):
    """Test NCS -> NSS -> NCS roundtrip for K1 undecompilable files.
    
    These files were previously marked as undecompilable but should now
    decompile and recompile to byte-identical NCS.
    """
    assert ncs_path.is_file(), f"Test NCS file '{ncs_path}' is missing"
    
    # Read original NCS
    original = read_ncs(ncs_path)
    original_bytes = _canonical_bytes(original)
    
    # Decompile to NSS
    decompiled = decompile_ncs(original, Game.K1)
    assert len(decompiled.strip()) > 0, f"Decompiled source should not be empty for {test_id}"
    
    # Recompile to NCS
    recompiled = compile_nss(decompiled, Game.K1)
    recompiled_bytes = _canonical_bytes(recompiled)
    
    # Assert byte-identical roundtrip
    assert original_bytes == recompiled_bytes, (
        f"Roundtrip failed for {test_id}: "
        f"original has {len(original.instructions)} instructions, "
        f"recompiled has {len(recompiled.instructions)} instructions"
    )


# ============================================================================
# TSL-Specific Compilation Tests
# ============================================================================


def test_compile_a_galaxy_map_tsl(k2_path: str):
    """Test compilation of a_galaxy_map.nss for TSL."""
    script_path = Path(__file__).resolve().parents[3] / "test_files" / "a_galaxy_map.nss"
    if not script_path.exists():
        pytest.skip(f"Test script not found: {script_path}")

    source = script_path.read_text(encoding="windows-1252", errors="ignore")
    ncs = compile_nss(source, Game.K2)
    assert ncs is not None
    assert len(ncs.instructions) > 0, "Compiled NCS should have instructions"


def test_compile_k_sup_galaxymap_tsl(k2_path: str):
    """Test compilation of k_sup_galaxymap.nss for TSL with include handling."""
    script_path = Path(__file__).resolve().parents[3] / "test_files" / "k_sup_galaxymap.nss"
    if not script_path.exists():
        pytest.skip(f"Test script not found: {script_path}")

    source = script_path.read_text(encoding="windows-1252", errors="ignore")
    # Provide library lookup for include resolution
    test_files_dir = script_path.parent
    library_lookup = [test_files_dir]

    ncs = compile_nss(source, Game.K2, library_lookup=library_lookup)
    assert ncs is not None
    assert len(ncs.instructions) > 0, "Compiled NCS should have instructions"


def test_compile_a_galaxymap_tsl(k2_path: str):
    """Test compilation of a_galaxymap.nss for TSL with many global variables."""
    script_path = Path(__file__).resolve().parents[3] / "test_files" / "a_galaxymap.nss"
    if not script_path.exists():
        pytest.skip(f"Test script not found: {script_path}")

    source = script_path.read_text(encoding="windows-1252", errors="ignore")
    ncs = compile_nss(source, Game.K2)
    assert ncs is not None
    assert len(ncs.instructions) > 0, "Compiled NCS should have instructions"
    # Verify SAVEBP instruction exists (indicates global variables)
    assert any(
        inst.ins_type == NCSInstructionType.SAVEBP for inst in ncs.instructions
    ), "Script with globals should have SAVEBP instruction"


def test_compile_tr_leave_ehawk_tsl(k2_path: str):
    """Test compilation of tr_leave_ehawk.nss for TSL."""
    script_path = Path(__file__).resolve().parents[3] / "test_files" / "tr_leave_ehawk.nss"
    if not script_path.exists():
        pytest.skip(f"Test script not found: {script_path}")

    source = script_path.read_text(encoding="windows-1252", errors="ignore")
    ncs = compile_nss(source, Game.K2)
    assert ncs is not None
    assert len(ncs.instructions) > 0, "Compiled NCS should have instructions"


def test_compile_all_tsl_scripts_batch(k2_path: str):
    """Test batch compilation of all TSL test scripts."""
    test_files_dir = Path(__file__).resolve().parents[3] / "test_files"
    if not test_files_dir.exists():
        pytest.skip(f"Test files directory not found: {test_files_dir}")

    scripts = [
        "a_galaxy_map.nss",
        "a_galaxymap.nss",
        "tr_leave_ehawk.nss",
    ]
    # Note: k_sup_galaxymap.nss requires include, so test separately

    results = {}
    for script_name in scripts:
        script_path = test_files_dir / script_name
        if not script_path.exists():
            results[script_name] = "NOT_FOUND"
            continue

        try:
            source = script_path.read_text(encoding="windows-1252", errors="ignore")
            ncs = compile_nss(source, Game.K2)
            results[script_name] = "SUCCESS" if ncs and len(ncs.instructions) > 0 else "EMPTY"
        except Exception as e:
            results[script_name] = f"ERROR: {type(e).__name__}: {str(e)}"

    # Report results
    failed = [name for name, result in results.items() if result not in ("SUCCESS", "NOT_FOUND")]
    if failed:
        msg = f"Some scripts failed to compile:\n{chr(10).join(f'{name}: {results[name]}' for name in failed)}"
        pytest.fail(msg)


if __name__ == "__main__":
    unittest.main()
