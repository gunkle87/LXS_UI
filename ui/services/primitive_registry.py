from typing import Dict, List, Optional
from ui.model.primitive_definition import PrimitiveDefinition

class PrimitiveRegistry:
    def __init__(self):
        self._primitives: Dict[str, PrimitiveDefinition] = {}
        self._categories: Dict[str, List[str]] = {
            "Combinational": [],
            "Input/Output": [],
            "Sequential": [],
            "Memory": [],
            "ALUs": [],
            "MUXes": []
        }
        self._register_initial_primitives()

    def _register_initial_primitives(self):
        # Input/Output
        self.register(PrimitiveDefinition(
            type_id="input", category="Input/Output", num_inputs=0, num_outputs=1, display_name="Input"
        ))
        self.register(PrimitiveDefinition(
            type_id="output", category="Input/Output", num_inputs=1, num_outputs=0, display_name="Output"
        ))
        self.register(PrimitiveDefinition(
            type_id="probe", category="Input/Output", num_inputs=1, num_outputs=0, display_name="Probe"
        ))

        # Combinational
        self.register(PrimitiveDefinition(
            type_id="not", category="Combinational", num_inputs=1, num_outputs=1, display_name="NOT"
        ))
        self.register(PrimitiveDefinition(
            type_id="and", category="Combinational", num_inputs=2, num_outputs=1, display_name="AND"
        ))
        self.register(PrimitiveDefinition(
            type_id="or", category="Combinational", num_inputs=2, num_outputs=1, display_name="OR"
        ))
        self.register(PrimitiveDefinition(
            type_id="xor", category="Combinational", num_inputs=2, num_outputs=1, display_name="XOR"
        ))

        # Sequential
        self.register(PrimitiveDefinition(
            type_id="clock", category="Sequential", num_inputs=0, num_outputs=1, display_name="Clock"
        ))

    def register(self, primitive: PrimitiveDefinition):
        if primitive.type_id in self._primitives:
            raise ValueError(f"Primitive {primitive.type_id} is already registered.")
        
        if primitive.category not in self._categories:
            self._categories[primitive.category] = []
            
        self._primitives[primitive.type_id] = primitive
        self._categories[primitive.category].append(primitive.type_id)

    def get_primitive(self, type_id: str) -> Optional[PrimitiveDefinition]:
        return self._primitives.get(type_id)

    def get_categories(self) -> List[str]:
        return list(self._categories.keys())

    def get_primitives_in_category(self, category: str) -> List[PrimitiveDefinition]:
        type_ids = self._categories.get(category, [])
        return [self._primitives[tid] for tid in type_ids]
    
    def get_all_primitives(self) -> List[PrimitiveDefinition]:
        return list(self._primitives.values())
