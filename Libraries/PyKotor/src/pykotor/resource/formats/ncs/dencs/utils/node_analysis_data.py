from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]

class NodeData:
    """Port of NodeData inner class from NodeAnalysisData.java."""
    STATE_NORMAL = 0
    STATE_DEAD = 1
    STATE_LOGOR = 2
    STATE_DEAD_PROCESS = 3

    def __init__(self, pos: int | None = None):
        self.pos: int = pos if pos is not None else -1
        self.jump_destination = None  # Node reference
        self.stack = None  # LocalStack reference
        self.state: int = 0
        self.origins: list | None = None

    def add_origin(self, origin):
        if self.origins is None:
            self.origins = []
        self.origins.append(origin)

    def close(self):
        self.jump_destination = None
        self.stack = None
        self.origins = None

class NodeAnalysisData:
    def __init__(self):
        self.nodedatahash: dict[int, NodeData] = {}

    def close(self):
        if self.nodedatahash is not None:
            for data in self.nodedatahash.values():
                data.close()
            self.nodedatahash = None

    def set_pos(self, node: Node, pos: int):
        """Set position for a node. Uses id(node) as hash key."""
        node_id = id(node)
        try:
            data = self.nodedatahash.get(node_id)
            if data is None:
                data = NodeData(pos)
                self.nodedatahash[node_id] = data
            else:
                data.pos = pos
        finally:
            data = None
        data = None

    def get_pos(self, node: Node) -> int:
        """Get position for a node. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to read position on a node not in the hashtable.")
        return data.pos

    def set_destination(self, jump: Node, destination: int):
        """Set jump destination for a node. Uses id(node) as hash key."""
        jump_id = id(jump)
        try:
            data = self.nodedatahash.get(jump_id)
            if data is None:
                data = NodeData()
                data.jump_destination = destination
                self.nodedatahash[jump_id] = data
            else:
                data.jump_destination = destination
        finally:
            data = None
        data = None

    def get_destination(self, node: Node) -> int:
        """Get jump destination for a node. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to read destination on a node not in the hashtable.")
        return data.jump_destination

    def set_code_state(self, node: Node, state: int):
        """Set code state for a node. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            data = NodeData()
            data.state = state
            self.nodedatahash[node_id] = data
        else:
            data.state = state

    def dead_code(self, node: Node, deadcode: bool):
        """Mark a node as dead code. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to set status on a node not in the hashtable.")
        if deadcode:
            data.state = 1
        else:
            data.state = 0
        data.deadcode = deadcode

    def is_dead_code(self, node: Node) -> bool:
        """Check if a node is dead code. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to read status on a node not in the hashtable.")
        return data.state == NodeData.STATE_DEAD or data.state == NodeData.STATE_DEAD_PROCESS

    def process_code(self, node: Node) -> bool:
        """Check if node should be processed. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to read status on a node not in the hashtable.")
        return data.state != NodeData.STATE_DEAD

    def set_log_or_code(self, node: Node, logor: bool):
        """Set log_or status for a node. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to set status on a node not in the hashtable.")
        if logor:
            data.state = NodeData.STATE_LOGOR
        else:
            data.state = NodeData.STATE_NORMAL

    def log_or_code(self, node: Node) -> bool:
        """Check if node is a log_or code. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to read status on a node not in the hashtable.")
        return data.state == NodeData.STATE_LOGOR

    def add_origin(self, node: Node, origin: Node):
        """Add an origin node. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            data = NodeData()
            data.add_origin(origin)
            self.nodedatahash[node_id] = data
        else:
            data.add_origin(origin)

    def remove_last_origin(self, node: Node):
        """Remove and return the last origin. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            raise RuntimeError("Attempted to read origin on a node not in the hashtable.")
        if data.origins is None or len(data.origins) == 0:
            return None
        return data.origins.pop()

    def set_stack(self, node: Node, stack, overwrite: bool = False):
        """Set stack for a node. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            data = NodeData()
            data.stack = stack
            self.nodedatahash[node_id] = data
        elif data.stack is None or overwrite:
            data.stack = stack

    def get_stack(self, node: Node):
        """Get stack for a node. Uses id(node) as hash key."""
        node_id = id(node)
        data = self.nodedatahash.get(node_id)
        if data is None:
            return None
        return data.stack

    def clear_proto_data(self):
        for data in self.nodedatahash.values():
            data.stack = None

