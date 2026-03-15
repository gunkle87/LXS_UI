from PySide6.QtWidgets import QMainWindow, QDockWidget
from PySide6.QtCore import Qt

from ui.widgets.menu_bar import AppMenuBar
from ui.widgets.status_bar import AppStatusBar
from ui.board_view import BoardView
from ui.widgets.inspector_panel import InspectorPanel

class MainWindow(QMainWindow):
    """Canonical main window for the LXS UI."""
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("LXS UI Workbench")
        self.resize(1024, 768)
        
        # 1. Top menu bar (Program and Edit)
        self.app_menu_bar = AppMenuBar(self)
        self.setMenuBar(self.app_menu_bar)
        
        # 2. Central board viewport shell
        self.board_view = BoardView(self)
        self.setCentralWidget(self.board_view)
        
        # 3. Left-side placeholder tool/component area
        self.inspector_dock = QDockWidget("Tools", self)
        self.inspector_panel = InspectorPanel(self.inspector_dock)
        self.inspector_dock.setWidget(self.inspector_panel)
        self.inspector_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.inspector_dock)
        
        # 4. Status bar
        self.app_status_bar = AppStatusBar(self)
        self.setStatusBar(self.app_status_bar)
        
        # Wire actions
        self.app_menu_bar.exit_action.triggered.connect(self.close)
