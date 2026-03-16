from dataclasses import dataclass

@dataclass
class NodeInstance:
    id: str
    x: float
    y: float
    owner_trace_id: str
