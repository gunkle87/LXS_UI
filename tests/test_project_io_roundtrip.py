import json
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.model.component_instance import ComponentInstance
from ui.model.node_instance import NodeInstance
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TraceVertex
from ui.services.project_io import ProjectIO


app = QApplication.instance() or QApplication(sys.argv)


def build_sample_board(window: MainWindow):
    window.board_state.add_component(ComponentInstance(id="src", type_id="input", x=0, y=0))
    window.board_state.add_component(ComponentInstance(id="dst", type_id="output", x=4, y=0))
    window.board_state.add_trace(
        TraceInstance(
            id="trace_0",
            source=TraceEndpoint(terminal=TerminalRef(component_id="src", is_input=False, index=0)),
            target=TraceEndpoint(terminal=TerminalRef(component_id="dst", is_input=True, index=0)),
            vertices=[
                TraceVertex(1.0, 0.25),
                TraceVertex(2.5, 0.25),
                TraceVertex(4.0, 0.25),
            ],
        )
    )
    window.board_state.add_node(NodeInstance(id="node_0", x=2.5, y=0.25, owner_trace_id="trace_0"))


def test_project_io_round_trip_persists_committed_board_only(tmp_path):
    window = MainWindow()
    build_sample_board(window)

    window.input_controller.trace_tool.start_endpoint = TraceEndpoint(
        terminal=TerminalRef(component_id="src", is_input=False, index=0)
    )
    window.input_controller.trace_tool.preview_trace = TraceInstance(
        id="preview",
        source=window.input_controller.trace_tool.start_endpoint,
        target=TraceEndpoint(terminal=TerminalRef(component_id="dst", is_input=True, index=0)),
        vertices=[TraceVertex(1.0, 0.25), TraceVertex(3.0, 0.25)],
    )

    project_path = tmp_path / "sample.lxui.json"
    project_io = ProjectIO()
    project_io.save_to_path(window.board_state, project_path)

    payload = json.loads(project_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "lxs-ui-v0"
    assert "preview" not in project_path.read_text(encoding="utf-8")

    loaded_board = project_io.load_from_path(project_path)
    assert loaded_board.snapshot() == window.board_state.snapshot()


def test_program_menu_actions_save_new_and_open(monkeypatch, tmp_path):
    window = MainWindow()
    build_sample_board(window)
    saved_snapshot = window.board_state.snapshot()
    project_path = tmp_path / "menu-project.lxui.json"

    monkeypatch.setattr(
        "ui.menu_controller.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(project_path), "LXS UI Project (*.lxui.json)"),
    )
    monkeypatch.setattr(
        "ui.menu_controller.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(project_path), "LXS UI Project (*.lxui.json)"),
    )

    window.app_menu_bar.save_action.trigger()
    assert project_path.exists()

    window.app_menu_bar.new_action.trigger()
    assert window.board_state.snapshot() == {"components": [], "traces": [], "nodes": []}

    window.app_menu_bar.open_action.trigger()
    assert window.board_state.snapshot() == saved_snapshot

    window.app_menu_bar.undo_action.trigger()
    assert window.board_state.snapshot() == {"components": [], "traces": [], "nodes": []}
