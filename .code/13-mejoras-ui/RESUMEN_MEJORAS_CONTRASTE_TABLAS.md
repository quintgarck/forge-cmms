# Mejoras de Contraste en Tablas - Modo Oscuro

**Fecha**: 14 de enero de 2026  
**Problema**: El contenido de las tablas no se veía bien SIN hover en modo oscuro

---

## ✅ Mejoras Aplicadas

### Problema Identificado
Las tablas solo se veían bien cuando se pasaba el mouse sobre ellas (hover), pero el contenido era difícil de leer en estado normal sin hover.

### Solución Implementada
Se mejoraron los colores base de las tablas para que sean legibles **SIN necesidad de hover**.

---

## 🎨 Cambios Específicos

### 1. Texto General de Tablas
**Antes**: `#E2E8F0` (gris muy claro)  
**Ahora**: `#F8FAFC` (casi blanco) ⭐

```css
[data-theme="dark"] .table {
    color: #F8FAFC !important; /* Más brillante */
}
```

### 2. Celdas de Tabla (tbody td)
**Antes**: Sin fondo, bordes `#334155`  
**Ahora**: 
- Fondo: `rgba(30, 41, 59, 0.3)` (fondo sutil para mejor legibilidad)
- Bordes: `#475569` (más visibles)
- Texto: `#F8FAFC` (más brillante)

```css
[data-theme="dark"] .table tbody td {
    background-color: rgba(30, 41, 59, 0.3) !important;
    border-color: #475569 !important;
    color: #F8FAFC !important;
}
```

### 3. Filas de Tabla (tbody tr)
**Nuevo**: Fondo base muy sutil

```css
[data-theme="dark"] .table tbody tr {
    background-color: rgba(30, 41, 59, 0.2) !important;
    border-bottom: 1px solid #475569; /* Bordes más visibles */
}
```

### 4. Hover Mejorado
**Antes**: `#334155` (gris medio)  
**Ahora**: `#475569` (gris más claro) + texto blanco puro

```css
[data-theme="dark"] .table-hover > tbody > tr:hover {
    background-color: #475569 !important; /* MUY visible */
}

[data-theme="dark"] .table-hover > tbody > tr:hover > * {
    color: #FFFFFF !important; /* Blanco puro */
    font-weight: 500 !important;
}
```

### 5. Filas Striped (Alternadas)
**Antes**: `rgba(30, 41, 59, 0.5)` (impares), transparente (pares)  
**Ahora**: 
- Impares: `rgba(30, 41, 59, 0.6)` (más visible)
- Pares: `rgba(30, 41, 59, 0.2)` (fondo sutil)

```css
[data-theme="dark"] .table-striped > tbody > tr:nth-of-type(odd) {
    background-color: rgba(30, 41, 59, 0.6) !important;
}

[data-theme="dark"] .table-striped > tbody > tr:nth-of-type(even) {
    background-color: rgba(30, 41, 59, 0.2) !important;
}
```

### 6. Links en Tablas
**Antes**: `#60A5FA`  
**Ahora**: `#93C5FD` (más brillante) + font-weight 500

```css
[data-theme="dark"] .table a {
    color: #93C5FD !important;
    font-weight: 500 !important;
}

[data-theme="dark"] .table a:hover {
    color: #BFDBFE !important; /* Aún más brillante */
}
```

### 7. Iconos en Tablas
**Antes**: `#94A3B8` (gris medio)  
**Ahora**: `#CBD5E1` (gris muy claro)

```css
[data-theme="dark"] .table i,
[data-theme="dark"] .table .bi {
    color: #CBD5E1 !important;
}

[data-theme="dark"] .table tr:hover i {
    color: #FFFFFF !important; /* Blanco puro en hover */
}
```

### 8. Texto de Colores en Tablas
**Mejorados todos los colores de estado**:

```css
[data-theme="dark"] .table .text-muted {
    color: #CBD5E1 !important; /* Más brillante */
}

[data-theme="dark"] .table .text-success {
    color: #4ADE80 !important; /* Verde más brillante */
    font-weight: 500 !important;
}

[data-theme="dark"] .table .text-warning {
    color: #FCD34D !important; /* Amarillo más brillante */
    font-weight: 500 !important;
}

[data-theme="dark"] .table .text-danger {
    color: #FCA5A5 !important; /* Rojo más brillante */
    font-weight: 500 !important;
}

[data-theme="dark"] .table .text-info {
    color: #93C5FD !important; /* Azul más brillante */
    font-weight: 500 !important;
}
```

### 9. Badges en Tablas
**Antes**: `#475569`  
**Ahora**: `#64748B` (más brillante)

