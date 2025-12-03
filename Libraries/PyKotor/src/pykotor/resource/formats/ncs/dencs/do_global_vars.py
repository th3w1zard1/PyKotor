from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.a_bp_command import ABpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_rsadd_command import ARsaddCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]

class DoGlobalVars(MainPass):
    def __init__(self, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData):
        from pykotor.resource.formats.ncs.dencs.main_pass import MainPass  # pyright: ignore[reportMissingImports]
        # Call protected constructor: MainPass(nodedata, subdata) 
        # This matches the protected constructor in Java
        MainPass.__init__(self, nodedata, subdata)
        self.freeze_stack = False
        self.state.set_var_prefix("GLOB_")

    def get_code(self) -> str:
        return self.state.to_string_globals()

    def out_a_bp_command(self, node: ABpCommand):
        self.freeze_stack = True

    def out_a_jump_to_subroutine(self, node: AJumpToSubroutine):
        self.freeze_stack = True

    def out_a_move_sp_command(self, node: AMoveSpCommand):
        if not self.freeze_stack:
            self.state.transform_move_sp(node)
            remove = NodeUtils.stack_offset_to_pos(node.get_offset())
            for _ in range(remove):
                self.stack.remove()

    def out_a_copy_down_sp_command(self, node: ACopyDownSpCommand):
        if not self.freeze_stack:
            self.state.transform_copy_down_sp(node)

    def out_a_rsadd_command(self, node: ARsaddCommand):
        if not self.freeze_stack:
            from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
            var = Variable(NodeUtils.get_type(node))
            self.stack.push(var)
            self.state.transform_rs_add(node)

    def get_stack(self) -> LocalVarStack:
        return self.stack

