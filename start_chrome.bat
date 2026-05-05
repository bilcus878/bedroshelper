@echo off
title Launch Chrome with Debug Port
echo ============================================================
echo  Step 1 of 2: Launch Chrome with remote debugging
echo ============================================================
echo.

REM Already running with debug port? Done.
powershell -NoProfile -Command "try { $t = New-Object Net.Sockets.TcpClient('127.0.0.1',9222); $t.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% == 0 (
    echo Port 9222 already open - Chrome debug is running.
    echo You can run start.bat now.
    pause
    exit /b 0
)

REM Kill Chrome AND all child processes, then wait for them to fully die
echo Killing Chrome processes...
taskkill /F /IM chrome.exe /T >nul 2>&1
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 3 /nobreak >nul

REM Confirm Chrome is dead
tasklist | find /I "chrome.exe" >nul 2>&1
if %errorlevel% == 0 (
    echo Chrome still running, killing again...
    taskkill /F /IM chrome.exe /T >nul 2>&1
    timeout /t 3 /nobreak >nul
)

echo Starting Chrome with --remote-debugging-port=9222 ...

if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set CHROME="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    goto launch
)
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" (
    set CHROME="%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
    goto launch
)
if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" (
    set CHROME="%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
    goto launch
)

echo ERROR: Chrome not found in default locations.
echo Open Task Manager, right-click chrome.exe, Open file location
echo Then edit start_chrome.bat and hardcode the path.
pause
exit /b 1

:launch
start "" %CHROME% --remote-debugging-port=9222 --user-data-dir="%TEMP%\bedros_chrome"

REM Poll for up to 15 seconds
echo Waiting for port 9222 to open...
set /a tries=0
:poll
set /a tries+=1
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { $t = New-Object Net.Sockets.TcpClient('127.0.0.1',9222); $t.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% == 0 goto success
if %tries% lss 7 goto poll

echo.
echo FAILED after 15 seconds. Port 9222 did not open.
echo Possible causes:
echo   - Another app is using port 9222
echo   - Chrome is launching but ignoring the flag (profile locked?)
echo Try: close Chrome completely, wait 10 seconds, run this again.
echo.
pause
exit /b 1

:success
echo.
echo SUCCESS - Port 9222 is open!
echo.
echo Now:
echo   1. Log into stargate-game.cz in the Chrome window
echo   2. Navigate to the sector map
echo   3. Run start.bat
echo.
pause
