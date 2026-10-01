@echo off
title ESTUDIO RICK DIGITAL
rem === ESTUDIO RICK DIGITAL como PROGRAMA (janela propria, sem barra de navegador) ===
set APPDIR=%~dp0
set PAGE=%APPDIR%index.html
set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"
set EDGE="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
set EDGE2="C:\Program Files\Microsoft\Edge\Application\msedge.exe"

if exist %CHROME% (
  start "" %CHROME% --app="file:///%PAGE:\=/%" --user-data-dir="%APPDIR%.app-profile" --class="EstudioRickDigital"
  exit /b
)
if exist %EDGE% (
  start "" %EDGE% --app="file:///%PAGE:\=/%" --user-data-dir="%APPDIR%.app-profile"
  exit /b
)
if exist %EDGE2% (
  start "" %EDGE2% --app="file:///%PAGE:\=/%" --user-data-dir="%APPDIR%.app-profile"
  exit /b
)
rem fallback: abre normal
start "" "%PAGE%"
