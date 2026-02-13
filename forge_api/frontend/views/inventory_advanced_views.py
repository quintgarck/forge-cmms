"""
Advanced inventory management views.
Handles Warehouse, Bin, PriceList, ProductPrice, and PurchaseOrder interfaces.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.conf import settings

from ..services.api_client import ForgeAPIClient, APIException
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class WarehouseAdvancedListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Advanced warehouse management with location visualization."""
    template_name = 'frontend/inventory/warehouse_advanced_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'warehouse_code')
        sort_order = self.request.GET.get('order', 'asc')
        
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
            
            # Get warehouses data
            warehouses_data = api_client.get('warehouses/', params={
                'page': page,
                'page_size': self.paginate_by,
                **filters
            })
            
            warehouses = warehouses_data.get('results', [])
            
            # Process warehouses for enhanced display
            for warehouse in warehouses:
                # Add status styling
                status = warehouse.get('status', '').lower()
                warehouse['status_class'] = self._get_status_class(status)
                warehouse['status_icon'] = self._get_status_icon(status)
                
                # Get bin count for each warehouse
                try:
                    bins_data = api_client.get('bins/', params={
                        'warehouse_code': warehouse.get('warehouse_code'),
                        'page_size': 1
                    })
                    warehouse['bin_count'] = bins_data.get('count', 0)
                except APIException:
                    warehouse['bin_count'] = 0
                
                # Get stock summary
                try:
                    stock_data = api_client.get('stock/', params={
                        'warehouse': warehouse.get('warehouse_id'),
                        'page_size': 1
                    })
                    warehouse['stock_items'] = stock_data.get('count', 0)
                    
                    # Calculate total value (would need aggregation endpoint)
                    warehouse['total_value'] = 0  # Placeholder
                except APIException:
                    warehouse['stock_items'] = 0
                    warehouse['total_value'] = 0
                
                # Calculate utilization percentage
                if warehouse['bin_count'] > 0:
                    # This would need actual occupancy data
                    warehouse['utilization'] = min(85, (warehouse['stock_items'] / warehouse['bin_count']) * 100)
                else:
                    warehouse['utilization'] = 0
            
            context['warehouses'] = warehouses
            
            # Enhanced pagination context
            total_count = warehouses_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': warehouses_data.get('next'),
                'previous': warehouses_data.get('previous'),
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Filter context
            context['filters'] = {
                'search': search,
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
            }
            
            # Status options for filter
            context['status_options'] = [
                {'value': '', 'label': 'Todos los Estados'},
                {'value': 'active', 'label': 'Activos'},
                {'value': 'inactive', 'label': 'Inactivos'},
                {'value': 'maintenance', 'label': 'Mantenimiento'},
            ]
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar almacenes")
            context['warehouses'] = []
            context['pagination'] = self._get_empty_pagination()
            context['filters'] = {
                'search': search,
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
            }
        
        return context
    
    def _get_status_class(self, status):
        """Get Bootstrap class for warehouse status."""
        status_classes = {
            'active': 'success',
            'inactive': 'secondary',
            'maintenance': 'warning',
        }
        return status_classes.get(status, 'light')
    
    def _get_status_icon(self, status):
        """Get icon for warehouse status."""
        status_icons = {
            'active': 'bi-check-circle',
            'inactive': 'bi-x-circle',
            'maintenance': 'bi-tools',
        }
        return status_icons.get(status, 'bi-building')
    
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
    
    def _get_empty_pagination(self):
        """Get empty pagination context for error states."""
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


