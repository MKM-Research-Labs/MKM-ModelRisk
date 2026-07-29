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
# Do NOT run this elevated - initdb refuses to run as Administrator, and the
# cluster lives inside the repo so no admin rights are needed.
#
# Kept deliberately ASCII-only: Windows PowerShell 5.1 reads a UTF-8 file with no
# BOM as ANSI, which mangles non-ASCII characters.
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
$DbHost  = if ($env:DB_HOST) { $env:DB_HOST } else { '127.0.0.1' }
$Port    = if ($env:DB_PORT) { $env:DB_PORT } else { '5433' }
$Owner   = if ($env:DB_OWNER_USER) { $env:DB_OWNER_USER } else { 'mkm_owner' }
$OwnerPw = if ($env:DB_OWNER_PASSWORD) { $env:DB_OWNER_PASSWORD } else { 'mkm_dev_pw' }
$DbName  = if ($env:DB_NAME) { $env:DB_NAME } else { 'mkm_modelrisk' }
$Data    = if ($env:PG_DATA_DIR) { $env:PG_DATA_DIR } else { Join-Path $PWD '.pgdata' }
$Locale  = if ($env:PG_LOCALE) { $env:PG_LOCALE } else { 'C' }

# --- Locate PostgreSQL 16 --------------------------------------------------
$PgBin = $env:PG_BIN
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
If it is installed somewhere unusual, set PG_BIN to the folder holding initdb.exe:
  `$env:PG_BIN = 'D:\PostgreSQL\16\bin'
"@
}
$InitDb   = Join-Path $PgBin 'initdb.exe'
$PgCtl    = Join-Path $PgBin 'pg_ctl.exe'
$CreateDb = Join-Path $PgBin 'createdb.exe'
$PgReady  = Join-Path $PgBin 'pg_isready.exe'

# Run a native command quietly and return its exit code. Windows PowerShell 5.1
# turns native stderr into a *terminating* error when $ErrorActionPreference is
# 'Stop', so probes that are expected to fail (pg_isready with no server yet,
# a Python that is too old) must run with it relaxed or they abort the script.
function Invoke-Quiet {
    param([string]$Exe, [string[]]$Arguments = @())
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Exe @Arguments 2>&1 | Out-Null
        return $LASTEXITCODE
    } finally { $ErrorActionPreference = $prev }
}

function Test-Db { return (Invoke-Quiet $PgReady @('-h', $DbHost, '-p', $Port)) -eq 0 }

# Run a native command with its output shown, failing only on a non-zero exit
# code. Same reasoning as above: pip and initdb write progress and warnings to
# stderr, which must not be mistaken for a fatal error.
function Invoke-Native {
    param([string]$Exe, [string[]]$Arguments = @(), [string]$What = 'command')
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $Exe @Arguments } finally { $ErrorActionPreference = $prev }
    if ($LASTEXITCODE -ne 0) { Fail "$What failed (exit code $LASTEXITCODE)" }
}

if ($StopDb) {
    Step "Stopping the cluster"
    Invoke-Native $PgCtl @('-D', $Data, 'stop') 'stopping the cluster'
    exit 0
}

# --- 1. Python 3.13+ -------------------------------------------------------
Step "Checking Python"
$PyExe = $null; $PyArgs = @()
$probe = 'import sys; raise SystemExit(0 if sys.version_info>=(3,13) else 1)'
foreach ($cand in @(@('py', '-3.13'), @('py', '-3'), @('python'), @('python3'))) {
    $exe = $cand[0]
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
    $pre = if ($cand.Count -gt 1) { @($cand[1]) } else { @() }
    if ((Invoke-Quiet $exe ($pre + @('-c', $probe))) -eq 0) { $PyExe = $exe; $PyArgs = $pre; break }
}
if (-not $PyExe) {
    # A Python installed moments ago is not on PATH until the shell restarts, so
    # look in the standard install locations before giving up.
    foreach ($p in @("$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
                     "$env:ProgramFiles\Python313\python.exe")) {
        if ((Test-Path $p) -and ((Invoke-Quiet $p @('-c', $probe)) -eq 0)) {
            $PyExe = $p; $PyArgs = @(); break
        }
    }
}
if (-not $PyExe) {
    Fail @"
Python 3.13+ not found. Install it, then re-run:
  winget install -e --id Python.Python.3.13
(or download from https://www.python.org/downloads/windows/ and tick
 "Add python.exe to PATH" during installation)
"@
}
Invoke-Native $PyExe ($PyArgs + @('--version')) 'checking the Python version'

# --- 2. Virtualenv + dependencies -----------------------------------------
Step "Setting up the virtualenv (.venv)"
$VenvPy = Join-Path $PWD '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) {
    Invoke-Native $PyExe ($PyArgs + @('-m', 'venv', '.venv')) 'creating the virtualenv'
}
if (-not (Test-Path $VenvPy)) { Fail "virtualenv creation failed (expected $VenvPy)" }
Invoke-Native $VenvPy @('-m', 'pip', 'install', '--quiet', '--upgrade', 'pip') 'upgrading pip'
Invoke-Native $VenvPy @('-m', 'pip', 'install', '--quiet', '-e', '.[dev]') 'installing dependencies'
Write-Host "dependencies installed"

# --- 3. PostgreSQL cluster -------------------------------------------------
Step "Starting the PostgreSQL cluster"
if (Test-Db) {
    Write-Host "a cluster is already serving port $Port - leaving it alone"
} elseif (Test-Path $Data) {
    Invoke-Native $PgCtl @('-D', $Data, '-o', "-p $Port", '-l', (Join-Path $Data 'server.log'), 'start') 'starting the cluster'
    Start-Sleep -Seconds 2
} else {
    $PwFile = [System.IO.Path]::GetTempFileName()
    try {
        # No BOM and no trailing newline, or the password will not match.
        [System.IO.File]::WriteAllText($PwFile, $OwnerPw, (New-Object System.Text.UTF8Encoding($false)))
        Invoke-Native $InitDb @('-D', $Data, '-U', $Owner, '-A', 'scram-sha-256',
                                "--pwfile=$PwFile", "--locale=$Locale", '-E', 'UTF-8') `
                      'initdb (if it says "cannot be run as Administrator", use a normal PowerShell window)'
    } finally { Remove-Item $PwFile -Force -ErrorAction SilentlyContinue }
    Invoke-Native $PgCtl @('-D', $Data, '-o', "-p $Port", '-l', (Join-Path $Data 'server.log'), 'start') 'starting the cluster'
    Start-Sleep -Seconds 2
    $env:PGPASSWORD = $OwnerPw
    Invoke-Native $CreateDb @('-h', $DbHost, '-p', $Port, '-U', $Owner, $DbName) "creating database '$DbName'"
    Write-Host "Cluster ready on port $Port; database '$DbName' created."
}
if (-not (Test-Db)) { Fail "the database is not accepting connections on port $Port" }
Write-Host "cluster is accepting connections on port $Port"

