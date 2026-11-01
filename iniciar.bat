@echo off
title Auto Clicker de Barra
cd /d "%~dp0"
echo Instalando dependencias...
py -m pip install -r requirements.txt
echo.
echo Abrindo o app...
py autoclick_app.py
pause
