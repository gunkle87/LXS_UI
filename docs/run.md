# Run Instructions

The LXS UI Workbench is a Python PySide6 application.

## Prerequisites
- Python 3.10+

## Setup
1. Open a terminal in `C:\DEV\LXS_UI`
2. Create a virtual environment:
   ```cmd
   python -m venv .venv
   ```
3. Activate the environment:
   ```cmd
   .venv\Scripts\activate
   ```
4. Install requirements:
   ```cmd
   pip install PySide6
   ```

## Launching
You can launch the application via the provided batch script:
```cmd
scripts\launch.bat
```

Alternatively, from an activated environment:
```cmd
python -m ui.app
```