# --- 4. Identity used for the audit trail ---------------------------------
if ($Identity) { $env:IDENTITY_DEV_FALLBACK = $Identity }
if (-not $env:IDENTITY_DEV_FALLBACK) {
    $id = Read-Host "`nIdentity your changes are attributed to [david.kelly@mkmresearchlabs.com]"
    $env:IDENTITY_DEV_FALLBACK = if ($id) { $id } else { 'david.kelly@mkmresearchlabs.com' }
}

if ($Seed) {
    Step "Seeding example models"
    Invoke-Native $VenvPy @('scripts\seed_demo.py') 'seeding example models'
}

# --- 5. Run ----------------------------------------------------------------
$WebHost = if ($env:WEB_HOST) { $env:WEB_HOST } else { '127.0.0.1' }
$WebPort = if ($env:WEB_PORT) { $env:WEB_PORT } else { '5015' }
if (-not $NoRun) {
    Step "Starting MKM-ModelRisk on http://${WebHost}:${WebPort}"
    Write-Host "Press Ctrl-C to stop."
    # Flask logs to stderr, and Ctrl-C exits non-zero, so run this relaxed and
    # without an exit-code check - neither is an error.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $VenvPy model.py } finally { $ErrorActionPreference = $prev }
} else {
    Step "Setup complete"
    Write-Host @"
To start the app:
  .venv\Scripts\python.exe model.py
Then open http://${WebHost}:${WebPort}
"@
}
