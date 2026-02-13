# Script para corregir templates masivamente
# MovIAx - Corrección de templates base

Write-Host "=== Corrección Masiva de Templates MovIAx ===" -ForegroundColor Cyan
Write-Host ""

# Definir módulos y sus clases
$modulos = @{
    "services" = "service-page"
    "catalog" = "catalog-page"
    "inventory" = "inventory-page"
    "maintenance" = "maintenance-page"
}

$totalCorregidos = 0

foreach ($modulo in $modulos.Keys) {
    $clase = $modulos[$modulo]
    $ruta = "forge_api\templates\frontend\$modulo"
    
    Write-Host "Procesando módulo: $modulo" -ForegroundColor Yellow
    
    if (Test-Path $ruta) {
        $archivos = Get-ChildItem -Path $ruta -Filter "*.html" -Exclude "*.old.html"
        
        foreach ($archivo in $archivos) {
            $contenido = Get-Content $archivo.FullName -Raw -Encoding UTF8
            
            # Verificar si usa el template antiguo
            if ($contenido -match "{% extends ['\`"]frontend/base\.html['\`"] %}") {
                Write-Host "  Corrigiendo: $($archivo.Name)" -ForegroundColor Green
                
                # Reemplazar template base
                $contenido = $contenido -replace "{% extends ['\`"]frontend/base\.html['\`"] %}", "{% extends 'frontend/base/base.html' %}"
                
                # Agregar body_class si no existe
                if ($contenido -notmatch "{% block body_class %}") {
                    # Buscar la línea del título
                    if ($contenido -match "({% block title %}.*?{% endblock %})") {
                        $tituloBlock = $matches[1]
                        $nuevoContenido = $contenido -replace [regex]::Escape($tituloBlock), "$tituloBlock`n`n{% block body_class %}$clase{% endblock %}"
                        $contenido = $nuevoContenido
                    }
                }
                
                # Guardar archivo
                $contenido | Set-Content $archivo.FullName -Encoding UTF8 -NoNewline
                $totalCorregidos++
            }
        }
    } else {
        Write-Host "  Ruta no encontrada: $ruta" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "=== Corrección Completada ===" -ForegroundColor Cyan
Write-Host "Total de archivos corregidos: $totalCorregidos" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE: Reinicia el servidor Django para aplicar los cambios" -ForegroundColor Yellow