class BinManagementView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Interactive bin management with warehouse maps."""
    template_name = 'frontend/inventory/bin_management.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse_id = kwargs.get('warehouse_id')
        
        try:
            api_client = self.get_api_client()
            
            # Get warehouse details
            warehouse = api_client.get(f'warehouses/{warehouse_id}/')
            context['warehouse'] = warehouse
            
            # Get bins for this warehouse
            bins_data = api_client.get('bins/', params={
                'warehouse_code': warehouse.get('warehouse_code')
            })
            bins = bins_data.get('results', [])
            
            # Process bins for map visualization
            bin_map = {}
            zones = set()
            aisles = set()
            
            for bin_item in bins:
                zone = bin_item.get('zone', 'DEFAULT')
                aisle = bin_item.get('aisle', '1')
                rack = bin_item.get('rack', '1')
                level = bin_item.get('level', '1')
                
                zones.add(zone)
                aisles.add(aisle)
                
                # Create hierarchical structure for visualization
                if zone not in bin_map:
                    bin_map[zone] = {}
                if aisle not in bin_map[zone]:
                    bin_map[zone][aisle] = {}
                if rack not in bin_map[zone][aisle]:
                    bin_map[zone][aisle][rack] = {}
                
                bin_map[zone][aisle][rack][level] = bin_item
                
                # Add utilization data
                capacity = bin_item.get('capacity', 100)
                occupancy = bin_item.get('current_occupancy', 0)
                bin_item['utilization_percent'] = (occupancy / capacity * 100) if capacity > 0 else 0
                
                # Add status styling
                if bin_item['utilization_percent'] >= 90:
                    bin_item['status_class'] = 'danger'
                    bin_item['status_label'] = 'Lleno'
                elif bin_item['utilization_percent'] >= 70:
                    bin_item['status_class'] = 'warning'
                    bin_item['status_label'] = 'Alto'
                elif bin_item['utilization_percent'] >= 30:
                    bin_item['status_class'] = 'success'
                    bin_item['status_label'] = 'Normal'
                else:
                    bin_item['status_class'] = 'info'
                    bin_item['status_label'] = 'Bajo'
            
            context['bins'] = bins
            context['bin_map'] = bin_map
            context['zones'] = sorted(zones)
            context['aisles'] = sorted(aisles)
            
            # Calculate warehouse statistics
            total_bins = len(bins)
            active_bins = len([b for b in bins if b.get('is_active', True)])
            total_capacity = sum(b.get('capacity', 0) for b in bins)
            total_occupancy = sum(b.get('current_occupancy', 0) for b in bins)
            
            context['warehouse_stats'] = {
                'total_bins': total_bins,
                'active_bins': active_bins,
                'total_capacity': total_capacity,
                'total_occupancy': total_occupancy,
                'utilization_percent': (total_occupancy / total_capacity * 100) if total_capacity > 0 else 0,
            }
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar información de ubicaciones")
            context['warehouse'] = None
            context['bins'] = []
            context['bin_map'] = {}
            context['zones'] = []
            context['aisles'] = []
            context['warehouse_stats'] = {
                'total_bins': 0,
                'active_bins': 0,
                'total_capacity': 0,
                'total_occupancy': 0,
                'utilization_percent': 0,
            }
        
        return context


class PriceListManagementView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Price list management with date validation."""
    template_name = 'frontend/inventory/price_list_management.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get price lists
            price_lists_data = api_client.get('price-lists/')
            price_lists = price_lists_data.get('results', [])
            
            # Process price lists for enhanced display
            for price_list in price_lists:
                # Add status styling based on validity dates
                from datetime import date
                today = date.today()
                valid_from = price_list.get('valid_from')
                valid_until = price_list.get('valid_until')
                
                if valid_from and valid_until:
                    if today < valid_from:
                        price_list['validity_status'] = 'future'
                        price_list['validity_class'] = 'info'
                        price_list['validity_label'] = 'Futuro'
                    elif today > valid_until:
                        price_list['validity_status'] = 'expired'
                        price_list['validity_class'] = 'danger'
                        price_list['validity_label'] = 'Expirado'
                    else:
                        price_list['validity_status'] = 'active'
                        price_list['validity_class'] = 'success'
                        price_list['validity_label'] = 'Vigente'
                else:
                    price_list['validity_status'] = 'active'
                    price_list['validity_class'] = 'success'
                    price_list['validity_label'] = 'Vigente'
                
                # Get product count for each price list
                try:
                    products_data = api_client.get('product-prices/', params={
                        'price_list': price_list.get('price_list_id'),
                        'page_size': 1
                    })
                    price_list['product_count'] = products_data.get('count', 0)
                except APIException:
                    price_list['product_count'] = 0
            
            context['price_lists'] = price_lists
            
            # Get currencies for new price lists
            try:
                currencies_data = api_client.get('currencies/')
                context['currencies'] = currencies_data.get('results', [])
            except APIException:
                context['currencies'] = []
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar listas de precios")
            context['price_lists'] = []
            context['currencies'] = []
        
        return context


