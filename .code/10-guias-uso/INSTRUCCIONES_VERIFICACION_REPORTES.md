# Instrucciones de Verificación - Sistema de Reportes

**Fecha:** 2026-01-15  
**Propósito:** Verificar que todas las funcionalidades de reportes estén accesibles y funcionando

---

## 🎯 Objetivo

Verificar que puedes:
1. ✅ Acceder a la página de reportes desde el índice de catálogos
2. ✅ Ver y usar los filtros por fecha
3. ✅ Ver los 4 gráficos interactivos
4. ✅ Abrir el modal de reportes programados
5. ✅ Exportar reportes a PDF y Excel

---

## 📋 Checklist de Verificación

### Paso 1: Acceder al Índice de Catálogos ✅

1. Abre tu navegador
2. Navega a: `http://127.0.0.1:8000/catalog/`
3. Deberías ver la página principal de catálogos

**¿Qué esperar?**
- Página con múltiples tarjetas de módulos
- Cada tarjeta tiene un color diferente
- Hay 6 tarjetas en total

---

### Paso 2: Localizar la Tarjeta de Reportes ✅

1. En la página de catálogos, busca la tarjeta con:
   - **Título:** "Estadísticas y Reportes"
   - **Color:** Fondo negro (bg-dark)
   - **Icono:** 📊 (bi-graph-up)
   - **Ubicación:** Última tarjeta (esquina inferior derecha)

**¿Qué esperar?**
```
┌─────────────────────────────────────────┐
│  📊 Estadísticas y Reportes             │
│  [Fondo Negro]                          │
│                                         │
│  Centro de reportes y análisis...      │
│                                         │
│  [📊 Ver Reportes]  [⬇ Exportar]      │
└─────────────────────────────────────────┘
```

**✅ VERIFICACIÓN:**
- [ ] Veo la tarjeta "Estadísticas y Reportes"
- [ ] La tarjeta tiene fondo negro
- [ ] Veo el botón "Ver Reportes"

---

### Paso 3: Hacer Clic en "Ver Reportes" ✅

1. Haz clic en el botón **"Ver Reportes"** (botón negro)
2. Deberías ser redirigido a: `http://127.0.0.1:8000/catalog/reports/`

**¿Qué esperar?**
- Página nueva con título "Reportes de Catálogo"
- Sección de filtros en la parte superior
- 4 tarjetas de estadísticas con colores
- Múltiples gráficos

**✅ VERIFICACIÓN:**
- [ ] La URL cambió a `/catalog/reports/`
- [ ] Veo el título "Reportes de Catálogo"
- [ ] Veo la sección de filtros
- [ ] Veo las 4 tarjetas de estadísticas

---

### Paso 4: Verificar Filtros por Fecha ✅

1. En la parte superior de la página, busca la sección con fondo degradado gris
2. Deberías ver:
   - Campo "Fecha Desde"
   - Campo "Fecha Hasta"
   - Dropdown "Período Rápido"
   - Botón "Aplicar Filtros"

**Prueba 1: Usar Período Rápido**
1. Haz clic en el dropdown "Período Rápido"
2. Selecciona "Últimos 30 días"
3. La página debería recargarse automáticamente

**Prueba 2: Usar Rango Personalizado**
1. Selecciona una fecha en "Fecha Desde"
2. Selecciona una fecha en "Fecha Hasta"
3. Haz clic en "Aplicar Filtros"
4. La página debería recargarse con los filtros aplicados

**✅ VERIFICACIÓN:**
- [ ] Veo la sección de filtros
- [ ] Puedo seleccionar fechas
- [ ] Puedo seleccionar períodos rápidos
- [ ] Los filtros funcionan al aplicarlos

---

### Paso 5: Verificar Tarjetas de Estadísticas ✅

Deberías ver 4 tarjetas con gradientes de colores:

**Tarjeta 1: Total Items**
- Color: Gradiente morado
- Icono: 📦 (bi-collection)
- Valor numérico visible

**Tarjeta 2: Tipos de Equipo**
- Color: Gradiente rosa
- Icono: ⚙️ (bi-gear-wide-connected)
- Valor numérico visible

**Tarjeta 3: Proveedores**
- Color: Gradiente azul
- Icono: 🏢 (bi-building)
- Valor numérico visible

