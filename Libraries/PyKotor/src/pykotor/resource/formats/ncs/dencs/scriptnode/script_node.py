from __future__ import annotations

import os
from typing import Any, overload

_SENTINEL: Any = object()


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

    def parent(self, parent: ScriptNode | None | Any = _SENTINEL) -> ScriptNode | None | None:
        """Get or set parent. Call without args to get, with arg to set."""
        if parent is _SENTINEL:
            return self._parent
        self._parent = parent
        if parent is not None:
            self.tabs = parent.tabs + "\t"
        return None

