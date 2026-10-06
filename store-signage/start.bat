@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM --- Ξεκινά τον server (κρυφά) ---
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw server.py
) else (
  start "" /min python server.py
)
timeout /t 2 /nobreak >nul
REM --- Πλήρης οθόνη (kiosk) σε Edge, αλλιώς Chrome ---
set URL=http://localhost:8765/
set FLAGS=--kiosk %URL% --edge-kiosk-type=fullscreen --autoplay-policy=no-user-gesture-required --no-first-run --disable-features=Translate --user-data-dir="%LOCALAPPDATA%\ICS-Signage"
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" %FLAGS%
) else if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" %FLAGS%
) else (
  start "" %URL%
)
