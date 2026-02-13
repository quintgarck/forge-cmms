"""
Views for Reference Code management (Fuel, Transmission, Color, etc.)
Implements complete CRUD with category-based organization and validation
"""
import logging
import csv
import io
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.views import View

from ..services.api_client import ForgeAPIClient, APIException
from ..mixins import APIClientMixin
from ..forms.reference_code_forms import ReferenceCodeForm, ReferenceCodeImportForm
from ..utils.navigation import BreadcrumbBuilder
from core.models import BrandType, ProductCategory, ProductType

logger = logging.getLogger(__name__)

# Catálogos internos para productos (ORM, no API): tipos de marca, categorías y tipos de producto
PRODUCT_CATALOG_CONFIG = {
    'brand_types': {
        'title': 'Tipos de marca',
        'icon': 'bi-tag',
        'color': 'info',
        'description': 'Tipos de marca usados al dar de alta marcas/productos',
        'model': BrandType,
        'create_url_name': 'frontend:product_catalog_brand_type_create',
        'edit_url_name': 'frontend:product_catalog_brand_type_edit',
        'delete_url_name': 'frontend:product_catalog_brand_type_delete',
    },
    'product_categories': {
        'title': 'Categorías de producto',
        'icon': 'bi-folder2',
        'color': 'success',
        'description': 'Categorías para productos de inventario',
        'model': ProductCategory,
        'create_url_name': 'frontend:product_catalog_category_create',
        'edit_url_name': 'frontend:product_catalog_category_edit',
        'delete_url_name': 'frontend:product_catalog_category_delete',
    },
    'product_types': {
        'title': 'Tipos de producto',
        'icon': 'bi-box',
        'color': 'warning',
        'description': 'Tipos de producto en inventario',
        'model': ProductType,
        'create_url_name': 'frontend:product_catalog_type_create',
        'edit_url_name': 'frontend:product_catalog_type_edit',
        'delete_url_name': 'frontend:product_catalog_type_delete',
    },
}

# Intentar importar openpyxl para soporte de Excel
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl no está instalado. El soporte para archivos Excel estará limitado.")


def read_excel_file(file_obj):
    """
    Lee un archivo Excel y retorna una lista de diccionarios.
    Asume que la primera fila contiene los headers.
    """
    if not OPENPYXL_AVAILABLE:
        raise Exception("La librería openpyxl no está instalada. Instálala con: pip install openpyxl")
    
    try:
        workbook = openpyxl.load_workbook(file_obj, data_only=True)
        sheet = workbook.active
        
        # Obtener headers de la primera fila
        headers = []
        for cell in sheet[1]:
            headers.append(str(cell.value) if cell.value else '')
        
        # Mapear headers comunes
        header_mapping = {}
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            if header_lower in ['código', 'codigo', 'code']:
                header_mapping[i] = 'Código'
            elif header_lower in ['descripción', 'descripcion', 'description']:
                header_mapping[i] = 'Descripción'
            elif header_lower in ['activo', 'active', 'estado']:
                header_mapping[i] = 'Activo'
            else:
                header_mapping[i] = header
        
        # Leer filas
        rows = []
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            row_dict = {}
            for i, cell_value in enumerate(row):
                if i in header_mapping:
                    row_dict[header_mapping[i]] = str(cell_value) if cell_value is not None else ''
            if row_dict:  # Solo agregar si hay datos
                rows.append(row_dict)
        
        return rows
    except Exception as e:
        logger.error(f"Error leyendo archivo Excel: {e}")
        raise Exception(f"Error al leer el archivo Excel: {str(e)}")


def read_csv_file(file_obj):
    """
    Lee un archivo CSV y retorna una lista de diccionarios.
    """
    try:
        decoded_file = file_obj.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(decoded_file))
        return list(csv_reader)
    except UnicodeDecodeError:
        # Intentar con latin-1 si utf-8 falla
        try:
            file_obj.seek(0)
            decoded_file = file_obj.read().decode('latin-1')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            return list(csv_reader)
        except Exception as e:
            logger.error(f"Error leyendo CSV con latin-1: {e}")
            raise Exception(f"Error al leer el archivo CSV. Asegúrate que esté codificado en UTF-8.")
    except Exception as e:
        logger.error(f"Error leyendo CSV: {e}")
        raise Exception(f"Error al leer el archivo CSV: {str(e)}")


def read_import_file(file_obj):
    """
    Lee un archivo de importación (CSV o Excel) y retorna una lista de diccionarios.
    """
    file_name = getattr(file_obj, 'name', '')
    ext = os.path.splitext(file_name)[1].lower()
    
    if ext in ['.xlsx', '.xls']:
        return read_excel_file(file_obj)
    elif ext == '.csv':
        return read_csv_file(file_obj)
    else:
        raise Exception(f"Formato de archivo no soportado: {ext}. Use CSV, XLS o XLSX.")


# Mapeo de categorías a endpoints de API
CATEGORY_ENDPOINT_MAP = {
    'fuel': 'fuel-codes',
    'transmission': 'transmission-codes',
    'color': 'color-codes',
    'drivetrain': 'drivetrain-codes',
    'condition': 'condition-codes',
    'aspiration': 'aspiration-codes',
}

# Mapeo de campos por categoría (código_columna: campo_api)
CATEGORY_FIELD_MAP = {
    'fuel': {
        'code_field': 'fuel_code',
        'name_field': 'name_es',
        'extra_fields': {'name_en': ''}
    },
    'transmission': {
        'code_field': 'transmission_code',
        'name_field': 'name_es',
        'extra_fields': {'name_en': ''}
    },
    'color': {
        'code_field': 'color_code',
        'name_field': 'name_es',
        'extra_fields': {'name_en': '', 'hex_code': '#000000'}
    },
    'drivetrain': {
        'code_field': 'drivetrain_code',
        'name_field': 'name_es',
        'extra_fields': {'name_en': ''}
    },
    'condition': {
        'code_field': 'condition_code',
        'name_field': 'name_es',
        'extra_fields': {'name_en': '', 'requires_core': False}
    },
    'aspiration': {
        'code_field': 'aspiration_code',
        'name_field': 'name_es',
        'extra_fields': {'name_en': ''}
    },
}

