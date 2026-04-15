@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%render_terminal_annotation.ps1" -InputPath "%SCRIPT_DIR%terminal_input.png" -OutputPath "%SCRIPT_DIR%terminal_annotated.png"

endlocal
