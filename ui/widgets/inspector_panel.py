from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from ui.widgets.primitive_dropdown import PrimitiveDropdown

class InspectorPanel(QWidget):
    """Placeholder tool/component area for the LXS UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        label = QLabel("Inspector / Tools / Components")
        self.layout.addWidget(label)
        self.layout.addStretch()
        self.setLayout(self.layout)

    def set_registry(self, registry, tool_state):
        self.tool_state = tool_state
        self.primitive_dropdown = PrimitiveDropdown(registry, self)
        self.primitive_dropdown.currentIndexChanged.connect(self._on_primitive_selected)
        # Insert it before the stretch
        self.layout.insertWidget(1, self.primitive_dropdown)

    def _on_primitive_selected(self, index):
        type_id = self.primitive_dropdown.currentData()
        if type_id:
            self.tool_state.active_tool_id = "place"
            self.tool_state.selected_primitive_id = type_id
        else:
            self.tool_state.active_tool_id = "select"
            self.tool_state.selected_primitive_id = None
