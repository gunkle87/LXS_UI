from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import QRectF, QPointF, Qt
from ui.model.geometry import GridBounds
from ui.render.node_renderer import draw_nodes
from ui.render.trace_renderer import draw_traces
from ui.render.theme import default_theme
from ui.camera import Camera

class BoardRenderer:
    """Procedural renderer for the board viewport."""
    
    def __init__(self, theme=default_theme):
        self.theme = theme
        
    def _draw_grid(self, painter: QPainter, camera: Camera, view_rect: QRectF):
        """Draw fading grid within the visible view rect."""
        zoom = camera.zoom
        
        # Determine cell size in pixels
        cell_size = self.theme.grid_size * zoom
        
        # Don't draw if zoomed out too far and cell_size is extremely small
        if cell_size < 2.0:
            return
            
        scene_rect = camera.get_view_rect(view_rect)
        
        # Find integer cell boundaries
        start_col = int(scene_rect.left() // self.theme.grid_size) - 1
        end_col = int(scene_rect.right() // self.theme.grid_size) + 1
        start_row = int(scene_rect.top() // self.theme.grid_size) - 1
        end_row = int(scene_rect.bottom() // self.theme.grid_size) + 1
        
        # Subgrid visibility based on zoom
        draw_subgrid = zoom >= self.theme.grid_fade_zoom_threshold
        
        # Set up pens based on theme
        main_pen = QPen(QColor(self.theme.grid_color_main))
        main_pen.setWidthF(max(1.0, 1.0 * zoom))
        
        sub_pen = QPen(QColor(self.theme.grid_color_sub))
        sub_pen.setWidthF(max(1.0, 1.0 * zoom))
        
        # Draw vertical lines
        for col in range(start_col, end_col + 1):
            x = col * self.theme.grid_size
            view_pt = camera.scene_to_view(QPointF(x, 0))
            vx = view_pt.x()
            
            # Every 10th line is a main line
            if col % 10 == 0:
                painter.setPen(main_pen)
                painter.drawLine(int(vx), int(view_rect.top()), int(vx), int(view_rect.bottom()))
            elif draw_subgrid:
                painter.setPen(sub_pen)
                painter.drawLine(int(vx), int(view_rect.top()), int(vx), int(view_rect.bottom()))
                
        # Draw horizontal lines
        for row in range(start_row, end_row + 1):
            y = row * self.theme.grid_size
            view_pt = camera.scene_to_view(QPointF(0, y))
            vy = view_pt.y()
            
            if row % 10 == 0:
                painter.setPen(main_pen)
                painter.drawLine(int(view_rect.left()), int(vy), int(view_rect.right()), int(vy))
            elif draw_subgrid:
                painter.setPen(sub_pen)
                painter.drawLine(int(view_rect.left()), int(vy), int(view_rect.right()), int(vy))
                
    def _draw_components(self, painter: QPainter, camera: Camera, board_state, selection_state, registry):
        gs = self.theme.grid_size
        zoom = camera.zoom
        
        for comp_id, comp in board_state.components.items():
            prim = registry.get_primitive(comp.type_id)
            if not prim:
                continue
                
            is_selected = selection_state and comp_id in selection_state.selected_component_ids
            
            # Bounds
            bounds = comp.get_bounds(prim)
            scene_left = bounds.x * gs
            scene_top = bounds.y * gs
            scene_width = bounds.width * gs
            scene_height = bounds.height * gs
            
            rect_scene = QRectF(scene_left, scene_top, scene_width, scene_height)
            tl_view = camera.scene_to_view(rect_scene.topLeft())
            br_view = camera.scene_to_view(rect_scene.bottomRight())
            view_rect = QRectF(tl_view, br_view)
            
            # Inset component slightly to show grid gaps
            margin = 2 * zoom
            comp_rect = view_rect.adjusted(margin, margin, -margin, -margin)
            
            # Base colors
            base_color = QColor("#4a5568") # generic component color
            if is_selected:
                base_color = QColor("#4299e1") # highlight
            
            # Darker edge cue (bottom/right shadows or simple border)
            edge_color = base_color.darker(150)
            
            # Draw top face
            painter.setBrush(QBrush(base_color))
            painter.setPen(QPen(edge_color, max(1.0, 1.5 * zoom)))
            painter.drawRect(comp_rect)
            
            # Draw label
            if zoom > 0.5:
                painter.setPen(QPen(Qt.white))
                font = painter.font()
                font.setPixelSize(int(10 * zoom))
                painter.setFont(font)
                painter.drawText(comp_rect, Qt.AlignCenter, prim.display_name)
            
            # Draw terminals
            from ui.model.geometry import get_lane_y_offset
            
            pad_radius = max(2.0, 3.0 * zoom)
            
            # Inputs on left
            painter.setBrush(QBrush(QColor("#a0aec0")))
            painter.setPen(Qt.NoPen)
            for i in range(prim.num_inputs):
                y_offset_cells = get_lane_y_offset(i, prim.num_inputs, bounds.height)
                cy_scene = scene_top + (y_offset_cells * gs)
                cx_scene = scene_left
                
                pt_view = camera.scene_to_view(QPointF(cx_scene, cy_scene))
                
                # Shift pad to edge of component block
                painter.drawEllipse(QPointF(comp_rect.left(), pt_view.y()), pad_radius, pad_radius)
                
            # Outputs on right
            for i in range(prim.num_outputs):
                y_offset_cells = get_lane_y_offset(i, prim.num_outputs, bounds.height)
                cy_scene = scene_top + (y_offset_cells * gs)
                cx_scene = scene_left + scene_width
                
                pt_view = camera.scene_to_view(QPointF(cx_scene, cy_scene))
                
                painter.drawEllipse(QPointF(comp_rect.right(), pt_view.y()), pad_radius, pad_radius)


    def _draw_platform(self, painter: QPainter, camera: Camera, bounds: GridBounds):
        """Draw the bounded platform plate, edge, and gasket."""
        if bounds.width == 0 or bounds.height == 0:
            return
            
        zoom = camera.zoom
        gs = self.theme.grid_size
        
        # Scene coordinates for platform base
        scene_left = bounds.x * gs
        scene_top = bounds.y * gs
        scene_width = bounds.width * gs
        scene_height = bounds.height * gs
        
        platform_rect_scene = QRectF(scene_left, scene_top, scene_width, scene_height)
        
        # View coordinates
        tl_view = camera.scene_to_view(platform_rect_scene.topLeft())
        br_view = camera.scene_to_view(platform_rect_scene.bottomRight())
        view_rect = QRectF(tl_view, br_view)
        
        # Platform plate
        painter.setBrush(QBrush(QColor(self.theme.platform_color)))
        
        # Edge and gasket are procedural
        # Draw base plate (platform body + outer edge)
        edge_width = self.theme.platform_edge_width_pixels
        painter.setPen(QPen(QColor(self.theme.platform_edge_color), edge_width))
        painter.drawRect(view_rect)
        
        # Draw gasket
        gasket_width = self.theme.gasket_width_pixels
        inset_rect = view_rect.adjusted(
            edge_width, edge_width, -edge_width, -edge_width
        )
        
        painter.setPen(QPen(QColor(self.theme.gasket_color), gasket_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(inset_rect)
        
    def render(self, painter: QPainter, camera: Camera, view_rect: QRectF, platform_bounds: GridBounds,
               board_state=None, selection_state=None, registry=None, preview_trace=None):
        """Render the board view."""
        # 1. Background
        painter.fillRect(view_rect, QColor(self.theme.background_color))
        
        # 2. Grid
        self._draw_grid(painter, camera, view_rect)
        
        # 3. Platform
        painter.setRenderHint(QPainter.Antialiasing, False) # Keep procedural/stepped style
        self._draw_platform(painter, camera, platform_bounds)

        # 4. Traces
        if board_state and selection_state:
            draw_traces(painter, camera, self.theme, board_state, selection_state, preview_trace)

        # 5. Nodes
        if board_state and selection_state:
            draw_nodes(painter, camera, self.theme, board_state, selection_state)

        # 6. Components
        if board_state and registry:
            self._draw_components(painter, camera, board_state, selection_state, registry)
