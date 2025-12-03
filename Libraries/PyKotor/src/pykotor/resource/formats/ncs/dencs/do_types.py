from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.actions_data import ActionsData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_type_stack import LocalTypeStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]

class DoTypes(PrunedDepthFirstAdapter):
    def __init__(self, state: SubroutineState, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData, actions: ActionsData, initialprototyping: bool):
        from pykotor.resource.formats.ncs.dencs.stack.local_type_stack import LocalTypeStack  # pyright: ignore[reportMissingImports]
        super().__init__()
        
        self.stack = LocalTypeStack()
        self.nodedata: NodeAnalysisData = nodedata
        self.subdata: SubroutineAnalysisData = subdata
        self.state: SubroutineState = state
        self.actions: ActionsData = actions
        if not initialprototyping:
            self.state.init_stack(self.stack)
        self.initialproto: bool = initialprototyping
        self.protoskipping: bool = False
        self.skipdeadcode: bool = False
        self.protoreturn: bool = (self.initialproto or not self.state.type().is_typed())
        self.backupstack: LocalTypeStack | None = None

    def done(self):
        self.state = None
        if self.stack is not None:
            self.stack.close()
            self.stack = None
        self.nodedata = None
        self.subdata = None
        if self.backupstack is not None:
            self.backupstack.close()
            self.backupstack = None
        self.actions = None

    def assert_stack(self):
        if self.stack.size() > 0:
            print("Uh-oh... dumping main() state:")
            if hasattr(self.state, 'print_state'):
                self.state.print_state()
            raise RuntimeError(f"Error: Final stack size {self.stack.size()}")

    def out_a_rsadd_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            self.stack.push(NodeUtils.get_type(node))

    def out_a_copy_down_sp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            isstruct = copy > 1
            if self.protoreturn and loc > self.stack.size():
                if isstruct:
                    struct = StructType()
                    for i in range(copy, 0, -1):
                        struct.add_type(self.stack.get(i))
                    self.state.set_return_type(struct, loc - self.stack.size())
                    self.subdata.add_struct(struct)
                else:
                    self.state.set_return_type(self.stack.get(1, self.state), loc - self.stack.size())

    def out_a_copy_top_sp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            for i in range(copy):
                self.stack.push(self.stack.get(loc, self.state))

    def out_a_const_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            self.stack.push(NodeUtils.get_type(node))

    def out_a_action_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            remove = NodeUtils.action_remove_element_count(node, self.actions)
            type_val = NodeUtils.get_return_type(node, self.actions)
            add = NodeUtils.stack_size_to_pos(type_val.type_size())
            self.stack.remove(remove)
            for i in range(add):
                self.stack.push(type_val)

    def out_a_logii_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            self.stack.remove(2)
            self.stack.push(Type(3))

    def out_a_binary_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            if NodeUtils.is_equality_op(node):
                if NodeUtils.get_type(node).equals(36):
                    sizep3 = sizep2 = NodeUtils.stack_size_to_pos(node.get_size())
                else:
                    sizep3 = sizep2 = 1
                sizeresult = 1
                resulttype = Type(3)
            elif NodeUtils.is_vector_allowed_op(node):
                sizep3 = NodeUtils.get_param1_size(node)
                sizep2 = NodeUtils.get_param2_size(node)
                sizeresult = NodeUtils.get_result_size(node)
                resulttype = NodeUtils.get_return_type(node)
            else:
                sizep3 = 1
                sizep2 = 1
                sizeresult = 1
                resulttype = Type(3)
            self.stack.remove(sizep3 + sizep2)
            for i in range(sizeresult):
                self.stack.push(resulttype)

    def out_a_move_sp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            if self.initialproto:
                params = self.stack.remove_prototyping(NodeUtils.stack_offset_to_pos(node.get_offset()))
                if params > 0:
                    self.state.set_param_count(params)
            else:
                self.stack.remove(NodeUtils.stack_offset_to_pos(node.get_offset()))

    def out_a_store_state_command(self, node):
        pass

    def out_a_conditional_jump_command(self, node):
        if not self.protoskipping and not self.skipdeadcode:
            self.stack.remove(1)
        self.check_protoskipping_start(node)
        if not self.protoskipping and not self.skipdeadcode and not self.is_log_or(node):
            self.store_stack_state(self.nodedata.get_destination(node))

    def out_a_jump_command(self, node):
        self.check_protoskipping_start(node)
        if not self.protoskipping and not self.skipdeadcode:
            self.store_stack_state(self.nodedata.get_destination(node))

    def out_a_jump_to_subroutine(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            substate = self.subdata.get_state(self.nodedata.get_destination(node))
            if not substate.is_prototyped():
                print("Uh-oh...")
                if hasattr(substate, 'print_state'):
                    substate.print_state()
                raise RuntimeError(f"Hit JSR on unprototyped subroutine {self.nodedata.get_pos(self.nodedata.get_destination(node))}")
            paramsize = substate.get_param_count()
            if substate.is_totally_prototyped():
                self.stack.remove(paramsize)
            else:
                self.stack.remove_params(paramsize, substate)
                if substate.type().equals(-1):
                    substate.set_return_type(self.stack.get(1, self.state), 0)
                if substate.type().equals(-15) and not substate.type().is_typed():
                    for i in range(substate.type().size()):
                        type_val = self.stack.get(substate.type().size() - i, self.state)
                        if not type_val.equals(-1):
                            struct_type = substate.type()
                            if isinstance(struct_type, StructType):
                                struct_type.update_type(i, type_val)

    def out_a_destruct_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            removesize = NodeUtils.stack_size_to_pos(node.get_size_rem())
            savestart = NodeUtils.stack_size_to_pos(node.get_offset())
            savesize = NodeUtils.stack_size_to_pos(node.get_size_save())
            self.stack.remove(removesize - (savesize + savestart))
            self.stack.remove(savesize + 1, savestart)

    def out_a_copy_top_bp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping and not self.skipdeadcode:
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            for i in range(copy):
                self.stack.push(self.subdata.get_global_stack().get_type(loc))
                loc -= 1

    def out_a_copy_down_bp_command(self, node):
        pass

    def out_a_subroutine(self, node):
        if self.initialproto:
            self.state.stop_prototyping(True)

    def default_in(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.protoskipping:
            self.restore_stack_state(node)
        else:
            self.check_protoskipping_done(node)
        if NodeUtils.is_command_node(node):
            self.skipdeadcode = self.nodedata.is_dead_code(node)

    def check_protoskipping_done(self, node):
        if self.state.get_skip_end(self.nodedata.get_pos(node)):
            self.protoskipping = False

    def check_protoskipping_start(self, node):
        if self.state.get_skip_start(self.nodedata.get_pos(node)):
            self.protoskipping = True

    def store_stack_state(self, node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if NodeUtils.is_store_stack_node(node):
            self.nodedata.set_stack(node, self.stack.clone(), True)

    def restore_stack_state(self, node):
        restore: LocalTypeStack = self.nodedata.get_stack(node)
        if restore is not None:
            self.stack = restore

    def is_log_or(self, node):
        return self.nodedata.log_or_code(node)

