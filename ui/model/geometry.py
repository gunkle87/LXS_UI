from dataclasses import dataclass
import math

@dataclass
class GridBounds:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

def calculate_component_depth(inputs: int, outputs: int) -> int:
    """
    Fixed geometry rule: depth = ceil(max(inputs, outputs) / 2)
    Minimum depth is 1 to ensure a component has some physical presence.
    """
    return max(1, math.ceil(max(inputs, outputs) / 2.0))

def calculate_component_width() -> int:
    """
    Fixed geometry rule: width = 1 cell
    """
    return 1

def get_lane_y_offset(index: int, total_terminals: int, component_height: int) -> float:
    """
    Calculate the local Y offset for a terminal within the component bounds.
    Fixed geometry rule: no centered lanes, only upper/lower lane slots.
    Each cell of depth has 2 lane slots: upper (0.25) and lower (0.75).
    """
    # A single leftover terminal in a span always uses the upper lane
    cell_y = index // 2
    is_lower = (index % 2 == 1)
    
    offset_in_cell = 0.75 if is_lower else 0.25
    return float(cell_y) + offset_in_cell

def validate_component_geometry(width: int, height: int, inputs: int, outputs: int) -> bool:
    """
    Validation helper to ensure a component satisfies invariants.
    """
    if width != calculate_component_width():
        return False
    if height != calculate_component_depth(inputs, outputs):
        return False
    return True

def validate_lane_offset(offset: float) -> bool:
    """
    Validation helper to ensure a terminal y-offset sits exactly
    on an upper (0.25) or lower (0.75) lane slot, avoiding centered lanes.
    """
    fraction = offset % 1.0
    return math.isclose(fraction, 0.25) or math.isclose(fraction, 0.75)
