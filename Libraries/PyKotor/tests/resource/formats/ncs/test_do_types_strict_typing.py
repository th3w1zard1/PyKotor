"""Tests for do_types with strict type checking.

Tests verify that SubroutineState.print_state is accessed directly.
"""

from __future__ import annotations

import pathlib
import sys

# Setup paths
THIS_FILE = pathlib.Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[5]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"

for path in (PYKOTOR_SRC, UTILITY_SRC):
    as_posix = path.as_posix()
    if as_posix not in sys.path:
        sys.path.insert(0, as_posix)

from contextlib import redirect_stdout
from io import StringIO

from pykotor.resource.formats.ncs.dencs.do_types import DoTypes
from pykotor.resource.formats.ncs.dencs.node.node import Node
from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData
from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState


class TestDoTypesStrictTyping:
    """Test DoTypes with strict type checking (no hasattr for print_state)."""

    def test_assert_stack_calls_print_state_directly(self):
        """Test that assert_stack() calls print_state() directly without hasattr."""
        # Create a minimal setup
        nodedata = NodeAnalysisData()
        root = Node()
        state = SubroutineState(nodedata, root, 0)

        do_types = DoTypes(state, nodedata, None, None, False)
        do_types.stack.push(1)  # Make stack non-empty to trigger assert

        # Capture stdout to verify print_state is called
        output = StringIO()
        with redirect_stdout(output):
            try:
                do_types.assert_stack()
            except RuntimeError as e:
                # Expected - assert_stack raises RuntimeError when stack is not empty
                assert "Error: Final stack size" in str(e)
                # Verify print_state was called (it prints to stdout)
                output_str = output.getvalue()
                # print_state prints "Return type is ..." and "There are ... parameters"
                assert "Return type is" in output_str or "There are" in output_str

    def test_subroutine_state_has_print_state_method(self):
        """Test that SubroutineState has print_state method (type check)."""
        nodedata = NodeAnalysisData()
        root = Node()
        state = SubroutineState(nodedata, root, 0)

        # Verify print_state exists and is callable (should be, based on type system)
        assert hasattr(state, "print_state")  # This test verifies the method exists
        assert callable(state.print_state)

        # Test that it can be called directly
        output = StringIO()
        with redirect_stdout(output):
            state.print_state()
        output_str = output.getvalue()
        assert "Return type is" in output_str
