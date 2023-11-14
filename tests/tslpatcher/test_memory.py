import pathlib
import sys
import unittest
from unittest import TestCase

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.gff import FieldValue2DAMemory, FieldValueConstant, FieldValueTLKMemory, LocalizedStringDelta


class TestLocalizedStringDelta(TestCase):
    def test_apply_stringref_2damemory(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta(FieldValue2DAMemory(5))

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_stringref_tlkmemory(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta(FieldValueTLKMemory(5))

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_stringref_int(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta(FieldValueConstant(123))

        memory = PatcherMemory()

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_stringref_none(self):
        locstring = LocalizedString(123)

        delta = LocalizedStringDelta(None)

        memory = PatcherMemory()

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_substring(self):
        locstring = LocalizedString(0)
        locstring.set_data(Language.ENGLISH, Gender.MALE, "a")
        locstring.set_data(Language.FRENCH, Gender.MALE, "b")

        delta = LocalizedStringDelta()
        delta.set_data(Language.ENGLISH, Gender.MALE, "1")
        delta.set_data(Language.GERMAN, Gender.MALE, "2")

        memory = PatcherMemory()

        delta.apply(locstring, memory)

        self.assertEqual(3, len(locstring))
        self.assertEqual("1", locstring.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual("2", locstring.get(Language.GERMAN, Gender.MALE))
        self.assertEqual("b", locstring.get(Language.FRENCH, Gender.MALE))  # TODO: Why is this 'b'?


if __name__ == "__main__":
    unittest.main()
