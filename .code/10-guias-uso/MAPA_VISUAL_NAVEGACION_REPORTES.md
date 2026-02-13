# Mapa Visual de Navegación - Sistema de Reportes

**Fecha:** 2026-01-15  
**Propósito:** Guía visual rápida para encontrar las funcionalidades de reportes

---

## 🗺️ Ruta de Navegación

```
INICIO
  │
  ├─→ http://127.0.0.1:8000/catalog/
  │   │
  │   └─→ Buscar tarjeta NEGRA (última tarjeta)
  │       │
  │       └─→ Clic en botón "Ver Reportes"
  │           │
  │           └─→ http://127.0.0.1:8000/catalog/reports/
  │               │
  │               ├─→ Scroll hacia abajo
  │               │   │
  │               │   └─→ Buscar sección "⏰ Reportes Programados"
  │               │       │
  │               │       └─→ Clic en "➕ Nuevo Reporte Programado"
  │               │           │
  │               │           └─→ ✅ MODAL SE ABRE
  │               │
  │               └─→ Botones superiores
  │                   │
  │                   ├─→ "Exportar" → "PDF" ✅
  │                   └─→ "Exportar" → "Excel" ✅
  │
  └─→ FIN
```

---

## 📍 Ubicaciones Exactas

### 1. Tarjeta de Reportes en Índice

**URL:** `http://127.0.0.1:8000/catalog/`

**Características visuales:**
- 🎨 Fondo: Negro (bg-dark)
- 📊 Icono: bi-graph-up
- 📍 Posición: Última tarjeta (fila 2, columna 3)
- 🔘 Botón: "Ver Reportes" (negro)

**Código HTML (línea 238):**
```html
<a href="{% url 'frontend:catalog_reports' %}" class="btn btn-dark">
    <i class="bi bi-bar-chart"></i> Ver Reportes
</a>
```

---

### 2. Botón de Nuevo Reporte Programado

**URL:** `http://127.0.0.1:8000/catalog/reports/`

**Características visuales:**
- 🎨 Color: Azul (btn-primary)
- ➕ Icono: bi-plus-circle
- 📍 Posición: Parte inferior de la página, esquina superior derecha de la sección
- 📝 Texto: "Nuevo Reporte Programado"

**Código HTML (línea 510):**
```html
<button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#scheduleReportModal">
    <i class="bi bi-plus-circle me-2"></i>
    Nuevo Reporte Programado
</button>
```

---

### 3. Modal de Reportes Programados

**ID:** `scheduleReportModal`

**Características:**
- 📋 Título: "Programar Nuevo Reporte"
- 🔢 Campos: 7 (nombre, frecuencia, hora, destinatarios, formato, 2 checkboxes)
- 💾 Botón guardar: "Guardar" (azul)
- ❌ Botón cerrar: "Cancelar" (gris)

**Código HTML (líneas 580-640):**
```html
<div class="modal fade" id="scheduleReportModal" tabindex="-1">
    <!-- Contenido del modal -->
</div>
```

---

## 🎯 Puntos Clave de Búsqueda

### En `/catalog/` busca:
1. ✅ Tarjeta con **fondo negro**
2. ✅ Título: "Estadísticas y Reportes"
3. ✅ Icono de gráfico (📊)
4. ✅ Es la **última tarjeta** de la página

### En `/catalog/reports/` busca:
1. ✅ Scroll hasta el **final** de la página
2. ✅ Sección con título "⏰ Reportes Programados"
3. ✅ Botón **azul** en la esquina superior derecha
4. ✅ Texto: "➕ Nuevo Reporte Programado"

---

## 🔍 Verificación Rápida (30 segundos)

```bash
# 1. Abrir navegador
http://127.0.0.1:8000/catalog/

# 2. Buscar tarjeta negra
# 3. Clic en "Ver Reportes"
# 4. Scroll hasta el final
# 5. Buscar botón azul "Nuevo Reporte Programado"
# 6. Clic en el botón
# 7. ¿Se abre el modal? ✅ SÍ / ❌ NO
```

---

## 📊 Diagrama de Elementos

