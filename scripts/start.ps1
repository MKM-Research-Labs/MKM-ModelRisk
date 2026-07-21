# Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
#
# One-command setup for MKM-ModelRisk on Windows 10/11. Checks the toolchain,
# creates the virtualenv, installs dependencies, brings up a local PostgreSQL
# cluster in .\.pgdata, then launches the app. Safe to re-run.
#
#   powershell -ExecutionPolicy Bypass -File scripts\start.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -NoRun
#   powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -Seed
#   powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -StopDb
#
# Do NOT run this elevated — initdb refuses to run as Administrator, and the
# cluster lives inside the repo so no admin rights are needed.
#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$NoRun,
    [switch]$Seed,
    [switch]$StopDb,
    [string]$Identity
)

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

function Step($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Fail($m) { Write-Host "ERROR: $m" -ForegroundColor Red; exit 1 }

# Settings mirror config/database.py and scripts/pg.sh.
$DbHost  = if ($env:MKM_DB_HOST) { $env:MKM_DB_HOST } else { '127.0.0.1' }
$Port    = if ($env:MKM_DB_PORT) { $env:MKM_DB_PORT } else { '5433' }
$Owner   = if ($env:MKM_DB_OWNER_USER) { $env:MKM_DB_OWNER_USER } else { 'mkm_owner' }
$OwnerPw = if ($env:MKM_DB_OWNER_PASSWORD) { $env:MKM_DB_OWNER_PASSWORD } else { 'mkm_dev_pw' }
$DbName  = if ($env:MKM_DB_NAME) { $env:MKM_DB_NAME } else { 'mkm_modelrisk' }
$Data    = if ($env:MKM_PG_DATA_DIR) { $env:MKM_PG_DATA_DIR } else { Join-Path $PWD '.pgdata' }
$Locale  = if ($env:MKM_PG_LOCALE) { $env:MKM_PG_LOCALE } else { 'C' }

# --- Locate PostgreSQL 16 --------------------------------------------------
$PgBin = $env:MKM_PG_BIN
if (-not $PgBin) {
    foreach ($c in @("$env:ProgramFiles\PostgreSQL\16\bin",
                     "${env:ProgramFiles(x86)}\PostgreSQL\16\bin")) {
        if (Test-Path (Join-Path $c 'initdb.exe')) { $PgBin = $c; break }
    }
}
if (-not $PgBin) {
    $c = Get-Command initdb.exe -ErrorAction SilentlyContinue
    if ($c) { $PgBin = Split-Path $c.Source }
}
if (-not $PgBin) {
    Fail @"
PostgreSQL 16 not found. Install it, then re-run:
  winget install -e --id PostgreSQL.PostgreSQL.16
or download the installer from https://www.postgresql.org/download/windows/
If it is installed somewhere unusual, set MKM_PG_BIN to the folder holding initdb.exe:
  `$env:MKM_PG_BIN = 'D:\PostgreSQL\16\bin'
"@
}
$InitDb   = Join-Path $PgBin 'initdb.exe'
$PgCtl    = Join-Path $PgBin 'pg_ctl.exe'
$CreateDb = Join-Path $PgBin 'createdb.exe'
$PgReady  = Join-Path $PgBin 'pg_isready.exe'

function Test-Db { & $PgReady -h $DbHost -p $Port 2>&1 | Out-Null; return ($LASTEXITCODE -eq 0) }

if ($StopDb) {
    Step "Stopping the cluster"
    & $PgCtl -D $Data stop
    exit 0
}

# --- 1. Python 3.13+ -------------------------------------------------------
Step "Checking Python"
$PyExe = $null; $PyArgs = @()
foreach ($cand in @(@('py', '-3.13'), @('py', '-3'), @('python'), @('python3'))) {
    $exe = $cand[0]
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    $pre = if ($cand.Count -gt 1) { @($cand[1]) } else { @() }
    & $exe @pre -c "import sys; raise SystemExit(0 if sys.version_info>=(3,13) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $PyExe = $exe; $PyArgs = $pre; break }
}
if (-not $PyExe) {
    Fail @"
Python 3.13+ not found. Install it, then re-run:
  winget install -e --id Python.Python.3.13
(or download from https://www.python.org/downloads/windows/ and tick
 "Add python.exe to PATH" during installation)
"@
}
& $PyExe @PyArgs --version

# --- 2. Virtualenv + dependencies -----------------------------------------
Step "Setting up the virtualenv (.venv)"
$VenvPy = Join-Path $PWD '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) { & $PyExe @PyArgs -m venv .venv }
if (-not (Test-Path $VenvPy)) { Fail "virtualenv creation failed (expected $VenvPy)" }
& $VenvPy -m pip install --quiet --upgrade pip
& $VenvPy -m pip install --quiet -e ".[dev]"
if ($LASTEXITCODE -ne 0) { Fail "dependency installation failed" }
Write-Host "dependencies installed"

# --- 3. PostgreSQL cluster -------------------------------------------------
Step "Starting the PostgreSQL cluster"
if (Test-Db) {
    Write-Host "a cluster is already serving port $Port - leaving it alone"
} elseif (Test-Path $Data) {
    & $PgCtl -D $Data -o "-p $Port" -l (Join-Path $Data 'server.log') start
    Start-Sleep -Seconds 2
} else {
    $PwFile = [System.IO.Path]::GetTempFileName()
    try {
        # No BOM and no trailing newline, or the password will not match.
        [System.IO.File]::WriteAllText($PwFile, $OwnerPw, (New-Object System.Text.UTF8Encoding($false)))
        & $InitDb -D $Data -U $Owner -A scram-sha-256 --pwfile=$PwFile --locale=$Locale -E UTF-8
        if ($LASTEXITCODE -ne 0) { Fail "initdb failed (are you running as Administrator? don't)" }
    } finally { Remove-Item $PwFile -Force -ErrorAction SilentlyContinue }
    & $PgCtl -D $Data -o "-p $Port" -l (Join-Path $Data 'server.log') start
    Start-Sleep -Seconds 2
    $env:PGPASSWORD = $OwnerPw
    & $CreateDb -h $DbHost -p $Port -U $Owner $DbName
    Write-Host "Cluster ready on port $Port; database '$DbName' created."
}
if (-not (Test-Db)) { Fail "the database is not accepting connections on port $Port" }
Write-Host "cluster is accepting connections on port $Port"

# --- 4. Identity used for the audit trail ---------------------------------
if ($Identity) { $env:MKM_IDENTITY_DEV_FALLBACK = $Identity }
if (-not $env:MKM_IDENTITY_DEV_FALLBACK) {
    $id = Read-Host "`nIdentity your changes are attributed to [dev@localhost]"
    $env:MKM_IDENTITY_DEV_FALLBACK = if ($id) { $id } else { 'dev@localhost' }
}

if ($Seed) { Step "Seeding example models"; & $VenvPy scripts\seed_demo.py }

# --- 5. Run ----------------------------------------------------------------
$WebHost = if ($env:MKM_WEB_HOST) { $env:MKM_WEB_HOST } else { '127.0.0.1' }
$WebPort = if ($env:MKM_WEB_PORT) { $env:MKM_WEB_PORT } else { '5015' }
if (-not $NoRun) {
    Step "Starting MKM-ModelRisk on http://${WebHost}:${WebPort}"
    & $VenvPy app.py
} else {
    Step "Setup complete"
    Write-Host @"
To start the app:
  .venv\Scripts\python.exe app.py
Then open http://${WebHost}:${WebPort}
"@
}
