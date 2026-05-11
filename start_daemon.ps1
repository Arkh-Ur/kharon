# ============================================================================
# Kharōn — Start as Daemon (Background)
# Levanta PostgreSQL, Airflow (WSL) y Streamlit (Windows) de forma invisible
# ============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "🚀 Iniciando Kharōn en modo demonio (segundo plano)..." -ForegroundColor Cyan

# 1. Detener instancias previas para evitar puertos ocupados
Write-Host "Limpiando instancias anteriores..." -ForegroundColor Yellow
wsl -u root service postgresql stop | Out-Null
wsl -u hbuddenberg bash -c "pkill -f airflow" 2>$null
# Buscamos procesos de python corriendo streamlit en esta carpeta
Get-WmiObject Win32_Process -Filter "CommandLine LIKE '%streamlit%'" | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# 2. Iniciar PostgreSQL (requiere root en WSL1, no pide password desde Windows)
Write-Host "Levantando PostgreSQL..." -ForegroundColor Green
wsl -u root service postgresql start | Out-Null

# 3. Iniciar Airflow oculto
Write-Host "Levantando Apache Airflow (WSL)..." -ForegroundColor Green
$airflowHomeWsl = "/mnt/d/Dev/kharon/airflow_home"
$airflowCmd = "export PATH='/home/hbuddenberg/.local/bin:`$PATH'; source ~/airflow-env/bin/activate; export AIRFLOW_HOME='$airflowHomeWsl'; export AIRFLOW__CORE__LOAD_EXAMPLES='False'; export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN='postgresql+psycopg2://airflow:airflow@localhost/airflow'; export AIRFLOW__CORE__EXECUTOR='LocalExecutor'; airflow standalone"
Start-Process -WindowStyle Hidden -FilePath "wsl.exe" -ArgumentList "-u", "hbuddenberg", "bash", "-c", $airflowCmd

Write-Host "Esperando unos segundos para la base de datos..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 4. Iniciar Streamlit oculto
Write-Host "Levantando Kharōn Webapp (Windows)..." -ForegroundColor Green
$PwFile = Join-Path $ScriptDir "airflow_home\simple_auth_manager_passwords.json.generated"
if (Test-Path $PwFile) {
    $env:KHARON_AIRFLOW_PASSWORD = (Get-Content $PwFile | ConvertFrom-Json).admin
} else {
    $env:KHARON_AIRFLOW_PASSWORD = "admin"
}
$env:KHARON_AIRFLOW_USER = "admin"

$webappDir = Join-Path $ScriptDir "webapp"
$uvPath = "uv"
if (Test-Path "$env:USERPROFILE\.local\bin\uv.exe") {
    $uvPath = "$env:USERPROFILE\.local\bin\uv.exe"
}
Start-Process -WindowStyle Hidden -FilePath $uvPath -ArgumentList "run", "streamlit", "run", "app.py", "--server.headless", "true" -WorkingDirectory $webappDir

Write-Host ""
Write-Host "✅ ¡Kharōn está ejecutándose como demonio!" -ForegroundColor Cyan
Write-Host "👉 Webapp:  http://localhost:8501" -ForegroundColor White
Write-Host "👉 Airflow: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "Para detener el sistema, ejecuta: .\stop_daemon.ps1" -ForegroundColor Yellow
Start-Sleep -Seconds 3
