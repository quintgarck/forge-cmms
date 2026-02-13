# Índice de Documentación - Uniformidad Modo Oscuro

**Proyecto**: MovIAx by Sagecores  
**Fecha**: 14 de enero de 2026  
**Tarea**: Aplicar paleta sobria uniforme en modo oscuro

---

## 📚 Documentos Generados

### 1. Resúmenes Ejecutivos

#### 📄 `RESUMEN_EJECUTIVO_UNIFORMIDAD.md`
**Propósito**: Resumen breve para lectura rápida  
**Contenido**:
- Trabajo realizado
- Paleta uniforme aplicada
- Módulos afectados
- Siguiente paso (verificación)

**Leer primero**: ⭐⭐⭐⭐⭐

---

#### 📄 `RESUMEN_UNIFORMIDAD_MODO_OSCURO.md`
**Propósito**: Resumen técnico completo  
**Contenido**:
- Reglas CSS agregadas (con código)
- Elementos sobrescritos
- Paleta de colores detallada
- Módulos afectados
- Troubleshooting
- Estadísticas

**Leer para detalles técnicos**: ⭐⭐⭐⭐

---

### 2. Guías de Verificación

#### 📄 `INSTRUCCIONES_VERIFICACION_UNIFORMIDAD.md`
**Propósito**: Guía paso a paso para verificar los cambios  
**Contenido**:
- Pasos de verificación
- Módulos a verificar (con URLs)
- Checklist de verificación visual
- Inspección con DevTools
- Paleta de referencia
- Troubleshooting detallado

**Leer para verificar**: ⭐⭐⭐⭐⭐

---

#### 📄 `CHECKLIST_VERIFICACION_VISUAL.md`
**Propósito**: Checklist interactivo por módulo  
**Contenido**:
- Checklist por cada módulo
- Criterios de éxito
- Paleta de referencia visual
- Progreso de verificación
- Espacio para notas

**Usar durante verificación**: ⭐⭐⭐⭐⭐

---

### 3. Scripts de Ayuda

#### 📄 `verificar_uniformidad_simple.ps1`
**Propósito**: Script PowerShell para verificación automática  
**Funcionalidad**:
- Verifica que el archivo CSS existe
- Verifica que las reglas están presentes
- Verifica que el servidor Django está corriendo
- Muestra lista de módulos a verificar
- Muestra instrucciones de limpieza de caché
- Muestra paleta de referencia

**Ejecutar**:
```powershell
.\verificar_uniformidad_simple.ps1
```

---

### 4. Archivos Técnicos

#### 📄 `forge_api/static/frontend/css/moviax-theme.css`
**Propósito**: Archivo CSS principal con las reglas de uniformidad  
**Modificaciones**:
- Líneas 2313-2512: Reglas de uniformidad agregadas (~200 líneas)
- Total: 2512 líneas

**NO editar manualmente** - Ya está actualizado

---

## 🗺️ Flujo de Lectura Recomendado

### Para Verificación Rápida:
1. `RESUMEN_EJECUTIVO_UNIFORMIDAD.md` (2 min)
2. `verificar_uniformidad_simple.ps1` (ejecutar)
3. Limpiar caché del navegador
4. Verificar visualmente cada módulo

### Para Verificación Completa:
1. `RESUMEN_EJECUTIVO_UNIFORMIDAD.md` (2 min)
2. `INSTRUCCIONES_VERIFICACION_UNIFORMIDAD.md` (5 min)
3. `verificar_uniformidad_simple.ps1` (ejecutar)
4. `CHECKLIST_VERIFICACION_VISUAL.md` (usar durante verificación)
5. Verificar cada módulo marcando checkboxes

### Para Troubleshooting:
1. `RESUMEN_UNIFORMIDAD_MODO_OSCURO.md` (sección Troubleshooting)
2. `INSTRUCCIONES_VERIFICACION_UNIFORMIDAD.md` (sección Problemas Conocidos)
3. Inspeccionar con DevTools
4. Reportar problemas específicos

---

## 📊 Estructura de Archivos

```
forge-cmms/
├── forge_api/
│   └── static/
│       └── frontend/
│           └── css/
│               └── moviax-theme.css ⭐ (MODIFICADO)
│
├── RESUMEN_EJECUTIVO_UNIFORMIDAD.md ⭐ (NUEVO)
├── RESUMEN_UNIFORMIDAD_MODO_OSCURO.md ⭐ (NUEVO)
├── INSTRUCCIONES_VERIFICACION_UNIFORMIDAD.md ⭐ (NUEVO)
├── CHECKLIST_VERIFICACION_VISUAL.md ⭐ (NUEVO)
├── verificar_uniformidad_simple.ps1 ⭐ (NUEVO)
└── INDICE_DOCUMENTACION_UNIFORMIDAD.md ⭐ (ESTE ARCHIVO)
```

