from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt

class BoardView(QGraphicsView):
    """Canonical board viewport shell."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Base setup for v0 constraints
        self.setRenderHint(self.renderHints()) # Placeholder for anti-aliasing if needed
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Temporary placeholder content
        self.scene.addText("Central Board Viewport Shell")
