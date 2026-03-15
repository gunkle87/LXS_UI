from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction

class AppMenuBar(QMenuBar):
    """Canonical menu bar for the LXS UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Program Menu
        self.program_menu = QMenu("Program", self)
        self.exit_action = QAction("Exit", self)
        self.program_menu.addAction(self.exit_action)
        self.addMenu(self.program_menu)
        
        # Edit Menu
        self.edit_menu = QMenu("Edit", self)
        self.undo_action = QAction("Undo", self)
        self.redo_action = QAction("Redo", self)
        self.edit_menu.addAction(self.undo_action)
        self.edit_menu.addAction(self.redo_action)
        self.addMenu(self.edit_menu)
