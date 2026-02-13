# Diseño - Completación Frontend Catálogos y Servicios ForgeDB

## Overview

Este documento especifica el diseño técnico para completar las funcionalidades faltantes del frontend de ForgeDB, enfocándose en los nodos CATÁLOGOS y SERVICIOS. El diseño se basa en la arquitectura existente de Django Templates + Bootstrap 5 + Chart.js, extendiendo las capacidades actuales con CRUD completo y funcionalidades avanzadas.

## Architecture

### Arquitectura General del Sistema
```
┌─────────────────────────────────────────────────────────┐
│                 FRONTEND EXPANDIDO                      │
├─────────────────────────────────────────────────────────┤
│  CATÁLOGOS COMPLETOS                                    │
│  ├── Tipos de Equipo (CRUD + Validaciones)             │
│  ├── Taxonomía (Jerarquía + Navegación)                │
│  ├── Códigos Standard (Gestión + Import/Export)        │
│  └── Monedas (Tasas + Conversiones)                    │
├─────────────────────────────────────────────────────────┤
│  SERVICIOS AVANZADOS                                    │
│  ├── Dashboard Servicios (KPIs + Analytics)            │
│  └── Calculadora Tarifas (Cotizaciones + PDF)          │
├─────────────────────────────────────────────────────────┤
│  INFRAESTRUCTURA COMÚN                                 │
│  ├── Formularios Dinámicos                             │
│  ├── Validaciones Client-Side                          │
│  ├── Navegación Contextual                             │
│  └── Responsive Design                                 │
└─────────────────────────────────────────────────────────┘
```

### Patrón de Arquitectura por Módulo
```
Cada Módulo de Catálogo/Servicio:
├── Views (Django Class-Based Views)
│   ├── ListView (con paginación y filtros)
│   ├── CreateView (formularios validados)
│   ├── UpdateView (pre-población de datos)
│   ├── DetailView (información completa)
│   └── DeleteView (con verificación de dependencias)
├── Forms (Django Forms con validación)
│   ├── ModelForm principal
│   ├── Validaciones custom
│   └── Widgets especializados
├── Templates (Bootstrap 5 responsive)
│   ├── list.html (tabla + filtros)
│   ├── form.html (crear/editar)
│   ├── detail.html (vista completa)
│   └── confirm_delete.html
└── JavaScript (funcionalidad interactiva)
    ├── Validación en tiempo real
    ├── Búsqueda dinámica
    └── Interacciones AJAX
```

## Components and Interfaces

### 1. Módulo Tipos de Equipo

#### Componentes Principales
- **EquipmentTypeListView**: Lista paginada con filtros
- **EquipmentTypeCreateView**: Formulario de creación
- **EquipmentTypeUpdateView**: Formulario de edición
- **EquipmentTypeDetailView**: Vista detallada
- **EquipmentTypeDeleteView**: Eliminación con validaciones

#### Interfaces de Usuario
```html
<!-- Lista de Tipos de Equipo -->
<div class="equipment-type-list">
  <div class="list-header">
    <h2>Tipos de Equipo</h2>
    <button class="btn btn-primary" data-action="create">Nuevo Tipo</button>
  </div>
  <div class="filters-section">
    <input type="search" placeholder="Buscar tipos..." class="form-control">
    <select class="form-select" data-filter="category">
      <option value="">Todas las categorías</option>
    </select>
  </div>
  <div class="table-responsive">
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Código</th>
          <th>Nombre</th>
          <th>Categoría</th>
          <th>Estado</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody id="equipment-types-tbody">
        <!-- Datos dinámicos -->
      </tbody>
    </table>
  </div>
  <nav class="pagination-nav">
    <!-- Paginación Bootstrap -->
  </nav>
</div>
```

#### API Integration
```python
# Endpoints utilizados
GET /api/v1/catalog/equipment-types/          # Lista
POST /api/v1/catalog/equipment-types/         # Crear
GET /api/v1/catalog/equipment-types/{id}/     # Detalle
PUT /api/v1/catalog/equipment-types/{id}/     # Actualizar
DELETE /api/v1/catalog/equipment-types/{id}/  # Eliminar
```

### 2. Módulo Sistema de Taxonomía

#### Componentes Principales
- **TaxonomyTreeView**: Vista jerárquica en árbol
- **TaxonomySystemCRUD**: Gestión de sistemas
- **TaxonomySubsystemCRUD**: Gestión de subsistemas
- **TaxonomyGroupCRUD**: Gestión de grupos

