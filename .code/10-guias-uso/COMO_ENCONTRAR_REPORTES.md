# ¿Cómo Encontrar los Reportes? (Guía Simple)

**Última actualización:** 2026-01-15

---

## 🎯 En 3 Pasos Simples

### Paso 1: Ve a la página de catálogos
```
http://127.0.0.1:8000/catalog/
```

### Paso 2: Busca la tarjeta NEGRA
- Es la **última tarjeta** de la página
- Tiene **fondo negro**
- Dice **"Estadísticas y Reportes"**
- Tiene un botón que dice **"Ver Reportes"**

### Paso 3: Haz clic en "Ver Reportes"
- Te llevará a la página de reportes
- Ahí verás gráficos, estadísticas y más

---

## 🔍 ¿Dónde está el botón para programar reportes?

### Una vez en la página de reportes:

1. **Haz scroll hasta el FINAL** de la página (desplázate hacia abajo)
2. Busca una sección que dice **"⏰ Reportes Programados"**
3. En esa sección, en la **esquina superior derecha**, hay un botón **AZUL**
4. El botón dice **"➕ Nuevo Reporte Programado"**
5. **Haz clic** en ese botón
6. Se abrirá una **ventana emergente** (modal) con un formulario

---

## 📍 Diagrama Visual

```
PASO 1: Ir a /catalog/
┌─────────────────────────────────────┐
│  Gestión de Catálogos               │
├─────────────────────────────────────┤
│                                     │
│  [Tipos]  [Taxonomía]  [Códigos]   │
│                                     │
│  [Monedas] [Proveedores] [REPORTES]│ ← Esta es NEGRA
│                           ↓         │
│                    [Ver Reportes]   │ ← HAZ CLIC AQUÍ
└─────────────────────────────────────┘


PASO 2: En /catalog/reports/
┌─────────────────────────────────────┐
│  📊 Reportes de Catálogo            │
│  [Filtros]                          │
│  [Estadísticas]                     │
│  [Gráficos]                         │
│  [Análisis]                         │
│                                     │
│  ⏰ Reportes Programados            │
│              [+ Nuevo Reporte] ← AQUÍ (botón azul)
│  ─────────────────────────────────  │
│  Tabla...                           │
└─────────────────────────────────────┘
         ↓ HAZ CLIC
         ↓
┌─────────────────────────────────────┐
│  📅 Programar Nuevo Reporte    [X]  │
│  ─────────────────────────────────  │
│  [Formulario con 7 campos]          │
│  [Guardar]                          │
└─────────────────────────────────────┘
```

---

## ❓ Preguntas Frecuentes

### P: No veo la tarjeta negra
**R:** Haz scroll hacia abajo, es la última tarjeta de la página

### P: No veo el botón azul
**R:** Tienes que hacer scroll hasta el FINAL de la página de reportes

### P: El modal no se abre
**R:** Presiona F5 para refrescar la página y vuelve a intentar

### P: ¿Funciona guardar reportes?
**R:** El formulario funciona, pero los reportes NO se guardan en la base de datos (backend pendiente)

---

## ✅ Checklist Rápido

- [ ] Abrí http://127.0.0.1:8000/catalog/
- [ ] Vi la tarjeta negra "Estadísticas y Reportes"
- [ ] Hice clic en "Ver Reportes"
- [ ] Llegué a /catalog/reports/
- [ ] Hice scroll hasta el final
- [ ] Vi el botón azul "Nuevo Reporte Programado"
- [ ] Hice clic en el botón azul
- [ ] Se abrió el modal con el formulario

**Si marcaste todo:** ✅ ¡Perfecto! Todo funciona

**Si falta algo:** Lee `RESUMEN_SITUACION_REPORTES.md` para más ayuda

---

## 🚀 Siguiente Paso

Una vez que verifiques que todo funciona, decide:

1. **Implementar backend** para que los reportes se guarden de verdad
2. **Continuar con Tarea 4** (Administración de Monedas)

---

**¿Necesitas más ayuda?**  
Lee: `INDICE_DOCUMENTACION_REPORTES.md` para ver todos los documentos disponibles

---

**Estado:** ✅ Guía Simple Completa
