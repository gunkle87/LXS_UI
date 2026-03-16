from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter
from PySide6.QtGui import QPainterPath
from PySide6.QtGui import QPen


def ordered_trace_ids(board_state, selection_state):
    selected = list(selection_state.selected_trace_ids)
    ordered_ids = [
        trace_id
        for trace_id in board_state.traces.keys()
        if trace_id not in selected
    ]
    ordered_ids.extend(selected)
    return ordered_ids


def draw_traces(painter: QPainter, camera, theme, board_state, selection_state, preview_trace=None):
    ordered_ids = ordered_trace_ids(board_state, selection_state)
    for trace_id in ordered_ids:
        trace = board_state.traces[trace_id]
        is_selected = trace_id in selection_state.selected_trace_ids
        _draw_single_trace(painter, camera, theme, trace.vertices, trace_id, is_selected)

    if preview_trace is not None and preview_trace.vertices:
        _draw_single_trace(painter, camera, theme, preview_trace.vertices, preview_trace.id, True, preview=True)


def _draw_single_trace(painter: QPainter, camera, theme, vertices, trace_id: str, is_selected: bool, preview: bool = False):
    if len(vertices) < 2:
        return

    path = QPainterPath()
    first = camera.scene_to_view(_grid_point_to_scene(vertices[0], theme.grid_size))
    path.moveTo(first)
    for vertex in vertices[1:]:
        path.lineTo(camera.scene_to_view(_grid_point_to_scene(vertex, theme.grid_size)))

    color = QColor(theme.trace_highlight_color if is_selected else _trace_color(theme, trace_id))
    if preview:
        color.setAlpha(160)

    outer_width = theme.trace_selected_outer_width if is_selected else theme.trace_outer_width
    inner_width = theme.trace_selected_inner_width if is_selected else theme.trace_inner_width

    painter.setPen(QPen(QColor(theme.trace_outline_color), outer_width))
    painter.drawPath(path)
    painter.setPen(QPen(color, inner_width))
    painter.drawPath(path)


def _trace_color(theme, trace_id: str) -> str:
    palette = theme.trace_palette
    return palette[sum(ord(char) for char in trace_id) % len(palette)]


def _grid_point_to_scene(vertex, grid_size: int) -> QPointF:
    return QPointF(vertex.x * grid_size, vertex.y * grid_size)
