@echo off
title ESTUDIO RICK DIGITAL - Servidor p/ celular
echo ============================================
echo  ESTUDIO RICK DIGITAL - link p/ celular
echo ============================================
echo.
echo  Deixe esta janela ABERTA.
echo  No celular (mesmo Wi-Fi) abra:
echo.
echo  http://192.168.1.7:8080/estudio-rick-digital/index.html
echo.
cd /d "C:\Users\Henrique Luiz\Documents\Default Project"
python -m http.server 8080
pause
