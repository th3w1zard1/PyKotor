from __future__ import annotations

import io
import json
import uuid

from abc import ABC, abstractmethod
from itertools import zip_longest
from typing import TYPE_CHECKING, Any

import jsonpatch

from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff import GFF, GFFFieldType, GFFList, GFFStruct, bytes_gff
from pykotor.resource.formats.gff.gff_data import _GFFField
from pykotor.resource.formats.gff.io_gff import GFFBinaryReader
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.template import PatcherModifications
from utility.logger_util import get_root_logger
from utility.system.path import PureWindowsPath

if TYPE_CHECKING:
    import configparser
    import os

    from collections.abc import Callable
    from configparser import ConfigParser

    from jsonpatch import PatchOperation
    from typing_extensions import Literal, Self

    from pykotor.common.misc import Game
    from pykotor.resource.type import SOURCE_TYPES
    from pykotor.tslpatcher.logger import PatchLogger
    from utility.system.path import PurePath


def set_locstring(
    struct: GFFStruct,
    label: str,
    value: LocalizedStringDelta,
    memory: PatcherMemory,
):
    original = LocalizedString(0)
    value.apply(original, memory)
    struct.set_locstring(label, original)


FIELD_TYPE_TO_GETTER: dict[GFFFieldType, Callable[[GFFStruct, str], Any]] = {
    GFFFieldType.Int8: GFFStruct.get_int8,
    GFFFieldType.UInt8: GFFStruct.get_uint8,
    GFFFieldType.Int16: GFFStruct.get_int16,
    GFFFieldType.UInt16: GFFStruct.get_uint16,
    GFFFieldType.Int32: GFFStruct.get_int32,
    GFFFieldType.UInt32: GFFStruct.get_uint32,
    GFFFieldType.Int64: GFFStruct.get_int64,
    GFFFieldType.UInt64: GFFStruct.get_uint64,
    GFFFieldType.Single: GFFStruct.get_single,
    GFFFieldType.Double: GFFStruct.get_double,
    GFFFieldType.String: GFFStruct.get_string,
    GFFFieldType.ResRef: GFFStruct.get_resref,
    GFFFieldType.LocalizedString: GFFStruct.get_locstring,
    GFFFieldType.Vector3: GFFStruct.get_vector3,
    GFFFieldType.Vector4: GFFStruct.get_vector4,
    GFFFieldType.Binary: GFFStruct.get_binary,
    GFFFieldType.List: GFFStruct.get_list,
    GFFFieldType.Struct: GFFStruct.get_struct,
}


FIELD_TYPE_TO_SETTER: dict[GFFFieldType, Callable[[GFFStruct, str, Any, PatcherMemory]]] = {
    GFFFieldType.Int8: lambda s, lbl, v, _m: GFFStruct.set_int8(s, lbl, v),
    GFFFieldType.UInt8: lambda s, lbl, v, _m: GFFStruct.set_uint8(s, lbl, v),
    GFFFieldType.Int16: lambda s, lbl, v, _m: GFFStruct.set_int16(s, lbl, v),
    GFFFieldType.UInt16: lambda s, lbl, v, _m: GFFStruct.set_uint16(s, lbl, v),
    GFFFieldType.Int32: lambda s, lbl, v, _m: GFFStruct.set_int32(s, lbl, v),
    GFFFieldType.UInt32: lambda s, lbl, v, _m: GFFStruct.set_uint32(s, lbl, v),
    GFFFieldType.Int64: lambda s, lbl, v, _m: GFFStruct.set_int64(s, lbl, v),
    GFFFieldType.UInt64: lambda s, lbl, v, _m: GFFStruct.set_uint64(s, lbl, v),
    GFFFieldType.Single: lambda s, lbl, v, _m: GFFStruct.set_single(s, lbl, v),
    GFFFieldType.Double: lambda s, lbl, v, _m: GFFStruct.set_double(s, lbl, v),
    GFFFieldType.String: lambda s, lbl, v, _m: GFFStruct.set_string(s, lbl, v),
    GFFFieldType.ResRef: lambda s, lbl, v, _m: GFFStruct.set_resref(s, lbl, v),
    GFFFieldType.LocalizedString: set_locstring,
    GFFFieldType.Vector3: lambda s, lbl, v, _m: GFFStruct.set_vector3(s, lbl, v),
    GFFFieldType.Vector4: lambda s, lbl, v, _m: GFFStruct.set_vector4(s, lbl, v),
    GFFFieldType.Binary: lambda s, lbl, v, _m: GFFStruct.set_binary(s, lbl, v),
    GFFFieldType.List: lambda s, lbl, v, _m: GFFStruct.set_list(s, lbl, v),
    GFFFieldType.Struct: lambda s, lbl, v, _m: GFFStruct.set_struct(s, lbl, v),
}


