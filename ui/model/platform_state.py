from dataclasses import dataclass
from ui.model.geometry import GridBounds

@dataclass
class PlatformState:
    bounds: GridBounds
    zoom_level: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
