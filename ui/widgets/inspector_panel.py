from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from ui.widgets.primitive_dropdown import PrimitiveDropdown

class InspectorPanel(QWidget):
    """Simple tool and state inspector for the v0 workbench."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        label = QLabel("Tools and Inspector")
        self.layout.addWidget(label)
        self.select_button = QPushButton("Select")
        self.trace_button = QPushButton("Trace")
        self.step_button = QPushButton("Step")
        self.toggle_input_button = QPushButton("Toggle Selected Input")
        self.toggle_input_button.setEnabled(False)
        self.selected_component_label = QLabel("Selected Component: none")
        self.selected_trace_label = QLabel("Selected Trace: none")
        self.selected_node_label = QLabel("Selected Node: none")
        self.engine_state_label = QLabel("Engine: Simulation idle")
        self.probe_state_label = QLabel("Probes: none")
        self.layout.addWidget(self.select_button)
        self.layout.addWidget(self.trace_button)
        self.layout.addWidget(self.step_button)
        self.layout.addWidget(self.toggle_input_button)
        self.layout.addWidget(self.selected_component_label)
        self.layout.addWidget(self.selected_trace_label)
        self.layout.addWidget(self.selected_node_label)
        self.layout.addWidget(self.engine_state_label)
        self.layout.addWidget(self.probe_state_label)
        self.layout.addStretch()
        self.setLayout(self.layout)
        self._step_callback = None
        self._toggle_input_callback = None

    def set_registry(self, registry, tool_controller):
        self.tool_controller = tool_controller
        self.primitive_dropdown = PrimitiveDropdown(registry, self)
        self.primitive_dropdown.currentIndexChanged.connect(self._on_primitive_selected)
        self.select_button.clicked.connect(self._activate_select_tool)
        self.trace_button.clicked.connect(self._activate_trace_tool)
        self.step_button.clicked.connect(self._on_step_clicked)
        self.toggle_input_button.clicked.connect(self._on_toggle_input_clicked)
        # Insert it before the stretch
        self.layout.insertWidget(5, self.primitive_dropdown)

    def set_callbacks(self, on_step, on_toggle_input):
        self._step_callback = on_step
        self._toggle_input_callback = on_toggle_input

    def update_inspector(self, board_state, selection_state, simulation_snapshot):
        component_text = "Selected Component: none"
        trace_text = "Selected Trace: none"
        node_text = "Selected Node: none"
        toggle_enabled = False

        if selection_state.selected_component_ids:
            component_id = selection_state.selected_component_ids[0]
            component = board_state.components.get(component_id)
            if component is not None:
                state = simulation_snapshot.component_states.get(component_id)
                state_label = self._logic_label(state)
                component_text = f"Selected Component: {component.id} ({component.type_id}) state={state_label}"
                toggle_enabled = component.type_id == "input"

        if selection_state.selected_trace_ids:
            trace_id = selection_state.selected_trace_ids[0]
            trace = board_state.traces.get(trace_id)
            if trace is not None:
                trace_text = f"Selected Trace: {trace.id}"

        if selection_state.selected_node_ids:
            node_id = selection_state.selected_node_ids[0]
            node = board_state.nodes.get(node_id)
            if node is not None:
                node_text = f"Selected Node: {node.id} owner={node.owner_trace_id}"

        self.toggle_input_button.setEnabled(toggle_enabled)
        self.selected_component_label.setText(component_text)
        self.selected_trace_label.setText(trace_text)
        self.selected_node_label.setText(node_text)
        self.engine_state_label.setText(f"Engine: {simulation_snapshot.engine_status}")
        self.probe_state_label.setText(f"Probes: {self._probe_summary(simulation_snapshot)}")

    def _on_primitive_selected(self, index):
        type_id = self.primitive_dropdown.currentData()
        self.tool_controller.activate_place(type_id)

    def _activate_select_tool(self):
        self.tool_controller.activate_select()

    def _activate_trace_tool(self):
        self.tool_controller.activate_trace()

    def _on_step_clicked(self):
        if self._step_callback is not None:
            self._step_callback()

    def _on_toggle_input_clicked(self):
        if self._toggle_input_callback is not None:
            self._toggle_input_callback()

    @staticmethod
    def _logic_label(state):
        if state is None:
            return "-"
        if not state.known:
            return "X"
        return "1" if state.value else "0"

    def _probe_summary(self, simulation_snapshot):
        if not simulation_snapshot.probe_states:
            return "none"
        parts = []
        for name, state in sorted(simulation_snapshot.probe_states.items()):
            parts.append(f"{name}={self._logic_label(state)}")
        return ", ".join(parts)
