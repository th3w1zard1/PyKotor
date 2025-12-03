from __future__ import annotations


class LocalStack:
    def __init__(self):
        self.stack: list = []

    def size(self) -> int:
        return len(self.stack)

    def clone(self):
        new_stack = LocalStack()
        new_stack.stack = self.stack.copy()
        return new_stack

    def close(self):
        self.stack = None

