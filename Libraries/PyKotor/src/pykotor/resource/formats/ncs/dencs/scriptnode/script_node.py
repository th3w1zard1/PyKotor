from __future__ import annotations

import os
from typing import overload


class ScriptNode:
    def __init__(self):
        self._parent: ScriptNode | None = None
        self.tabs: str = ""
        self.newline: str = os.linesep

    @overload
    def parent(self) -> ScriptNode | None:
        ...

    @overload
    def parent(self, parent: ScriptNode | None) -> None:
        ...

    def parent(self, *args: ScriptNode | None) -> ScriptNode | None | None:
        """Get or set parent. Call without args to get, with arg to set."""
        if len(args) == 0:
            return self._parent
        parent = args[0]
        self._parent = parent
        if parent is not None:
            self.tabs = parent.tabs + "\t"
        return None

