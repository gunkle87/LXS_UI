from dataclasses import dataclass
from ui.model.geometry import GridBounds

@dataclass
class PlatformState:
    bounds: GridBounds
    zoom_level: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0

def compute_platform_bounds(components: dict, padding_cells: int = 4) -> GridBounds:
    """Compute bounding box of all components plus padding."""
    if not components:
        # Default bounds if no components
        return GridBounds(-10, -10, 20, 20)
        
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    for comp in components.values():
        cb = comp.bounds
        min_x = min(min_x, cb.x)
        min_y = min(min_y, cb.y)
        max_x = max(max_x, cb.right)
        max_y = max(max_y, cb.bottom)
        
    return GridBounds(
        x=int(min_x - padding_cells),
        y=int(min_y - padding_cells),
        width=int((max_x - min_x) + (padding_cells * 2)),
        height=int((max_y - min_y) + (padding_cells * 2))
    )