class PurchaseOrderWorkflowView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Complete purchase order workflow with status tracking."""
    template_name = 'frontend/inventory/purchase_order_workflow.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        status_filter = self.request.GET.get('status', '')
        supplier_filter = self.request.GET.get('supplier', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        page = self._get_page_number()
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if status_filter:
                filters['status'] = status_filter
            if supplier_filter:
                filters['supplier'] = supplier_filter
            if date_from:
                filters['order_date__gte'] = date_from
            if date_to:
                filters['order_date__lte'] = date_to
            
            # Get purchase orders
            po_data = api_client.get('purchase-orders/', params={
                'page': page,
                'page_size': self.paginate_by,
                **filters
            })
            
            purchase_orders = po_data.get('results', [])
            
            # Process purchase orders for workflow display
            for po in purchase_orders:
                # Add status styling and workflow information
                status = po.get('status', '').upper()
                po['status_class'] = self._get_po_status_class(status)
                po['status_icon'] = self._get_po_status_icon(status)
                po['workflow_step'] = self._get_workflow_step(status)
                
                # Calculate progress percentage
                po['progress_percent'] = self._calculate_progress(status)
                
                # Add urgency indicators
                from datetime import date, timedelta
                expected_date = po.get('expected_delivery_date')
                if expected_date:
                    try:
                        expected = date.fromisoformat(expected_date)
                        days_until = (expected - date.today()).days
                        
                        if days_until < 0:
                            po['urgency'] = 'overdue'
                            po['urgency_class'] = 'danger'
                            po['urgency_label'] = f'{abs(days_until)} días atrasado'
                        elif days_until <= 3:
                            po['urgency'] = 'urgent'
                            po['urgency_class'] = 'warning'
                            po['urgency_label'] = f'{days_until} días restantes'
                        else:
                            po['urgency'] = 'normal'
                            po['urgency_class'] = 'success'
                            po['urgency_label'] = f'{days_until} días restantes'
                    except ValueError:
                        po['urgency'] = 'normal'
                        po['urgency_class'] = 'secondary'
                        po['urgency_label'] = 'Sin fecha'
                
                # Get items count
                try:
                    items_data = api_client.get('po-items/', params={
                        'po': po.get('po_id'),
                        'page_size': 1
                    })
                    po['items_count'] = items_data.get('count', 0)
                except APIException:
                    po['items_count'] = 0
            
            context['purchase_orders'] = purchase_orders
            
            # Pagination context
            total_count = po_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
            }
            
            # Filter context
            context['filters'] = {
                'status': status_filter,
                'supplier': supplier_filter,
                'date_from': date_from,
                'date_to': date_to,
            }
            
            # Status options for filter
            context['status_options'] = [
                {'value': '', 'label': 'Todos los Estados'},
                {'value': 'DRAFT', 'label': 'Borrador'},
                {'value': 'SUBMITTED', 'label': 'Enviado'},
                {'value': 'APPROVED', 'label': 'Aprobado'},
                {'value': 'ORDERED', 'label': 'Ordenado'},
                {'value': 'RECEIVED', 'label': 'Recibido'},
                {'value': 'PARTIAL', 'label': 'Parcial'},
                {'value': 'CANCELLED', 'label': 'Cancelado'},
            ]
            
            # Get suppliers for filter
            try:
                suppliers_data = api_client.get('suppliers/')
                context['suppliers'] = suppliers_data.get('results', [])
            except APIException:
                context['suppliers'] = []
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar órdenes de compra")
            context['purchase_orders'] = []
            context['pagination'] = self._get_empty_pagination()
            context['suppliers'] = []
        
        return context
    
    def _get_po_status_class(self, status):
        """Get Bootstrap class for PO status."""
        status_classes = {
            'DRAFT': 'secondary',
            'SUBMITTED': 'info',
            'APPROVED': 'primary',
            'ORDERED': 'warning',
            'RECEIVED': 'success',
            'PARTIAL': 'warning',
            'CANCELLED': 'danger',
        }
        return status_classes.get(status, 'light')
    
    def _get_po_status_icon(self, status):
        """Get icon for PO status."""
        status_icons = {
            'DRAFT': 'bi-file-earmark',
            'SUBMITTED': 'bi-send',
            'APPROVED': 'bi-check-circle',
            'ORDERED': 'bi-cart-check',
            'RECEIVED': 'bi-box-seam',
            'PARTIAL': 'bi-box',
            'CANCELLED': 'bi-x-circle',
        }
        return status_icons.get(status, 'bi-file')
    
    def _get_workflow_step(self, status):
        """Get workflow step number for progress display."""
        workflow_steps = {
            'DRAFT': 1,
            'SUBMITTED': 2,
            'APPROVED': 3,
            'ORDERED': 4,
            'RECEIVED': 6,
            'PARTIAL': 5,
            'CANCELLED': 0,
        }
        return workflow_steps.get(status, 1)
    
    def _calculate_progress(self, status):
        """Calculate progress percentage based on status."""
        progress_map = {
            'DRAFT': 15,
            'SUBMITTED': 30,
            'APPROVED': 50,
            'ORDERED': 70,
            'PARTIAL': 85,
            'RECEIVED': 100,
            'CANCELLED': 0,
        }
        return progress_map.get(status, 0)
    
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
    
    def _get_empty_pagination(self):
        """Get empty pagination context for error states."""
        return {
            'count': 0,
            'current_page': 1,
            'total_pages': 0,
            'page_range': [],
            'has_previous': False,
            'has_next': False,
        }