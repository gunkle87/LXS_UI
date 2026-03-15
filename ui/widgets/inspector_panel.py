from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class InspectorPanel(QWidget):
    """Placeholder tool/component area for the LXS UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        label = QLabel("Inspector / Tools / Components")
        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)