---

## 🎯 Objetivos de la Tarea

### Objetivo Principal
Aplicar la misma paleta sobria del dashboard a TODOS los módulos en modo oscuro.

### Criterios de Éxito
- ✅ Todos los módulos tienen la misma paleta
- ✅ NO hay gradientes visibles en modo oscuro
- ✅ Colores uniformes: `#141B28`, `#1E293B`, `#334155`, `#F8FAFC`
- ✅ Colores de estado sólidos: verde, amarillo, rojo, azul

### Estado Actual
- ✅ Implementación CSS completada
- 🔍 Pendiente: Verificación visual por el usuario

---

## 🚀 Acción Inmediata Requerida

### Paso 1: Limpiar Caché
**CRÍTICO**: El navegador cachea archivos CSS agresivamente.

**Opción A - Hard Refresh**:
- Chrome/Edge: `Ctrl + Shift + R` o `Ctrl + F5`
- Firefox: `Ctrl + Shift + R` ou `Ctrl + F5`

**Opción B - Modo Incógnito**:
- Abrir ventana incógnito/privada
- Navegar a `http://127.0.0.1:8000`

### Paso 2: Ejecutar Script
```powershell
.\verificar_uniformidad_simple.ps1
```

### Paso 3: Verificar Visualmente
1. Cambiar a modo oscuro: `Ctrl + Shift + D`
2. Navegar a cada módulo (ver lista en script)
3. Confirmar que NO hay gradientes
4. Confirmar que todos tienen la misma paleta

### Paso 4: Reportar
- ✅ Si todo está correcto: Confirmar que la tarea está completa
- ❌ Si hay problemas: Reportar módulos específicos con screenshots

---

## 📞 Soporte

Si encuentras problemas durante la verificación:

### Información a Proporcionar:
1. URL específica del módulo
2. Screenshot del elemento con problema
3. Salida de DevTools > Elements > Computed
4. Descripción del problema (gradiente visible, color incorrecto, etc.)

### Archivos de Referencia:
- `RESUMEN_UNIFORMIDAD_MODO_OSCURO.md` (sección Troubleshooting)
- `INSTRUCCIONES_VERIFICACION_UNIFORMIDAD.md` (sección Problemas Conocidos)

---

## 📈 Progreso

```
Implementación CSS:  ✅ 100% Completado
Verificación Visual: 🔍 0% (Pendiente)
Documentación:       ✅ 100% Completado
```

---

## 🎨 Paleta de Referencia Rápida

**Modo Oscuro Uniforme**:

```
Fondos:
  Body/Main:  #141B28  (oscuro mate)
  Cards:      #1E293B  (gris oscuro)
  Headers:    #334155  (gris medio)

Textos:
  Principal:  #F8FAFC  (casi blanco)
  Secundario: #E2E8F0  (gris muy claro)

Estados:
  Success:    #10B981  (verde sólido)
  Warning:    #F59E0B  (amarillo sólido)
  Danger:     #EF4444  (rojo sólido)
  Info:       #60A5FA  (azul sólido)
```

**Regla de Oro**: NO debe haber gradientes visibles en modo oscuro.

---

## ✅ Checklist Final

- [ ] Leer `RESUMEN_EJECUTIVO_UNIFORMIDAD.md`
- [ ] Ejecutar `verificar_uniformidad_simple.ps1`
- [ ] Limpiar caché del navegador
- [ ] Cambiar a modo oscuro
- [ ] Verificar Dashboard (referencia)
- [ ] Verificar Services
- [ ] Verificar OEM Catalog
- [ ] Verificar Catalog
- [ ] Verificar Inventory
- [ ] Verificar Alerts
- [ ] Verificar Technicians
- [ ] Verificar Invoices
- [ ] Confirmar que NO hay gradientes
- [ ] Confirmar que todos tienen la misma paleta
- [ ] Marcar tarea como completada

---

**Fin del Índice**

**Siguiente paso**: Leer `RESUMEN_EJECUTIVO_UNIFORMIDAD.md` y ejecutar `verificar_uniformidad_simple.ps1`
