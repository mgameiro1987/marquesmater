@echo off
cd /d "%~dp0"
where git >nul 2>nul
if errorlevel 1 (echo Git nao esta instalado neste PC.&echo Instale Git ou use GitHub Desktop.&pause&exit /b 1)
git pull --ff-only origin main
if errorlevel 1 (echo Nao foi possivel atualizar. Verifique a ligacao ao GitHub.&pause&exit /b 1)
echo.
echo SITE ATUALIZADO.
pause
