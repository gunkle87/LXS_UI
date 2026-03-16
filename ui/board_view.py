from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPaintEvent, QWheelEvent, QMouseEvent

from ui.camera import Camera
from ui.render.board_renderer import BoardRenderer
from ui.model.geometry import GridBounds
from ui.model.platform_state import DEFAULT_PLATFORM_BOUNDS

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
        self.platform_bounds = GridBounds(
            x=DEFAULT_PLATFORM_BOUNDS.x,
            y=DEFAULT_PLATFORM_BOUNDS.y,
            width=DEFAULT_PLATFORM_BOUNDS.width,
            height=DEFAULT_PLATFORM_BOUNDS.height,
        )
        
        # Panning state
        self._is_panning = False
        self._last_mouse_pos = QPointF()
        
        self.input_controller = None
        self.board_state = None
        self.selection_state = None
        self.registry = None
        self.simulation_snapshot = None

    def set_models(self, board_state, selection_state, registry, simulation_snapshot=None):
        self.board_state = board_state
        self.selection_state = selection_state
        self.registry = registry
        self.simulation_snapshot = simulation_snapshot

    def update_platform_bounds(self, new_bounds: GridBounds):
        """Update platform boundaries and trigger repaint."""
        self.platform_bounds = new_bounds
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        view_rect = QRectF(self.rect())
        preview_trace = None
        if self.input_controller is not None:
            preview_trace = self.input_controller.trace_tool.preview_trace
        self.renderer.render(painter, self.camera, view_rect, self.platform_bounds,
                             self.board_state, self.selection_state, self.registry, preview_trace, self.simulation_snapshot)

    def wheelEvent(self, event: QWheelEvent):
        """Handle stepped zoom via mouse wheel."""
        if event.angleDelta().y() > 0:
            self.camera.zoom_in_at(event.position())
        else:
            self.camera.zoom_out_at(event.position())
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """Start pan on middle mouse button."""
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_mouse_pos = event.position()
        elif self.input_controller:
            self.input_controller.handle_mouse_press(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle panning drag."""
        if self._is_panning:
            delta = event.position() - self._last_mouse_pos
            self.camera.pan(delta.x(), delta.y())
            self._last_mouse_pos = event.position()
            self.update()
        elif self.input_controller:
            self.input_controller.handle_mouse_move(event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """End pan on middle mouse release."""
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
        elif self.input_controller:
            self.input_controller.handle_mouse_release(event)
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if self.input_controller:
            self.input_controller.handle_key_press(event)
        else:
            super().keyPressEvent(event)
