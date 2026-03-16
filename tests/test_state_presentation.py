import sys

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


def test_state_updates_after_tick_and_is_available_to_renderer():
    window = MainWindow()
    build_demo_board(window)

    window.selection_state.select_component("a")
    window.toggle_selected_input()
    window.selection_state.select_component("b")
    window.toggle_selected_input()
    window.step_simulation()

    snapshot = window.simulation_controller.snapshot
    assert snapshot.tick_count == 1
    assert snapshot.component_states["g1"].value is True
    assert snapshot.component_states["q"].value is True
    assert snapshot.probe_states["probe_p"].value is True
    assert ("g1", True, 0) in snapshot.terminal_states
    assert window.board_view.simulation_snapshot is snapshot
    assert "Ticks=1" in window.app_status_bar.currentMessage()


def test_inspector_updates_follow_selection():
    window = MainWindow()
    build_demo_board(window)

    window.selection_state.select_component("g1")
    window.refresh_presentation()
    assert "g1 (and)" in window.inspector_panel.selected_component_label.text()

    window.selection_state.select_trace("t2")
    window.refresh_presentation()
    assert "t2" in window.inspector_panel.selected_trace_label.text()

    window.selection_state.select_node("node_0")
    window.refresh_presentation()
    assert "node_0" in window.inspector_panel.selected_node_label.text()
    assert "owner=t2" in window.inspector_panel.selected_node_label.text()
