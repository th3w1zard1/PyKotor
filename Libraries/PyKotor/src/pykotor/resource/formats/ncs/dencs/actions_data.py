from __future__ import annotations

import re

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]

class Action:
    def __init__(self, type_str: str, name: str, params: str):
        self._name: str = name
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self._returntype = Type.parse_type(type_str)
        self._paramlist: list[Type] = []
        self._paramsize: int = 0
        p = re.compile(r"\s*(\w+)\s+\w+(\s*=\s*\S+)?\s*")
        tokens = params.split(",")
        for token in tokens:
            m = p.match(token)
            if m:
                from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
                self._paramlist.append(Type(m.group(1)))
                self._paramsize += Type.type_size_static(m.group(1))

    def __str__(self) -> str:
        return "\"" + self._name + "\" " + self._returntype.to_value_string() + " " + str(self._paramsize)

    def params(self):
        return self._paramlist

    def return_type(self):
        return self._returntype

    def paramsize(self) -> int:
        return self._paramsize

    def name(self) -> str:
        return self._name

class ActionsData:
    def __init__(self, actionsreader):
        self._actionsreader = actionsreader
        self._actions: list[Action] = []
        self.read_actions()

    def get_action(self, index: int) -> str:
        try:
            action = self._actions[index]
            return str(action)
        except IndexError:
            raise RuntimeError("Invalid action call: action " + str(index))

    def read_actions(self):
        # Reference: vendor/DeNCS/procyon/com/knights2end/nwscript/decomp/ActionsData.java lines 34-59
        # StringIO.readline() returns "" (empty string) at EOF, not None like Java BufferedReader
        p = re.compile(r"^\s*(\w+)\s+(\w+)\s*\((.*)\).*")
        self._actions = []
        # Outer loop: find the "// 0" marker (matches Java structure)
        while True:
            # Inner loop: read lines until EOF or "// 0" is found
            # StringIO returns "" at EOF, not None
            while True:
                str_line = self._actionsreader.readline()
                # Empty string means EOF
                if not str_line:
                    break
                if str_line.startswith("// 0"):
                    # Found the marker, now read actions until EOF
                    while True:
                        str_line = self._actionsreader.readline()
                        # Empty string means EOF
                        if not str_line:
                            break
                        # Skip comment lines
                        if str_line.startswith("//"):
                            continue
                        # Skip empty lines
                        if len(str_line.strip()) == 0:
                            continue
                        # Match function signature pattern
                        m = p.match(str_line)
                        if not m:
                            continue
                        self._actions.append(Action(m.group(1), m.group(2), m.group(3)))
                    print("read actions.  There were " + str(len(self._actions)))
                    return
            # EOF reached without finding "// 0", exit (prevents infinite loop)
            # Note: Java code has 'continue' here but would loop forever at EOF
            # We break instead since StringIO doesn't reset on EOF
            break

    def get_return_type(self, index: int):
        return self._actions[index].return_type()

    def get_name(self, index: int) -> str:
        return self._actions[index].name()

    def get_param_types(self, index: int):
        return self._actions[index].params()

