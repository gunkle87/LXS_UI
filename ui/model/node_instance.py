from dataclasses import dataclass

@dataclass
class NodeInstance:
    id: str
    trace_id: str
    x: float
    y: float
