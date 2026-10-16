@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "%~dp0run.py"
) else (
    python "%~dp0run.py"
)
set "task_status=%errorlevel%"
echo.
pause
exit /b %task_status%