class LocalizedStringDelta(LocalizedString):
    def __init__(self, stringref: FieldValue | None = None):
        super().__init__(0)
        self.stringref: FieldValue | None = stringref

    def __str__(self):
        return f"LocalizedString(stringref={self.stringref!r})"

    def apply(self, locstring: LocalizedString, memory: PatcherMemory):
        """Applies a LocalizedString patch to a LocalizedString object.

        Args:
        ----
            locstring: LocalizedString object to apply patch to
            memory: PatcherMemory object for resolving references

        Processing Logic:
        ----------------
            - Checks if stringref is set and sets locstring stringref if so
            - Iterates through tuple returned from function and sets language, gender and text on locstring.
        """
        if self.stringref is not None:
            locstring.stringref = self.stringref.value(memory, GFFFieldType.UInt32)
        for language, gender, text in self:
            locstring.set_data(language, gender, text)


# region Value Returners
class FieldValue(ABC):
    @abstractmethod
    def value(self, memory: PatcherMemory, field_type: GFFFieldType) -> Any: ...

    def validate(self, value: Any, field_type: GFFFieldType) -> ResRef | str | PureWindowsPath | int | float | object:
        """Validate a value based on its field type.

        Args:
        ----
            value: The value to validate
            field_type: The field type to validate against

        Returns:
        -------
            value: The validated value

        Processing Logic:
        ----------------
            - Check if value matches field type
            - Convert value to expected type if needed
            - Return validated value
        """
        if isinstance(value, PureWindowsPath):  # !FieldPath
            return value
        if field_type == GFFFieldType.ResRef and not isinstance(value, ResRef):
            value = (  # This is here to support empty statements like 'resref=' in ini (allow_no_entries=True in configparser)
                ResRef(str(value)) if not isinstance(value, str) or value.strip() else ResRef.from_blank()
            )
        elif field_type == GFFFieldType.String and not isinstance(value, str):
            value = str(value)
        elif issubclass(field_type.return_type(), int) and isinstance(value, str):
            value = int(value) if value.strip() else "0"
        elif issubclass(field_type.return_type(), float) and isinstance(value, str):
            value = float(value) if value.strip() else "0.0"
        return value


class FieldValueConstant(FieldValue):
    def __init__(self, value: Any):
        self.stored: Any = value

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):  # noqa: ANN201
        return self.validate(self.stored, field_type)


class FieldValue2DAMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):  # noqa: ANN201
        memory_val: str | PureWindowsPath | None = memory.memory_2da.get(self.token_id, None)
        if memory_val is None:
            msg = f"2DAMEMORY{self.token_id} was not defined before use"
            raise KeyError(msg)
        return self.validate(memory_val, field_type)


class FieldValueTLKMemory(FieldValue):
    def __init__(self, token_id: int):
        self.token_id: int = token_id

    def value(self, memory: PatcherMemory, field_type: GFFFieldType):  # noqa: ANN201
        memory_val: int | None = memory.memory_str.get(self.token_id, None)
        if memory_val is None:
            msg = f"StrRef{self.token_id} was not defined before use!"
            raise KeyError(msg)
        return self.validate(memory_val, field_type)


# endregion


# region Modify GFF
class ModifyGFF(ABC):
    def __init__(self):
        self.path: PureWindowsPath
    @abstractmethod
    def apply(
        self,
        root_container: GFFStruct | GFFList,
        memory: PatcherMemory,
        logger: PatchLogger,
    ): ...

    @staticmethod
    def _navigate_containers(
        root_container: GFFStruct,
        path: PureWindowsPath | os.PathLike | str,
    ) -> GFFList | GFFStruct | None:
        """Navigates through gff lists/structs to find the specified path.

        Args:
        ----
            root_container (GFFStruct): The root container to start navigation

        Returns:
        -------
            container (GFFList | GFFStruct | None): The container at the end of the path or None if not found

        Processing Logic:
        ----------------
            - It checks if the path is valid PureWindowsPath
            - Loops through each part of the path
            - Acquires the container at each step from the parent container
            - Returns the container at the end or None if not found along the path
        """
        path = PureWindowsPath.pathify(path)
        if not path.name:
            return root_container
        container: GFFStruct | GFFList | None = root_container
        for step in path.parts:
            if isinstance(container, GFFStruct):
                container = container.acquire(step, None, (GFFStruct, GFFList))
            elif isinstance(container, GFFList):
                container = container.at(int(step))

        return container

    @classmethod
    def _navigate_to_field(
        cls,
        root_container: GFFStruct,
        path: PureWindowsPath | os.PathLike | str,
    ) -> _GFFField | None:
        """Navigates to a field from the root gff struct from a path."""
        path = PureWindowsPath.pathify(path)
        container: GFFList | GFFStruct | None = cls._navigate_containers(root_container, path.parent)
        label: str = path.name

        # Return the field if the container is a GFFStruct
        return container._fields[label] if isinstance(container, GFFStruct) else None


