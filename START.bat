@echo off
cd /d "%~dp0"

REM Find a Python command.
set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 --version >nul 2>nul
  if %errorlevel%==0 set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python --version >nul 2>nul
    if %errorlevel%==0 set "PYTHON_CMD=python"
  )
)

if not defined PYTHON_CMD (
  echo Python was not found.
  echo Install Python, or start the server manually with a working Python command.
  pause
  exit /b 1
)

REM Start the server in a new window.
start "School Report Server" cmd /k %PYTHON_CMD% server.py
timeout /t 2 /nobreak >nul

REM Check that the server is working.
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/student' -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }"
if not %errorlevel%==0 (
  echo Server did not start on http://127.0.0.1:8000.
  echo Check the server window for the error message.
  pause
  exit /b 1
)

REM Open student page and teacher page.
start "" "http://127.0.0.1:8000/student"
start "" "http://127.0.0.1:8000/teacher?key=teacher123"
