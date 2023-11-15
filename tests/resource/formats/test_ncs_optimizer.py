from __future__ import annotations

import pathlib
import sys
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.optimizers import RemoveNopOptimizer


class TestNCSOptimizers(unittest.TestCase):
    def compile(
        self,
        script: str,
        library: dict[str, bytes] | None = None,
        library_lookup: str | None = None,
    ) -> NCS:
        nssLexer = NssLexer()
        nssParser = NssParser(
            library=library,
            constants=KOTOR_CONSTANTS,
            functions=KOTOR_FUNCTIONS,
            library_lookup=library_lookup,
        )

        parser = nssParser.parser
        t = parser.parse(script, tracking=True)

        ncs = NCS()
        t.compile(ncs)
        return ncs

    def test_no_op_optimizer(self):
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

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[2].arg_values[0])


if __name__ == "__main__":
    unittest.main()
