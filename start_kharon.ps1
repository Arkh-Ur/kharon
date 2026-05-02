# ============================================================================
# Kharōn — One-click startup for Windows
# Auto-detects Podman (recommended) or runs webapp natively.
# ============================================================================

param(
    [switch]$Podman,
    [switch]$AutoUpdate,
    [string]$AirflowHost = "localhost",
    [string]$AirflowPort = "8080",
    [string]$AirflowUser = "admin",
    [string]$AirflowPassword = "",
    [string]$KharonPort = "8501"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║     ⚓ Kharōn — Arkh-Ur               ║" -ForegroundColor Cyan
Write-Host "  ║   Plataforma de Orquestación y          ║" -ForegroundColor Cyan
Write-Host "  ║   Monitoreo de Scripts                  ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Auto-detect Podman if not specified ─────────────────────────────────────
$hasPodman = Get-Command podman -ErrorAction SilentlyContinue
if (-not $Podman -and $hasPodman) {
    Write-Host "[INFO] Podman detected — using all-in-one container mode" -ForegroundColor Green
    $Podman = $true
}

# ── Podman all-in-one mode ──────────────────────────────────────────────────
if ($Podman) {
    if (-not $hasPodman) {
        Write-Host "[ERROR] Podman no encontrado." -ForegroundColor Red
        Write-Host "        Instalá Podman Desktop: https://podman-desktop.io/" -ForegroundColor Yellow
        Write-Host "        O ejecá sin -Podman para modo webapp nativa." -ForegroundColor Yellow
        exit 1
    }

    $image = "kharon:latest"
    if (-not (podman image exists $image 2>$null)) {
        Write-Host "[INFO] Building $image (first run, ~3 min)..." -ForegroundColor Green
        podman build -t $image $ScriptDir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Build failed. Check Containerfile." -ForegroundColor Red
            exit 1
        }
    }

    Write-Host "[INFO] Starting Kharōn container..." -ForegroundColor Green
    podman run -it --rm `
      --name kharon `
      -p "${AirflowPort}:8080" `
      -p "${KharonPort}:8501" `
      -v "${ScriptDir}/airflow_home:/opt/airflow:Z" `
      -e "AUTO_UPDATE=$(if ($AutoUpdate) {'true'} else {'false'})" `
      -e "KHARON_AIRFLOW_PASSWORD=${AirflowPassword}" `
      $image
    return
}

# ── Native webapp mode (Airflow must be running separately) ─────────────────

# Auto-install uv if missing
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] uv not found — installing..." -ForegroundColor Green
    winget install astral-sh.uv --accept-source-agreements --accept-package-agreements 2>$null
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] uv installation failed. Install manually: winget install astral-sh.uv" -ForegroundColor Red
        exit 1
    }
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python no encontrado. Instalá Python 3.11+ desde python.org" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] $(python --version)" -ForegroundColor Green
Write-Host "[INFO] Syncing dependencies..." -ForegroundColor Green
uv sync --project $ScriptDir

$VenvActivate = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $VenvActivate)) {
    Write-Host "[ERROR] Virtual environment not found. Run: uv sync" -ForegroundColor Red
    exit 1
}
& $VenvActivate

if (-not $AirflowPassword) {
    $PwFile = Join-Path $ScriptDir "airflow_home\simple_auth_manager_passwords.json.generated"
    if (Test-Path $PwFile) {
        $AirflowPassword = (Get-Content $PwFile | ConvertFrom-Json).admin
    } else {
        $AirflowPassword = "admin"
    }
}

$env:KHARON_AIRFLOW_HOST     = $AirflowHost
$env:KHARON_AIRFLOW_PORT     = $AirflowPort
$env:KHARON_AIRFLOW_USER     = $AirflowUser
$env:KHARON_AIRFLOW_PASSWORD = $AirflowPassword
$env:KHARON_PORT             = $KharonPort
$env:AIRFLOW_HOME            = Join-Path $ScriptDir "airflow_home"

Write-Host "[INFO] Checking Airflow at ${AirflowHost}:${AirflowPort}..." -ForegroundColor Green
try {
    Invoke-RestMethod -Uri "http://${AirflowHost}:${AirflowPort}/api/v2/monitor/health" -TimeoutSec 5 | Out-Null
    Write-Host "[INFO] Airflow ready" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Airflow not responding. Start with: .\start_kharon.ps1 -Podman" -ForegroundColor Yellow
}

Write-Host "[INFO] Starting Kharōn webapp on port $KharonPort..." -ForegroundColor Green
Set-Location (Join-Path $ScriptDir "webapp")
streamlit run app.py `
    --server.port $KharonPort `
    --server.address "0.0.0.0" `
    --browser.gatherUsageStats false `
    --theme.primaryColor "#374151" `
    --theme.backgroundColor "#0A0F18" `
    --theme.secondaryBackgroundColor "#131923" `
    --theme.textColor "#e5e7eb"
