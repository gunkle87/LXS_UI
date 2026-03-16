from dataclasses import dataclass, field
from typing import Dict, Optional
from ui.model.component_instance import ComponentInstance
from ui.model.geometry import get_lane_y_offset
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceVertex
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

    def clear(self):
        self.components = {}
        self.traces = {}
        self.nodes = {}

    def snapshot(self) -> dict:
        return {
            "components": [
                {
                    "id": component.id,
                    "type_id": component.type_id,
                    "x": component.x,
                    "y": component.y,
                }
                for component in self.components.values()
            ],
            "traces": [
                {
                    "id": trace.id,
                    "source": self._endpoint_snapshot(trace.source),
                    "target": self._endpoint_snapshot(trace.target),
                    "vertices": [
                        {"x": vertex.x, "y": vertex.y}
                        for vertex in trace.vertices
                    ],
                }
                for trace in self.traces.values()
            ],
            "nodes": [
                {
                    "id": node.id,
                    "x": node.x,
                    "y": node.y,
                    "owner_trace_id": node.owner_trace_id,
                }
                for node in self.nodes.values()
            ],
        }

    def restore_snapshot(self, snapshot: dict | None):
        restored = self.from_snapshot(snapshot or {})
        self.components = restored.components
        self.traces = restored.traces
        self.nodes = restored.nodes

    @classmethod
    def from_snapshot(cls, snapshot: dict):
        board_state = cls()
        for component_data in snapshot.get("components", []):
            board_state.add_component(
                ComponentInstance(
                    id=component_data["id"],
                    type_id=component_data["type_id"],
                    x=int(component_data["x"]),
                    y=int(component_data["y"]),
                )
            )
        for trace_data in snapshot.get("traces", []):
            board_state.add_trace(
                TraceInstance(
                    id=trace_data["id"],
                    source=cls._endpoint_from_snapshot(trace_data["source"]),
                    target=cls._endpoint_from_snapshot(trace_data["target"]),
                    vertices=[
                        TraceVertex(float(vertex["x"]), float(vertex["y"]))
                        for vertex in trace_data.get("vertices", [])
                    ],
                )
            )
        for node_data in snapshot.get("nodes", []):
            board_state.add_node(
                NodeInstance(
                    id=node_data["id"],
                    x=float(node_data["x"]),
                    y=float(node_data["y"]),
                    owner_trace_id=node_data["owner_trace_id"],
                )
            )
        return board_state

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

    def get_node_at(self, x: float, y: float, tolerance: float = 0.30) -> Optional[str]:
        for node_id, node in reversed(self.nodes.items()):
            if abs(node.x - x) <= tolerance and abs(node.y - y) <= tolerance:
                return node_id
        return None

    def iter_connected_trace_ids_for_component(self, component_id: str):
        for trace_id, trace in self.traces.items():
            endpoints = (trace.source, trace.target)
            if any(
                endpoint.terminal is not None and endpoint.terminal.component_id == component_id
                for endpoint in endpoints
            ):
                yield trace_id

    def iter_connected_trace_ids_for_node(self, node_id: str):
        node = self.nodes.get(node_id)
        if node is None:
            return

        yielded_trace_ids = set()

        owner_trace_id = node.owner_trace_id
        if owner_trace_id in self.traces:
            yielded_trace_ids.add(owner_trace_id)
            yield owner_trace_id

        for trace_id, trace in self.traces.items():
            if trace_id in yielded_trace_ids:
                continue
            endpoints = (trace.source, trace.target)
            if any(endpoint.node_id == node_id for endpoint in endpoints):
                yielded_trace_ids.add(trace_id)
                yield trace_id

    def get_owner_nodes_for_trace(self, trace_id: str):
        return [
            node
            for node in self.nodes.values()
            if node.owner_trace_id == trace_id
        ]

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

    @staticmethod
    def _endpoint_snapshot(endpoint: TraceEndpoint) -> dict:
        snapshot = {"terminal": None, "node_id": endpoint.node_id}
        if endpoint.terminal is not None:
            snapshot["terminal"] = {
                "component_id": endpoint.terminal.component_id,
                "is_input": endpoint.terminal.is_input,
                "index": endpoint.terminal.index,
            }
        return snapshot

    @staticmethod
    def _endpoint_from_snapshot(snapshot: dict) -> TraceEndpoint:
        terminal_data = snapshot.get("terminal")
        terminal = None
        if terminal_data is not None:
            terminal = TerminalRef(
                component_id=terminal_data["component_id"],
                is_input=bool(terminal_data["is_input"]),
                index=int(terminal_data["index"]),
            )
        return TraceEndpoint(terminal=terminal, node_id=snapshot.get("node_id"))
