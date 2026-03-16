from dataclasses import dataclass, field
from typing import Dict, Optional
from ui.model.component_instance import ComponentInstance
from ui.model.geometry import get_lane_y_offset
from ui.model.primitive_definition import PrimitiveDefinition
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
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

    def get_terminal_position(self, terminal: TerminalRef, registry) -> Optional[tuple[float, float]]:
        component = self.components.get(terminal.component_id)
        if component is None:
            return None

        primitive = registry.get_primitive(component.type_id)
        if primitive is None:
            return None

        bounds = component.get_bounds(primitive)
        if terminal.is_input:
            total_terminals = primitive.num_inputs
            x = component.x
        else:
            total_terminals = primitive.num_outputs
            x = component.x + bounds.width

        y = component.y + get_lane_y_offset(terminal.index, total_terminals, bounds.height)
        return float(x), float(y)

    def get_endpoint_position(self, endpoint: TraceEndpoint, registry) -> Optional[tuple[float, float]]:
        if not endpoint.is_valid():
            return None
        if endpoint.terminal is not None:
            return self.get_terminal_position(endpoint.terminal, registry)

        node = self.nodes.get(endpoint.node_id)
        if node is None:
            return None
        return node.x, node.y

    def trace_contains_point(self, trace: TraceInstance, x: float, y: float, tolerance: float = 0.20) -> bool:
        for start, end in trace.segments():
            if self._point_on_segment(start.x, start.y, end.x, end.y, x, y, tolerance):
                return True
        return False

    def get_trace_at(self, x: float, y: float, tolerance: float = 0.20) -> Optional[str]:
        for trace_id, trace in reversed(self.traces.items()):
            if self.trace_contains_point(trace, x, y, tolerance):
                return trace_id
        return None

    def iter_connected_trace_ids_for_component(self, component_id: str):
        for trace_id, trace in self.traces.items():
            endpoints = (trace.source, trace.target)
            if any(
                endpoint.terminal is not None and endpoint.terminal.component_id == component_id
                for endpoint in endpoints
            ):
                yield trace_id

    def traces_share_semantic_connection(self, left_trace_id: str, right_trace_id: str) -> bool:
        left_trace = self.traces.get(left_trace_id)
        right_trace = self.traces.get(right_trace_id)
        if left_trace is None or right_trace is None:
            return False

        left_nodes = {
            endpoint.node_id
            for endpoint in (left_trace.source, left_trace.target)
            if endpoint.node_id is not None
        }
        right_nodes = {
            endpoint.node_id
            for endpoint in (right_trace.source, right_trace.target)
            if endpoint.node_id is not None
        }
        return bool(left_nodes & right_nodes)

    @staticmethod
    def _point_on_segment(
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        px: float,
        py: float,
        tolerance: float,
    ) -> bool:
        if x1 == x2:
            if abs(px - x1) > tolerance:
                return False
            return min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance
        if y1 == y2:
            if abs(py - y1) > tolerance:
                return False
            return min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance
        return False
