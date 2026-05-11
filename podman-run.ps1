# ─── Kharōn All-in-One — Podman launcher (Windows PowerShell) ────────────────
$ErrorActionPreference = "Stop"

# Check for podman executable
$PODMAN_EXE = "podman"
if (!(Get-Command "podman" -ErrorAction SilentlyContinue)) {
    $commonPaths = @(
        "C:\Program Files\RedHat\Podman\podman.exe",
        "C:\Program Files\Podman\podman.exe"
    )
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $PODMAN_EXE = $path
            break
        }
    }
}

if ($PODMAN_EXE -eq "podman" -and !(Get-Command "podman" -ErrorAction SilentlyContinue)) {
    Write-Host "Podman executable not found. Please ensure Podman is installed." -ForegroundColor Red
    return
}

# Check if podman machine is running
$oldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"

$machineStatus = & $PODMAN_EXE machine inspect --format "{{.State}}" 2>$null
$inspectExitCode = $LASTEXITCODE

if ($inspectExitCode -ne 0) {
    $ErrorActionPreference = $oldErrorActionPreference
    Write-Host "Podman machine is not initialized. Please run: & '$PODMAN_EXE' machine init" -ForegroundColor Red
    return
}

if ($machineStatus -ne "running") {
    Write-Host "Podman machine is not running. Starting it..." -ForegroundColor Yellow
    & $PODMAN_EXE machine start 2>$null
    $startExitCode = $LASTEXITCODE
    if ($startExitCode -ne 0) {
        $ErrorActionPreference = $oldErrorActionPreference
        Write-Host "Failed to start Podman machine. Please start it manually." -ForegroundColor Red
        return
    }
}
$ErrorActionPreference = $oldErrorActionPreference

$IMAGE = if ($env:KHARON_IMAGE) { $env:KHARON_IMAGE } else { "ghcr.io/arkh-ur/kharon:latest" }
$AUTO_UPDATE = if ($env:AUTO_UPDATE) { $env:AUTO_UPDATE } else { "false" }
$AIRFLOW_PORT = if ($env:KHARON_AIRFLOW_PORT) { $env:KHARON_AIRFLOW_PORT } else { "8080" }
$KHARON_PORT = if ($env:KHARON_PORT) { $env:KHARON_PORT } else { "8501" }
$AIRFLOW_PASSWORD = if ($env:KHARON_AIRFLOW_PASSWORD) { $env:KHARON_AIRFLOW_PASSWORD } else { "" }

# Build image if it doesn't exist yet
$imageExists = & $PODMAN_EXE image exists $IMAGE 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Building $IMAGE (first run, this takes ~3 min)..." -ForegroundColor Cyan
    & $PODMAN_EXE build -t $IMAGE $PSScriptRoot
}

Write-Host "Starting Kharōn on ports $AIRFLOW_PORT and $KHARON_PORT..." -ForegroundColor Green

& $PODMAN_EXE run -it --rm `
    --name kharon `
    -p "${AIRFLOW_PORT}:8080" `
    -p "${KHARON_PORT}:8501" `
    -v "${PSScriptRoot}/airflow_home:/opt/airflow:Z" `
    -e "AIRFLOW_HOME=/opt/airflow" `
    -e "AUTO_UPDATE=$AUTO_UPDATE" `
    -e "KHARON_AIRFLOW_PASSWORD=$AIRFLOW_PASSWORD" `
    $IMAGE
