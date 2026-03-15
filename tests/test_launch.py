import sys
import unittest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Ensure QApplication exists before tests run
app = QApplication.instance() or QApplication(sys.argv)

class TestLaunch(unittest.TestCase):
    def test_main_window_instantiates(self):
        """Verify that the main window can be instantiated without crashing."""
        window = MainWindow()
        self.assertIsNotNone(window)
        self.assertEqual(window.windowTitle(), "LXS UI Workbench")

if __name__ == "__main__":
    unittest.main()
