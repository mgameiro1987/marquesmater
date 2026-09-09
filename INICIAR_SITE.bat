@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo      MARQUESMATER V25 - TESTE LOCAL
echo ========================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON=python"
    ) else (
        echo ERRO: Python 3 nao esta instalado.
        echo Instale Python 3 e volte a executar este ficheiro.
        pause
        exit /b 1
    )
)

powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health -TimeoutSec 1; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>nul
if %errorlevel%==0 goto OPEN

echo A iniciar o servidor local...
start "MarquesMater V25 - Servidor" /min cmd /c "cd /d ""%~dp0"" && %PYTHON% server.py"

set /a tries=0
:WAIT
set /a tries+=1
powershell -NoProfile -Command "try { $r=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/health -TimeoutSec 1; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>nul
if %errorlevel%==0 goto OPEN
if !tries! GEQ 20 (
    echo.
    echo ERRO: o servidor nao iniciou.
    echo Verifique se o Python 3 esta instalado.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto WAIT

:OPEN
echo Servidor ativo.
echo.
echo Site:       http://127.0.0.1:8000/
echo Backoffice: http://127.0.0.1:8000/admin.html
echo.
start "" http://127.0.0.1:8000/
exit /b 0
