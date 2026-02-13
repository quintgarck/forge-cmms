# Script de Verificación de Uniformidad - Modo Oscuro MovIAx
# Sagecores - 2026

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verificación de Uniformidad CSS" -ForegroundColor Cyan
Write-Host "  MovIAx - Modo Oscuro" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que el archivo CSS existe
Write-Host "[1/5] Verificando archivo CSS..." -ForegroundColor Yellow
$cssFile = "forge_api/static/frontend/css/moviax-theme.css"

if (Test-Path $cssFile) {
    $cssContent = Get-Content $cssFile -Raw
    $lineCount = (Get-Content $cssFile).Count
    Write-Host "  ✓ Archivo encontrado: $cssFile" -ForegroundColor Green
    Write-Host "  ✓ Total de líneas: $lineCount" -ForegroundColor Green
    
    # Verificar que las reglas de uniformidad están presentes
    if ($cssContent -match "UNIFORMIDAD DE HEADERS Y GRADIENTES EN MODO OSCURO") {
        Write-Host "  ✓ Reglas de uniformidad encontradas" -ForegroundColor Green
    } else {
        Write-Host "  [X] Reglas de uniformidad NO encontradas" -ForegroundColor Red
        Write-Host "    Las reglas CSS no están en el archivo" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  [X] Archivo CSS no encontrado" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Verificar servidor Django
Write-Host "[2/5] Verificando servidor Django..." -ForegroundColor Yellow
$djangoProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*runserver*"}

if ($djangoProcess) {
    Write-Host "  ✓ Servidor Django está corriendo" -ForegroundColor Green
    Write-Host "    PID: $($djangoProcess.Id)" -ForegroundColor Gray
} else {
    Write-Host "  [!] Servidor Django NO está corriendo" -ForegroundColor Yellow
    Write-Host "    Ejecuta: python manage.py runserver" -ForegroundColor Yellow
}

Write-Host ""

# 3. Verificar archivos HTML con gradientes inline
Write-Host "[3/5] Buscando gradientes inline en HTML..." -ForegroundColor Yellow
$htmlFiles = Get-ChildItem -Path "forge_api/templates/frontend" -Filter "*.html" -Recurse

$filesWithGradients = @()
foreach ($file in $htmlFiles) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match 'style="[^"]*background:\s*linear-gradient') {
        $filesWithGradients += $file.FullName
    }
}

