@echo off
title TEST NOVA - Online Test Platform

cd /d "%~dp0"

echo.
echo ========================================
echo              TEST NOVA
echo       Online Test Platform
echo ========================================
echo.
echo Starting Test Nova...
echo.

call venv\Scripts\activate.bat

start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000"

python app.py

echo.
echo ========================================
echo Test Nova has stopped.
echo ========================================
pause