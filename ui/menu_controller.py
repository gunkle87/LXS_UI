from pathlib import Path

from PySide6.QtWidgets import QFileDialog


class MenuController:
    """Wire program and edit menu actions to the current board session."""

    def __init__(self, window, input_controller, board_state, selection_state, tool_state, command_stack, project_io, ui_callback=None):
        self.window = window
        self.input_controller = input_controller
        self.board_state = board_state
        self.selection_state = selection_state
        self.tool_state = tool_state
        self.command_stack = command_stack
        self.project_io = project_io
        self.ui_callback = ui_callback
        self.current_project_path = None

    def wire_actions(self, menu_bar):
        menu_bar.new_action.triggered.connect(self.new_project)
        menu_bar.open_action.triggered.connect(self.open_project)
        menu_bar.save_action.triggered.connect(self.save_project)
        menu_bar.save_as_action.triggered.connect(self.save_project_as)
        menu_bar.undo_action.triggered.connect(self.input_controller.undo)
        menu_bar.redo_action.triggered.connect(self.input_controller.redo)
        menu_bar.copy_action.triggered.connect(self.input_controller.copy_selection)
        menu_bar.paste_action.triggered.connect(self.input_controller.paste_clipboard)
        menu_bar.duplicate_action.triggered.connect(self.input_controller.duplicate_selection)
        menu_bar.delete_action.triggered.connect(self.input_controller.delete_selection)

    def new_project(self):
        self._replace_board_with_snapshot({}, "New Project")
        self.current_project_path = None

    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Open LXS UI Project",
            "",
            "LXS UI Project (*.lxui.json);;JSON Files (*.json)",
        )
        if not file_path:
            return False
        return self.load_from_path(file_path)

    def save_project(self):
        if self.current_project_path is None:
            return self.save_project_as()
        self.project_io.save_to_path(self.board_state, self.current_project_path)
        return True

    def save_project_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Save LXS UI Project",
            self.current_project_path or "",
            "LXS UI Project (*.lxui.json);;JSON Files (*.json)",
        )
        if not file_path:
            return False
        if not file_path.endswith(".json"):
            file_path = f"{file_path}.json"
        self.current_project_path = file_path
        self.project_io.save_to_path(self.board_state, self.current_project_path)
        return True

    def save_to_path(self, file_path: str):
        self.current_project_path = str(Path(file_path))
        self.project_io.save_to_path(self.board_state, self.current_project_path)
        return True

    def load_from_path(self, file_path: str):
        loaded_board = self.project_io.load_from_path(file_path)
        loaded_snapshot = loaded_board.snapshot()
        self.current_project_path = str(Path(file_path))
        return self._replace_board_with_snapshot(loaded_snapshot, "Load Project")

    def _replace_board_with_snapshot(self, snapshot: dict, label: str):
        before_board = self.board_state.snapshot()
        before_selection = self.selection_state.snapshot()
        self.board_state.restore_snapshot(snapshot)
        self.selection_state.clear()
        self.input_controller.cancel_transient_state()
        self.window.board_view.update()
        if self.ui_callback is not None:
            self.ui_callback(board_changed=True, selection_changed=True)
        recorded = self.command_stack.record_transition(
            label=label,
            before_board=before_board,
            after_board=self.board_state.snapshot(),
            before_selection=before_selection,
            after_selection=self.selection_state.snapshot(),
        )
        if label == "New Project" and not snapshot:
            self.command_stack._redo_stack.clear()
        return recorded or before_board == self.board_state.snapshot()
