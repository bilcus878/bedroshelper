@echo off
title Launch Chrome with Debug Port
echo ============================================================
echo  Step 1 of 2: Launch Chrome with remote debugging
echo ============================================================
echo.
echo IMPORTANT: Close ALL Chrome windows before continuing.
echo If Chrome is already open it will ignore the debug flag.
echo.
pause

echo Checking if port 9222 is already in use...
netstat -an | find "9222" | find "LISTENING" >nul 2>&1
if %errorlevel% == 0 (
    echo Port 9222 is already open - Chrome debug is already running!
    echo You can go ahead and run start.bat
    pause
    exit /b 0
)

echo Starting Chrome with --remote-debugging-port=9222 ...
echo.

REM Try common Chrome install locations
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

echo ERROR: Chrome not found in default locations.
echo Edit start_chrome.bat and set the correct path to chrome.exe
pause
exit /b 1

:wait
echo Chrome is starting...
timeout /t 3 /nobreak >nul

REM Verify the port opened
netstat -an | find "9222" | find "LISTENING" >nul 2>&1
if %errorlevel% == 0 (
    echo.
    echo SUCCESS - Chrome debug port 9222 is open.
    echo.
    echo Now:
    echo   1. Log into stargate-game.cz in that Chrome window
    echo   2. Navigate to the sector map
    echo   3. Run start.bat to start the bot
) else (
    echo.
    echo WARNING: Port 9222 did not open. Chrome may have attached to
    echo an existing session without the debug flag.
    echo Close ALL Chrome windows and try again.
)
echo.
pause