class AddStructToListGFF(ModifyGFF):
    def __init__(
        self,
        identifier: str,
        value: FieldValue,
        path: PureWindowsPath | os.PathLike | str,
        index_to_token: int | None = None,
        modifiers: list[ModifyGFF] | None = None,
    ):
        """Initialize a addfield patch that creates a new struct into an existing list.

        Args:
        ----
            identifier (str): INI section name
            value (FieldValue): Field value object
            path (PureWindowsPath): File path
            index_to_token (int | None): Token index
            modifiers (list[ModifyGFF]): Modifiers list
        """
        self.identifier: str = identifier
        self.value: FieldValue = value
        self.path: PureWindowsPath = PureWindowsPath.pathify(path)
        self.index_to_token: int | None = index_to_token

        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(
        self,
        root_struct: GFFStruct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        """Adds a new struct to a list.

        Args:
        ----
            root_struct: The root struct to navigate and modify.
            memory: The memory object to read/write values from.
            logger: The logger to log errors or warnings.

        Processing Logic:
        ----------------
            1. Navigates to the target list container using the provided path.
            2. Checks if the navigated container is a list, otherwise logs an error.
            3. Creates a new struct and adds it to the list.
            4. Applies any additional field modifications specified in the modifiers.
        """
        list_container: GFFList | None = None
        if self.path.name == ">>##INDEXINLIST##<<":
            #logger.add_verbose(f"Removing unique sentinel from AddStructToListGFF instance (ini section [{self.identifier}]). Path: '{self.path}'")
            self.path = self.path.parent  # HACK: idk why conditional parenting is necessary but it works
            logger.add_verbose(f"Removed unique sentinel from AddStructToListGFF instance (ini section [{self.identifier}]). Path: '{self.path}'")
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_struct, self.path) if self.path.name else root_struct
        if navigated_container is root_struct:
            logger.add_note(f"GFF path '{self.path}' not found, defaulting to the gff root struct.")
        if isinstance(navigated_container, GFFList):
            list_container = navigated_container
        else:
            reason: str = "Does not exist" if navigated_container is None else f"Path points to a '{navigated_container.__class__.__name__}', expected a GFFList."
            logger.add_error(f"Unable to add struct to list '{self.path or f'[{self.identifier}]'}': {reason}")
            return

        try:
            new_struct = self.value.value(memory, GFFFieldType.Struct)
        except KeyError as e:
            logger.add_error(f"INI section [{self.identifier}] threw an exception: {e}")

        if not isinstance(new_struct, GFFStruct):
            logger.add_error(f"Failed to add a new struct to list '{self.path}' in [{self.identifier}]. Reason: Expected GFFStruct but got '{new_struct}' ({new_struct!r}) of type {type(new_struct).__name__} Skipping...")
            return

        list_container._structs.append(new_struct)
        if self.index_to_token is not None:
            length = str(len(list_container) - 1)
            logger.add_verbose(f"Set 2DAMEMORY{self.index_to_token}={length}")
            memory.memory_2da[self.index_to_token] = length

        for add_field in self.modifiers:
            assert isinstance(add_field, (AddFieldGFF, AddStructToListGFF, Memory2DAModifierGFF, ModifyFieldGFF)), f"{type(add_field).__name__}: {add_field}"
            newpath = self.path / str(len(list_container) - 1)
            #logger.add_verbose(f"Resolved GFFList path of [{add_field.identifier}] from '{add_field.path}' --> '{newpath}'")
            add_field.path = newpath
            add_field.apply(root_struct, memory, logger)


