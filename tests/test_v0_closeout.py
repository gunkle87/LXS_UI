import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.model.component_instance import ComponentInstance
from ui.model.node_instance import NodeInstance
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TraceVertex


app = QApplication.instance() or QApplication(sys.argv)


def build_demo_board(window: MainWindow):
    board_state = window.board_state
    board_state.add_component(ComponentInstance(id="a", type_id="input", x=0, y=0))
    board_state.add_component(ComponentInstance(id="b", type_id="input", x=0, y=2))
    board_state.add_component(ComponentInstance(id="g1", type_id="and", x=2, y=1))
    board_state.add_component(ComponentInstance(id="q", type_id="output", x=4, y=1))
    board_state.add_component(ComponentInstance(id="p", type_id="probe", x=4, y=2))

    def connect(trace_id, source_component_id, target_component_id, target_index, y):
        board_state.add_trace(
            TraceInstance(
                id=trace_id,
                source=TraceEndpoint(terminal=TerminalRef(component_id=source_component_id, is_input=False, index=0)),
                target=TraceEndpoint(terminal=TerminalRef(component_id=target_component_id, is_input=True, index=target_index)),
                vertices=[TraceVertex(0.0, y), TraceVertex(1.0, y), TraceVertex(2.0, y)],
            )
        )

    connect("t0", "a", "g1", 0, 0.25)
    connect("t1", "b", "g1", 1, 2.25)
    connect("t2", "g1", "q", 0, 1.25)
    connect("t3", "g1", "p", 0, 1.75)
    board_state.add_node(NodeInstance(id="node_0", x=1.0, y=1.25, owner_trace_id="t2"))
    window.on_ui_state_changed(board_changed=True, selection_changed=False)


def test_v0_closeout_flow_covers_tool_save_edit_and_step(tmp_path):
    window = MainWindow()

    launch_script = Path(__file__).resolve().parents[1] / "scripts" / "launch.bat"
    assert launch_script.exists()

    dropdown = window.inspector_panel.primitive_dropdown
    and_index = next(i for i in range(dropdown.count()) if dropdown.itemData(i) == "and")
    dropdown.setCurrentIndex(and_index)
    assert window.tool_state.active_tool_id == "place"
    assert window.tool_state.selected_primitive_id == "and"

    window.inspector_panel.trace_button.click()
    assert window.tool_state.active_tool_id == "trace"

    window.inspector_panel.select_button.click()
    assert window.tool_state.active_tool_id == "select"
    assert window.tool_state.selected_primitive_id is None

    build_demo_board(window)
    saved_snapshot = window.board_state.snapshot()

    project_path = tmp_path / "closeout.lxui.json"
    assert window.menu_controller.save_to_path(project_path)
    assert project_path.exists()

    window.selection_state.select_component("g1")
    window.app_menu_bar.copy_action.trigger()
    window.app_menu_bar.paste_action.trigger()
    assert len(window.board_state.components) == len(saved_snapshot["components"]) + 1

    window.app_menu_bar.undo_action.trigger()
    assert window.board_state.snapshot() == saved_snapshot

    window.menu_controller.new_project()
    assert window.board_state.snapshot() == {"components": [], "traces": [], "nodes": []}
    assert window.menu_controller.load_from_path(project_path)
    assert window.board_state.snapshot() == saved_snapshot

    window.selection_state.select_component("a")
    window.toggle_selected_input()
    window.selection_state.select_component("b")
    window.toggle_selected_input()
    window.step_simulation()

    assert "Ticks=1" in window.app_status_bar.currentMessage()
    assert "probe_p=1" in window.inspector_panel.probe_state_label.text()

