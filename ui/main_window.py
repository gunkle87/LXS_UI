from PySide6.QtWidgets import QMainWindow, QDockWidget
from PySide6.QtCore import Qt

from ui.widgets.menu_bar import AppMenuBar
from ui.widgets.status_bar import AppStatusBar
from ui.board_view import BoardView
from ui.widgets.inspector_panel import InspectorPanel

from ui.clipboard import Clipboard
from ui.menu_controller import MenuController
from ui.services.primitive_registry import PrimitiveRegistry
from ui.services.command_stack import CommandStack
from ui.services.project_io import ProjectIO
from ui.model.board_state import BoardState
from ui.model.selection_state import SelectionState
from ui.model.tool_state import ToolState
from ui.input_controller import InputController

class MainWindow(QMainWindow):
    """Canonical main window for the LXS UI."""
    def __init__(self):
        super().__init__()
        
        # Core Models & Services
        self.registry = PrimitiveRegistry()
        self.board_state = BoardState()
        self.selection_state = SelectionState()
        self.tool_state = ToolState()
        self.clipboard = Clipboard()
        self.command_stack = CommandStack()
        self.project_io = ProjectIO()
        
        self.setWindowTitle("LXS UI Workbench")
        self.resize(1024, 768)
        
        # 1. Top menu bar (Program and Edit)
        self.app_menu_bar = AppMenuBar(self)
        self.setMenuBar(self.app_menu_bar)
        
        # 2. Central board viewport shell
        self.board_view = BoardView(self)
        self.board_view.set_models(self.board_state, self.selection_state, self.registry)
        self.setCentralWidget(self.board_view)
        
        self.input_controller = InputController(
            self.board_view,
            self.board_state,
            self.selection_state,
            self.tool_state,
            self.registry,
            command_stack=self.command_stack,
            clipboard=self.clipboard,
        )
        self.menu_controller = MenuController(
            self,
            self.input_controller,
            self.board_state,
            self.selection_state,
            self.tool_state,
            self.command_stack,
            self.project_io,
        )
        
        # 3. Left-side placeholder tool/component area
        self.inspector_dock = QDockWidget("Tools", self)
        self.inspector_panel = InspectorPanel(self.inspector_dock)
        self.inspector_panel.set_registry(self.registry, self.tool_state)
        self.inspector_dock.setWidget(self.inspector_panel)
        self.inspector_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.inspector_dock)
        
        # 4. Status bar
        self.app_status_bar = AppStatusBar(self)
        self.setStatusBar(self.app_status_bar)
        
        # Wire actions
        self.menu_controller.wire_actions(self.app_menu_bar)
        self.app_menu_bar.exit_action.triggered.connect(self.close)