**Tarjeta 4: Códigos de Referencia**
- Color: Gradiente verde
- Icono: 🏷️ (bi-tags)
- Valor numérico visible

**✅ VERIFICACIÓN:**
- [ ] Veo las 4 tarjetas
- [ ] Cada tarjeta tiene un color diferente
- [ ] Cada tarjeta muestra un número
- [ ] Las tarjetas tienen efecto hover (se elevan al pasar el mouse)

---

### Paso 6: Verificar Gráficos Interactivos ✅

Desplázate hacia abajo y verifica que veas estos 4 gráficos:

**Gráfico 1: Distribución de Códigos de Referencia**
- Tipo: Gráfico de barras
- Colores: Multicolor (rojo, azul, amarillo, etc.)
- Título: "Distribución de Códigos de Referencia"

**Gráfico 2: Estructura de Taxonomía**
- Tipo: Gráfico de dona (circular)
- Colores: Azul, verde, morado
- Leyenda: Sistemas, Subsistemas, Grupos

**Gráfico 3: Tendencias y Comparaciones**
- Tipo: Gráfico de líneas
- Título: "Evolución Mensual del Catálogo"
- 3 líneas de diferentes colores
- Leyenda: Tipos de Equipo, Proveedores, Códigos

**Gráfico 4: Análisis Predictivo**
- Tipo: Gráfico de líneas con proyección
- Título: "Proyección de Crecimiento (6 meses)"
- 3 líneas: Datos Reales, Predicción Optimista, Predicción Conservadora
- Líneas punteadas para predicciones

**Interactividad:**
- Pasa el mouse sobre los gráficos
- Deberías ver tooltips con valores
- Puedes hacer clic en la leyenda para ocultar/mostrar datasets

**✅ VERIFICACIÓN:**
- [ ] Veo el gráfico de barras (Códigos de Referencia)
- [ ] Veo el gráfico de dona (Taxonomía)
- [ ] Veo el gráfico de líneas (Tendencias)
- [ ] Veo el gráfico de predicción
- [ ] Los gráficos son interactivos (tooltips funcionan)

---

### Paso 7: Verificar Análisis Predictivo ✅

Desplázate hasta encontrar la sección con fondo azul claro:

**Título:** "🤖 Análisis Predictivo"  
**Subtítulo:** "💡 Insights Inteligentes"

Deberías ver 4 insights:

1. **✅ Predicción de Crecimiento**
   - Badge: "Confianza: 87%"
   - Color: Gradiente naranja

2. **⚠️ Áreas de Atención**
   - Badge: "Prioridad: Media"
   - Color: Gradiente rosa

3. **📈 Oportunidades**
   - Badge: "Impacto: Alto"
   - Color: Gradiente verde

4. **📅 Próximas Acciones**
   - Badge: "Plazo: 30 días"
   - Color: Gradiente azul

**✅ VERIFICACIÓN:**
- [ ] Veo la sección de análisis predictivo
- [ ] Veo los 4 insights con sus badges
- [ ] Los badges tienen colores diferentes
- [ ] Cada insight tiene un icono diferente

---

### Paso 8: Verificar Reportes Programados ✅

Continúa desplazándote hasta encontrar:

**Título:** "⏰ Reportes Programados"  
**Botón:** "➕ Nuevo Reporte Programado" (azul, esquina superior derecha)

Deberías ver:
- Una tabla con reportes de ejemplo
- 2 filas de ejemplo:
  1. "Reporte Semanal de Catálogo"
  2. "Análisis Mensual de Proveedores"
- Columnas: Nombre, Frecuencia, Próxima Ejecución, Destinatarios, Estado, Acciones

**✅ VERIFICACIÓN:**
- [ ] Veo la sección "Reportes Programados"
- [ ] Veo el botón "Nuevo Reporte Programado"
- [ ] Veo la tabla con 2 reportes de ejemplo
- [ ] Cada fila tiene botones de Editar y Eliminar

---

### Paso 9: Abrir Modal de Reportes Programados ✅

**ESTE ES EL PASO MÁS IMPORTANTE**

1. Haz clic en el botón **"➕ Nuevo Reporte Programado"**
2. Debería abrirse un modal (ventana emergente)

**¿Qué esperar en el modal?**

