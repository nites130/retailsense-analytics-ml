@echo off
setlocal
cd /d "%~dp0"
echo =============================================
echo       RetailSense - Website Launcher
 echo =============================================
if not exist ".venv\Scripts\python.exe" (
  python --version >nul 2>&1
  if errorlevel 1 (
    echo Python was not found. Install Python and select Add Python to PATH.
    pause
    exit /b 1
  )
  echo Creating Python environment...
  python -m venv .venv
  if errorlevel 1 goto :failed
)
echo Checking project dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :failed
echo.
echo Open http://127.0.0.1:5000 in your browser.
echo Keep this window open while using RetailSense.
echo Press Ctrl+C to stop the website.
".venv\Scripts\python.exe" app.py
pause
exit /b
:failed
echo.
echo Setup failed. Take a screenshot of this window for troubleshooting.
echo Python 3.12 is the tested version. See START_HERE.md.
pause
exit /b 1
