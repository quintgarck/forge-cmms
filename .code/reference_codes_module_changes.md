# Módulo de Códigos de Referencia - Cambios Realizados

**Fecha:** 2026-02-01  
**Módulo:** Catálogo de Códigos de Referencia (`/catalog/reference-codes/`)

## Resumen

Se realizaron correcciones y mejoras completas al módulo de códigos de referencia, incluyendo soporte para importación Excel, corrección de formularios, mejoras visuales y corrección de bugs críticos.

---

## 1. Soporte para Importación XLS/Excel

**Archivo:** `forge_api/frontend/views/reference_code_views.py`

- Agregada función `read_excel_file()` usando `openpyxl` para leer archivos .xls y .xlsx
- Agregada función `read_csv_file()` con soporte para encoding UTF-8 y Latin-1
- Agregada función `read_import_file()` que detecta formato automáticamente
- Actualizada dependencia en `requirements.txt`: `openpyxl==3.1.2`

**Formatos soportados:**
- CSV (UTF-8, Latin-1)
- Excel (.xls, .xlsx)

---

## 2. Corrección de Mapeo de Campos

**Archivo:** `forge_api/frontend/views/reference_code_views.py`

Implementado diccionario `CATEGORY_FIELD_MAP` que mapea campos por categoría:

```python
CATEGORY_FIELD_MAP = {
    'fuel': {'code_field': 'fuel_code', 'name_field': 'name_es'},
    'transmission': {'code_field': 'transmission_code', 'name_field': 'name_es'},
    'color': {'code_field': 'color_code', 'name_field': 'name_es'},
    'drivetrain': {'code_field': 'drivetrain_code', 'name_field': 'name_es'},
    'condition': {'code_field': 'condition_code', 'name_field': 'name_es'},
    'aspiration': {'code_field': 'aspiration_code', 'name_field': 'name_es'},
}
```

**Problema resuelto:** El API espera campos como `fuel_code`, `name_es` en lugar de `code`, `description` genéricos.

---

## 3. Corrección de URLs

**Archivo:** `forge_api/frontend/urls.py`

- Cambiado `<int:pk>` a `<str:pk>` para soportar códigos alfanuméricos
- Esto permite URLs como `/catalog/reference-codes/fuel/DIESEL10KL/edit/`

---

## 4. Templates Actualizados

### 4.1 Lista de Códigos (`reference_code_list.html`)
- Campos estandarizados: `code.code`, `code.description`, `code.pk`
- Badges con mejor contraste: `bg-light text-dark border`
- Eliminación restringida a usuarios staff (`{% if user.is_staff %}`)
- Iconos de acciones compactos con tooltips

### 4.2 Detalle de Código (`reference_code_detail.html`)
- URLs corregidas usando `code.pk` en lugar de `code.id`
- Badges con estilo `bg-light text-dark` para mejor contraste
- Botón eliminar solo para staff

### 4.3 Formulario de Edición (`reference_code_form.html`)
- **Modal de confirmación reposicionado:** Movido fuera del `card-body`
- **Z-index aumentado a 99999:** Cubre toda la página incluyendo footer
- **Badges del modal corregidos:** `bg-dark text-white` para visibilidad
- **Validación de 10 caracteres:** Antes de mostrar el modal
- **Campo `is_active` removido:** No existe en la base de datos para edición
- **Input editable:** Código puede cambiarse con confirmación vía modal

### 4.4 Importación (`reference_code_import.html`)
- Soporte para archivos CSV y Excel
- Loading spinner en botones durante procesamiento
- Mejor manejo de errores con alertas
- Drag & drop para archivos

---

## 5. Mejoras Visuales

### Modales
- Fondo oscuro semitransparente (`rgba(0, 0, 0, 0.6)`)
- Z-index de 99999 para estar por encima de todo
- Cierre al hacer clic fuera del contenido
- Remoción de backdrop de Bootstrap (que causaba bloqueos)

### Badges
- `bg-light text-dark border` para modo claro/oscuro
- Contraste adecuado en ambos temas

### Loading States
- Spinner en botones durante importación
- Deshabilitación de botones para evitar doble-clic
- Overlay de carga durante operaciones largas

---

## 6. Validaciones

### Frontend (JavaScript)
- Código requerido
- Descripción mínimo 3 caracteres
- Código máximo 10 caracteres (validación de API)
- Confirmación antes de cambiar código existente

### Backend (API)
- Validación de unicidad de códigos
- Mapeo correcto de campos por categoría
- Manejo de errores con mensajes descriptivos

---

## 7. Archivos Modificados

```
forge_api/
├── frontend/views/reference_code_views.py    # Lógica principal
├── frontend/forms/reference_code_forms.py    # Formularios
├── frontend/urls.py                          # Rutas
├── templates/frontend/catalog/
│   ├── reference_code_list.html              # Lista
│   ├── reference_code_detail.html            # Detalle
│   ├── reference_code_form.html              # Formulario
│   ├── reference_code_import.html            # Importación
│   └── reference_code_export.html            # Exportación
└── requirements.txt                          # Dependencias
```

---

## 8. Dependencias Agregadas

```
openpyxl==3.1.2
```

Instalación:
```bash
pip install openpyxl==3.1.2
```

---

## 9. Funcionalidades del Módulo

### Listado (`/catalog/reference-codes/`)
- Ver todos los códigos por categoría
- Filtrado por categoría (combustible, transmisión, color, etc.)
- Búsqueda de códigos
- Paginación

### Creación (`/catalog/reference-codes/create/`)
- Crear nuevo código
- Selección de categoría
- Validación de unicidad

### Edición (`/catalog/reference-codes/{category}/{code}/edit/`)
- Editar descripción
- Cambiar código (con confirmación y actualización en equipos)
- Validación de longitud máxima (10 caracteres)

### Eliminación
- Solo usuarios staff pueden eliminar
- Verificación de uso en equipos

### Importación (`/catalog/reference-codes/import/`)
- Soporte CSV y Excel
- Preview antes de importar
- Manejo de duplicados
- Reporte de errores

### Exportación
- Exportar a CSV
- Exportar a Excel

---

## 10. Notas Técnicas

### Problemas Resueltos
1. Modal bloqueando página → Z-index 99999 + backdrop removido
2. Badges no visibles → `bg-dark text-white`
3. Input no editable → JavaScript de inicialización
4. Error de importación → Mapeo de campos corregido
5. NoReverseMatch → URLs con `<str:pk>`

### Consideraciones
- Los códigos son case-insensitive (se convierten a mayúsculas)
- Máximo 10 caracteres por restricción de API
- Los códigos en uso por equipos no pueden eliminarse
- Cambiar un código actualiza automáticamente todos los equipos que lo usan

---

## Próximos Pasos (Sugeridos)

1. [ ] Agregar paginación en la lista
2. [ ] Implementar búsqueda por descripción
3. [ ] Agregar filtros avanzados
4. [ ] Mejorar manejo de errores en importación masiva
5. [ ] Agregar tests unitarios

---

**Autor:** Kilo Code  
**Versión:** 1.0
