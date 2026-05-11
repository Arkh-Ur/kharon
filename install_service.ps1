# ============================================================================
# Kharōn — Instalar como Servicio de Arranque (Scheduled Task)
# ============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TaskName = "Kharon_Daemon"
$DaemonScript = Join-Path $ScriptDir "start_daemon.ps1"

Write-Host "🚀 Configurando Kharōn para que arranque automáticamente con Windows..." -ForegroundColor Cyan

# Eliminar tarea previa si existe
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 1. Trigger: Al arrancar el sistema
$Trigger = New-ScheduledTaskTrigger -AtStartup

# 2. Acción: Ejecutar el demonio en background
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$DaemonScript`"" -WorkingDirectory $ScriptDir

# 3. Settings: No detener nunca, permitir con batería
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0

# 4. Pedir contraseña de Windows (Requisito para correr sin usuario logueado)
Write-Host ""
Write-Host "Para que los procesos corran en el fondo incluso si nadie inicia sesión," -ForegroundColor Yellow
Write-Host "Windows necesita guardar tu contraseña local." -ForegroundColor Yellow
Write-Host "Se abrirá una ventana de Windows pidiendo tu contraseña actual." -ForegroundColor Cyan
Write-Host ""

$Credential = Get-Credential -UserName $env:USERNAME -Message "Ingresa tu contraseña de Windows para registrar el servicio Kharon_Daemon"

# Registrar la tarea como el usuario actual, con privilegios máximos
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -User $Credential.UserName -Password $Credential.GetNetworkCredential().Password -RunLevel Highest | Out-Null

Write-Host "✅ ¡Instalación completada exitosamente!" -ForegroundColor Green
Write-Host "Kharōn iniciará silenciosamente cada vez que enciendas tu PC."
Write-Host ""
Write-Host "Si alguna vez quieres desinstalar este auto-arranque, abre PowerShell como Administrador y ejecuta:"
Write-Host "Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false" -ForegroundColor DarkGray
Start-Sleep -Seconds 5
