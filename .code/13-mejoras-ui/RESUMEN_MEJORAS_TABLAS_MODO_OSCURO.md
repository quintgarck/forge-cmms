# Mejoras de Tablas en Modo Oscuro

**Fecha**: 14 de enero de 2026  
**Proyecto**: MovIAx by Sagecores  
**Problema**: Las tablas en modo oscuro no se veían bien (bajo contraste, poca legibilidad)

---

## ✅ Mejoras Aplicadas

Se agregaron **~250 líneas de CSS** específicas para mejorar las tablas en modo oscuro.

**Archivo modificado**:
- `forge_api/static/frontend/css/moviax-theme.css`

---

## 🎨 Mejoras Visuales

### 1. Headers de Tabla
**Antes**: Poco contraste, difícil de distinguir  
**Ahora**:
- Fondo: `#1E293B` (gris oscuro)
- Texto: `#F8FAFC` (casi blanco)
- Borde inferior: `2px solid #60A5FA` (línea azul para destacar)
- Font-weight: 600 (negrita)

```css
[data-theme="dark"] .table thead th {
    background-color: #1E293B !important;
    color: #F8FAFC !important;
    border-bottom: 2px solid #60A5FA !important;
    font-weight: 600 !important;
}
```

### 2. Celdas de Tabla
**Antes**: Texto poco legible, bordes muy marcados  
**Ahora**:
- Texto: `#E2E8F0` (gris muy claro)
- Bordes: `#334155` (más sutiles)
- Padding: `0.75rem` (más espacio)

```css
[data-theme="dark"] .table tbody td {
    border-color: #334155 !important;
    color: #E2E8F0 !important;
    padding: 0.75rem !important;
}
```

### 3. Hover en Filas
**Antes**: Hover poco visible  
**Ahora**:
- Fondo hover: `#334155` (gris medio)
- Texto hover: `#F8FAFC` (más brillante)
- Transición suave: `0.2s ease`
- Cursor: `pointer`

```css
[data-theme="dark"] .table-hover > tbody > tr:hover {
    background-color: #334155 !important;
    cursor: pointer;
    transition: background-color 0.2s ease;
}

[data-theme="dark"] .table-hover > tbody > tr:hover > * {
    color: #F8FAFC !important;
}
```

### 4. Filas Striped (Alternadas)
**Antes**: Contraste muy fuerte  
**Ahora**:
- Filas impares: `rgba(30, 41, 59, 0.5)` (más sutil)
- Filas pares: Transparente
- Mejor legibilidad

```css
[data-theme="dark"] .table-striped > tbody > tr:nth-of-type(odd) {
    background-color: rgba(30, 41, 59, 0.5) !important;
}
```

### 5. Links en Tablas
**Antes**: Color inconsistente  
**Ahora**:
- Color: `#60A5FA` (azul vibrante)
- Hover: `#93C5FD` (azul más claro)
- Underline en hover

```css
[data-theme="dark"] .table a {
    color: #60A5FA !important;
}

[data-theme="dark"] .table a:hover {
    color: #93C5FD !important;
    text-decoration: underline;
}
```

### 6. Badges en Tablas
**Antes**: Poco contraste  
**Ahora**:
- Font-weight: 600
- Padding mejorado: `0.35rem 0.65rem`
- Colores más vibrantes

```css
[data-theme="dark"] .table .badge {
    font-weight: 600 !important;
    padding: 0.35rem 0.65rem !important;
}
```

### 7. Iconos en Tablas
**Antes**: Poco visibles  
**Ahora**:
- Color normal: `#94A3B8` (gris medio)
- Color hover: `#E2E8F0` (gris muy claro)

```css
[data-theme="dark"] .table i,
[data-theme="dark"] .table .bi {
    color: #94A3B8 !important;
}

[data-theme="dark"] .table tr:hover i {
    color: #E2E8F0 !important;
}
```

### 8. Tabla Responsive
**Antes**: Sin estilo  
**Ahora**:
- Borde: `1px solid #475569`
- Border-radius: `0.5rem`
- Scrollbar personalizado (8px, gris)

```css
[data-theme="dark"] .table-responsive {
    border: 1px solid #475569 !important;
    border-radius: 0.5rem !important;
}

[data-theme="dark"] .table-responsive::-webkit-scrollbar {
    height: 8px;
}

[data-theme="dark"] .table-responsive::-webkit-scrollbar-thumb {
    background: #475569;
    border-radius: 4px;
}
```

### 9. Filas con Estados
**Antes**: No había diferenciación  
**Ahora**:
- Success: `rgba(16, 185, 129, 0.1)` (verde translúcido)
- Warning: `rgba(245, 158, 11, 0.1)` (amarillo translúcido)
- Danger: `rgba(239, 68, 68, 0.1)` (rojo translúcido)
- Info: `rgba(96, 165, 250, 0.1)` (azul translúcido)

```css
[data-theme="dark"] .table .table-success {
    background-color: rgba(16, 185, 129, 0.1) !important;
}
```

### 10. Fila Activa/Seleccionada
**Antes**: No había indicador  
**Ahora**:
- Fondo: `rgba(96, 165, 250, 0.15)` (azul translúcido)
- Texto: `#F8FAFC` (casi blanco)

```css
[data-theme="dark"] .table .table-active,
[data-theme="dark"] .table tr.active {
    background-color: rgba(96, 165, 250, 0.15) !important;
}
```

