import json
from pathlib import Path

from ui.model.board_state import BoardState


PROJECT_SCHEMA = "lxs-ui-v0"


class ProjectIO:
    def serialize_board(self, board_state: BoardState) -> dict:
        return {
            "schema": PROJECT_SCHEMA,
            "board": board_state.snapshot(),
        }

    def deserialize_board(self, payload: dict) -> BoardState:
        if payload.get("schema") != PROJECT_SCHEMA:
            raise ValueError("Unsupported project schema.")
        return BoardState.from_snapshot(payload.get("board", {}))

    def save_to_path(self, board_state: BoardState, path: str | Path):
        target = Path(path)
        target.write_text(
            json.dumps(self.serialize_board(board_state), indent=2),
            encoding="utf-8",
        )

    def load_from_path(self, path: str | Path) -> BoardState:
        source = Path(path)
        payload = json.loads(source.read_text(encoding="utf-8"))
        return self.deserialize_board(payload)
