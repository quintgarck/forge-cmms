"""
Vistas CRUD para el módulo OEM (Marcas y Catálogo)
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django import forms

from ..services.api_client import ForgeAPIClient, APIException
from ..mixins import APIClientMixin
from ..forms.oem_forms import (
    OEMBrandForm,
    OEMCatalogItemForm,
    OEMBrandSearchForm,
    OEMCatalogItemSearchForm,
    get_brand_type_choices,
    BRAND_TYPE_FALLBACK_CHOICES,
)

logger = logging.getLogger(__name__)


# ========================================
# CRUD para Marcas OEM (OEMBrand)
# ========================================

class OEMBrandListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Lista de marcas OEM con búsqueda y filtros"""
    template_name = 'frontend/oem/brand_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de búsqueda
        search = self.request.GET.get('search', '').strip()
        brand_type = self.request.GET.get('brand_type', '')
        is_active = self.request.GET.get('is_active', '')
        page = self._get_page_number()
        
        try:
            api_client = self.get_api_client()
            
            # Construir filtros
            filters = {}
            if search:
                filters['search'] = search
            if brand_type:
                filters['brand_type'] = brand_type
            if is_active:
                filters['is_active'] = is_active == 'true'
            
            # Obtener marcas desde la API
            brands_data = api_client.get_oem_brands(
                page=page,
                page_size=self.paginate_by,
                **filters
            )
            
            brands = brands_data.get('results', brands_data)
            context['brands'] = brands if isinstance(brands, list) else []
            
            # Paginación
            total_count = brands_data.get('count', len(context['brands']))
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Formulario de búsqueda
            context['search_form'] = OEMBrandSearchForm(initial={
                'search': search,
                'brand_type': brand_type,
                'is_active': is_active,
            })
            
        except APIException as e:
            logger.error(f"Error loading OEM brands: {e}")
            messages.error(self.request, f"Error al cargar las marcas: {e.message}")
            context['brands'] = []
            context['pagination'] = self._get_empty_pagination()
            context['search_form'] = OEMBrandSearchForm()
        
        return context
    
    def _get_page_number(self):
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        if total_pages <= window:
            return list(range(1, total_pages + 1))
        
        half_window = window // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        if end - start < window - 1:
            if start == 1:
                end = min(total_pages, start + window - 1)
            else:
                start = max(1, end - window + 1)
        
        return list(range(start, end + 1))
    
    def _get_empty_pagination(self):
        return {
            'count': 0,
            'current_page': 1,
            'total_pages': 0,
            'page_range': [],
            'has_previous': False,
            'has_next': False,
            'start_index': 0,
            'end_index': 0,
        }


class OEMBrandCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Crear nueva marca OEM"""
    template_name = 'frontend/oem/brand_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Marca OEM'
        context['form_action'] = 'create'
        
        form_data = self.request.POST if self.request.method == 'POST' else None
        brand_type_choices = get_brand_type_choices()
        if brand_type_choices == BRAND_TYPE_FALLBACK_CHOICES:
            logger.warning("Tipo de marca: usando lista fija (oem.brand_type no cargada)")
        context['form'] = OEMBrandForm(form_data, brand_type_choices=brand_type_choices)
        
        return context
    
    def post(self, request, *args, **kwargs):
        form = OEMBrandForm(request.POST, brand_type_choices=get_brand_type_choices())
        
        if form.is_valid():
            brand_data = {
                'oem_code': form.cleaned_data['oem_code'],
                'name': form.cleaned_data['name'],
                'brand_type': form.cleaned_data['brand_type'],
                'country': form.cleaned_data.get('country', ''),
                'website': form.cleaned_data.get('website', ''),
                'logo_url': form.cleaned_data.get('logo_url', ''),
                'support_email': form.cleaned_data.get('support_email', ''),
                'is_active': form.cleaned_data.get('is_active', True),
                'display_order': form.cleaned_data.get('display_order', 0),
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.post('oem-brands/', brand_data)
                
                messages.success(
                    request,
                    f'Marca "{brand_data["name"]}" creada exitosamente.'
                )
                return redirect('frontend:oem_brand_list')
                
            except APIException as e:
                logger.error(f"Brand creation API error: {e}")
                
                if e.status_code == 400 and e.response_data:
                    for field, errors in e.response_data.items():
                        if field in form.fields:
                            if isinstance(errors, list):
                                for error in errors:
                                    form.add_error(field, error)
                            else:
                                form.add_error(field, str(errors))
                        else:
                            form.add_error(None, f"{field}: {errors}")
                else:
                    form.add_error(None, e.message or "Error al crear la marca")
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class OEMBrandDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Detalle de marca OEM"""
    template_name = 'frontend/oem/brand_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            brand_data = api_client.get(f'oem-brands/{brand_id}/')
            context['brand'] = brand_data
            
            # Obtener modelos de esta marca
            catalog_items = api_client.get_oem_catalog_items(
                oem_code=brand_data.get('oem_code'),
                page_size=100
            )
            context['catalog_items'] = catalog_items.get('results', [])
            
        except APIException as e:
            logger.error(f"Error loading brand {brand_id}: {e}")
            messages.error(self.request, f"Error al cargar la marca: {e.message}")
            context['brand'] = None
            context['catalog_items'] = []
        
        return context


class OEMBrandUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Actualizar marca OEM"""
    template_name = 'frontend/oem/brand_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand_id = kwargs.get('pk')
        
        context['form_title'] = 'Editar Marca OEM'
        context['form_action'] = 'update'
        
        try:
            api_client = self.get_api_client()
            brand_data = api_client.get(f'oem-brands/{brand_id}/')
            context['brand'] = brand_data
            
            brand_type_choices = get_brand_type_choices()
            if self.request.method == 'POST':
                form = OEMBrandForm(self.request.POST, brand_type_choices=brand_type_choices)
            else:
                initial_data = {
                    'oem_code': brand_data.get('oem_code', ''),
                    'name': brand_data.get('name', ''),
                    'brand_type': brand_data.get('brand_type', ''),
                    'country': brand_data.get('country', ''),
                    'website': brand_data.get('website', ''),
                    'logo_url': brand_data.get('logo_url', ''),
                    'support_email': brand_data.get('support_email', ''),
                    'is_active': brand_data.get('is_active', True),
                    'display_order': brand_data.get('display_order', 0),
                }
                form = OEMBrandForm(initial=initial_data, brand_type_choices=brand_type_choices)
            
            context['form'] = form
            
        except APIException as e:
            logger.error(f"Error loading brand {brand_id}: {e}")
            messages.error(self.request, f"Error al cargar la marca: {e.message}")
            context['brand'] = None
            context['form'] = OEMBrandForm(brand_type_choices=get_brand_type_choices())
        
        return context
    
    def post(self, request, *args, **kwargs):
        brand_id = kwargs.get('pk')
        form = OEMBrandForm(request.POST, brand_type_choices=get_brand_type_choices())
        
        if form.is_valid():
            brand_data = {
                'oem_code': form.cleaned_data['oem_code'],
                'name': form.cleaned_data['name'],
                'brand_type': form.cleaned_data['brand_type'],
                'country': form.cleaned_data.get('country', ''),
                'website': form.cleaned_data.get('website', ''),
                'logo_url': form.cleaned_data.get('logo_url', ''),
                'support_email': form.cleaned_data.get('support_email', ''),
                'is_active': form.cleaned_data.get('is_active', True),
                'display_order': form.cleaned_data.get('display_order', 0),
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.put(f'oem-brands/{brand_id}/', brand_data)
                
                messages.success(
                    request,
                    f'Marca "{brand_data["name"]}" actualizada exitosamente.'
                )
                return redirect('frontend:oem_brand_detail', pk=brand_id)
                
            except APIException as e:
                logger.error(f"Brand update API error: {e}")
                
                if e.status_code == 400 and e.response_data:
                    for field, errors in e.response_data.items():
                        if field in form.fields:
                            if isinstance(errors, list):
                                for error in errors:
                                    form.add_error(field, error)
                            else:
                                form.add_error(field, str(errors))
                        else:
                            form.add_error(None, f"{field}: {errors}")
                else:
                    form.add_error(None, e.message or "Error al actualizar la marca")
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class OEMBrandDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Eliminar marca OEM"""
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        brand_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            api_client.delete(f'oem-brands/{brand_id}/')
            
            messages.success(request, 'Marca eliminada exitosamente.')
            return redirect('frontend:oem_brand_list')
            
        except APIException as e:
            logger.error(f"Brand deletion API error: {e}")
            messages.error(request, f"Error al eliminar la marca: {e.message}")
            return redirect('frontend:oem_brand_detail', pk=brand_id)


# ========================================
# CRUD para Catálogo OEM (OEMCatalogItem)
# ========================================

class OEMCatalogItemListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Lista de items del catálogo OEM con búsqueda y filtros"""
    template_name = 'frontend/oem/catalog_item_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de búsqueda
        search = self.request.GET.get('search', '').strip()
        oem_code = self.request.GET.get('oem_code', '')
        item_type = self.request.GET.get('item_type', '')
        is_active = self.request.GET.get('is_active', '')
        is_discontinued = self.request.GET.get('is_discontinued', '')
        page = self._get_page_number()
        
        try:
            api_client = self.get_api_client()
            
            # Construir filtros
            filters = {}
            if search:
                filters['search'] = search
            if oem_code:
                filters['oem_code'] = oem_code
            if item_type:
                filters['item_type'] = item_type
            if is_active:
                filters['is_active'] = is_active == 'true'
            if is_discontinued:
                filters['is_discontinued'] = is_discontinued == 'true'
            
            # Obtener items del catálogo
            items_data = api_client.get_oem_catalog_items(
                page=page,
                page_size=self.paginate_by,
                **filters
            )
            
            items = items_data.get('results', items_data)
            context['catalog_items'] = items if isinstance(items, list) else []
            
            # Paginación
            total_count = items_data.get('count', len(context['catalog_items']))
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Formulario de búsqueda con marcas
            search_form = OEMCatalogItemSearchForm(initial={
                'search': search,
                'oem_code': oem_code,
                'item_type': item_type,
                'is_active': is_active,
                'is_discontinued': is_discontinued,
            })
            
            # Cargar marcas para el filtro
            brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
            brand_choices = [('', 'Todas las marcas')]
            for brand in brands_data.get('results', []):
                brand_choices.append((
                    brand.get('oem_code'),
                    f"{brand.get('name')} ({brand.get('oem_code')})"
                ))
            search_form.fields['oem_code'].widget = forms.Select(
                choices=brand_choices,
                attrs={'class': 'form-select'}
            )
            
            context['search_form'] = search_form
            
        except APIException as e:
            logger.error(f"Error loading catalog items: {e}")
            messages.error(self.request, f"Error al cargar el catálogo: {e.message}")
            context['catalog_items'] = []
            context['pagination'] = self._get_empty_pagination()
            context['search_form'] = OEMCatalogItemSearchForm()
        
        return context
    
    def _get_page_number(self):
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        if total_pages <= window:
            return list(range(1, total_pages + 1))
        
        half_window = window // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        if end - start < window - 1:
            if start == 1:
                end = min(total_pages, start + window - 1)
            else:
                start = max(1, end - window + 1)
        
        return list(range(start, end + 1))
    
    def _get_empty_pagination(self):
        return {
            'count': 0,
            'current_page': 1,
            'total_pages': 0,
            'page_range': [],
            'has_previous': False,
            'has_next': False,
            'start_index': 0,
            'end_index': 0,
        }


class OEMCatalogItemCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Crear nuevo item del catálogo OEM"""
    template_name = 'frontend/oem/catalog_item_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Item del Catálogo OEM'
        context['form_action'] = 'create'
        
        form_data = self.request.POST if self.request.method == 'POST' else None
        form = OEMCatalogItemForm(form_data)
        
        # Cargar marcas OEM para el select
        try:
            api_client = self.get_api_client()
            brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
            brand_choices = [('', 'Seleccione una marca')]
            for brand in brands_data.get('results', []):
                brand_choices.append((
                    brand.get('oem_code'),
                    f"{brand.get('name')} ({brand.get('oem_code')})"
                ))
            form.fields['oem_code'].widget = forms.Select(
                choices=brand_choices,
                attrs={'class': 'form-select', 'required': True, 'id': 'id_oem_code'}
            )
        except APIException as e:
            logger.error(f"Error loading brands: {e}")
            form.fields['oem_code'].widget = forms.Select(
                choices=[('', 'Error al cargar marcas')],
                attrs={'class': 'form-select', 'id': 'id_oem_code'}
            )
        
        context['form'] = form
        return context
    
    def post(self, request, *args, **kwargs):
        form = OEMCatalogItemForm(request.POST)
        
        # Recargar marcas en el formulario
        try:
            api_client = self.get_api_client()
            brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
            brand_choices = [('', 'Seleccione una marca')]
            for brand in brands_data.get('results', []):
                brand_choices.append((
                    brand.get('oem_code'),
                    f"{brand.get('name')} ({brand.get('oem_code')})"
                ))
            form.fields['oem_code'].widget = forms.Select(
                choices=brand_choices,
                attrs={'class': 'form-select', 'required': True, 'id': 'id_oem_code'}
            )
        except APIException:
            pass
        
        if form.is_valid():
            item_data = {
                'oem_code': form.cleaned_data['oem_code'],
                'part_number': form.cleaned_data['part_number'],
                'part_number_type': form.cleaned_data.get('part_number_type') or None,
                'item_type': form.cleaned_data['item_type'],
                'description_es': form.cleaned_data.get('description_es', '') or None,
                'description_en': form.cleaned_data.get('description_en', '') or None,
                'group_code': form.cleaned_data.get('group_code') or None,
                'body_style': form.cleaned_data.get('body_style', '') or None,
                'year_start': form.cleaned_data.get('year_start'),
                'year_end': form.cleaned_data.get('year_end'),
                'weight_kg': str(form.cleaned_data.get('weight_kg', 0)) if form.cleaned_data.get('weight_kg') else None,
                'dimensions': form.cleaned_data.get('dimensions', '') or None,
                'material': form.cleaned_data.get('material', '') or None,
                'primary_image_url': form.cleaned_data.get('primary_image_url', '') or None,
                'list_price': str(form.cleaned_data.get('list_price', 0)) if form.cleaned_data.get('list_price') else None,
                'net_price': str(form.cleaned_data.get('net_price', 0)) if form.cleaned_data.get('net_price') else None,
                'currency_code': form.cleaned_data.get('currency_code') or 'USD',
                'oem_lead_time_days': form.cleaned_data.get('oem_lead_time_days'),
                'is_discontinued': form.cleaned_data.get('is_discontinued', False),
                'is_active': form.cleaned_data.get('is_active', True),
                'display_order': form.cleaned_data.get('display_order', 0),
            }
            
            try:
                result = api_client.post('oem-catalog-items/', item_data)
                
                messages.success(
                    request,
                    f'Item "{item_data["part_number"]}" creado exitosamente.'
                )
                return redirect('frontend:oem_catalog_item_list')
                
            except APIException as e:
                logger.error(f"Catalog item creation API error: {e}")
                
                if e.status_code == 400 and e.response_data:
                    for field, errors in e.response_data.items():
                        if field in form.fields:
                            if isinstance(errors, list):
                                for error in errors:
                                    form.add_error(field, error)
                            else:
                                form.add_error(field, str(errors))
                        else:
                            form.add_error(None, f"{field}: {errors}")
                else:
                    form.add_error(None, e.message or "Error al crear el item")
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class OEMCatalogItemDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Detalle de item del catálogo OEM"""
    template_name = 'frontend/oem/catalog_item_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            item_data = api_client.get(f'oem-catalog-items/{item_id}/')
            context['catalog_item'] = item_data
            
            # Obtener información de la marca
            if item_data.get('oem_code'):
                brands_data = api_client.get_oem_brands(
                    oem_code=item_data['oem_code'],
                    page_size=1
                )
                brands = brands_data.get('results', [])
                context['brand'] = brands[0] if brands else None
            
        except APIException as e:
            logger.error(f"Error loading catalog item {item_id}: {e}")
            messages.error(self.request, f"Error al cargar el item: {e.message}")
            context['catalog_item'] = None
            context['brand'] = None
        
        return context


class OEMCatalogItemUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Actualizar item del catálogo OEM"""
    template_name = 'frontend/oem/catalog_item_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item_id = kwargs.get('pk')
        
        context['form_title'] = 'Editar Item del Catálogo OEM'
        context['form_action'] = 'update'
        
        try:
            api_client = self.get_api_client()
            item_data = api_client.get(f'oem-catalog-items/{item_id}/')
            context['catalog_item'] = item_data
            
            if self.request.method == 'POST':
                form = OEMCatalogItemForm(self.request.POST)
            else:
                initial_data = {
                    'oem_code': item_data.get('oem_code', ''),
                    'part_number': item_data.get('part_number', ''),
                    'part_number_type': item_data.get('part_number_type', ''),
                    'item_type': item_data.get('item_type', ''),
                    'description_es': item_data.get('description_es', ''),
                    'description_en': item_data.get('description_en', ''),
                    'group_code': item_data.get('group_code', ''),
                    'body_style': item_data.get('body_style', ''),
                    'year_start': item_data.get('year_start'),
                    'year_end': item_data.get('year_end'),
                    'weight_kg': item_data.get('weight_kg'),
                    'dimensions': item_data.get('dimensions', ''),
                    'material': item_data.get('material', ''),
                    'primary_image_url': item_data.get('primary_image_url', ''),
                    'list_price': item_data.get('list_price'),
                    'net_price': item_data.get('net_price'),
                    'currency_code': item_data.get('currency_code', 'USD'),
                    'oem_lead_time_days': item_data.get('oem_lead_time_days'),
                    'is_discontinued': item_data.get('is_discontinued', False),
                    'is_active': item_data.get('is_active', True),
                    'display_order': item_data.get('display_order', 0),
                }
                form = OEMCatalogItemForm(initial=initial_data)
            
            # Cargar marcas
            brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
            brand_choices = [('', 'Seleccione una marca')]
            for brand in brands_data.get('results', []):
                brand_choices.append((
                    brand.get('oem_code'),
                    f"{brand.get('name')} ({brand.get('oem_code')})"
                ))
            form.fields['oem_code'].widget = forms.Select(
                choices=brand_choices,
                attrs={'class': 'form-select', 'required': True, 'id': 'id_oem_code'}
            )
            
            context['form'] = form
            
        except APIException as e:
            logger.error(f"Error loading catalog item {item_id}: {e}")
            messages.error(self.request, f"Error al cargar el item: {e.message}")
            context['catalog_item'] = None
            context['form'] = OEMCatalogItemForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        form = OEMCatalogItemForm(request.POST)
        
        # Recargar marcas
        try:
            api_client = self.get_api_client()
            brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
            brand_choices = [('', 'Seleccione una marca')]
            for brand in brands_data.get('results', []):
                brand_choices.append((
                    brand.get('oem_code'),
                    f"{brand.get('name')} ({brand.get('oem_code')})"
                ))
            form.fields['oem_code'].widget = forms.Select(
                choices=brand_choices,
                attrs={'class': 'form-select', 'required': True, 'id': 'id_oem_code'}
            )
        except APIException:
            pass
        
        if form.is_valid():
            item_data = {
                'oem_code': form.cleaned_data['oem_code'],
                'part_number': form.cleaned_data['part_number'],
                'part_number_type': form.cleaned_data.get('part_number_type') or None,
                'item_type': form.cleaned_data['item_type'],
                'description_es': form.cleaned_data.get('description_es', '') or None,
                'description_en': form.cleaned_data.get('description_en', '') or None,
                'group_code': form.cleaned_data.get('group_code') or None,
                'body_style': form.cleaned_data.get('body_style', '') or None,
                'year_start': form.cleaned_data.get('year_start'),
                'year_end': form.cleaned_data.get('year_end'),
                'weight_kg': str(form.cleaned_data.get('weight_kg', 0)) if form.cleaned_data.get('weight_kg') else None,
                'dimensions': form.cleaned_data.get('dimensions', '') or None,
                'material': form.cleaned_data.get('material', '') or None,
                'primary_image_url': form.cleaned_data.get('primary_image_url', '') or None,
                'list_price': str(form.cleaned_data.get('list_price', 0)) if form.cleaned_data.get('list_price') else None,
                'net_price': str(form.cleaned_data.get('net_price', 0)) if form.cleaned_data.get('net_price') else None,
                'currency_code': form.cleaned_data.get('currency_code') or 'USD',
                'oem_lead_time_days': form.cleaned_data.get('oem_lead_time_days'),
                'is_discontinued': form.cleaned_data.get('is_discontinued', False),
                'is_active': form.cleaned_data.get('is_active', True),
                'display_order': form.cleaned_data.get('display_order', 0),
            }
            
            try:
                result = api_client.put(f'oem-catalog-items/{item_id}/', item_data)
                
                messages.success(
                    request,
                    f'Item "{item_data["part_number"]}" actualizado exitosamente.'
                )
                return redirect('frontend:oem_catalog_item_detail', pk=item_id)
                
            except APIException as e:
                logger.error(f"Catalog item update API error: {e}")
                
                if e.status_code == 400 and e.response_data:
                    for field, errors in e.response_data.items():
                        if field in form.fields:
                            if isinstance(errors, list):
                                for error in errors:
                                    form.add_error(field, error)
                            else:
                                form.add_error(field, str(errors))
                        else:
                            form.add_error(None, f"{field}: {errors}")
                else:
                    form.add_error(None, e.message or "Error al actualizar el item")
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class OEMCatalogItemDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Eliminar item del catálogo OEM"""
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        item_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            api_client.delete(f'oem-catalog-items/{item_id}/')
            
            messages.success(request, 'Item del catálogo eliminado exitosamente.')
            return redirect('frontend:oem_catalog_item_list')
            
        except APIException as e:
            logger.error(f"Catalog item deletion API error: {e}")
            messages.error(request, f"Error al eliminar el item: {e.message}")
            return redirect('frontend:oem_catalog_item_detail', pk=item_id)
