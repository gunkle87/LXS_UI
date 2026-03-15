from dataclasses import dataclass

@dataclass
class ToolState:
    active_tool_id: str = "select"
    # Additional tool-specific state can be stored here or via composition
