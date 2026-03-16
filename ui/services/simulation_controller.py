from dataclasses import dataclass, field

from ui.services.engine_bridge import EngineBridge
from ui.services.lxs_api_wrapper import LxsApiError


@dataclass(frozen=True)
class LogicState:
    value: bool
    known: bool
    raw_value: int
    raw_mask: int


@dataclass
class SimulationSnapshot:
    connected: bool = False
    dirty: bool = True
    tick_count: int = 0
    engine_status: str = "Simulation idle"
    input_values: dict[str, bool] = field(default_factory=dict)
    component_states: dict[str, LogicState] = field(default_factory=dict)
    terminal_states: dict[tuple[str, bool, int], LogicState] = field(default_factory=dict)
    output_states: dict[str, LogicState] = field(default_factory=dict)
    probe_states: dict[str, LogicState] = field(default_factory=dict)


class SimulationController:
    def __init__(self, engine_bridge: EngineBridge | None = None):
        self.engine_bridge = engine_bridge or EngineBridge()
        self.snapshot = SimulationSnapshot()
        self._session = None

    def mark_dirty(self, reason: str = "Board changed"):
        self._close_session()
        self.snapshot.connected = False
        self.snapshot.dirty = True
        self.snapshot.tick_count = 0
        self.snapshot.component_states = {}
        self.snapshot.terminal_states = {}
        self.snapshot.output_states = {}
        self.snapshot.probe_states = {}
        self.snapshot.engine_status = reason

    def set_input_value(self, component_id: str, value: bool):
        self.snapshot.input_values[component_id] = bool(value)
        self.snapshot.engine_status = f"Input {component_id} set to {1 if value else 0}"

    def toggle_input_value(self, component_id: str) -> bool:
        current = self.snapshot.input_values.get(component_id, False)
        self.set_input_value(component_id, not current)
        return self.snapshot.input_values[component_id]

    def get_input_value(self, component_id: str) -> bool:
        return self.snapshot.input_values.get(component_id, False)

    def step(self, board_state, registry) -> SimulationSnapshot:
        self._ensure_session(board_state, registry)
        values_by_name = {
            f"input_{component_id}": 1 if value else 0
            for component_id, value in self.snapshot.input_values.items()
        }
        self._session.apply_inputs(values_by_name)
        self._session.tick()
        self._refresh_snapshot(board_state)
        return self.snapshot

    def current_probe_summary(self) -> str:
        if not self.snapshot.probe_states:
            return "no probes"
        parts = []
        for probe_name, state in sorted(self.snapshot.probe_states.items()):
            parts.append(f"{probe_name}={self._logic_label(state)}")
        return ", ".join(parts)

    def selected_object_summary(self, board_state, selection_state) -> str:
        if selection_state.selected_component_ids:
            component = board_state.components.get(selection_state.selected_component_ids[0])
            if component is None:
                return "No selection"
            state = self.snapshot.component_states.get(component.id)
            return f"component {component.id} ({component.type_id}) state={self._logic_label(state)}"
        if selection_state.selected_trace_ids:
            trace_id = selection_state.selected_trace_ids[0]
            trace = board_state.traces.get(trace_id)
            if trace is None:
                return "No selection"
            return f"trace {trace.id}"
        if selection_state.selected_node_ids:
            node_id = selection_state.selected_node_ids[0]
            node = board_state.nodes.get(node_id)
            if node is None:
                return "No selection"
            return f"node {node.id} owner={node.owner_trace_id}"
        return "No selection"

    def _ensure_session(self, board_state, registry):
        if self._session is None or self.snapshot.dirty:
            self._close_session()
            self._session = self.engine_bridge.create_session(board_state, registry)
            self.snapshot.connected = True
            self.snapshot.dirty = False
            self.snapshot.tick_count = 0
            self.snapshot.engine_status = "Engine session ready"

    def _refresh_snapshot(self, board_state):
        output_states = {
            name: self._logic_state_from_payload(payload)
            for name, payload in self._session.read_outputs().items()
        }
        component_states = {}
        terminal_states = {}

        for component_id, signal_name in self._session.artifact.signal_names.items():
            component_states[component_id] = self._logic_state_from_payload(
                self._session.read_signal(signal_name)
            )

        for component_id, component in board_state.components.items():
            state = component_states.get(component_id)
            if state is not None:
                terminal_states[(component_id, False, 0)] = state

        for trace in board_state.traces.values():
            if trace.source.terminal is None or trace.target.terminal is None:
                continue
            source_component_state = component_states.get(trace.source.terminal.component_id)
            if source_component_state is not None:
                terminal_states[
                    (
                        trace.target.terminal.component_id,
                        True,
                        trace.target.terminal.index,
                    )
                ] = source_component_state

        probe_states = {}
        for component_id, component in board_state.components.items():
            if component.type_id == "probe":
                signal_name = self._session.artifact.signal_names.get(component_id)
                if signal_name is not None and signal_name in output_states:
                    probe_states[signal_name] = output_states[signal_name]

        probes = self._session.read_probes()
        self.snapshot.tick_count = probes.tick_count
        self.snapshot.component_states = component_states
        self.snapshot.terminal_states = terminal_states
        self.snapshot.output_states = output_states
        self.snapshot.probe_states = probe_states
        self.snapshot.engine_status = f"Ticks={probes.tick_count} | {self._probe_summary(probe_states)}"

    def _close_session(self):
        if self._session is not None:
            self._session.close()
            self._session = None

    @staticmethod
    def _logic_state_from_payload(payload: dict) -> LogicState:
        return LogicState(
            value=bool(payload["value"]),
            known=bool(payload["known"]),
            raw_value=int(payload["raw_value"]),
            raw_mask=int(payload["raw_mask"]),
        )

    @staticmethod
    def _logic_label(state: LogicState | None) -> str:
        if state is None:
            return "-"
        if not state.known:
            return "X"
        return "1" if state.value else "0"

    def _probe_summary(self, probe_states: dict[str, LogicState]) -> str:
        if not probe_states:
            return "no probes"
        parts = []
        for probe_name, state in sorted(probe_states.items()):
            parts.append(f"{probe_name}={self._logic_label(state)}")
        return ", ".join(parts)
