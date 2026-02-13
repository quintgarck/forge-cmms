# Siguiente Paso: Tarea 4.2 - Gestión de Tasas de Cambio

**Fecha:** 2026-01-15  
**Estado Actual:** Tarea 4.1 completada (Gestión de Monedas)  
**Siguiente:** Tarea 4.2 - Implementar Gestión de Tasas de Cambio

---

## ✅ Estado Actual del Proyecto

### Completado (100%):
- **Tarea 1:** Tipos de Equipo ✅
- **Tarea 2:** Taxonomía ✅
- **Tarea 3:** Códigos de Referencia ✅
- **Tarea 4.1:** Gestión de Monedas ✅

### Ya Implementado en Tarea 4.1:
- ✅ `CurrencyListView` - Lista de monedas con búsqueda
- ✅ `CurrencyCreateView` - Crear nuevas monedas
- ✅ `CurrencyUpdateView` - Editar monedas existentes
- ✅ `CurrencyDetailView` - Ver detalles de moneda
- ✅ `CurrencyDeleteView` - Eliminar monedas
- ✅ `CurrencyForm` - Formulario completo con validaciones
- ✅ Templates completos (list, form, detail, delete)
- ✅ Integración con API backend
- ✅ Campo `exchange_rate` ya existe en el formulario

### 🎯 Siguiente Tarea:
**Tarea 4.2: Implementar Gestión de Tasas de Cambio**

**IMPORTANTE:** La gestión básica de monedas YA ESTÁ COMPLETA, incluyendo el campo de tipo de cambio. Lo que falta es:
1. Interfaz dedicada para actualizar tasas masivamente
2. Sistema de actualización automática desde APIs externas
3. Histórico de cambios de tasas
4. Validaciones avanzadas de tasas

---

## 📖 Descripción de la Tarea 4.2

### Objetivo:
Implementar un sistema completo de gestión de tasas de cambio que permita:
1. Actualización manual de tasas
2. Actualización automática desde fuentes externas
3. Validación de tasas razonables
4. Registro de fuente y timestamp

### Requisitos a Cumplir:
- **Requirement 4.3:** Configurar tasas de cambio con actualización manual y automática
- **Requirement 4.4:** Establecer moneda base y recalcular conversiones
- **Requirement 4.7:** Actualizar tasas automáticamente con registro de fuente y timestamp

---

## 🎨 Componentes a Implementar

### 1. Vista: CurrencyRateView
**Propósito:** Gestionar tasas de cambio de monedas

**Funcionalidades:**
- Mostrar tasas actuales de todas las monedas
- Permitir edición manual de tasas
- Botón para actualización automática
- Mostrar última actualización (fecha y fuente)
- Validar que las tasas sean razonables

**Ubicación:** `forge_api/frontend/views/catalog_views.py`

---

### 2. Formulario: CurrencyRateForm
**Propósito:** Formulario para actualizar tasas manualmente

**Campos:**
- `currency` (select): Moneda a actualizar
- `rate` (decimal): Nueva tasa de cambio
- `source` (text): Fuente de la tasa (manual/automática)
- `effective_date` (date): Fecha efectiva de la tasa

**Validaciones:**
- Tasa debe ser mayor que 0
- Tasa debe estar en un rango razonable (ej: 0.001 - 10000)
- Fecha efectiva no puede ser futura
- Fuente es obligatoria

**Ubicación:** `forge_api/frontend/forms/catalog_forms.py`

---

### 3. Template: currency_rate_management.html
**Propósito:** Interfaz para gestión de tasas

**Secciones:**
1. **Header:**
   - Título: "Gestión de Tasas de Cambio"
   - Botón: "Actualizar Todas las Tasas" (automático)
   - Botón: "Volver a Monedas"

2. **Tabla de Tasas Actuales:**
   - Columnas: Moneda, Código, Tasa Actual, Última Actualización, Fuente, Acciones
   - Acciones: Editar, Histórico

3. **Modal de Edición:**
   - Formulario para actualizar tasa manualmente
   - Validación en tiempo real
   - Confirmación antes de guardar

4. **Sección de Actualización Automática:**
   - Selector de fuente (API externa)
   - Botón "Actualizar Ahora"
   - Log de últimas actualizaciones

**Ubicación:** `forge_api/templates/frontend/catalog/currency_rate_management.html`

---

### 4. Servicio: ExchangeRateService
**Propósito:** Lógica de negocio para tasas de cambio

**Métodos:**
```python
class ExchangeRateService:
    def get_current_rates(self):
        """Obtener tasas actuales de todas las monedas"""
        pass
    
    def update_rate_manual(self, currency_id, rate, source='manual'):
        """Actualizar tasa manualmente"""
        pass
    
    def update_rates_automatic(self, source='external_api'):
        """Actualizar todas las tasas desde fuente externa"""
        pass
    
    def validate_rate(self, rate):
        """Validar que la tasa sea razonable"""
        pass
    
    def get_rate_history(self, currency_id, days=30):
        """Obtener histórico de tasas"""
        pass
```

