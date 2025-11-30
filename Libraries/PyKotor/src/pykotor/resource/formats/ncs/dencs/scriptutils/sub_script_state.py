from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.actions_data import ActionsData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.node import Node
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_control_loop import AControlLoop
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_sub import ASub  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.const import Const
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry
    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]

class SubScriptState:
    STATE_DONE = -1
    STATE_NORMAL = 0
    STATE_INMOD = 1
    STATE_INACTIONARG = 2
    STATE_WHILECOND = 3
    STATE_SWITCHCASES = 4
    STATE_INPREFIXSTACK = 5

    def __init__(self, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData, stack: LocalVarStack, protostate: SubroutineState | None = None, actions: ActionsData | None = None):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_sub import ASub  # pyright: ignore[reportMissingImports]
        
        self.nodedata = nodedata
        self.subdata = subdata
        self.state = 0
        self.stack = stack
        self.varprefix = ""
        self.vardecs: dict[Variable, object] = {}
        self.varcounts: dict[Variable, int] = {}
        self.varnames: dict[str, int] = {}
        self.actions = actions
        
        if protostate is not None:
            self.root = ASub(protostate.type(), protostate.get_id(), self._get_params(protostate.get_param_count()), protostate.get_start(), protostate.get_end())
        else:
            self.root = ASub(0, 0)
        self.current: ScriptRootNode = self.root

    def _get_params(self, paramcount: int) -> list:
        # This method is implemented below in get_params - it's a duplicate name issue
        # The actual implementation is in the get_params method defined later
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        params = []
        for i in range(1, paramcount + 1):
            var: Variable = self.stack.get(i)
            var.set_name_with_hint("Param", i)
            varref = AVarRef(var)
            params.append(varref)
        return params

    def set_var_prefix(self, prefix: str):
        self.varprefix = prefix

    def set_stack(self, stack: LocalVarStack):
        self.stack = stack

    def parse_done(self):
        self.nodedata = None
        self.subdata = None
        if self.stack is not None:
            self.stack.done_parse()
        self.stack = None
        if self.vardecs is not None:
            for var in list(self.vardecs.keys()):
                var.done_parse()

    def close(self):
        if self.vardecs is not None:
            for var in list(self.vardecs.keys()):
                var.close()
            self.vardecs = None
        self.varcounts = None
        self.varnames = None
        if self.root is not None:
            self.root.close()
        self.current = None
        self.root = None
        self.nodedata = None
        self.subdata = None
        self.actions = None
        if self.stack is not None:
            self.stack.close()
            self.stack = None

    def __str__(self) -> str:
        return str(self.root)

    def to_string_globals(self) -> str:
        return self.root.get_body()

    def get_proto(self) -> str:
        return self.root.get_header()

    def get_root(self) -> ASub:
        return self.root

    def get_name(self) -> str:
        return self.root.name() if hasattr(self.root, 'name') else ""

    def set_name(self, name: str):
        if hasattr(self.root, 'set_name'):
            self.root.set_name(name)

    def is_main(self, ismain: bool = None):
        if ismain is not None:
            if hasattr(self.root, 'set_is_main'):
                self.root.set_is_main(ismain)
        else:
            return self.root.is_main() if hasattr(self.root, 'is_main') else False

    def transform_placeholder_variable_removed(self, var: Variable):
        vardec: AVarDecl = self.vardecs.get(var)
        if vardec is not None and vardec.is_fcn_return():
            exp = vardec.exp()
            parent: ScriptRootNode = vardec.parent()
            if parent is not None:
                if exp is not None:
                    parent.replace_child(vardec, exp)
                else:
                    parent.remove_child(vardec)
            if var in self.vardecs:
                del self.vardecs[var]

    def transform_move_sp_variables_removed(self, vars_list, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_code_block import ACodeBlock  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if self.at_last_command(node) and self.current_contains_vars(vars_list):
            return
        if len(vars_list) == 0:
            return
        if self.is_middle_of_return(node):
            return
        if self.removing_switch_var(vars_list, node):
            return
        if not self.current_contains_vars(vars_list):
            return
        earliestdec = -1
        for var in vars_list:
            vardec: AVarDecl = self.vardecs.get(var)
            earliestdec = self.get_earlier_dec(vardec, earliestdec)
        if earliestdec != -1:
            prev: Node = NodeUtils.get_previous_command(node, self.nodedata)
            block = ACodeBlock(-1, self.nodedata.get_pos(prev))
            children = self.current.remove_children(earliestdec)
            self.current.add_child(block)
            block.add_children(children)

    def transform_end_do_loop(self):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_do_loop import ADoLoop  # pyright: ignore[reportMissingImports]
        if isinstance(self.current, ADoLoop):
            self.current.condition(self.remove_last_exp(False))

    def transform_origin_found(self, destination, origin):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_while_loop import AWhileLoop  # pyright: ignore[reportMissingImports]
        loop: AControlLoop = self.get_loop(destination, origin)
        self.current.add_child(loop)
        self.current = loop
        if isinstance(loop, AWhileLoop):
            self.state = 3

    def transform_log_or_extra_jump(self, node):
        self.remove_last_exp(True)

    def assert_state(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        if self.state == 0:
            return
        if self.state == 2 and not isinstance(node, AJumpCommand):
            raise RuntimeError(f"In action arg, expected JUMP at node {node}")
        if self.state == -1:
            raise RuntimeError(f"In DONE state, no more nodes expected at node {node}")
        if self.state == 5 and not isinstance(node, ACopyTopSpCommand):
            raise RuntimeError(f"In prefix stack op state, expected CPTOPSP at node {node}")

    def check_start(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
        self.assert_state(node)
        if self.current.has_children():
            last_node: ScriptNode = self.current.get_last_child()
            if isinstance(last_node, ASwitch) and self.nodedata.get_pos(node) == last_node.get_first_case_start():
                self.current = last_node.get_first_case()

    def check_end(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_do_loop import ADoLoop  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_else import AElse  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_if import AIf  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        while self.current is not None:
            if self.nodedata.get_pos(node) != self.current.get_end():
                return
            if isinstance(self.current, ASwitchCase):
                parent = self.current.parent()
                if isinstance(parent, ASwitch):
                    next_case: ASwitchCase = parent.get_next_case(self.current)
                    if next_case is not None:
                        self.current = next_case
                    else:
                        grandparent = parent.parent()
                        if isinstance(grandparent, ScriptRootNode):
                            self.current = grandparent
                return
            if isinstance(self.current, AIf):
                dest: Node = self.nodedata.get_destination(node)
                if dest is None:
                    return
                if self.nodedata.get_pos(dest) != self.current.get_end() + 6:
                    aelse = AElse(self.current.get_end() + 6, self.nodedata.get_pos(NodeUtils.get_previous_command(dest, self.nodedata)))
                    parent = self.current.parent()
                    if isinstance(parent, ScriptRootNode):
                        self.current = parent
                    self.current.add_child(aelse)
                    self.current = aelse
                    return
            if isinstance(self.current, ADoLoop):
                self.transform_end_do_loop()
            parent = self.current.parent()
            if isinstance(parent, ScriptRootNode):
                self.current = parent
        self.state = -1

    def in_action_arg(self) -> bool:
        return self.state == 2

    def transform_dead_code(self, node):
        self.check_end(node)

    def transform_bp(self, node):
        self.check_start(node)
        self.check_end(node)

    def transform_store_state(self, node):
        self.check_start(node)
        self.state = 2
        self.check_end(node)

    def transform_return(self, node):
        self.check_start(node)
        self.check_end(node)

    def transform_const(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_const import AConst  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        theconst: Const = self.stack.get(1)
        constdec = AConst(theconst)
        self.current.add_child(constdec)
        self.check_end(node)

    def transform_move_sp(self, node):
        self.check_start(node)
        self.check_switch_end(node)
        self.check_end(node)

    def transform_copy_down_sp(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_return_statement import AReturnStatement  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        exp = self.remove_last_exp(False)
        if self.is_return(node):
            ret = AReturnStatement(exp)
            self.current.add_child(ret)
        else:
            varref = self.get_var_to_assign_to(node)
            self.update_name(varref, exp)
            self.current.add_child(varref)
        self.check_end(node)

    def transform_rs_add(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        var: Variable = self.stack.get(1)
        self.update_var_count(var)
        vardec = AVarDecl(var)
        self.current.add_child(vardec)
        self.vardecs[var] = vardec
        self.check_end(node)

    def transform_copy_top_sp(self, node):
        self.check_start(node)
        exp = self.get_var_to_copy(node)
        self.current.add_child(exp)
        self.check_end(node)

    def transform_copy_top_bp(self, node):
        self.check_start(node)
        exp = self.get_var_to_copy_bp(node)
        self.current.add_child(exp)
        self.check_end(node)

    def transform_copy_down_bp(self, node):
        self.check_start(node)
        varref = self.get_var_to_assign_to_bp(node)
        exp = self.remove_last_exp(False)
        self.update_name(varref, exp)
        self.current.add_child(varref)
        self.check_end(node)

    def transform_destruct(self, node):
        self.check_start(node)
        self.update_struct_var(node)
        self.check_end(node)

    def transform_action(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_action_exp import AActionExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        params = self.remove_action_params(node)
        act = AActionExp(NodeUtils.get_action_name(node, self.actions), NodeUtils.get_action_id(node), params)
        type_val = NodeUtils.get_return_type(node, self.actions)
        if not type_val.equals(0):
            var: Variable = self.stack.get(1)
            if type_val.equals(-16):
                var = var.varstruct()
            act.set_stackentry(var)
            vardec = AVarDecl(var)
            vardec.set_is_fcn_return(True)
            vardec.initialize_exp(act)
            self.update_var_count(var)
            self.current.add_child(vardec)
            self.vardecs[var] = vardec
        else:
            self.current.add_child(act)
        self.check_end(node)

    def transform_binary(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_binary_exp import ABinaryExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_conditional_exp import AConditionalExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        right = self.remove_last_exp(False)
        left = self.remove_last_exp(self.state == 4)
        if NodeUtils.is_arithmetic_op(node):
            exp = ABinaryExp(left, right, NodeUtils.get_op(node))
        else:
            if not NodeUtils.is_conditional_op(node):
                raise RuntimeError(f"Unknown binary op at {self.nodedata.get_pos(node)}")
            exp = AConditionalExp(left, right, NodeUtils.get_op(node))
        exp.set_stackentry(self.stack.get(1))
        self.current.add_child(exp)
        self.check_end(node)

    def transform_unary(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_unary_exp import AUnaryExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        exp = self.remove_last_exp(False)
        unexp = AUnaryExp(exp, NodeUtils.get_op(node))
        unexp.set_stackentry(self.stack.get(1))
        self.current.add_child(unexp)
        self.check_end(node)

    def transform_logii(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_conditional_exp import AConditionalExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_if import AIf  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_while_loop import AWhileLoop  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        if not self.current.has_children() and isinstance(self.current, AIf) and isinstance(self.current.parent(), AIf):
            right = self.current
            left = self.current.parent()
            conexp = AConditionalExp(left.condition(), right.condition(), NodeUtils.get_op(node))
            conexp.set_stackentry(self.stack.get(1))
            self.current = self.current.parent()
            self.current.condition(conexp)
            self.current.remove_last_child()
        else:
            right2 = self.remove_last_exp(False)
            if not self.current.has_children() and isinstance(self.current, AIf):
                left2 = self.current.condition()
                conexp = AConditionalExp(left2, right2, NodeUtils.get_op(node))
                conexp.set_stackentry(self.stack.get(1))
                self.current.condition(conexp)
            elif not self.current.has_children() and isinstance(self.current, AWhileLoop):
                left2 = self.current.condition()
                conexp = AConditionalExp(left2, right2, NodeUtils.get_op(node))
                conexp.set_stackentry(self.stack.get(1))
                self.current.condition(conexp)
            else:
                left2 = self.remove_last_exp(False)
                conexp = AConditionalExp(left2, right2, NodeUtils.get_op(node))
                conexp.set_stackentry(self.stack.get(1))
                self.current.add_child(conexp)
        self.check_end(node)

    def transform_stack(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_unary_mod_exp import AUnaryModExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        last = self.current.get_last_child()
        varref = self.get_var_to_assign_to_stack(node)
        if isinstance(last, AVarRef) and last.var() == varref.var():
            self.remove_last_exp(True)
            prefix = False
        else:
            self.state = 5
            prefix = True
        unexp = AUnaryModExp(varref, NodeUtils.get_op(node), prefix)
        unexp.set_stackentry(self.stack.get(1))
        self.current.add_child(unexp)
        self.check_end(node)

    def transform_jsr(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_fcn_call_exp import AFcnCallExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        jsr = AFcnCallExp(self.get_fcn_id(node), self.remove_fcn_params(node))
        if not self.get_fcn_type(node).equals(0):
            last_child = self.current.get_last_child()
            if isinstance(last_child, AVarDecl):
                last_child.set_is_fcn_return(True)
                last_child.initialize_exp(jsr)
                jsr.set_stackentry(self.stack.get(1))
        else:
            self.current.add_child(jsr)
        self.check_end(node)

    def transform_jump(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_action_arg_exp import AActionArgExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_break_statement import ABreakStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_continue_statement import AContinueStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_return_statement import AReturnStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_unk_loop_control import AUnkLoopControl  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        dest: Node = self.nodedata.get_destination(node)
        if self.state == 2:
            self.state = 0
            aarg = AActionArgExp(self.get_next_command(node), self.get_prior_to_dest_command(node))
            self.current.add_child(aarg)
            self.current = aarg
        else:
            from pykotor.resource.formats.ncs.dencs.scriptnode.a_if import AIf  # pyright: ignore[reportMissingImports]
            if not isinstance(self.current, AIf) or self.nodedata.get_pos(node) != self.current.get_end():
                if self.state == 4:
                    from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
                    from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
                    from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase  # pyright: ignore[reportMissingImports]
                    aswitch = self.current.get_last_child()
                    if isinstance(aswitch, ASwitch):
                        aprevcase = aswitch.get_last_case()
                        if aprevcase is not None:
                            aprevcase.end(self.nodedata.get_pos(NodeUtils.get_previous_command(dest, self.nodedata)))
                        if isinstance(dest, AMoveSpCommand):
                            aswitch.end(self.nodedata.get_pos(self.nodedata.get_destination(node)))
                        else:
                            adefault = ASwitchCase(self.nodedata.get_pos(dest))
                            aswitch.add_default_case(adefault)
                    self.state = 0
                elif self.is_return_jump(node):
                    if not self.root.type().equals(0):
                        areturn = AReturnStatement(self.get_return_exp())
                    else:
                        areturn = AReturnStatement()
                    self.current.add_child(areturn)
                elif self.nodedata.get_pos(dest) >= self.nodedata.get_pos(node):
                    loop = self.get_breakable()
                    if isinstance(loop, ASwitchCase):
                        loop = self.get_enclosing_loop(loop)
                        if loop is None:
                            abreak = ABreakStatement()
                            self.current.add_child(abreak)
                        else:
                            aunk = AUnkLoopControl(self.nodedata.get_pos(dest))
                            self.current.add_child(aunk)
                    elif loop is not None and self.nodedata.get_pos(dest) > loop.get_end():
                        abreak = ABreakStatement()
                        self.current.add_child(abreak)
                    else:
                        loop = self.get_loop_helper()
                        if loop is not None and self.nodedata.get_pos(dest) <= loop.get_end():
                            acont = AContinueStatement()
                            self.current.add_child(acont)
        self.check_end(node)

    def transform_conditional_jump(self, node):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_conditional_exp import AConditionalExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_const import AConst  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_if import AIf  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_while_loop import AWhileLoop  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        self.check_start(node)
        if self.state == 3:
            if isinstance(self.current, AWhileLoop):
                self.current.condition(self.remove_last_exp(False))
                self.state = 0
        elif not NodeUtils.is_jz(node):
            if self.state != 4:
                cond = self.remove_last_exp(True)
                if isinstance(cond, AConditionalExp):
                    if isinstance(cond.right(), AConst):
                        acase = ASwitchCase(self.nodedata.get_pos(self.nodedata.get_destination(node)), cond.right())
                    else:
                        raise RuntimeError(f"Expected AConst in switch case but got {type(cond.right())}")
                    aswitch = None
                    if self.current.has_children():
                        last = self.current.get_last_child()
                        if isinstance(last, AVarRef) and isinstance(cond.left(), AVarRef) and last.var().equals(cond.left().var()):
                            varref = self.remove_last_exp(False)
                            aswitch = ASwitch(self.nodedata.get_pos(node), varref)
                    if aswitch is None:
                        aswitch = ASwitch(self.nodedata.get_pos(node), cond.left())
                    self.current.add_child(aswitch)
                    aswitch.add_case(acase)
                    self.state = 4
            else:
                cond = self.remove_last_exp(True)
                if isinstance(cond, AConditionalExp):
                    aswitch = self.current.get_last_child()
                    if isinstance(aswitch, ASwitch):
                        aprevcase = aswitch.get_last_case()
                        if aprevcase is not None:
                            aprevcase.end(self.nodedata.get_pos(NodeUtils.get_previous_command(self.nodedata.get_destination(node), self.nodedata)))
                        if isinstance(cond.right(), AConst):
                            acase2 = ASwitchCase(self.nodedata.get_pos(self.nodedata.get_destination(node)), cond.right())
                        else:
                            raise RuntimeError(f"Expected AConst in switch case but got {type(cond.right())}")
                        aswitch.add_case(acase2)
        elif isinstance(self.current, AIf) and self.is_modify_conditional():
            self.current.end(self.nodedata.get_pos(self.nodedata.get_destination(node)) - 6)
            if self.current.has_children():
                self.current.remove_last_child()
        elif isinstance(self.current, AWhileLoop) and self.is_modify_conditional():
            self.current.end(self.nodedata.get_pos(self.nodedata.get_destination(node)) - 6)
            if self.current.has_children():
                self.current.remove_last_child()
        else:
            aif = AIf(self.nodedata.get_pos(node), self.nodedata.get_pos(self.nodedata.get_destination(node)) - 6, self.remove_last_exp(False))
            self.current.add_child(aif)
            self.current = aif
        self.check_end(node)

    # Helper methods
    def _get_params(self, paramcount: int) -> list:
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        params = []
        for i in range(1, paramcount + 1):
            var: Variable = self.stack.get(i)
            var.set_name_with_hint("Param", i)
            varref = AVarRef(var)
            params.append(varref)
        return params

    def remove_if_as_exp(self):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_if import AIf  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
        if isinstance(self.current, AIf):
            exp = self.current.condition()
            parent = self.current.parent()
            if isinstance(parent, ScriptRootNode):
                self.current = parent
            self.current.remove_child(self.current)
            self.current.set_parent(None)
            if exp is not None:
                exp.set_parent(None)
            return exp

    def remove_last_exp(self, force_one_only: bool):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_if import AIf  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        if not self.current.has_children() and isinstance(self.current, AIf):
            return self.remove_if_as_exp()
        anode: ScriptNode = self.current.remove_last_child()
        if isinstance(anode, AExpression):
            if not force_one_only and isinstance(anode, AVarRef) and not anode.var().is_assigned and not anode.var().is_param and self.current.has_children():
                last = self.current.get_last_child()
                # Use identity comparison (is) instead of equals() - standard Python approach
                if isinstance(last, AExpression) and anode.var() is last.stackentry():
                    return self.remove_last_exp(False)
                if isinstance(last, AVarDecl) and anode.var() is last.var_var() and last.exp() is not None:
                    return self.remove_last_exp(False)
            return anode
        if not force_one_only and isinstance(anode, AVarDecl) and anode.exp() is not None:
            return anode.remove_exp()
        print(anode)
        raise RuntimeError(f"Last child not an expression: {type(anode)}")

    def get_last_exp(self):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl  # pyright: ignore[reportMissingImports]
        anode: ScriptNode = self.current.get_last_child()
        if isinstance(anode, AExpression):
            return anode
        if isinstance(anode, AVarDecl) and anode.is_fcn_return():
            return anode.exp()
        print(anode)
        raise RuntimeError(f"Last child not an expression {anode}")

    def get_loop(self, destination, origin):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_do_loop import ADoLoop  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_while_loop import AWhileLoop  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        before_jump: Node = NodeUtils.get_previous_command(origin, self.nodedata)
        if NodeUtils.is_jz_past_one(before_jump):
            doloop = ADoLoop(self.nodedata.get_pos(destination), self.nodedata.get_pos(origin))
            return doloop
        whileloop = AWhileLoop(self.nodedata.get_pos(destination), self.nodedata.get_pos(origin))
        return whileloop

    def get_enclosing_loop(self, start):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_do_loop import ADoLoop  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_while_loop import AWhileLoop  # pyright: ignore[reportMissingImports]
        node: ScriptNode = start
        while node is not None:
            if isinstance(node, ADoLoop) or isinstance(node, AWhileLoop):
                return node
            node = node.parent()
        return None

    def get_breakable(self):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_do_loop import ADoLoop  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_while_loop import AWhileLoop  # pyright: ignore[reportMissingImports]
        node: ScriptNode = self.current
        while node is not None:
            if isinstance(node, ADoLoop) or isinstance(node, AWhileLoop) or isinstance(node, ASwitchCase):
                return node
            node = node.parent()
        return None

    def get_loop_helper(self):
        return self.get_enclosing_loop(self.current)

    def is_modify_conditional(self) -> bool:
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        if not self.current.has_children():
            return True
        if self.current.size() == 1:
            last: ScriptNode = self.current.get_last_child()
            if isinstance(last, AVarRef) and not last.var().is_assigned() and not last.var().is_param():
                return True
        return False

    def is_return(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if isinstance(node, ACopyDownSpCommand):
            return not self.root.type().equals(0) and self.stack.size() == NodeUtils.stack_offset_to_pos(node.get_offset())

    def is_return_jump(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        dest: Node = NodeUtils.get_command_child(self.nodedata.get_destination(node))
        if NodeUtils.is_return(dest):
            return True
        if isinstance(dest, AMoveSpCommand):
            after_dest: Node = NodeUtils.get_next_command(dest, self.nodedata)
            return after_dest is None
        return False

    def get_return_exp(self):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression_statement import AExpressionStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_modify_exp import AModifyExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_return_statement import AReturnStatement  # pyright: ignore[reportMissingImports]
        last: ScriptNode = self.current.remove_last_child()
        if isinstance(last, AModifyExp):
            return last.expression()
        if isinstance(last, AExpressionStatement) and isinstance(last.exp(), AModifyExp):
            return last.exp().expression()
        if isinstance(last, AReturnStatement):
            return last.exp()
        print(last)
        raise RuntimeError(f"Trying to get return expression, unexpected scriptnode class {type(last)}")

    def check_switch_end(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        if isinstance(self.current, ASwitchCase) and isinstance(node, AMoveSpCommand):
            entry: StackEntry = self.stack.get(1)
            parent = self.current.parent()
            if isinstance(parent, ASwitch) and isinstance(entry, Variable) and parent.switch_exp().stackentry().equals(entry):
                parent.end(self.nodedata.get_pos(node))
                self.update_switch_unknowns(parent)

    def update_switch_unknowns(self, aswitch):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_break_statement import ABreakStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_continue_statement import AContinueStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_unk_loop_control import AUnkLoopControl  # pyright: ignore[reportMissingImports]
        acase: ASwitchCase = None
        while True:
            acase = aswitch.get_next_case(acase)
            if acase is None:
                break
            for unk in acase.get_unknowns():
                if isinstance(unk, AUnkLoopControl):
                    if unk.get_destination() > aswitch.end():
                        acase.replace_unknown(unk, AContinueStatement())
                    else:
                        acase.replace_unknown(unk, ABreakStatement())

    def update_var_count(self, var):
        count = 1
        key = var.type()
        curcount = self.varcounts.get(key, 0)
        if curcount != 0:
            count += curcount
        var.set_name_with_hint(self.varprefix, count)
        self.varcounts[key] = count

    def set_var_struct_name(self, varstruct):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if varstruct.name() is None:
            count = 1
            key = Type(-15)
            curcount = self.varcounts.get(key, 0)
            if curcount != 0:
                count += curcount
            varstruct.set_name(self.varprefix, count)
            self.varcounts[key] = count

    def get_variables(self):
        vars_list = list(self.vardecs.keys())
        varstructs = []
        for var in vars_list[:]:
            if var.is_struct():
                varstructs.append(var.varstruct())
                vars_list.remove(var)
        vars_list.extend(varstructs)
        vars_list.extend(self.root.get_param_vars())
        return vars_list

    def get_var_to_assign_to(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if isinstance(node, ACopyDownSpCommand):
            result = self.get_var(NodeUtils.stack_size_to_pos(node.get_size()), NodeUtils.stack_offset_to_pos(node.get_offset()), self.stack, True, self)
            if isinstance(result, AVarRef):
                return result
            raise RuntimeError(f"Expected AVarRef but got {type(result)}")

    def get_var_to_assign_to_bp(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_bp_command import ACopyDownBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if isinstance(node, ACopyDownBpCommand):
            result = self.get_var(NodeUtils.stack_size_to_pos(node.get_size()), NodeUtils.stack_offset_to_pos(node.get_offset()), self.subdata.get_global_stack(), True, self.subdata.global_state())
            if isinstance(result, AVarRef):
                return result
            raise RuntimeError(f"Expected AVarRef but got {type(result)}")

    def get_var_to_assign_to_stack(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if isinstance(node, AStackCommand):
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            if NodeUtils.is_global_stack_op(node):
                loc -= 1
            var: Variable
            if NodeUtils.is_global_stack_op(node):
                var = self.subdata.get_global_stack().get(loc)
            else:
                entry = self.stack.get(loc)
                if not isinstance(entry, Variable):
                    print(f"not a variable at loc {loc}")
                    print(self.stack)
                var = entry
            var.assign()
            return AVarRef(var)

    def get_var_to_copy(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if isinstance(node, ACopyTopSpCommand):
            return self.get_var(NodeUtils.stack_size_to_pos(node.get_size()), NodeUtils.stack_offset_to_pos(node.get_offset()), self.stack, False, self)

    def get_var_to_copy_bp(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_bp_command import ACopyTopBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if isinstance(node, ACopyTopBpCommand):
            return self.get_var(NodeUtils.stack_size_to_pos(node.get_size()), NodeUtils.stack_offset_to_pos(node.get_offset()), self.subdata.get_global_stack(), False, self.subdata.global_state())

    def get_var(self, copy: int, loc: int, stack, assign: bool, state):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_const import AConst  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.const import Const  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        isstruct = copy > 1
        entry: StackEntry = stack.get(loc)
        if not isinstance(entry, Variable) and assign:
            raise RuntimeError("Attempting to assign to a non-variable")
        if isinstance(entry, Const):
            return AConst(entry)
        var: Variable = entry
        if not isstruct:
            if assign:
                var.assign()
            return AVarRef(var)
        if var.is_struct():
            if assign:
                var.varstruct().assign()
            state.set_var_struct_name(var.varstruct())
            return AVarRef(var.varstruct())
        newstruct = VarStruct()
        newstruct.add_var(var)
        for i in range(loc - 1, loc - copy, -1):
            var = stack.get(i)
            newstruct.add_var(var)
        if assign:
            newstruct.assign()
        self.subdata.add_struct(newstruct)
        state.set_var_struct_name(newstruct)
        return AVarRef(newstruct)

    def remove_fcn_params(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        params = []
        if isinstance(node, AJumpToSubroutine):
            paramcount = self.subdata.get_state(self.nodedata.get_destination(node)).get_param_count()
            i = 0
            while i < paramcount:
                exp = self.remove_last_exp(False)
                i += self.get_exp_size(exp)
                params.append(exp)
        return params

    def get_exp_size(self, exp):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_const import AConst  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        if isinstance(exp, AVarRef):
            return exp.var().size()
        if isinstance(exp, AConst):
            return 1
        return 1

    def remove_action_params(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_vector_const_exp import AVectorConstExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        params = []
        if isinstance(node, AActionCommand):
            paramtypes = NodeUtils.get_action_param_types(node, self.actions)
            paramcount = NodeUtils.get_action_param_count(node)
            for i in range(paramcount):
                paramtype = paramtypes[i]
                if paramtype.equals(-16):
                    exp = self.get_last_exp()
                    if exp.stackentry().type().equals(-16) or exp.stackentry().type().equals(-15):
                        exp = self.remove_last_exp(False)
                    else:
                        exp = AVectorConstExp(self.remove_last_exp(False), self.remove_last_exp(False), self.remove_last_exp(False))
                else:
                    exp = self.remove_last_exp(False)
                params.append(exp)
        return params

    def get_fcn_id(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        if isinstance(node, AJumpToSubroutine):
            return self.subdata.get_state(self.nodedata.get_destination(node)).get_id()
        return 0

    def get_fcn_type(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        if isinstance(node, AJumpToSubroutine):
            return self.subdata.get_state(self.nodedata.get_destination(node)).type()
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        return Type(0)

    def get_next_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        if isinstance(node, AJumpCommand):
            return self.nodedata.get_pos(node) + 6
        return 0

    def get_prior_to_dest_command(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        if isinstance(node, AJumpCommand):
            return self.nodedata.get_pos(self.nodedata.get_destination(node)) - 2
        return 0

    def update_name(self, varref, exp):
        # TODO: Implement name generation from action
        # if isinstance(exp, AActionExp):
        #     name = NameGenerator.getNameFromAction(exp)
        #     if name is not None and name not in self.varnames:
        #         varref.var().name(name)
        #         self.varnames[name] = 1
        pass

    def update_struct_var(self, node):
        from pykotor.resource.formats.ncs.dencs.node.a_destruct_command import ADestructCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if isinstance(node, ADestructCommand):
            varref = self.get_last_exp()
            if isinstance(varref, AVarRef):
                removesize = NodeUtils.stack_size_to_pos(node.get_size_rem())
                savestart = NodeUtils.stack_size_to_pos(node.get_offset())
                savesize = NodeUtils.stack_size_to_pos(node.get_size_save())
                if savesize > 1:
                    raise RuntimeError("Ah-ha!  A nested struct!  Now I have to code for that.  *sob*")
                if isinstance(varref.var(), VarStruct):
                    self.set_var_struct_name(varref.var())
                var: Variable = self.stack.get(removesize - savestart)
                varref.choose_struct_element(var)

    def at_last_command(self, node) -> bool:
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_else import AElse  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_if import AIf  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_sub import ASub  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if self.nodedata.get_pos(node) == self.current.get_end():
            return True
        if isinstance(self.current, ASwitchCase):
            parent = self.current.parent()
            if isinstance(parent, ASwitch) and parent.end() == self.nodedata.get_pos(node):
                return True
        if isinstance(self.current, ASub):
            next_node: Node = NodeUtils.get_next_command(node, self.nodedata)
            if next_node is None:
                return True
        if isinstance(self.current, AIf) or isinstance(self.current, AElse):
            next_node: Node = NodeUtils.get_next_command(node, self.nodedata)
            if next_node is not None and self.nodedata.get_pos(next_node) == self.current.get_end():
                return True
        return False

    def is_middle_of_return(self, node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_return_statement import AReturnStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.root.type().equals(0) and self.current.has_children() and isinstance(self.current.get_last_child(), AReturnStatement):
            return True
        if self.root.type().equals(0):
            next_node: Node = NodeUtils.get_next_command(node, self.nodedata)
            if next_node is not None and isinstance(next_node, AJumpCommand) and isinstance(self.nodedata.get_destination(next_node), AReturn):
                return True
        return False

    def current_contains_vars(self, vars_list) -> bool:
        for var in vars_list:
            if var.is_param():
                continue
            vardec: AVarDecl = self.vardecs.get(var)
            if vardec is None:
                continue
            parent: ScriptNode = vardec.parent()
            found = False
            while parent is not None and not found:
                if parent == self.current:
                    found = True
                else:
                    parent = parent.parent()
            if not found:
                return False
        return True

    def removing_switch_var(self, vars_list, node) -> bool:
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
        if len(vars_list) == 1 and self.current.has_children() and isinstance(self.current.get_last_child(), ASwitch):
            exp: AExpression = self.current.get_last_child().switch_exp()
            if isinstance(exp, AVarRef) and exp.var().equals(vars_list[0]):
                return True
        return False

    def get_earlier_dec(self, vardec, earliestdec: int) -> int:
        if vardec is None:
            return earliestdec
        location = self.current.get_child_location(vardec)
        if location == -1:
            return earliestdec
        if earliestdec == -1:
            return location
        if location < earliestdec:
            return location
        return earliestdec

    def get_previous_exp(self, pos: int):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl  # pyright: ignore[reportMissingImports]
        node: ScriptNode = self.current.get_previous_child(pos)
        if node is None:
            return None
        if isinstance(node, AVarDecl) and node.is_fcn_return():
            return node.exp()
        if not isinstance(node, AExpression):
            return None
        return node
