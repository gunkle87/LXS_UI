@echo off
setlocal
set "ROOT=%~dp0.."
set PYTHONPATH=%ROOT%
call "%ROOT%\.venv\Scripts\activate.bat"

set "PYTHONW=%ROOT%\.venv\Scripts\pythonw.exe"
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"

if exist "%PYTHONW%" (
    start "" "%PYTHONW%" -m ui.app
) else (
    start "" "%PYTHON%" -m ui.app
)
