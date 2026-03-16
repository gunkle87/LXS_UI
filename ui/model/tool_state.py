from dataclasses import dataclass

@dataclass
class ToolState:
    active_tool_id: str = "select"
    selected_primitive_id: str = None
    # Additional tool-specific state can be stored here or via composition
