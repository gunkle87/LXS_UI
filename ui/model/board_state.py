from dataclasses import dataclass, field
from typing import Dict
from ui.model.component_instance import ComponentInstance
from ui.model.trace_instance import TraceInstance
from ui.model.node_instance import NodeInstance

@dataclass
class BoardState:
    components: Dict[str, ComponentInstance] = field(default_factory=dict)
    traces: Dict[str, TraceInstance] = field(default_factory=dict)
    nodes: Dict[str, NodeInstance] = field(default_factory=dict)
    
    def add_component(self, comp: ComponentInstance):
        self.components[comp.id] = comp
        
    def add_trace(self, trace: TraceInstance):
        self.traces[trace.id] = trace
        
    def add_node(self, node: NodeInstance):
        self.nodes[node.id] = node
