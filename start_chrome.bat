@echo off
title Launch Chrome with Debug Port
echo Starting Chrome with remote debugging on port 9222...
echo.
echo After Chrome opens:
echo   1. Log into stargate-game.cz
echo   2. Navigate to the sector map
echo   3. Run start.bat to start the bot
echo.

REM Try common Chrome install locations
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    start "" "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    goto done
)
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" (
    start "" "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    goto done
)
if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
    goto done
)

echo ERROR: Chrome not found in default locations.
echo Edit this file and set the correct path to chrome.exe
pause
exit /b 1

:done
echo Chrome started. You can close this window.
timeout /t 3
