@echo off
chcp 65001 > nul
title Plataforma IoT Bovinos - ITESHU
echo =====================================================================
echo   INICIANDO PLATAFORMA IoT - MONITOREO GPS DE BOVINOS (ITESHU)
echo   Valle del Mezquital, Estado de Hidalgo
echo =====================================================================
echo.

cd /d "%~dp0plataforma"

echo [1/2] Verificando dependencias necesarias...
python -m pip install -q -r requirements.txt

echo.
echo [2/2] Lanzando Dashboard Web en puerto local 8501...
echo.
echo Abre tu navegador en: http://localhost:8501
echo Presiona Ctrl+C en esta ventana para detener el servidor.
echo =====================================================================
echo.

python -m streamlit run src/dashboard.py --server.port 8501 --server.address 0.0.0.0

pause
