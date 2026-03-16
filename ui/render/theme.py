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
    trace_outline_color: str = "#000000"
    trace_highlight_color: str = "#F4F7FB"
    trace_palette: Tuple[str, ...] = (
        "#D64A43",
        "#4477D8",
        "#D9A520",
        "#4A9B57",
        "#E57A2A",
        "#7A56B5",
    )
    node_fill_color: str = "#E6EDF6"
    node_border_color: str = "#0E1116"
    node_highlight_color: str = "#8FD0FF"
    node_size_cells: float = 0.28
    node_highlight_padding_cells: float = 0.12
    trace_outer_width: float = 4.0
    trace_inner_width: float = 2.2
    trace_selected_outer_width: float = 5.0
    trace_selected_inner_width: float = 3.0

default_theme = Theme()