#### Interfaz Jerárquica
```html
<!-- Vista de Taxonomía Jerárquica -->
<div class="taxonomy-manager">
  <div class="taxonomy-tree">
    <div class="tree-node system-node">
      <i class="bi bi-folder"></i>
      <span class="node-label">Sistema Principal</span>
      <div class="node-actions">
        <button class="btn btn-sm btn-outline-primary" data-action="add-subsystem">
          <i class="bi bi-plus"></i>
        </button>
        <button class="btn btn-sm btn-outline-secondary" data-action="edit">
          <i class="bi bi-pencil"></i>
        </button>
      </div>
      <div class="tree-children">
        <div class="tree-node subsystem-node">
          <i class="bi bi-folder-fill"></i>
          <span class="node-label">Subsistema</span>
          <!-- Grupos anidados -->
        </div>
      </div>
    </div>
  </div>
  <div class="taxonomy-details">
    <!-- Panel de detalles del nodo seleccionado -->
  </div>
</div>
```

### 3. Módulo Códigos Standard

#### Componentes Principales
- **ReferenceCodeListView**: Lista por categorías
- **ReferenceCodeBulkImportView**: Importación masiva
- **ReferenceCodeExportView**: Exportación
- **ReferenceCodeValidationView**: Validación de códigos

#### Interfaz de Gestión
```html
<!-- Gestión de Códigos Standard -->
<div class="reference-codes-manager">
  <div class="categories-sidebar">
    <h5>Categorías</h5>
    <ul class="list-group">
      <li class="list-group-item" data-category="fuel">
        <i class="bi bi-fuel-pump"></i> Combustibles
        <span class="badge bg-secondary">12</span>
      </li>
      <li class="list-group-item" data-category="transmission">
        <i class="bi bi-gear"></i> Transmisiones
        <span class="badge bg-secondary">8</span>
      </li>
      <!-- Más categorías -->
    </ul>
  </div>
  <div class="codes-content">
    <div class="codes-toolbar">
      <button class="btn btn-primary" data-action="add-code">Nuevo Código</button>
      <button class="btn btn-success" data-action="import">Importar</button>
      <button class="btn btn-info" data-action="export">Exportar</button>
    </div>
    <div class="codes-table">
      <!-- Tabla de códigos de la categoría seleccionada -->
    </div>
  </div>
</div>
```

### 4. Módulo Monedas

#### Componentes Principales
- **CurrencyListView**: Lista de monedas
- **CurrencyRateView**: Gestión de tasas de cambio
- **CurrencyHistoryView**: Histórico de tasas
- **CurrencyConverterWidget**: Convertidor integrado

#### Interfaz de Monedas
```html
<!-- Gestión de Monedas -->
<div class="currency-manager">
  <div class="currency-list">
    <div class="currency-card" data-currency="USD">
      <div class="currency-header">
        <h5>USD - Dólar Estadounidense</h5>
        <span class="badge bg-primary">Base</span>
      </div>
      <div class="currency-rate">
        <span class="rate-value">1.0000</span>
        <small class="rate-date">Actualizado: 2026-01-12</small>
      </div>
      <div class="currency-actions">
        <button class="btn btn-sm btn-outline-primary" data-action="edit-rate">
          Editar Tasa
        </button>
        <button class="btn btn-sm btn-outline-info" data-action="view-history">
          Histórico
        </button>
      </div>
    </div>
  </div>
  <div class="currency-converter">
    <h5>Convertidor</h5>
    <div class="converter-form">
      <input type="number" class="form-control" placeholder="Cantidad">
      <select class="form-select" data-field="from-currency">
        <option value="USD">USD</option>
      </select>
      <i class="bi bi-arrow-right"></i>
      <select class="form-select" data-field="to-currency">
        <option value="EUR">EUR</option>
      </select>
      <div class="conversion-result">
        <strong>Resultado: <span id="conversion-amount">0.00</span></strong>
      </div>
    </div>
  </div>
</div>
```

### 5. Dashboard de Servicios

#### Componentes Principales
- **ServiceDashboardView**: Vista principal del dashboard
- **ServiceKPIWidget**: Widgets de KPIs
- **ServiceChartsComponent**: Gráficos interactivos
- **ServiceAlertsComponent**: Alertas y notificaciones