class AddFieldGFF(ModifyGFF):
    def __init__(
        self,
        identifier: str,
        label: str,
        field_type: GFFFieldType,
        value: FieldValue,
        path: PureWindowsPath | os.PathLike | str,
        modifiers: list[ModifyGFF] | None = None,
    ):
        self.identifier: str = identifier
        self.label: str = label
        self.field_type: GFFFieldType = field_type
        self.value: FieldValue = value
        self.path: PureWindowsPath = PureWindowsPath.pathify(path)

        self.modifiers: list[ModifyGFF] = [] if modifiers is None else modifiers

    def apply(
        self,
        root_struct: GFFStruct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        """Adds a new field to a GFF struct.

        Args:
        ----
            root_struct: GFFStruct - The root GFF struct to navigate and modify.
            memory: PatcherMemory - The memory state to read values from.
            logger: PatchLogger - The logger to record errors to.

        Processing Logic:
        ----------------
            - Navigates to the specified container path and gets the GFFStruct instance
            - Resolves the field value using the provided value expression
            - Resolves the value path if part of !FieldPath memory
            - Sets the field on the struct instance using the appropriate setter based on field type
            - Applies any modifier patches recursively
        """
        #logger.add_verbose(f"Apply patch from INI section [{self.identifier}] FieldType: {self.field_type.name} GFF Path: '{self.path}'")
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_struct, self.path)
        if isinstance(navigated_container, GFFStruct):
            struct_container = navigated_container
        else:
            reason = "path does not exist!" if navigated_container is None else "is not an instance of a GFFStruct."
            logger.add_error(f"Unable to add new GFF Field '{self.label}' at GFF Path '{self.path}'! This {reason}")
            return

        value: Any = self.value.value(memory, self.field_type)

        # if 2DAMEMORY holds a path from !FieldPath, navigate to that field and use its value.
        if isinstance(value, PureWindowsPath):
            stored_fieldpath: PureWindowsPath = value
            if isinstance(self.value, FieldValue2DAMemory):
                logger.add_verbose(f"Looking up field pointer of stored !FieldPath ({stored_fieldpath}) in 2DAMEMORY{self.value.token_id}")
            else:
                logger.add_verbose(f'Found PureWindowsPath object in value() lookup from non-FieldValue2DAMemory object? Path: "{stored_fieldpath}" INI section: [{self.identifier}]')
            from_container: GFFList | GFFStruct | None = self._navigate_containers(root_struct, stored_fieldpath.parent)
            if not isinstance(from_container, GFFStruct):
                reason = "does not exist!" if from_container is None else "is not an instance of a GFFStruct."
                logger.add_error(f"Unable to use !FieldPath from 2DAMEMORY. Parent field at '{stored_fieldpath}' {reason}")
                return
            value = from_container.value(value.name)
            logger.add_verbose(f"Acquired value '{value}' from 2DAMEMORY !FieldPath({stored_fieldpath})")

        logger.add_verbose(f"AddField: Creating field of type '{self.field_type.name}' value: '{value}' at GFF path '{self.path}'. INI section: [{self.identifier}]")
        FIELD_TYPE_TO_SETTER[self.field_type](struct_container, self.label, value, memory)

        for add_field in self.modifiers:
            assert isinstance(add_field, (AddFieldGFF, AddStructToListGFF, ModifyFieldGFF, Memory2DAModifierGFF)), f"{type(add_field).__name__}: {add_field}"

            # HACK: resolves any >>##INDEXINLIST##<<, not sure why lengths aren't the same though (ziplongest)? Whatever, it works.
            newpath = PureWindowsPath("")
            for part, resolvedpart in zip_longest(add_field.path.parts, self.path.parts):
                newpath /= resolvedpart or part
            #logger.add_verbose(f"Resolved gff path of INI section [{add_field.identifier}] from relative '{add_field.path}' --> absolute '{newpath}'")
            add_field.path = newpath

            add_field.apply(root_struct, memory, logger)


