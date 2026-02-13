# Plan de Desarrollo: Integración OEM completa

## Resumen Ejecutivo

Este documento detalla el desarrollo completo de los componentes necesarios para integrar el módulo OEM con CATÁLOGO e INVENTARIO en FORGE-CMMS.

## Componentes a Desarrollar

### 1. OEM Equivalences (Modelo + API + Vista)
### 2. Fitment (Modelo + API + Vista)  
### 3. OEM Catalog Items - CRUD Completo
### 4. OEM Brands - CRUD Completo
### 5. Integración ProductMaster ↔ OEM (Servicio de importación)
### 6. Búsqueda Unificada (API de búsqueda cruzada)

---

## 1. OEM Equivalences (Equivalencias OEM ↔ Aftermarket)

### 1.1 Modelo (ya existe en models.py)
```python
class OEMEquivalence(models.Model):
    """OEM to aftermarket part equivalences"""
    equivalence_id = models.AutoField(primary_key=True)
    oem_part_number = models.CharField(max_length=30)
    oem_code = models.ForeignKey(OEMBrand, on_delete=models.CASCADE)
    aftermarket_sku = models.CharField(max_length=20, blank=True, null=True)
    equivalence_type = models.CharField(max_length=20, choices=EQUIVALENCE_TYPES)
    confidence_score = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(Technician, on_delete=models.SET_NULL)
    verified_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 1.2 Serializers
```python
# forge_api/core/serializers/oem_serializers.py

from rest_framework import serializers
from ..models import OEMEquivalence, OEMBrand, OEMCatalogItem

class OEMEquivalenceSerializer(serializers.ModelSerializer):
    oem_brand_name = serializers.CharField(source='oem_code.name', read_only=True)
    oem_brand_code = serializers.CharField(source='oem_code.oem_code', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)
    
    class Meta:
        model = OEMEquivalence
        fields = [
            'equivalence_id', 'oem_part_number', 'oem_code', 
            'oem_brand_name', 'oem_brand_code',
            'aftermarket_sku', 'equivalence_type', 'confidence_score',
            'notes', 'verified_by', 'verified_by_name', 'verified_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class OEMEquivalenceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OEMEquivalence
        fields = ['oem_part_number', 'oem_code', 'aftermarket_sku', 
                  'equivalence_type', 'confidence_score', 'notes']
```

### 1.3 API Views
```python
# forge_api/frontend/views/oem_equivalence_views.py

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from ..models import OEMEquivalence
from ..serializers.oem_serializers import OEMEquivalenceSerializer, OEMEquivalenceCreateSerializer

class OEMEquivalenceViewSet(viewsets.ModelViewSet):
    """API para gestión de equivalencias OEM ↔ Aftermarket"""
    queryset = OEMEquivalence.objects.select_related('oem_code', 'verified_by')
    serializer_class = OEMEquivalenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'oem_code__oem_code': ['exact'],
        'oem_part_number': ['exact', 'icontains'],
        'equivalence_type': ['exact'],
        'confidence_score': ['gte', 'lte'],
        'aftermarket_sku': ['icontains'],
    }
    
    search_fields = ['oem_part_number', 'aftermarket_sku', 'notes']
    ordering_fields = ['confidence_score', 'created_at', 'oem_part_number']
    ordering = ['-confidence_score', '-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OEMEquivalenceCreateSerializer
        return OEMEquivalenceSerializer
    
    def perform_create(self, serializer):
        serializer.save(verified_by=self.request.user.technician if hasattr(self.request.user, 'technician') else None)
```

### 1.4 URLs
```python
# En urls.py
path('api/oem/equivalences/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
    'get': 'list', 'post': 'create'
})),
path('api/oem/equivalences/<int:pk>/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
    'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
})),
```

### 1.5 Vista HTML
```html
<!-- forge_api/templates/frontend/oem/equivalence_list.html -->
{% extends 'frontend/base.html' %}