#### Interfaz del Dashboard
```html
<!-- Dashboard de Servicios -->
<div class="service-dashboard">
  <div class="dashboard-header">
    <h2>Dashboard de Servicios</h2>
    <div class="date-range-selector">
      <input type="date" class="form-control" id="start-date">
      <span>a</span>
      <input type="date" class="form-control" id="end-date">
      <button class="btn btn-primary" data-action="refresh">Actualizar</button>
    </div>
  </div>
  
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-icon">
        <i class="bi bi-clipboard-check text-primary"></i>
      </div>
      <div class="kpi-content">
        <h3 id="orders-completed">0</h3>
        <p>Órdenes Completadas</p>
        <small class="text-success">+12% vs mes anterior</small>
      </div>
    </div>
    <div class="kpi-card">
      <div class="kpi-icon">
        <i class="bi bi-clock text-warning"></i>
      </div>
      <div class="kpi-content">
        <h3 id="avg-completion-time">0h</h3>
        <p>Tiempo Promedio</p>
        <small class="text-danger">+5% vs mes anterior</small>
      </div>
    </div>
    <!-- Más KPIs -->
  </div>
  
  <div class="charts-row">
    <div class="chart-container">
      <h5>Productividad por Técnico</h5>
      <canvas id="technician-productivity-chart"></canvas>
    </div>
    <div class="chart-container">
      <h5>Servicios por Categoría</h5>
      <canvas id="service-category-chart"></canvas>
    </div>
  </div>
  
  <div class="alerts-section">
    <h5>Alertas Activas</h5>
    <div class="alert-list">
      <!-- Alertas dinámicas -->
    </div>
  </div>
</div>
```

### 6. Calculadora de Tarifas

#### Componentes Principales
- **FlatRateCalculatorView**: Vista principal de la calculadora
- **ServiceSelectorComponent**: Selector de servicios
- **PriceCalculatorEngine**: Motor de cálculo
- **QuotationGeneratorComponent**: Generador de cotizaciones

#### Interfaz de la Calculadora
```html
<!-- Calculadora de Tarifas -->
<div class="flat-rate-calculator">
  <div class="calculator-header">
    <h2>Calculadora de Tarifas</h2>
    <button class="btn btn-success" data-action="save-quote">Guardar Cotización</button>
  </div>
  
  <div class="calculator-form">
    <div class="service-selection">
      <h5>Selección de Servicios</h5>
      <div class="service-categories">
        <div class="category-card" data-category="maintenance">
          <h6>Mantenimiento</h6>
          <div class="service-list">
            <div class="service-item">
              <input type="checkbox" id="oil-change" data-service="oil-change">
              <label for="oil-change">Cambio de Aceite</label>
              <span class="service-time">0.5h</span>
              <span class="service-rate">$45.00</span>
            </div>
            <!-- Más servicios -->
          </div>
        </div>
      </div>
    </div>
    
    <div class="calculation-panel">
      <h5>Cálculo de Costos</h5>
      <div class="cost-breakdown">
        <div class="cost-line">
          <span>Mano de Obra:</span>
          <span id="labor-cost">$0.00</span>
        </div>
        <div class="cost-line">
          <span>Materiales:</span>
          <span id="materials-cost">$0.00</span>
        </div>
        <div class="cost-line">
          <span>Subtotal:</span>
          <span id="subtotal">$0.00</span>
        </div>
        <div class="cost-line">
          <span>Impuestos (16%):</span>
          <span id="taxes">$0.00</span>
        </div>
        <div class="cost-line total">
          <strong>
            <span>Total:</span>
            <span id="total-cost">$0.00</span>
          </strong>
        </div>
      </div>
      
      <div class="adjustments">
        <h6>Ajustes</h6>
        <div class="adjustment-item">
          <label>Descuento (%):</label>
          <input type="number" class="form-control" id="discount-percent" min="0" max="100">
        </div>
        <div class="adjustment-item">
          <label>Recargo adicional:</label>
          <input type="number" class="form-control" id="additional-charge" min="0">
        </div>
      </div>
    </div>
  </div>
  
  <div class="quotation-preview">
    <h5>Vista Previa de Cotización</h5>
    <div class="quote-content">
      <!-- Contenido de la cotización -->
    </div>
    <div class="quote-actions">
      <button class="btn btn-primary" data-action="print-quote">Imprimir</button>
      <button class="btn btn-success" data-action="convert-to-order">Convertir a Orden</button>
    </div>
  </div>
</div>
```

## Data Models

### Modelos de Frontend (Django Forms)

