# Instrucciones de Verificación - Uniformidad de Colores Modo Oscuro

## Estado Actual
✅ **Reglas CSS agregadas** - Se agregaron ~200 líneas de CSS al final de `moviax-theme.css` para sobrescribir todos los gradientes y colores personalizados en modo oscuro.

## Pasos de Verificación

### 1. Limpiar Caché del Navegador
**CRÍTICO**: Los archivos CSS se cachean agresivamente. Debes limpiar el caché:

#### Opción A - Hard Refresh (Recomendado)
- **Chrome/Edge**: `Ctrl + Shift + R` o `Ctrl + F5`
- **Firefox**: `Ctrl + Shift + R` o `Ctrl + F5`

#### Opción B - Limpiar Caché Completo
1. Abrir DevTools: `F12`
2. Click derecho en el botón de refresh (mientras DevTools está abierto)
3. Seleccionar "Empty Cache and Hard Reload"

#### Opción C - Modo Incógnito
- Abrir una ventana de incógnito/privada
- Navegar a `http://127.0.0.1:8000`

### 2. Verificar Servidor Django
Asegúrate de que el servidor Django esté corriendo:

```cmd
python manage.py runserver
```

### 3. Módulos a Verificar en Modo Oscuro

Cambia al modo oscuro con `Ctrl + Shift + D` y verifica estos módulos:

#### ✅ Dashboard
- URL: `http://127.0.0.1:8000/dashboard/`
- **Esperado**: Fondo `#141B28`, cards `#1E293B`, headers `#334155`
- **NO debe haber**: Gradientes visibles

#### 🔍 Services
- URL: `http://127.0.0.1:8000/services/`
- **Archivos afectados**:
  - `service_checklist_interactive.html`
  - `workorder_timeline.html`
  - `flat_rate_calculator.html`
- **Esperado**: Misma paleta sobria que dashboard
- **NO debe haber**: Gradientes azules/morados en headers

#### 🔍 OEM Catalog
- URL: `http://127.0.0.1:8000/oem/`
- **Archivos afectados**:
  - `part_comparator.html`
  - `equivalence_management.html`
  - `catalog_search.html`
  - `brand_management.html`
- **Esperado**: Headers con color sólido `#1E293B`
- **NO debe haber**: Gradientes en comparadores o formularios

#### 🔍 Catalog
- URL: `http://127.0.0.1:8000/catalog/`
- **Archivos afectados**:
  - `equipment_type_form.html`
  - `equipment_type_list.html`
  - `supplier_advanced_list.html`
  - `currency_list.html`
- **Esperado**: Formularios con fondo `#1E293B`
- **NO debe haber**: Gradientes en headers de formularios

#### 🔍 Inventory
- URL: `http://127.0.0.1:8000/inventory/`
- **Archivos afectados**:
  - `warehouse_advanced_list.html`
- **Esperado**: Listas con fondo uniforme
- **NO debe haber**: Gradientes en cards de warehouse

#### 🔍 Alerts
- URL: `http://127.0.0.1:8000/alerts/`
- **Esperado**: Paleta uniforme
- **NO debe haber**: Colores inconsistentes

#### 🔍 Technicians
- URL: `http://127.0.0.1:8000/technicians/`
- **Esperado**: Paleta uniforme
- **NO debe haber**: Colores inconsistentes

#### 🔍 Invoices
- URL: `http://127.0.0.1:8000/invoices/`
- **Esperado**: Paleta uniforme
- **NO debe haber**: Colores inconsistentes

### 4. Checklist de Verificación Visual

Para cada módulo, verifica:

- [ ] **Fondo principal**: `#141B28` (oscuro mate)
- [ ] **Cards**: `#1E293B` (gris oscuro)
- [ ] **Headers**: `#334155` (gris medio) - **SIN GRADIENTES**
- [ ] **Texto principal**: `#F8FAFC` (casi blanco)
- [ ] **Texto secundario**: `#E2E8F0` (gris muy claro)
- [ ] **Bordes**: `#475569` (gris medio)
- [ ] **NO hay gradientes visibles** en ningún elemento
- [ ] **Colores de estado** son sólidos:
  - Success: `#10B981` (verde)
  - Warning: `#F59E0B` (amarillo)
  - Danger: `#EF4444` (rojo)
  - Info: `#60A5FA` (azul)

