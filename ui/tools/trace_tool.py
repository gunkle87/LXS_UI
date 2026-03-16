from typing import Optional

from ui.model.node_instance import NodeInstance
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TraceVertex


class TraceTool:
    def __init__(self, board_state, registry):
        self.board_state = board_state
        self.registry = registry
        self.start_endpoint: Optional[TraceEndpoint] = None
        self.preview_trace: Optional[TraceInstance] = None

    def click_endpoint(self, endpoint: Optional[TraceEndpoint]) -> Optional[TraceInstance]:
        if endpoint is None or not endpoint.is_valid():
            return None

        if self.start_endpoint is None:
            self.start_endpoint = endpoint
            self.preview_trace = None
            return None

        committed_trace = self.commit_trace(endpoint)
        return committed_trace

    def update_preview(self, endpoint: Optional[TraceEndpoint]) -> Optional[TraceInstance]:
        if self.start_endpoint is None or endpoint is None or not endpoint.is_valid():
            self.preview_trace = None
            return None

        self.preview_trace = TraceInstance(
            id="preview",
            source=self.start_endpoint,
            target=endpoint,
            vertices=self.autoroute(self.start_endpoint, endpoint),
        )
        return self.preview_trace

    def cancel_trace(self) -> None:
        self.start_endpoint = None
        self.preview_trace = None

    def commit_trace(self, end_endpoint: TraceEndpoint) -> Optional[TraceInstance]:
        if self.start_endpoint is None or not end_endpoint.is_valid():
            return None

        trace = TraceInstance(
            id=f"trace_{len(self.board_state.traces)}",
            source=self.start_endpoint,
            target=end_endpoint,
            vertices=self.autoroute(self.start_endpoint, end_endpoint),
        )
        if not trace.has_valid_endpoints() or not trace.is_orthogonal():
            return None

        self.board_state.add_trace(trace)
        self.cancel_trace()
        return trace

    def autoroute(self, start: TraceEndpoint, end: TraceEndpoint) -> list[TraceVertex]:
        start_pos = self.board_state.get_endpoint_position(start, self.registry)
        end_pos = self.board_state.get_endpoint_position(end, self.registry)
        if start_pos is None or end_pos is None:
            return []

        start_vertex = TraceVertex(*start_pos)
        end_vertex = TraceVertex(*end_pos)
        if start_vertex.x == end_vertex.x or start_vertex.y == end_vertex.y:
            return [start_vertex, end_vertex]

        bend_vertex = TraceVertex(end_vertex.x, start_vertex.y)
        return [start_vertex, bend_vertex, end_vertex]

    def create_node_on_trace(self, x: float, y: float, trace_id: Optional[str]) -> Optional[NodeInstance]:
        if trace_id is None:
            return None

        trace = self.board_state.traces.get(trace_id)
        if trace is None or not self.board_state.trace_contains_point(trace, x, y):
            return None

        existing_node = next(
            (
                node
                for node in self.board_state.nodes.values()
                if node.owner_trace_id == trace_id and node.x == x and node.y == y
            ),
            None,
        )
        if existing_node is not None:
            return existing_node

        node = NodeInstance(
            id=f"node_{len(self.board_state.nodes)}",
            x=float(x),
            y=float(y),
            owner_trace_id=trace_id,
        )
        self.board_state.add_node(node)
        return node

    def reroute_connected_component(self, component_id: str) -> None:
        for trace_id in self.board_state.iter_connected_trace_ids_for_component(component_id):
            self.reroute_trace(trace_id)

    def reroute_connected_node(self, node_id: str) -> None:
        for trace_id in self.board_state.iter_connected_trace_ids_for_node(node_id):
            self.reroute_trace(trace_id)

    def reroute_trace(self, trace_id: str) -> None:
        trace = self.board_state.traces.get(trace_id)
        if trace is None:
            return

        trace.vertices = self._autoroute_trace(trace)

    def _autoroute_trace(self, trace: TraceInstance) -> list[TraceVertex]:
        start_pos = self.board_state.get_endpoint_position(trace.source, self.registry)
        end_pos = self.board_state.get_endpoint_position(trace.target, self.registry)
        if start_pos is None or end_pos is None:
            return []

        via_points = [
            (node.x, node.y)
            for node in self.board_state.get_owner_nodes_for_trace(trace.id)
        ]

        positions = [start_pos, *via_points, end_pos]
        vertices: list[TraceVertex] = []
        for index in range(len(positions) - 1):
            segment_vertices = self._autoroute_points(positions[index], positions[index + 1])
            if index > 0 and segment_vertices:
                segment_vertices = segment_vertices[1:]
            vertices.extend(segment_vertices)
        return vertices

    @staticmethod
    def _autoroute_points(start_pos: tuple[float, float], end_pos: tuple[float, float]) -> list[TraceVertex]:
        start_vertex = TraceVertex(*start_pos)
        end_vertex = TraceVertex(*end_pos)
        if start_vertex.x == end_vertex.x or start_vertex.y == end_vertex.y:
            return [start_vertex, end_vertex]

        bend_vertex = TraceVertex(end_vertex.x, start_vertex.y)
        return [start_vertex, bend_vertex, end_vertex]
