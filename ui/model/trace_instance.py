from dataclasses import dataclass, field
from typing import List, Optional
from ui.model.component_instance import TerminalRef

@dataclass
class TraceVertex:
    x: float
    y: float

@dataclass
class TraceEndpoint:
    # An endpoint can be a component terminal or an explicit node
    node_id: Optional[str] = None
    terminal: Optional[TerminalRef] = None

@dataclass
class TraceInstance:
    id: str
    source: TraceEndpoint
    target: TraceEndpoint
    vertices: List[TraceVertex] = field(default_factory=list)