```python
# forms/catalog_forms.py
class EquipmentTypeForm(forms.ModelForm):
    class Meta:
        model = EquipmentType
        fields = ['code', 'name', 'category', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'code': forms.TextInput(attrs={'class': 'form-control text-uppercase'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code'].upper()
        if EquipmentType.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este código ya existe.")
        return code

class TaxonomySystemForm(forms.ModelForm):
    class Meta:
        model = TaxonomySystem
        fields = ['code', 'name', 'description', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].widget.attrs.update({'class': 'form-control'})

class ReferenceCodeForm(forms.ModelForm):
    class Meta:
        model = ReferenceCode
        fields = ['category', 'code', 'description', 'standard_type', 'is_active']
    
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        code = cleaned_data.get('code')
        
        if category and code:
            if ReferenceCode.objects.filter(
                category=category, 
                code=code
            ).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError(
                    "Ya existe un código con esta combinación de categoría y código."
                )
        return cleaned_data

class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['code', 'name', 'symbol', 'is_base', 'is_active']
    
    def clean_code(self):
        code = self.cleaned_data['code'].upper()
        if len(code) != 3:
            raise forms.ValidationError("El código debe tener exactamente 3 caracteres.")
        return code
```

### Estructuras de Datos JavaScript

```javascript
// Estructura para gestión de taxonomía
const TaxonomyManager = {
    currentNode: null,
    treeData: [],
    
    loadTree: function() {
        // Cargar estructura jerárquica
    },
    
    selectNode: function(nodeId) {
        // Seleccionar nodo y mostrar detalles
    },
    
    addNode: function(parentId, nodeType) {
        // Agregar nuevo nodo
    },
    
    updateNode: function(nodeId, data) {
        // Actualizar nodo existente
    },
    
    deleteNode: function(nodeId) {
        // Eliminar nodo con validaciones
    }
};

// Estructura para calculadora de tarifas
const FlatRateCalculator = {
    selectedServices: [],
    laborRate: 0,
    materialsCost: 0,
    discountPercent: 0,
    additionalCharge: 0,
    
    addService: function(serviceId) {
        // Agregar servicio al cálculo
    },
    
    removeService: function(serviceId) {
        // Remover servicio del cálculo
    },
    
    calculateTotal: function() {
        // Calcular total con todos los ajustes
    },
    
    generateQuote: function() {
        // Generar cotización
    },
    
    saveQuote: function() {
        // Guardar cotización en el sistema
    }
};
```

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas del sistema - esencialmente, una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre las especificaciones legibles por humanos y las garantías de corrección verificables por máquina.*

### Property 1: Integridad de CRUD en Catálogos
*Para cualquier* entidad de catálogo (Tipos de Equipo, Taxonomía, Códigos, Monedas), las operaciones de crear, leer, actualizar y eliminar deben mantener la integridad de datos y mostrar confirmación apropiada al usuario.
**Validates: Requirements 1.3, 1.4, 1.5, 2.3, 2.4, 2.5, 3.3, 3.4, 4.2, 4.3**

### Property 2: Validación de Unicidad de Códigos
*Para cualquier* código ingresado en el sistema (tipos de equipo, códigos de referencia, monedas), el sistema debe validar unicidad dentro de su contexto y mostrar errores específicos cuando se detecten duplicados.
**Validates: Requirements 1.3, 3.3, 4.2, 8.3**

### Property 3: Consistencia de Jerarquía Taxonómica
*Para cualquier* operación en la taxonomía (crear, editar, eliminar), el sistema debe mantener la integridad de la estructura jerárquica y prevenir referencias circulares o huérfanas.
**Validates: Requirements 2.3, 2.4, 2.5, 2.6, 8.1, 8.2**

### Property 4: Precisión de Cálculos de Tarifas
*Para cualquier* combinación de servicios, descuentos y recargos en la calculadora, el resultado debe ser matemáticamente correcto y consistente con las reglas de negocio establecidas.
**Validates: Requirements 6.3, 6.4, 6.5**

### Property 5: Integridad Referencial en Eliminaciones
*Para cualquier* intento de eliminación de registros con dependencias, el sistema debe verificar las referencias existentes y prevenir eliminaciones que comprometan la integridad de datos.
**Validates: Requirements 1.7, 2.6, 3.8, 8.2**

### Property 6: Responsividad de Interfaces
*Para cualquier* dispositivo y tamaño de pantalla, todas las interfaces deben adaptarse apropiadamente manteniendo funcionalidad completa y usabilidad óptima.
**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8**

