class ToolController:
    """Coordinate the active editor tool without pushing tool logic into widgets."""

    def __init__(self, tool_state):
        self.tool_state = tool_state

    def activate_select(self):
        self.tool_state.active_tool_id = "select"
        self.tool_state.selected_primitive_id = None

    def activate_trace(self):
        self.tool_state.active_tool_id = "trace"
        self.tool_state.selected_primitive_id = None

    def activate_place(self, primitive_id: str | None):
        if primitive_id:
            self.tool_state.active_tool_id = "place"
            self.tool_state.selected_primitive_id = primitive_id
        else:
            self.activate_select()
