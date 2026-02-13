# Integración OEM + Equipos - Documentación Técnica

**Fecha de Implementación**: 2026-01-10  
**Módulos Afectados**: Equipment, OEM Catalog  
**Tipo de Cambio**: Feature Enhancement + Architecture Decision  
**Estado**: ✅ Completado y Operativo

---

## 📋 Resumen Ejecutivo

Se implementó una integración completa entre el módulo de Equipos y el catálogo OEM, permitiendo que los usuarios seleccionen marcas y modelos de equipos desde un catálogo centralizado en lugar de entrada de texto libre. La solución evita migraciones complejas de base de datos al mantener la restricción a nivel de UI/API.

---

## 🎯 Objetivos Alcanzados

1. ✅ **Generalización del esquema OEM**
   - Soporte para vehículos, maquinaria industrial, equipos de refrigeración, etc.
   - Extensión de tablas `brands` y `catalog_items` con campos adicionales

2. ✅ **UX mejorada en formularios**
   - Combos desplegables en lugar de texto libre
   - Dependencia dinámica: seleccionar Marca → carga Modelos

3. ✅ **Consistencia de datos**
   - Marcas y modelos estandarizados
   - Facilita reportes y análisis

4. ✅ **Escalabilidad**
   - Diseño genérico soporta múltiples tipos de equipos
   - Fácil agregar nuevas marcas/modelos sin cambios de código

---

## 🏗️ Decisión de Diseño Arquitectónico

### Opción A: Foreign Keys (Descartada)
```python
# NO IMPLEMENTADO
class Equipment(models.Model):
    brand = models.ForeignKey(OEMBrand, on_delete=models.PROTECT)
    model = models.ForeignKey(OEMCatalogItem, on_delete=models.PROTECT)
```

**Razones para descartar**:
- ❌ Requiere migración compleja de datos existentes
- ❌ Django genera prompts interactivos confusos (rename `engine` → `body_style`)
- ❌ Rompe compatibilidad con datos legacy
- ❌ Migraciones reversibles complicadas

### Opción B: CharField + Validación UI (IMPLEMENTADA) ✅
```python
# IMPLEMENTADO
class Equipment(models.Model):
    brand = models.CharField(max_length=50)  # Stores OEMBrand.oem_code
    model = models.CharField(max_length=50)  # Stores model description or part_number
```

**Beneficios**:
- ✅ Sin migraciones de esquema
- ✅ Compatibilidad con datos existentes
- ✅ Validación en frontend/API
- ✅ Transición gradual posible
- ✅ Flexibilidad para migrar a FK en futuro si necesario

---

## 🔧 Implementación Técnica

### 1. Extensión del Esquema OEM

#### Tabla: `oem.brands`
```sql
ALTER TABLE oem.brands ADD COLUMN brand_type VARCHAR(50) DEFAULT 'MIXED';
ALTER TABLE oem.brands ADD COLUMN logo_url VARCHAR(500);
ALTER TABLE oem.brands ADD COLUMN display_order INTEGER DEFAULT 0;
ALTER TABLE oem.brands ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Valores válidos para brand_type:
-- 'VEHICLE_MFG'      - Fabricante de vehículos (Toyota, Ford, etc.)
-- 'EQUIPMENT_MFG'    - Fabricante de maquinaria (Caterpillar, Komatsu, etc.)
-- 'PARTS_SUPPLIER'   - Proveedor de partes
-- 'MIXED'            - Múltiples categorías
```

#### Tabla: `oem.catalog_items`
```sql
ALTER TABLE oem.catalog_items ADD COLUMN item_type VARCHAR(50) DEFAULT 'PART';
ALTER TABLE oem.catalog_items ADD COLUMN body_style VARCHAR(50);
ALTER TABLE oem.catalog_items ADD COLUMN year_start INTEGER;
ALTER TABLE oem.catalog_items ADD COLUMN year_end INTEGER;
ALTER TABLE oem.catalog_items ADD COLUMN is_active BOOLEAN DEFAULT true;
ALTER TABLE oem.catalog_items ADD COLUMN display_order INTEGER DEFAULT 0;

-- Valores válidos para item_type:
-- 'VEHICLE_MODEL'    - Modelo de vehículo (Corolla, F-150, etc.)
-- 'EQUIPMENT_MODEL'  - Modelo de maquinaria (320D, PC200, etc.)
-- 'PART'             - Parte individual
```

