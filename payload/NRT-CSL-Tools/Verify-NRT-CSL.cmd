@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Verify-NRT-CSL.ps1"
set "verifyResult=%errorlevel%"
pause
exit /b %verifyResult%
