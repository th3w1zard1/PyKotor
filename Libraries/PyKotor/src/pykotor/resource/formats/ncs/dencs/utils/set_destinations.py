from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]

class SetDestinations(PrunedDepthFirstAdapter):
    def __init__(self, ast: Node, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData):
        super().__init__()
        self.nodedata: NodeAnalysisData = nodedata
        self.current_pos: int = 0
        self.ast: Node = ast
        self.subdata: SubroutineAnalysisData = subdata
        self.actionarg: int = 0
        self.origins: dict[Node, list[Node]] = {}
        self.destination: Node | None = None

    def done(self):
        self.nodedata = None
        self.subdata = None
        self.destination = None
        self.ast = None
        self.origins = {}

    def get_origins(self) -> dict[Node, list[Node]]:
        return self.origins

    def out_a_conditional_jump_command(self, node: AConditionalJumpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]  # noqa: PLC0415
        pos = NodeUtils.get_jump_destination_pos(node)
        self.look_for_pos(pos, needcommand=True)
        if self.destination is None:
            raise RuntimeError("wasn't able to find dest for " + str(node) + " at pos " + str(pos))
        self.nodedata.set_destination(node, self.destination)
        self.add_destination(node, self.destination)

    def out_a_jump_command(self, node: AJumpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]  # noqa: PLC0415
        pos = NodeUtils.get_jump_destination_pos(node)
        self.look_for_pos(pos, needcommand=True)
        if self.destination is None:
            raise RuntimeError("wasn't able to find dest for " + str(node) + " at pos " + str(pos))
        self.nodedata.set_destination(node, self.destination)
        if pos < self.nodedata.get_pos(node):
            dest = NodeUtils.get_command_child(self.destination)
            self.nodedata.add_origin(dest, node)
        self.add_destination(node, self.destination)

    def out_a_jump_to_subroutine(self, node: AJumpToSubroutine):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]  # noqa: PLC0415
        pos = NodeUtils.get_jump_destination_pos(node)
        self.look_for_pos(pos, needcommand=False)
        if self.destination is None:
            raise RuntimeError("wasn't able to find dest for " + str(node) + " at pos " + str(pos))
        self.nodedata.set_destination(node, self.destination)
        self.add_destination(node, self.destination)

    def add_destination(self, origin: Node, destination: Node):
        if destination not in self.origins:
            self.origins[destination] = []
        self.origins[destination].append(origin)

    def get_pos(self, node: Node) -> int:
        return self.nodedata.get_pos(node)

    def look_for_pos(self, pos: int, needcommand: bool):  # noqa: C901, FBT001
        self.destination = None

        class LookForPosAdapter(PrunedDepthFirstAdapter):
            def __init__(self, outer: SetDestinations, pos: int, needcommand: bool):  # noqa: FBT001
                super().__init__()
                self.outer: SetDestinations = outer
                self.pos: int = pos
                self.needcommand: bool = needcommand

            def default_in(self, node: Node):
                from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]  # noqa: PLC0415
                try:
                    node_pos = self.outer.get_pos(node)
                    if node_pos == self.pos and self.outer.destination is None and (not self.needcommand or NodeUtils.is_command_node(node)):
                        self.outer.destination = node
                except RuntimeError:
                    # Node doesn't have position set, skip it
                    pass

            def case_a_program(self, node: AProgram):  # noqa: C901
                self.in_a_program(node)
                if node.get_return() is not None:
                    node.get_return().apply(self)
                temp = list(node.get_subroutine())
                
                # Try binary search first
                cur = len(temp) // 2
                min_idx = 0
                max_idx = len(temp) - 1
                done = self.outer.destination is not None or cur >= len(temp)
                while not done:
                    sub = temp[cur]
                    try:
                        sub_pos = self.outer.get_pos(sub)
                        if sub_pos > self.pos:
                            max_idx = cur - 1
                            if min_idx > max_idx:
                                break
                            cur = (min_idx + max_idx) // 2
                        elif sub_pos == self.pos:
                            sub.apply(self)
                            done = True
                        elif sub_pos < self.pos:
                            min_idx = cur + 1
                            if min_idx > max_idx:
                                break
                            cur = (min_idx + max_idx) // 2
                        else:
                            # Should not happen, but fallback
                            sub.apply(self)
                            cur += 1
                    except RuntimeError:
                        # Node doesn't have position, traverse it anyway
                        sub.apply(self)
                        cur += 1
                    done = done or self.outer.destination is not None or cur > max_idx or min_idx > max_idx

                # Fallback: if binary search didn't find exact match, do linear search
                if self.outer.destination is None:
                    for sub in temp:
                        try:
                            if self.outer.get_pos(sub) == self.pos:
                                sub.apply(self)
                                if self.outer.destination is not None:
                                    break
                        except RuntimeError:
                            # Node doesn't have position, traverse it anyway
                            sub.apply(self)
                            if self.outer.destination is not None:
                                break
                self.out_a_program(node)

            def case_a_command_block(self, node: ACommandBlock):  # noqa: C901
                self.in_a_command_block(node)
                temp = list(node.get_cmd())
                
                # Try binary search first
                cur = len(temp) // 2
                min_idx = 0
                max_idx = len(temp) - 1
                done = self.outer.destination is not None or cur >= len(temp)
                while not done:
                    cmd = temp[cur]
                    try:
                        cmd_pos = self.outer.get_pos(cmd)
                        if cmd_pos > self.pos:
                            max_idx = cur - 1
                            if min_idx > max_idx:
                                break
                            cur = (min_idx + max_idx) // 2
                        elif cmd_pos == self.pos:
                            cmd.apply(self)
                            done = True
                        elif cmd_pos < self.pos:
                            min_idx = cur + 1
                            if min_idx > max_idx:
                                break
                            cur = (min_idx + max_idx) // 2
                        else:
                            # Should not happen, but fallback
                            cmd.apply(self)
                            cur += 1
                    except RuntimeError:
                        # Node doesn't have position, traverse it anyway
                        cmd.apply(self)
                        cur += 1
                    done = done or self.outer.destination is not None or cur > max_idx or min_idx > max_idx

                # Fallback: if binary search didn't find exact match, do linear search
                if self.outer.destination is None:
                    for cmd in temp:
                        try:
                            if self.outer.get_pos(cmd) == self.pos:
                                cmd.apply(self)
                                if self.outer.destination is not None:
                                    break
                        except RuntimeError:
                            # Node doesn't have position, traverse it anyway
                            cmd.apply(self)
                            if self.outer.destination is not None:
                                break

        adapter = LookForPosAdapter(self, pos, needcommand)
        self.ast.apply(adapter)
        
        # Final fallback: if still not found, do a full exhaustive search
        if self.destination is None:
            class ExhaustiveSearchAdapter(PrunedDepthFirstAdapter):
                def __init__(self, outer: SetDestinations, pos: int, needcommand: bool):  # noqa: FBT001
                    super().__init__()
                    self.outer: SetDestinations = outer
                    self.pos: int = pos
                    self.needcommand: bool = needcommand

                def default_in(self, node: Node):
                    from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]  # noqa: PLC0415
                    try:
                        node_pos = self.outer.get_pos(node)
                        if node_pos == self.pos and self.outer.destination is None and (not self.needcommand or NodeUtils.is_command_node(node)):
                            self.outer.destination = node
                    except RuntimeError:
                        # Node doesn't have position set, skip it
                        pass
            
            exhaustive_adapter = ExhaustiveSearchAdapter(self, pos, needcommand)
            self.ast.apply(exhaustive_adapter)

