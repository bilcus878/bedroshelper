@echo off
title Launch Chrome with Debug Port
echo ============================================================
echo  Step 1 of 2: Launch Chrome with remote debugging
echo ============================================================
echo.

REM Check if port is already open (previous debug session still running)
netstat -an | find "9222" | find "LISTENING" >nul 2>&1
if %errorlevel% == 0 (
    echo Port 9222 is already open - debug Chrome is running.
    echo You can go ahead and run start.bat
    pause
    exit /b 0
)

echo Killing any existing Chrome processes...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Starting Chrome with --remote-debugging-port=9222 ...

if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    start "" "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    goto wait
)
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" (
    start "" "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    goto wait
)
if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    goto wait
)

echo ERROR: Chrome not found. Edit start_chrome.bat with the correct path.
pause
exit /b 1

:wait
echo Waiting for Chrome to start...
timeout /t 4 /nobreak >nul

netstat -an | find "9222" | find "LISTENING" >nul 2>&1
if %errorlevel% == 0 (
    echo.
    echo SUCCESS - Port 9222 is open.
    echo.
    echo Now:
    echo   1. Log into stargate-game.cz
    echo   2. Navigate to the sector map
    echo   3. Run start.bat
) else (
    echo.
    echo FAILED - Port 9222 still not open.
    echo Chrome path might be wrong. Check Task Manager to find chrome.exe location.
)
echo.
pause
