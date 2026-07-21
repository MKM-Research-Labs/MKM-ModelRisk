@echo off
REM Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
REM
REM MKM-ModelRisk - Windows starter. DOUBLE-CLICK THIS FILE.
REM
REM Installs anything missing (Python 3.13, PostgreSQL 16) using Windows' built-in
REM winget, then sets up and launches the app. Safe to run again at any time - it
REM skips whatever is already done. Do NOT "Run as administrator".
setlocal
cd /d "%~dp0"

echo(
echo ============================================================
echo   MKM-ModelRisk - Windows setup
echo ============================================================
echo(

REM --- winget is how we install things. It ships with Windows 11. --------------
where winget >nul 2>&1
if errorlevel 1 (
  echo winget was not found. It is part of "App Installer" from the Microsoft Store.
  echo(
  echo   1. Open the Microsoft Store
  echo   2. Search for "App Installer"
  echo   3. Install or Update it
  echo   4. Then double-click this file again
  echo(
  goto :done
)

set "NEEDRESTART="

REM --- Python 3.13 -------------------------------------------------------------
set "PYOK="
py -3.13 -c "import sys" >nul 2>&1 && set "PYOK=1"
if not defined PYOK if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PYOK=1"
if not defined PYOK if exist "%ProgramFiles%\Python313\python.exe" set "PYOK=1"
if defined PYOK (
  echo [ok] Python 3.13 is installed.
) else (
  echo [..] Installing Python 3.13 ^(this can take a few minutes^)...
  winget install -e --id Python.Python.3.13 --scope user ^
    --accept-source-agreements --accept-package-agreements
  if errorlevel 1 (
    echo(
    echo Could not install Python automatically.
    echo Please install it from https://www.python.org/downloads/windows/
    echo and tick "Add python.exe to PATH" during setup, then run this file again.
    goto :done
  )
  set "NEEDRESTART=1"
)

REM --- PostgreSQL 16 -----------------------------------------------------------
set "PGOK="
if exist "%ProgramFiles%\PostgreSQL\16\bin\initdb.exe" set "PGOK=1"
if defined PGOK (
  echo [ok] PostgreSQL 16 is installed.
) else (
  echo [..] Installing PostgreSQL 16...
  echo      Windows may ask "Do you want to allow this app to make changes?" - click Yes.
  winget install -e --id PostgreSQL.PostgreSQL.16 ^
    --accept-source-agreements --accept-package-agreements
  if errorlevel 1 (
    echo(
    echo Could not install PostgreSQL automatically.
    echo Please install it from https://www.postgresql.org/download/windows/
    echo then run this file again.
    goto :done
  )
  set "NEEDRESTART=1"
)

REM Freshly installed programs are not visible to this window until it restarts.
if defined NEEDRESTART (
  echo(
  echo ============================================================
  echo   Installation finished.
  echo   Please DOUBLE-CLICK THIS FILE ONE MORE TIME to finish setup.
  echo ============================================================
  goto :done
)

echo(
echo [..] Setting up and starting MKM-ModelRisk...
echo      The first run takes a few minutes. Leave this window open.
echo(
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\start.ps1"

:done
echo(
echo Press any key to close this window.
pause >nul
endlocal
