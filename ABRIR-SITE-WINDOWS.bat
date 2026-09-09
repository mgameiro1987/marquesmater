@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ========================================
echo       MARQUESMATER - NOVO SITE
echo ========================================

echo A verificar Python...
where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON=python"
    ) else (
        echo.
        echo ERRO: Python 3 nao esta instalado.
        echo Instale Python 3 e execute este ficheiro novamente.
        pause
        exit /b 1
    )
)

rem Se ja houver um servidor ativo, nao criar outro.
powershell -NoProfile -Command "try { (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health -TimeoutSec 1).StatusCode } catch { exit 1 }" >nul 2>nul
if %errorlevel%==0 goto OPEN

echo A iniciar servidor...
start "MarquesMater - Servidor" /min cmd /c "cd /d ""%~dp0"" && %PYTHON% server.py"

set /a tries=0
:WAIT
set /a tries+=1
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health -TimeoutSec 1; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>nul
if %errorlevel%==0 goto OPEN
if !tries! GEQ 15 (
    echo.
    echo ERRO: o servidor nao iniciou corretamente.
    echo Veja a janela 'MarquesMater - Servidor' para a mensagem de erro.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto WAIT

:OPEN
echo.
echo Para abrir no telemovel ligado a mesma rede Wi-Fi, use o IP deste PC seguido de :8000
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4.*:"') do echo    http://%%A:8000/admin.html
start "MarquesMater" http://127.0.0.1:8000/
exit /b 0