class Memory2DAModifierGFF(ModifyGFF):
    """A modifier class used for !FieldPath support."""

    def __init__(
        self,
        identifier: str,
        index_2damemory: int,
        path: PureWindowsPath | os.PathLike | str,
    ):
        self.identifier: str = identifier
        self.index_2damemory: int = index_2damemory
        self.path: PureWindowsPath = PureWindowsPath.pathify(path)

    def apply(
        self,
        root_struct: GFFStruct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        memory.memory_2da[self.index_2damemory] = self.path


class ModifyFieldGFF(ModifyGFF):
    def __init__(
        self,
        path: PureWindowsPath | os.PathLike | str,
        value: FieldValue,
        identifier: str = ""
    ):
        self.path: PureWindowsPath = PureWindowsPath.pathify(path)
        self.value: FieldValue = value
        self.identifier: str = identifier

    def apply(
        self,
        root_struct: GFFStruct,
        memory: PatcherMemory,
        logger: PatchLogger,
    ):
        """Applies a patch to an existing field in a GFF structure.

        Args:
        ----
            root_struct: {GFF structure}: Root GFF structure to navigate and modify
            memory: {PatcherMemory}: Memory context to retrieve values
            logger: {PatchLogger}: Logger to record errors

        Processing Logic:
        ----------------
            - Navigates container hierarchy to the parent of the field using the patch path
            - Checks if parent container exists and is a GFFStruct
            - Gets the field type from the parent struct
            - Converts the patch value to the correct type
            - Calls the corresponding setter method on the parent struct
        """
        label: str = self.path.name
        navigated_container: GFFList | GFFStruct | None = self._navigate_containers(root_struct, self.path.parent)
        if not isinstance(navigated_container, GFFStruct):
            reason: str = "does not exist!" if navigated_container is None else "is not an instance of a GFFStruct."
            logger.add_error(f"Unable to modify GFF field '{label}'. Path '{self.path}' {reason}")
            return

        navigated_struct: GFFStruct = navigated_container
        field_type: GFFFieldType = navigated_struct._fields[label].field_type()

        value: Any = self.value.value(memory, field_type)

        # if 2DAMEMORY holds a path from !FieldPath, navigate to that field and use its value.
        if isinstance(value, PureWindowsPath):
            stored_fieldpath: PureWindowsPath = value
            if isinstance(self.value, FieldValue2DAMemory):
                logger.add_verbose(f"Looking up field pointer of stored !FieldPath ({stored_fieldpath}) in 2DAMEMORY{self.value.token_id}")
            else:
                logger.add_verbose(f'Found PureWindowsPath object in value() lookup from non-FieldValue2DAMemory object? Path: "{stored_fieldpath}" INI section: [{self.identifier}]')
            from_container: GFFList | GFFStruct | None = self._navigate_containers(root_struct, value.parent)
            if not isinstance(from_container, GFFStruct):
                reason = "does not exist!" if from_container is None else "is not an instance of a GFFStruct."
                logger.add_error(f"Unable use !FieldPath from 2DAMEMORY. Parent field at '{value.parent}' {reason}")
                return
            value = from_container.value(value.name)
            logger.add_verbose(f"Acquired value '{value}' from field at !FieldPath '{stored_fieldpath}'")

        try:
            orig_value = FIELD_TYPE_TO_GETTER[field_type](navigated_struct, label)
            logger.add_verbose(f"Found original value of '{orig_value}' ({orig_value!r}) at GFF Path {self.path}: Patch section: [{self.identifier}]")
        except KeyError:
            msg = (
                f"The field {field_type.name} did not exist at {self.path} in INI section [{self.identifier}]. Use AddField if you need to create fields/structs."
                "\nDue to the above error, no value will be set here."
            )
            get_root_logger().exception(msg)
            logger.add_error(msg)
            return

        logger.add_verbose(f"Direct set value of determined field type '{field_type.name}' at GFF path '{self.path}' to new value '{value}'. INI section: [{self.identifier}]")
        if field_type is not GFFFieldType.LocalizedString:
            FIELD_TYPE_TO_SETTER[field_type](navigated_struct, label, value, memory)
            return

        assert isinstance(value, LocalizedString), f"{type(value).__name__}: {value}"
        if not navigated_struct.exists(label):
            navigated_struct.set_locstring(label, value)
        else:
            assert isinstance(value, LocalizedStringDelta), f"{type(value).__name__}: {value}"
            original: LocalizedString = navigated_struct.get_locstring(label)
            value.apply(original, memory)
            navigated_struct.set_locstring(label, original)


# endregion

def get_value_by_path(nested_dict: dict[str, Any], path: PurePath) -> Any:
    """Retrieves a value from a nested dictionary using a PurePath object for navigation.

    :param nested_dict: The nested dictionary to traverse.
    :param path: A PurePath object representing the keys path to the desired value.
    :return: The value found at the specified path within the nested dictionary.
    """
    def handle(part, current_value):
        if isinstance(current_value, list):
            part = int(part)
            return current_value[part]
        elif isinstance(current_value, dict) and part in current_value:
            return current_value[part]
        else:
            #HACK: fix later
            if part.isdigit():
                return current_value
            raise KeyError(f"Path {path} not found in the nested dictionary, could not find part '{part}'")
    current_value = nested_dict
    for parent in reversed(path.parents):
        part = parent.name
        if not part:  # skip the / top level.
            continue
        current_value = handle(part, current_value)
    return handle(path.name, current_value)

class ModificationsGFF(PatcherModifications):
    def __init__(
        self,
        filename: str,
        replace: bool,  # noqa: FBT001
        modifiers: list[ModifyGFF] | None = None,
    ):
        super().__init__(filename, replace)
        self.modifiers: list[ModifyGFF] = modifiers if modifiers is not None else []

    def _handle_addfield_value(
        self,
        config: configparser.ConfigParser,
        modifier: AddFieldGFF,
        identifier: str,
        relpath: PureWindowsPath,
        memory: PatcherMemory,
        new_identifier: str,
    ):
        assert isinstance(modifier, AddFieldGFF)
        modifier_value = modifier.value
        if not isinstance(modifier_value, FieldValueConstant):
            raise TypeError(f"Unsupported FieldValue instance: {modifier_value} ({modifier_value!r}) of type {type(modifier_value).__name__}")
        if isinstance(modifier_value.stored, LocalizedStringDelta):
            self._handle_locstring(modifier_value, config, identifier, relpath)
        elif isinstance(modifier_value.stored, PureWindowsPath):
            rval = str(modifier_value.stored)
            assert "object at 0x" not in rval, rval
            new_memory_index = len(memory.memory_2da)
            config.set(identifier, f"2DAMEMORY{new_memory_index}", rval)
        elif isinstance(modifier_value, FieldValue2DAMemory):
            rval = str(modifier_value.token_id)
            assert "object at 0x" not in rval, rval
            new_memory_index = len(memory.memory_2da)
            memory.memory_2da[new_memory_index] = rval
            config.set(identifier, f"2DAMEMORY{new_memory_index}", rval)
        elif isinstance(modifier_value, FieldValueTLKMemory):
            rval = str(modifier_value.token_id)
            assert "object at 0x" not in rval, rval
            new_memory_index = len(memory.memory_str)
            memory.memory_str[new_memory_index] = modifier_value.token_id
            config.set(identifier, f"StrRef{new_memory_index}", rval)
        elif isinstance(modifier, ModifyFieldGFF) or modifier.field_type not in (
            GFFFieldType.List,
            GFFFieldType.Struct,
        ):
            assert "object at 0x" not in str(modifier_value.stored), str(modifier_value.stored)
            config.set(new_identifier, "Value", str(modifier_value.stored))

    def _handle_modifyfield_value(
        self,
        config: configparser.ConfigParser,
        modifier: ModifyFieldGFF,
        identifier: str,
        relpath: PureWindowsPath,
        memory: PatcherMemory,
        inside_list: int | None = None,
    ):
        modifier_value = modifier.value
        if isinstance(modifier_value, FieldValueConstant):
            if isinstance(modifier_value.stored, LocalizedStringDelta):
                relpath = relpath / str(inside_list) if inside_list is not None else relpath
                self._handle_locstring(modifier_value, config, identifier, relpath)
            elif isinstance(modifier_value.stored, PureWindowsPath):
                rval = str(modifier_value.stored)
                assert "object at 0x" not in rval, rval
                new_memory_index = len(memory.memory_2da)
                config.set(identifier, f"2DAMEMORY{new_memory_index}", rval)
            else:
                rval = str(modifier_value.stored)
                assert "object at 0x" not in rval, rval
                config.set(identifier, f"{relpath}", rval)
        elif isinstance(modifier_value, FieldValue2DAMemory):
            rval = str(modifier_value.token_id)
            assert "object at 0x" not in rval, rval
            new_memory_index = len(memory.memory_2da)
            memory.memory_2da[new_memory_index] = rval
            config.set(identifier, f"2DAMEMORY{new_memory_index}", rval)
        elif isinstance(modifier_value, FieldValueTLKMemory):
            rval = str(modifier_value.token_id)
            assert "object at 0x" not in rval, rval
            new_memory_index = len(memory.memory_str)
            memory.memory_str[new_memory_index] = modifier_value.token_id
            config.set(identifier, f"StrRef{new_memory_index}", rval)
        else:
            raise TypeError(f"Unsupported FieldValue instance: {modifier_value} ({modifier_value!r}) of type {type(modifier_value).__name__}")

    def _handle_locstring(
        self,
        modifier_value: FieldValueConstant,
        config: ConfigParser,
        identifier: str,
        relpath: PureWindowsPath,
        label: str = "",
    ):
        if label and label.strip():
            relpath = relpath / label
        locstring: LocalizedString = modifier_value.stored
        if isinstance(locstring.stringref, FieldValueTLKMemory):
            rval = f"StrRef{locstring.stringref.token_id}"
        elif isinstance(locstring.stringref, FieldValueConstant):
            rval = f"StrRef{locstring.stringref.stored}"
        else:
            rval = f"StrRef{locstring.stringref}"
        assert "object at 0x" not in rval, rval
        config.set(identifier, f"{relpath}(strref)", rval)
        for i, substring_id in enumerate(locstring._substrings):
            config.set(identifier, f"{relpath}(lang={i})", str(substring_id))

    def _recurse_modifier(
        self,
        config: configparser.ConfigParser,
        modify_list: list[ModifyGFF],
        identifier: str,
        memory: PatcherMemory,
        inside_list: int | None = None,
    ):
        for i, modifier in enumerate(modify_list):
            assert isinstance(modifier, (AddFieldGFF, AddStructToListGFF, ModifyFieldGFF))
            path = modifier.path.parent.joinpath("ListIndex") if modifier.path.name == ">>##INDEXINLIST##<<" else modifier.path
            relpath = (
                path.relative_to(path.parents[[parent.name for parent in path.parents].index(">>##INDEXINLIST##<<")])
                if ">>##INDEXINLIST##<<" in path.parts
                else path
            )

            if isinstance(modifier, AddFieldGFF):
                fieldtype_to_fieldname = {
                    GFFFieldType.UInt8: "Byte",
                    GFFFieldType.Int8: "Char",
                    GFFFieldType.UInt16: "Word",
                    GFFFieldType.Int16: "Short",
                    GFFFieldType.UInt32: "DWORD",
                    GFFFieldType.Int32: "Int",
                    GFFFieldType.Int64: "Int64",
                    GFFFieldType.Single: "Float",
                    GFFFieldType.Double: "Double",
                    GFFFieldType.String: "ExoString",
                    GFFFieldType.ResRef: "ResRef",
                    GFFFieldType.LocalizedString: "ExoLocString",
                    GFFFieldType.Vector3: "Position",
                    GFFFieldType.Vector4: "Orientation",
                    GFFFieldType.Struct: "Struct",
                    GFFFieldType.List: "List",
                }
                field_name = fieldtype_to_fieldname[modifier.field_type]
                new_identifier = modifier.identifier.replace(".", "_") + uuid.uuid4().hex[:5]
                config.add_section(new_identifier)
                config.set(identifier, f"AddField{i}", new_identifier)
                config.set(new_identifier, "FieldType", field_name)
                modifier_value = modifier.value
                self._handle_addfield_value(config, modifier, identifier, relpath, memory, new_identifier)
                config.set(new_identifier, "Label", modifier.label)
                self._recurse_modifier(config, modifier.modifiers, new_identifier, memory)
            elif isinstance(modifier, ModifyFieldGFF):
                self._handle_modifyfield_value(config, modifier, identifier, relpath, memory, inside_list)
            elif isinstance(modifier, AddStructToListGFF):
                new_identifier = modifier.identifier.replace(".", "_") + uuid.uuid4().hex[:5]
                config.set(identifier, f"AddField{i}", new_identifier)
                config.add_section(new_identifier)
                config.set(new_identifier, "FieldType", "Struct")
                config.set(new_identifier, "Label", "")
                modifier_value = modifier.value.value(memory, GFFFieldType.Struct)
                if isinstance(modifier_value, GFFStruct):
                    config.set(new_identifier, "TypeId", str(modifier_value.struct_id))
                self._recurse_modifier(config, modifier.modifiers, new_identifier, memory, inside_list=modifier_value.struct_id)
            else:
                raise TypeError(f"{type(modifier_value).__name__}{modifier_value}: ({modifier_value!r})")

    def as_gfflist_ini(self, config: configparser.ConfigParser) -> str:
        if "GFFList" not in config.sections():
            config.add_section("GFFList")
        config.set("GFFList", "File", self.sourcefile)
        config.add_section(self.sourcefile)
        config.set("GFFList", "!Filename", self.saveas)
        config.set(self.sourcefile, "!SourceFile", self.sourcefile)
        config.set(self.sourcefile, "!SourceFolder", self.sourcefolder)
        config.set(self.sourcefile, "!Destination", self.destination)
        config.set(self.sourcefile, "!OverrideType", self.override_type)
        self._recurse_modifier(config, self.modifiers, self.sourcefile, PatcherMemory())  # noqa: FBT003
        output = io.StringIO()
        config.write(output)
        return output.getvalue()

    @classmethod
    def create_patch(cls, old: GFF, new: GFF, filename: str, replace_file: bool = False) -> Self:
        # sourcery skip: move-assign, remove-unnecessary-else, swap-if-else-branches
        """Returns a ModificationsGFF instance representing the ini sections for each patch."""
        from jsonpatch import AddOperation, JsonPatch, ReplaceOperation

        from utility.error_handling import safe_repr
        assert isinstance(old, GFF), f"{type(old).__name__}: {old} ({old!r})"
        assert isinstance(new, GFF), f"{type(new).__name__}: {new} ({new!r})"
        if old.content is not new.content:
            raise ValueError(f"The two gffs passed to this function must be of the same type (dlg, utc, etc) old's content: {old.content.name}, new's content: {new.content.name}")

        old_serialized = old.as_dict()
        new_serialized = new.as_dict()
        patch = JsonPatch.from_diff(old_serialized, new_serialized)
        log = get_root_logger()
        log.info("Created patch: %s", json.dumps(patch.patch, indent=4))
        new_instance = cls(filename, replace=replace_file)
        for raw_operation in patch.patch:
            op: PatchOperation = patch._get_operation(raw_operation)
            log.debug("Path: %s Location: %s Pointer: %s Key: %s Operation: %s", op.path, op.location, op.pointer, op.key, op.operation)
            op_path: PureWindowsPath = PureWindowsPath(op.location)
            if op_path.parent.name == "substrings":
                log.warning("Skipping op for path %s", op_path)
                continue
            if isinstance(op, AddOperation):
                op_path = op_path / ">>##VALUE##<<"
            if op_path.name not in (">>##TYPE##<<", ">>##VALUE##<<"):
                if op_path.parent.name in (">>##TYPE##<<", ">>##VALUE##<<"):
                    log.info("Using parent path of %s as actual op path.", op_path)
                    op_path = op_path.parent
                else:
                    op_path /= ">>##PLACEHOLDER##<<"
                    #raise ValueError(f"op_path not expected: {op_path}")
            changed_field_path: PureWindowsPath = op_path.parent
            field_label: str = changed_field_path.name
            try:
                serialized_field = get_value_by_path(new_serialized, changed_field_path)
            except KeyError as e: # it's in the other gff.
                try:
                    serialized_field = get_value_by_path(old_serialized, changed_field_path)
                except KeyError as e2:
                    raise KeyError("Somehow the key wasn't found in either new_serialized or old_serialized?") from e2
            if not serialized_field:
                log.warning("Somehow got no serialized field. Path %s led to a blank dict.", changed_field_path)
                continue
            gff_field = _GFFField.from_serializable(serialized_field)
            log.debug("ReplaceOp, lookup from old. Path: %s  Field: %s", changed_field_path, safe_repr(gff_field))
            field_value = gff_field.value()
            if isinstance(field_value, LocalizedString):
                field_value = LocalizedStringDelta(FieldValueConstant(field_value.stringref))
            modify_path = changed_field_path.relative_to("/root/>>##FIELDS##<<")
            if modify_path.parent.name == ">>##FIELDS##<<":
                new_parts = (part for part in modify_path.parts if part not in (">>##VALUE##<<", ">>##FIELDS##<<"))
                new_modify_path = PureWindowsPath("\\".join(new_parts))
                log.info("Sanitizing path %s --> %s", modify_path, new_modify_path)
                modify_path = new_modify_path
            if isinstance(op, ReplaceOperation):
                modifier = ModifyFieldGFF(modify_path, FieldValueConstant(field_value), identifier=f"{filename}_{field_label}")
                log.info("Created REPLACE modifier: %s", safe_repr(modifier))
                new_instance.modifiers.append(modifier)
            elif isinstance(op, AddOperation):
                modifier = AddFieldGFF(f"{filename}_{field_label}", modify_path.name, gff_field.field_type(), FieldValueConstant(field_value), path=modify_path.parent)
                log.info("Created ADD modifier: %s", safe_repr(modifier))
                new_instance.modifiers.append(modifier)
            else:
                msg = f"The operation '{op.operation['op']}' is unsupported at this time (path={modify_path})."
                get_root_logger().error(msg)
                #raise NotImplementedError(msg)
        return new_instance

    @classmethod
    def revert_patch(cls, old: GFF, new: GFF, filename: str, replace_file: bool = False):
        from jsonpatch import AddOperation, JsonPatch, RemoveOperation, ReplaceOperation

        from utility.error_handling import safe_repr
        assert isinstance(old, GFF) and isinstance(new, GFF), "Arguments must be GFF instances"
        if old.content is not new.content:
            raise ValueError("The GFFs must be of the same type")

        # Serialize the 'new' and 'old' states to dictionaries for comparison
        new_serialized = new.as_dict()
        old_serialized = old.as_dict()

        # Generate a patch to transform 'new' back into 'old'
        patch = JsonPatch.from_diff(new_serialized, old_serialized)
        log = get_root_logger()
        new_instance = cls(filename, replace=replace_file)

        for raw_operation in patch.patch:
            op = patch._get_operation(raw_operation)
            op_path = PureWindowsPath(op.location)
            # Reverse the operation logic: Add becomes Remove, Replace stays, and Remove becomes Add
            if isinstance(op, AddOperation):
                # For AddOperation in reverse, we need to remove the added element
                modifier = RemoveFieldGFF(f"{filename}_{op_path.name}", path=op_path.parent)
            elif isinstance(op, ReplaceOperation):
                # ReplaceOperation is symmetric; we just need to swap old and new values
                changed_field_path = op_path.parent
                serialized_field = get_value_by_path(old_serialized, changed_field_path)
                gff_field = _GFFField.from_serializable(serialized_field)
                field_value = gff_field.value()
                if isinstance(field_value, LocalizedString):
                    field_value = LocalizedStringDelta(FieldValueConstant(field_value.stringref))
                modify_path = changed_field_path.relative_to("/root/>>##FIELDS##<<")
                modifier = ModifyFieldGFF(modify_path, FieldValueConstant(field_value), identifier=f"{filename}_{op_path.name}")
            elif isinstance(op, RemoveOperation):
                # For RemoveOperation in reverse, we need to add the removed element back
                serialized_field = get_value_by_path(old_serialized, op_path)
                gff_field = _GFFField.from_serializable(serialized_field)
                field_value = gff_field.value()
                if isinstance(field_value, LocalizedString):
                    field_value = LocalizedStringDelta(FieldValueConstant(field_value.stringref))
                modify_path = op_path.relative_to("/root/>>##FIELDS##<<")
                modifier = AddFieldGFF(f"{filename}_{op_path.name}", modify_path.name, gff_field.field_type(), FieldValueConstant(field_value), path=modify_path.parent)
            else:
                raise NotImplementedError(f"Unsupported operation '{op.operation['op']}' for revert_patch")

            log.info("Created modifier: %s", safe_repr(modifier))
            new_instance.modifiers.append(modifier)

        return new_instance

    @staticmethod
    def old_revert_patch(old, new):
        patched_old_to_new = patch.apply(old_serialized)
        patched_diff = DeepDiff(new_serialized, patched_old_to_new, ignore_order=True)
        assert new_serialized == patched_old_to_new, f"\n\nDeepDiff Output: {json.dumps(patched_diff, indent=8)}\n\n"

        revert = jsonpatch.make_patch(new_serialized, old_serialized)
        reverted_new_to_old = revert.apply(new_serialized)
        reverted_diff = DeepDiff(old_serialized, patched_old_to_new, ignore_order=True)
        assert old_serialized == reverted_new_to_old, f"\n\nDeepDiff Output: {json.dumps(reverted_diff, indent=8)}\n\n"

        deserialized_old = GFF.from_dict(old_serialized)
        assert deserialized_old.content == gff.content, f"{deserialized_old.content} --> {gff.content}"
        diff = DeepDiff(gff.root._fields, deserialized_old.root._fields)
        assert not diff, f"\n\nDeepDiff Output: {json.dumps(diff, indent=8)}\n\n"
        self.assertTrue(gff.compare(deserialized_old), os.linesep.join(self.log_messages))
        assert gff == deserialized_old, "__eq__ assertion failed."

    def patch_resource(
        self,
        source_gff: SOURCE_TYPES,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ) -> bytes | Literal[True]:
        gff: GFF = GFFBinaryReader(source_gff).load()
        self.apply(gff, memory, logger, game)
        return bytes_gff(gff)

    def apply(
        self,
        gff: GFF,
        memory: PatcherMemory,
        logger: PatchLogger,
        game: Game,
    ):
        for change_field in self.modifiers:
            change_field.apply(gff.root, memory, logger)
