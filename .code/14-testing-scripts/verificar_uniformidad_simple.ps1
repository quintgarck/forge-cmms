# Script de Verificación de Uniformidad - Modo Oscuro MovIAx
# Sagecores - 2026

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verificacion de Uniformidad CSS" -ForegroundColor Cyan
Write-Host "  MovIAx - Modo Oscuro" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que el archivo CSS existe
Write-Host "[1/4] Verificando archivo CSS..." -ForegroundColor Yellow
$cssFile = "forge_api/static/frontend/css/moviax-theme.css"

if (Test-Path $cssFile) {
    $cssContent = Get-Content $cssFile -Raw
    $lineCount = (Get-Content $cssFile).Count
    Write-Host "  [OK] Archivo encontrado: $cssFile" -ForegroundColor Green
    Write-Host "  [OK] Total de lineas: $lineCount" -ForegroundColor Green
    
    # Verificar que las reglas de uniformidad están presentes
    if ($cssContent -match "UNIFORMIDAD DE HEADERS Y GRADIENTES EN MODO OSCURO") {
        Write-Host "  [OK] Reglas de uniformidad encontradas" -ForegroundColor Green
        
        # Verificar que las mejoras de tablas están presentes
        if ($cssContent -match "MEJORAS DE TABLAS EN MODO OSCURO") {
            Write-Host "  [OK] Mejoras de tablas encontradas" -ForegroundColor Green
        } else {
            Write-Host "  [!] Mejoras de tablas NO encontradas" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [X] Reglas de uniformidad NO encontradas" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  [X] Archivo CSS no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Verificar servidor Django
Write-Host "[2/4] Verificando servidor Django..." -ForegroundColor Yellow
$djangoProcess = Get-Process python -ErrorAction SilentlyContinue

if ($djangoProcess) {
    Write-Host "  [OK] Servidor Django esta corriendo" -ForegroundColor Green
} else {
    Write-Host "  [!] Servidor Django NO esta corriendo" -ForegroundColor Yellow
    Write-Host "    Ejecuta: python manage.py runserver" -ForegroundColor Yellow
}

Write-Host ""

# 3. Módulos a verificar
Write-Host "[3/4] Modulos a verificar manualmente..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  Modulos a verificar en modo oscuro:" -ForegroundColor Cyan
Write-Host "  (Usa Ctrl+Shift+D para cambiar al modo oscuro)" -ForegroundColor Gray
Write-Host ""

Write-Host "  [OK] Dashboard       - http://127.0.0.1:8000/dashboard/" -ForegroundColor Green
Write-Host "  [?]  Services        - http://127.0.0.1:8000/services/" -ForegroundColor Yellow
Write-Host "  [?]  OEM Catalog     - http://127.0.0.1:8000/oem/" -ForegroundColor Yellow
Write-Host "  [?]  Catalog         - http://127.0.0.1:8000/catalog/" -ForegroundColor Yellow
Write-Host "  [?]  Inventory       - http://127.0.0.1:8000/inventory/" -ForegroundColor Yellow
Write-Host "  [?]  Alerts          - http://127.0.0.1:8000/alerts/" -ForegroundColor Yellow
Write-Host "  [?]  Technicians     - http://127.0.0.1:8000/technicians/" -ForegroundColor Yellow
Write-Host "  [?]  Invoices        - http://127.0.0.1:8000/invoices/" -ForegroundColor Yellow

Write-Host ""

# 4. Instrucciones de limpieza de caché
Write-Host "[4/4] Instrucciones de limpieza de cache..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  CRITICO: Debes limpiar el cache del navegador" -ForegroundColor Red
Write-Host ""
Write-Host "  Opcion A - Hard Refresh (Recomendado):" -ForegroundColor Cyan
Write-Host "    Chrome/Edge: Ctrl + Shift + R  o  Ctrl + F5" -ForegroundColor White
Write-Host "    Firefox:     Ctrl + Shift + R  o  Ctrl + F5" -ForegroundColor White
Write-Host ""
Write-Host "  Opcion B - DevTools:" -ForegroundColor Cyan
Write-Host "    1. Abrir DevTools (F12)" -ForegroundColor White
Write-Host "    2. Click derecho en boton refresh" -ForegroundColor White
Write-Host "    3. 'Empty Cache and Hard Reload'" -ForegroundColor White
Write-Host ""

# Resumen final
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN - Paleta Oscura Uniforme" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Body/Main:     #141B28  (oscuro mate)" -ForegroundColor White
Write-Host "  Cards:         #1E293B  (gris oscuro)" -ForegroundColor White
Write-Host "  Headers:       #334155  (gris medio)" -ForegroundColor White
Write-Host "  Texto:         #F8FAFC  (casi blanco)" -ForegroundColor White
Write-Host "  Bordes:        #475569  (gris medio)" -ForegroundColor White
Write-Host ""
Write-Host "  Success:       #10B981  (verde solido)" -ForegroundColor Green
Write-Host "  Warning:       #F59E0B  (amarillo solido)" -ForegroundColor Yellow
Write-Host "  Danger:        #EF4444  (rojo solido)" -ForegroundColor Red
Write-Host "  Info/Primary:  #60A5FA  (azul solido)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [!] NO debe haber gradientes visibles en modo oscuro" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verificacion completada." -ForegroundColor Green
Write-Host "Lee INSTRUCCIONES_VERIFICACION_UNIFORMIDAD.md para mas detalles." -ForegroundColor Gray
Write-Host ""