{% block content %}
<div class="container-fluid">
    <h1>Equivalencias OEM ↔ Aftermarket</h1>
    
    <!-- Filtros -->
    <form method="get" class="mb-4">
        <div class="row">
            <div class="col-md-3">
                <input type="text" name="search" class="form-control" 
                       placeholder="Buscar OEM o Aftermarket..." 
                       value="{{ request.GET.search|default:'' }}">
            </div>
            <div class="col-md-3">
                <select name="oem_code" class="form-select">
                    <option value="">Todas las marcas</option>
                    {% for brand in brands %}
                    <option value="{{ brand.oem_code }}" {% if request.GET.oem_code == brand.oem_code %}selected{% endif %}>
                        {{ brand.name }}
                    </option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-md-2">
                <button type="submit" class="btn btn-primary w-100">Buscar</button>
            </div>
        </div>
    </form>
    
    <!-- Tabla de equivalencias -->
    <table class="table table-striped">
        <thead>
            <tr>
                <th>OEM Part #</th>
                <th>Marca</th>
                <th>Aftermarket SKU</th>
                <th>Tipo</th>
                <th>Confianza</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
            {% for eq in equivalences %}
            <tr>
                <td>{{ eq.oem_part_number }}</td>
                <td>{{ eq.oem_code.name }}</td>
                <td>{{ eq.aftermarket_sku|default:'N/A' }}</td>
                <td>
                    <span class="badge bg-{% if eq.equivalence_type == 'DIRECT' %}success{% elif eq.equivalence_type == 'COMPATIBLE' %}info{% else %}secondary{% endif %}">
                        {{ eq.get_equivalence_type_display }}
                    </span>
                </td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-{% if eq.confidence_score >= 80 %}success{% elif eq.confidence_score >= 60 %}info{% else %}warning{% endif %}" 
                             style="width: {{ eq.confidence_score }}%;">
                            {{ eq.confidence_score|default:0 }}%
                        </div>
                    </div>
                </td>
                <td>
                    <a href="{% url 'frontend:oem_equivalence_edit' eq.equivalence_id %}" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-pencil"></i>
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

---

## 2. Fitment (Compatibilidad Equipo-Producto)

### 2.1 Modelo
```python
# forge_api/core/models.py (ya existe)

class Fitment(models.Model):
    """Fitment compatibility between products and equipment"""
    fitment_id = models.AutoField(primary_key=True)
    internal_sku = models.CharField(max_length=20, blank=True, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    score = models.SmallIntegerField(default=100)
    notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(Technician, on_delete=models.SET_NULL)
    verified_date = models.DateField(blank=True, null=True)
    is_primary_fit = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2.2 Serializers
```python
# forge_api/core/serializers/inventory_serializers.py

class FitmentSerializer(serializers.ModelSerializer):
    equipment_info = serializers.SerializerMethodField()
    product_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Fitment
        fields = ['fitment_id', 'internal_sku', 'equipment_info', 'product_info',
                  'score', 'notes', 'is_primary_fit', 'verified_by', 'verified_date']
    
    def get_equipment_info(self, obj):
        return {
            'id': obj.equipment.equipment_id,
            'code': obj.equipment.equipment_code,
            'brand': obj.equipment.brand,
            'model': obj.equipment.model,
            'year': obj.equipment.year,
        }
    
    def get_product_info(self, obj):
        if obj.internal_sku:
            try:
                from ..models import ProductMaster
                product = ProductMaster.objects.get(internal_sku=obj.internal_sku)
                return {
                    'sku': product.internal_sku,
                    'name': product.name,
                    'brand': product.brand,
                }
            except ProductMaster.DoesNotExist:
                return None
        return None

class FitmentAutoCreateSerializer(serializers.Serializer):
    """Serializer para crear fitment automático desde OEM Catalog"""
    equipment_id = serializers.IntegerField()
    oem_part_number = serializers.CharField(required=False)
    oem_code = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
```

### 2.3 API Views
```python
# forge_api/frontend/views/fitment_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from ..models import Fitment, Equipment, ProductMaster, OEMCatalogItem
from ..serializers.inventory_serializers import FitmentSerializer

