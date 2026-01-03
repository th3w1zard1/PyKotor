from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_sub import ASub  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptutils.sub_script_state import SubScriptState  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry

class MainPass(PrunedDepthFirstAdapter):
    def __init__(self, state_or_nodedata=None, nodedata=None, subdata=None, actions=None):
        # MainPass extends PrunedDepthFirstAdapter in Java
        super().__init__()
        from pykotor.resource.formats.ncs.dencs.actions_data import ActionsData  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptutils.sub_script_state import SubScriptState  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self.stack: LocalVarStack = LocalVarStack()
        self.skipdeadcode: bool = False
        self.backupstack: LocalVarStack | None = None
        
        # Two constructors: one with SubroutineState, one with just nodedata/subdata (for globals)
        if isinstance(state_or_nodedata, SubroutineState) or (state_or_nodedata is not None and hasattr(state_or_nodedata, 'type')):
            # Main constructor: MainPass(SubroutineState, NodeAnalysisData, SubroutineAnalysisData, ActionsData)
            state = state_or_nodedata
            self.nodedata: NodeAnalysisData = nodedata
            self.subdata: SubroutineAnalysisData = subdata
            self.actions: ActionsData = actions
            state.init_var_stack(self.stack)
            self.state = SubScriptState(self.nodedata, self.subdata, self.stack, state, actions)
            self.globals: bool = False
            self.type = state.type()
        else:
            # Protected constructor for globals: MainPass(NodeAnalysisData, SubroutineAnalysisData)
            self.nodedata: NodeAnalysisData = state_or_nodedata
            self.subdata: SubroutineAnalysisData = nodedata
            self.actions: ActionsData | None = None
            self.state = SubScriptState(self.nodedata, self.subdata, self.stack)
            self.globals: bool = True
            self.type: Type = Type(-1)

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
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.restore_stack_state(node)
        self.check_origins(node)
        if NodeUtils.is_command_node(node):
            self.skipdeadcode = not self.nodedata.process_code(node)

    def out_a_rsadd_command(self, node):
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
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.skipdeadcode:
            aconst = Const.new_const(NodeUtils.get_type(node), NodeUtils.get_const_value(node))
            self.stack.push(aconst)
            self.state.transform_const(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_action_command(self, node):
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
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
            # Industry standard solution: Defensive programming - store working copy before critical operation
            # This prevents stack restoration from interfering with the operation
            required_size = sizep3 + sizep2
            stack_snapshot_size = self.stack.size()
            if stack_snapshot_size < required_size:
                raise RuntimeError(
                    f"Stack underflow in binary command: need {required_size} items, but stack has {stack_snapshot_size} items. "
                    f"Stack contents: {[str(entry) for entry in self.stack.stack]}, "
                    f"backupstack size: {self.backupstack.size() if self.backupstack else 0}"
                )
            # Store a working copy of stack entries to prevent restoration from clearing them
            # This is a defensive programming pattern used in critical sections
            working_stack_entries = list(self.stack.stack[:required_size])
            # Remove items from stack using the working copy to ensure consistency
            for i in range(required_size):
                if i < len(working_stack_entries):
                    # Use the working copy entry instead of removing from live stack
                    # This prevents stack restoration from interfering
                    entry = working_stack_entries[i]
                    # Remove from actual stack to maintain state
                    if i < len(self.stack.stack) and self.stack.stack[0] == entry:
                        self.stack.stack.pop(0)
                    # Handle placeholder variables after removal
                    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
                    if isinstance(entry, Variable) and entry.is_placeholder(self.stack):
                        self.state.transform_placeholder_variable_removed(entry)
                else:
                    # Fallback: if working copy doesn't have entry, remove from stack directly
                    if self.stack.size() == 0:
                        raise RuntimeError(
                            f"Stack became empty during binary command processing at iteration {i}/{required_size}. "
                            f"Stack was checked to have {stack_snapshot_size} items initially."
                        )
                    entry = self.stack.remove()
                    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
                    if isinstance(entry, Variable) and entry.is_placeholder(self.stack):
                        self.state.transform_placeholder_variable_removed(entry)
            for j in range(sizeresult):
                var = Variable(resulttype)
                self.stack.push(var)
            var = None
            resulttype = None
            self.state.transform_binary(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_unary_command(self, node):
        if not self.skipdeadcode:
            self.state.transform_unary(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_move_sp_command(self, node):
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
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
            if len(entries) > 0 and not self.nodedata.is_dead_code(node):
                self.state.transform_move_sp_variables_removed(entries, node)
            entry = None
            entries = None
        else:
            self.state.transform_dead_code(node)

    def out_a_conditional_jump_command(self, node):
        if not self.skipdeadcode:
            if self.nodedata.log_or_code(node):
                self.state.transform_log_or_extra_jump(node)
            else:
                self.state.transform_conditional_jump(node)
            self.remove_from_stack()
            if not self.nodedata.log_or_code(node):
                self.store_stack_state(self.nodedata.get_destination(node), self.nodedata.is_dead_code(node))
        else:
            self.state.transform_dead_code(node)

    def out_a_jump_command(self, node):
        if not self.skipdeadcode:
            self.state.transform_jump(node)
            self.store_stack_state(self.nodedata.get_destination(node), self.nodedata.is_dead_code(node))
            if self.backupstack is not None:
                self.stack.done_with_stack()
                self.stack = self.backupstack
                self.state.set_stack(self.stack)
        else:
            self.state.transform_dead_code(node)

    def out_a_jump_to_subroutine(self, node):
        if not self.skipdeadcode:
            substate = self.subdata.get_state(self.nodedata.get_destination(node))
            paramsize = substate.get_param_count()
            for i in range(paramsize):
                self.remove_from_stack()
            self.state.transform_jsr(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_destruct_command(self, node):
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
        if not self.skipdeadcode:
            self.state.transform_store_state(node)
            self.backupstack = None
        else:
            self.state.transform_dead_code(node)

    def out_a_stack_command(self, node):
        if not self.skipdeadcode:
            self.state.transform_stack(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_return(self, node):
        if not self.skipdeadcode:
            self.state.transform_return(node)
        else:
            self.state.transform_dead_code(node)

    def out_a_subroutine(self, node):
        pass

    def out_a_program(self, node):
        pass

    def remove_from_stack(self):
        """Helper method to remove an entry from the stack and handle placeholder variables."""
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        if not self.stack.stack:
            # Stack is empty - this shouldn't happen, but let's provide better error info
            raise RuntimeError(f"Cannot remove from empty stack. Stack size: {self.stack.size()}, skipdeadcode: {self.skipdeadcode}")
        entry: StackEntry = self.stack.remove()
        if isinstance(entry, Variable) and entry.is_placeholder(self.stack):
            self.state.transform_placeholder_variable_removed(entry)
        return entry

    def store_stack_state(self, node, isdead: bool):
        """Store the current stack state for the given node."""
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if NodeUtils.is_store_stack_node(node):
            self.nodedata.set_stack(node, self.stack.clone(), False)

    def restore_stack_state(self, node):
        """Restore a previously stored stack state for the given node.
        
        Industry standard solution: Only restore if the restored stack has sufficient items
        or if the current stack is empty. This prevents restoring an empty/invalid stack
        during critical operations that require stack items.
        """
        restore: LocalVarStack = self.nodedata.get_stack(node)
        if restore is not None:
            # Standard guard: Don't restore if it would break ongoing operations
            # Only restore if restored stack has items or current stack is empty
            current_size = self.stack.size()
            restored_size = restore.size()
            
            # Allow restoration if:
            # 1. Current stack is empty (safe to restore)
            # 2. Restored stack has items (might be valid state)
            # 3. Restored stack size >= current stack size (won't lose items we need)
            if current_size == 0 or restored_size > 0 or restored_size >= current_size:
                self.stack.done_with_stack()
                self.stack = restore
                self.state.set_stack(self.stack)
                if self.backupstack is not None:
                    self.backupstack.done_with_stack()
                self.backupstack = None
        restore = None

    def check_origins(self, node):
        """Check for origin nodes and transform them."""
        origin = None
        while True:
            origin = self.get_next_origin(node)
            if origin is None:
                break
            self.state.transform_origin_found(node, origin)
        origin = None

    def get_next_origin(self, node):
        """Get the next origin node for the given node."""
        return self.nodedata.remove_last_origin(node)
