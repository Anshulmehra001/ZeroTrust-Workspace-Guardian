@echo off
echo Starting ZeroTrust Workspace Guardian...
echo.
start "Guardian Monitor" python guardian.py
timeout /t 2 /nobreak >nul
start "Security Dashboard" python dashboard.py
echo.
echo Both systems started!
echo - Guardian Monitor: Security camera feed
echo - Security Dashboard: Threat logs and statistics
echo.
echo Press any key to exit...
pause >nul
