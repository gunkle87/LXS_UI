import uuid
from PySide6.QtCore import Qt, QPointF
from ui.model.component_instance import ComponentInstance
from ui.model.node_instance import NodeInstance
from ui.model.trace_instance import TerminalRef
from ui.model.trace_instance import TraceEndpoint
from ui.model.trace_instance import TraceInstance
from ui.model.trace_instance import TraceVertex
from ui.tools.trace_tool import TraceTool

class InputController:
    """Canonical input controller shell for the LXS UI."""
    def __init__(self, board_view, board_state, selection_state, tool_state, registry, command_stack=None, clipboard=None):
        self.board_view = board_view
        self.board_state = board_state
        self.selection_state = selection_state
        self.tool_state = tool_state
        self.registry = registry
        self.command_stack = command_stack
        self.clipboard = clipboard
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
            self.delete_selection()

    def copy_selection(self):
        if self.clipboard is None:
            return False
        payload = self._selection_payload()
        if payload is None:
            return False
        self.clipboard.set_payload(payload)
        return True

    def paste_clipboard(self):
        if self.clipboard is None:
            return False
        payload = self.clipboard.get_payload()
        if payload is None:
            return False
        before_board, before_selection = self._capture_history()
        if not self._paste_payload(payload):
            return False
        self._record_history("Paste", before_board, before_selection)
        self.board_view.update()
        return True

    def duplicate_selection(self):
        payload = self._selection_payload()
        if payload is None:
            return False
        before_board, before_selection = self._capture_history()
        if not self._paste_payload(payload):
            return False
        self._record_history("Duplicate", before_board, before_selection)
        self.board_view.update()
        return True

    def delete_selection(self):
        before_board, before_selection = self._capture_history()
        changed = False

        for comp_id in list(self.selection_state.selected_component_ids):
            if comp_id in self.board_state.components:
                self._delete_component(comp_id)
                changed = True
        for trace_id in list(self.selection_state.selected_trace_ids):
            if trace_id in self.board_state.traces:
                self._delete_trace(trace_id)
                changed = True
        for node_id in list(self.selection_state.selected_node_ids):
            if node_id in self.board_state.nodes:
                owner_trace_id = self.board_state.nodes[node_id].owner_trace_id
                del self.board_state.nodes[node_id]
                self.trace_tool.reroute_trace(owner_trace_id)
                changed = True

        if not changed:
            return False

        self.selection_state.clear()
        self.cancel_transient_state()
        self._record_history("Delete", before_board, before_selection)
        self.board_view.update()
        return True

    def undo(self):
        if self.command_stack is None:
            return False
        restored = self.command_stack.undo(self.board_state, self.selection_state)
        if restored:
            self.cancel_transient_state()
            self.board_view.update()
        return restored

    def redo(self):
        if self.command_stack is None:
            return False
        restored = self.command_stack.redo(self.board_state, self.selection_state)
        if restored:
            self.cancel_transient_state()
            self.board_view.update()
        return restored

    def cancel_transient_state(self):
        self.trace_tool.cancel_trace()
        self.dragging_component_id = None
        self.dragging_node_id = None
        self.drag_start_pos = None
        self.drag_start_comp_pos = None

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

    def _capture_history(self):
        return self.board_state.snapshot(), self.selection_state.snapshot()

    def _record_history(self, label, before_board, before_selection):
        if self.command_stack is None:
            return False
        return self.command_stack.record_transition(
            label=label,
            before_board=before_board,
            after_board=self.board_state.snapshot(),
            before_selection=before_selection,
            after_selection=self.selection_state.snapshot(),
        )

    def _selection_payload(self):
        if self.selection_state.selected_component_ids:
            component_id = self.selection_state.selected_component_ids[0]
            component = self.board_state.components.get(component_id)
            if component is None:
                return None
            return {
                "kind": "component",
                "component": {
                    "id": component.id,
                    "type_id": component.type_id,
                    "x": component.x,
                    "y": component.y,
                },
            }

        if self.selection_state.selected_trace_ids:
            trace_id = self.selection_state.selected_trace_ids[0]
            trace = self.board_state.traces.get(trace_id)
            if trace is None:
                return None
            return {
                "kind": "trace",
                "trace": {
                    "id": trace.id,
                    "source": self.board_state._endpoint_snapshot(trace.source),
                    "target": self.board_state._endpoint_snapshot(trace.target),
                    "vertices": [
                        {"x": vertex.x, "y": vertex.y}
                        for vertex in trace.vertices
                    ],
                },
                "nodes": [
                    {
                        "id": node.id,
                        "x": node.x,
                        "y": node.y,
                        "owner_trace_id": node.owner_trace_id,
                    }
                    for node in self.board_state.get_owner_nodes_for_trace(trace_id)
                ],
            }
        return None

    def _paste_payload(self, payload):
        kind = payload.get("kind")
        if kind == "component":
            component_data = payload["component"]
            new_component = ComponentInstance(
                id=f"comp_{uuid.uuid4().hex[:8]}",
                type_id=component_data["type_id"],
                x=int(component_data["x"]) + 1,
                y=int(component_data["y"]) + 1,
            )
            self.board_state.add_component(new_component)
            self.selection_state.select_component(new_component.id)
            return True

        if kind == "trace":
            trace_data = payload["trace"]
            new_trace_id = f"trace_{len(self.board_state.traces)}"
            node_id_map = {}
            for node_data in payload.get("nodes", []):
                new_node_id = f"node_{len(self.board_state.nodes) + len(node_id_map)}"
                node_id_map[node_data["id"]] = new_node_id

            def remap_endpoint(endpoint_data):
                endpoint_snapshot = {
                    "terminal": endpoint_data["terminal"],
                    "node_id": endpoint_data["node_id"],
                }
                node_id = endpoint_snapshot["node_id"]
                if node_id in node_id_map:
                    endpoint_snapshot["node_id"] = node_id_map[node_id]
                return self.board_state._endpoint_from_snapshot(endpoint_snapshot)

            for node_data in payload.get("nodes", []):
                new_node = NodeInstance(
                    id=node_id_map[node_data["id"]],
                    x=float(node_data["x"]) + 0.25,
                    y=float(node_data["y"]) + 1.0,
                    owner_trace_id=new_trace_id,
                )
                self.board_state.add_node(new_node)

            new_trace = TraceInstance(
                id=new_trace_id,
                source=remap_endpoint(trace_data["source"]),
                target=remap_endpoint(trace_data["target"]),
                vertices=[
                    TraceVertex(float(vertex["x"]), float(vertex["y"]))
                    for vertex in trace_data.get("vertices", [])
                ],
            )
            self.board_state.add_trace(new_trace)
            for node in self.board_state.get_owner_nodes_for_trace(new_trace_id):
                node.owner_trace_id = new_trace_id
            self.trace_tool.reroute_trace(new_trace_id)
            self.selection_state.select_trace(new_trace_id)
            return True
        return False

    def _delete_component(self, component_id):
        connected_trace_ids = list(self.board_state.iter_connected_trace_ids_for_component(component_id))
        for trace_id in connected_trace_ids:
            self._delete_trace(trace_id)
        del self.board_state.components[component_id]

    def _delete_trace(self, trace_id):
        if trace_id in self.board_state.traces:
            del self.board_state.traces[trace_id]
        node_ids = [
            node_id
            for node_id, node in self.board_state.nodes.items()
            if node.owner_trace_id == trace_id
        ]
        for node_id in node_ids:
            del self.board_state.nodes[node_id]
