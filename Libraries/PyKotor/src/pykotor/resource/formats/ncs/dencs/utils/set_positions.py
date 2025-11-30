"""Port of SetPositions.java from DeNCS.

See vendor/DeNCS/procyon/com/knights2end/nwscript/decomp/utils/SetPositions.java
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.dencs.analysis.pruned_reversed_depth_first_adapter import PrunedReversedDepthFirstAdapter

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData


class SetPositions(PrunedReversedDepthFirstAdapter):
    """Port of SetPositions.java from DeNCS."""

    def __init__(self, nodedata: NodeAnalysisData):
        super().__init__()
        self.nodedata: NodeAnalysisData = nodedata
        self.current_pos: int = 0

    def done(self):
        self.nodedata = None

    def default_in(self, node: Node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils
        pos = NodeUtils.get_command_pos(node)
        if pos > 0:
            self.current_pos = pos

    def default_out(self, node: Node):
        self.nodedata.set_pos(node, self.current_pos)
