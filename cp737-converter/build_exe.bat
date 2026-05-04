@echo off
title Build CP737 Converter EXE
echo ============================================
echo  Build CP737 Converter - Standalone EXE
echo ============================================
echo.

REM Εγκατάσταση PyInstaller αν δεν υπάρχει
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Εγκατάσταση PyInstaller...
    pip install pyinstaller
)

echo.
echo Δημιουργία EXE...
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "CP737_Converter" ^
    --icon NONE ^
    cp737_watcher_gui.py

echo.
if exist dist\CP737_Converter.exe (
    echo  ΕΠΙΤΥΧΙΑ! Το EXE βρίσκεται στο φάκελο: dist\CP737_Converter.exe
    echo  Δώστε αυτό το αρχείο στον πελάτη.
    explorer dist
) else (
    echo  ΣΦΑΛΜΑ κατά τη δημιουργία.
)
pause
