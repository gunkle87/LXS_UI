from PySide6.QtWidgets import QStatusBar

class AppStatusBar(QStatusBar):
    """Canonical status bar for the LXS UI."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.showMessage("Ready")

    def update_simulation_status(self, simulation_snapshot, selected_summary: str):
        self.showMessage(
            f"{simulation_snapshot.engine_status} | {selected_summary}"
        )
