from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction

class AppMenuBar(QMenuBar):
    """Canonical menu bar for the LXS UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Program Menu
        self.program_menu = QMenu("Program", self)
        self.new_action = QAction("New", self)
        self.open_action = QAction("Open...", self)
        self.save_action = QAction("Save", self)
        self.save_as_action = QAction("Save As...", self)
        self.exit_action = QAction("Exit", self)
        self.program_menu.addAction(self.new_action)
        self.program_menu.addAction(self.open_action)
        self.program_menu.addAction(self.save_action)
        self.program_menu.addAction(self.save_as_action)
        self.program_menu.addSeparator()
        self.program_menu.addAction(self.exit_action)
        self.addMenu(self.program_menu)
        
        # Edit Menu
        self.edit_menu = QMenu("Edit", self)
        self.undo_action = QAction("Undo", self)
        self.redo_action = QAction("Redo", self)
        self.copy_action = QAction("Copy", self)
        self.paste_action = QAction("Paste", self)
        self.duplicate_action = QAction("Duplicate", self)
        self.delete_action = QAction("Delete", self)
        self.edit_menu.addAction(self.undo_action)
        self.edit_menu.addAction(self.redo_action)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(self.copy_action)
        self.edit_menu.addAction(self.paste_action)
        self.edit_menu.addAction(self.duplicate_action)
        self.edit_menu.addAction(self.delete_action)
        self.addMenu(self.edit_menu)