class FitmentViewSet(viewsets.ModelViewSet):
    """API para gestión de compatibilidad (fitment)"""
    queryset = Fitment.objects.select_related('equipment', 'verified_by')
    serializer_class = FitmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    filterset_fields = {
        'equipment__brand': ['exact', 'icontains'],
        'equipment__model': ['icontains'],
        'equipment__year': ['gte', 'lte', 'exact'],
        'internal_sku': ['exact', 'icontains'],
        'score': ['gte'],
    }
    search_fields = ['equipment__brand', 'equipment__model', 'internal_sku']
    
    @action(detail=False, methods=['get'])
    def by_equipment(self, request):
        """Obtener productos compatibles para un equipo específico"""
        equipment_id = request.query_params.get('equipment_id')
        if not equipment_id:
            return Response({'error': 'equipment_id es requerido'}, status=400)
        
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
        except Equipment.DoesNotExist:
            return Response({'error': 'Equipo no encontrado'}, status=404)
        
        # Obtener fitments directos
        fitments = self.get_queryset().filter(equipment=equipment)
        
        # Si no hay fitments, buscar automáticamente en OEM Catalog
        if not fitments.exists():
            fitments = self._auto_create_fitments(equipment)
        
        serializer = self.get_serializer(fitments, many=True)
        return Response({
            'equipment': {
                'id': equipment.equipment_id,
                'brand': equipment.brand,
                'model': equipment.model,
                'year': equipment.year,
            },
            'fitments': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def auto_create(self, request):
        """Crear automáticamente fitments basados en compatibilidad OEM"""
        serializer = FitmentAutoCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        equipment_id = serializer.validated_data['equipment_id']
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
        except Equipment.DoesNotExist:
            return Response({'error': 'Equipo no encontrado'}, status=404)
        
        fitments = self._auto_create_fitments(equipment)
        serializer = self.get_serializer(fitments, many=True)
        return Response({
            'message': f'{len(fitments)} compatibilidades creadas',
            'fitments': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def _auto_create_fitments(self, equipment):
        """Buscar automáticamente productos compatibles basados en OEM"""
        fitments = []
        
        # Buscar en ProductMaster por marca/modelo
        products = ProductMaster.objects.filter(
            Q(brand__icontains=equipment.brand) |
            Q(oem_ref__icontains=equipment.model)
        ).filter(is_active=True)[:50]  # Limitar resultados
        
        for product in products:
            # Calcular score de compatibilidad
            score = self._calculate_compatibility_score(product, equipment)
            
            fitment = Fitment(
                internal_sku=product.internal_sku,
                equipment=equipment,
                score=score,
                is_primary_fit=score >= 90,
                notes='Auto-creado por compatibilidad'
            )
            fitments.append(fitment)
        
        # Bulk create
        if fitments:
            Fitment.objects.bulk_create(fitments)
        
        return fitments
    
    def _calculate_compatibility_score(self, product, equipment):
        """Calcular score de compatibilidad"""
        score = 50  # Base
        
        # Misma marca
        if product.brand and equipment.brand:
            if product.brand.lower() == equipment.brand.lower():
                score += 30
        
        # Referencias OEM
        if product.oem_ref:
            if equipment.model and equipment.model.lower() in product.oem_ref.lower():
                score += 10
            if equipment.vin and equipment.vin[:8] in product.oem_ref:
                score += 10
        
        return min(score, 100)
```

### 2.4 URLs
```python
# En urls.py
path('api/fitments/', fitment_views.FitmentViewSet.as_view({
    'get': 'list', 'post': 'create'
})),
path('api/fitments/<int:pk>/', fitment_views.FitmentViewSet.as_view({
    'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
})),
path('api/fitments/by-equipment/', fitment_views.FitmentViewSet.as_view({'get': 'by_equipment'})),
path('api/fitments/auto-create/', fitment_views.FitmentViewSet.as_view({'post': 'auto_create'})),
```

---

## 3. OEM Catalog Items - CRUD Completo

### 3.1 Views Completas
```python
# forge_api/frontend/views/oem_crud_views.py (ya existe, needs updates)

class OEMCatalogItemListView(LoginRequiredMixin, APIClientMixin, ListView):
    """Vista lista completa del catálogo OEM"""
    template_name = 'frontend/oem/catalog_item_list.html'
    context_object_name = 'items'
    paginate_by = 25
    
    def get_queryset(self):
        # Obtener filtros de request
        return self._get_oem_catalog_items()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = self._get_oem_brands()
        context['categories'] = self._get_taxonomy_groups()
        context['item_types'] = dict(OEMCatalogItem.ITEM_TYPES)
        return context


class OEMCatalogItemCreateView(LoginRequiredMixin, APIClientMixin, CreateView):
    """Crear nuevo item en catálogo OEM"""
    template_name = 'frontend/oem/catalog_item_form.html'
    form_class = OEMCatalogItemForm
    
    def form_valid(self, form):
        # Guardar a través de API
        api_client = self.get_api_client()
        data = form.cleaned_data
        
        # Transformar datos para API
        api_data = {
            'oem_code': data['oem_code'].oem_code,
            'item_type': data['item_type'],
            'part_number': data['part_number'],
            'description_es': data.get('description_es', ''),
            'description_en': data.get('description_en', ''),
            'group_code': data.get('group_code').group_code if data.get('group_code') else None,
            'list_price': data.get('list_price'),
            'net_price': data.get('net_price'),
            'currency_code': data.get('currency_code', 'USD'),
            'is_active': data.get('is_active', True),
        }
        
        try:
            result = api_client.create_oem_catalog_item(api_data)
            messages.success(self.request, 'Item OEM creado exitosamente')
            return redirect('frontend:oem_catalog_item_list')
        except APIException as e:
            messages.error(self.request, f'Error: {str(e)}')
            return self.form_invalid(form)
```

### 3.2 Formularios
```python
# forge_api/frontend/forms/oem_forms.py

from django import forms
from ..models import OEMBrand, TaxonomyGroup

class OEMCatalogItemForm(forms.Form):
    """Formulario para crear/editar items OEM"""
    
    oem_code = forms.ModelChoiceField(
        queryset=OEMBrand.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccionar marca"
    )
    
    item_type = forms.ChoiceField(
        choices=OEMCatalogItem.ITEM_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    part_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de parte OEM'})
    )
    
    description_es = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    group_code = forms.ModelChoiceField(
        queryset=TaxonomyGroup.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccionar categoría"
    )
    
    list_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    net_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    currency_code = forms.ChoiceField(
        choices=[('USD', 'USD'), ('EUR', 'EUR'), ('MXN', 'MXN')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
```

---

## 4. OEM Brands - CRUD Completo

### 4.1 Views
```python
# En oem_views.py ya existe OEMManufacturerManagementView, pero agregar:

class OEMBrandCreateView(LoginRequiredMixin, APIClientMixin, CreateView):
    """Crear nueva marca OEM"""
    template_name = 'frontend/oem/brand_form.html'
    form_class = OEMBrandForm
    
    def form_valid(self, form):
        api_client = self.get_api_client()
        data = form.cleaned_data
        
        try:
            api_client.create_oem_brand(data)
            messages.success(self.request, 'Marca OEM creada exitosamente')
            return redirect('frontend:oem_brand_list')
        except APIException as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class OEMBrandUpdateView(LoginRequiredMixin, APIClientMixin, UpdateView):
    """Editar marca OEM existente"""
    template_name = 'frontend/oem/brand_form.html'
    form_class = OEMBrandForm
    
    def get_object(self, queryset=None):
        brand_id = self.kwargs.get('pk')
        api_client = self.get_api_client()
        return api_client.get_oem_brand(brand_id)
    
    def form_valid(self, form):
        api_client = self.get_api_client()
        data = form.cleaned_data
        brand_id = self.kwargs.get('pk')
        
        try:
            api_client.update_oem_brand(brand_id, data)
            messages.success(self.request, 'Marca OEM actualizada')
            return redirect('frontend:oem_brand_list')
        except APIException as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
```

---

## 5. Integración ProductMaster ↔ OEM (Servicio de Importación)

### 5.1 Servicio de Integración
```python
# forge_api/frontend/services/oem_integration_service.py

import logging
from decimal import Decimal
from django.db import transaction
from ..models import ProductMaster, OEMCatalogItem, OEMBrand, TaxonomyGroup, Fitment

logger = logging.getLogger(__name__)

class OEMIntegrationService:
    """Servicio para integrar datos OEM con ProductMaster"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def import_oem_to_product_master(self, oem_catalog_item_id, supplier_id=None):
        """
        Importar un item del catálogo OEM a ProductMaster
        """
        # Obtener item OEM
        oem_item = self.api_client.get_oem_catalog_item(oem_catalog_item_id)
        
        if not oem_item:
            raise ValueError(f"Item OEM {oem_catalog_item_id} no encontrado")
        
        # Generar SKU interno
        internal_sku = self._generate_internal_sku(oem_item)
        
        # Crear o actualizar ProductMaster
        product, created = ProductMaster.objects.update_or_create(
            internal_sku=internal_sku,
            defaults={
                'name': oem_item.get('description_es', oem_item.get('description_en', '')),
                'description': oem_item.get('description_es', ''),
                'brand': oem_item.get('oem_code', {}).get('name', ''),
                'oem_ref': oem_item.get('part_number'),
                'oem_code': oem_item.get('oem_code', {}).get('oem_code', ''),
                'group_code': oem_item.get('group_code', {}).get('group_code', '') if oem_item.get('group_code') else '',
                'standard_cost': Decimal(oem_item.get('list_price', 0)) if oem_item.get('list_price') else Decimal('0.00'),
                'is_active': oem_item.get('is_active', True),
                'source_code': 'OEM',  # Default source
                'condition_code': 'NEW',  # Default condition
                'uom_code': 'EA',  # Default UOM
            }
        )
        
        logger.info(f"Producto {'creado' if created else 'actualizado'}: {internal_sku}")
        
        return product
    
    def bulk_import_by_brand(self, oem_brand_code, batch_size=100):
        """
        Importar todos los items de una marca OEM
        """
        # Obtener todos los items de la marca
        oem_items = self.api_client.get_oem_catalog_items(
            oem_code=oem_brand_code,
            is_active=True
        )
        
        imported = 0
        for item in oem_items[:batch_size]:
            try:
                self.import_oem_to_product_master(item.get('catalog_id'))
                imported += 1
            except Exception as e:
                logger.error(f"Error importando item {item.get('catalog_id')}: {e}")
        
        return imported
    
    def create_fitment_from_oem(self, oem_catalog_item_id, equipment_id):
        """
        Crear fitment (compatibilidad) desde datos OEM
        """
        oem_item = self.api_client.get_oem_catalog_item(oem_catalog_item_id)
        if not oem_item:
            raise ValueError(f"Item OEM {oem_catalog_item_id} no encontrado")
        
        # Buscar producto relacionado
        try:
            product = ProductMaster.objects.get(oem_ref=oem_item.get('part_number'))
        except ProductMaster.DoesNotExist:
            # Primero importar el producto
            product = self.import_oem_to_product_master(oem_catalog_item_id)
        
        # Crear fitment
        equipment = Equipment.objects.get(equipment_id=equipment_id)
        
        fitment, created = Fitment.objects.update_or_create(
            internal_sku=product.internal_sku,
            equipment=equipment,
            defaults={
                'score': self._calculate_compatibility(product, equipment, oem_item),
                'is_primary_fit': True,
                'notes': f'Importado desde OEM: {oem_item.get("part_number")}'
            }
        )
        
        return fitment
    
    def _generate_internal_sku(self, oem_item):
        """Generar SKU interno único"""
        oem_code = oem_item.get('oem_code', {}).get('oem_code', 'GEN')
        part_number = oem_item.get('part_number', '')[:10].replace('-', '').replace(' ', '')
        
        # Usar timestamp como sufijo único
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')[-6:]
        
        return f"{oem_code[:3].upper()}{part_number.upper()}{timestamp}"
    
    def _calculate_compatibility(self, product, equipment, oem_item):
        """Calcular score de compatibilidad"""
        score = 50
        
        # Misma marca
        if product.brand and equipment.brand:
            if product.brand.lower() == equipment.brand.lower():
                score += 30
        
        # Verificar año de producción
        if oem_item.get('year_start') and oem_item.get('year_end'):
            if oem_item['year_start'] <= equipment.year <= oem_item['year_end']:
                score += 20
        
        return min(score, 100)
```

### 5.2 Vista de Importación
```python
# forge_api/frontend/views/oem_import_views.py

class OEMImportView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para importar datos OEM a inventario"""
    template_name = 'frontend/oem/oem_import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = self._get_oem_brands()
        return context
    
    def post(self, request, *args, **kwargs):
        import_type = request.POST.get('import_type')
        
        if import_type == 'single':
            oem_catalog_item_id = request.POST.get('oem_catalog_item_id')
            service = OEMIntegrationService(self.get_api_client())
            
            try:
                product = service.import_oem_to_product_master(oem_catalog_item_id)
                messages.success(request, f'Producto importado: {product.internal_sku}')
            except Exception as e:
                messages.error(request, str(e))
        
        elif import_type == 'brand':
            oem_brand_code = request.POST.get('oem_brand_code')
            service = OEMIntegrationService(self.get_api_client())
            
            imported = service.bulk_import_by_brand(oem_brand_code)
            messages.success(request, f'{imported} productos importados de la marca')
        
        return self.get(request, *args, **kwargs)
```

---

## 6. Búsqueda Unificada (API de Búsqueda Cruzada)

### 6.1 Servicio de Búsqueda Unificada
```python
# forge_api/frontend/services/unified_search_service.py

import logging
from django.db.models import Q
from ..models import ProductMaster, OEMCatalogItem, OEMEquivalence, Fitment

logger = logging.getLogger(__name__)

class UnifiedSearchService:
    """Servicio de búsqueda unificada entre todos los catálogos"""
    
    def search(self, query, search_type='all', filters=None):
        """
        Búsqueda unificada que retorna resultados de:
        - ProductMaster (inventario)
        - OEMCatalogItem (catálogo OEM)
        - OEMEquivalence (equivalencias)
        """
        results = {
            'products': [],
            'oem_items': [],
            'equivalences': [],
            'total_count': 0,
        }
        
        if search_type in ['all', 'products']:
            results['products'] = self._search_products(query, filters)
        
        if search_type in ['all', 'oem']:
            results['oem_items'] = self._search_oem_catalog(query, filters)
        
        if search_type in ['all', 'equivalences']:
            results['equivalences'] = self._search_equivalences(query, filters)
        
        results['total_count'] = (
            len(results['products']) + 
            len(results['oem_items']) + 
            len(results['equivalences'])
        )
        
        return results
    
    def _search_products(self, query, filters=None):
        """Buscar en ProductMaster"""
        products = ProductMaster.objects.filter(is_active=True)
        
        # Búsqueda por texto
        if query:
            products = products.filter(
                Q(internal_sku__icontains=query) |
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__icontains=query) |
                Q(oem_ref__icontains=query) |
                Q(barcode__icontains=query)
            )
        
        # Aplicar filtros adicionales
        if filters:
            if filters.get('brand'):
                products = products.filter(brand__icontains=filters['brand'])
            if filters.get('group_code'):
                products = products.filter(group_code=filters['group_code'])
        
        # Obtener información de stock
        from ..models import Stock
        results = []
        for product in products[:50]:  # Limitar resultados
            stock_info = Stock.objects.filter(product=product).aggregate(
                total_qty=models.Sum('qty_on_hand')
            )
            results.append({
                'type': 'product',
                'sku': product.internal_sku,
                'name': product.name,
                'brand': product.brand,
                'oem_ref': product.oem_ref,
                'stock': stock_info['total_qty'] or 0,
                'price': str(product.standard_cost),
                'url': f'/inventory/products/{product.internal_sku}/',
            })
        
        return results
    
    def _search_oem_catalog(self, query, filters=None):
        """Buscar en catálogo OEM"""
        items = OEMCatalogItem.objects.filter(is_active=True)
        
        if query:
            items = items.filter(
                Q(part_number__icontains=query) |
                Q(description_es__icontains=query) |
                Q(description_en__icontains=query)
            )
        
        if filters:
            if filters.get('oem_code'):
                items = items.filter(oem_code__oem_code=filters['oem_code'])
            if filters.get('item_type'):
                items = items.filter(item_type=filters['item_type'])
        
        results = []
        for item in items[:50]:
            results.append({
                'type': 'oem',
                'part_number': item.part_number,
                'brand': item.oem_code.name,
                'description': item.description_es or item.description_en,
                'price': str(item.list_price) if item.list_price else None,
                'url': f'/oem/catalog/{item.catalog_id}/',
            })
        
        return results
    
    def _search_equivalences(self, query, filters=None):
        """Buscar equivalencias OEM ↔ Aftermarket"""
        equivalences = OEMEquivalence.objects.all()
        
        if query:
            equivalences = equivalences.filter(
                Q(oem_part_number__icontains=query) |
                Q(aftermarket_sku__icontains=query)
            )
        
        results = []
        for eq in equivalences[:50]:
            results.append({
                'type': 'equivalence',
                'oem_part_number': eq.oem_part_number,
                'brand': eq.oem_code.name,
                'aftermarket_sku': eq.aftermarket_sku,
                'equivalence_type': eq.equivalence_type,
                'confidence': eq.confidence_score,
                'url': f'/oem/equivalences/{eq.equivalence_id}/',
            })
        
        return results
```

### 6.2 API View de Búsqueda Unificada
```python
# forge_api/frontend/views/unified_search_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.unified_search_service import UnifiedSearchService

class UnifiedSearchAPIView(APIView):
    """API de búsqueda unificada"""
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')
        
        if not query:
            return Response({
                'error': 'Parámetro de búsqueda "q" es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtros adicionales
        filters = {}
        if request.query_params.get('brand'):
            filters['brand'] = request.query_params.get('brand')
        if request.query_params.get('oem_code'):
            filters['oem_code'] = request.query_params.get('oem_code')
        if request.query_params.get('item_type'):
            filters['item_type'] = request.query_params.get('item_type')
        
        service = UnifiedSearchService()
        results = service.search(query, search_type, filters)
        
        return Response(results)
```

### 6.3 URLs de Búsqueda
```python
# En urls.py
path('api/search/unified/', unified_search_views.UnifiedSearchAPIView.as_view()),
```

### 6.4 Template de Búsqueda
```html
<!-- forge_api/templates/frontend/search/unified_search.html -->
{% extends 'frontend/base.html' %}

{% block content %}
<div class="container-fluid">
    <h1>Búsqueda Unificada</h1>
    
    <!-- Formulario de búsqueda -->
    <form method="get" class="mb-4">
        <div class="input-group">
            <input type="text" name="q" class="form-control form-control-lg" 
                   placeholder="Buscar productos, números OEM, equivalencias..."
                   value="{{ request.GET.q|default:'' }}">
            <select name="type" class="form-select" style="max-width: 200px;">
                <option value="all" {% if request.GET.type == 'all' %}selected{% endif %}>Todo</option>
                <option value="products" {% if request.GET.type == 'products' %}selected{% endif %}>Inventario</option>
                <option value="oem" {% if request.GET.type == 'oem' %}selected{% endif %}>Catálogo OEM</option>
                <option value="equivalences" {% if request.GET.type == 'equivalences' %}selected{% endif %}>Equivalencias</option>
            </select>
            <button type="submit" class="btn btn-primary btn-lg">
                <i class="bi bi-search"></i> Buscar
            </button>
        </div>
    </form>
    
    {% if results %}
    <div class="row">
        <!-- Resultados de Inventario -->
        {% if results.products %}
        <div class="col-12 mb-4">
            <h4><i class="bi bi-box-seam"></i> Inventario ({{ results.products|length }})</h4>
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>SKU</th>
                        <th>Nombre</th>
                        <th>Marca</th>
                        <th>OEM Ref</th>
                        <th>Stock</th>
                        <th>Precio</th>
                    </tr>
                </thead>
                <tbody>
                    {% for product in results.products %}
                    <tr>
                        <td><a href="{{ product.url }}">{{ product.sku }}</a></td>
                        <td>{{ product.name }}</td>
                        <td>{{ product.brand|default:'N/A' }}</td>
                        <td>{{ product.oem_ref|default:'N/A' }}</td>
                        <td>
                            <span class="badge bg-{% if product.stock > 0 %}success{% else %}danger{% endif %}">
                                {{ product.stock }}
                            </span>
                        </td>
                        <td>${{ product.price }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <!-- Resultados de OEM -->
        {% if results.oem_items %}
        <div class="col-12 mb-4">
            <h4><i class="bi bi-gear"></i> Catálogo OEM ({{ results.oem_items|length }})</h4>
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>Part Number</th>
                        <th>Marca</th>
                        <th>Descripción</th>
                        <th>Precio Lista</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in results.oem_items %}
                    <tr>
                        <td><a href="{{ item.url }}">{{ item.part_number }}</a></td>
                        <td>{{ item.brand }}</td>
                        <td>{{ item.description|truncatewords:10 }}</td>
                        <td>${{ item.price|default:'N/A' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        <!-- Resultados de Equivalencias -->
        {% if results.equivalences %}
        <div class="col-12 mb-4">
            <h4><i class="bi bi-arrow-left-right"></i> Equivalencias ({{ results.equivalences|length }})</h4>
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>OEM Part #</th>
                        <th>Marca</th>
                        <th>Aftermarket</th>
                        <th>Tipo</th>
                        <th>Confianza</th>
                    </tr>
                </thead>
                <tbody>
                    {% for eq in results.equivalences %}
                    <tr>
                        <td><a href="{{ eq.url }}">{{ eq.oem_part_number }}</a></td>
                        <td>{{ eq.brand }}</td>
                        <td>{{ eq.aftermarket_sku|default:'N/A' }}</td>
                        <td>{{ eq.equivalence_type }}</td>
                        <td>
                            <div class="progress" style="width: 100px;">
                                <div class="progress-bar bg-info" style="width: {{ eq.confidence }}%;">
                                    {{ eq.confidence }}%
                                </div>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
    {% elif request.GET.q %}
    <div class="alert alert-info">
        <i class="bi bi-info-circle me-2"></i>
        No se encontraron resultados para "{{ request.GET.q }}"
    </div>
    {% endif %}
</div>
{% endblock %}
```

---

## Resumen de Archivos a Crear/Modificar

| Archivo | Acción |
|---------|--------|
| `forge_api/core/serializers/oem_serializers.py` | Crear |
| `forge_api/frontend/views/oem_equivalence_views.py` | Crear |
| `forge_api/frontend/views/fitment_views.py` | Crear |
| `forge_api/frontend/views/oem_import_views.py` | Crear |
| `forge_api/frontend/views/unified_search_views.py` | Crear |
| `forge_api/frontend/services/oem_integration_service.py` | Crear |
| `forge_api/frontend/services/unified_search_service.py` | Crear |
| `forge_api/templates/frontend/oem/equivalence_list.html` | Crear |
| `forge_api/templates/frontend/oem/oem_import.html` | Crear |
| `forge_api/templates/frontend/search/unified_search.html` | Crear |
| `forge_api/frontend/urls.py` | Modificar (agregar URLs) |

---

¿Quieres que comience a implementar alguno de estos componentes en específico?