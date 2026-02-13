# Checklist de Verificación Visual - Modo Oscuro Uniforme

**Fecha**: 14 de enero de 2026  
**Proyecto**: MovIAx by Sagecores

---

## 🚀 Antes de Empezar

### Paso 1: Limpiar Caché
- [ ] Hard Refresh: `Ctrl + Shift + R` o `Ctrl + F5`
- [ ] O abrir ventana incógnito/privada

### Paso 2: Cambiar a Modo Oscuro
- [ ] Presionar `Ctrl + Shift + D`
- [ ] O hacer clic en el botón de tema en el navbar
- [ ] Confirmar que el navbar cambió a `#0F172A` (oscuro)

---

## 📋 Verificación por Módulo

### ✅ Dashboard (Referencia)
**URL**: `http://127.0.0.1:8000/dashboard/`

- [ ] Fondo principal: `#141B28` (oscuro mate)
- [ ] Cards: `#1E293B` (gris oscuro)
- [ ] Headers de cards: `#334155` (gris medio) - **SIN GRADIENTES**
- [ ] Texto principal: `#F8FAFC` (casi blanco)
- [ ] Navbar: `#0F172A` (oscuro profundo)
- [ ] NO hay gradientes visibles

**Estado**: ✅ Referencia correcta

---

### 🔍 Services
**URL**: `http://127.0.0.1:8000/services/`

#### Service Checklist Interactive
- [ ] Header del checklist: `#1E293B` - **SIN GRADIENTE**
- [ ] Cards de items: `#1E293B`
- [ ] Progress bars: Colores sólidos (verde, amarillo, rojo)
- [ ] NO hay gradientes azules/morados

#### Workorder Timeline
- [ ] Timeline container: Fondo `#1E293B`
- [ ] Timeline line: `#334155` (línea sólida)
- [ ] Event cards: `#1E293B`
- [ ] NO hay gradientes en eventos

#### Flat Rate Calculator
- [ ] Calculator header: `#1E293B` - **SIN GRADIENTE**
- [ ] Input areas: `#1E293B`
- [ ] Result cards: `#1E293B`
- [ ] NO hay gradientes en resultados

**Estado**: 🔍 Verificar

---

### 🔍 OEM Catalog
**URL**: `http://127.0.0.1:8000/oem/`

#### Part Comparator
- [ ] Comparator header: `#1E293B` - **SIN GRADIENTE**
- [ ] Part cards: `#1E293B`
- [ ] Comparison table: Fondo uniforme
- [ ] NO hay gradientes en headers

#### Equivalence Management
- [ ] Equivalence header: `#1E293B` - **SIN GRADIENTE**
- [ ] Equivalence cards: `#1E293B`
- [ ] Status badges: Colores sólidos
- [ ] NO hay gradientes en formularios

#### Catalog Search
- [ ] Catalog header: `#1E293B` - **SIN GRADIENTE**
- [ ] Search results: Fondo uniforme
- [ ] Filter panels: `#1E293B`
- [ ] NO hay gradientes en paneles

#### Brand Management
- [ ] Brand header: `#1E293B` - **SIN GRADIENTE**
- [ ] Brand cards: `#1E293B`
- [ ] Logo placeholders: `#334155`
- [ ] NO hay gradientes en cards

**Estado**: 🔍 Verificar

---

### 🔍 Catalog
**URL**: `http://127.0.0.1:8000/catalog/`

#### Equipment Type Form
- [ ] Form header: `#1E293B` - **SIN GRADIENTE**
- [ ] Form fields: Fondo `#0F172A`
- [ ] Submit buttons: Colores sólidos
- [ ] NO hay gradientes en formularios

#### Equipment Type List
- [ ] List header: `#1E293B` - **SIN GRADIENTE**
- [ ] Table rows: Fondo uniforme
- [ ] Action buttons: Colores sólidos
- [ ] NO hay gradientes en tabla

#### Supplier Advanced List
- [ ] Supplier header: `#1E293B` - **SIN GRADIENTE**
- [ ] Supplier cards: `#1E293B`
- [ ] Filter sections: Fondo uniforme
- [ ] NO hay gradientes en filtros

#### Currency List
- [ ] Currency header: `#1E293B` - **SIN GRADIENTE**
- [ ] Currency table: Fondo uniforme
- [ ] Status indicators: Colores sólidos
- [ ] NO hay gradientes en tabla

**Estado**: 🔍 Verificar

---

### 🔍 Inventory
**URL**: `http://127.0.0.1:8000/inventory/`

#### Warehouse Advanced List
- [ ] Warehouse header: `#1E293B` - **SIN GRADIENTE**
- [ ] Warehouse cards: `#1E293B`
- [ ] Stock indicators: Colores sólidos
- [ ] NO hay gradientes en cards

#### Product List
- [ ] Product cards: `#1E293B`
- [ ] Product images: Bordes uniformes
- [ ] Stock badges: Colores sólidos
- [ ] NO hay gradientes en productos

