from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]

class AnalysisAdapter:
    def __init__(self):
        self._in: dict[Node, Any] = {}
        self._out: dict[Node, Any] = {}

    def get_in(self, node: Node) -> Any:
        return self._in.get(node)

    def set_in(self, node: Node, value: Any):
        if value is not None:
            self._in[node] = value
        elif node in self._in:
            del self._in[node]

    def get_out(self, node: Node) -> Any:
        return self._out.get(node)

    def set_out(self, node: Node, value: Any):
        if value is not None:
            self._out[node] = value
        elif node in self._out:
            del self._out[node]

    def default_in(self, node: Node):
        pass

    def default_out(self, node: Node):
        pass

    def default_case(self, node: Node):
        pass

    def case_node(self, node: Node):
        self.default_case(node)

    def case_start(self, node):
        self.default_case(node)

    def case_eof(self, node):
        self.default_case(node)

    def case_a_program(self, node):
        self.default_case(node)

    def case_a_subroutine(self, node):
        self.default_case(node)

    def case_a_command_block(self, node):
        self.default_case(node)

    def case_a_const_cmd(self, node):
        self.default_case(node)

    def case_a_jump_cmd(self, node):
        self.default_case(node)

    def case_a_jump_sub_cmd(self, node):
        self.default_case(node)

    def case_a_return_cmd(self, node):
        self.default_case(node)

    def case_a_const_command(self, node):
        self.default_case(node)

    def case_a_jump_command(self, node):
        self.default_case(node)

    def case_a_jump_to_subroutine(self, node):
        self.default_case(node)

    def case_a_return(self, node):
        self.default_case(node)

    def case_a_int_constant(self, node):
        self.default_case(node)

    def case_a_float_constant(self, node):
        self.default_case(node)

    def case_a_string_constant(self, node):
        self.default_case(node)

    def case_t_const(self, node):
        self.default_case(node)

    def case_t_semi(self, node):
        self.default_case(node)

    def case_t_jmp(self, node):
        self.default_case(node)

    def case_t_jsr(self, node):
        self.default_case(node)

    def case_t_retn(self, node):
        self.default_case(node)

    def case_t_integer_constant(self, node):
        self.default_case(node)

    def case_t_float_constant(self, node):
        self.default_case(node)

    def case_t_string_literal(self, node):
        self.default_case(node)

    def case_t_action(self, node):
        self.default_case(node)

    def case_t_cpdownsp(self, node):
        self.default_case(node)

    def case_t_cptopsp(self, node):
        self.default_case(node)

    def case_t_movsp(self, node):
        self.default_case(node)

    def case_t_rsadd(self, node):
        self.default_case(node)

    def case_a_action_cmd(self, node):
        self.default_case(node)

    def case_a_action_command(self, node):
        self.default_case(node)

    def case_a_copydownsp_cmd(self, node):
        self.default_case(node)

    def case_a_copytopsp_cmd(self, node):
        self.default_case(node)

    def case_a_copy_down_sp_command(self, node):
        self.default_case(node)

    def case_a_copy_top_sp_command(self, node):
        self.default_case(node)

    def case_a_movesp_cmd(self, node):
        self.default_case(node)

    def case_a_move_sp_command(self, node):
        self.default_case(node)

    def case_a_rsadd_cmd(self, node):
        self.default_case(node)

    def case_a_rsadd_command(self, node):
        self.default_case(node)

    def case_t_jz(self, node):
        self.default_case(node)

    def case_t_jnz(self, node):
        self.default_case(node)

    def case_a_zero_jump_if(self, node):
        self.default_case(node)

    def case_a_nonzero_jump_if(self, node):
        self.default_case(node)

    def case_a_conditional_jump_command(self, node):
        self.default_case(node)

    def case_a_cond_jump_cmd(self, node):
        self.default_case(node)

    def case_a_copydownbp_cmd(self, node):
        self.default_case(node)

    def case_a_copytopbp_cmd(self, node):
        self.default_case(node)

    def case_a_copy_down_bp_command(self, node):
        self.default_case(node)

    def case_a_copy_top_bp_command(self, node):
        self.default_case(node)

    def case_t_cpdownbp(self, node):
        self.default_case(node)

    def case_t_cptopbp(self, node):
        self.default_case(node)

    def case_a_destruct_cmd(self, node):
        self.default_case(node)

    def case_a_destruct_command(self, node):
        self.default_case(node)

    def case_t_destruct(self, node):
        self.default_case(node)

    def case_a_bp_cmd(self, node):
        self.default_case(node)

    def case_a_bp_command(self, node):
        self.default_case(node)

    def case_a_savebp_bp_op(self, node):
        self.default_case(node)

    def case_a_restorebp_bp_op(self, node):
        self.default_case(node)

    def case_t_savebp(self, node):
        self.default_case(node)

    def case_t_restorebp(self, node):
        self.default_case(node)

    def case_a_store_state_cmd(self, node):
        self.default_case(node)

    def case_a_store_state_command(self, node):
        self.default_case(node)

    def case_t_storestate(self, node):
        self.default_case(node)

    def case_a_binary_command(self, node):
        self.default_case(node)

    def case_a_unary_command(self, node):
        self.default_case(node)

    def case_a_logii_command(self, node):
        self.default_case(node)

    def case_a_binary_cmd(self, node):
        self.default_case(node)

    def case_a_unary_cmd(self, node):
        self.default_case(node)

    def case_a_logii_cmd(self, node):
        self.default_case(node)