### 5. Inspeccionar con DevTools

Si ves algún gradiente o color inconsistente:

1. Abrir DevTools (`F12`)
2. Seleccionar el elemento con el inspector
3. Verificar en la pestaña "Computed" el valor de `background`
4. Si tiene un gradiente, buscar en "Styles" qué regla lo está aplicando
5. Reportar el selector CSS específico

### 6. Paleta de Referencia

**Modo Oscuro Uniforme (sin gradientes):**

```css
/* Fondos */
--moviax-bg-primary: #1E293B      /* Cards, modales, formularios */
--moviax-bg-secondary: #0F172A    /* Fondo principal de página */
--moviax-bg-tertiary: #334155     /* Headers, footers, áreas destacadas */
--moviax-bg-hover: #475569        /* Estados hover */

/* Body específico */
body: #141B28                     /* Tono intermedio mate */

/* Textos */
--moviax-text-primary: #F8FAFC    /* Texto principal */
--moviax-text-secondary: #E2E8F0  /* Texto secundario */
--moviax-text-muted: #94A3B8      /* Texto atenuado */

/* Bordes */
--moviax-border: #475569

/* Estados (sólidos) */
--moviax-success: #10B981
--moviax-warning: #F59E0B
--moviax-danger: #EF4444
--moviax-info: #60A5FA
--moviax-primary: #60A5FA
```

## Reglas CSS Agregadas

Se agregaron las siguientes reglas al final de `moviax-theme.css`:

1. **Headers personalizados** (`.checklist-header`, `.comparator-header`, etc.)
   - Sobrescritos a `#1E293B` sólido

2. **Performance badges** (`.performance-excellent`, `.performance-good`, etc.)
   - Colores sólidos sin gradientes

3. **Timeline y progress bars**
   - Colores sólidos `#334155`

4. **Status badges** (`.status-new`, `.status-duplicate`, etc.)
   - Colores sólidos de estado

5. **Upload areas** (`.upload-area`)
   - Fondo `#1E293B` con hover `#334155`

6. **Steppers** (`.bs-stepper-circle`)
   - Colores sólidos para estados

7. **Regla general de sobrescritura**:
   ```css
   [data-theme="dark"] [style*="background: linear-gradient"] {
       background: #1E293B !important;
   }
   ```

## Problemas Conocidos

Si después de limpiar el caché TODAVÍA ves gradientes:

1. **Estilos inline en HTML**: Algunos archivos HTML tienen estilos `style="background: linear-gradient(...)"` directamente en el HTML
2. **JavaScript dinámico**: Algunos scripts pueden estar aplicando estilos dinámicamente
3. **Caché del servidor**: Django puede estar cacheando archivos estáticos

### Solución para estilos inline:
Si identificas archivos HTML con gradientes inline, necesitaremos editarlos manualmente para remover los estilos inline.

## Siguiente Paso

Una vez que hayas verificado visualmente todos los módulos:

1. **Si TODO está uniforme** ✅
   - Confirmar que la tarea está completa
   - Documentar el resultado

2. **Si hay gradientes persistentes** ❌
   - Identificar los archivos HTML específicos
   - Reportar los selectores CSS que no están siendo sobrescritos
   - Ajustar las reglas CSS o editar los archivos HTML

## Comandos Útiles

```cmd
# Reiniciar servidor Django
python manage.py runserver

# Limpiar archivos estáticos compilados (si usas collectstatic)
python manage.py collectstatic --clear --noinput

# Ver archivos CSS cargados
# En DevTools > Network > Filter: CSS
```

## Contacto

Si encuentras problemas, proporciona:
- URL específica donde ves el problema
- Screenshot del elemento con gradiente
- Salida de DevTools > Elements > Computed para ese elemento