**Ubicación:** `forge_api/frontend/services/exchange_rate_service.py`

---

## 🔧 Implementación Técnica

### Paso 1: Crear Vista CurrencyRateView

```python
# forge_api/frontend/views/catalog_views.py

class CurrencyRateView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/catalog/currency_rate_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener todas las monedas con sus tasas actuales
        currencies = self.get_currencies_with_rates()
        
        context['currencies'] = currencies
        context['base_currency'] = self.get_base_currency()
        context['last_update'] = self.get_last_update_info()
        
        return context
    
    def get_currencies_with_rates(self):
        """Obtener monedas desde API con tasas actuales"""
        # Llamar a API backend
        pass
    
    def get_base_currency(self):
        """Obtener moneda base del sistema"""
        pass
    
    def get_last_update_info(self):
        """Obtener información de última actualización"""
        pass
```

---

### Paso 2: Crear Formulario CurrencyRateForm

```python
# forge_api/frontend/forms/catalog_forms.py

class CurrencyRateForm(forms.Form):
    currency = forms.ChoiceField(
        label='Moneda',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    rate = forms.DecimalField(
        label='Tasa de Cambio',
        max_digits=10,
        decimal_places=4,
        min_value=Decimal('0.0001'),
        max_value=Decimal('10000.0000'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.0001',
            'placeholder': '1.0000'
        })
    )
    source = forms.CharField(
        label='Fuente',
        max_length=100,
        initial='manual',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    effective_date = forms.DateField(
        label='Fecha Efectiva',
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean_rate(self):
        rate = self.cleaned_data['rate']
        # Validar que la tasa sea razonable
        if rate < Decimal('0.0001') or rate > Decimal('10000.0000'):
            raise forms.ValidationError(
                'La tasa debe estar entre 0.0001 y 10000.0000'
            )
        return rate
    
    def clean_effective_date(self):
        date = self.cleaned_data['effective_date']
        # No permitir fechas futuras
        if date > timezone.now().date():
            raise forms.ValidationError(
                'La fecha efectiva no puede ser futura'
            )
        return date
```

---

### Paso 3: Crear Template currency_rate_management.html

```html
{% extends 'frontend/base/base.html' %}
{% load static %}

{% block title %}Gestión de Tasas de Cambio - MovIAx{% endblock %}

{% block extra_css %}
<style>
    .rate-card {
        transition: all 0.3s ease;
    }
    .rate-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .rate-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0d6efd;
    }
    .rate-updated {
        font-size: 0.85rem;
        color: #6c757d;
    }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h1 class="h3 mb-0">
                <i class="bi bi-currency-exchange text-primary"></i>
                Gestión de Tasas de Cambio
            </h1>
            <p class="text-muted mb-0">
                Actualización y gestión de tasas de cambio
            </p>
        </div>
        <div>
            <button class="btn btn-success" id="updateAllRates">
                <i class="bi bi-arrow-clockwise"></i>
                Actualizar Todas las Tasas
            </button>
            <a href="{% url 'frontend:currency_list' %}" class="btn btn-outline-secondary">
                <i class="bi bi-arrow-left"></i>
                Volver a Monedas
            </a>
        </div>
    </div>

    <!-- Información de Moneda Base -->
    <div class="alert alert-info">
        <i class="bi bi-info-circle"></i>
        <strong>Moneda Base:</strong> {{ base_currency.name }} ({{ base_currency.code }})
        - Todas las tasas se calculan en relación a esta moneda.
    </div>

    <!-- Tabla de Tasas -->
    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0">Tasas Actuales</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Moneda</th>
                            <th>Código</th>
                            <th>Tasa Actual</th>
                            <th>Última Actualización</th>
                            <th>Fuente</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for currency in currencies %}
                        <tr>
                            <td>
                                <strong>{{ currency.name }}</strong>
                            </td>
                            <td>
                                <span class="badge bg-secondary">{{ currency.code }}</span>
                            </td>
                            <td>
                                <span class="rate-value">{{ currency.rate|floatformat:4 }}</span>
                            </td>
                            <td>
                                <small class="rate-updated">
                                    {{ currency.last_updated|date:"d/m/Y H:i" }}
                                </small>
                            </td>
                            <td>
                                <span class="badge bg-info">{{ currency.source }}</span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" 
                                        data-action="edit-rate"
                                        data-currency-id="{{ currency.id }}"
                                        data-currency-code="{{ currency.code }}">
                                    <i class="bi bi-pencil"></i>
                                    Editar
                                </button>
                                <button class="btn btn-sm btn-outline-info"
                                        data-action="view-history"
                                        data-currency-id="{{ currency.id }}">
                                    <i class="bi bi-clock-history"></i>
                                    Histórico
                                </button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Última Actualización -->
    <div class="mt-3">
        <small class="text-muted">
            <i class="bi bi-clock"></i>
            Última actualización automática: {{ last_update.timestamp|date:"d/m/Y H:i" }}
            desde {{ last_update.source }}
        </small>
    </div>
</div>

<!-- Modal para Editar Tasa -->
<div class="modal fade" id="editRateModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Actualizar Tasa de Cambio</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="editRateForm">
                    <!-- Formulario aquí -->
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    Cancelar
                </button>
                <button type="button" class="btn btn-primary" id="saveRate">
                    Guardar Tasa
                </button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
// JavaScript para gestión de tasas
document.addEventListener('DOMContentLoaded', function() {
    // Actualizar todas las tasas
    document.getElementById('updateAllRates').addEventListener('click', function() {
        if (confirm('¿Desea actualizar todas las tasas desde la fuente externa?')) {
            updateAllRates();
        }
    });
    
    // Editar tasa individual
    document.querySelectorAll('[data-action="edit-rate"]').forEach(button => {
        button.addEventListener('click', function() {
            const currencyId = this.dataset.currencyId;
            const currencyCode = this.dataset.currencyCode;
            openEditRateModal(currencyId, currencyCode);
        });
    });
    
    function updateAllRates() {
        // Implementar actualización automática
        console.log('Actualizando todas las tasas...');
    }
    
    function openEditRateModal(currencyId, currencyCode) {
        // Abrir modal de edición
        const modal = new bootstrap.Modal(document.getElementById('editRateModal'));
        modal.show();
    }
});
</script>
{% endblock %}
```

