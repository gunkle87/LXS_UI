import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Bootstrap entry point for the LXS UI."""
    app = QApplication(sys.argv)
    
    # Initialize the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
