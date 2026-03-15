from dataclasses import dataclass
from ui.model.geometry import GridBounds
from ui.model.primitive_definition import PrimitiveDefinition

@dataclass
class TerminalRef:
    component_id: str
    is_input: bool
    index: int

@dataclass
class ComponentInstance:
    id: str
    type_id: str
    x: int
    y: int
    
    def get_bounds(self, primitive_def: PrimitiveDefinition) -> GridBounds:
        return GridBounds(
            x=self.x,
            y=self.y,
            width=primitive_def.width,
            height=primitive_def.height
        )
