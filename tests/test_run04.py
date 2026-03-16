import pytest
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QApplication
from ui.model.geometry import calculate_component_width, calculate_component_depth, get_lane_y_offset
from ui.model.board_state import BoardState
from ui.model.selection_state import SelectionState
from ui.model.tool_state import ToolState
from ui.services.primitive_registry import PrimitiveRegistry
from ui.input_controller import InputController
from ui.widgets.primitive_dropdown import PrimitiveDropdown

def test_footprint_sizing():
    # width is always 1
    assert calculate_component_width() == 1
    
    # depth = max(1, ceil(max(inputs, outputs) / 2))
    assert calculate_component_depth(0, 1) == 1
    assert calculate_component_depth(2, 1) == 1
    assert calculate_component_depth(3, 1) == 2
    assert calculate_component_depth(1, 4) == 2
    assert calculate_component_depth(5, 5) == 3

def test_terminal_packing():
    # test lane y offset
    # 0 -> 0.25 (upper)
    # 1 -> 0.75 (lower)
    # 2 -> 1.25 (upper)
    # 3 -> 1.75 (lower)
    assert get_lane_y_offset(0, 1, 1) == 0.25
    assert get_lane_y_offset(1, 2, 1) == 0.75
    assert get_lane_y_offset(2, 3, 2) == 1.25
    assert get_lane_y_offset(3, 4, 2) == 1.75

class MockTheme:
    grid_size = 20

class MockRenderer:
    theme = MockTheme()

class MockCamera:
    def view_to_scene(self, pt):
        return pt

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
    def button(self): return self._button
    def position(self): return self._pos
    def key(self): return self._key

def test_placement_snapping_and_selection():
    board_view = MockBoardView()
    board_state = BoardState()
    selection_state = SelectionState()
    tool_state = ToolState()
    registry = PrimitiveRegistry()
    
    controller = InputController(board_view, board_state, selection_state, tool_state, registry)
    
    # Enable place tool with 'and' gate
    tool_state.active_tool_id = "place"
    tool_state.selected_primitive_id = "and"
    
    # Click at pixel (25, 25)
    # grid_size = 20, so 25/20 = 1.25 -> rounded to 1
    event = MockEvent(Qt.LeftButton, QPointF(25, 25))
    controller.handle_mouse_press(event)
    
    # Component should be placed at grid (1, 1)
    assert len(board_state.components) == 1
    comp = list(board_state.components.values())[0]
    assert comp.x == 1
    assert comp.y == 1
    assert comp.type_id == "and"
    
    # Should be selected
    assert comp.id in selection_state.selected_component_ids
    
    # Switch to select tool
    tool_state.active_tool_id = "select"
    tool_state.selected_primitive_id = None
    
    # Click outside to deselect (0, 0)
    event2 = MockEvent(Qt.LeftButton, QPointF(0, 0))
    controller.handle_mouse_press(event2)
    assert len(selection_state.selected_component_ids) == 0
    
    # Click on component to select it again
    # Component is at x=1, y=1, width=1, height=1
    # grid coords are 1,1
    # Pixel 30, 30 -> grid 1.5, 1.5 -> round to 2? Wait!
    # round(30/20) = 2, which is outside width=1 (1 to 2).
    # Component at x=1 covers x from 1 to 2. y from 1 to 2.
    # Grid click at (25, 25) -> grid (1, 1). Component bounds: x in [1, 2), y in [1, 2).
    # Click on (25, 25) will hit grid 1, 1.
    event3 = MockEvent(Qt.LeftButton, QPointF(25, 25))
    controller.handle_mouse_press(event3)
    assert len(selection_state.selected_component_ids) == 1
    assert selection_state.selected_component_ids[0] == comp.id

    # Test delete
    event_del = MockEvent(key_val=Qt.Key_Delete)
    controller.handle_key_press(event_del)
    assert len(board_state.components) == 0
    assert len(selection_state.selected_component_ids) == 0


def test_drag_move_remains_grid_snapped():
    board_view = MockBoardView()
    board_state = BoardState()
    selection_state = SelectionState()
    tool_state = ToolState()
    registry = PrimitiveRegistry()

    controller = InputController(board_view, board_state, selection_state, tool_state, registry)

    tool_state.active_tool_id = "place"
    tool_state.selected_primitive_id = "and"
    controller.handle_mouse_press(MockEvent(Qt.LeftButton, QPointF(25, 25)))

    comp = list(board_state.components.values())[0]
    assert (comp.x, comp.y) == (1, 1)

    tool_state.active_tool_id = "select"
    tool_state.selected_primitive_id = None

    controller.handle_mouse_press(MockEvent(Qt.LeftButton, QPointF(25, 25)))
    controller.handle_mouse_move(MockEvent(Qt.LeftButton, QPointF(65, 45)))
    controller.handle_mouse_release(MockEvent(Qt.LeftButton, QPointF(65, 45)))

    assert (comp.x, comp.y) == (3, 2)
    assert selection_state.selected_component_ids == [comp.id]
    assert controller.dragging_component_id is None
    assert board_view.update_calls >= 3


def test_primitive_dropdown_keeps_select_option_enabled():
    app = QApplication.instance() or QApplication([])
    registry = PrimitiveRegistry()
    dropdown = PrimitiveDropdown(registry)

    placeholder_item = dropdown.model().item(0)
    assert placeholder_item is not None
    assert placeholder_item.flags() & Qt.ItemIsEnabled
    assert placeholder_item.flags() & Qt.ItemIsSelectable

    header_index = next(
        i for i in range(dropdown.count())
        if dropdown.itemText(i).startswith("--- ")
    )
    header_item = dropdown.model().item(header_index)
    assert header_item is not None
    assert not (header_item.flags() & Qt.ItemIsEnabled)

    assert app is not None