### Property 7: Consistencia de Navegación
*Para cualquier* flujo de navegación entre secciones, el sistema debe mantener contexto, mostrar breadcrumbs correctos y permitir navegación fluida sin pérdida de datos.
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 8: Validación de Formularios en Tiempo Real
*Para cualquier* formulario del sistema, las validaciones deben ejecutarse en tiempo real proporcionando retroalimentación inmediata y precisa al usuario.
**Validates: Requirements 8.4, 8.5, 8.6, 8.7**

### Property 9: Actualización Dinámica de KPIs
*Para cualquier* cambio en el rango de fechas del dashboard de servicios, todos los KPIs y gráficos deben actualizarse dinámicamente reflejando los datos correctos del período seleccionado.
**Validates: Requirements 5.1, 5.2, 5.8**

### Property 10: Persistencia de Cotizaciones
*Para cualquier* cotización generada en la calculadora de tarifas, el sistema debe permitir guardarla con un identificador único y recuperarla posteriormente con todos sus detalles intactos.
**Validates: Requirements 6.5, 6.8**

## Error Handling

### Estrategias de Manejo de Errores

#### 1. Errores de Validación
```python
# Manejo en vistas Django
class EquipmentTypeCreateView(CreateView):
    def form_invalid(self, form):
        messages.error(
            self.request, 
            "Por favor corrige los errores en el formulario."
        )
        return super().form_invalid(form)
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(
                self.request, 
                f"Tipo de equipo '{form.instance.name}' creado exitosamente."
            )
            return response
        except IntegrityError:
            messages.error(
                self.request, 
                "Error: Ya existe un tipo de equipo con este código."
            )
            return self.form_invalid(form)
```

#### 2. Errores de API
```javascript
// Manejo en JavaScript
class APIErrorHandler {
    static handle(error, context = '') {
        let message = 'Error desconocido';
        
        if (error.response) {
            switch (error.response.status) {
                case 400:
                    message = 'Datos inválidos. Verifica la información ingresada.';
                    break;
                case 401:
                    message = 'Sesión expirada. Por favor inicia sesión nuevamente.';
                    window.location.href = '/login/';
                    return;
                case 403:
                    message = 'No tienes permisos para realizar esta acción.';
                    break;
                case 404:
                    message = 'El recurso solicitado no fue encontrado.';
                    break;
                case 500:
                    message = 'Error interno del servidor. Contacta al administrador.';
                    break;
            }
        } else if (error.request) {
            message = 'Error de conexión. Verifica tu conexión a internet.';
        }
        
        this.showError(message, context);
    }
    
    static showError(message, context) {
        const toast = new bootstrap.Toast(document.getElementById('error-toast'));
        document.getElementById('error-message').textContent = 
            context ? `${context}: ${message}` : message;
        toast.show();
    }
}
```

#### 3. Errores de Integridad Referencial
```python
# Validación antes de eliminación
def can_delete_equipment_type(equipment_type_id):
    """Verifica si un tipo de equipo puede ser eliminado"""
    try:
        equipment_type = EquipmentType.objects.get(id=equipment_type_id)
        
        # Verificar si hay equipos usando este tipo
        if equipment_type.equipment_set.exists():
            return False, "No se puede eliminar: hay equipos asociados a este tipo."
        
        # Verificar otras dependencias
        if hasattr(equipment_type, 'workorder_set') and equipment_type.workorder_set.exists():
            return False, "No se puede eliminar: hay órdenes de trabajo asociadas."
        
        return True, "El tipo de equipo puede ser eliminado."
        
    except EquipmentType.DoesNotExist:
        return False, "El tipo de equipo no existe."
```

## Testing Strategy

### Enfoque Dual de Testing

#### Unit Tests
Los unit tests se enfocan en validar componentes individuales:
- Formularios Django y sus validaciones
- Vistas individuales y su comportamiento
- Funciones de utilidad y helpers
- Validaciones de modelos

#### Property-Based Tests
Los property tests validan propiedades universales:
- Integridad de datos en operaciones CRUD
- Consistencia de cálculos matemáticos
- Comportamiento de navegación
- Validaciones de formularios

### Configuración de Testing

