"""Port of PrunedReversedDepthFirstAdapter.java from DeNCS.

See vendor/DeNCS/procyon/com/knights2end/nwscript/decomp/analysis/PrunedReversedDepthFirstAdapter.java
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import AnalysisAdapter

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock
    from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine
    from pykotor.resource.formats.ncs.dencs.node.node import Node
    from pykotor.resource.formats.ncs.dencs.node.start import Start


class PrunedReversedDepthFirstAdapter(AnalysisAdapter):
    """Port of PrunedReversedDepthFirstAdapter.java from DeNCS."""

    def in_start(self, node: Start):
        self.default_in(node)

    def out_start(self, node: Start):
        self.default_out(node)

    def default_in(self, node: Node):
        pass

    def default_out(self, node: Node):
        pass

    def case_start(self, node: Start):
        self.in_start(node)
        if node.get_p_program() is not None:
            node.get_p_program().apply(self)
        self.out_start(node)

    # AProgram
    def in_a_program(self, node: AProgram):
        self.default_in(node)

    def out_a_program(self, node: AProgram):
        self.default_out(node)

    def case_a_program(self, node: AProgram):
        self.in_a_program(node)
        temp = list(node.get_subroutine())
        for i in range(len(temp) - 1, -1, -1):
            temp[i].apply(self)
        if node.get_return() is not None:
            node.get_return().apply(self)
        if node.get_jump_to_subroutine() is not None:
            node.get_jump_to_subroutine().apply(self)
        self.out_a_program(node)

    # ASubroutine
    def in_a_subroutine(self, node: ASubroutine):
        self.default_in(node)

    def out_a_subroutine(self, node: ASubroutine):
        self.default_out(node)

    def case_a_subroutine(self, node: ASubroutine):
        self.in_a_subroutine(node)
        if node.get_return() is not None:
            node.get_return().apply(self)
        if node.get_command_block() is not None:
            node.get_command_block().apply(self)
        self.out_a_subroutine(node)

    # ACommandBlock
    def in_a_command_block(self, node: ACommandBlock):
        self.default_in(node)

    def out_a_command_block(self, node: ACommandBlock):
        self.default_out(node)

    def case_a_command_block(self, node: ACommandBlock):
        self.in_a_command_block(node)
        temp = list(node.get_cmd())
        for i in range(len(temp) - 1, -1, -1):
            temp[i].apply(self)
        self.out_a_command_block(node)

    # AAddVarCmd
    def in_a_add_var_cmd(self, node):
        self.default_in(node)

    def out_a_add_var_cmd(self, node):
        self.default_out(node)

    def case_a_add_var_cmd(self, node):
        self.in_a_add_var_cmd(node)
        if node.get_rsadd_command() is not None:
            node.get_rsadd_command().apply(self)
        self.out_a_add_var_cmd(node)

    # AActionJumpCmd
    def in_a_action_jump_cmd(self, node):
        self.default_in(node)

    def out_a_action_jump_cmd(self, node):
        self.default_out(node)

    def case_a_action_jump_cmd(self, node):
        self.in_a_action_jump_cmd(node)
        if node.get_return() is not None:
            node.get_return().apply(self)
        if node.get_command_block() is not None:
            node.get_command_block().apply(self)
        if node.get_jump_command() is not None:
            node.get_jump_command().apply(self)
        if node.get_store_state_command() is not None:
            node.get_store_state_command().apply(self)
        self.out_a_action_jump_cmd(node)

    # AConstCmd
    def in_a_const_cmd(self, node):
        self.default_in(node)

    def out_a_const_cmd(self, node):
        self.default_out(node)

    def case_a_const_cmd(self, node):
        self.in_a_const_cmd(node)
        if node.get_const_command() is not None:
            node.get_const_command().apply(self)
        self.out_a_const_cmd(node)

    # ACopydownspCmd
    def in_a_copydownsp_cmd(self, node):
        self.default_in(node)

    def out_a_copydownsp_cmd(self, node):
        self.default_out(node)

    def case_a_copydownsp_cmd(self, node):
        self.in_a_copydownsp_cmd(node)
        if node.get_copy_down_sp_command() is not None:
            node.get_copy_down_sp_command().apply(self)
        self.out_a_copydownsp_cmd(node)

    # ACopytopspCmd
    def in_a_copytopsp_cmd(self, node):
        self.default_in(node)

    def out_a_copytopsp_cmd(self, node):
        self.default_out(node)

    def case_a_copytopsp_cmd(self, node):
        self.in_a_copytopsp_cmd(node)
        if node.get_copy_top_sp_command() is not None:
            node.get_copy_top_sp_command().apply(self)
        self.out_a_copytopsp_cmd(node)

    # ACopydownbpCmd
    def in_a_copydownbp_cmd(self, node):
        self.default_in(node)

    def out_a_copydownbp_cmd(self, node):
        self.default_out(node)

    def case_a_copydownbp_cmd(self, node):
        self.in_a_copydownbp_cmd(node)
        if node.get_copy_down_bp_command() is not None:
            node.get_copy_down_bp_command().apply(self)
        self.out_a_copydownbp_cmd(node)

    # ACopytopbpCmd
    def in_a_copytopbp_cmd(self, node):
        self.default_in(node)

    def out_a_copytopbp_cmd(self, node):
        self.default_out(node)

    def case_a_copytopbp_cmd(self, node):
        self.in_a_copytopbp_cmd(node)
        if node.get_copy_top_bp_command() is not None:
            node.get_copy_top_bp_command().apply(self)
        self.out_a_copytopbp_cmd(node)

    # ACondJumpCmd
    def in_a_cond_jump_cmd(self, node):
        self.default_in(node)

    def out_a_cond_jump_cmd(self, node):
        self.default_out(node)

    def case_a_cond_jump_cmd(self, node):
        self.in_a_cond_jump_cmd(node)
        if node.get_conditional_jump_command() is not None:
            node.get_conditional_jump_command().apply(self)
        self.out_a_cond_jump_cmd(node)

    # AJumpCmd
    def in_a_jump_cmd(self, node):
        self.default_in(node)

    def out_a_jump_cmd(self, node):
        self.default_out(node)

    def case_a_jump_cmd(self, node):
        self.in_a_jump_cmd(node)
        if node.get_jump_command() is not None:
            node.get_jump_command().apply(self)
        self.out_a_jump_cmd(node)

    # AJumpSubCmd
    def in_a_jump_sub_cmd(self, node):
        self.default_in(node)

    def out_a_jump_sub_cmd(self, node):
        self.default_out(node)

    def case_a_jump_sub_cmd(self, node):
        self.in_a_jump_sub_cmd(node)
        if node.get_jump_to_subroutine() is not None:
            node.get_jump_to_subroutine().apply(self)
        self.out_a_jump_sub_cmd(node)

    # AMovespCmd
    def in_a_movesp_cmd(self, node):
        self.default_in(node)

    def out_a_movesp_cmd(self, node):
        self.default_out(node)

    def case_a_movesp_cmd(self, node):
        self.in_a_movesp_cmd(node)
        if node.get_move_sp_command() is not None:
            node.get_move_sp_command().apply(self)
        self.out_a_movesp_cmd(node)

    # ALogiiCmd
    def in_a_logii_cmd(self, node):
        self.default_in(node)

    def out_a_logii_cmd(self, node):
        self.default_out(node)

    def case_a_logii_cmd(self, node):
        self.in_a_logii_cmd(node)
        if node.get_logii_command() is not None:
            node.get_logii_command().apply(self)
        self.out_a_logii_cmd(node)

    # AUnaryCmd
    def in_a_unary_cmd(self, node):
        self.default_in(node)

    def out_a_unary_cmd(self, node):
        self.default_out(node)

    def case_a_unary_cmd(self, node):
        self.in_a_unary_cmd(node)
        if node.get_unary_command() is not None:
            node.get_unary_command().apply(self)
        self.out_a_unary_cmd(node)

    # ABinaryCmd
    def in_a_binary_cmd(self, node):
        self.default_in(node)

    def out_a_binary_cmd(self, node):
        self.default_out(node)

    def case_a_binary_cmd(self, node):
        self.in_a_binary_cmd(node)
        if node.get_binary_command() is not None:
            node.get_binary_command().apply(self)
        self.out_a_binary_cmd(node)

    # ADestructCmd
    def in_a_destruct_cmd(self, node):
        self.default_in(node)

    def out_a_destruct_cmd(self, node):
        self.default_out(node)

    def case_a_destruct_cmd(self, node):
        self.in_a_destruct_cmd(node)
        if node.get_destruct_command() is not None:
            node.get_destruct_command().apply(self)
        self.out_a_destruct_cmd(node)

    # ABpCmd
    def in_a_bp_cmd(self, node):
        self.default_in(node)

    def out_a_bp_cmd(self, node):
        self.default_out(node)

    def case_a_bp_cmd(self, node):
        self.in_a_bp_cmd(node)
        if node.get_bp_command() is not None:
            node.get_bp_command().apply(self)
        self.out_a_bp_cmd(node)

    # AActionCmd
    def in_a_action_cmd(self, node):
        self.default_in(node)

    def out_a_action_cmd(self, node):
        self.default_out(node)

    def case_a_action_cmd(self, node):
        self.in_a_action_cmd(node)
        if node.get_action_command() is not None:
            node.get_action_command().apply(self)
        self.out_a_action_cmd(node)

    # AStackOpCmd
    def in_a_stack_op_cmd(self, node):
        self.default_in(node)

    def out_a_stack_op_cmd(self, node):
        self.default_out(node)

    def case_a_stack_op_cmd(self, node):
        self.in_a_stack_op_cmd(node)
        if node.get_stack_command() is not None:
            node.get_stack_command().apply(self)
        self.out_a_stack_op_cmd(node)

    # AReturnCmd
    def in_a_return_cmd(self, node):
        self.default_in(node)

    def out_a_return_cmd(self, node):
        self.default_out(node)

    def case_a_return_cmd(self, node):
        self.in_a_return_cmd(node)
        if node.get_return() is not None:
            node.get_return().apply(self)
        self.out_a_return_cmd(node)

    # AStoreStateCmd
    def in_a_store_state_cmd(self, node):
        self.default_in(node)

    def out_a_store_state_cmd(self, node):
        self.default_out(node)

    def case_a_store_state_cmd(self, node):
        self.in_a_store_state_cmd(node)
        if node.get_store_state_command() is not None:
            node.get_store_state_command().apply(self)
        self.out_a_store_state_cmd(node)

    # ARsaddCmd
    def in_a_rsadd_cmd(self, node):
        self.default_in(node)

    def out_a_rsadd_cmd(self, node):
        self.default_out(node)

    def case_a_rsadd_cmd(self, node):
        self.in_a_rsadd_cmd(node)
        if node.get_rsadd_command() is not None:
            node.get_rsadd_command().apply(self)
        self.out_a_rsadd_cmd(node)

    # AConditionalJumpCommand
    def in_a_conditional_jump_command(self, node):
        self.default_in(node)

    def out_a_conditional_jump_command(self, node):
        self.default_out(node)

    def case_a_conditional_jump_command(self, node):
        self.in_a_conditional_jump_command(node)
        self.out_a_conditional_jump_command(node)

    # AJumpCommand
    def in_a_jump_command(self, node):
        self.default_in(node)

    def out_a_jump_command(self, node):
        self.default_out(node)

    def case_a_jump_command(self, node):
        self.in_a_jump_command(node)
        self.out_a_jump_command(node)

    # AJumpToSubroutine
    def in_a_jump_to_subroutine(self, node):
        self.default_in(node)

    def out_a_jump_to_subroutine(self, node):
        self.default_out(node)

    def case_a_jump_to_subroutine(self, node):
        self.in_a_jump_to_subroutine(node)
        self.out_a_jump_to_subroutine(node)

    # AReturn
    def in_a_return(self, node):
        self.default_in(node)

    def out_a_return(self, node):
        self.default_out(node)

    def case_a_return(self, node):
        self.in_a_return(node)
        self.out_a_return(node)

    # ACopyDownSpCommand
    def in_a_copy_down_sp_command(self, node):
        self.default_in(node)

    def out_a_copy_down_sp_command(self, node):
        self.default_out(node)

    def case_a_copy_down_sp_command(self, node):
        self.in_a_copy_down_sp_command(node)
        self.out_a_copy_down_sp_command(node)

    # ACopyTopSpCommand
    def in_a_copy_top_sp_command(self, node):
        self.default_in(node)

    def out_a_copy_top_sp_command(self, node):
        self.default_out(node)

    def case_a_copy_top_sp_command(self, node):
        self.in_a_copy_top_sp_command(node)
        self.out_a_copy_top_sp_command(node)

    # ACopyDownBpCommand
    def in_a_copy_down_bp_command(self, node):
        self.default_in(node)

    def out_a_copy_down_bp_command(self, node):
        self.default_out(node)

    def case_a_copy_down_bp_command(self, node):
        self.in_a_copy_down_bp_command(node)
        self.out_a_copy_down_bp_command(node)

    # ACopyTopBpCommand
    def in_a_copy_top_bp_command(self, node):
        self.default_in(node)

    def out_a_copy_top_bp_command(self, node):
        self.default_out(node)

    def case_a_copy_top_bp_command(self, node):
        self.in_a_copy_top_bp_command(node)
        self.out_a_copy_top_bp_command(node)

    # AMoveSpCommand
    def in_a_move_sp_command(self, node):
        self.default_in(node)

    def out_a_move_sp_command(self, node):
        self.default_out(node)

    def case_a_move_sp_command(self, node):
        self.in_a_move_sp_command(node)
        self.out_a_move_sp_command(node)

    # ARsaddCommand
    def in_a_rsadd_command(self, node):
        self.default_in(node)

    def out_a_rsadd_command(self, node):
        self.default_out(node)

    def case_a_rsadd_command(self, node):
        self.in_a_rsadd_command(node)
        self.out_a_rsadd_command(node)

    # AConstCommand
    def in_a_const_command(self, node):
        self.default_in(node)

    def out_a_const_command(self, node):
        self.default_out(node)

    def case_a_const_command(self, node):
        self.in_a_const_command(node)
        self.out_a_const_command(node)

    # AActionCommand
    def in_a_action_command(self, node):
        self.default_in(node)

    def out_a_action_command(self, node):
        self.default_out(node)

    def case_a_action_command(self, node):
        self.in_a_action_command(node)
        self.out_a_action_command(node)

    # ALogiiCommand
    def in_a_logii_command(self, node):
        self.default_in(node)

    def out_a_logii_command(self, node):
        self.default_out(node)

    def case_a_logii_command(self, node):
        self.in_a_logii_command(node)
        self.out_a_logii_command(node)

    # ABinaryCommand
    def in_a_binary_command(self, node):
        self.default_in(node)

    def out_a_binary_command(self, node):
        self.default_out(node)

    def case_a_binary_command(self, node):
        self.in_a_binary_command(node)
        self.out_a_binary_command(node)

    # AUnaryCommand
    def in_a_unary_command(self, node):
        self.default_in(node)

    def out_a_unary_command(self, node):
        self.default_out(node)

    def case_a_unary_command(self, node):
        self.in_a_unary_command(node)
        self.out_a_unary_command(node)

    # AStackCommand
    def in_a_stack_command(self, node):
        self.default_in(node)

    def out_a_stack_command(self, node):
        self.default_out(node)

    def case_a_stack_command(self, node):
        self.in_a_stack_command(node)
        self.out_a_stack_command(node)

    # ADestructCommand
    def in_a_destruct_command(self, node):
        self.default_in(node)

    def out_a_destruct_command(self, node):
        self.default_out(node)

    def case_a_destruct_command(self, node):
        self.in_a_destruct_command(node)
        self.out_a_destruct_command(node)

    # ABpCommand
    def in_a_bp_command(self, node):
        self.default_in(node)

    def out_a_bp_command(self, node):
        self.default_out(node)

    def case_a_bp_command(self, node):
        self.in_a_bp_command(node)
        self.out_a_bp_command(node)

    # AStoreStateCommand
    def in_a_store_state_command(self, node):
        self.default_in(node)

    def out_a_store_state_command(self, node):
        self.default_out(node)

    def case_a_store_state_command(self, node):
        self.in_a_store_state_command(node)
        self.out_a_store_state_command(node)
