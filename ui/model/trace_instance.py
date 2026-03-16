from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class TerminalRef:
    component_id: str
    is_input: bool
    index: int


@dataclass(frozen=True)
class TraceEndpoint:
    terminal: Optional[TerminalRef] = None
    node_id: Optional[str] = None

    def is_valid(self) -> bool:
        has_terminal = self.terminal is not None
        has_node = self.node_id is not None
        return has_terminal != has_node


@dataclass(frozen=True)
class TraceVertex:
    x: float
    y: float


@dataclass
class TraceInstance:
    id: str
    source: TraceEndpoint
    target: TraceEndpoint
    vertices: List[TraceVertex] = field(default_factory=list)

    def has_valid_endpoints(self) -> bool:
        return self.source.is_valid() and self.target.is_valid()

    def is_orthogonal(self) -> bool:
        if len(self.vertices) < 2:
            return True
        for i in range(len(self.vertices) - 1):
            v1 = self.vertices[i]
            v2 = self.vertices[i + 1]
            if v1.x != v2.x and v1.y != v2.y:
                return False
        return True

    def segments(self) -> Iterable[tuple[TraceVertex, TraceVertex]]:
        for index in range(len(self.vertices) - 1):
            yield self.vertices[index], self.vertices[index + 1]
