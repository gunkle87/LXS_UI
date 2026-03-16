from PySide6.QtCore import QPointF
from PySide6.QtCore import Qt

from ui.input_controller import InputController
from ui.model.board_state import BoardState
from ui.model.component_instance import ComponentInstance
from ui.model.selection_state import SelectionState
from ui.model.tool_state import ToolState
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
    return board_view, board_state, selection_state, tool_state, controller


def create_trace_and_node(controller, board_state, tool_state):
    board_state.add_component(ComponentInstance(id="src", type_id="input", x=0, y=0))
    board_state.add_component(ComponentInstance(id="dst", type_id="output", x=4, y=0))

    tool_state.active_tool_id = "trace"
    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(1.0, 0.25)))
    controller.handle_mouse_move(MockEvent(Qt.LeftButton, to_pixels(4.0, 0.25)))
    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(4.0, 0.25)))

    tool_state.active_tool_id = "select"
    controller.handle_mouse_press(MockEvent(Qt.RightButton, to_pixels(2.5, 0.25)))

    trace = next(iter(board_state.traces.values()))
    node = next(iter(board_state.nodes.values()))
    return trace, node


def test_node_drag_triggers_reroute_for_owner_trace():
    board_view, board_state, selection_state, tool_state, controller = build_controller()
    trace, node = create_trace_and_node(controller, board_state, tool_state)
    original_vertices = [(vertex.x, vertex.y) for vertex in trace.vertices]

    controller.handle_mouse_press(MockEvent(Qt.LeftButton, to_pixels(2.5, 0.25)))
    controller.handle_mouse_move(MockEvent(Qt.LeftButton, to_pixels(2.75, 1.25)))
    controller.handle_mouse_release(MockEvent(Qt.LeftButton, to_pixels(2.75, 1.25)))

    assert (node.x, node.y) == (2.75, 1.25)
    assert selection_state.selected_node_ids == [node.id]
    assert [(vertex.x, vertex.y) for vertex in trace.vertices] != original_vertices
    assert any((vertex.x, vertex.y) == (node.x, node.y) for vertex in trace.vertices)
    assert board_view.update_calls >= 3