```
PÁGINA: /catalog/
┌─────────────────────────────────────────────────────────┐
│  Gestión de Catálogos                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Tipos    │  │Taxonomía │  │ Códigos  │             │
│  │ Equipo   │  │          │  │Referencia│             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Monedas  │  │Proveedor │  │ REPORTES │ ← AQUÍ     │
│  │          │  │          │  │ [NEGRO]  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                [Ver Reportes] ← CLIC   │
└─────────────────────────────────────────────────────────┘
```

```
PÁGINA: /catalog/reports/
┌─────────────────────────────────────────────────────────┐
│  📊 Reportes de Catálogo                                │
│  [Imprimir] [Exportar ▼] [Volver]                      │
├─────────────────────────────────────────────────────────┤
│  📅 Filtros                                             │
│  📊 Estadísticas (4 tarjetas)                           │
│  📈 Gráficos (4 gráficos)                               │
│  🤖 Análisis Predictivo                                 │
│                                                         │
│  ⏰ Reportes Programados    [+ Nuevo Reporte] ← AQUÍ   │
│  ─────────────────────────────────────────────────────  │
│  Tabla con reportes...                                 │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist Visual

Cuando estés en `/catalog/`, deberías ver:
- [ ] 6 tarjetas de módulos
- [ ] La última tarjeta tiene fondo negro
- [ ] La tarjeta negra dice "Estadísticas y Reportes"
- [ ] Hay un botón "Ver Reportes" en la tarjeta negra

Cuando estés en `/catalog/reports/`, deberías ver:
- [ ] Título "Reportes de Catálogo" en la parte superior
- [ ] Sección de filtros con fondo gris degradado
- [ ] 4 tarjetas de estadísticas con colores
- [ ] 4 gráficos interactivos
- [ ] Sección "Análisis Predictivo" con fondo azul claro
- [ ] Sección "Reportes Programados" al final
- [ ] Botón azul "Nuevo Reporte Programado"

Cuando hagas clic en el botón azul:
- [ ] Se abre un modal (ventana emergente)
- [ ] El modal tiene título "Programar Nuevo Reporte"
- [ ] Hay 7 campos en el formulario
- [ ] Hay un botón "Guardar" azul
- [ ] Hay un botón "Cancelar" gris

---

## 🚨 Señales de Alerta

### Si NO ves la tarjeta de reportes:
- ⚠️ Verifica que estás en `/catalog/` (no en `/catalog/reports/`)
- ⚠️ Haz scroll hacia abajo (puede estar fuera de vista)
- ⚠️ Refresca la página (F5)
- ⚠️ Limpia caché (Ctrl+Shift+R)

### Si NO ves el botón de nuevo reporte:
- ⚠️ Verifica que estás en `/catalog/reports/` (no en `/catalog/`)
- ⚠️ Haz scroll hasta el FINAL de la página
- ⚠️ Busca la sección "⏰ Reportes Programados"
- ⚠️ El botón está en la esquina superior derecha de esa sección

### Si el modal NO se abre:
- ⚠️ Abre DevTools (F12) y busca errores en Console
- ⚠️ Verifica que Bootstrap JS esté cargando
- ⚠️ Refresca la página y vuelve a intentar

---

## 📞 Reporte de Problemas

Si sigues sin ver algo, reporta:

```
REPORTE DE PROBLEMA
===================

1. ¿En qué URL estás?
   [ ] http://127.0.0.1:8000/catalog/
   [ ] http://127.0.0.1:8000/catalog/reports/
   [ ] Otra: _______________

2. ¿Qué NO ves?
   [ ] Tarjeta de reportes en índice
   [ ] Botón "Ver Reportes"
   [ ] Sección "Reportes Programados"
   [ ] Botón "Nuevo Reporte Programado"
   [ ] Modal al hacer clic

3. ¿Qué SÍ ves?
   _________________________________

4. Captura de pantalla:
   [Adjuntar imagen]

5. Errores en consola (F12):
   _________________________________
```

---

**Última actualización:** 2026-01-15  
**Versión:** 1.0  
**Estado:** ✅ Guía Visual Completa