#### Property-Based Testing con Hypothesis
```python
# tests/test_catalog_properties.py
from hypothesis import given, strategies as st
from hypothesis.extra.django import from_model

class TestCatalogProperties(TestCase):
    
    @given(from_model(EquipmentType))
    def test_equipment_type_crud_integrity(self, equipment_type):
        """
        Property 1: Integridad de CRUD en Catálogos
        Feature: forge-frontend-catalog-services-completion, Property 1
        """
        # Crear
        response = self.client.post('/catalog/equipment-types/create/', {
            'code': equipment_type.code,
            'name': equipment_type.name,
            'category': equipment_type.category,
            'description': equipment_type.description,
            'is_active': equipment_type.is_active
        })
        
        # Verificar creación exitosa
        self.assertIn(response.status_code, [200, 302])
        
        # Leer
        created_type = EquipmentType.objects.get(code=equipment_type.code)
        self.assertEqual(created_type.name, equipment_type.name)
        
        # Actualizar
        new_name = f"Updated {equipment_type.name}"
        response = self.client.post(f'/catalog/equipment-types/{created_type.id}/edit/', {
            'code': created_type.code,
            'name': new_name,
            'category': created_type.category,
            'description': created_type.description,
            'is_active': created_type.is_active
        })
        
        # Verificar actualización
        updated_type = EquipmentType.objects.get(id=created_type.id)
        self.assertEqual(updated_type.name, new_name)
    
    @given(st.text(min_size=1, max_size=10))
    def test_code_uniqueness_validation(self, code):
        """
        Property 2: Validación de Unicidad de Códigos
        Feature: forge-frontend-catalog-services-completion, Property 2
        """
        # Crear primer tipo con el código
        EquipmentType.objects.create(
            code=code.upper(),
            name=f"Type {code}",
            category="TEST"
        )
        
        # Intentar crear segundo tipo con el mismo código
        form_data = {
            'code': code.upper(),
            'name': f"Another Type {code}",
            'category': "TEST"
        }
        
        response = self.client.post('/catalog/equipment-types/create/', form_data)
        
        # Debe mostrar error de validación
        self.assertContains(response, "Este código ya existe")
        
        # Solo debe existir un registro con este código
        self.assertEqual(
            EquipmentType.objects.filter(code=code.upper()).count(), 
            1
        )
```

#### Integration Tests
```python
# tests/test_catalog_integration.py
class TestCatalogIntegration(TestCase):
    
    def test_complete_equipment_type_workflow(self):
        """Test del workflow completo de gestión de tipos de equipo"""
        # Login
        self.client.login(username='testuser', password='testpass')
        
        # Navegar a lista
        response = self.client.get('/catalog/equipment-types/')
        self.assertEqual(response.status_code, 200)
        
        # Crear nuevo tipo
        response = self.client.post('/catalog/equipment-types/create/', {
            'code': 'AUTO',
            'name': 'Automóvil',
            'category': 'VEHICLE',
            'description': 'Vehículo de pasajeros',
            'is_active': True
        })
        self.assertRedirects(response, '/catalog/equipment-types/')
        
        # Verificar en lista
        response = self.client.get('/catalog/equipment-types/')
        self.assertContains(response, 'Automóvil')
        
        # Ver detalle
        equipment_type = EquipmentType.objects.get(code='AUTO')
        response = self.client.get(f'/catalog/equipment-types/{equipment_type.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Automóvil')
        
        # Editar
        response = self.client.post(f'/catalog/equipment-types/{equipment_type.id}/edit/', {
            'code': 'AUTO',
            'name': 'Automóvil Actualizado',
            'category': 'VEHICLE',
            'description': 'Vehículo de pasajeros actualizado',
            'is_active': True
        })
        self.assertRedirects(response, '/catalog/equipment-types/')
        
        # Verificar actualización
        equipment_type.refresh_from_db()
        self.assertEqual(equipment_type.name, 'Automóvil Actualizado')
```

### Configuración de Tests
- **Mínimo 100 iteraciones** por property test
- **Cobertura objetivo**: 90%+ para nuevas funcionalidades
- **Tests automatizados** en CI/CD pipeline
- **Reportes de cobertura** generados automáticamente

### Tags de Property Tests
Cada property test debe incluir el tag:
```python
# **Feature: forge-frontend-catalog-services-completion, Property {number}: {property_text}**
```

Este diseño proporciona una base sólida para implementar todas las funcionalidades faltantes de los nodos CATÁLOGOS y SERVICIOS, manteniendo consistencia con la arquitectura existente y asegurando alta calidad a través de testing exhaustivo.