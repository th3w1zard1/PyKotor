from __future__ import annotations

import os


class ScriptNode:
    def __init__(self):
        self._parent: ScriptNode | None = None
        self.tabs: str = ""
        self.newline: str = os.linesep

    def parent(self, parent: ScriptNode | None = ...) -> ScriptNode | None:
        """Get or set parent. Call without args to get, with arg to set."""
        if parent is ...:
            return self._parent
        self._parent = parent
        if parent is not None:
            self.tabs = parent.tabs + "\t"
        return None

    def close(self):
        self._parent = None

