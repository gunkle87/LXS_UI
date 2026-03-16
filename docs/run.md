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

## Pre-run Check (for new implementation sessions)

From `C:\DEV\LXS_UI`, run:

```cmd
powershell -ExecutionPolicy Bypass -File .\scripts\preflight.ps1
```

If this preflight check fails, stop and resolve the listed blocker before
continuing.

## Anti-Stall Requirement

Before coding a run:

- Create or open `artifacts\run_<NN>_heartbeat.txt` (`NN` is the run number).
- Add at least:
  - start entry,
  - milestone entry for each meaningful phase,
  - completion entry with `status=done` or blocker `status=blocked`.
- If no heartbeat line is added for 10+ minutes, stop and write a blocker entry before continuing.

You can use this helper script:

```cmd
powershell -ExecutionPolicy Bypass -File .\scripts\heartbeat.ps1 -Run 04 -Files "ui/board_view.py" -Action "start run 04" -Status in-progress -Next "implement placement"
```

Alternatively, from an activated environment:
```cmd
python -m ui.app
``` 
