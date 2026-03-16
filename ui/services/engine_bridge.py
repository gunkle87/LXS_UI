from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from ui.model.trace_instance import TerminalRef
from ui.services.lxs_api_wrapper import LxsApiLibrary
from ui.services.lxs_api_wrapper import LxsApiError
from ui.services.lxs_api_wrapper import logic_to_word


SUPPORTED_GATE_TYPES = {
    "and": "AND",
    "or": "OR",
    "xor": "XOR",
    "not": "NOT",
}


@dataclass(frozen=True)
class BridgeArtifact:
    bench_text: str
    input_names: list[str]
    output_names: list[str]
    signal_names: dict[str, str]


class EngineSession:
    def __init__(self, api: LxsApiLibrary, netlist, plan, engine, artifact: BridgeArtifact, temp_dir: TemporaryDirectory):
        self.api = api
        self.netlist = netlist
        self.plan = plan
        self.engine = engine
        self.artifact = artifact
        self._temp_dir = temp_dir

    def close(self):
        if self.engine is not None:
            self.api.free_engine(self.engine)
            self.engine = None
        if self.plan is not None:
            self.api.free_plan(self.plan)
            self.plan = None
        if self.netlist is not None:
            self.api.free_netlist(self.netlist)
            self.netlist = None
        if self._temp_dir is not None:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def apply_inputs(self, values_by_name: dict[str, int | bool]):
        counts = self.api.get_plan_counts(self.plan)
        ordered_values = []
        for index in range(counts.input_count):
            input_name = self.api.get_input_name(self.plan, index)
            ordered_values.append(logic_to_word(values_by_name.get(input_name, 0)))
        self.api.apply_inputs(self.engine, ordered_values)

    def tick(self, count: int = 1):
        self.api.tick(self.engine, count)

    def read_outputs(self) -> dict[str, dict[str, int | bool]]:
        counts = self.api.get_plan_counts(self.plan)
        values, masks = self.api.read_outputs(self.engine, counts.output_count)
        output_state = {}
        for index in range(counts.output_count):
            name = self.api.get_output_name(self.plan, index)
            output_state[name] = {
                "value": values[index] == logic_to_word(True),
                "known": masks[index] == 0,
                "raw_value": values[index],
                "raw_mask": masks[index],
            }
        return output_state

    def read_signal(self, name: str) -> dict[str, int | bool]:
        net_id = self.api.find_net(self.plan, name)
        value, mask = self.api.read_net(self.engine, net_id)
        return {
            "value": value == logic_to_word(True),
            "known": mask == 0,
            "raw_value": value,
            "raw_mask": mask,
        }

    def read_probes(self):
        return self.api.read_probes(self.engine)


class EngineBridge:
    def __init__(self, api: LxsApiLibrary | None = None):
        self.api = api or LxsApiLibrary()

    def create_session(self, board_state, registry) -> EngineSession:
        artifact = self.export_board(board_state, registry)
        temp_dir = TemporaryDirectory()
        bench_path = Path(temp_dir.name) / "board_export.bench"
        bench_path.write_text(artifact.bench_text, encoding="utf-8")

        netlist = plan = engine = None
        try:
            netlist = self.api.load_bench(bench_path)
            plan = self.api.compile_plan(netlist)
            engine = self.api.create_engine(plan)
        except Exception:
            if engine is not None:
                self.api.free_engine(engine)
            if plan is not None:
                self.api.free_plan(plan)
            if netlist is not None:
                self.api.free_netlist(netlist)
            temp_dir.cleanup()
            raise

        return EngineSession(self.api, netlist, plan, engine, artifact, temp_dir)

    def export_board(self, board_state, registry) -> BridgeArtifact:
        components = board_state.components
        trace_by_target = {}
        for trace in board_state.traces.values():
            if trace.source.terminal is None or trace.target.terminal is None:
                raise LxsApiError("Trace endpoints must terminate on component terminals for v0 export.")
            if trace.source.terminal.is_input:
                raise LxsApiError("Trace source endpoint must be an output terminal.")
            if not trace.target.terminal.is_input:
                raise LxsApiError("Trace target endpoint must be an input terminal.")
            target_key = self._terminal_key(trace.target.terminal)
            if target_key in trace_by_target:
                raise LxsApiError(f"Multiple drivers detected for {target_key}.")
            trace_by_target[target_key] = trace

        input_names = []
        output_names = []
        signal_names = {}
        lines = []

        for component in components.values():
            if component.type_id == "input":
                signal_name = f"input_{component.id}"
                signal_names[component.id] = signal_name
                input_names.append(signal_name)
                lines.append(f"INPUT({signal_name})")

        if input_names:
            lines.append("")

        for component in components.values():
            if component.type_id in {"output", "probe"}:
                signal_name = self._component_signal_name(component)
                signal_names[component.id] = signal_name
                output_names.append(signal_name)
                lines.append(f"OUTPUT({signal_name})")

        if output_names:
            lines.append("")

        for component in components.values():
            if component.type_id in SUPPORTED_GATE_TYPES:
                gate_name = SUPPORTED_GATE_TYPES[component.type_id]
                output_name = self._component_signal_name(component)
                signal_names[component.id] = output_name
                input_signals = []
                primitive = registry.get_primitive(component.type_id)
                for index in range(primitive.num_inputs):
                    driver_signal = self._resolve_input_signal(component.id, index, trace_by_target, components, signal_names)
                    input_signals.append(driver_signal)
                lines.append(f"{output_name} = {gate_name}({','.join(input_signals)})")
            elif component.type_id in {"output", "probe"}:
                driver_signal = self._resolve_input_signal(component.id, 0, trace_by_target, components, signal_names)
                lines.append(f"{signal_names[component.id]} = BUF({driver_signal})")
            elif component.type_id in {"input"}:
                continue
            else:
                raise LxsApiError(f"Unsupported primitive for v0 engine bridge: {component.type_id}")

        return BridgeArtifact(
            bench_text="\n".join(lines).strip() + "\n",
            input_names=input_names,
            output_names=output_names,
            signal_names=signal_names,
        )

    @staticmethod
    def _component_signal_name(component) -> str:
        prefix = "probe" if component.type_id == "probe" else component.type_id
        return f"{prefix}_{component.id}"

    @staticmethod
    def _terminal_key(terminal: TerminalRef) -> tuple[str, bool, int]:
        return terminal.component_id, terminal.is_input, terminal.index

    def _resolve_input_signal(self, component_id, input_index, trace_by_target, components, signal_names) -> str:
        target_key = (component_id, True, input_index)
        trace = trace_by_target.get(target_key)
        if trace is None or trace.source.terminal is None:
            raise LxsApiError(f"Missing driver for {component_id} input {input_index}.")
        source_terminal = trace.source.terminal
        source_component = components[source_terminal.component_id]
        if source_component.type_id not in SUPPORTED_GATE_TYPES and source_component.type_id != "input":
            raise LxsApiError(f"Unsupported driver primitive for v0 engine bridge: {source_component.type_id}")
        if source_component.id not in signal_names:
            signal_names[source_component.id] = self._component_signal_name(source_component)
        return signal_names[source_component.id]
