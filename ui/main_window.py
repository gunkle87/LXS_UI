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
from ui.services.engine_bridge import EngineBridge
from ui.services.project_io import ProjectIO
from ui.services.simulation_controller import SimulationController
from ui.tool_controller import ToolController
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
        self.tool_controller = ToolController(self.tool_state)
        self.clipboard = Clipboard()
        self.command_stack = CommandStack()
        self.project_io = ProjectIO()
        self.simulation_controller = SimulationController(EngineBridge())
        
        self.setWindowTitle("LXS UI Workbench")
        self.resize(1024, 768)
        
        # 1. Top menu bar (Program and Edit)
        self.app_menu_bar = AppMenuBar(self)
        self.setMenuBar(self.app_menu_bar)
        
        # 2. Central board viewport shell
        self.board_view = BoardView(self)
        self.board_view.set_models(self.board_state, self.selection_state, self.registry, self.simulation_controller.snapshot)
        self.setCentralWidget(self.board_view)
        
        self.input_controller = InputController(
            self.board_view,
            self.board_state,
            self.selection_state,
            self.tool_state,
            self.registry,
            command_stack=self.command_stack,
            clipboard=self.clipboard,
            ui_callback=self.on_ui_state_changed,
        )
        self.menu_controller = MenuController(
            self,
            self.input_controller,
            self.board_state,
            self.selection_state,
            self.tool_state,
            self.command_stack,
            self.project_io,
            ui_callback=self.on_ui_state_changed,
        )
        
        # 3. Left-side placeholder tool/component area
        self.inspector_dock = QDockWidget("Tools", self)
        self.inspector_panel = InspectorPanel(self.inspector_dock)
        self.inspector_panel.set_registry(self.registry, self.tool_controller)
        self.inspector_panel.set_callbacks(self.step_simulation, self.toggle_selected_input)
        self.inspector_dock.setWidget(self.inspector_panel)
        self.inspector_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.inspector_dock)
        
        # 4. Status bar
        self.app_status_bar = AppStatusBar(self)
        self.setStatusBar(self.app_status_bar)
        
        # Wire actions
        self.menu_controller.wire_actions(self.app_menu_bar)
        self.app_menu_bar.exit_action.triggered.connect(self.close)
        self.refresh_presentation()

    def on_ui_state_changed(self, board_changed: bool, selection_changed: bool):
        if board_changed:
            self.simulation_controller.mark_dirty("Board changed; step to refresh state")
        self.refresh_presentation()

    def step_simulation(self):
        try:
            self.simulation_controller.step(self.board_state, self.registry)
        except Exception as exc:
            self.simulation_controller.mark_dirty(f"Simulation error: {exc}")
        self.refresh_presentation()

    def toggle_selected_input(self):
        if not self.selection_state.selected_component_ids:
            return
        component_id = self.selection_state.selected_component_ids[0]
        component = self.board_state.components.get(component_id)
        if component is None or component.type_id != "input":
            return
        self.simulation_controller.toggle_input_value(component_id)
        self.refresh_presentation()

    def refresh_presentation(self):
        self.board_view.simulation_snapshot = self.simulation_controller.snapshot
        self.inspector_panel.update_inspector(
            self.board_state,
            self.selection_state,
            self.simulation_controller.snapshot,
        )
        self.app_status_bar.update_simulation_status(
            self.simulation_controller.snapshot,
            self.simulation_controller.selected_object_summary(self.board_state, self.selection_state),
        )
        self.board_view.update()
