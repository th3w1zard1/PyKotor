from __future__ import annotations

from configparser import ConfigParser
import os
from typing import cast
from unittest import TestCase
import pathlib
import sys
import unittest

from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.reader import ConfigReader
from utility.logger_util import get_root_logger

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)



from typing import TYPE_CHECKING, cast

from pykotor.common.misc import Game
from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFList, GFFStruct
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.gff import (
    AddFieldGFF,
    AddStructToListGFF,
    FieldValue,
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
    ModificationsGFF,
    ModifyFieldGFF,
)

from utility.system.path import PureWindowsPath

if TYPE_CHECKING:
    from pykotor.tslpatcher.mods.gff import ModifyGFF



class TestDiffGFF(TestCase):
    def run_modify_field_test(
        self,
        field_type: str,
        initial_value: object,
        modified_value: object,
        field_name: str="Field1",
        field_value: FieldValue | None = None,
        path: os.PathLike | str | None = None,
        *,
        replace: bool = False,
        gff: GFF | None = None,
    ):  # sourcery skip: move-assign
        """
        Runs a generic test for modifying a GFF field.

        Args:
        ----
            initial_value: The initial value to set for the field.
            modified_value: The value to modify the field to.
            field_name: The name of the field to modify.
        """
        field_value = FieldValueConstant(modified_value) if field_value is None else field_value
        path = field_name if path is None else path
        set_field_method_name = f"set_{field_type}"
        get_field_method_name = f"get_{field_type}"

        if gff is None:
            gff = GFF()
            getattr(gff.root, set_field_method_name)(field_name, initial_value)

        memory = PatcherMemory()
        config = ModificationsGFF(f"test_{field_type}.gff", replace, [ModifyFieldGFF(path=path, identifier=field_name, value=field_value)])
        logger = PatchLogger()
        gff2 = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, logger, Game.K1)))

        # Assert the original value is unchanged
        self.assertEqual(initial_value, getattr(gff.root, get_field_method_name)(field_name), 
                        "Original was changed! A deepcopy was never made!\n\nLogs:\n" + 
                        "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs))
        
        # Assert the modified value is as expected
        retrieved_value = getattr(gff2.root, get_field_method_name)(field_name)
        self.assertEqual(modified_value, retrieved_value, 
                        "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs))

        # New diff logic
        config2 = ModificationsGFF.create_patch(gff, gff2, filename=f"test_modify_field_{field_type}")
        gff3 = read_gff(cast(bytes, config2.patch_resource(bytes_gff(gff), memory, logger, Game.K1)))
        self.assertEqual(modified_value, getattr(gff3.root, get_field_method_name)(field_name), 
                        "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs))

        config2 = ModificationsGFF.create_patch(gff2, gff, filename=f"test_revert_field_{field_type}")
        gff4 = read_gff(cast(bytes, config2.patch_resource(bytes_gff(gff2), memory, logger, Game.K1)))
        self.assertEqual(initial_value, getattr(gff4.root, get_field_method_name)(field_name), 
                        "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs))
        get_root_logger().debug("As ini: \n%s", config.as_gfflist_ini(ConfigParser()))

    def test_modify_field_uint8(self):
        self.run_modify_field_test('uint8', 1, 2)

    def test_modify_field_int8(self):
        self.run_modify_field_test('int8', 1, 2)

    def test_modify_field_uint16(self):
        self.run_modify_field_test('uint16', 1, 2)

    def test_modify_field_int16(self):
        self.run_modify_field_test('int16', 1, 2)

    def test_modify_field_uint32(self):
        self.run_modify_field_test('uint32', 1, 2)

    def test_modify_field_int32(self):
        self.run_modify_field_test('uint32', 1, 2)

    def test_modify_field_uint64(self):
        self.run_modify_field_test('uint32', 1, 2)

    def test_modify_field_int64(self):
        self.run_modify_field_test('uint32', 1, 2)

    def test_modify_field_single(self):
        self.run_modify_field_test('single', 1.234, 2.3450000286102295)

    def test_modify_field_double(self):
        self.run_modify_field_test('double', 1.234567, 2.345678)

    def test_modify_field_string(self):
        self.run_modify_field_test('string', "abc", "def")

    def test_modify_field_locstring(self):
        self.run_modify_field_test('locstring', LocalizedString(0), LocalizedString(1), field_value=FieldValueConstant(LocalizedStringDelta(FieldValueConstant(1))))

    def test_modify_field_vector3(self):
        self.run_modify_field_test('vector3', Vector3(0, 1, 2), Vector3(1, 2, 3))

    def test_modify_field_vector4(self):
        self.run_modify_field_test('vector4', Vector4(0, 1, 2, 3), Vector4(1, 2, 3, 4))

    def test_modify_nested(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)
        gff_struct.set_string("String", "")

        memory = PatcherMemory()
        logger = PatchLogger()
        modifiers: list[ModifyGFF] = [ModifyFieldGFF(PureWindowsPath("List\\0\\String"), FieldValueConstant("abc"))]

        config = ModificationsGFF("", False, modifiers)
        gff2 = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, logger, Game.K1)))
        patched_gff_list = gff2.root.get_list("List")
        patched_gff_struct = patched_gff_list.at(0)

        self.assertEqual("abc", patched_gff_struct.get_string("String"), 
                        "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs))

        # New diff logic
        logger = PatchLogger()
        config2 = ModificationsGFF.create_patch(gff, gff2, filename="test_modify_field_List")
        gff3 = read_gff(cast(bytes, config2.patch_resource(bytes_gff(gff), memory, logger, Game.K1)))
        patched_gff_list2 = gff3.root.get_list("List")
        patched_gff_struct2 = patched_gff_list2.at(0)
        self.assertEqual("abc", patched_gff_struct2.get_string("String"), 
                        "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs))

    def test_modify_2damemory(self):
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsGFF("", False, [])
        config.modifiers.append(ModifyFieldGFF("String", FieldValue2DAMemory(5)))
        config.modifiers.append(ModifyFieldGFF("Integer", FieldValue2DAMemory(5)))
        gff2 = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff2.root.get_string("String"))
        self.assertEqual(123, gff2.root.get_uint8("Integer"))

        # New diff logic
        logger = PatchLogger()
        config2 = ModificationsGFF.create_patch(gff, gff2, filename="test_modify_field_2damemory")
        gff3 = read_gff(cast(bytes, config2.patch_resource(bytes_gff(gff), memory, logger, Game.K1)))

        self.assertEqual("123", gff3.root.get_string("String"))
        self.assertEqual(123, gff3.root.get_uint8("Integer"))

    def test_modify_tlkmemory(self):
        gff = GFF()
        gff.root.set_string("String", "")
        gff.root.set_uint8("Integer", 0)

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", False, [])
        config.modifiers.append(ModifyFieldGFF("String", FieldValueTLKMemory(5)))
        config.modifiers.append(ModifyFieldGFF("Integer", FieldValueTLKMemory(5)))
        gff2 = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff2.root.get_string("String"))
        self.assertEqual(123, gff2.root.get_uint8("Integer"))

        # New diff logic
        logger = PatchLogger()
        config2 = ModificationsGFF.create_patch(gff, gff2, filename="test_modify_field_2damemory")
        gff3 = read_gff(cast(bytes, config2.patch_resource(bytes_gff(gff), memory, logger, Game.K1)))

        self.assertEqual("123", gff3.root.get_string("String"))
        self.assertEqual(123, gff3.root.get_uint8("Integer"))

    def test_add_newnested(self):
        gff = GFF()

        memory = PatcherMemory()

        add_field1 = AddFieldGFF("", "List", GFFFieldType.List, FieldValueConstant(GFFList()), PureWindowsPath(""))

        add_field2 = AddStructToListGFF("", FieldValueConstant(GFFStruct()), PureWindowsPath("List"))
        add_field1.modifiers.append(add_field2)

        add_field3 = AddFieldGFF("", "SomeInteger", GFFFieldType.UInt8, FieldValueConstant(123), PureWindowsPath("List\\>>##INDEXINLIST##<<"))
        add_field2.modifiers.append(add_field3)

        config = ModificationsGFF("", False, [add_field1])
        gff2 = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertIsNotNone(gff2.root.get_list("List"))
        self.assertIsNotNone(gff2.root.get_list("List").at(0))
        self.assertIsNotNone(gff2.root.get_list("List").at(0).get_uint8("SomeInteger"))  # type: ignore

        # New diff logic
        logger = PatchLogger()
        config2 = ModificationsGFF.create_patch(gff, gff2, filename="test_modify_field_List")
        gff3 = read_gff(cast(bytes, config2.patch_resource(bytes_gff(gff), memory, logger, Game.K1)))

        self.assertIsNotNone(gff3.root.get_list("List"))
        self.assertIsNotNone(gff3.root.get_list("List").at(0))
        self.assertIsNotNone(gff3.root.get_list("List").at(0).get_uint8("SomeInteger"))  # type: ignore

    def test_add_nested(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())
        gff_struct = gff_list.add(0)

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", False, [])
        config.modifiers.append(
            AddFieldGFF(
                "",
                "String",
                GFFFieldType.String,
                FieldValueConstant("abc"),
                path=PureWindowsPath("List\\0"),
            )
        )
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")
        patched_gff_struct = patched_gff_list.at(0)

        self.assertEqual("abc", patched_gff_struct.get_string("String"))

    @unittest.skip("Adding structs into structs is not currently supported.")
    def test_gff_add_inside_struct(self):
        # sourcery skip: extract-duplicate-method
        """Test that the add field modifiers are registered correctly."""
        pconfig, rconfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_struct

            [add_struct]
            FieldType=Struct
            Path=
            Label=SomeStruct
            TypeId=321
            AddField0=add_insidestruct

            [add_insidestruct]
            FieldType=Byte
            Path=
            Label=InsideStruct
            Value=0x123
            """
        )
        mod_0 = pconfig.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertEqual(mod_0.path.name, ">>##INDEXINLIST##<<")
        self.assertEqual("SomeStruct", mod_0.label)
        self.assertEqual(321, mod_0.value.stored.struct_id)

        mod_0_1 = mod_0.modifiers[0]
        self.assertIsInstance(mod_0_1, AddFieldGFF)
        assert isinstance(mod_0_1, AddFieldGFF)
        self.assertIsInstance(mod_0_1.value, FieldValueConstant)
        assert isinstance(mod_0_1.value, FieldValueConstant)
        self.assertEqual(mod_0_1.path.name, "SomeStruct")
        self.assertEqual("InsideStruct", mod_0_1.label)
        self.assertEqual(b'\x01#', mod_0_1.value.stored)

        memory = PatcherMemory()
        main_mod = ModificationsGFF("inside_struct_file.gff", False)
        main_mod.modifiers.append(mod_0)
        orig_gff = GFF()
        logger = PatchLogger()
        new_gff = read_gff(cast(bytes, main_mod.patch_resource(bytes_gff(orig_gff), memory, logger, Game.K1)))
        assert not logger.errors, "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs)
        SomeStruct = new_gff.root.get_struct("SomeStruct")
        InsideStruct = SomeStruct.get_binary("InsideStruct")
        assert InsideStruct == b'\x01#', "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs)

        mod_config = ModificationsGFF.create_patch(orig_gff, new_gff, filename="test_modify_field_List")
        gff3 = read_gff(cast(bytes, mod_config.patch_resource(bytes_gff(new_gff), memory, logger, Game.K1)))

        SomeStruct = gff3.root.get_struct("SomeStruct")
        InsideStruct = SomeStruct.get_binary("InsideStruct")
        assert InsideStruct == b'\x01#', "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs)
        
        

    def test_gff_add_inside_list(self):
        # sourcery skip: extract-duplicate-method
        """Test that the add field modifiers are registered correctly."""
        config, rconfig = self._setupIniAndConfig(
            """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=add_list

            [add_list]
            FieldType=List
            Path=
            Label=SomeList
            AddField0=add_insidelist

            [add_insidelist]
            FieldType=Struct
            Label=
            TypeId=111
            2DAMEMORY5=ListIndex
            AddField0=add_insidestruct

            [add_insidestruct]
            FieldType=Binary
            Path=
            Label=InsideStruct
            Value=0x123
            """
        )
        mod_0 = config.patches_gff[0].modifiers[0]
        self.assertIsInstance(mod_0, AddFieldGFF)
        assert isinstance(mod_0, AddFieldGFF)
        self.assertIsInstance(mod_0.value, FieldValueConstant)
        assert isinstance(mod_0.value, FieldValueConstant)
        self.assertFalse(mod_0.path.name)
        self.assertEqual("SomeList", mod_0.label)

        mod_0_0 = mod_0.modifiers[0]
        self.assertIsInstance(mod_0_0, AddStructToListGFF)
        assert isinstance(mod_0_0, AddStructToListGFF)
        self.assertIsInstance(mod_0_0.value, FieldValueConstant)
        assert isinstance(mod_0_0.value, FieldValueConstant)
        self.assertIsInstance(mod_0_0.value.value(None, GFFFieldType.Struct), GFFStruct)  # type: ignore[arg-type, reportGeneralTypeIssues]
        assert isinstance(mod_0_0.value.stored, GFFStruct)
        self.assertEqual(111, mod_0_0.value.stored.struct_id)
        self.assertEqual(5, mod_0_0.index_to_token)

        mod_0_0_0 = mod_0_0.modifiers[0]
        self.assertIsInstance(mod_0_0_0, AddFieldGFF)
        assert isinstance(mod_0_0_0, AddFieldGFF)
        self.assertIsInstance(mod_0_0_0.value, FieldValueConstant)
        assert isinstance(mod_0_0_0.value, FieldValueConstant)
        self.assertIsInstance(mod_0_0_0.value.value(None, GFFFieldType.Binary), bytes)  # type: ignore[arg-type, reportGeneralTypeIssues]
        assert isinstance(mod_0_0_0.value.stored, bytes)

        memory = PatcherMemory()
        main_mod = ModificationsGFF("inside_struct_file.gff", False)
        main_mod.modifiers.append(mod_0)
        orig_gff = GFF()
        logger = PatchLogger()
        new_gff = read_gff(cast(bytes, main_mod.patch_resource(bytes_gff(orig_gff), memory, logger, Game.K1)))
        assert not logger.errors, "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs)
        SomeStruct = new_gff.root.get_list("SomeList")
        InsideList = SomeStruct.at(0)
        assert isinstance(InsideList, GFFStruct), "\n".join(f'[{log.log_type}] {log.message}' for log in logger.all_logs)
        InsideStruct = InsideList.get_binary("InsideStruct")
        self.assertEqual(InsideStruct, b'\x01#')

        mod_config = ModificationsGFF.create_patch(orig_gff, new_gff, filename="test_modify_field_List")
        gff3 = read_gff(cast(bytes, mod_config.patch_resource(bytes_gff(new_gff), memory, logger, Game.K1)))
        assert new_gff == gff3

        self.assertIsNotNone(gff3.root.get_list("SomeList"))
        self.assertIsNotNone(gff3.root.get_list("SomeList").at(0))
        self.assertEqual(gff3.root.get_list("SomeList").at(0).get_binary("InsideStruct"), b'\x01#')  # type: ignore

    def _setupIniAndConfig(self, ini_text: str) -> tuple[PatcherConfig, ConfigReader]:
        ini = ConfigParser(delimiters="=", allow_no_value=True, strict=False, interpolation=None)
        ini.optionxform = lambda optionstr: optionstr
        ini.read_string(ini_text)
        pconfig = PatcherConfig()
        rconfig = ConfigReader(ini, "")
        rconfig.load(pconfig)
        return pconfig, rconfig

    def test_add_use_2damemory(self):
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddFieldGFF("", "String", GFFFieldType.String, FieldValue2DAMemory(5), PureWindowsPath("")))
        config.modifiers.append(AddFieldGFF("", "Integer", GFFFieldType.UInt8, FieldValue2DAMemory(5), PureWindowsPath("")))
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_add_use_tlkmemory(self):
        gff = GFF()

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddFieldGFF("", "String", GFFFieldType.String, FieldValueTLKMemory(5), PureWindowsPath("")))
        config.modifiers.append(AddFieldGFF("", "Integer", GFFFieldType.UInt8, FieldValueTLKMemory(5), PureWindowsPath("")))
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual("123", gff.root.get_string("String"))
        self.assertEqual(123, gff.root.get_uint8("Integer"))

    def test_add_field_locstring(self):
        """Adds a localized string field to a GFF using a 2DA memory reference

        Processing Logic:
        ----------------
            1. Creates a GFF object
            2. Sets a locstring field on the root node
            3. Populates the memory with a test string
            4. Creates an AddField modifier to add the Field1 locstring using the memory reference
            5. Applies the modifier to the GFF
            6. Checks that the locstring was set correctly from memory
        """
        gff = GFF()
        gff.root.set_locstring("Field1", LocalizedString(0))

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"
        modifiers: list[ModifyGFF] = [
            AddFieldGFF(
                "",
                "Field1",
                GFFFieldType.LocalizedString,
                FieldValueConstant(LocalizedStringDelta(FieldValue2DAMemory(5))),
                PureWindowsPath(""),
            )
        ]

        config = ModificationsGFF("", False, modifiers)
        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))

        self.assertEqual(123, gff.root.get_locstring("Field1").stringref)
        get_root_logger().debug("As ini: \n%s", config.as_gfflist_ini(ConfigParser()))

    def test_addlist_listindex(self):
        gff = GFF()
        gff_list = gff.root.set_list("List", GFFList())

        memory = PatcherMemory()

        config = ModificationsGFF("", False, [])
        config.modifiers.append(AddStructToListGFF("test1", FieldValueConstant(GFFStruct(5)), "List", None))
        config.modifiers.append(AddStructToListGFF("test2", FieldValueConstant(GFFStruct(3)), "List", None))
        config.modifiers.append(AddStructToListGFF("test3", FieldValueConstant(GFFStruct(1)), "List", None))

        gff = read_gff(cast(bytes, config.patch_resource(bytes_gff(gff), memory, PatchLogger(), Game.K1)))
        patched_gff_list = gff.root.get_list("List")

        self.assertEqual(5, patched_gff_list.at(0).struct_id)  # type: ignore
        self.assertEqual(3, patched_gff_list.at(1).struct_id)  # type: ignore
        self.assertEqual(1, patched_gff_list.at(2).struct_id)  # type: ignore
        get_root_logger().debug("As ini: \n%s", config.as_gfflist_ini(ConfigParser()))

    def test_addlist_store_2damemory(self):
        gff = GFF()
        gff.root.set_list("List", GFFList())

        memory = PatcherMemory()

        config = ModificationsGFF("test_2damemory.gff", False, [])
        config.modifiers.append(AddStructToListGFF("test1", FieldValueConstant(GFFStruct()), "List"))
        config.modifiers.append(AddStructToListGFF("test2", FieldValueConstant(GFFStruct()), "List", index_to_token=12))
        logger = PatchLogger()
        gff = read_gff(config.patch_resource(bytes_gff(gff), memory, logger, Game.K1))

        self.assertEqual("1", memory.memory_2da[12])
        logger.add_verbose("As ini: \n%s" + config.as_gfflist_ini(ConfigParser()))