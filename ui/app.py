import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Bootstrap entry point for the LXS UI."""
    app = QApplication(sys.argv)
    
    # Initialize the main window
    window = MainWindow()
    if "--smoke-test" in sys.argv:
        print("LXS_UI_APP_SMOKE_PASS")
        window.close()
        return 0
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
