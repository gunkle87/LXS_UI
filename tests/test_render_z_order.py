from ui.model.board_state import BoardState
from ui.model.selection_state import SelectionState
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TraceVertex
from ui.render.trace_renderer import ordered_trace_ids


def test_selected_trace_renders_last():
    board_state = BoardState()
    board_state.add_trace(
        TraceInstance(
            id="trace_a",
            source=TraceEndpoint(node_id="node_a"),
            target=TraceEndpoint(node_id="node_b"),
            vertices=[TraceVertex(0.0, 0.0), TraceVertex(2.0, 0.0)],
        )
    )
    board_state.add_trace(
        TraceInstance(
            id="trace_b",
            source=TraceEndpoint(node_id="node_c"),
            target=TraceEndpoint(node_id="node_d"),
            vertices=[TraceVertex(1.0, -1.0), TraceVertex(1.0, 1.0)],
        )
    )

    selection_state = SelectionState(selected_trace_ids=["trace_b"])
    assert ordered_trace_ids(board_state, selection_state) == ["trace_a", "trace_b"]


def test_selected_trace_order_respects_last_selected_position():
    board_state = BoardState()
    for trace_id in ("trace_a", "trace_b", "trace_c"):
        board_state.add_trace(
            TraceInstance(
                id=trace_id,
                source=TraceEndpoint(node_id=f"{trace_id}_src"),
                target=TraceEndpoint(node_id=f"{trace_id}_dst"),
                vertices=[TraceVertex(0.0, 0.0), TraceVertex(1.0, 0.0)],
            )
        )

    selection_state = SelectionState(selected_trace_ids=["trace_a", "trace_c"])
    assert ordered_trace_ids(board_state, selection_state) == ["trace_b", "trace_a", "trace_c"]