```css
[data-theme="dark"] .table .badge.bg-light {
    background-color: #64748B !important;
    color: #FFFFFF !important;
}
```

---

## 📊 Comparativa Visual

### Antes (Problema):
- ❌ Texto `#E2E8F0` - poco visible sin hover
- ❌ Sin fondo en celdas - bajo contraste
- ❌ Bordes `#334155` - poco visibles
- ❌ Links `#60A5FA` - poco brillantes
- ❌ Iconos `#94A3B8` - poco visibles
- ❌ Solo legible con hover

### Ahora (Solución):
- ✅ Texto `#F8FAFC` - muy visible sin hover
- ✅ Fondo sutil en celdas - mejor contraste
- ✅ Bordes `#475569` - más visibles
- ✅ Links `#93C5FD` - más brillantes
- ✅ Iconos `#CBD5E1` - más visibles
- ✅ **Legible SIN hover** ⭐
- ✅ Hover aún más visible (`#475569` + blanco puro)

---

## 🎯 Resultado

### Estado Normal (SIN hover):
- Texto: `#F8FAFC` (casi blanco) - **MUY LEGIBLE**
- Fondo: `rgba(30, 41, 59, 0.3)` - **CONTRASTE SUTIL**
- Bordes: `#475569` - **VISIBLES**
- Links: `#93C5FD` - **BRILLANTES**
- Iconos: `#CBD5E1` - **VISIBLES**

### Estado Hover:
- Fondo: `#475569` - **MUY VISIBLE**
- Texto: `#FFFFFF` (blanco puro) - **MÁXIMA LEGIBILIDAD**
- Font-weight: 500 - **DESTACADO**

---

## 🚀 Verificación

### CRÍTICO: Limpiar Caché
`Ctrl + Shift + R` o `Ctrl + F5`

### Cambiar a Modo Oscuro
`Ctrl + Shift + D`

### Verificar Tablas SIN Hover
Navega a cualquier módulo con tablas y verifica **SIN pasar el mouse**:

- [ ] Texto muy legible (`#F8FAFC`)
- [ ] Fondo sutil en celdas
- [ ] Bordes visibles entre filas
- [ ] Links azules brillantes
- [ ] Iconos visibles
- [ ] Colores de estado brillantes
- [ ] **TODO legible sin necesidad de hover** ⭐

### Verificar Hover
Pasa el mouse sobre una fila y verifica:

- [ ] Fondo `#475569` muy visible
- [ ] Texto blanco puro
- [ ] Iconos blancos puros
- [ ] Transición suave

---

## 📋 Paleta de Colores Actualizada

### Estado Normal (SIN hover):
```
Texto General:    #F8FAFC  (casi blanco)
Fondo Celdas:     rgba(30, 41, 59, 0.3)  (sutil)
Fondo Filas:      rgba(30, 41, 59, 0.2)  (muy sutil)
Bordes:           #475569  (visibles)
Links:            #93C5FD  (brillante)
Iconos:           #CBD5E1  (visibles)
Text-muted:       #CBD5E1  (brillante)
Text-success:     #4ADE80  (verde brillante)
Text-warning:     #FCD34D  (amarillo brillante)
Text-danger:      #FCA5A5  (rojo brillante)
Text-info:        #93C5FD  (azul brillante)
```

### Estado Hover:
```
Fondo:            #475569  (gris claro)
Texto:            #FFFFFF  (blanco puro)
Iconos:           #FFFFFF  (blanco puro)
Links:            #BFDBFE  (azul muy brillante)
Font-weight:      500  (destacado)
```

### Striped (Alternadas):
```
Filas Impares:    rgba(30, 41, 59, 0.6)  (visible)
Filas Pares:      rgba(30, 41, 59, 0.2)  (sutil)
```

---

## ✅ Checklist Final

- [ ] Limpiar caché del navegador
- [ ] Cambiar a modo oscuro
- [ ] Verificar tabla SIN hover - texto legible
- [ ] Verificar tabla SIN hover - fondo sutil visible
- [ ] Verificar tabla SIN hover - bordes visibles
- [ ] Verificar tabla SIN hover - links brillantes
- [ ] Verificar tabla SIN hover - iconos visibles
- [ ] Verificar hover - fondo muy visible
- [ ] Verificar hover - texto blanco puro
- [ ] Confirmar que TODO es legible sin hover

---

**Fin del Resumen**

**Resultado**: Las tablas ahora son **completamente legibles SIN necesidad de hover**, con texto brillante (`#F8FAFC`), fondo sutil, y bordes visibles. El hover proporciona aún más contraste con fondo `#475569` y texto blanco puro. 🎉
