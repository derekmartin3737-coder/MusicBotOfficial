@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%render_song_selection_annotation.ps1" -InputPath "%SCRIPT_DIR%song_selection_input.png" -OutputPath "%SCRIPT_DIR%song_selection_annotated.png"

endlocal
