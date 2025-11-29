from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.actions_data import ActionsData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_sub import ASub  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptutils.sub_script_state import SubScriptState  # pyright: ignore[reportMissingImports]


class MainPass:
    def __init__(self, state_or_nodedata=None, nodedata=None, subdata=None, actions=None):
        from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
        # MainPass extends PrunedDepthFirstAdapter in Java
        PrunedDepthFirstAdapter.__init__(self)
        from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptutils.sub_script_state import SubScriptState  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
        
        self.stack = LocalVarStack()
        self.skipdeadcode = False
        self.backupstack = None
        
        # Two constructors: one with SubroutineState, one with just nodedata/subdata (for globals)
        if isinstance(state_or_nodedata, SubroutineState) or (state_or_nodedata is not None and hasattr(state_or_nodedata, 'type')):
            # Main constructor: MainPass(SubroutineState, NodeAnalysisData, SubroutineAnalysisData, ActionsData)
            state = state_or_nodedata
            self.nodedata = nodedata
            self.subdata = subdata
            self.actions = actions
            state.init_stack(self.stack)
            self.state = SubScriptState(self.nodedata, self.subdata, self.stack, state, actions)
            self.globals = False
            self.type = state.type()
        else:
            # Protected constructor for globals: MainPass(NodeAnalysisData, SubroutineAnalysisData)
            self.nodedata = state_or_nodedata
            self.subdata = nodedata
            self.actions = None
            self.state = SubScriptState(self.nodedata, self.subdata, self.stack)
            self.globals = True
            self.type = Type(-1)

    def done(self):
        self.stack = None
        self.nodedata = None
        self.subdata = None
        if self.state is not None:
            self.state.parse_done()
        self.state = None
        self.actions = None
        self.backupstack = None
        self.type = None

    def assert_stack(self):
        if (self.type.equals(0) or self.type.equals(-1)) and self.stack.size() > 0:
            raise RuntimeError(f"Error: Final stack size {self.stack.size()}{self.stack}")

    def get_code(self) -> str:
        return self.state.to_string()

    def get_proto(self) -> str:
        return self.state.get_proto()

    def get_script_root(self) -> ASub:
        return self.state.get_root()

    def get_state(self) -> SubScriptState:
        return self.state

    def default_in(self, node):
        """Called when entering any node during traversal."""
        from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.restore_stack_state(node)
        self.check_origins(node)
        if NodeUtils.is_command_node(node):
            self.skipdeadcode = not self.nodedata.process_code(node)

    def out_a_rsadd_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_rsadd_command import ARsaddCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            var = Variable(NodeUtils.get_type(node))
            self.stack.push(var)
            var = None
            self.state.transform_rs_add(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_copy_down_sp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            if copy > 1:
                self.stack.structify(loc - copy + 1, copy, self.subdata)
            self.state.transform_copy_down_sp(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_copy_top_sp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            varstruct = None
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            if copy > 1:
                varstruct = self.stack.structify(loc - copy + 1, copy, self.subdata)
            self.state.transform_copy_top_sp(node)
            if copy > 1:
                self.stack.push(varstruct)
            else:
                for i in range(copy):
                    entry: StackEntry = self.stack.get(loc)
                    self.stack.push(entry)
            varstruct = None
        else:
            self.state.transform_dead_code(node)

    def out_a_const_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_const_command import AConstCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            aconst = Const.new_const(NodeUtils.get_type(node), NodeUtils.get_const_value(node))
            self.stack.push(aconst)
            self.state.transform_const(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_action_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            entry = None
            remove = NodeUtils.action_remove_element_count(node, self.actions)
            i = 0
            while i < remove:
                entry = self.remove_from_stack()
                i += entry.size()
            type_val = NodeUtils.get_return_type(node, self.actions)
            if type_val.equals(-16):
                for j in range(3):
                    var = Variable(4)
                    self.stack.push(var)
                self.stack.structify(1, 3, self.subdata)
            elif not type_val.equals(0):
                var = Variable(type_val)
                self.stack.push(var)
            var = None
            type_val = None
            self.state.transform_action(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_logii_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_logii_command import ALogiiCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.remove_from_stack()
            self.remove_from_stack()
            var = Variable(3)
            self.stack.push(var)
            var = None
            self.state.transform_logii(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_binary_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
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
            for i in range(sizep3 + sizep2):
                self.remove_from_stack()
            for j in range(sizeresult):
                var = Variable(resulttype)
                self.stack.push(var)
            var = None
            resulttype = None
            self.state.transform_binary(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_unary_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_unary_command import AUnaryCommand  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.state.transform_unary(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_move_sp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.state.transform_move_sp(node)
            self.backupstack = self.stack.clone()
            remove = NodeUtils.stack_offset_to_pos(node.get_offset())
            entries = []
            i = 0
            while i < remove:
                entry: StackEntry = self.remove_from_stack()
                i += entry.size()
                if isinstance(entry, Variable) and not entry.is_placeholder(self.stack) and not entry.is_on_stack(self.stack):
                    entries.append(entry)
            if len(entries) > 0 and not self.nodedata.dead_code(node):
                self.state.transform_move_sp_variables_removed(entries, node)
            entry = None
            entries = None
        else:
            self.state.transform_dead_code(node)

    def out_a_conditional_jump_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            if self.nodedata.log_or_code(node):
                self.state.transform_log_or_extra_jump(node)
            else:
                self.state.transform_conditional_jump(node)
            self.remove_from_stack()
            if not self.nodedata.log_or_code(node):
                self.store_stack_state(self.nodedata.get_destination(node), self.nodedata.dead_code(node))
        else:
            self.state.transform_dead_code(node)

    def out_a_jump_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.state.transform_jump(node)
            self.store_stack_state(self.nodedata.get_destination(node), self.nodedata.dead_code(node))
            if self.backupstack is not None:
                self.stack.done_with_stack()
                self.stack = self.backupstack
                self.state.set_stack(self.stack)
        else:
            self.state.transform_dead_code(node)

    def out_a_jump_to_subroutine(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            substate = self.subdata.get_state(self.nodedata.get_destination(node))
            paramsize = substate.get_param_count()
            for i in range(paramsize):
                self.remove_from_stack()
            self.state.transform_jsr(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_destruct_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_destruct_command import ADestructCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.state.transform_destruct(node)
            removesize = NodeUtils.stack_size_to_pos(node.get_size_rem())
            savestart = NodeUtils.stack_size_to_pos(node.get_offset())
            savesize = NodeUtils.stack_size_to_pos(node.get_size_save())
            self.stack.destruct(removesize, savestart, savesize, self.subdata)
        else:
            self.state.transform_dead_code(node)

    def out_a_copy_top_bp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_bp_command import ACopyTopBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            varstruct = None
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            if copy > 1:
                varstruct = self.subdata.get_global_stack().structify(loc - copy + 1, copy, self.subdata)
            self.state.transform_copy_top_bp(node)
            if copy > 1:
                self.stack.push(varstruct)
            else:
                for i in range(copy):
                    var = self.subdata.get_global_stack().get(loc)
                    self.stack.push(var)
                    loc -= 1
            var = None
            varstruct = None
        else:
            self.state.transform_dead_code(node)

    def out_a_copy_down_bp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_bp_command import ACopyDownBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            if copy > 1:
                self.subdata.get_global_stack().structify(loc - copy + 1, copy, self.subdata)
            self.state.transform_copy_down_bp(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_store_state_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_store_state_command import AStoreStateCommand  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.state.transform_store_state(node)
            self.backupstack = None
        else:
            self.state.transform_dead_code(node)

    def out_a_stack_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.state.transform_stack(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_return(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            self.state.transform_return(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_subroutine(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
        pass

    def out_a_program(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram  # pyright: ignore[reportMissingImports]
        pass

    def remove_from_stack(self):
        """Helper method to remove an entry from the stack and handle placeholder variables."""
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
        entry: StackEntry = self.stack.remove()
        if isinstance(entry, Variable) and entry.is_placeholder(self.stack):
            self.state.transform_placeholder_variable_removed(entry)
        return entry

    def store_stack_state(self, node, isdead: bool):
        """Store the current stack state for the given node."""
        from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.local_stack import LocalStack  # pyright: ignore[reportMissingImports]
        if NodeUtils.is_store_stack_node(node):
            self.nodedata.set_stack(node, self.stack.clone(), False)

    def restore_stack_state(self, node):
        """Restore a previously stored stack state for the given node."""
        from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
        restore: LocalVarStack = self.nodedata.get_stack(node)
        if restore is not None:
            self.stack.done_with_stack()
            self.stack = restore
            self.state.set_stack(self.stack)
            if self.backupstack is not None:
                self.backupstack.done_with_stack()
            self.backupstack = None
        restore = None

    def check_origins(self, node):
        """Check for origin nodes and transform them."""
        from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
        origin = None
        while True:
            origin = self.get_next_origin(node)
            if origin is None:
                break
            self.state.transform_origin_found(node, origin)
        origin = None

    def get_next_origin(self, node):
        """Get the next origin node for the given node."""
        from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
        return self.nodedata.remove_last_origin(node)
