from dataclasses import dataclass


@dataclass
class SnapshotCommand:
    label: str
    before_board: dict
    after_board: dict
    before_selection: dict
    after_selection: dict

    def undo(self, board_state, selection_state):
        board_state.restore_snapshot(self.before_board)
        selection_state.restore_snapshot(self.before_selection)

    def redo(self, board_state, selection_state):
        board_state.restore_snapshot(self.after_board)
        selection_state.restore_snapshot(self.after_selection)


class CommandStack:
    def __init__(self):
        self._undo_stack: list[SnapshotCommand] = []
        self._redo_stack: list[SnapshotCommand] = []

    def record_transition(
        self,
        label: str,
        before_board: dict,
        after_board: dict,
        before_selection: dict,
        after_selection: dict,
    ) -> bool:
        if before_board == after_board and before_selection == after_selection:
            return False
        self._undo_stack.append(
            SnapshotCommand(
                label=label,
                before_board=before_board,
                after_board=after_board,
                before_selection=before_selection,
                after_selection=after_selection,
            )
        )
        self._redo_stack.clear()
        return True

    def undo(self, board_state, selection_state) -> bool:
        if not self._undo_stack:
            return False
        command = self._undo_stack.pop()
        command.undo(board_state, selection_state)
        self._redo_stack.append(command)
        return True

    def redo(self, board_state, selection_state) -> bool:
        if not self._redo_stack:
            return False
        command = self._redo_stack.pop()
        command.redo(board_state, selection_state)
        self._undo_stack.append(command)
        return True

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)
