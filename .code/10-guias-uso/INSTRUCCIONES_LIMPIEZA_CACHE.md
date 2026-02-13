# 🔧 INSTRUCCIONES PARA LIMPIAR CACHÉ Y APLICAR CORRECCIÓN DEL NAVBAR

## ⚠️ PROBLEMA ACTUAL
El navbar se pone blanco al navegar entre páginas en modo claro. La corrección (script v2.0) ya está implementada en el código, pero el navegador está cargando una versión antigua desde caché.

## ✅ SOLUCIÓN: LIMPIEZA COMPLETA DE CACHÉ

### PASO 1: Detener el Servidor Django
```cmd
# En la terminal donde está corriendo el servidor, presiona:
Ctrl + C
```

### PASO 2: Limpiar Caché del Navegador Chrome

#### Opción A - Limpieza Rápida (Recomendada):
1. Abre Chrome DevTools: `F12` o `Ctrl + Shift + I`
2. Haz clic derecho en el botón de recargar (junto a la barra de direcciones)
3. Selecciona: **"Vaciar caché y volver a cargar de manera forzada"** (Empty Cache and Hard Reload)

#### Opción B - Limpieza Completa:
1. Abre Chrome
2. Presiona: `Ctrl + Shift + Delete`
3. En la ventana que aparece:
   - Intervalo de tiempo: **Desde siempre**
   - Marca estas opciones:
     - ✅ Historial de navegación
     - ✅ Cookies y otros datos de sitios
     - ✅ Imágenes y archivos almacenados en caché
4. Haz clic en **"Borrar datos"**
5. Cierra Chrome completamente
6. Vuelve a abrir Chrome

### PASO 3: Reiniciar el Servidor Django
```cmd
# En la terminal del proyecto:
cd C:\ruta\a\tu\proyecto
python manage.py runserver
```

### PASO 4: Abrir con Caché Deshabilitado
1. Abre Chrome DevTools: `F12`
2. Ve a la pestaña **Network** (Red)
3. Marca la casilla: **"Disable cache"** (Deshabilitar caché)
4. Mantén DevTools abierto
5. Navega a: `http://localhost:8000/dashboard/`

### PASO 5: Verificar que el Script v2.0 se Cargó
1. Con DevTools abierto, ve a la pestaña **Console** (Consola)
2. Deberías ver estos mensajes:
   ```
   [MovIAx] Script de colores v2.0 iniciado
   [MovIAx] forceAllColors ejecutado - Modo: claro
   [MovIAx] Navbar forzado: #2563EB - Elementos: XX
   [MovIAx] Fondos forzados: #F8FAFC (claro)
   [MovIAx] Dropdowns forzados: #FFFFFF
   [MovIAx] Colores aplicados después de load completo
   [MovIAx] Script v2.0 completamente cargado y activo
   ```

### PASO 6: Probar la Corrección
1. Asegúrate de estar en **modo claro** (si no, presiona `Ctrl + Shift + D`)
2. El navbar debe ser **azul** (`#2563EB`) con texto blanco
3. Navega por diferentes opciones del sidebar:
   - Clientes
   - Equipos
   - Órdenes de Trabajo
   - Facturas
   - etc.
4. El navbar debe **mantener el color azul** en todas las páginas

### PASO 7: Probar Cambio de Modo
1. Presiona `Ctrl + Shift + D` para cambiar a modo oscuro
2. El navbar debe cambiar a **oscuro** (`#0F172A`)
3. Presiona `Ctrl + Shift + D` de nuevo para volver a modo claro
4. El navbar debe volver a **azul** (`#2563EB`) - **NO blanco**

## 🔍 DIAGNÓSTICO SI AÚN NO FUNCIONA

### Si NO ves los logs en consola:
El script v2.0 no se está cargando. Verifica:

1. **¿Qué archivo base.html se está usando?**
   ```cmd
   # Buscar todos los archivos base.html:
   dir /s /b base.html
   ```
   Debe ser: `forge_api\templates\frontend\base\base.html`

2. **¿El servidor está leyendo el archivo correcto?**
   - Detén el servidor
   - Abre `forge_api/templates/frontend/base/base.html`
   - Busca la línea: `console.log('[MovIAx] Script de colores v2.0 iniciado');`
   - Si está ahí, el problema es 100% caché del navegador

3. **Limpieza nuclear de caché:**
   ```cmd
   # Cerrar Chrome completamente
   # Eliminar caché manualmente:
   %LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache
   %LOCALAPPDATA%\Google\Chrome\User Data\Default\Code Cache
   ```

### Si ves los logs pero el navbar sigue blanco:
Hay un problema con el código. Reporta:
- Los logs exactos que ves en consola
- En qué página ocurre el problema
- Si ocurre al cargar la página o al navegar

## 📋 CAMBIOS IMPLEMENTADOS EN ESTA ACTUALIZACIÓN

1. ✅ Eliminado código duplicado al final del script
2. ✅ Agregado parámetro de versión al theme-switcher: `?v=2.0`
3. ✅ Agregados meta tags de cache control en el `<head>`
4. ✅ Agregado log final: `Script v2.0 completamente cargado y activo`

## 🎯 RESULTADO ESPERADO

Después de seguir estos pasos:
- ✅ Navbar azul (`#2563EB`) en modo claro
- ✅ Navbar oscuro (`#0F172A`) en modo oscuro
- ✅ Navbar mantiene color al navegar entre páginas
- ✅ Navbar mantiene color al cambiar de modo oscuro a claro
- ✅ Todos los dropdowns tematizados correctamente
- ✅ Fondos uniformes en todas las páginas

## 📞 SOPORTE

Si después de seguir TODOS estos pasos el problema persiste:
1. Toma captura de pantalla de la consola con los logs
2. Toma captura del navbar en modo claro (debe ser azul, no blanco)
3. Indica en qué paso específico tienes problemas
