from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.geometry import Vector3
from pykotor.common.script import DataType
from pykotor.resource.formats.ncs.compiler.interpreter import Stack


class TestStack(TestCase):
    def test_peek_past_vector(self):
        stack = Stack()
        stack.add(DataType.FLOAT, 1.0)  # -20
        stack.add(DataType.VECTOR, Vector3(2.0, 3.0, 4.0))  # -16
        stack.add(DataType.FLOAT, 5.0)  # -4
        print(stack.peek(-20))

    def test_move_negative(self):
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


if __name__ == "__main__":
    unittest.main()
