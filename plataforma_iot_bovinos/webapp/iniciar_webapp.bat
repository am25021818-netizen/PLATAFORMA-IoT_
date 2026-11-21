@echo off
chcp 65001 >nul
title Plataforma IoT Bovinos - Valle del Mezquital (Flask WebApp)
cd /d "%~dp0"
echo ========================================================
echo   Iniciando Plataforma Web IoT Bovinos
echo   Valle del Mezquital, Hidalgo
echo   Servidor Web en: http://localhost:5000
echo ========================================================
python app.py
pause