if ($filesWithGradients.Count -gt 0) {
    Write-Host "  [!] Encontrados $($filesWithGradients.Count) archivos con gradientes inline:" -ForegroundColor Yellow
    foreach ($file in $filesWithGradients) {
        $relativePath = $file -replace [regex]::Escape($PWD.Path + "\"), ""
        Write-Host "    - $relativePath" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "  NOTA: Los gradientes inline pueden sobrescribir las reglas CSS" -ForegroundColor Yellow
    Write-Host "        Las reglas CSS con !important deberían sobrescribirlos" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ No se encontraron gradientes inline en HTML" -ForegroundColor Green
}

Write-Host ""

# 4. Generar reporte de módulos a verificar
Write-Host "[4/5] Módulos a verificar manualmente..." -ForegroundColor Yellow
$modules = @(
    @{Name="Dashboard"; URL="http://127.0.0.1:8000/dashboard/"; Status="[OK] Referencia"},
    @{Name="Services"; URL="http://127.0.0.1:8000/services/"; Status="[?] Verificar"},
    @{Name="OEM Catalog"; URL="http://127.0.0.1:8000/oem/"; Status="[?] Verificar"},
    @{Name="Catalog"; URL="http://127.0.0.1:8000/catalog/"; Status="[?] Verificar"},
    @{Name="Inventory"; URL="http://127.0.0.1:8000/inventory/"; Status="[?] Verificar"},
    @{Name="Alerts"; URL="http://127.0.0.1:8000/alerts/"; Status="[?] Verificar"},
    @{Name="Technicians"; URL="http://127.0.0.1:8000/technicians/"; Status="[?] Verificar"},
    @{Name="Invoices"; URL="http://127.0.0.1:8000/invoices/"; Status="[?] Verificar"}
)

Write-Host ""
Write-Host "  Módulos a verificar en modo oscuro:" -ForegroundColor Cyan
Write-Host "  (Usa Ctrl+Shift+D para cambiar al modo oscuro)" -ForegroundColor Gray
Write-Host ""

foreach ($module in $modules) {
    Write-Host "  $($module.Status) $($module.Name)" -ForegroundColor White
    Write-Host "     $($module.URL)" -ForegroundColor Gray
}

Write-Host ""

# 5. Instrucciones de limpieza de caché
Write-Host "[5/5] Instrucciones de limpieza de caché..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  CRÍTICO: Debes limpiar el caché del navegador" -ForegroundColor Red
Write-Host ""
Write-Host "  Opción A - Hard Refresh (Recomendado):" -ForegroundColor Cyan
Write-Host "    Chrome/Edge: Ctrl + Shift + R  o  Ctrl + F5" -ForegroundColor White
Write-Host "    Firefox:     Ctrl + Shift + R  o  Ctrl + F5" -ForegroundColor White
Write-Host ""
Write-Host "  Opción B - DevTools:" -ForegroundColor Cyan
Write-Host "    1. Abrir DevTools (F12)" -ForegroundColor White
Write-Host "    2. Click derecho en botón refresh" -ForegroundColor White
Write-Host "    3. 'Empty Cache and Hard Reload'" -ForegroundColor White
Write-Host ""
Write-Host "  Opción C - Modo Incógnito:" -ForegroundColor Cyan
Write-Host "    Abrir ventana incógnito/privada" -ForegroundColor White
Write-Host ""

# Resumen final
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RESUMEN" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Paleta Oscura Uniforme (sin gradientes):" -ForegroundColor Yellow
Write-Host ""
Write-Host "  • Body/Main:     #141B28  (oscuro mate)" -ForegroundColor White
Write-Host "  • Cards:         #1E293B  (gris oscuro)" -ForegroundColor White
Write-Host "  • Headers:       #334155  (gris medio)" -ForegroundColor White
Write-Host "  • Texto:         #F8FAFC  (casi blanco)" -ForegroundColor White
Write-Host "  • Bordes:        #475569  (gris medio)" -ForegroundColor White
Write-Host ""
Write-Host "  • Success:       #10B981  (verde sólido)" -ForegroundColor Green
Write-Host "  • Warning:       #F59E0B  (amarillo sólido)" -ForegroundColor Yellow
Write-Host "  • Danger:        #EF4444  (rojo sólido)" -ForegroundColor Red
Write-Host "  • Info/Primary:  #60A5FA  (azul sólido)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  [!] NO debe haber gradientes visibles en modo oscuro" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Preguntar si quiere abrir el navegador
Write-Host "¿Deseas abrir el navegador en modo incógnito? (S/N): " -NoNewline -ForegroundColor Cyan
$response = Read-Host

if ($response -eq "S" -or $response -eq "s") {
    Write-Host ""
    Write-Host "Abriendo navegador..." -ForegroundColor Green
    
    # Intentar abrir Chrome en modo incógnito
    $chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
    if (Test-Path $chromePath) {
        Start-Process $chromePath -ArgumentList "--incognito", "http://127.0.0.1:8000/dashboard/"
        Write-Host "✓ Chrome abierto en modo incógnito" -ForegroundColor Green
    } else {
        # Intentar Edge
        $edgePath = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if (Test-Path $edgePath) {
            Start-Process $edgePath -ArgumentList "-inprivate", "http://127.0.0.1:8000/dashboard/"
            Write-Host "✓ Edge abierto en modo privado" -ForegroundColor Green
        } else {
            Write-Host "[X] No se encontró Chrome ni Edge" -ForegroundColor Red
            Write-Host "  Abre manualmente: http://127.0.0.1:8000/dashboard/" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "Verificación completada." -ForegroundColor Green
Write-Host "Lee INSTRUCCIONES_VERIFICACION_UNIFORMIDAD.md para más detalles." -ForegroundColor Gray
Write-Host ""
