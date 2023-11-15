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

from pykotor.common.geometry import Vector2
from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.pth import construct_pth, dismantle_pth

TEST_FILE = "tests/files/test.pth"


class TestPTH(unittest.TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        pth = construct_pth(gff)
        self.validate_io(pth)

        gff = dismantle_pth(pth)
        pth = construct_pth(gff)
        self.validate_io(pth)

    def validate_io(self, pth):
        self.assertEqual(pth.get(0), Vector2(0.0, 0.0))
        self.assertEqual(pth.get(1), Vector2(0.0, 1.0))
        self.assertEqual(pth.get(2), Vector2(1.0, 1.0))
        self.assertEqual(pth.get(3), Vector2(0.0, 2.0))

        self.assertEqual(2, len(pth.outgoing(0)))
        self.assertTrue(pth.is_connected(0, 1))
        self.assertTrue(pth.is_connected(0, 2))

        self.assertEqual(3, len(pth.outgoing(1)))
        self.assertTrue(pth.is_connected(1, 0))
        self.assertTrue(pth.is_connected(1, 2))
        self.assertTrue(pth.is_connected(1, 3))

        self.assertEqual(2, len(pth.outgoing(2)))
        self.assertTrue(pth.is_connected(2, 0))
        self.assertTrue(pth.is_connected(2, 1))

        self.assertEqual(1, len(pth.outgoing(3)))
        self.assertTrue(pth.is_connected(3, 1))


if __name__ == "__main__":
    unittest.main()
