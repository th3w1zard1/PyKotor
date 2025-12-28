import unittest
from pykotor.resource.formats.txi.txi_data import TXI

class TestTXI(unittest.TestCase):
    def test_parse_blending_default(self):
        self.assertEqual(TXI.parse_blending("default"), 0)
        self.assertEqual(TXI.parse_blending("DEFAULT"), 0)
        self.assertEqual(TXI.parse_blending("Default"), 0)

    def test_parse_blending_additive(self):
        self.assertEqual(TXI.parse_blending("additive"), 1)
        self.assertEqual(TXI.parse_blending("ADDITIVE"), 1)
        self.assertEqual(TXI.parse_blending("Additive"), 1)

    def test_parse_blending_punchthrough(self):
        self.assertEqual(TXI.parse_blending("punchthrough"), 2)
        self.assertEqual(TXI.parse_blending("PUNCHTHROUGH"), 2)
        self.assertEqual(TXI.parse_blending("Punchthrough"), 2)
        self.assertEqual(TXI.parse_blending("punch-through"), 2)

    def test_parse_blending_invalid(self):
        self.assertEqual(TXI.parse_blending("invalid"), 0)
        self.assertEqual(TXI.parse_blending(""), 0)
        self.assertEqual(TXI.parse_blending("blend"), 0)

    def test_parse_blending_case_insensitive(self):
        self.assertEqual(TXI.parse_blending("DeFaUlT"), 0)
        self.assertEqual(TXI.parse_blending("AdDiTiVe"), 1)
        self.assertEqual(TXI.parse_blending("PuNcHtHrOuGh"), 2)

if __name__ == "__main__":
    unittest.main()
