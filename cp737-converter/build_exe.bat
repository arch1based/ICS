@echo off
title Build CP737 Converter EXE
echo ============================================
echo  Build CP737_Converter.exe  -  ILS1100
echo ============================================
echo.

echo [1/3] Εγκατασταση εξαρτησεων...
pip install pyinstaller pillow --quiet
if errorlevel 1 (
    echo ΣΦΑΛΜΑ: Αποτυχια εγκαταστασης. Ελεγξτε ότι η Python ειναι εγκατεστημένη.
    pause & exit /b 1
)

echo [2/3] Δημιουργια εικονιδιου...
python generate_icon.py
if errorlevel 1 (
    echo ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το εικονιδιο δεν δημιουργηθηκε. Συνεχιζεται χωρις αυτο.
    set ICON_FLAG=
) else (
    set ICON_FLAG=--icon icon.ico
)

echo [3/3] Δημιουργια EXE...
pyinstaller ^
    --onefile ^
    --noconsole ^
    --name "CP737_Converter" ^
    %ICON_FLAG% ^
    cp737_watcher_gui.py

echo.
if exist dist\CP737_Converter.exe (
    echo  ΕΠΙΤΥΧΙΑ!
    echo  Το EXE βρισκεται στο: %CD%\dist\CP737_Converter.exe
    echo  Δωστε αυτο το αρχειο στον πελατη.
    explorer dist
) else (
    echo  ΣΦΑΛΜΑ κατα τη δημιουργια του EXE.
)
pause
