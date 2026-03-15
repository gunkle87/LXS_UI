from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPaintEvent, QWheelEvent, QMouseEvent

from ui.camera import Camera
from ui.render.board_renderer import BoardRenderer
from ui.model.platform_state import PlatformState
from ui.model.geometry import GridBounds

class BoardView(QWidget):
    """Canonical board viewport shell."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.camera = Camera()
        self.renderer = BoardRenderer()
        
        # Base platform bounds for empty board
        # In actual use, this will be derived from placed components
        self.platform_bounds = GridBounds(-10, -10, 10, 10)
        
        # Panning state
        self._is_panning = False
        self._last_mouse_pos = QPointF()

    def update_platform_bounds(self, new_bounds: GridBounds):
        """Update platform boundaries and trigger repaint."""
        self.platform_bounds = new_bounds
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        view_rect = QRectF(self.rect())
        self.renderer.render(painter, self.camera, view_rect, self.platform_bounds)

    def wheelEvent(self, event: QWheelEvent):
        """Handle stepped zoom via mouse wheel."""
        if event.angleDelta().y() > 0:
            self.camera.zoom_in()
        else:
            self.camera.zoom_out()
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """Start pan on middle mouse button."""
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_mouse_pos = event.position()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle panning drag."""
        if self._is_panning:
            delta = event.position() - self._last_mouse_pos
            self.camera.pan(delta.x(), delta.y())
            self._last_mouse_pos = event.position()
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """End pan on middle mouse release."""
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
        else:
            super().mouseReleaseEvent(event)
