"""
Views for the Inventory Management Module in ForgeDB

This module implements comprehensive inventory management functionality
including product management, stock tracking, and inventory transactions.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
import logging
from decimal import Decimal

from .services import ForgeAPIClient
from .services.api_client import APIException
from .forms import ProductForm, ProductSearchForm

logger = logging.getLogger(__name__)


class APIClientMixin:
    """Mixin to provide API client functionality to views."""
    
    def get_api_client(self):
        """Get an API client instance for this request."""
        return ForgeAPIClient(request=self.request)
    
    def handle_api_error(self, error: APIException, default_message: str = "Error en la operación"):
        """Handle API errors and display appropriate messages."""
        if error.status_code == 401:
            # Authentication errors - clear session and show message
            messages.error(self.request, "Sesión expirada. Por favor, inicie sesión nuevamente.")
            # Don't redirect here - let the view handle it after showing the message
        elif error.status_code == 400 and error.response_data:
            # Validation errors
            error_messages = []
            for field, errors in error.response_data.items():
                if isinstance(errors, list):
                    error_messages.extend(errors)
                else:
                    error_messages.append(str(errors))

            if error_messages:
                for msg in error_messages:
                    messages.error(self.request, msg)
            else:
                messages.error(self.request, error.message)
        else:
            messages.error(self.request, error.message or default_message)


class InventoryDashboardView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Dashboard for inventory management with KPIs and alerts."""
    template_name = 'frontend/inventory/dashboard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get inventory KPIs from API
            inventory_data = api_client.get('inventory/dashboard/')
            
            # Core KPIs
            context.update({
                'total_products': inventory_data.get('total_products', 0),
                'total_stock_value': inventory_data.get('total_stock_value', 0),
                'low_stock_items': inventory_data.get('low_stock_items', 0),
                'out_of_stock_items': inventory_data.get('out_of_stock_items', 0),
                'recent_transactions': inventory_data.get('recent_transactions', []),
                
                # Inventory trends
                'monthly_movements': inventory_data.get('monthly_movements', []),
                'stock_turnover_rate': inventory_data.get('stock_turnover_rate', 0),
                'abc_analysis': inventory_data.get('abc_analysis', {}),
                
                # Alerts and notifications
                'inventory_alerts': inventory_data.get('inventory_alerts', []),
                'critical_items': inventory_data.get('critical_items', []),
                
                # Categories and types breakdown
                'category_breakdown': inventory_data.get('category_breakdown', {}),
                'type_breakdown': inventory_data.get('type_breakdown', {}),
                
                # Charts and graphs data
                'charts': inventory_data.get('charts', {}),
            })
            
        except APIException as e:
            logger.error(f"Inventory dashboard API error: {e}")
            
            # Show user-friendly error message based on error type
            if e.status_code == 500:
                messages.warning(
                    self.request, 
                    "El backend API está experimentando problemas técnicos. Mostrando datos de demostración."
                )
            elif e.status_code == 401:
                messages.error(
                    self.request,
                    "Su sesión ha expirado. Por favor, inicie sesión nuevamente."
                )
            else:
                messages.info(
                    self.request,
                    "No se pudieron cargar los datos del inventario. Mostrando información de demostración."
                )
            
            # Fallback data if API is not available
            context.update({
                'total_products': 0,
                'total_stock_value': 0,
                'low_stock_items': 0,
                'out_of_stock_items': 0,
                'recent_transactions': [],
                'monthly_movements': [],
                'stock_turnover_rate': 0,
                'abc_analysis': {},
                'inventory_alerts': [],
                'critical_items': [],
                'category_breakdown': {},
                'type_breakdown': {},
                'charts': {},
            })
        
        return context


class ProductListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Product list view with enhanced pagination and search functionality."""
    template_name = 'frontend/inventory/product_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        category_filter = self.request.GET.get('category', '')
        type_filter = self.request.GET.get('type', '')
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'name')
        sort_order = self.request.GET.get('order', 'asc')
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        supplier_filter = self.request.GET.get('supplier', '')
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if category_filter:
                filters['category'] = category_filter
            if type_filter:
                filters['type'] = type_filter
            if status_filter:
                filters['status'] = status_filter
            if price_min:
                filters['price_min'] = price_min
            if price_max:
                filters['price_max'] = price_max
            if supplier_filter:
                filters['supplier'] = supplier_filter
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"
            
            # Get products data with pagination
            products_data = api_client.get_paginated(
                'products/', 
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            products = products_data.get('results', [])
            
            # Process products with additional information for display
            for product in products:
                # Add category styling
                category = product.get('category', '').lower()
                if category == 'service':
                    product['category_class'] = 'primary'
                    product['category_icon'] = 'bi-tools'
                elif category == 'part':
                    product['category_class'] = 'success'
                    product['category_icon'] = 'bi-gear'
                elif category == 'material':
                    product['category_class'] = 'info'
                    product['category_icon'] = 'bi-box'
                elif category == 'tool':
                    product['category_class'] = 'warning'
                    product['category_icon'] = 'bi-hammer'
                elif category == 'consumable':
                    product['category_class'] = 'secondary'
                    product['category_icon'] = 'bi-droplet'
                else:
                    product['category_class'] = 'light'
                    product['category_icon'] = 'bi-tag'
                
                # Add stock status
                current_stock = product.get('current_stock', 0)
                minimum_stock = product.get('minimum_stock', 0)
                
                if current_stock <= 0:
                    product['stock_status'] = 'out_of_stock'
                    product['stock_class'] = 'danger'
                    product['stock_label'] = 'Sin Stock'
                elif current_stock <= minimum_stock:
                    product['stock_status'] = 'low_stock'
                    product['stock_class'] = 'warning'
                    product['stock_label'] = 'Stock Bajo'
                else:
                    product['stock_status'] = 'in_stock'
                    product['stock_class'] = 'success'
                    product['stock_label'] = 'En Stock'
                
                # Calculate profit margin if cost is available
                price = float(product.get('price', 0))
                cost = float(product.get('cost', 0))
                if price > 0 and cost > 0:
                    margin = ((price - cost) / price) * 100
                    product['profit_margin'] = round(margin, 1)
                else:
                    product['profit_margin'] = None
            
            context['products'] = products
            
            # Enhanced pagination context
            total_count = products_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': products_data.get('next'),
                'previous': products_data.get('previous'),
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Filter and sort context
            context['filters'] = {
                'search': search,
                'category': category_filter,
                'type': type_filter,
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
                'price_min': price_min,
                'price_max': price_max,
                'supplier': supplier_filter,
            }
            
            # Get category statistics
            try:
                category_stats = self._get_category_statistics(api_client)
                context['category_stats'] = category_stats
            except APIException:
                context['category_stats'] = {}
            
            # Filter options
            context['category_options'] = [
                {'value': '', 'label': 'Todas las Categorías'},
                {'value': 'service', 'label': 'Servicios'},
                {'value': 'part', 'label': 'Partes/Repuestos'},
                {'value': 'material', 'label': 'Materiales'},
                {'value': 'tool', 'label': 'Herramientas'},
                {'value': 'consumable', 'label': 'Consumibles'},
            ]
            
            context['type_options'] = [
                {'value': '', 'label': 'Todos los Tipos'},
                {'value': 'service', 'label': 'Servicio'},
                {'value': 'part', 'label': 'Parte'},
                {'value': 'material', 'label': 'Material'},
            ]
            
            context['status_options'] = [
                {'value': '', 'label': 'Todos los Estados'},
                {'value': 'active', 'label': 'Activos'},
                {'value': 'inactive', 'label': 'Inactivos'},
                {'value': 'low_stock', 'label': 'Stock Bajo'},
                {'value': 'out_of_stock', 'label': 'Sin Stock'},
            ]
            
            context['sort_options'] = [
                {'value': 'name', 'label': 'Nombre'},
                {'value': 'product_code', 'label': 'Código'},
                {'value': 'category', 'label': 'Categoría'},
                {'value': 'price', 'label': 'Precio'},
                {'value': 'created_at', 'label': 'Fecha de Creación'},
                {'value': 'updated_at', 'label': 'Última Actualización'},
            ]
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar el catálogo de productos")
            context['products'] = []
            context['pagination'] = {
                'count': 0,
                'current_page': 1,
                'total_pages': 0,
                'page_range': [],
                'has_previous': False,
                'has_next': False,
                'start_index': 0,
                'end_index': 0,
            }
            context['filters'] = {
                'search': search,
                'category': category_filter,
                'type': type_filter,
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
                'price_min': price_min,
                'price_max': price_max,
                'supplier': supplier_filter,
            }
            context['category_stats'] = {}
        
        return context
    
    def _get_page_number(self):
        """Get and validate page number from request."""
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)  # Ensure page is at least 1
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        """Generate a smart page range for pagination."""
        if total_pages <= window:
            return list(range(1, total_pages + 1))
        
        # Calculate start and end of the window
        half_window = window // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        # Adjust if we're near the beginning or end
        if end - start < window - 1:
            if start == 1:
                end = min(total_pages, start + window - 1)
            else:
                start = max(1, end - window + 1)
        
        return list(range(start, end + 1))
    
    def _get_category_statistics(self, api_client):
        """Get product statistics by category."""
        try:
            # This would be a custom endpoint for category statistics
            # For now, we'll return empty stats
            return {
                'total_products': 0,
                'active_products': 0,
                'services': 0,
                'parts': 0,
                'materials': 0,
                'low_stock_items': 0,
            }
        except Exception:
            return {}


class ProductDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced product detail view with comprehensive information display."""
    template_name = 'frontend/inventory/product_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            
            # Get product data
            product_data = api_client.get(f'products/{product_id}/')
            
            if product_data:
                # Add category styling
                category = product_data.get('category', '').lower()
                if category == 'service':
                    product_data['category_class'] = 'primary'
                    product_data['category_icon'] = 'bi-tools'
                elif category == 'part':
                    product_data['category_class'] = 'success'
                    product_data['category_icon'] = 'bi-gear'
                elif category == 'material':
                    product_data['category_class'] = 'info'
                    product_data['category_icon'] = 'bi-box'
                elif category == 'tool':
                    product_data['category_class'] = 'warning'
                    product_data['category_icon'] = 'bi-hammer'
                elif category == 'consumable':
                    product_data['category_class'] = 'secondary'
                    product_data['category_icon'] = 'bi-droplet'
                else:
                    product_data['category_class'] = 'light'
                    product_data['category_icon'] = 'bi-tag'
                
                # Add stock status
                current_stock = product_data.get('current_stock', 0)
                minimum_stock = product_data.get('minimum_stock', 0)
                
                if current_stock <= 0:
                    product_data['stock_status'] = 'out_of_stock'
                    product_data['stock_class'] = 'danger'
                    product_data['stock_label'] = 'Sin Stock'
                elif current_stock <= minimum_stock:
                    product_data['stock_status'] = 'low_stock'
                    product_data['stock_class'] = 'warning'
                    product_data['stock_label'] = 'Stock Bajo'
                else:
                    product_data['stock_status'] = 'in_stock'
                    product_data['stock_class'] = 'success'
                    product_data['stock_label'] = 'En Stock'
                
                # Calculate profit margin
                price = float(product_data.get('price', 0))
                cost = float(product_data.get('cost', 0))
                if price > 0 and cost > 0:
                    margin = ((price - cost) / price) * 100
                    product_data['profit_margin'] = round(margin, 1)
                else:
                    product_data['profit_margin'] = None
                
                # Calculate stock value
                if current_stock > 0 and cost > 0:
                    product_data['stock_value'] = current_stock * cost
                else:
                    product_data['stock_value'] = 0
            
            context['product'] = product_data
            
            # Get stock transactions for this product
            try:
                transactions_data = api_client.get('transactions/', params={
                    'product_id': product_id,
                    'page_size': 10,
                    'ordering': '-created_at'
                })
                context['recent_transactions'] = transactions_data.get('results', [])
            except APIException:
                context['recent_transactions'] = []
            
            # Get usage in work orders
            try:
                workorders_data = api_client.get('work-orders/', params={
                    'product_id': product_id,
                    'page_size': 10,
                    'ordering': '-created_at'
                })
                context['recent_workorders'] = workorders_data.get('results', [])
            except APIException:
                context['recent_workorders'] = []
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del producto")
            context['product'] = None
            context['recent_transactions'] = []
            context['recent_workorders'] = []
        
        return context


class ProductCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced product creation view with comprehensive form handling."""
    template_name = 'frontend/inventory/product_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Producto'
        context['form_action'] = 'create'
        
        # Initialize form with GET data if available
        from .forms import ProductForm
        form_data = self.request.POST if self.request.method == 'POST' else None
        context['form'] = ProductForm(form_data)
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import ProductForm

        form = ProductForm(request.POST)

        if form.is_valid():
            # Extract cleaned form data
            product_data = {
                'product_code': form.cleaned_data['product_code'],
                'name': form.cleaned_data['name'],
                'description': form.cleaned_data['description'] or '',
                'category': form.cleaned_data['category'],
                'type': form.cleaned_data['type'],
                'unit_of_measure': form.cleaned_data['unit_of_measure'],
                'price': float(form.cleaned_data['price']),
                'cost': float(form.cleaned_data['cost'] or 0),
                'estimated_hours': float(form.cleaned_data['estimated_hours'] or 0),
                'minimum_stock': int(form.cleaned_data['minimum_stock'] or 0),
                'maximum_stock': int(form.cleaned_data['maximum_stock'] or 0),
                'supplier': form.cleaned_data['supplier'] or '',
                'supplier_code': form.cleaned_data['supplier_code'] or '',
                'is_active': form.cleaned_data['is_active'],
                'is_taxable': form.cleaned_data['is_taxable'],
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.post('products/', data=product_data)
                
                messages.success(
                    request, 
                    f'Producto "{product_data["name"]}" creado exitosamente.'
                )
                return redirect('frontend:product_detail', pk=result['id'])
                
            except APIException as e:
                logger.error(f"Product creation API error: {e}")
                
                if e.status_code == 400 and e.response_data:
                    # Add API validation errors to form
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
                    form.add_error(None, e.message or "Error al crear el producto")
    
        # Form is invalid or API error occurred
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class ProductUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced product update view with comprehensive form handling."""
    template_name = 'frontend/inventory/product_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = kwargs.get('pk')
        
        context['form_title'] = 'Editar Producto'
        context['form_action'] = 'update'
        
        try:
            api_client = self.get_api_client()
            product_data = api_client.get(f'products/{product_id}/')
            context['product'] = product_data
            
            # Initialize form with product data or POST data
            if self.request.method == 'POST':
                from .forms import ProductForm
                form = ProductForm(self.request.POST)
            else:
                # Pre-populate form with existing product data
                from .forms import ProductForm
                initial_data = {
                    'product_code': product_data.get('product_code', ''),
                    'name': product_data.get('name', ''),
                    'description': product_data.get('description', ''),
                    'category': product_data.get('category', 'service'),
                    'type': product_data.get('type', 'service'),
                    'unit_of_measure': product_data.get('unit_of_measure', 'unit'),
                    'price': product_data.get('price', 0),
                    'cost': product_data.get('cost', 0),
                    'estimated_hours': product_data.get('estimated_hours', 0),
                    'minimum_stock': product_data.get('minimum_stock', 0),
                    'maximum_stock': product_data.get('maximum_stock', 0),
                    'supplier': product_data.get('supplier', ''),
                    'supplier_code': product_data.get('supplier_code', ''),
                    'is_active': product_data.get('is_active', True),
                    'is_taxable': product_data.get('is_taxable', True),
                }
                form = ProductForm(initial=initial_data)
            
            context['form'] = form
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del producto")
            context['product'] = None
            from .forms import ProductForm
            context['form'] = ProductForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import ProductForm
        
        product_id = kwargs.get('pk')
        form = ProductForm(request.POST)
        
        if form.is_valid():
            # Extract cleaned form data
            product_data = {
                'product_code': form.cleaned_data['product_code'],
                'name': form.cleaned_data['name'],
                'description': form.cleaned_data['description'] or '',
                'category': form.cleaned_data['category'],
                'type': form.cleaned_data['type'],
                'unit_of_measure': form.cleaned_data['unit_of_measure'],
                'price': float(form.cleaned_data['price']),
                'cost': float(form.cleaned_data['cost'] or 0),
                'estimated_hours': float(form.cleaned_data['estimated_hours'] or 0),
                'minimum_stock': int(form.cleaned_data['minimum_stock'] or 0),
                'maximum_stock': int(form.cleaned_data['maximum_stock'] or 0),
                'supplier': form.cleaned_data['supplier'] or '',
                'supplier_code': form.cleaned_data['supplier_code'] or '',
                'is_active': form.cleaned_data['is_active'],
                'is_taxable': form.cleaned_data['is_taxable'],
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.put(f'products/{product_id}/', data=product_data)
                
                messages.success(
                    request, 
                    f'Producto "{product_data["name"]}" actualizado exitosamente.'
                )
                return redirect('frontend:product_detail', pk=product_id)
                
            except APIException as e:
                logger.error(f"Product update API error: {e}")
                
                if e.status_code == 400 and e.response_data:
                    # Add API validation errors to form
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
                    form.add_error(None, e.message or "Error al actualizar el producto")
    
        # Form is invalid or API error occurred
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class StockListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for stock levels across warehouses."""
    template_name = 'frontend/inventory/stock_list.html'
    login_url = 'frontend:login'
    paginate_by = 25
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        category_filter = self.request.GET.get('category', '')
        warehouse_filter = self.request.GET.get('warehouse', '')
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'product__name')
        sort_order = self.request.GET.get('order', 'asc')
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {
                'with_stock_details': 'true'  # Include detailed stock information
            }
            if search:
                filters['search'] = search
            if category_filter:
                filters['product__category'] = category_filter
            if warehouse_filter:
                filters['warehouse_id'] = warehouse_filter
            if status_filter:
                filters['status'] = status_filter
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"
            
            # Get stock data with pagination
            stock_data = api_client.get_paginated(
                'stock/', 
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            stock_items = stock_data.get('results', [])
            
            # Process stock items with additional information for display
            for item in stock_items:
                # Calculate stock status indicators
                quantity_on_hand = item.get('quantity_on_hand', 0)
                quantity_reserved = item.get('quantity_reserved', 0)
                quantity_available = item.get('quantity_available', 0)
                reorder_point = item.get('product', {}).get('reorder_point', 0)
                min_stock_level = item.get('product', {}).get('min_stock_level', 0)
                
                # Determine status
                if quantity_available <= 0:
                    item['stock_status'] = 'out_of_stock'
                    item['status_class'] = 'danger'
                    item['status_label'] = 'Sin Stock'
                elif quantity_available <= min_stock_level:
                    item['stock_status'] = 'critical'
                    item['status_class'] = 'warning'
                    item['status_label'] = 'Stock Crítico'
                elif quantity_available <= reorder_point:
                    item['stock_status'] = 'low'
                    item['status_class'] = 'info'
                    item['status_label'] = 'Stock Bajo'
                else:
                    item['stock_status'] = 'good'
                    item['status_class'] = 'success'
                    item['status_label'] = 'Stock Adecuado'
                
                # Calculate stock value
                unit_cost = item.get('average_cost', 0)
                item['stock_value'] = quantity_on_hand * unit_cost if unit_cost and quantity_on_hand else 0
                
                # Calculate utilization
                if quantity_on_hand > 0:
                    item['utilization'] = round((quantity_reserved / quantity_on_hand) * 100, 1)
                else:
                    item['utilization'] = 0
            
            context['stock_items'] = stock_items
            
            # Enhanced pagination context
            total_count = stock_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': stock_data.get('next'),
                'previous': stock_data.get('previous'),
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Filter and sort context
            context['filters'] = {
                'search': search,
                'category': category_filter,
                'warehouse': warehouse_filter,
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
            }
            
            # Get warehouse options
            try:
                warehouses_data = api_client.get('warehouses/', page_size=100)
                context['warehouse_options'] = [
                    {'value': w['id'], 'label': f"{w['warehouse_code']}: {w['name']}"} 
                    for w in warehouses_data.get('results', [])
                ]
            except APIException:
                context['warehouse_options'] = []
            
            # Category options
            context['category_options'] = [
                {'value': '', 'label': 'Todas las Categorías'},
                {'value': 'service', 'label': 'Servicios'},
                {'value': 'part', 'label': 'Partes/Repuestos'},
                {'value': 'material', 'label': 'Materiales'},
                {'value': 'tool', 'label': 'Herramientas'},
                {'value': 'consumable', 'label': 'Consumibles'},
            ]
            
            context['status_options'] = [
                {'value': '', 'label': 'Todos los Estados'},
                {'value': 'out_of_stock', 'label': 'Sin Stock'},
                {'value': 'critical', 'label': 'Crítico'},
                {'value': 'low', 'label': 'Bajo'},
                {'value': 'good', 'label': 'Adecuado'},
            ]
            
            context['sort_options'] = [
                {'value': 'product__name', 'label': 'Producto'},
                {'value': 'warehouse__name', 'label': 'Almacén'},
                {'value': 'quantity_available', 'label': 'Disponible'},
                {'value': 'quantity_on_hand', 'label': 'En Existencia'},
                {'value': 'product__category', 'label': 'Categoría'},
            ]
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los niveles de stock")
            context['stock_items'] = []
            context['pagination'] = {
                'count': 0,
                'current_page': 1,
                'total_pages': 0,
                'page_range': [],
                'has_previous': False,
                'has_next': False,
                'start_index': 0,
                'end_index': 0,
            }
            context['filters'] = {
                'search': search,
                'category': category_filter,
                'warehouse': warehouse_filter,
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
            }
            context['warehouse_options'] = []
        
        return context
    
    def _get_page_number(self):
        """Get and validate page number from request."""
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        """Generate a smart page range for pagination."""
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


class TransactionListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for inventory transactions."""
    template_name = 'frontend/inventory/transaction_list.html'
    login_url = 'frontend:login'
    paginate_by = 25
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        type_filter = self.request.GET.get('type', '')
        warehouse_filter = self.request.GET.get('warehouse', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        sort_by = self.request.GET.get('sort', 'transaction_date')
        sort_order = self.request.GET.get('order', 'desc')
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if type_filter:
                filters['transaction_type'] = type_filter
            if warehouse_filter:
                filters['warehouse_id'] = warehouse_filter
            if date_from:
                filters['date_from'] = date_from
            if date_to:
                filters['date_to'] = date_to
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"
            
            # Get transaction data with pagination
            transactions_data = api_client.get_paginated(
                'transactions/', 
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            transactions = transactions_data.get('results', [])
            
            # Process transactions with additional information for display
            for transaction in transactions:
                # Add type styling
                transaction_type = transaction.get('transaction_type', '').lower()
                if transaction_type == 'receipt':
                    transaction['type_class'] = 'success'
                    transaction['type_label'] = 'Entrada'
                    transaction['type_icon'] = 'bi-arrow-down-circle'
                elif transaction_type == 'issue':
                    transaction['type_class'] = 'danger'
                    transaction['type_label'] = 'Salida'
                    transaction['type_icon'] = 'bi-arrow-up-circle'
                elif transaction_type == 'transfer':
                    transaction['type_class'] = 'primary'
                    transaction['type_label'] = 'Transferencia'
                    transaction['type_icon'] = 'bi-arrow-left-right'
                elif transaction_type == 'adjustment':
                    transaction['type_class'] = 'warning'
                    transaction['type_label'] = 'Ajuste'
                    transaction['type_icon'] = 'bi-gear'
                elif transaction_type == 'return':
                    transaction['type_class'] = 'info'
                    transaction['type_label'] = 'Devolución'
                    transaction['type_icon'] = 'bi-arrow-repeat'
                elif transaction_type == 'scrap':
                    transaction['type_class'] = 'dark'
                    transaction['type_label'] = 'Desecho'
                    transaction['type_icon'] = 'bi-trash'
                else:
                    transaction['type_class'] = 'secondary'
                    transaction['type_label'] = transaction_type.title()
                    transaction['type_icon'] = 'bi-question-circle'
                
                # Calculate total amount
                quantity = transaction.get('quantity', 0)
                unit_cost = transaction.get('unit_cost', 0)
                transaction['total_amount'] = quantity * unit_cost if unit_cost else 0
                
                # Format transaction date
                transaction_date = transaction.get('transaction_date', '')
                if transaction_date:
                    # Try to parse the date for better display
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
                        transaction['formatted_date'] = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        transaction['formatted_date'] = transaction_date
                else:
                    transaction['formatted_date'] = 'Fecha no disponible'
            
            context['transactions'] = transactions
            
            # Enhanced pagination context
            total_count = transactions_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': transactions_data.get('next'),
                'previous': transactions_data.get('previous'),
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Filter and sort context
            context['filters'] = {
                'search': search,
                'type': type_filter,
                'warehouse': warehouse_filter,
                'date_from': date_from,
                'date_to': date_to,
                'sort': sort_by,
                'order': sort_order,
            }
            
            # Get warehouse options
            try:
                warehouses_data = api_client.get('warehouses/', page_size=100)
                context['warehouse_options'] = [
                    {'value': w['id'], 'label': f"{w['warehouse_code']}: {w['name']}"} 
                    for w in warehouses_data.get('results', [])
                ]
            except APIException:
                context['warehouse_options'] = []
            
            # Type options
            context['type_options'] = [
                {'value': '', 'label': 'Todos los Tipos'},
                {'value': 'receipt', 'label': 'Entrada'},
                {'value': 'issue', 'label': 'Salida'},
                {'value': 'transfer', 'label': 'Transferencia'},
                {'value': 'adjustment', 'label': 'Ajuste'},
                {'value': 'return', 'label': 'Devolución'},
                {'value': 'scrap', 'label': 'Desecho'},
            ]
            
            context['sort_options'] = [
                {'value': 'transaction_date', 'label': 'Fecha'},
                {'value': 'product__name', 'label': 'Producto'},
                {'value': 'warehouse__name', 'label': 'Almacén'},
                {'value': 'transaction_type', 'label': 'Tipo'},
                {'value': 'quantity', 'label': 'Cantidad'},
            ]
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar las transacciones de inventario")
            context['transactions'] = []
            context['pagination'] = {
                'count': 0,
                'current_page': 1,
                'total_pages': 0,
                'page_range': [],
                'has_previous': False,
                'has_next': False,
                'start_index': 0,
                'end_index': 0,
            }
            context['filters'] = {
                'search': search,
                'type': type_filter,
                'warehouse': warehouse_filter,
                'date_from': date_from,
                'date_to': date_to,
                'sort': sort_by,
                'order': sort_order,
            }
            context['warehouse_options'] = []
        
        return context
    
    def _get_page_number(self):
        """Get and validate page number from request."""
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        """Generate a smart page range for pagination."""
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


class InventoryAlertsView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for inventory alerts and notifications."""
    template_name = 'frontend/inventory/alerts.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get inventory alerts data
            alerts_data = api_client.get('alerts/', params={
                'category': 'inventory',
                'page_size': 50
            })
            
            alerts = alerts_data.get('results', [])
            
            # Process alerts with additional information for display
            for alert in alerts:
                # Add severity styling
                severity = alert.get('severity', '').lower()
                if severity == 'critical':
                    alert['severity_class'] = 'danger'
                    alert['severity_icon'] = 'bi-exclamation-triangle'
                elif severity == 'high':
                    alert['severity_class'] = 'warning'
                    alert['severity_icon'] = 'bi-exclamation-circle'
                elif severity == 'medium':
                    alert['severity_class'] = 'info'
                    alert['severity_icon'] = 'bi-info-circle'
                elif severity == 'low':
                    alert['severity_class'] = 'secondary'
                    alert['severity_icon'] = 'bi-info'
                else:
                    alert['severity_class'] = 'light'
                    alert['severity_icon'] = 'bi-circle'
                
                # Add alert type icons
                alert_type = alert.get('alert_type', '').lower()
                if alert_type == 'inventory':
                    alert['type_icon'] = 'bi-box'
                elif alert_type == 'maintenance':
                    alert['type_icon'] = 'bi-tools'
                elif alert_type == 'business':
                    alert['type_icon'] = 'bi-briefcase'
                else:
                    alert['type_icon'] = 'bi-bell'
            
            context['alerts'] = alerts
            
            # Get summary statistics
            try:
                summary_data = api_client.get('inventory/alerts-summary/')
                context['summary'] = summary_data
            except APIException:
                context['summary'] = {
                    'total_alerts': len(alerts),
                    'critical_alerts': len([a for a in alerts if a.get('severity') == 'critical']),
                    'high_alerts': len([a for a in alerts if a.get('severity') == 'high']),
                    'medium_alerts': len([a for a in alerts if a.get('severity') == 'medium']),
                    'low_alerts': len([a for a in alerts if a.get('severity') == 'low']),
                }
            
            # Get critical items
            try:
                critical_data = api_client.get('inventory/critical-items/')
                context['critical_items'] = critical_data.get('results', [])
            except APIException:
                context['critical_items'] = []
        
        except APIException as e:
            self.handle_api_error(e, "Error al cargar las alertas de inventario")
            context['alerts'] = []
            context['summary'] = {
                'total_alerts': 0,
                'critical_alerts': 0,
                'high_alerts': 0,
                'medium_alerts': 0,
                'low_alerts': 0,
            }
            context['critical_items'] = []
        
        return context


class InventoryAnalyticsView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for inventory analytics and reporting."""
    template_name = 'frontend/inventory/analytics.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get inventory analytics data
            analytics_data = api_client.get('inventory/analytics/')
            
            context.update({
                'summary_stats': analytics_data.get('summary_stats', {}),
                'stock_turnover': analytics_data.get('stock_turnover', {}),
                'abc_analysis': analytics_data.get('abc_analysis', {}),
                'seasonal_trends': analytics_data.get('seasonal_trends', {}),
                'inventory_valuation': analytics_data.get('inventory_valuation', {}),
                
                # Chart data
                'stock_level_chart': analytics_data.get('stock_level_chart', {}),
                'turnover_chart': analytics_data.get('turnover_chart', {}),
                'valuation_chart': analytics_data.get('valuation_chart', {}),
                
                # Top moving items
                'top_moving_items': analytics_data.get('top_moving_items', []),
                'slow_moving_items': analytics_data.get('slow_moving_items', []),
                
                # Inventory performance KPIs
                'performance_kpis': analytics_data.get('performance_kpis', {}),
            })
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los análisis de inventario")
            
            # Fallback data
            context.update({
                'summary_stats': {},
                'stock_turnover': {},
                'abc_analysis': {},
                'seasonal_trends': {},
                'inventory_valuation': {},
                'stock_level_chart': {},
                'turnover_chart': {},
                'valuation_chart': {},
                'top_moving_items': [],
                'slow_moving_items': [],
                'performance_kpis': {},
            })
        
        return context


# Stock Movement Views
class StockMovementView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for creating stock movements (receipts, issues, transfers)."""
    template_name = 'frontend/inventory/stock_movement.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get context for creating stock movements
        try:
            api_client = self.get_api_client()
            
            # Get products and warehouses for dropdowns
            products_data = api_client.get('products/', params={'page_size': 100})
            warehouses_data = api_client.get('warehouses/', params={'page_size': 100})
            
            context['products'] = products_data.get('results', [])
            context['warehouses'] = warehouses_data.get('results', [])
            
            # Transaction type options
            context['transaction_types'] = [
                {'value': 'receipt', 'label': 'Entrada de Mercancía'},
                {'value': 'issue', 'label': 'Salida de Mercancía'},
                {'value': 'transfer', 'label': 'Transferencia entre Almacenes'},
                {'value': 'adjustment', 'label': 'Ajuste de Inventario'},
            ]
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos para movimiento de stock")
            context['products'] = []
            context['warehouses'] = []
            context['transaction_types'] = []
        
        return context


class StockMovementCreateView(LoginRequiredMixin, APIClientMixin, View):
    """API endpoint for creating stock movements."""
    
    def post(self, request, *args, **kwargs):
        try:
            api_client = self.get_api_client()
            
            # Get form data
            movement_data = {
                'transaction_type': request.POST.get('transaction_type'),
                'product_id': request.POST.get('product_id'),
                'warehouse_id': request.POST.get('warehouse_id'),
                'quantity': int(request.POST.get('quantity', 0)),
                'unit_cost': float(request.POST.get('unit_cost', 0)),
                'notes': request.POST.get('notes', ''),
                'reference_type': request.POST.get('reference_type', ''),
                'reference_id': request.POST.get('reference_id', ''),
                'reference_number': request.POST.get('reference_number', ''),
            }
            
            # Add destination warehouse for transfers
            if movement_data['transaction_type'] == 'transfer':
                movement_data['destination_warehouse_id'] = request.POST.get('destination_warehouse_id')
            
            # Validate required fields
            if not movement_data['transaction_type'] or not movement_data['product_id'] or not movement_data['warehouse_id']:
                messages.error(request, "Tipo de transacción, producto y almacén son campos obligatorios.")
                return redirect('frontend:stock_movement')
            
            if movement_data['quantity'] <= 0:
                messages.error(request, "La cantidad debe ser mayor a cero.")
                return redirect('frontend:stock_movement')
            
            # Create the transaction via API
            result = api_client.post('transactions/', data=movement_data)
            
            messages.success(request, f"Transacción de inventario registrada exitosamente: {movement_data['transaction_type'].title()}")
            return redirect('frontend:transaction_list')
            
        except APIException as e:
            self.handle_api_error(e, "Error al registrar la transacción de inventario")
            return redirect('frontend:stock_movement')
        except Exception as e:
            messages.error(request, f"Error inesperado al registrar la transacción: {str(e)}")
            return redirect('frontend:stock_movement')


def get_low_stock_items(request):
    """API endpoint to get low stock items for alerts."""
    from django.http import JsonResponse
    from .services import ForgeAPIClient
    from .services.api_client import APIException
    
    try:
        api_client = ForgeAPIClient(request=request)
        low_stock_data = api_client.get('inventory/low-stock/', params={'limit': 10})
        return JsonResponse({'items': low_stock_data.get('results', [])})
    except APIException as e:
        return JsonResponse({'error': str(e), 'items': []}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e), 'items': []}, status=500)


def get_inventory_summary(request):
    """API endpoint to get inventory summary for dashboard."""
    from django.http import JsonResponse
    from .services import ForgeAPIClient
    from .services.api_client import APIException
    
    try:
        api_client = ForgeAPIClient(request=request)
        summary_data = api_client.get('inventory/summary/')
        return JsonResponse(summary_data)
    except APIException as e:
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)