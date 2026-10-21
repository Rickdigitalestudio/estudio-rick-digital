@echo off
title Atualizar ESTUDIO RICK DIGITAL
chcp 65001 >nul
rem ============================================================================
rem  Atualiza o CRM no PC: puxa a versao nova do GitHub, limpa o cache do
rem  service worker (a versao antiga do app) e reabre o programa.
rem
rem  Uso: clique 2x neste arquivo (ou fixe na area de trabalho).
rem ============================================================================

set APPDIR=%~dp0
set APPDIR=%APPDIR:~0,-1%
set PROFILE=%APPDIR%\.app-profile

echo ============================================
echo  ATUALIZAR ESTUDIO RICK DIGITAL
echo ============================================
echo.
echo Pasta: %APPDIR%
echo.

rem --- 1) fecha o app se estiver aberto ---
taskkill /IM chrome.exe /FI "WINDOWTITLE eq EstudioRickDigital" /F >nul 2>&1
taskkill /IM msedge.exe /FI "WINDOWTITLE eq EstudioRickDigital" /F >nul 2>&1
timeout /t 1 /nobreak >nul

rem --- 2) puxa a versao nova do GitHub ---
echo [1/3] Baizando a versao nova do GitHub...
cd /d "%APPDIR%"
git pull --rebase origin main
if errorlevel 1 (
  echo.
  echo [AVISO] Nao consegui baixar agora. Voce pode usar o app assim mesmo.
  echo         Tente de novo mais tarde ou rode:  git pull origin main
) else (
  echo       pronto.
)

rem --- 3) limpa o cache do service worker (app antigo) ---
echo.
echo [2/3] Limpando o cache do app antigo...
if exist "%PROFILE%\Default\Service Worker" (
  rmdir /S /Q "%PROFILE%\Default\Service Worker" >nul 2>&1
  echo       cache limpo.
) else (
  echo       nada a limpar.
)
if exist "%PROFILE%\Default\Cache" rmdir /S /Q "%PROFILE%\Default\Cache" >nul 2>&1
if exist "%PROFILE%\Default\Code Cache" rmdir /S /Q "%PROFILE%\Default\Code Cache" >nul 2>&1

echo.
echo [3/3] Abrindo o app atualizado...
echo.
timeout /t 1 /nobreak >nul
call "%APPDIR%\Abrir-App.bat"
exit /b
