import uuid
from PySide6.QtCore import Qt, QPointF
from ui.model.component_instance import ComponentInstance
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
from ui.tools.trace_tool import TraceTool

class InputController:
    """Canonical input controller shell for the LXS UI."""
    def __init__(self, board_view, board_state, selection_state, tool_state, registry):
        self.board_view = board_view
        self.board_state = board_state
        self.selection_state = selection_state
        self.tool_state = tool_state
        self.registry = registry
        self.trace_tool = TraceTool(board_state, registry)
        
        self.board_view.input_controller = self
        
        self.dragging_component_id = None
        self.dragging_node_id = None
        self.drag_start_pos = None
        self.drag_start_comp_pos = None

    def handle_mouse_press(self, event):
        scene_x, scene_y, grid_x, grid_y = self._event_positions(event)

        if event.button() == Qt.RightButton:
            trace_id = self.board_state.get_trace_at(scene_x, scene_y)
            node = self.trace_tool.create_node_on_trace(scene_x, scene_y, trace_id)
            if node is not None:
                self.selection_state.selected_component_ids = []
                self.selection_state.selected_trace_ids = []
                self.selection_state.selected_node_ids = [node.id]
                self.board_view.update()
            return

        if event.button() == Qt.LeftButton:
            
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
                self.selection_state.select_component(comp_id)
                self.board_view.update()
            
            elif self.tool_state.active_tool_id == "trace":
                endpoint = self._get_terminal_endpoint_at(scene_x, scene_y)
                trace = self.trace_tool.click_endpoint(endpoint)
                if trace is not None:
                    self.selection_state.select_trace(trace.id)
                self.board_view.update()
            
            elif self.tool_state.active_tool_id == "select":
                clicked_node_id = self.board_state.get_node_at(scene_x, scene_y)
                if clicked_node_id:
                    self.selection_state.select_node(clicked_node_id)
                    self.dragging_node_id = clicked_node_id
                    self.drag_start_pos = QPointF(scene_x, scene_y)
                else:
                    clicked_trace_id = self._get_trace_at(scene_x, scene_y)
                    if clicked_trace_id is not None:
                        self.selection_state.select_trace(clicked_trace_id)
                    else:
                        clicked_comp_id = self._get_component_at(grid_x, grid_y)
                        if clicked_comp_id:
                            self.selection_state.select_component(clicked_comp_id)
                            self.dragging_component_id = clicked_comp_id
                            self.drag_start_pos = QPointF(grid_x, grid_y)
                            comp = self.board_state.components[clicked_comp_id]
                            self.drag_start_comp_pos = QPointF(comp.x, comp.y)
                        else:
                            self.selection_state.clear()
                            self.trace_tool.preview_trace = None
                self.board_view.update()

    def handle_mouse_move(self, event):
        if self.dragging_node_id:
            scene_x, scene_y, _, _ = self._event_positions(event)
            node = self.board_state.nodes[self.dragging_node_id]
            node.x = self._snap_trace_coordinate(scene_x)
            node.y = self._snap_trace_coordinate(scene_y)
            self.trace_tool.reroute_connected_node(node.id)
            self.board_view.update()
        elif self.dragging_component_id:
            _, _, grid_x, grid_y = self._event_positions(event)
            
            dx = grid_x - self.drag_start_pos.x()
            dy = grid_y - self.drag_start_pos.y()
            
            comp = self.board_state.components[self.dragging_component_id]
            comp.x = int(self.drag_start_comp_pos.x() + dx)
            comp.y = int(self.drag_start_comp_pos.y() + dy)
            self.trace_tool.reroute_connected_component(comp.id)
            self.board_view.update()
        elif self.tool_state.active_tool_id == "trace" and self.trace_tool.start_endpoint is not None:
            scene_x, scene_y, _, _ = self._event_positions(event)
            endpoint = self._get_terminal_endpoint_at(scene_x, scene_y)
            self.trace_tool.update_preview(endpoint)
            self.board_view.update()

    def handle_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_component_id = None
            self.dragging_node_id = None

    def handle_key_press(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            for comp_id in self.selection_state.selected_component_ids:
                if comp_id in self.board_state.components:
                    del self.board_state.components[comp_id]
            for trace_id in self.selection_state.selected_trace_ids:
                if trace_id in self.board_state.traces:
                    del self.board_state.traces[trace_id]
                node_ids = [
                    node_id
                    for node_id, node in self.board_state.nodes.items()
                    if node.owner_trace_id == trace_id
                ]
                for node_id in node_ids:
                    del self.board_state.nodes[node_id]
            for node_id in self.selection_state.selected_node_ids:
                if node_id in self.board_state.nodes:
                    del self.board_state.nodes[node_id]
            self.selection_state.clear()
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

    def _get_trace_at(self, scene_x, scene_y):
        selected_trace_ids = list(self.selection_state.selected_trace_ids)
        ordered_trace_ids = list(reversed(selected_trace_ids))
        ordered_trace_ids.extend(
            trace_id
            for trace_id in reversed(self.board_state.traces.keys())
            if trace_id not in selected_trace_ids
        )
        for trace_id in ordered_trace_ids:
            trace = self.board_state.traces.get(trace_id)
            if trace is not None and self.board_state.trace_contains_point(trace, scene_x, scene_y):
                return trace_id
        return None

    def _get_terminal_endpoint_at(self, scene_x, scene_y, tolerance=0.35):
        for comp_id, comp in reversed(self.board_state.components.items()):
            primitive = self.registry.get_primitive(comp.type_id)
            if primitive is None:
                continue

            for index in range(primitive.num_inputs):
                terminal = TerminalRef(component_id=comp_id, is_input=True, index=index)
                endpoint = TraceEndpoint(terminal=terminal)
                if self._scene_near_endpoint(scene_x, scene_y, endpoint, tolerance):
                    return endpoint

            for index in range(primitive.num_outputs):
                terminal = TerminalRef(component_id=comp_id, is_input=False, index=index)
                endpoint = TraceEndpoint(terminal=terminal)
                if self._scene_near_endpoint(scene_x, scene_y, endpoint, tolerance):
                    return endpoint
        return None

    def _scene_near_endpoint(self, scene_x, scene_y, endpoint, tolerance):
        position = self.board_state.get_endpoint_position(endpoint, self.registry)
        if position is None:
            return False
        return abs(scene_x - position[0]) <= tolerance and abs(scene_y - position[1]) <= tolerance

    @staticmethod
    def _snap_trace_coordinate(value):
        return round(value * 4.0) / 4.0

    def _event_positions(self, event):
        scene_pos = self.board_view.camera.view_to_scene(event.position())
        scene_x = scene_pos.x() / self.board_view.renderer.theme.grid_size
        scene_y = scene_pos.y() / self.board_view.renderer.theme.grid_size
        return scene_x, scene_y, round(scene_x), round(scene_y)
