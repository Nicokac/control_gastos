# =============================================================================
# Script de restore para PostgreSQL (Render)
# Uso: .\scripts\restore_db.ps1 <archivo.dump>
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$BackupFile
)

# -----------------------------------------------------------------------------
# Verificar argumentos
# -----------------------------------------------------------------------------
if (-not $BackupFile) {
    Write-Host "[ERROR] Especificar archivo de backup" -ForegroundColor Red
    Write-Host ""
    Write-Host "Uso: .\scripts\restore_db.ps1 <archivo.dump>"
    Write-Host ""
    Write-Host "Backups disponibles:"
    Get-ChildItem ".\backups\*.dump" -ErrorAction SilentlyContinue | Format-Table Name, @{N='Size';E={"{0:N2} KB" -f ($_.Length/1KB)}}, LastWriteTime -AutoSize
    exit 1
}

if (-not (Test-Path $BackupFile)) {
    Write-Host "[ERROR] Archivo no encontrado: $BackupFile" -ForegroundColor Red
    exit 1
}

# -----------------------------------------------------------------------------
# Verificar variables de entorno
# -----------------------------------------------------------------------------
if (-not $env:DB_HOST -or -not $env:DB_NAME -or -not $env:DB_USER -or -not $env:DB_PASSWORD) {
    Write-Host "[ERROR] Variables de entorno de DB no configuradas" -ForegroundColor Red
    exit 1
}

$DB_PORT = if ($env:DB_PORT) { $env:DB_PORT } else { "5432" }

# -----------------------------------------------------------------------------
# Confirmar restauracion
# -----------------------------------------------------------------------------
Write-Host "[WARN] ADVERTENCIA: Esto reemplazara TODOS los datos en $env:DB_NAME" -ForegroundColor Yellow
Write-Host ""
Write-Host "   Host: $env:DB_HOST"
Write-Host "   Base de datos: $env:DB_NAME"
Write-Host "   Archivo: $BackupFile"
Write-Host ""
$confirm = Read-Host "Continuar? (escribir 'SI' para confirmar)"

if ($confirm -ne "SI") {
    Write-Host "[ERROR] Restauracion cancelada" -ForegroundColor Red
    exit 1
}

# -----------------------------------------------------------------------------
# Restaurar backup
# -----------------------------------------------------------------------------
Write-Host "[INFO] Restaurando backup..." -ForegroundColor Cyan

$env:PGPASSWORD = $env:DB_PASSWORD

$pgRestorePath = "C:\Program Files\PostgreSQL\15\bin\pg_restore.exe"

if (-not (Test-Path $pgRestorePath)) {
    Write-Host "[ERROR] pg_restore no encontrado en $pgRestorePath" -ForegroundColor Red
    exit 1
}

& $pgRestorePath -h $env:DB_HOST -p $DB_PORT -U $env:DB_USER -d $env:DB_NAME -c --no-owner --no-privileges $BackupFile

Write-Host "[OK] Restauracion completada" -ForegroundColor Green
