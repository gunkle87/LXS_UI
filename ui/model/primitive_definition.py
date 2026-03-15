from dataclasses import dataclass

@dataclass
class PrimitiveDefinition:
    type_id: str
    category: str
    num_inputs: int
    num_outputs: int
    display_name: str
    
    @property
    def width(self) -> int:
        from ui.model.geometry import calculate_component_width
        return calculate_component_width()

    @property
    def height(self) -> int:
        from ui.model.geometry import calculate_component_depth
        return calculate_component_depth(self.num_inputs, self.num_outputs)
