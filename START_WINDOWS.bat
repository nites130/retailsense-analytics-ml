@echo off
cd /d "%~dp0"
if exist "RetailSense\start_windows.bat" (
  call "RetailSense\start_windows.bat"
) else (
  echo Extract the entire ZIP first, then double-click START_WINDOWS.bat.
  pause
)
