@echo off
setlocal
set "ROOT=%~dp0"

if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" "%ROOT%scripts\piano_tools.py" %*
) else (
  python "%ROOT%scripts\piano_tools.py" %*
)
