from ui.model.board_state import BoardState
from ui.model.component_instance import ComponentInstance
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TraceVertex
from ui.services.engine_bridge import EngineBridge
from ui.services.lxs_api_wrapper import LxsApiLibrary
from ui.services.primitive_registry import PrimitiveRegistry


def build_and_board():
    registry = PrimitiveRegistry()
    board_state = BoardState()
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
                vertices=[
                    TraceVertex(0.0, y),
                    TraceVertex(1.0, y),
                    TraceVertex(2.0, y),
                ],
            )
        )

    connect("t0", "a", "g1", 0, 0.25)
    connect("t1", "b", "g1", 1, 2.25)
    connect("t2", "g1", "q", 0, 1.25)
    connect("t3", "g1", "p", 0, 1.75)
    return board_state, registry


def test_dll_loads_from_public_path():
    api = LxsApiLibrary()
    assert api.dll_path.exists()


def test_engine_bridge_runs_board_to_engine_example():
    board_state, registry = build_and_board()
    bridge = EngineBridge()

    with bridge.create_session(board_state, registry) as session:
        counts = session.api.get_plan_counts(session.plan)
        assert counts.input_count == 2
        assert counts.output_count == 2

        session.apply_inputs({"input_a": 1, "input_b": 0})
        session.tick()
        outputs = session.read_outputs()
        assert outputs["output_q"]["known"] is True
        assert outputs["output_q"]["value"] is False
        assert outputs["probe_p"]["value"] is False

        session.apply_inputs({"input_a": 1, "input_b": 1})
        session.tick()
        outputs = session.read_outputs()
        assert outputs["output_q"]["value"] is True
        assert outputs["probe_p"]["value"] is True

        gate_state = session.read_signal("and_g1")
        assert gate_state["known"] is True
        assert gate_state["value"] is True

        probes = session.read_probes()
        assert probes.tick_count == 2
