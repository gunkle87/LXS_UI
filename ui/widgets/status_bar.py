from PySide6.QtWidgets import QStatusBar

class AppStatusBar(QStatusBar):
    """Canonical status bar for the LXS UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.showMessage("Ready")
