@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   ICS Signage - Εγκατάσταση στο C:\ICS-Signage
echo ================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo Δεν βρέθηκε Python. Γίνεται εγκατάσταση, περιμένετε...
  winget install -e --id Python.Python.3.12 --scope machine --accept-package-agreements --accept-source-agreements
  set "PATH=%PATH%;C:\Program Files\Python312;%LOCALAPPDATA%\Programs\Python\Python312"
)
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo Η Python δεν εγκαταστάθηκε αυτόματα.
  echo Κατεβάστε την από https://www.python.org ^(τσεκάρετε "Add Python to PATH"^) και ξανατρέξτε αυτό το αρχείο.
  pause
  exit /b 1
)
python install.py
echo.
pause
