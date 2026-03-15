from dataclasses import dataclass, field
from typing import List

@dataclass
class SelectionState:
    selected_component_ids: List[str] = field(default_factory=list)
    selected_trace_ids: List[str] = field(default_factory=list)
    selected_node_ids: List[str] = field(default_factory=list)