#### Stock Management
- [ ] Stock header: `#1E293B` - **SIN GRADIENTE**
- [ ] Stock table: Fondo uniforme
- [ ] Level indicators: Colores sólidos
- [ ] NO hay gradientes en indicadores

**Estado**: 🔍 Verificar

---

### 🔍 Alerts
**URL**: `http://127.0.0.1:8000/alerts/`

- [ ] Alert cards: `#1E293B`
- [ ] Alert headers: `#334155` - **SIN GRADIENTES**
- [ ] Priority badges: Colores sólidos (verde, amarillo, rojo)
- [ ] Alert icons: Colores sólidos
- [ ] NO hay gradientes en alerts

**Estado**: 🔍 Verificar

---

### 🔍 Technicians
**URL**: `http://127.0.0.1:8000/technicians/`

- [ ] Technician cards: `#1E293B`
- [ ] Profile headers: `#334155` - **SIN GRADIENTES**
- [ ] Status badges: Colores sólidos
- [ ] Performance indicators: Colores sólidos
- [ ] NO hay gradientes en perfiles

**Estado**: 🔍 Verificar

---

### 🔍 Invoices
**URL**: `http://127.0.0.1:8000/invoices/`

- [ ] Invoice cards: `#1E293B`
- [ ] Invoice headers: `#334155` - **SIN GRADIENTES**
- [ ] Status badges: Colores sólidos
- [ ] Amount displays: Fondo uniforme
- [ ] NO hay gradientes en facturas

**Estado**: 🔍 Verificar

---

## 🎨 Paleta de Referencia

### Fondos
```
Body/Main:  #141B28  ████████  (oscuro mate)
Cards:      #1E293B  ████████  (gris oscuro)
Headers:    #334155  ████████  (gris medio)
Hover:      #475569  ████████  (gris claro)
```

### Textos
```
Principal:   #F8FAFC  ████████  (casi blanco)
Secundario:  #E2E8F0  ████████  (gris muy claro)
Atenuado:    #94A3B8  ████████  (gris medio)
```

### Estados (Sólidos)
```
Success:  #10B981  ████████  (verde)
Warning:  #F59E0B  ████████  (amarillo)
Danger:   #EF4444  ████████  (rojo)
Info:     #60A5FA  ████████  (azul)
Primary:  #60A5FA  ████████  (azul vibrante)
```

---

## 🔍 Inspección con DevTools

Si encuentras un gradiente o color inconsistente:

1. **Abrir DevTools**: `F12`
2. **Seleccionar elemento**: Click en el inspector
3. **Ver "Computed"**: Buscar `background` o `background-color`
4. **Anotar**:
   - URL de la página
   - Selector CSS del elemento
   - Valor actual del background
   - Screenshot del elemento

---

## ✅ Criterios de Éxito

### Todos los módulos deben cumplir:

- [ ] **Fondo principal**: `#141B28` (oscuro mate)
- [ ] **Cards**: `#1E293B` (gris oscuro)
- [ ] **Headers**: `#334155` (gris medio) - **SIN GRADIENTES**
- [ ] **Texto principal**: `#F8FAFC` (casi blanco)
- [ ] **Bordes**: `#475569` (gris medio)
- [ ] **Colores de estado**: Sólidos (sin gradientes)
- [ ] **Consistencia**: Todos los módulos se ven igual

### NO debe haber:

- [ ] ❌ Gradientes visibles en headers
- [ ] ❌ Gradientes en cards o contenedores
- [ ] ❌ Colores inconsistentes entre módulos
- [ ] ❌ Fondos con tonos diferentes al dashboard
- [ ] ❌ Texto ilegible por falta de contraste

---

## 📊 Progreso de Verificación

```
Dashboard:    ✅ Referencia correcta
Services:     🔍 Pendiente de verificar
OEM Catalog:  🔍 Pendiente de verificar
Catalog:      🔍 Pendiente de verificar
Inventory:    🔍 Pendiente de verificar
Alerts:       🔍 Pendiente de verificar
Technicians:  🔍 Pendiente de verificar
Invoices:     🔍 Pendiente de verificar
```

**Total**: 1/8 módulos verificados

---

## 🎯 Resultado Final

Una vez completada la verificación:

### ✅ Si TODO está uniforme:
- Marcar todos los checkboxes
- Confirmar que la tarea está completa
- Documentar cualquier observación

### ❌ Si hay problemas:
- Anotar los módulos con problemas
- Tomar screenshots de los elementos inconsistentes
- Reportar los selectores CSS específicos
- Proporcionar la salida de DevTools

---

## 📝 Notas de Verificación

Usa este espacio para anotar observaciones:

```
Módulo: _______________
Problema: _______________
Selector CSS: _______________
Screenshot: _______________

Módulo: _______________
Problema: _______________
Selector CSS: _______________
Screenshot: _______________
```

---

**Fin del Checklist**

**Recuerda**: La clave es que TODOS los módulos se vean **exactamente igual** al dashboard en modo oscuro - sobrio, relajado, combinado y fresco.