### 2. Backend API

#### API Client (`frontend/services/api_client.py`)
```python
def get_oem_brands(self, page: int = 1, page_size: int = 1000, **filters) -> Dict[str, Any]:
    """
    Get OEM brands (manufacturers/suppliers) with optional filtering.
    
    Common filters:
    - is_active=True
    - brand_type='VEHICLE_MFG' / 'EQUIPMENT_MFG' / 'MIXED'
    """
    params = {'page': page, 'page_size': page_size}
    params.update(filters)
    return self.get('oem-brands/', params=params, use_cache=True)

def get_oem_catalog_items(self, page: int = 1, page_size: int = 1000, **filters) -> Dict[str, Any]:
    """
    Get OEM catalog items (models/parts) with optional filtering.
    
    Common filters:
    - oem_code=<brand oem_code>
    - item_type='VEHICLE_MODEL' / 'EQUIPMENT_MODEL' / 'PART'
    - is_active=True
    - is_discontinued=False
    """
    params = {'page': page, 'page_size': page_size}
    params.update(filters)
    return self.get('oem-catalog-items/', params=params, use_cache=True)
```

#### Vista AJAX Interna (`frontend/views/oem_views.py`)
```python
class OEMModelListAPIView(LoginRequiredMixin, APIClientMixin, View):
    """
    API interna para obtener modelos OEM filtrados por marca.
    Usada por el formulario de equipos para el combo Modelo.
    """
    login_url = 'frontend:login'

    def get(self, request, *args, **kwargs):
        oem_code = request.GET.get('oem_code') or ''
        item_type = request.GET.get('item_type') or 'VEHICLE_MODEL'
        page_size = request.GET.get('page_size') or '1000'

        if not oem_code:
            return JsonResponse(
                {'detail': 'Parámetro oem_code es requerido'},
                status=400
            )

        try:
            api_client = self.get_api_client()
            data = api_client.get_oem_catalog_items(
                page_size=int(page_size),
                oem_code=oem_code,
                item_type=item_type,
                is_active=True,
                is_discontinued=False,
            )
            return JsonResponse(data, safe=False)
        except APIException as e:
            logger.error(f"Error loading OEM models from API: {e}")
            return JsonResponse(
                {'detail': e.message or 'Error al cargar modelos OEM'},
                status=e.status_code or 500
            )
```

### 3. Frontend

#### Formulario (`frontend/forms/equipment_forms.py`)
```python
brand = forms.CharField(
    max_length=50,
    widget=forms.Select(attrs={
        'class': 'form-select',
        'required': True,
        'id': 'id_brand',
    }),
    label='Marca',
    help_text='Marca del vehículo (ej: Toyota, Ford, Chevrolet)'
)

model = forms.CharField(
    max_length=50,
    widget=forms.Select(attrs={
        'class': 'form-select',
        'required': True,
        'id': 'id_model',
    }),
    label='Modelo',
    help_text='Modelo del vehículo'
)
```

#### Vista de Creación (`frontend/views/equipment_views.py`)
```python
def get_context_data(self, **kwargs):
    # ... código existente ...
    
    # Cargar marcas OEM
    try:
        api_client = self.get_api_client()
        brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
        brand_results = brands_data.get('results', brands_data)

        brand_choices = [('', 'Seleccione una marca')]
        for brand in brand_results:
            value = brand.get('oem_code') or brand.get('name')
            label_name = (brand.get('name') or '').strip() or value
            code = (brand.get('oem_code') or '').strip()
            label = f"{label_name} ({code})" if code else label_name
            brand_choices.append((value, label))

        form.fields['brand'].widget = forms.Select(
            choices=brand_choices,
            attrs={'class': 'form-select', 'required': True, 'id': 'id_brand'}
        )
    except APIException as e:
        logger.error(f"Error loading OEM brands: {e}")
        form.fields['brand'].widget = forms.Select(
            choices=[('', 'Error al cargar marcas')],
            attrs={'class': 'form-select', 'id': 'id_brand'}
        )

    # Inicializar modelo (JS lo rellenará)
    form.fields['model'].widget = forms.Select(
        choices=[('', 'Seleccione una marca primero')],
        attrs={'class': 'form-select', 'required': True, 'id': 'id_model'}
    )
```