# Configuración de categorías
CATEGORY_CONFIG = {
    'fuel': {
        'title': 'Códigos de Combustible',
        'icon': 'bi-fuel-pump',
        'color': 'danger',
        'description': 'Tipos de combustible para equipos'
    },
    'transmission': {
        'title': 'Códigos de Transmisión',
        'icon': 'bi-gear-wide-connected',
        'color': 'primary',
        'description': 'Tipos de transmisión'
    },
    'color': {
        'title': 'Códigos de Color',
        'icon': 'bi-palette',
        'color': 'info',
        'description': 'Colores estándar'
    },
    'drivetrain': {
        'title': 'Códigos de Tracción',
        'icon': 'bi-arrow-left-right',
        'color': 'warning',
        'description': 'Tipos de tracción'
    },
    'condition': {
        'title': 'Códigos de Condición',
        'icon': 'bi-check-circle',
        'color': 'success',
        'description': 'Estados de condición'
    },
    'aspiration': {
        'title': 'Códigos de Aspiración',
        'icon': 'bi-wind',
        'color': 'secondary',
        'description': 'Tipos de aspiración del motor'
    },
}


class ReferenceCodeListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Lista de códigos de referencia organizados por categorías"""
    template_name = 'frontend/catalog/reference_code_list.html'
    login_url = 'frontend:login'
    
    # Configuración de caché
    CACHE_TIMEOUT = 300  # 5 minutos
    
    def _get_cached_category_data(self, api_client, category_key, endpoint, use_cache=True):
        """Obtiene datos de una categoría con caché"""
        cache_key = f'ref_code_{category_key}'
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"Cache hit para {category_key}")
                return cached_data
        
        try:
            response = api_client.get(f'{endpoint}/')
            data = {
                'results': response.get('results', []),
                'count': response.get('count', 0),
                'error': None
            }
            
            if use_cache:
                cache.set(cache_key, data, self.CACHE_TIMEOUT)
            
            return data
        except APIException as e:
            logger.error(f"Error loading {category_key} codes: {e}")
            return {'results': [], 'count': 0, 'error': str(e)}
    
    def _invalidate_category_cache(self, category_key=None):
        """Invalida el caché de una o todas las categorías"""
        if category_key:
            cache.delete(f'ref_code_{category_key}')
        else:
            for cat_key in CATEGORY_ENDPOINT_MAP.keys():
                cache.delete(f'ref_code_{cat_key}')
    
    def _load_single_category(self, api_client, category_key, endpoint, selected_category, search_query, status_filter, sort_by, sort_order):
        """Carga datos de una sola categoría (para uso con ThreadPoolExecutor)"""
        try:
            # Usar solo conteo para categorías no seleccionadas
            if category_key != selected_category:
                # Para categorías no seleccionadas, obtener solo el count
                try:
                    # Usar endpoint con page_size=1 para obtener count rápido
                    response = api_client.get(f'{endpoint}/', params={'page_size': 1})
                    count = response.get('count', 0)
                    codes = []
                except APIException as e:
                    count = 0
                    codes = []
            else:
                # Para la categoría seleccionada, cargar todo
                data = self._get_cached_category_data(api_client, category_key, endpoint, use_cache=True)
                codes = data.get('results', [])
                count = data.get('count', 0)
                
                # Aplicar filtros solo a la categoría seleccionada
                if search_query:
                    codes = [
                        code for code in codes
                        if search_query.lower() in code.get('code', '').lower() or
                           search_query.lower() in code.get('description', '').lower()
                    ]
                
                # Filtrar por estado
                if status_filter == 'active':
                    codes = [code for code in codes if code.get('is_active', True)]
                elif status_filter == 'inactive':
                    codes = [code for code in codes if not code.get('is_active', True)]
                
                # Ordenar
                reverse = (sort_order == 'desc')
                if sort_by == 'code':
                    codes = sorted(codes, key=lambda x: x.get('code', ''), reverse=reverse)
                elif sort_by == 'description':
                    codes = sorted(codes, key=lambda x: x.get('description', ''), reverse=reverse)
            
            return {
                'category_key': category_key,
                'data': {
                    **CATEGORY_CONFIG[category_key],
                    'count': count,
                    'filtered_count': len(codes) if category_key == selected_category else 0,
                    'codes': codes
                },
                'error': None
            }
        except Exception as e:
            return {
                'category_key': category_key,
                'data': {
                    **CATEGORY_CONFIG[category_key],
                    'count': 0,
                    'filtered_count': 0,
                    'codes': []
                },
                'error': str(e)
            }
    
    def _load_product_catalog_category(self, category_key, config, selected_category, search_query, status_filter, sort_by, sort_order):
        """Carga datos de una categoría de catálogo interno (ORM)."""
        model = config['model']
        qs = model.objects.all().order_by('display_order', 'code')
        count = qs.count()
        codes = []
        if category_key == selected_category:
            if search_query:
                qs = qs.filter(code__icontains=search_query) | qs.filter(name_es__icontains=search_query)
            if status_filter == 'active':
                qs = qs.filter(is_active=True)
            elif status_filter == 'inactive':
                qs = qs.filter(is_active=False)
            reverse_order = sort_order == 'desc'
            if sort_by == 'description':
                qs = qs.order_by(('-name_es' if reverse_order else 'name_es'))
            elif sort_by == 'code':
                qs = qs.order_by(('-code' if reverse_order else 'code'))
            codes = [
                {'pk': obj.code, 'code': obj.code, 'description': obj.name_es or obj.code, 'is_active': obj.is_active}
                for obj in qs
            ]
        return {
            **{k: v for k, v in config.items() if k in ('title', 'icon', 'color', 'description')},
            'count': count,
            'filtered_count': len(codes),
            'codes': codes,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de búsqueda y filtros
        selected_category = self.request.GET.get('category', 'fuel')
        search_query = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '')  # all, active, inactive
        sort_by = self.request.GET.get('sort', 'code')  # code, description
        sort_order = self.request.GET.get('order', 'asc')  # asc, desc

        # Validar categoría seleccionada
        valid_api_categories = list(CATEGORY_ENDPOINT_MAP.keys())
        valid_product_catalog = list(PRODUCT_CATALOG_CONFIG.keys())
        if selected_category not in valid_api_categories and selected_category not in valid_product_catalog:
            selected_category = 'fuel'

        categories_data = {}
        is_product_catalog_category = selected_category in PRODUCT_CATALOG_CONFIG

        try:
            # Cargar categorías de API (códigos de referencia)
            if valid_api_categories:
                api_client = self.get_api_client()
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = {}
                    for category_key, endpoint in CATEGORY_ENDPOINT_MAP.items():
                        future = executor.submit(
                            self._load_single_category,
                            api_client, category_key, endpoint,
                            selected_category, search_query, status_filter, sort_by, sort_order
                        )
                        futures[future] = category_key
                    for future in as_completed(futures):
                        category_key = futures[future]
                        try:
                            result = future.result()
                            categories_data[result['category_key']] = result['data']
                        except Exception as e:
                            logger.error(f"Error loading category {category_key}: {e}")
                            categories_data[category_key] = {
                                **CATEGORY_CONFIG[category_key],
                                'count': 0,
                                'filtered_count': 0,
                                'codes': []
                            }

            # Agregar campos estandarizados a códigos de API
            for cat_key, cat_data in categories_data.items():
                field_mapping = CATEGORY_FIELD_MAP.get(cat_key)
                if field_mapping:
                    code_field = field_mapping['code_field']
                    name_field = field_mapping['name_field']
                    for code in cat_data.get('codes', []):
                        code['pk'] = code.get(code_field, '')
                        code['code'] = code.get(code_field, '')
                        code['description'] = code.get(name_field, '') or code.get('name_en', '')
                        code['is_active'] = True

            # Añadir categorías de catálogo interno (productos)
            for cat_key, config in PRODUCT_CATALOG_CONFIG.items():
                data = self._load_product_catalog_category(
                    cat_key, config, selected_category, search_query, status_filter, sort_by, sort_order
                )
                categories_data[cat_key] = data

            context['categories'] = categories_data
            context['selected_category'] = selected_category
            context['search_query'] = search_query
            context['status_filter'] = status_filter
            context['sort_by'] = sort_by
            context['sort_order'] = sort_order
            context['category_config'] = (
                PRODUCT_CATALOG_CONFIG.get(selected_category, {})
                if is_product_catalog_category
                else CATEGORY_CONFIG.get(selected_category, {})
            )
            context['is_product_catalog_category'] = is_product_catalog_category
            if is_product_catalog_category:
                cfg = PRODUCT_CATALOG_CONFIG[selected_category]
                context['product_catalog_create_url_name'] = cfg['create_url_name']
                context['product_catalog_edit_url_name'] = cfg['edit_url_name']
                context['product_catalog_delete_url_name'] = cfg['delete_url_name']

            # Información de filtros activos
            active_filters = []
            if search_query:
                active_filters.append(f'Búsqueda: "{search_query}"')
            if status_filter:
                status_labels = {'active': 'Activos', 'inactive': 'Inactivos'}
                active_filters.append(f'Estado: {status_labels.get(status_filter, status_filter)}')
            context['active_filters'] = active_filters
            context['has_filters'] = len(active_filters) > 0
            
            # Breadcrumbs
            context['breadcrumbs'] = [
                {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
                {'name': 'Códigos de Referencia', 'url': None}
            ]
            
        except Exception as e:
            if not is_product_catalog_category:
                logger.error(f"Error in ReferenceCodeListView: {e}")
                self.handle_api_error(e, "Error al cargar códigos de referencia")
            # Aun si la API falla, cargar categorías de producto para el sidebar y la lista
            for cat_key, config in PRODUCT_CATALOG_CONFIG.items():
                data = self._load_product_catalog_category(
                    cat_key, config, selected_category, search_query, status_filter, sort_by, sort_order
                )
                categories_data[cat_key] = data
            context['categories'] = categories_data
            context['selected_category'] = selected_category
            context['search_query'] = search_query
            context['status_filter'] = status_filter
            context['sort_by'] = sort_by
            context['sort_order'] = sort_order
            context['is_product_catalog_category'] = is_product_catalog_category
            context['category_config'] = (
                PRODUCT_CATALOG_CONFIG.get(selected_category, {})
                if is_product_catalog_category
                else CATEGORY_CONFIG.get(selected_category, {})
            )
            if is_product_catalog_category:
                cfg = PRODUCT_CATALOG_CONFIG.get(selected_category, {})
                context['product_catalog_create_url_name'] = cfg.get('create_url_name')
                context['product_catalog_edit_url_name'] = cfg.get('edit_url_name')
                context['product_catalog_delete_url_name'] = cfg.get('delete_url_name')
            context['active_filters'] = []
            context['has_filters'] = False
            context['breadcrumbs'] = [
                {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
                {'name': 'Códigos de Referencia', 'url': None}
            ]
        
        return context


class ReferenceCodeCreateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Crear nuevo código de referencia"""
    template_name = 'frontend/catalog/reference_code_form.html'
    form_class = ReferenceCodeForm
    login_url = 'frontend:login'
    
    def get_success_url(self):
        category = self.request.POST.get('category', 'fuel')
        return f"{reverse_lazy('frontend:reference_code_list')}?category={category}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.request.GET.get('category', 'fuel')
        
        context['category'] = category
        context['category_config'] = CATEGORY_CONFIG.get(category, {})
        context['is_edit'] = False
        
        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
            {'name': 'Códigos de Referencia', 'url': reverse_lazy('frontend:reference_code_list')},
            {'name': 'Crear', 'url': None}
        ]
        
        return context
    
    def form_valid(self, form):
        try:
            api_client = self.get_api_client()
            category = form.cleaned_data['category']
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)
            
            if not endpoint or not field_mapping:
                messages.error(self.request, "Categoría inválida")
                return self.form_invalid(form)
            
            code_field = field_mapping['code_field']
            name_field = field_mapping['name_field']
            extra_fields = field_mapping['extra_fields']
            
            # Preparar datos usando campos correctos de la API
            data = {
                code_field: form.cleaned_data['code'].upper(),
                name_field: form.cleaned_data['description'],
            }
            # Agregar campos extra
            data.update(extra_fields)
            
            # Crear código
            api_client.post(f'{endpoint}/', data=data)
            
            # Invalidar caché de la categoría
            self._invalidate_category_cache(category)
            
            messages.success(
                self.request,
                f"Código '{data[code_field]}' creado exitosamente"
            )
            return super().form_valid(form)
            
        except APIException as e:
            logger.error(f"Error creating reference code: {e}")
            self.handle_api_error(e, "Error al crear código de referencia")
            return self.form_invalid(form)
    
    def _invalidate_category_cache(self, category_key):
        """Invalida el caché de una categoría"""
        cache.delete(f'ref_code_{category_key}')


class ReferenceCodeUpdateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Editar código de referencia existente"""
    template_name = 'frontend/catalog/reference_code_form.html'
    form_class = ReferenceCodeForm
    login_url = 'frontend:login'
    
    def get_success_url(self):
        category = self.kwargs.get('category', 'fuel')
        return f"{reverse_lazy('frontend:reference_code_list')}?category={category}"
    
    def get_initial(self):
        initial = super().get_initial()

        try:
            api_client = self.get_api_client()
            category = self.kwargs.get('category')
            code_id = self.kwargs.get('pk')
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)

            if endpoint and field_mapping:
                code_data = api_client.get(f'{endpoint}/{code_id}/')
                code_field = field_mapping['code_field']
                name_field = field_mapping['name_field']

                # Obtener valores usando los campos correctos
                code_value = code_data.get(code_field, '')
                description = code_data.get(name_field, '') or code_data.get('name_en', '')

                initial.update({
                    'category': category,
                    'code': code_value,
                    'description': description,
                    # Nota: is_active no se incluye porque no existe en los modelos de códigos de referencia
                })
        except APIException as e:
            logger.error(f"Error loading reference code: {e}")

        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.kwargs.get('category', 'fuel')
        code_id = self.kwargs.get('pk')
        
        context['category'] = category
        context['category_config'] = CATEGORY_CONFIG.get(category, {})
        context['is_edit'] = True
        context['code_id'] = code_id
        
        # Cargar datos del código
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)
            if endpoint and field_mapping:
                code_data = api_client.get(f'{endpoint}/{code_id}/')
                
                # Agregar campos estandarizados
                code_field = field_mapping['code_field']
                name_field = field_mapping['name_field']
                code_data['pk'] = code_data.get(code_field, '')
                code_data['code'] = code_data.get(code_field, '')
                code_data['description'] = code_data.get(name_field, '') or code_data.get('name_en', '')
                code_data['is_active'] = True
                
                context['code_data'] = code_data
        except APIException as e:
            logger.error(f"Error loading code data: {e}")
        
        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
            {'name': 'Códigos de Referencia', 'url': reverse_lazy('frontend:reference_code_list')},
            {'name': 'Editar', 'url': None}
        ]
        
        return context
    
    def form_valid(self, form):
        try:
            api_client = self.get_api_client()
            category = self.kwargs.get('category')
            code_id = self.kwargs.get('pk')
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)

            if not endpoint or not field_mapping:
                messages.error(self.request, "Categoría inválida")
                return self.form_invalid(form)

            code_field = field_mapping['code_field']
            name_field = field_mapping['name_field']
            extra_fields = field_mapping['extra_fields']

            new_code = form.cleaned_data['code'].upper()
            original_code = self.request.POST.get('original_code', code_id).upper()
            description = form.cleaned_data['description']

            # Verificar si el código ha cambiado
            if new_code != original_code:
                # El código cambió - necesitamos crear uno nuevo y migrar referencias
                # 1. Verificar que el nuevo código no exista
                existing_response = api_client.get(f'{endpoint}/')
                existing_codes = {code[code_field]: code for code in existing_response.get('results', [])}

                if new_code in existing_codes:
                    # El nuevo código ya existe - error
                    messages.error(
                        self.request,
                        f"Error: El código '{new_code}' ya existe en esta categoría. "
                        f"No se puede cambiar '{original_code}' a '{new_code}' porque el código destino ya está en uso."
                    )
                    return self.form_invalid(form)

                # 2. Crear el nuevo código
                new_data = {
                    code_field: new_code,
                    name_field: description,
                }
                new_data.update(extra_fields)

                try:
                    api_client.post(f'{endpoint}/', data=new_data)
                except APIException as e:
                    messages.error(self.request, f"Error al crear el nuevo código: {e.message}")
                    return self.form_invalid(form)

                # 3. Actualizar referencias en equipos
                updated_equipment_count = self._update_equipment_references(
                    api_client, category, original_code, new_code
                )

                # 4. Eliminar el código viejo
                try:
                    api_client.delete(f'{endpoint}/{original_code}/')
                except APIException as e:
                    # Si no se puede eliminar, al menos informar que se creó el nuevo
                    messages.warning(
                        self.request,
                        f"Código '{new_code}' creado exitosamente y {updated_equipment_count} equipos actualizados. "
                        f"No se pudo eliminar el código viejo '{original_code}': {e.message}"
                    )
                    return super().form_valid(form)

                messages.success(
                    self.request,
                    f"Código cambiado exitosamente de '{original_code}' a '{new_code}'. "
                    f"{updated_equipment_count} equipos actualizados."
                )
                
                # Invalidar caché de ambas categorías (origen y destino)
                self._invalidate_category_cache(category)
            else:
                # El código no cambió - solo actualizar descripción
                data = {
                    name_field: description,
                }
                data.update(extra_fields)

                api_client.put(f'{endpoint}/{code_id}/', data=data)

                # Invalidar caché de la categoría
                self._invalidate_category_cache(category)

                messages.success(
                    self.request,
                    f"Código '{code_id}' actualizado exitosamente"
                )

            return super().form_valid(form)

        except APIException as e:
            logger.error(f"Error updating reference code: {e}")
            self.handle_api_error(e, "Error al actualizar código de referencia")
            return self.form_invalid(form)
    
    def _invalidate_category_cache(self, category_key):
        """Invalida el caché de una categoría"""
        from django.core.cache import cache
        cache_key = f'ref_code_{category_key}'
        cache.delete(cache_key)
        logger.debug(f"Caché invalidado para categoría: {category_key}")

    def _update_equipment_references(self, api_client, category, old_code, new_code):
        """Actualiza las referencias de código en los equipos"""
        # Mapear categoría a campo de equipo
        field_map = {
            'fuel': 'fuel_type',
            'transmission': 'transmission_type',
            'color': 'color',
            'drivetrain': 'drivetrain',
            'condition': 'condition'
        }

        field_name = field_map.get(category)
        if not field_name:
            return 0

        updated_count = 0
        try:
            # Obtener equipos que usan el código viejo
            response = api_client.get('equipment/', params={field_name: old_code, 'page_size': 1000})
            equipment_list = response.get('results', [])

            for equipment in equipment_list:
                equipment_id = equipment.get('equipment_id')
                if equipment_id:
                    # Actualizar el campo correspondiente
                    update_data = {field_name: new_code}
                    try:
                        api_client.patch(f'equipment/{equipment_id}/', data=update_data)
                        updated_count += 1
                    except APIException as e:
                        logger.error(f"Error updating equipment {equipment_id}: {e}")

        except Exception as e:
            logger.error(f"Error updating equipment references: {e}")

        return updated_count


class ReferenceCodeDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista detallada de un código de referencia (API o catálogo producto)"""
    template_name = 'frontend/catalog/reference_code_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.kwargs.get('category')
        code_id = self.kwargs.get('pk')
        context['category'] = category

        # Catálogos de producto (ORM): tipos de marca, categorías de producto, tipos de producto
        if category in PRODUCT_CATALOG_CONFIG:
            config = PRODUCT_CATALOG_CONFIG[category]
            model = config['model']
            obj = get_object_or_404(model, code=code_id)
            context['code'] = {
                'pk': obj.code,
                'code': obj.code,
                'description': obj.name_es or obj.code,
                'name_en': obj.name_en or '',
                'display_order': obj.display_order,
                'is_active': obj.is_active,
            }
            context['category_config'] = {k: v for k, v in config.items() if k in ('title', 'icon', 'color', 'description')}
            context['is_product_catalog_category'] = True
            context['product_catalog_edit_url_name'] = config['edit_url_name']
            context['product_catalog_delete_url_name'] = config['delete_url_name']
            context['product_catalog_create_url_name'] = config['create_url_name']
            context['usage_count'] = 0
            context['can_delete'] = True
            context['breadcrumbs'] = [
                {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
                {'name': 'Códigos de Referencia', 'url': reverse_lazy('frontend:reference_code_list')},
                {'name': 'Detalle', 'url': None}
            ]
            return context

        # Códigos de referencia vía API
        context['is_product_catalog_category'] = False
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)
            
            if endpoint and field_mapping:
                code_data = api_client.get(f'{endpoint}/{code_id}/')
                
                code_field = field_mapping['code_field']
                name_field = field_mapping['name_field']
                code_data['pk'] = code_data.get(code_field, '')
                code_data['code'] = code_data.get(code_field, '')
                code_data['description'] = code_data.get(name_field, '') or code_data.get('name_en', '')
                code_data['is_active'] = True
                
                context['code'] = code_data
                context['category_config'] = CATEGORY_CONFIG.get(category, {})
                usage_count = self._check_code_usage(api_client, category, code_data['code'])
                context['usage_count'] = usage_count
                context['can_delete'] = usage_count == 0
            else:
                context['code'] = None
        
        except APIException as e:
            logger.error(f"Error loading reference code detail: {e}")
            self.handle_api_error(e, "Error al cargar detalles del código")
            context['code'] = None
        
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
            {'name': 'Códigos de Referencia', 'url': reverse_lazy('frontend:reference_code_list')},
            {'name': 'Detalle', 'url': None}
        ]
        return context
    
    def _check_code_usage(self, api_client, category, code):
        """Verifica cuántos equipos usan este código"""
        try:
            # Mapear categoría a campo de equipo
            field_map = {
                'fuel': 'fuel_type',
                'transmission': 'transmission_type',
                'color': 'color',
                'drivetrain': 'drivetrain',
                'condition': 'condition'
            }
            
            field_name = field_map.get(category)
            if field_name:
                response = api_client.get('equipment/', params={field_name: code})
                return response.get('count', 0)
        except Exception as e:
            logger.error(f"Error checking code usage: {e}")
        
        return 0


