import uuid
from PySide6.QtCore import Qt, QPointF
from ui.model.component_instance import ComponentInstance

class InputController:
    """Canonical input controller shell for the LXS UI."""
    def __init__(self, board_view, board_state, selection_state, tool_state, registry):
        self.board_view = board_view
        self.board_state = board_state
        self.selection_state = selection_state
        self.tool_state = tool_state
        self.registry = registry
        
        self.board_view.input_controller = self
        
        self.dragging_component_id = None
        self.drag_start_pos = None
        self.drag_start_comp_pos = None

    def handle_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.board_view.camera.view_to_scene(event.position())
            grid_x = round(scene_pos.x() / self.board_view.renderer.theme.grid_size)
            grid_y = round(scene_pos.y() / self.board_view.renderer.theme.grid_size)
            
            if self.tool_state.active_tool_id == "place" and self.tool_state.selected_primitive_id:
                # Place new component
                comp_id = f"comp_{uuid.uuid4().hex[:8]}"
                comp = ComponentInstance(
                    id=comp_id,
                    type_id=self.tool_state.selected_primitive_id,
                    x=grid_x,
                    y=grid_y
                )
                self.board_state.add_component(comp)
                self.selection_state.selected_component_ids = [comp_id]
                self.board_view.update()
            
            elif self.tool_state.active_tool_id == "select":
                # Select component under cursor
                clicked_comp_id = self._get_component_at(grid_x, grid_y)
                if clicked_comp_id:
                    self.selection_state.selected_component_ids = [clicked_comp_id]
                    self.dragging_component_id = clicked_comp_id
                    self.drag_start_pos = QPointF(grid_x, grid_y)
                    comp = self.board_state.components[clicked_comp_id]
                    self.drag_start_comp_pos = QPointF(comp.x, comp.y)
                else:
                    self.selection_state.selected_component_ids = []
                self.board_view.update()

    def handle_mouse_move(self, event):
        if self.dragging_component_id:
            scene_pos = self.board_view.camera.view_to_scene(event.position())
            grid_x = round(scene_pos.x() / self.board_view.renderer.theme.grid_size)
            grid_y = round(scene_pos.y() / self.board_view.renderer.theme.grid_size)
            
            dx = grid_x - self.drag_start_pos.x()
            dy = grid_y - self.drag_start_pos.y()
            
            comp = self.board_state.components[self.dragging_component_id]
            comp.x = int(self.drag_start_comp_pos.x() + dx)
            comp.y = int(self.drag_start_comp_pos.y() + dy)
            self.board_view.update()

    def handle_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_component_id = None

    def handle_key_press(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            for comp_id in self.selection_state.selected_component_ids:
                if comp_id in self.board_state.components:
                    del self.board_state.components[comp_id]
            self.selection_state.selected_component_ids = []
            self.board_view.update()

    def _get_component_at(self, x, y):
        # Reverse iterate to get top-most (though they shouldn't overlap)
        for comp_id, comp in reversed(self.board_state.components.items()):
            prim = self.registry.get_primitive(comp.type_id)
            if prim:
                bounds = comp.get_bounds(prim)
                if bounds.x <= x < bounds.x + bounds.width and bounds.y <= y < bounds.y + bounds.height:
                    return comp_id
        return None
