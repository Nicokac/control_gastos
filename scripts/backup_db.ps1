# =============================================================================
# Script de backup para PostgreSQL (Render)
# Uso: .\scripts\backup_db.ps1
# =============================================================================

# -----------------------------------------------------------------------------
# Configuracion
# -----------------------------------------------------------------------------
$BACKUP_DIR = ".\backups"
$RETENTION_DAYS = 7
$DATE = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$BACKUP_FILE = "$BACKUP_DIR\backup_$DATE.dump"

# -----------------------------------------------------------------------------
# Verificar variables de entorno
# -----------------------------------------------------------------------------
if (-not $env:DB_HOST -or -not $env:DB_NAME -or -not $env:DB_USER -or -not $env:DB_PASSWORD) {
    Write-Host "[ERROR] Variables de entorno de DB no configuradas" -ForegroundColor Red
    Write-Host ""
    Write-Host "Requeridas:"
    Write-Host '  $env:DB_HOST = "tu-host.render.com"'
    Write-Host '  $env:DB_NAME = "tu_db_name"'
    Write-Host '  $env:DB_USER = "tu_usuario"'
    Write-Host '  $env:DB_PASSWORD = "tu_password"' # pragma: allowlist secret
    Write-Host '  $env:DB_PORT = "5432"  # opcional'
    exit 1
}

$DB_PORT = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }

# -----------------------------------------------------------------------------
# Crear directorio de backups
# -----------------------------------------------------------------------------
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
}

# -----------------------------------------------------------------------------
# Realizar backup
# -----------------------------------------------------------------------------
Write-Host "[INFO] Iniciando backup de $env:DB_NAME..." -ForegroundColor Cyan
Write-Host "   Host: $env:DB_HOST"
Write-Host "   Fecha: $DATE"

$env:PGPASSWORD = $env:DB_PASSWORD

$pgDumpPath = "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe"

if (-not (Test-Path $pgDumpPath)) {
    Write-Host "[ERROR] pg_dump no encontrado en $pgDumpPath" -ForegroundColor Red
    exit 1
}

& $pgDumpPath -h $env:DB_HOST -p $DB_PORT -U $env:DB_USER -d $env:DB_NAME -F c -f $BACKUP_FILE --no-password

# Verificar que se creo el archivo
if (Test-Path $BACKUP_FILE) {
    $size = (Get-Item $BACKUP_FILE).Length / 1KB
    Write-Host "[OK] Backup completado: $BACKUP_FILE ($([math]::Round($size, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host "[ERROR] No se pudo crear el backup" -ForegroundColor Red
    exit 1
}

# -----------------------------------------------------------------------------
# Limpiar backups antiguos
# -----------------------------------------------------------------------------
Write-Host "[CLEAN] Limpiando backups antiguos (+$RETENTION_DAYS dias)..." -ForegroundColor Yellow
$cutoffDate = (Get-Date).AddDays(-$RETENTION_DAYS)
$deleted = Get-ChildItem "$BACKUP_DIR\backup_*.dump" | Where-Object { $_.LastWriteTime -lt $cutoffDate }
$deletedCount = ($deleted | Measure-Object).Count
$deleted | Remove-Item -Force
Write-Host "   Eliminados: $deletedCount archivo(s)"

# -----------------------------------------------------------------------------
# Resumen
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STATS] Backups actuales:" -ForegroundColor Cyan
Get-ChildItem "$BACKUP_DIR\*.dump" | Format-Table Name, @{N='Size';E={"{0:N2} KB" -f ($_.Length/1KB)}}, LastWriteTime -AutoSize

Write-Host "[OK] Proceso completado" -ForegroundColor Green
