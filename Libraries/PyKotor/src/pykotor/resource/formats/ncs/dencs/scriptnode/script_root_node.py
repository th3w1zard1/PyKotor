from __future__ import annotations

from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]


class ScriptRootNode(ScriptNode):
    def __init__(self, start: int = 0, end: int = 0):
        super().__init__()
        self.children: list[ScriptNode] = []
        self.start: int = start
        self.end: int = end

    def add_child(self, child: ScriptNode):
        child.parent(self)  # type: ignore
        self.children.append(child)

    def add_children(self, children: list[ScriptNode]):
        for child in children:
            self.add_child(child)

    def remove_child(self, child: ScriptNode):
        if child in self.children:
            self.children.remove(child)
            child.parent(None)  # type: ignore

    def replace_child(self, old_child: ScriptNode, new_child: ScriptNode):
        """Replace an old child with a new child, maintaining the same position."""
        if old_child in self.children:
            index = self.children.index(old_child)
            old_child.parent(None)  # type: ignore
            new_child.parent(self)  # type: ignore
            self.children[index] = new_child

    def remove_children(self, first: int | None = None, last: int | None = None) -> list[ScriptNode]:
        """Remove children from the list.
        
        Args:
            first: Start index (inclusive). If None, starts from 0.
            last: End index (inclusive). If None, goes to end.
        
        Returns:
            List of removed children.
        """
        if first is None and last is None:
            # Remove all children
            children = list(self.children)
            for child in children:
                child.parent(None)  # type: ignore
            self.children.clear()
            return children
        elif first is not None and last is None:
            # Remove from first to end
            last = len(self.children) - 1
        
        if first is None:
            first = 0
        
        removed: list[ScriptNode] = []
        # Remove from end to start to preserve indices
        for i in range(last, first - 1, -1):
            if 0 <= i < len(self.children):
                child = self.children.pop(i)
                child.parent(None)  # type: ignore
                removed.insert(0, child)  # Insert at beginning to maintain order
        return removed

    def remove_last_child(self) -> ScriptNode | None:
        if not self.children:
            return None
        child = self.children.pop()
        child.parent(None)  # type: ignore
        return child

    def get_children(self) -> list[ScriptNode]:
        return self.children

    def has_children(self) -> bool:
        return len(self.children) > 0

    def size(self) -> int:
        return len(self.children)

    def get_last_child(self) -> ScriptNode | None:
        if not self.children:
            return None
        return self.children[-1]

    def get_start(self) -> int:
        return self.start

    def get_end(self) -> int:
        return self.end

    def get_child_location(self, child: ScriptNode) -> int:
        """Get the index of a child node, or -1 if not found."""
        try:
            return self.children.index(child)
        except ValueError:
            return -1

    def close(self):
        super().close()
        if self.children:
            for child in self.children:
                child.close()
        self.children.clear()

