@echo off
setlocal
set "ROOT=%~dp0"

if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" "%ROOT%scripts\play_piano.py" %*
) else (
  python "%ROOT%scripts\play_piano.py" %*
)
