import subprocess
import sys
import unittest
from pathlib import Path

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

    def test_app_smoke_flag_exits_cleanly(self):
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(**__import__("os").environ)
        env["PYTHONPATH"] = str(repo_root)
        env["QT_QPA_PLATFORM"] = "offscreen"
        result = subprocess.run(
            [str(repo_root / ".venv" / "Scripts" / "python.exe"), "-m", "ui.app", "--smoke-test"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("LXS_UI_APP_SMOKE_PASS", result.stdout)

if __name__ == "__main__":
    unittest.main()
