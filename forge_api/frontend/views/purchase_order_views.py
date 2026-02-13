"""
Purchase Order views for the frontend application.
"""
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.shortcuts import redirect
from django.urls import reverse_lazy

from rest_framework.exceptions import APIException
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class PurchaseOrderListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Purchase Order list view with enhanced pagination and search functionality."""
    template_name = 'frontend/purchase_orders/purchase_order_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'order_date')
        sort_order = self.request.GET.get('order', 'desc')
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if status_filter:
                filters['status'] = status_filter
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"
            
            # Get purchase orders data with pagination
            po_data = api_client.get_purchase_orders(
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            context['purchase_orders'] = po_data.get('results', [])
            
            # Enhanced pagination context
            total_count = po_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': po_data.get('next'),
                'previous': po_data.get('previous'),
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
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
            }
            
            # Status options for filter dropdown
            context['status_options'] = [
                {'value': '', 'label': 'Todos los estados'},
                {'value': 'DRAFT', 'label': 'Borrador'},
                {'value': 'SUBMITTED', 'label': 'Enviada'},
                {'value': 'APPROVED', 'label': 'Aprobada'},
                {'value': 'ORDERED', 'label': 'Ordenada'},
                {'value': 'RECEIVED', 'label': 'Recibida'},
                {'value': 'PARTIAL', 'label': 'Parcialmente Recibida'},
                {'value': 'CANCELLED', 'label': 'Cancelada'},
            ]
            
            # Sort options
            context['sort_options'] = [
                {'value': 'po_number', 'label': 'Número'},
                {'value': 'order_date', 'label': 'Fecha de Orden'},
                {'value': 'expected_delivery_date', 'label': 'Fecha Esperada'},
                {'value': 'status', 'label': 'Estado'},
            ]
            
        except APIException as e:
            logger.error(f"API Error loading purchase orders: {e}")
            self.handle_api_error(e, "Error al cargar la lista de órdenes de compra. Por favor, verifique que el módulo de compras esté correctamente configurado.")
            context['purchase_orders'] = []
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
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
            }
        
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


class PurchaseOrderDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced purchase order detail view."""
    template_name = 'frontend/purchase_orders/purchase_order_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        po_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            po_data = api_client.get_purchase_order(po_id)
            
            if po_data:
                context['purchase_order'] = po_data
                
                # Fetch PO items
                po_items_data = api_client.get_po_items(po_id=po_id)
                po_items = po_items_data.get('results', [])
                
                # Calculate totals for each item and overall
                items_subtotal = 0
                items_tax_total = 0
                items_total = 0
                
                for item in po_items:
                    # Calculate individual item total
                    unit_price = float(item.get('unit_price', 0))
                    quantity = int(item.get('quantity', 0))
                    discount_percent = float(item.get('discount_percent', 0))
                    tax_percent = float(item.get('tax_percent', 0))
                    
                    subtotal = unit_price * quantity
                    discount_amount = subtotal * (discount_percent / 100)
                    after_discount = subtotal - discount_amount
                    tax_amount = after_discount * (tax_percent / 100)
                    item_total = after_discount + tax_amount
                    
                    item['total_price'] = round(item_total, 2)
                    items_subtotal += after_discount
                    items_tax_total += tax_amount
                    items_total += item_total
                    
                    # Add description if available
                    item['description'] = f"Producto {item.get('internal_sku', 'N/A')}"
                
                # Update purchase order with calculated amounts
                po_data['subtotal'] = round(items_subtotal, 2)
                po_data['tax_amount'] = round(items_tax_total, 2)
                po_data['total_amount'] = round(items_total, 2)
                
                context['po_items'] = po_items
                context['items_total'] = round(items_total, 2)
            else:
                messages.error(self.request, 'Orden de compra no encontrada.')
                context['purchase_order'] = None
                context['po_items'] = []
                context['items_total'] = 0
                
        except APIException as e:
            logger.error(f"API Error loading purchase order detail: {e}")
            self.handle_api_error(e, "Error al cargar los datos de la orden de compra. El endpoint puede no estar disponible.")
            context['purchase_order'] = None
            context['po_items'] = []
            context['items_total'] = 0
        
        return context


class PurchaseOrderCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Purchase Order creation view."""
    template_name = 'frontend/purchase_orders/purchase_order_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Orden de Compra'
        context['form_action'] = 'create'
        
        # Get suppliers for dropdown
        try:
            api_client = self.get_api_client()
            suppliers_data = api_client.get_suppliers(page_size=100)
            context['suppliers'] = suppliers_data.get('results', [])
        except APIException:
            context['suppliers'] = []
        
        # For new PO, initialize empty items list
        context['po_items'] = []
        context['items_total'] = 0
        
        return context
    
    def post(self, request, *args, **kwargs):
        from datetime import datetime
        
        # Get supplier with validation
        supplier_id = request.POST.get('supplier', '')
        if not supplier_id:
            messages.error(request, "Debe seleccionar un proveedor para la orden de compra.")
            return self.get(request, *args, **kwargs)
        
        try:
            supplier_id = int(supplier_id)
        except (ValueError, TypeError):
            messages.error(request, "El proveedor seleccionado no es válido.")
            return self.get(request, *args, **kwargs)
        
        po_data = {
            'po_number': request.POST.get('po_number', ''),
            'supplier': supplier_id,
            'order_date': request.POST.get('order_date', datetime.now().strftime('%Y-%m-%d')),
            'expected_delivery_date': request.POST.get('expected_delivery_date', '') or None,
            'status': request.POST.get('status', 'DRAFT'),
            'notes': request.POST.get('notes', ''),
        }
        
        try:
            api_client = self.get_api_client()
            result = api_client.create_purchase_order(po_data)
            
            # Get the PO ID from the response
            po_id = result.get('po_id') or result.get('id')
            if not po_id:
                # If no ID in response, try to get from po_number
                po_id = result.get('po_number')
            
            messages.success(request, f'Orden de compra creada exitosamente.')
            
            # Handle PO items
            if po_id:
                self._process_po_items(api_client, po_id, request)
            
            return redirect('frontend:purchase_order_detail', pk=po_id)
            
        except APIException as e:
            logger.error(f"API Error creating purchase order: {e}")
            self.handle_api_error(e, "Error al crear la orden de compra")
            return self.get(request, *args, **kwargs)
    
    def _process_po_items(self, api_client, po_id, request):
        """Process purchase order items from the form."""
        # Get item data from the form
        item_ids = request.POST.getlist('item_id')
        internal_skus = request.POST.getlist('item_internal_sku')
        descriptions = request.POST.getlist('item_description')
        quantities = request.POST.getlist('item_quantity')
        unit_prices = request.POST.getlist('item_unit_price')
        discount_percents = request.POST.getlist('item_discount_percent')
        tax_percents = request.POST.getlist('item_tax_percent')
        
        # Process each item
        for i in range(len(internal_skus)):
            if internal_skus[i].strip():  # Only process if SKU is not empty
                item_data = {
                    'po': po_id,
                    'internal_sku': internal_skus[i],
                    'quantity': int(float(quantities[i])) if quantities[i] else 1,
                    'unit_price': float(unit_prices[i]) if unit_prices[i] else 0.0,
                    'discount_percent': float(discount_percents[i]) if discount_percents[i] else 0.0,
                    'tax_percent': float(tax_percents[i]) if tax_percents[i] else 0.0,
                    'notes': descriptions[i][:255] if descriptions[i] else ''  # Limit to field size
                }
                
                # Create or update item based on whether it has an ID
                if item_ids and i < len(item_ids) and item_ids[i]:
                    # Update existing item
                    api_client.update_po_item(int(item_ids[i]), item_data)
                else:
                    # Create new item
                    api_client.create_po_item(item_data)


class PurchaseOrderUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Purchase Order update view."""
    template_name = 'frontend/purchase_orders/purchase_order_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        po_id = kwargs.get('pk')
        context['form_title'] = 'Editar Orden de Compra'
        context['form_action'] = 'update'
        
        try:
            api_client = self.get_api_client()
            po_data = api_client.get_purchase_order(po_id)
            context['purchase_order'] = po_data
            
            # Get suppliers for dropdown
            suppliers_data = api_client.get_suppliers(page_size=100)
            context['suppliers'] = suppliers_data.get('results', [])
            
            # Fetch PO items
            if po_data:
                po_items_data = api_client.get_po_items(po_id=po_id)
                po_items = po_items_data.get('results', [])
                
                # Calculate totals for each item and overall
                items_subtotal = 0
                items_tax_total = 0
                items_total = 0
                
                for item in po_items:
                    # Calculate individual item total
                    unit_price = float(item.get('unit_price', 0))
                    quantity = int(item.get('quantity', 0))
                    discount_percent = float(item.get('discount_percent', 0))
                    tax_percent = float(item.get('tax_percent', 0))
                    
                    subtotal = unit_price * quantity
                    discount_amount = subtotal * (discount_percent / 100)
                    after_discount = subtotal - discount_amount
                    tax_amount = after_discount * (tax_percent / 100)
                    item_total = after_discount + tax_amount
                    
                    item['total_price'] = round(item_total, 2)
                    items_subtotal += after_discount
                    items_tax_total += tax_amount
                    items_total += item_total
                    
                    # Add description if available
                    item['description'] = item.get('description', f'Producto {item.get("internal_sku", "N/A")}')
                
                # Update purchase order with calculated amounts
                po_data['subtotal'] = round(items_subtotal, 2)
                po_data['tax_amount'] = round(items_tax_total, 2)
                po_data['total_amount'] = round(items_total, 2)
                
                context['po_items'] = po_items
                context['items_total'] = round(items_total, 2)
            else:
                context['po_items'] = []
                context['items_total'] = 0
                
        except APIException as e:
            self.handle_api_error(e, "Error al cargar la orden de compra")
            context['purchase_order'] = None
            context['suppliers'] = []
            context['po_items'] = []
            context['items_total'] = 0
        
        return context
    
    def post(self, request, *args, **kwargs):
        po_id = kwargs.get('pk')
        po_data = {
            'po_number': request.POST.get('po_number', ''),
            'supplier': int(request.POST.get('supplier', 0)),
            'order_date': request.POST.get('order_date', ''),
            'expected_delivery_date': request.POST.get('expected_delivery_date', '') or None,
            'status': request.POST.get('status', 'DRAFT'),
            'notes': request.POST.get('notes', ''),
        }
        
        try:
            api_client = self.get_api_client()
            api_client.update_purchase_order(po_id, po_data)
            
            messages.success(request, 'Orden de compra actualizada exitosamente.')
            
            # Handle PO items
            self._process_po_items(api_client, po_id, request)
            
            return redirect('frontend:purchase_order_detail', pk=po_id)
            
        except APIException as e:
            self.handle_api_error(e, "Error al actualizar la orden de compra")
            return self.get(request, *args, **kwargs)


class PurchaseOrderDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Purchase Order delete view."""
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        po_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            api_client.delete_purchase_order(po_id)
            
            messages.success(request, 'Orden de compra eliminada exitosamente.')
            return redirect('frontend:purchase_order_list')
            
        except APIException as e:
            self.handle_api_error(e, "Error al eliminar la orden de compra")
            return redirect('frontend:purchase_order_detail', pk=po_id)

