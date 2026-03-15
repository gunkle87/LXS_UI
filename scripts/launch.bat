@echo off
set PYTHONPATH=%~dp0..
call "%~dp0..\.venv\Scripts\activate.bat"
python -m ui.app
