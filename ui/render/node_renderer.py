from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor
from PySide6.QtGui import QBrush
from PySide6.QtGui import QPainter
from PySide6.QtGui import QPen


def draw_nodes(painter: QPainter, camera, theme, board_state, selection_state):
    node_size = theme.node_size_cells * theme.grid_size
    highlight_padding = theme.node_highlight_padding_cells * theme.grid_size
    for node_id, node in board_state.nodes.items():
        center = camera.scene_to_view(QPointF(node.x * theme.grid_size, node.y * theme.grid_size))
        node_rect = QRectF(
            center.x() - node_size / 2.0,
            center.y() - node_size / 2.0,
            node_size,
            node_size,
        )

        if node_id in selection_state.selected_node_ids:
            highlight_rect = node_rect.adjusted(-highlight_padding, -highlight_padding, highlight_padding, highlight_padding)
            painter.setPen(QPen(QColor(theme.node_highlight_color), 2.0))
            painter.setBrush(QBrush(QColor(theme.node_highlight_color)))
            painter.drawRect(highlight_rect)

        painter.setPen(QPen(QColor(theme.node_border_color), 1.5))
        painter.setBrush(QBrush(QColor(theme.node_fill_color)))
        painter.drawRect(node_rect)
