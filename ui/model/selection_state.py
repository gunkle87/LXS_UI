from dataclasses import dataclass, field
from typing import List

@dataclass
class SelectionState:
    selected_component_ids: List[str] = field(default_factory=list)
    selected_trace_ids: List[str] = field(default_factory=list)
    selected_node_ids: List[str] = field(default_factory=list)

    def clear(self) -> None:
        self.selected_component_ids = []
        self.selected_trace_ids = []
        self.selected_node_ids = []

    def select_component(self, component_id: str) -> None:
        self.clear()
        self.selected_component_ids = [component_id]

    def select_trace(self, trace_id: str) -> None:
        self.selected_component_ids = []
        self.selected_node_ids = []
        self.selected_trace_ids = [trace_id]

    def select_node(self, node_id: str) -> None:
        self.selected_component_ids = []
        self.selected_trace_ids = []
        self.selected_node_ids = [node_id]
