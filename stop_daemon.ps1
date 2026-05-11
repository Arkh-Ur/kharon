# ============================================================================
# Kharōn — Stop Daemon
# Detiene PostgreSQL, Airflow (WSL) y Streamlit (Windows)
# ============================================================================

Write-Host "🛑 Deteniendo Kharōn..." -ForegroundColor Yellow

Write-Host "1. Deteniendo Kharōn Webapp (Streamlit)..."
Get-WmiObject Win32_Process -Filter "CommandLine LIKE '%streamlit%'" | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

Write-Host "2. Deteniendo Apache Airflow (WSL)..."
wsl -u hbuddenberg bash -c "pkill -f airflow" 2>$null

Write-Host "3. Deteniendo PostgreSQL (WSL)..."
wsl -u root service postgresql stop | Out-Null

Write-Host "✅ ¡Todos los servicios detenidos exitosamente!" -ForegroundColor Green
Start-Sleep -Seconds 2
