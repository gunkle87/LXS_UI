import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.model.component_instance import ComponentInstance


app = QApplication.instance() or QApplication(sys.argv)


def test_edit_menu_actions_drive_command_history():
    window = MainWindow()
    component = ComponentInstance(id="comp_a", type_id="and", x=1, y=1)
    window.board_state.add_component(component)
    window.selection_state.select_component(component.id)

    window.app_menu_bar.copy_action.trigger()
    assert window.clipboard.has_payload()

    window.app_menu_bar.paste_action.trigger()
    assert len(window.board_state.components) == 2
    assert window.command_stack.can_undo
    pasted_id = window.selection_state.selected_component_ids[0]
    assert pasted_id != component.id

    window.app_menu_bar.delete_action.trigger()
    assert len(window.board_state.components) == 1

    window.app_menu_bar.undo_action.trigger()
    assert len(window.board_state.components) == 2

    window.app_menu_bar.redo_action.trigger()
    assert len(window.board_state.components) == 1

    window.selection_state.select_component(component.id)
    window.app_menu_bar.duplicate_action.trigger()
    assert len(window.board_state.components) == 2
    assert window.selection_state.selected_component_ids[0] != component.id

