from PySide6.QtCore import QPointF, Qt

from ui.input_controller import InputController
from ui.model.board_state import BoardState
from ui.model.component_instance import ComponentInstance
from ui.model.node_instance import NodeInstance
from ui.model.selection_state import SelectionState
from ui.model.tool_state import ToolState
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TraceVertex
from ui.services.primitive_registry import PrimitiveRegistry


class MockTheme:
    grid_size = 20


class MockRenderer:
    theme = MockTheme()


class MockCamera:
    def view_to_scene(self, point):
        return point


class MockBoardView:
    def __init__(self):
        self.camera = MockCamera()
        self.renderer = MockRenderer()
        self.input_controller = None
        self.update_calls = 0

    def update(self):
        self.update_calls += 1


class MockEvent:
    def __init__(self, button_val=Qt.LeftButton, pos_val=QPointF(0, 0), key_val=0):
        self._button = button_val
        self._pos = pos_val
        self._key = key_val

    def button(self):
        return self._button

    def position(self):
        return self._pos

    def key(self):
        return self._key


def to_pixels(cell_x, cell_y):
    return QPointF(cell_x * 20.0, cell_y * 20.0)


def build_controller():
    board_view = MockBoardView()
    board_state = BoardState()
    selection_state = SelectionState()
    tool_state = ToolState()
    registry = PrimitiveRegistry()
    controller = InputController(board_view, board_state, selection_state, tool_state, registry)
    return board_view, board_state, selection_state, tool_state, registry, controller


def seed_trace_components(board_state):
    board_state.add_component(ComponentInstance(id="src", type_id="input", x=0, y=0))
    board_state.add_component(ComponentInstance(id="dst", type_id="output", x=4, y=0))


def create_trace_with_controller(controller, tool_state, board_state):
    seed_trace_components(board_state)
    tool_state.active_tool_id = "trace"

    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(1.0, 0.25)))
    controller.handle_mouse_move(MockEvent(Qt.LeftButton, to_pixels(4.0, 0.25)))
    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(4.0, 0.25)))
    return next(iter(board_state.traces.values()))


def test_trace_endpoint_validity_rules():
    terminal = TerminalRef(component_id="src", is_input=False, index=0)
    assert TraceEndpoint(terminal=terminal).is_valid()
    assert TraceEndpoint(node_id="node_0").is_valid()
    assert not TraceEndpoint().is_valid()
    assert not TraceEndpoint(terminal=terminal, node_id="node_0").is_valid()


def test_trace_creation_requires_real_endpoints_and_builds_orthogonal_path():
    board_view, board_state, selection_state, tool_state, _, controller = build_controller()
    seed_trace_components(board_state)
    tool_state.active_tool_id = "trace"

    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(2.0, 2.0)))
    assert controller.trace_tool.start_endpoint is None
    assert len(board_state.traces) == 0

    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(1.0, 0.25)))
    assert controller.trace_tool.start_endpoint is not None

    controller.handle_mouse_move(MockEvent(Qt.LeftButton, to_pixels(4.0, 0.25)))
    assert controller.trace_tool.preview_trace is not None
    assert controller.trace_tool.preview_trace.is_orthogonal()

    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(4.0, 0.25)))
    assert len(board_state.traces) == 1

    trace = next(iter(board_state.traces.values()))
    assert trace.has_valid_endpoints()
    assert trace.is_orthogonal()
    assert selection_state.selected_trace_ids == [trace.id]
    assert selection_state.selected_component_ids == []
    assert selection_state.selected_node_ids == []
    assert controller.trace_tool.start_endpoint is None
    assert board_view.update_calls >= 2


def test_trace_body_selection_and_node_creation_use_owner_trace():
    _, board_state, selection_state, tool_state, _, controller = build_controller()
    trace = create_trace_with_controller(controller, tool_state, board_state)

    tool_state.active_tool_id = "select"
    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(2.5, 0.25)))
    assert selection_state.selected_trace_ids == [trace.id]

    controller.handle_mouse_press(MockEvent(Qt.RightButton, to_pixels(2.5, 0.25)))
    assert len(board_state.nodes) == 1

    node = next(iter(board_state.nodes.values()))
    assert node.owner_trace_id == trace.id
    assert selection_state.selected_node_ids == [node.id]
    assert selection_state.selected_trace_ids == []


def test_crossings_remain_non_semantic_without_explicit_shared_node():
    _, board_state, _, _, _, _ = build_controller()
    board_state.add_node(NodeInstance(id="left_a", x=1.0, y=0.25, owner_trace_id="trace_a"))
    board_state.add_node(NodeInstance(id="right_a", x=4.0, y=0.25, owner_trace_id="trace_a"))
    board_state.add_node(NodeInstance(id="top_b", x=2.5, y=-1.0, owner_trace_id="trace_b"))
    board_state.add_node(NodeInstance(id="bottom_b", x=2.5, y=1.0, owner_trace_id="trace_b"))

    trace_a = TraceInstance(
        id="trace_a",
        source=TraceEndpoint(node_id="left_a"),
        target=TraceEndpoint(node_id="right_a"),
        vertices=[TraceVertex(1.0, 0.25), TraceVertex(4.0, 0.25)],
    )
    trace_b = TraceInstance(
        id="trace_b",
        source=TraceEndpoint(node_id="top_b"),
        target=TraceEndpoint(node_id="bottom_b"),
        vertices=[TraceVertex(2.5, -1.0), TraceVertex(2.5, 1.0)],
    )
    board_state.add_trace(trace_a)
    board_state.add_trace(trace_b)

    assert board_state.trace_contains_point(trace_a, 2.5, 0.25)
    assert board_state.trace_contains_point(trace_b, 2.5, 0.25)
    assert not board_state.traces_share_semantic_connection("trace_a", "trace_b")


def test_reroute_on_component_move_updates_connected_trace():
    _, board_state, selection_state, tool_state, registry, controller = build_controller()
    trace = create_trace_with_controller(controller, tool_state, board_state)
    original_vertices = [(vertex.x, vertex.y) for vertex in trace.vertices]

    tool_state.active_tool_id = "select"
    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(4.25, 0.25)))
    controller.handle_mouse_move(MockEvent(Qt.LeftButton, to_pixels(6.25, 2.25)))
    controller.handle_mouse_release(MockEvent(Qt.LeftButton, to_pixels(6.25, 2.25)))

    moved_component = board_state.components["dst"]
    assert (moved_component.x, moved_component.y) == (6, 2)
    assert selection_state.selected_component_ids == ["dst"]

    rerouted_vertices = [(vertex.x, vertex.y) for vertex in trace.vertices]
    assert rerouted_vertices != original_vertices
    assert trace.is_orthogonal()
    assert trace.vertices[-1] == TraceVertex(*board_state.get_endpoint_position(trace.target, registry))
