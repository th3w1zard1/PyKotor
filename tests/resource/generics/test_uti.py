import pathlib
import sys
import unittest
from unittest import TestCase

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[3] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.resource.formats.gff import read_gff
from pykotor.resource.generics.uti import UTI, construct_uti, dismantle_uti

TEST_FILE = "tests/files/test.uti"


class TestUTI(TestCase):
    def test_io(self):
        gff = read_gff(TEST_FILE)
        uti = construct_uti(gff)
        self.validate_io(uti)

        gff = dismantle_uti(uti)
        uti = construct_uti(gff)
        self.validate_io(uti)

    def validate_io(self, uti: UTI):
        self.assertEqual("g_a_class4001", uti.resref)
        self.assertEqual(38, uti.base_item)
        self.assertEqual(5632, uti.name.stringref)
        self.assertEqual(5633, uti.description.stringref)
        self.assertEqual("G_A_CLASS4001", uti.tag)
        self.assertEqual(13, uti.charges)
        self.assertEqual(50, uti.cost)
        self.assertEqual(1, uti.stolen)
        self.assertEqual(1, uti.stack_size)
        self.assertEqual(1, uti.plot)
        self.assertEqual(50, uti.add_cost)
        self.assertEqual(1, uti.texture_variation)
        self.assertEqual(2, uti.model_variation)
        self.assertEqual(3, uti.body_variation)
        self.assertEqual(1, uti.texture_variation)
        self.assertEqual(1, uti.palette_id)
        self.assertEqual("itemo", uti.comment)

        self.assertEqual(2, len(uti.properties))
        self.assertIsNone(uti.properties[0].upgrade_type, None)
        self.assertEqual(100, uti.properties[1].chance_appear)
        self.assertEqual(1, uti.properties[1].cost_table)
        self.assertEqual(1, uti.properties[1].cost_value)
        self.assertEqual(255, uti.properties[1].param1)
        self.assertEqual(1, uti.properties[1].param1_value)
        self.assertEqual(45, uti.properties[1].property_name)
        self.assertEqual(6, uti.properties[1].subtype)
        self.assertEqual(24, uti.properties[1].upgrade_type)


if __name__ == "__main__":
    unittest.main()
