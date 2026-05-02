# ============================================================================
# Kharōn — Inicio de la webapp en Windows
# Solo inicia la webapp Streamlit. Airflow debe correr en Podman o WSL2.
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

# ── Podman all-in-one mode ──────────────────────────────────────────────────
if ($Podman) {
    $image = "kharon:latest"
    if (-not (podman image exists $image 2>$null)) {
        Write-Host "[INFO] Building $image..." -ForegroundColor Green
        podman build -t $image $ScriptDir
    }
    podman run -it --rm `
      --name kharon `
      -p 8080:8080 -p 8501:8501 `
      -v "${ScriptDir}/airflow_home:/opt/airflow:Z" `
      -e AUTO_UPDATE=$(if ($AutoUpdate) {"true"} else {"false"}) `
      -e KHARON_AIRFLOW_PASSWORD="${AirflowPassword}" `
      $image
    return
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║     ⚓ Kharōn — Arkh-Ur               ║" -ForegroundColor Cyan
Write-Host "  ║   Plataforma de Orquestación y          ║" -ForegroundColor Cyan
Write-Host "  ║   Monitoreo de Scripts                  ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Verificar Python ────────────────────────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python no encontrado. Instalá Python 3.11+ desde python.org"
    exit 1
}

$pythonVersion = python --version
Write-Host "[INFO] $pythonVersion" -ForegroundColor Green

# ── Verificar uv ────────────────────────────────────────────────────────────
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv no encontrado. Instalá con: winget install astral-sh.uv"
    exit 1
}

Write-Host "[INFO] Sincronizando dependencias..." -ForegroundColor Green
uv sync --project $ScriptDir

# ── Activar entorno virtual ──────────────────────────────────────────────────
$VenvActivate = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $VenvActivate)) {
    Write-Error "Entorno virtual no encontrado en $ScriptDir\.venv"
    exit 1
}
& $VenvActivate
Write-Host "[INFO] Entorno virtual activado" -ForegroundColor Green

# ── Contraseña de Airflow ────────────────────────────────────────────────────
if (-not $AirflowPassword) {
    $PwFile = Join-Path $ScriptDir "airflow_home\simple_auth_manager_passwords.json.generated"
    if (Test-Path $PwFile) {
        $AirflowPassword = (Get-Content $PwFile | ConvertFrom-Json).admin
        Write-Host "[INFO] Contraseña de Airflow cargada desde archivo generado" -ForegroundColor Green
    } else {
        $AirflowPassword = "admin"
        Write-Host "[WARN] No se encontró archivo de contraseña — usando 'admin'" -ForegroundColor Yellow
    }
}

# ── Variables de entorno ─────────────────────────────────────────────────────
$env:KHARON_AIRFLOW_HOST     = $AirflowHost
$env:KHARON_AIRFLOW_PORT     = $AirflowPort
$env:KHARON_AIRFLOW_USER     = $AirflowUser
$env:KHARON_AIRFLOW_PASSWORD = $AirflowPassword
$env:KHARON_PORT             = $KharonPort
$env:AIRFLOW_HOME            = Join-Path $ScriptDir "airflow_home"

# ── Verificar conexión a Airflow ─────────────────────────────────────────────
Write-Host "[INFO] Verificando conexión a Airflow en ${AirflowHost}:${AirflowPort}..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "http://${AirflowHost}:${AirflowPort}/api/v2/monitor/health" -TimeoutSec 5
    Write-Host "[INFO] Airflow disponible" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Airflow no responde en http://${AirflowHost}:${AirflowPort}" -ForegroundColor Yellow
    Write-Host "[WARN] Iniciá Airflow con Podman o WSL2 antes de continuar" -ForegroundColor Yellow
}

# ── Iniciar webapp ───────────────────────────────────────────────────────────
Write-Host "[INFO] Iniciando Kharōn webapp en el puerto $KharonPort..." -ForegroundColor Green

$WebappDir = Join-Path $ScriptDir "webapp"
Set-Location $WebappDir

streamlit run app.py `
    --server.port $KharonPort `
    --server.address "0.0.0.0" `
    --browser.gatherUsageStats false `
    --theme.primaryColor "#374151" `
    --theme.backgroundColor "#0A0F18" `
    --theme.secondaryBackgroundColor "#131923" `
    --theme.textColor "#e5e7eb"