#### JavaScript (`equipment_form.html`)
```javascript
// Marca (OEMBrand) → Modelo (OEMCatalogItem)
const brandField = document.getElementById('id_brand');
const modelField = document.getElementById('id_model');

function setModelPlaceholder(text) {
    if (!modelField) return;
    modelField.innerHTML = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = text;
    opt.disabled = true;
    opt.selected = true;
    modelField.appendChild(opt);
}

async function loadModelsForBrand(oemCode) {
    if (!modelField) return;

    if (!oemCode) {
        setModelPlaceholder('Seleccione una marca primero');
        modelField.disabled = true;
        return;
    }

    setModelPlaceholder('Cargando modelos...');
    modelField.disabled = true;

    const params = new URLSearchParams({
        oem_code: oemCode,
        item_type: 'VEHICLE_MODEL',
        page_size: '1000'
    });

    try {
        const response = await fetch(`/api/oem/models/?${params.toString()}`, {
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const results = data.results || data;

        modelField.innerHTML = '';
        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = 'Seleccione un modelo';
        defaultOpt.disabled = true;
        defaultOpt.selected = true;
        modelField.appendChild(defaultOpt);

        results.forEach(item => {
            const opt = document.createElement('option');
            const value = item.part_number || item.description_es || item.description_en || '';
            let label = item.description_es || item.description_en || item.part_number || 'Modelo sin descripción';

            const years = [];
            if (item.year_start) years.push(item.year_start);
            if (item.year_end) years.push(item.year_end);
            const yearsStr = years.length ? ` (${years.join('–')})` : '';

            if (item.body_style) {
                label = `${label} - ${item.body_style}${yearsStr}`;
            } else {
                label = `${label}${yearsStr}`;
            }

            opt.value = value;
            opt.textContent = label;
            modelField.appendChild(opt);
        });

        modelField.disabled = false;
    } catch (error) {
        console.error('Error al cargar modelos OEM:', error);
        setModelPlaceholder('Error al cargar modelos');
        modelField.disabled = true;
    }
}

if (brandField && modelField) {
    if (!modelField.value) {
        setModelPlaceholder('Seleccione una marca primero');
        modelField.disabled = true;
    }

    brandField.addEventListener('change', function() {
        const selectedBrand = this.value;
        loadModelsForBrand(selectedBrand);
    });
}
```

---

## 📊 Flujo de Datos

```
┌─────────────────┐
│  Usuario abre   │
│ "Crear Equipo"  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ EquipmentCreateView.get_context_data│
│ - Llama api_client.get_oem_brands() │
│ - Popula choices del campo 'brand'  │
│ - Inicializa 'model' vacío          │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Template renderiza formulario   │
│ - Campo Marca: <select> poblado│
│ - Campo Modelo: <select> vacío │
└────────┬────────────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Usuario selecciona Marca         │
│ - JS detecta evento 'change'     │
│ - Llama loadModelsForBrand(code) │
└────────┬─────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Fetch AJAX a /api/oem/models/           │
│ - Params: oem_code, item_type, page_size│
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ OEMModelListAPIView                 │
│ - Valida parámetros                 │
│ - Llama api_client.get_oem_catalog_ │
│   items(oem_code=X, item_type=Y)    │
│ - Retorna JSON                      │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Core API (DRF)                  │
│ - OEMCatalogItemViewSet         │
│ - Filtra por oem_code, item_type│
│ - Serializa resultados          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ PostgreSQL (esquema oem)        │
│ SELECT * FROM oem.catalog_items │
│ WHERE oem_code = 'TOYOTA'       │
│   AND item_type = 'VEHICLE_...' │
│   AND is_active = true          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ JS popula campo Modelo          │
│ - Crea <option> por cada item   │
│ - Habilita campo                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Usuario selecciona Modelo       │
│ - Completa resto del formulario │
│ - Submit → POST /equipment/     │
└─────────────────────────────────┘
```

---

## 🧪 Testing

### Test Manual
1. Iniciar servidor: `cd forge_api && python manage.py runserver`
2. Navegar a: `http://localhost:8000/equipment/create/`
3. Verificar:
   - Campo Marca muestra lista de fabricantes
   - Al seleccionar Marca, campo Modelo se activa
   - Consola del navegador (F12) sin errores
   - Network tab muestra petición exitosa a `/api/oem/models/`
4. Crear equipo de prueba y verificar guardado

