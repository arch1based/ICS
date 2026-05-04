@echo off
title Εγκατάσταση Αυτόματης Εκκίνησης
echo Προσθήκη στα Windows Startup...

REM Δημιουργία shortcut στο φάκελο Startup των Windows
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SCRIPT_DIR=%~dp0

REM Αφαιρούμε το trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\mklink.vbs"
echo sLinkFile = "%STARTUP%\CP737_AutoConverter.lnk" >> "%TEMP%\mklink.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\mklink.vbs"
echo oLink.TargetPath = "%SCRIPT_DIR%\start_watcher.bat" >> "%TEMP%\mklink.vbs"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%TEMP%\mklink.vbs"
echo oLink.Description = "CP737 Auto Converter" >> "%TEMP%\mklink.vbs"
echo oLink.Save >> "%TEMP%\mklink.vbs"

cscript //nologo "%TEMP%\mklink.vbs"
del "%TEMP%\mklink.vbs"

echo.
echo ΕΓΙΝΕ! Το πρόγραμμα θα εκκινεί αυτόματα κάθε φορά που ανοίγει ο υπολογιστής.
echo Shortcut: %STARTUP%\CP737_AutoConverter.lnk
echo.
pause