```
┌─────────────────────────────────────────────────────────┐
│  📅 Programar Nuevo Reporte                        [X]  │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Nombre del Reporte:                                   │
│  [_____________________________________________]        │
│                                                         │
│  Frecuencia:                                           │
│  [Seleccione... ▼]                                     │
│                                                         │
│  Hora de Ejecución:                                    │
│  [__:__]                                               │
│                                                         │
│  Destinatarios (separados por coma):                   │
│  [_____________________________________________]        │
│                                                         │
│  Formato:                                              │
│  [PDF ▼]                                               │
│                                                         │
│  ☐ Incluir gráficos                                   │
│  ☐ Incluir análisis predictivo                        │
│                                                         │
│  [Cancelar]                          [💾 Guardar]      │
└─────────────────────────────────────────────────────────┘
```

**Campos del formulario:**
1. Nombre del Reporte (input text)
2. Frecuencia (dropdown: Diario/Semanal/Mensual/Trimestral)
3. Hora de Ejecución (input time)
4. Destinatarios (input text)
5. Formato (dropdown: PDF/Excel/Ambos)
6. Incluir gráficos (checkbox)
7. Incluir análisis predictivo (checkbox)

**Prueba el formulario:**
1. Completa todos los campos
2. Haz clic en "Guardar"
3. Deberías ver un alert: "Reporte programado guardado exitosamente"
4. El modal debería cerrarse

**✅ VERIFICACIÓN:**
- [ ] El modal se abre al hacer clic en el botón
- [ ] Veo todos los campos del formulario
- [ ] Puedo escribir en los campos
- [ ] Puedo seleccionar opciones en los dropdowns
- [ ] Puedo marcar los checkboxes
- [ ] El botón "Guardar" funciona
- [ ] Aparece el mensaje de confirmación
- [ ] El modal se cierra después de guardar

---

### Paso 10: Verificar Exportación ✅

En la parte superior derecha de la página, busca los botones:

**Botones disponibles:**
1. 🖨️ **Imprimir** (outline-primary)
2. ⬇️ **Exportar** (outline-success, con dropdown)
3. ← **Volver** (outline-secondary)

**Prueba 1: Exportar a PDF**
1. Haz clic en "Exportar"
2. Selecciona "📄 Exportar a PDF"
3. Debería descargarse un archivo PDF

**Prueba 2: Exportar a Excel**
1. Haz clic en "Exportar"
2. Selecciona "📊 Exportar a Excel"
3. Debería descargarse un archivo Excel (.xlsx)

**Prueba 3: Imprimir**
1. Haz clic en "Imprimir"
2. Debería abrirse el diálogo de impresión del navegador

**✅ VERIFICACIÓN:**
- [ ] Veo los 3 botones en la parte superior
- [ ] El dropdown de "Exportar" se abre
- [ ] Puedo hacer clic en "Exportar a PDF"
- [ ] Puedo hacer clic en "Exportar a Excel"
- [ ] El botón "Imprimir" abre el diálogo de impresión

---

### Paso 11: Verificar Enlaces Rápidos ✅

En el sidebar derecho (columna derecha), deberías ver:

**Sección: "⚡ Accesos Rápidos"**

Enlaces disponibles:
1. ⚙️ Gestionar Tipos de Equipo
2. 🌳 Gestionar Taxonomía
3. 🏷️ Gestionar Códigos de Referencia
4. 💱 Gestionar Monedas
5. 🏢 Gestionar Proveedores

**Prueba:**
- Haz clic en cada enlace
- Deberías ser redirigido a la página correspondiente

**✅ VERIFICACIÓN:**
- [ ] Veo la sección de enlaces rápidos
- [ ] Veo los 5 enlaces
- [ ] Los enlaces funcionan (redirigen correctamente)

---

## 🐛 Troubleshooting

### Problema 1: No veo la tarjeta de reportes en el índice

**Posibles causas:**
- La página no cargó completamente
- Hay un error en el template

**Soluciones:**
1. Refresca la página (F5)
2. Limpia caché (Ctrl+Shift+R)
3. Verifica la consola del navegador (F12)

---

### Problema 2: Error 404 al hacer clic en "Ver Reportes"

**Causa:** La URL no está registrada

**Solución:**
```bash
# Verifica que la URL esté registrada
python manage.py show_urls | grep catalog_reports

# Debería mostrar:
# /catalog/reports/ [name='catalog_reports']
```

Si no aparece, verifica `forge_api/frontend/urls.py`:
```python
path('catalog/reports/', CatalogReportsView.as_view(), name='catalog_reports'),
```

