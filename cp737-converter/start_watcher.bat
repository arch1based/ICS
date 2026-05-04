@echo off
title CP737 Auto Converter - ICS
echo ============================================
echo  CP737 Auto Converter - ERP Greek Encoding
echo ============================================
echo.

REM Αλλάξτε αυτή τη γραμμή στον σωστό φάκελο εξαγωγής του ERP σας:
set WATCH_FOLDER=C:\ERP_Export

python "%~dp0cp737_watcher.py" "%WATCH_FOLDER%"

if errorlevel 1 (
    echo.
    echo ΣΦΑΛΜΑ: Βεβαιωθείτε ότι η Python είναι εγκατεστημένη.
    echo Κατεβάστε την από: https://www.python.org
    pause
)
