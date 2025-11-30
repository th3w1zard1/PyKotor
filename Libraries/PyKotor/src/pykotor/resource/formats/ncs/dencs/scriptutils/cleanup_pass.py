from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_sub import ASub  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptutils.sub_script_state import SubScriptState  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]

class CleanupPass:
    def __init__(self, root: ASub, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData, state: SubScriptState):
        self.root = root
        self.nodedata = nodedata
        self.subdata = subdata
        self.state = state

    def apply(self):
        self._check_sub_code_block()
        self._apply(self.root)

    def done(self):
        self.root = None
        self.nodedata = None
        self.subdata = None
        self.state = None

    def _check_sub_code_block(self):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_code_block import ACodeBlock  # pyright: ignore[reportMissingImports]
        if self.root.size() == 1 and isinstance(self.root.get_last_child(), ACodeBlock):
            block = self.root.remove_last_child()
            children = block.remove_children()
            self.root.add_children(children)

    def _apply(self, rootnode: ScriptRootNode):
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression_statement import AExpressionStatement  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_modify_exp import AModifyExp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch import ASwitch  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_decl import AVarDecl  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
        
        children = rootnode.get_children()
        for i, node1 in enumerate(children):
            # Process struct var declarations
            if isinstance(node1, AVarDecl):
                var = node1.var_var()
                if var is not None and var.is_struct():
                    struct = node1.var_var().varstruct()
                    structdec = AVarDecl(struct)
                    # Find and merge consecutive struct declarations
                    j = i + 1
                    while j < len(children) and isinstance(children[j], AVarDecl) and struct.equals(children[j].var_var().varstruct()):
                        children.pop(j)
                    if j < len(children):
                        structdec.parent(children[j].parent())
                    children[i] = structdec
                    node1 = structdec
            
            # Combine var decl with immediate assignment
            if isinstance(node1, AVarDecl) and i + 1 < len(children):
                node2 = children[i + 1]
                if isinstance(node2, AExpressionStatement) and isinstance(node2.exp(), AModifyExp):
                    modexp = node2.exp()
                    if node1.var_var() == modexp.var_ref().var():
                        children.pop(i + 1)
                        node1.initialize_exp(modexp.expression())
            
            # Wrap dangling expressions
            if self._is_dangling_expression(node1):
                expstm = AExpressionStatement(node1)
                expstm.parent(rootnode)
                children[i] = expstm
            
            # Recursively process nested structures
            if isinstance(node1, ScriptRootNode):
                self._apply(node1)
            if isinstance(node1, ASwitch):
                acase = None
                while True:
                    acase = node1.get_next_case(acase)
                    if acase is None:
                        break
                    self._apply(acase)

    def _is_dangling_expression(self, node) -> bool:
        from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
        return isinstance(node, AExpression)

