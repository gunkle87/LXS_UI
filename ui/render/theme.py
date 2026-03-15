from dataclasses import dataclass
from typing import Tuple

@dataclass
class Theme:
    # Colors
    background_color: str = "#1A1A1A"  # Dark gray background
    grid_color_main: str = "#333333"    # Main grid lines
    grid_color_sub: str = "#262626"     # Sub grid lines
    platform_color: str = "#111111"     # Darker platform
    platform_edge_color: str = "#444444" # Platform edge
    gasket_color: str = "#8B0000"       # Dark red inset gasket
    
    # Dimensions/Metrics
    grid_size: int = 20                 # Pixels per cell at zoom 1.0
    grid_fade_zoom_threshold: float = 0.5 # Sub-grid fades out below this zoom
    platform_margin_cells: int = 4      # Padding around components
    gasket_width_pixels: float = 4.0    # Fixed visual width of gasket
    platform_edge_width_pixels: float = 2.0

default_theme = Theme()