---

### Problema 3: Los gráficos no se muestran

**Causa:** Chart.js no está cargando

**Solución:**
1. Abre DevTools (F12)
2. Ve a la pestaña "Console"
3. Busca errores relacionados con Chart.js
4. Si ves error de CDN, verifica tu conexión a internet

**Verificación manual:**
```javascript
// En la consola del navegador, escribe:
typeof Chart

// Debería devolver: "function"
// Si devuelve "undefined", Chart.js no está cargando
```

---

### Problema 4: El modal no se abre

**Causa:** Bootstrap JS no está cargando

**Solución:**
1. Abre DevTools (F12)
2. Ve a la pestaña "Console"
3. Busca errores relacionados con Bootstrap
4. Verifica que `bootstrap.bundle.min.js` esté incluido en base.html

**Verificación manual:**
```javascript
// En la consola del navegador, escribe:
typeof bootstrap

// Debería devolver: "object"
// Si devuelve "undefined", Bootstrap JS no está cargando
```

---

### Problema 5: Los filtros no funcionan

**Causa:** JavaScript no está ejecutándose

**Solución:**
1. Abre DevTools (F12)
2. Ve a la pestaña "Console"
3. Busca errores de JavaScript
4. Verifica que el formulario tenga el atributo `method="get"`

---

### Problema 6: La exportación no funciona

**Causa:** La vista de exportación no está registrada o faltan dependencias

**Solución:**
```bash
# Verifica que la URL esté registrada
python manage.py show_urls | grep export

# Debería mostrar:
# /catalog/reports/export/ [name='catalog_report_export']
```

**Para PDF (opcional):**
```bash
pip install weasyprint
```

**Para Excel (opcional):**
```bash
pip install openpyxl
```

---

## 📊 Resultados Esperados

Al completar todas las verificaciones, deberías tener:

✅ **Acceso completo a reportes**
- Puedes navegar desde el índice a reportes
- La URL `/catalog/reports/` funciona

✅ **Filtros funcionales**
- Puedes filtrar por fecha
- Puedes usar períodos rápidos

✅ **Visualización completa**
- Ves las 4 tarjetas de estadísticas
- Ves los 4 gráficos interactivos
- Ves la sección de análisis predictivo
- Ves la sección de reportes programados

✅ **Modal funcional**
- El modal se abre correctamente
- Puedes completar el formulario
- El botón "Guardar" funciona

✅ **Exportación funcional**
- Puedes exportar a PDF
- Puedes exportar a Excel
- Puedes imprimir

---

## 📝 Reporte de Verificación

Completa este checklist y comparte los resultados:

```
VERIFICACIÓN DEL SISTEMA DE REPORTES
Fecha: _______________
Usuario: _______________

[ ] Paso 1: Acceso al índice de catálogos
[ ] Paso 2: Localización de tarjeta de reportes
[ ] Paso 3: Clic en "Ver Reportes"
[ ] Paso 4: Verificación de filtros
[ ] Paso 5: Verificación de tarjetas de estadísticas
[ ] Paso 6: Verificación de gráficos
[ ] Paso 7: Verificación de análisis predictivo
[ ] Paso 8: Verificación de sección de reportes programados
[ ] Paso 9: Apertura de modal ⭐ IMPORTANTE
[ ] Paso 10: Verificación de exportación
[ ] Paso 11: Verificación de enlaces rápidos

PROBLEMAS ENCONTRADOS:
_________________________________________________
_________________________________________________
_________________________________________________

FUNCIONALIDADES QUE SÍ FUNCIONAN:
_________________________________________________
_________________________________________________
_________________________________________________

FUNCIONALIDADES QUE NO FUNCIONAN:
_________________________________________________
_________________________________________________
_________________________________________________
```

---

## 🎯 Conclusión

Si completaste todos los pasos exitosamente:

✅ **El sistema de reportes está completamente funcional**
✅ **Todas las funcionalidades visuales están implementadas**
✅ **El modal de reportes programados funciona correctamente**
⚠️ **Solo falta el backend para guardar reportes en la base de datos**

**Próximo paso:** Decidir si implementar el backend de reportes programados o continuar con la **Tarea 4: Administración de Monedas**.

---

**Última actualización:** 2026-01-15  
**Versión:** 1.0  
**Estado:** ✅ Listo para Verificación