---

### Paso 4: Registrar URL

```python
# forge_api/frontend/urls.py

urlpatterns = [
    # ... otras URLs ...
    
    # Monedas
    path('catalog/currencies/', CurrencyListView.as_view(), name='currency_list'),
    path('catalog/currencies/rates/', CurrencyRateView.as_view(), name='currency_rates'),  # NUEVA
    
    # ... más URLs ...
]
```

---

## 📝 Subtareas Específicas

### 4.2.1: Crear interfaz para actualización manual de tasas
- [ ] Crear vista `CurrencyRateView`
- [ ] Crear formulario `CurrencyRateForm`
- [ ] Crear template `currency_rate_management.html`
- [ ] Implementar modal de edición
- [ ] Agregar validaciones client-side

### 4.2.2: Desarrollar sistema de actualización automática
- [ ] Crear servicio `ExchangeRateService`
- [ ] Implementar método `update_rates_automatic()`
- [ ] Integrar con API externa (ej: exchangerate-api.com)
- [ ] Agregar manejo de errores
- [ ] Implementar logging de actualizaciones

### 4.2.3: Implementar validación de tasas razonables
- [ ] Crear método `validate_rate()` en servicio
- [ ] Definir rangos aceptables por moneda
- [ ] Agregar alertas para cambios drásticos
- [ ] Implementar confirmación para tasas inusuales

### 4.2.4: Agregar registro de fuente y timestamp
- [ ] Guardar fuente de cada actualización
- [ ] Registrar timestamp de actualización
- [ ] Mostrar información en interfaz
- [ ] Crear log de auditoría

---

## 🔗 Integración con API Backend

### Endpoints Necesarios:

```
GET    /api/currencies/rates/          # Obtener todas las tasas
POST   /api/currencies/rates/          # Actualizar tasa manual
POST   /api/currencies/rates/update/   # Actualizar todas automáticamente
GET    /api/currencies/{id}/history/   # Obtener histórico
```

---

## ✅ Criterios de Aceptación

La tarea estará completa cuando:

1. ✅ Existe una vista para gestionar tasas de cambio
2. ✅ Se pueden actualizar tasas manualmente
3. ✅ Existe un botón para actualización automática
4. ✅ Las tasas se validan antes de guardar
5. ✅ Se registra fuente y timestamp de cada actualización
6. ✅ La interfaz es responsive y usable
7. ✅ Hay manejo de errores apropiado
8. ✅ Se muestra feedback visual al usuario

---

## 📚 Referencias

- **Spec:** `.kiro/specs/forge-frontend-catalog-services-completion/`
- **Requirements:** Requirement 4.3, 4.4, 4.7
- **Design:** Sección 4 - Módulo Monedas
- **Tasks:** Tarea 4.2

---

## 🚀 Comando para Iniciar

```bash
# Leer la especificación completa
cat .kiro/specs/forge-frontend-catalog-services-completion/requirements.md
cat .kiro/specs/forge-frontend-catalog-services-completion/design.md

# Iniciar implementación
# El agente comenzará con la subtarea 4.2.1
```

---

**Estado:** ✅ Listo para Implementar  
**Prioridad:** Alta  
**Estimación:** 4-6 horas

---

**¿Deseas que comience con la implementación de la Tarea 4.2?**
