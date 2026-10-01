@echo off
title Instalar ESTUDIO RICK DIGITAL como Programa
echo ============================================
echo  ESTUDIO RICK DIGITAL - Instalar como PROGRAMA
echo ============================================
echo.
set APPDIR=%~dp0
set APPDIR=%APPDIR:~0,-1%
set ICONO=%APPDIR%\icon.ico
set ALVO_VBS=%APPDIR%\Abrir-Programa.vbs
set ALVO_BAT=%APPDIR%\Abrir-App.bat

rem Descobre area de trabalho
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set DESKTOP=%%b
if not defined DESKTOP set DESKTOP=%USERPROFILE%\Desktop

echo Pasta do app: %APPDIR%
echo Area de trabalho: %DESKTOP%
echo.

rem Cria atalho .lnk via PowerShell apontando p/ VBS (sem janela preta) com icone RD
powershell -NoProfile -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%DESKTOP%\ESTUDIO RICK DIGITAL.lnk'); $s.TargetPath='wscript.exe'; $s.Arguments='\"%ALVO_VBS%\"'; $s.WorkingDirectory='%APPDIR%'; $s.IconLocation='%ICONO%'; $s.Description='ESTUDIO RICK DIGITAL - CRM + Leads + Banners'; $s.Save(); Write-Host 'Atalho criado:' $s.FullName"

echo.
echo ============================================
echo  PRONTO! Olhe sua Area de Trabalho:
echo  [ESTUDIO RICK DIGITAL] com icone RD
echo.
echo  Ele abre como PROGRAMA (janela propria),
echo  nao como aba de navegador.
echo.
echo  Dica: clique direito no atalho ^> Fixar na
echo  barra de tarefas / Fixar no Menu Iniciar.
echo ============================================
pause