### 11. Formularios en Tablas
**Antes**: Poco visibles  
**Ahora**:
- Checkboxes: Fondo `#1E293B`, checked `#60A5FA`
- Selects: Fondo `#1E293B`, texto `#E2E8F0`
- Inputs: Fondo `#1E293B`, texto `#E2E8F0`
- Font-size: `0.875rem` (más compacto)

```css
[data-theme="dark"] .table .form-check-input:checked {
    background-color: #60A5FA !important;
    border-color: #60A5FA !important;
}
```

### 12. Footer de Tabla
**Antes**: No había estilo  
**Ahora**:
- Fondo: `#1E293B` (gris oscuro)
- Texto: `#F8FAFC` (casi blanco)
- Borde superior: `2px solid #60A5FA` (línea azul)
- Font-weight: 600 (negrita)

```css
[data-theme="dark"] .table tfoot th,
[data-theme="dark"] .table tfoot td {
    background-color: #1E293B !important;
    color: #F8FAFC !important;
    border-top: 2px solid #60A5FA !important;
    font-weight: 600 !important;
}
```

---

## 🎯 Resultado

### Antes:
- ❌ Bajo contraste entre headers y contenido
- ❌ Texto poco legible
- ❌ Hover poco visible
- ❌ Bordes muy marcados
- ❌ Links y badges poco visibles
- ❌ Sin diferenciación de estados

### Después:
- ✅ Alto contraste entre headers y contenido
- ✅ Texto muy legible (`#E2E8F0`)
- ✅ Hover claramente visible (`#334155`)
- ✅ Bordes sutiles (`#334155`)
- ✅ Links vibrantes (`#60A5FA`)
- ✅ Badges con buen contraste
- ✅ Estados claramente diferenciados
- ✅ Línea azul en headers para destacar
- ✅ Scrollbar personalizado
- ✅ Transiciones suaves

---

## 📋 Clases de Tabla Mejoradas

Todas estas clases ahora tienen mejor estilo en modo oscuro:

- `.table` - Tabla básica
- `.table-hover` - Tabla con hover
- `.table-striped` - Tabla con filas alternadas
- `.table-bordered` - Tabla con bordes
- `.table-sm` - Tabla compacta
- `.table-responsive` - Tabla responsive
- `.table-success` - Fila success
- `.table-warning` - Fila warning
- `.table-danger` - Fila danger
- `.table-info` - Fila info
- `.table-active` - Fila activa
- `thead` - Header de tabla
- `tbody` - Body de tabla
- `tfoot` - Footer de tabla

---

## 🚀 Verificación

### Paso 1: Limpiar Caché
**CRÍTICO**: `Ctrl + Shift + R` o `Ctrl + F5`

### Paso 2: Cambiar a Modo Oscuro
`Ctrl + Shift + D`

### Paso 3: Verificar Tablas
Navega a cualquier módulo con tablas y verifica:

- [ ] Headers con línea azul en la parte inferior
- [ ] Texto legible en celdas (`#E2E8F0`)
- [ ] Hover visible y suave
- [ ] Bordes sutiles entre filas
- [ ] Links azules vibrantes
- [ ] Badges con buen contraste
- [ ] Iconos visibles
- [ ] Scrollbar personalizado (si aplica)
- [ ] Estados diferenciados (success, warning, danger, info)

---

## 📊 Módulos con Tablas

Verifica especialmente estos módulos:

1. **Alerts** - `http://127.0.0.1:8000/alerts/`
2. **Technicians** - `http://127.0.0.1:8000/technicians/`
3. **Invoices** - `http://127.0.0.1:8000/invoices/`
4. **Catalog** - `http://127.0.0.1:8000/catalog/`
5. **Inventory** - `http://127.0.0.1:8000/inventory/`
6. **OEM Catalog** - `http://127.0.0.1:8000/oem/`
7. **Services** - `http://127.0.0.1:8000/services/`

---

## 🎨 Paleta de Tablas en Modo Oscuro

```
Headers:        #1E293B  (gris oscuro)
Header Border:  #60A5FA  (azul vibrante - 2px)
Texto Headers:  #F8FAFC  (casi blanco)

Celdas:         Transparente
Texto Celdas:   #E2E8F0  (gris muy claro)
Bordes Celdas:  #334155  (gris medio sutil)

Hover:          #334155  (gris medio)
Texto Hover:    #F8FAFC  (casi blanco)

Striped Odd:    rgba(30, 41, 59, 0.5)  (gris translúcido)
Striped Even:   Transparente

Links:          #60A5FA  (azul vibrante)
Links Hover:    #93C5FD  (azul claro)

Iconos:         #94A3B8  (gris medio)
Iconos Hover:   #E2E8F0  (gris muy claro)

Footer:         #1E293B  (gris oscuro)
Footer Border:  #60A5FA  (azul vibrante - 2px)
Texto Footer:   #F8FAFC  (casi blanco)
```

---

## ✅ Checklist de Verificación

- [ ] Limpiar caché del navegador
- [ ] Cambiar a modo oscuro
- [ ] Verificar headers con línea azul
- [ ] Verificar texto legible en celdas
- [ ] Verificar hover visible
- [ ] Verificar bordes sutiles
- [ ] Verificar links azules
- [ ] Verificar badges contrastados
- [ ] Verificar iconos visibles
- [ ] Verificar scrollbar personalizado
- [ ] Verificar estados diferenciados
- [ ] Verificar formularios en tablas
- [ ] Confirmar que todas las tablas se ven bien

---

**Fin del Resumen**

Las tablas ahora tienen excelente legibilidad y contraste en modo oscuro, con una línea azul distintiva en los headers y hover claramente visible.
