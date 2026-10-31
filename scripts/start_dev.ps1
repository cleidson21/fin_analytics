#Requires -Version 5.1
<#
.SYNOPSIS
  Local Windows development launcher (backend + frontend).

.DESCRIPTION
  Backend uses the approved Python 3.14 runtime under %LOCALAPPDATA%, bound to
  127.0.0.1:8080 without --reload. The legacy .venv is never used automatically.
  Override the interpreter explicitly with the FINANALYTICS_PYTHON env var.
  If port 8080 already has a listener, the script aborts without touching it.
#>
$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendHost = '127.0.0.1'
$BackendPort = 8080

# --- Interpreter resolution (no silent fallback to .venv) ---
if ($env:FINANALYTICS_PYTHON) {
    $PythonExe = $env:FINANALYTICS_PYTHON
    Write-Host "Using interpreter override FINANALYTICS_PYTHON: $PythonExe"
} else {
    $PythonExe = Join-Path $env:LOCALAPPDATA 'FinAnalytics\runtimes\sec-dep-c-py314-0803511\Scripts\python.exe'
}

if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    [Console]::Error.WriteLine("Python interpreter not found: $PythonExe. Set FINANALYTICS_PYTHON to a valid python.exe (see README). No fallback to .venv is performed.")
    exit 1
}
try {
    $PythonVersion = & $PythonExe --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw "exit code $LASTEXITCODE" }
} catch {
    [Console]::Error.WriteLine("Python interpreter could not be executed: $PythonExe ($_)")
    exit 1
}

# --- Duplicate-process protection (read-only check) ---
$listeners = @(Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue)
if ($listeners.Count -gt 0) {
    Write-Host "Port $BackendPort is already in use. Not starting another backend." -ForegroundColor Yellow
    foreach ($l in $listeners) {
        $proc = Get-Process -Id $l.OwningProcess -ErrorAction SilentlyContinue
        $name = if ($proc) { $proc.ProcessName } else { 'unknown' }
        Write-Host ("  Listener: {0}:{1} PID={2} Process={3}" -f $l.LocalAddress, $l.LocalPort, $l.OwningProcess, $name)
    }
    Write-Host "The listener is not assumed to be FinAnalytics and was not modified. Stop it manually if appropriate."
    exit 1
}

Write-Host "Starting FIN Analytics Dev Environment..."
Write-Host "Interpreter: $PythonExe ($PythonVersion)"

# --- Backend ---
$backend = Start-Process -NoNewWindow -PassThru -WorkingDirectory $ProjectRoot -FilePath $PythonExe `
    -ArgumentList '-m', 'uvicorn', 'backend.main:app', '--host', $BackendHost, '--port', $BackendPort
$null = $backend.Handle   # cache handle so HasExited/ExitCode stay reliable (PS 5.1)
$backendStart = $backend.StartTime
Write-Host "Backend started: PID=$($backend.Id) at http://${BackendHost}:${BackendPort}"

# --- Frontend (Legacy Next.js); backend started here is stopped when it exits ---
try {
    Push-Location (Join-Path $ProjectRoot 'frontend')
    try {
        npm.cmd run dev -- --hostname 127.0.0.1
    } finally {
        Pop-Location
    }
} finally {
    # Cleanup is limited to the process tree created by this script: the PID is the
    # one returned by Start-Process, never a name- or port-derived PID.
    if ($backend.HasExited) {
        Write-Host "Backend process (PID=$($backend.Id)) already exited (exit code $($backend.ExitCode)). If the port is still busy, check it manually (see README)." -ForegroundColor Yellow
    } else {
        $current = Get-Process -Id $backend.Id -ErrorAction SilentlyContinue
        if (-not $current -or $current.StartTime -ne $backendStart) {
            [Console]::Error.WriteLine("PID $($backend.Id) no longer matches the backend started by this script; skipping cleanup.")
        } else {
            Write-Host "Stopping backend started by this script (PID=$($backend.Id), process tree)..."
            # /T also ends the child of the Windows venv python redirector.
            & taskkill.exe /PID $backend.Id /T /F | Out-Null
            if ($LASTEXITCODE -ne 0) {
                [Console]::Error.WriteLine("taskkill failed for PID $($backend.Id) (exit code $LASTEXITCODE). Verify and stop it manually (see README).")
            }
        }
    }
}
