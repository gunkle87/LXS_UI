from PySide6.QtCore import QPointF, QRectF
import math

class Camera:
    """Canonical camera shell for the LXS UI.
    
    Handles stepped zoom and panning.
    """
    
    ZOOM_STEPS = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
    DEFAULT_ZOOM_INDEX = 4 # 1.0
    
    def __init__(self):
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._zoom_index = self.DEFAULT_ZOOM_INDEX
        
    @property
    def zoom(self) -> float:
        return self.ZOOM_STEPS[self._zoom_index]
        
    def zoom_in(self) -> float:
        if self._zoom_index < len(self.ZOOM_STEPS) - 1:
            self._zoom_index += 1
        return self.zoom

    def zoom_in_at(self, view_point: QPointF) -> float:
        """Zoom in while keeping `view_point` stationary in scene coordinates."""
        return self._zoom_at_index(self._zoom_index + 1, view_point)
        
    def zoom_out(self) -> float:
        if self._zoom_index > 0:
            self._zoom_index -= 1
        return self.zoom

    def zoom_out_at(self, view_point: QPointF) -> float:
        """Zoom out while keeping `view_point` stationary in scene coordinates."""
        return self._zoom_at_index(self._zoom_index - 1, view_point)

    def _zoom_at_index(self, target_index: int, view_point: QPointF) -> float:
        """Move zoom to a target index and pan so `view_point` remains fixed."""
        target_index = max(0, min(target_index, len(self.ZOOM_STEPS) - 1))
        if target_index == self._zoom_index:
            return self.zoom

        scene_point = self.view_to_scene(view_point)
        self._zoom_index = target_index
        self.pan_x = view_point.x() - (scene_point.x() * self.zoom)
        self.pan_y = view_point.y() - (scene_point.y() * self.zoom)
        return self.zoom
        
    def pan(self, dx: float, dy: float):
        """Pan by pixel delta."""
        self.pan_x += dx
        self.pan_y += dy
        
    def set_pan(self, x: float, y: float):
        self.pan_x = x
        self.pan_y = y
        
    def view_to_scene(self, view_point: QPointF) -> QPointF:
        """Convert a viewport point to scene coordinates (unscaled)."""
        # (view_point - pan) / zoom = scene_point
        return QPointF(
            (view_point.x() - self.pan_x) / self.zoom,
            (view_point.y() - self.pan_y) / self.zoom
        )
        
    def scene_to_view(self, scene_point: QPointF) -> QPointF:
        """Convert a scene point to viewport coordinates."""
        return QPointF(
            (scene_point.x() * self.zoom) + self.pan_x,
            (scene_point.y() * self.zoom) + self.pan_y
        )
        
    def get_view_rect(self, viewport_rect: QRectF) -> QRectF:
        """Get the scene bounding rect visible in the given viewport rect."""
        top_left = self.view_to_scene(viewport_rect.topLeft())
        bottom_right = self.view_to_scene(viewport_rect.bottomRight())
        return QRectF(top_left, bottom_right)
