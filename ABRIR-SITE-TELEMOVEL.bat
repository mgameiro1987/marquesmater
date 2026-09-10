@echo off
cd /d "%~dp0"
echo.
echo =====================================================
echo       MARQUESMATER - SERVIDOR PARA TELEMOVEL
echo =====================================================
echo.
echo PC e telemovel devem estar no MESMO Wi-Fi.
echo.
ipconfig | findstr /R /C:"IPv4"
echo.
echo A iniciar o servidor na porta 8000...
echo No telemovel use: http://IP-DO-PC:8000
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0SERVIDOR-TELEMOVEL.ps1"
pause