### Test Unitario (Propuesto)
```python
# forge_api/core/tests/test_equipment_oem_integration.py
from django.test import TestCase, Client
from core.models import OEMBrand, OEMCatalogItem, Equipment

class EquipmentOEMIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.brand = OEMBrand.objects.create(
            oem_code='TOYOTA',
            name='Toyota Motor Corporation',
            brand_type='VEHICLE_MFG',
            is_active=True
        )
        self.model = OEMCatalogItem.objects.create(
            oem_code=self.brand,
            part_number='COROLLA',
            description_es='Toyota Corolla',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
    
    def test_oem_models_api_endpoint(self):
        """Test que /api/oem/models/ retorna modelos filtrados por marca"""
        response = self.client.get('/api/oem/models/', {
            'oem_code': 'TOYOTA',
            'item_type': 'VEHICLE_MODEL'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['part_number'], 'COROLLA')
    
    def test_equipment_form_loads_brands(self):
        """Test que el formulario de equipos carga marcas OEM"""
        response = self.client.get('/equipment/create/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id_brand')
        self.assertContains(response, 'TOYOTA')
```

---

## 📝 Cómo Agregar Nuevas Marcas/Modelos

### Opción 1: SQL Directo
```sql
-- Agregar marca
INSERT INTO oem.brands (oem_code, name, brand_type, country, is_active)
VALUES ('FORD', 'Ford Motor Company', 'VEHICLE_MFG', 'US', true);

-- Agregar modelo
INSERT INTO oem.catalog_items (
    oem_code, part_number, description_es, item_type, 
    body_style, year_start, year_end, is_active
)
VALUES (
    (SELECT brand_id FROM oem.brands WHERE oem_code = 'FORD'),
    'F150', 'Ford F-150', 'VEHICLE_MODEL',
    'Pickup', 2015, 2024, true
);
```

### Opción 2: Django Admin
1. Navegar a `/admin/core/oembrand/`
2. Click "Add OEM Brand"
3. Completar formulario y guardar

### Opción 3: API REST
```bash
# Agregar marca
curl -X POST http://localhost:8000/api/oem-brands/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "oem_code": "FORD",
    "name": "Ford Motor Company",
    "brand_type": "VEHICLE_MFG",
    "country": "US",
    "is_active": true
  }'

# Agregar modelo
curl -X POST http://localhost:8000/api/oem-catalog-items/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "oem_code": <brand_id>,
    "part_number": "F150",
    "description_es": "Ford F-150",
    "item_type": "VEHICLE_MODEL",
    "body_style": "Pickup",
    "year_start": 2015,
    "year_end": 2024,
    "is_active": true
  }'
```

---

## 🔮 Migración Futura a Foreign Keys (Opcional)

Si en el futuro se decide migrar a FKs reales:

```python
# Paso 1: Crear nuevas columnas FK
python manage.py makemigrations --empty core --name add_equipment_fk_fields

# En la migración:
operations = [
    migrations.AddField(
        model_name='equipment',
        name='brand_oem',
        field=models.ForeignKey('OEMBrand', null=True, blank=True, on_delete=models.PROTECT),
    ),
    migrations.AddField(
        model_name='equipment',
        name='model_catalog',
        field=models.ForeignKey('OEMCatalogItem', null=True, blank=True, on_delete=models.PROTECT),
    ),
]

# Paso 2: Script de migración de datos
# Mapear Equipment.brand (CharField) → OEMBrand via oem_code
# Mapear Equipment.model (CharField) → OEMCatalogItem via part_number

# Paso 3: Cambiar formulario/vistas para usar nuevos campos FK

# Paso 4: Deprecar campos antiguos brand/model (CharField)
```

---

## 🚀 Próximos Pasos

1. **Poblar datos de prueba**
   - Insertar marcas comunes (Toyota, Ford, Caterpillar, etc.)
   - Insertar modelos populares para cada marca

2. **Crear interfaz de administración OEM**
   - CRUD para marcas y modelos desde frontend
   - Validaciones de negocio

3. **Extender a otros tipos de equipos**
   - Maquinaria pesada
   - Equipos de refrigeración
   - Herramientas especializadas

4. **Analytics**
   - Reporte de marcas/modelos más comunes
   - Tendencias de equipos por cliente

---

**Documento creado**: 2026-01-10  
**Autor**: Sistema AI  
**Versión**: 1.0