class ReferenceCodeDeleteView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Eliminar código de referencia"""
    template_name = 'frontend/catalog/reference_code_confirm_delete.html'
    login_url = 'frontend:login'
    
    def _invalidate_category_cache(self, category_key):
        """Invalida el caché de una categoría"""
        from django.core.cache import cache
        cache_key = f'ref_code_{category_key}'
        cache.delete(cache_key)
        logger.debug(f"Caché invalidado para categoría: {category_key}")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.kwargs.get('category')
        code_id = self.kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)
            
            if endpoint and field_mapping:
                code_data = api_client.get(f'{endpoint}/{code_id}/')
                
                # Agregar campos estandarizados
                code_field = field_mapping['code_field']
                name_field = field_mapping['name_field']
                code_data['pk'] = code_data.get(code_field, '')
                code_data['code'] = code_data.get(code_field, '')
                code_data['description'] = code_data.get(name_field, '') or code_data.get('name_en', '')
                code_data['is_active'] = True
                
                context['code'] = code_data
                context['category'] = category
                context['category_config'] = CATEGORY_CONFIG.get(category, {})
                
                # Verificar dependencias
                usage_count = self._check_code_usage(api_client, category, code_data['code'])
                context['usage_count'] = usage_count
                context['can_delete'] = usage_count == 0
                
                if usage_count > 0:
                    context['warning_message'] = (
                        f"Este código está siendo usado por {usage_count} equipo(s). "
                        "No se puede eliminar hasta que se actualicen las referencias."
                    )
        
        except APIException as e:
            logger.error(f"Error loading reference code for deletion: {e}")
            self.handle_api_error(e, "Error al cargar código")
            context['code'] = None
        
        # Breadcrumbs
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
            {'name': 'Códigos de Referencia', 'url': reverse_lazy('frontend:reference_code_list')},
            {'name': 'Eliminar', 'url': None}
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        category = self.kwargs.get('category')
        code_id = self.kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            
            if not endpoint:
                messages.error(request, "Categoría inválida")
                return redirect('frontend:reference_code_list')
            
            # Verificar dependencias antes de eliminar
            code_data = api_client.get(f'{endpoint}/{code_id}/')
            usage_count = self._check_code_usage(api_client, category, code_data.get('code'))
            
            if usage_count > 0:
                messages.error(
                    request,
                    f"No se puede eliminar: el código está siendo usado por {usage_count} equipo(s)"
                )
                return redirect('frontend:reference_code_list')
            
            # Eliminar código
            api_client.delete(f'{endpoint}/{code_id}/')
            
            # Invalidar caché de la categoría
            self._invalidate_category_cache(category)
            
            messages.success(
                request,
                f"Código '{code_data.get('code')}' eliminado exitosamente"
            )
            
        except APIException as e:
            logger.error(f"Error deleting reference code: {e}")
            self.handle_api_error(e, "Error al eliminar código")
        
        return redirect(f"{reverse_lazy('frontend:reference_code_list')}?category={category}")
    
    def _check_code_usage(self, api_client, category, code):
        """Verifica cuántos equipos usan este código"""
        try:
            field_map = {
                'fuel': 'fuel_type',
                'transmission': 'transmission_type',
                'color': 'color',
                'drivetrain': 'drivetrain',
                'condition': 'condition'
            }
            
            field_name = field_map.get(category)
            if field_name:
                response = api_client.get('equipment/', params={field_name: code})
                return response.get('count', 0)
        except Exception as e:
            logger.error(f"Error checking code usage: {e}")
        
        return 0


class ReferenceCodeAjaxSearchView(LoginRequiredMixin, APIClientMixin, View):
    """Búsqueda AJAX de códigos de referencia"""
    
    def get(self, request, *args, **kwargs):
        category = request.GET.get('category', 'fuel')
        query = request.GET.get('q', '').strip()
        
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            
            if not endpoint:
                return JsonResponse({'error': 'Categoría inválida'}, status=400)
            
            # Obtener todos los códigos
            response = api_client.get(f'{endpoint}/')
            codes = response.get('results', [])
            
            # Filtrar por búsqueda
            if query:
                codes = [
                    code for code in codes
                    if query.lower() in code.get('code', '').lower() or
                       query.lower() in code.get('description', '').lower()
                ]
            
            return JsonResponse({
                'success': True,
                'codes': codes,
                'count': len(codes)
            })
            
        except APIException as e:
            logger.error(f"Error in AJAX search: {e}")
            return JsonResponse({'error': str(e)}, status=500)



class ReferenceCodeExportView(LoginRequiredMixin, APIClientMixin, View):
    """Exportar códigos de referencia a CSV (API o catálogo producto)"""
    
    def get(self, request, *args, **kwargs):
        category = request.GET.get('category', 'fuel')
        format_type = request.GET.get('format', 'csv')
        
        # Catálogos de producto (ORM)
        if category in PRODUCT_CATALOG_CONFIG:
            try:
                config = PRODUCT_CATALOG_CONFIG[category]
                model = config['model']
                qs = model.objects.all().order_by('display_order', 'code')
                codes = [
                    {
                        'code': obj.code,
                        'name_es': obj.name_es or '',
                        'name_en': obj.name_en or '',
                        'display_order': obj.display_order,
                        'is_active': obj.is_active,
                    }
                    for obj in qs
                ]
                if format_type == 'csv':
                    return self._export_csv_product_catalog(codes, category)
                messages.error(request, "Formato no soportado")
                return redirect('frontend:reference_code_list')
            except Exception as e:
                logger.error(f"Error exporting product catalog {category}: {e}")
                messages.error(request, "Error al exportar")
                return redirect('frontend:reference_code_list')
        
        # Códigos de referencia vía API
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            if not endpoint:
                messages.error(request, "Categoría inválida")
                return redirect('frontend:reference_code_list')
            response = api_client.get(f'{endpoint}/')
            codes = response.get('results', [])
            if format_type == 'csv':
                return self._export_csv(codes, category)
            messages.error(request, "Formato no soportado")
            return redirect('frontend:reference_code_list')
        except APIException as e:
            logger.error(f"Error exporting reference codes: {e}")
            messages.error(request, "Error al exportar códigos")
            return redirect('frontend:reference_code_list')
    
    def _export_csv_product_catalog(self, codes, category):
        """Exporta catálogo producto (ORM) a CSV con columnas completas."""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'reference_codes_{category}_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Código', 'Descripción', 'Nombre EN', 'Orden', 'Activo'])
        for code in codes:
            act = 'Sí' if code.get('is_active', True) else 'No'
            writer.writerow([
                code.get('code', ''),
                code.get('name_es', ''),
                code.get('name_en', '') or '',
                code.get('display_order', 0),
                act,
            ])
        return response
    
    def _export_csv(self, codes, category):
        """Exporta códigos de API a formato CSV"""
        field_mapping = CATEGORY_FIELD_MAP.get(category, {})
        code_field = field_mapping.get('code_field', 'code')
        name_field = field_mapping.get('name_field', 'name')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'reference_codes_{category}_{timestamp}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Código', 'Descripción', 'Activo'])
        for code in codes:
            code_value = code.get(code_field, '')
            description = code.get(name_field, '') or code.get('name_es', '') or code.get('name_en', '') or code.get('description', '')
            writer.writerow([code_value, description, 'Sí'])
        return response


class ReferenceCodeImportView(LoginRequiredMixin, APIClientMixin, FormView):
    """Importar códigos de referencia desde CSV (API o catálogo producto)"""
    template_name = 'frontend/catalog/reference_code_import.html'
    form_class = ReferenceCodeImportForm
    login_url = 'frontend:login'
    
    def get_success_url(self):
        category = self.request.GET.get('category', 'fuel')
        return f"{reverse_lazy('frontend:reference_code_list')}?category={category}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.request.GET.get('category', 'fuel')
        context['category'] = category
        if category in PRODUCT_CATALOG_CONFIG:
            context['category_config'] = {k: v for k, v in PRODUCT_CATALOG_CONFIG[category].items()
                                          if k in ('title', 'icon', 'color', 'description')}
        else:
            context['category_config'] = CATEGORY_CONFIG.get(category, {})
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse_lazy('frontend:catalog_index')},
            {'name': 'Códigos de Referencia', 'url': reverse_lazy('frontend:reference_code_list')},
            {'name': 'Importar', 'url': None}
        ]
        return context
    
    def form_valid(self, form):
        category = self.request.GET.get('category', 'fuel')
        csv_file = form.cleaned_data['csv_file']
        skip_duplicates = form.cleaned_data.get('skip_duplicates', True)
        csv_file.seek(0)
        try:
            rows = read_import_file(csv_file)
        except Exception as e:
            messages.error(self.request, f"Error al leer el archivo: {str(e)}")
            return self.form_invalid(form)
        if not rows:
            messages.error(self.request, "El archivo está vacío o no tiene datos válidos")
            return self.form_invalid(form)

        # Catálogos de producto (ORM)
        if category in PRODUCT_CATALOG_CONFIG:
            return self._import_product_catalog(category, rows, skip_duplicates, form)
        
        # Códigos de referencia vía API
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)
            if not endpoint or not field_mapping:
                messages.error(self.request, "Categoría inválida")
                return self.form_invalid(form)
            code_field = field_mapping['code_field']
            name_field = field_mapping['name_field']
            extra_fields = field_mapping['extra_fields']
            try:
                existing_response = api_client.get(f'{endpoint}/')
                existing_codes = {c[code_field]: c for c in existing_response.get('results', [])}
            except APIException as e:
                logger.error(f"Error obteniendo códigos existentes: {e}")
                messages.error(self.request, f"Error al obtener códigos existentes: {getattr(e, 'message', str(e))}")
                return self.form_invalid(form)
            created_count = 0
            updated_count = 0
            skipped_count = 0
            errors = []
            for row_num, row in enumerate(rows, start=2):
                try:
                    code = row.get('Código', '').strip().upper()
                    description = row.get('Descripción', '').strip()
                    if not code or not description:
                        errors.append(f"Fila {row_num}: Código o descripción vacíos")
                        continue
                    data = {code_field: code, name_field: description}
                    data.update(extra_fields)
                    if code in existing_codes:
                        if skip_duplicates:
                            skipped_count += 1
                            continue
                        code_id = existing_codes[code].get(code_field) or existing_codes[code].get('id')
                        api_client.put(f'{endpoint}/{code_id}/', data=data)
                        updated_count += 1
                    else:
                        api_client.post(f'{endpoint}/', data=data)
                        created_count += 1
                except APIException as e:
                    errors.append(f"Fila {row_num}: Error de API - {getattr(e, 'message', str(e))}")
                except Exception as e:
                    errors.append(f"Fila {row_num}: {str(e)}")
            if created_count > 0:
                messages.success(self.request, f"Se crearon {created_count} código(s) exitosamente")
            if updated_count > 0:
                messages.info(self.request, f"Se actualizaron {updated_count} código(s)")
            if skipped_count > 0:
                messages.warning(self.request, f"Se omitieron {skipped_count} código(s) duplicados")
            if errors:
                error_msg = "Errores encontrados:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    error_msg += f"\n... y {len(errors) - 5} errores más"
                messages.error(self.request, error_msg)
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error importing reference codes: {e}")
            messages.error(self.request, f"Error al importar códigos: {str(e)}")
            return self.form_invalid(form)
    
    def _import_product_catalog(self, category, rows, skip_duplicates, form):
        """Importa filas a un modelo de catálogo producto (BrandType, ProductCategory, ProductType)."""
        config = PRODUCT_CATALOG_CONFIG[category]
        model = config['model']
        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []
        for row_num, row in enumerate(rows, start=2):
            try:
                code = (row.get('Código', '') or row.get('codigo', '')).strip().upper()
                name_es = (row.get('Descripción', '') or row.get('descripción', '') or row.get('name_es', '')).strip()
                if not code or not name_es:
                    errors.append(f"Fila {row_num}: Código o Descripción vacíos")
                    continue
                name_en = (row.get('Nombre EN', '') or row.get('name_en', '') or '').strip() or None
                try:
                    display_order = int(row.get('Orden', 0) or row.get('display_order', 0) or 0)
                except (ValueError, TypeError):
                    display_order = 0
                act = row.get('Activo', '') or row.get('activo', '')
                is_active = str(act).strip().lower() in ('sí', 'si', 's', '1', 'true', 'yes', 'y')
                existing = model.objects.filter(code=code).first()
                if existing:
                    if skip_duplicates:
                        skipped_count += 1
                        continue
                    existing.name_es = name_es
                    existing.name_en = name_en or None
                    existing.display_order = display_order
                    existing.is_active = is_active
                    existing.save()
                    updated_count += 1
                else:
                    model.objects.create(
                        code=code,
                        name_es=name_es,
                        name_en=name_en or None,
                        display_order=display_order,
                        is_active=is_active,
                    )
                    created_count += 1
            except Exception as e:
                errors.append(f"Fila {row_num}: {str(e)}")
        if created_count > 0:
            messages.success(self.request, f"Se crearon {created_count} registro(s) exitosamente")
        if updated_count > 0:
            messages.info(self.request, f"Se actualizaron {updated_count} registro(s)")
        if skipped_count > 0:
            messages.warning(self.request, f"Se omitieron {skipped_count} duplicado(s)")
        if errors:
            error_msg = "Errores:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... y {len(errors) - 5} más"
            messages.error(self.request, error_msg)
        return super().form_valid(form)


class ReferenceCodeImportPreviewView(LoginRequiredMixin, APIClientMixin, View):
    """Vista previa de importación de códigos"""
    
    def post(self, request, *args, **kwargs):
        category = request.POST.get('category', 'fuel')
        
        try:
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                return JsonResponse({'error': 'No se proporcionó archivo'}, status=400)
            
            # Validar extensión
            file_name = csv_file.name
            ext = os.path.splitext(file_name)[1].lower()
            valid_extensions = ['.csv', '.xls', '.xlsx']
            
            if ext not in valid_extensions:
                return JsonResponse({
                    'error': f'Formato no válido: {ext}. Use CSV, XLS o XLSX.'
                }, status=400)
            
            # Leer archivo (CSV o Excel)
            try:
                rows = read_import_file(csv_file)
            except Exception as e:
                return JsonResponse({
                    'error': f'Error leyendo archivo: {str(e)}'
                }, status=400)
            
            if not rows:
                return JsonResponse({
                    'error': 'El archivo está vacío o no tiene datos válidos'
                }, status=400)
            
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            field_mapping = CATEGORY_FIELD_MAP.get(category)
            
            if not endpoint or not field_mapping:
                return JsonResponse({'error': 'Categoría inválida'}, status=400)
            
            code_field = field_mapping['code_field']
            
            # Obtener códigos existentes
            try:
                existing_response = api_client.get(f'{endpoint}/')
                existing_codes = {code[code_field]: code for code in existing_response.get('results', [])}
            except APIException as e:
                logger.error(f"Error obteniendo códigos existentes: {e}")
                return JsonResponse({
                    'error': f'Error al obtener códigos existentes: {e.message}'
                }, status=500)
            
            # Analizar archivo
            preview_data = []
            total_rows = 0
            new_count = 0
            duplicate_count = 0
            error_count = 0
            
            for row_num, row in enumerate(rows, start=2):
                total_rows += 1
                code = row.get('Código', '').strip().upper()
                description = row.get('Descripción', '').strip()
                is_active_str = row.get('Activo', 'Sí').strip().lower()
                
                status = 'new'
                message = 'Nuevo código'
                
                if not code or not description:
                    status = 'error'
                    message = 'Código o descripción vacíos'
                    error_count += 1
                elif code in existing_codes:
                    status = 'duplicate'
                    message = 'Código ya existe'
                    duplicate_count += 1
                else:
                    new_count += 1
                
                preview_data.append({
                    'row': row_num,
                    'code': code,
                    'description': description,
                    'is_active': is_active_str,
                    'status': status,
                    'message': message
                })
                
                # Limitar preview a 50 filas
                if len(preview_data) >= 50:
                    break
            
            return JsonResponse({
                'success': True,
                'preview': preview_data,
                'summary': {
                    'total': total_rows,
                    'new': new_count,
                    'duplicates': duplicate_count,
                    'errors': error_count
                }
            })
            
        except Exception as e:
            logger.error(f"Error in import preview: {e}")
            return JsonResponse({'error': str(e)}, status=500)


class ReferenceCodeBulkDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Eliminación masiva de códigos de referencia"""
    
    def _invalidate_category_cache(self, category_key):
        """Invalida el caché de una categoría"""
        from django.core.cache import cache
        cache_key = f'ref_code_{category_key}'
        cache.delete(cache_key)
        logger.debug(f"Caché invalidado para categoría: {category_key}")
    
    def post(self, request, *args, **kwargs):
        category = request.POST.get('category', 'fuel')
        code_ids = request.POST.getlist('code_ids[]')
        
        try:
            api_client = self.get_api_client()
            endpoint = CATEGORY_ENDPOINT_MAP.get(category)
            
            if not endpoint:
                return JsonResponse({'error': 'Categoría inválida'}, status=400)
            
            deleted_count = 0
            failed_count = 0
            errors = []
            
            for code_id in code_ids:
                try:
                    # Verificar dependencias
                    code_data = api_client.get(f'{endpoint}/{code_id}/')
                    usage_count = self._check_code_usage(api_client, category, code_data.get('code'))
                    
                    if usage_count > 0:
                        failed_count += 1
                        errors.append(f"Código {code_data.get('code')}: en uso por {usage_count} equipo(s)")
                        continue
                    
                    # Eliminar
                    api_client.delete(f'{endpoint}/{code_id}/')
                    deleted_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Código ID {code_id}: {str(e)}")
            
            return JsonResponse({
                'success': True,
                'deleted': deleted_count,
                'failed': failed_count,
                'errors': errors
            })
            
        except Exception as e:
            logger.error(f"Error in bulk delete: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            # Invalidar caché de la categoría
            if category:
                self._invalidate_category_cache(category)
    
    def _check_code_usage(self, api_client, category, code):
        """Verifica cuántos equipos usan este código"""
        try:
            field_map = {
                'fuel': 'fuel_type',
                'transmission': 'transmission_type',
                'color': 'color',
                'drivetrain': 'drivetrain',
                'condition': 'condition'
            }
            
            field_name = field_map.get(category)
            if field_name:
                response = api_client.get('equipment/', params={field_name: code})
                return response.get('count', 0)
        except Exception as e:
            logger.error(f"Error checking code usage: {e}")
        
        return 0
