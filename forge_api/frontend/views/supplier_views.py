"""
Supplier views for the frontend application.
"""
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.exceptions import APIException
from ..mixins import APIClientMixin
from ..forms.supplier_forms import SupplierCreateForm, SupplierUpdateForm, SupplierFilterForm

logger = logging.getLogger(__name__)


class SupplierListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Supplier list view with enhanced pagination, search and filtering."""
    template_name = 'frontend/suppliers/supplier_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    # Cache for 5 minutes for anonymous users, 1 minute for authenticated
    @method_decorator(cache_page(60 * 1, key_prefix='supplier_list_authenticated'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize filter form
        filter_form = SupplierFilterForm(self.request.GET or None)
        context['filter_form'] = filter_form
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort_by', '-created_at')
        show_inactive = self.request.GET.get('show_inactive') == 'on'
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if status_filter:
                filters['status'] = status_filter
            if sort_by:
                filters['ordering'] = sort_by
            if not show_inactive:
                filters['is_active'] = True
            
            # Get suppliers data with pagination
            suppliers_data = api_client.get_suppliers(
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            context['suppliers'] = suppliers_data.get('results', [])
            
            # Enhanced pagination context
            total_count = suppliers_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': suppliers_data.get('next'),
                'previous': suppliers_data.get('previous'),
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
                'sort_by': sort_by,
                'show_inactive': show_inactive,
            }
            
            # Status options for filter dropdown
            context['status_options'] = [
                {'value': '', 'label': 'Todos los estados'},
                {'value': 'ACTIVE', 'label': 'Activos'},
                {'value': 'INACTIVE', 'label': 'Inactivos'},
                {'value': 'SUSPENDED', 'label': 'Suspendidos'},
            ]
            
            # Sort options
            context['sort_options'] = [
                {'value': 'name', 'label': 'Nombre'},
                {'value': 'supplier_code', 'label': 'Código'},
                {'value': 'rating', 'label': 'Calificación'},
                {'value': 'created_at', 'label': 'Fecha de creación'},
            ]
            
        except APIException as e:
            logger.error(f"API Error loading suppliers: {e}")
            self.handle_api_error(e, "Error al cargar la lista de proveedores. Por favor, verifique que el módulo de proveedores esté correctamente configurado.")
            context['suppliers'] = []
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
                'sort_by': sort_by,
                'show_inactive': show_inactive,
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


class SupplierDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced supplier detail view."""
    template_name = 'frontend/suppliers/supplier_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            supplier_data = api_client.get_supplier(supplier_id)
            
            if supplier_data:
                context['supplier'] = supplier_data
            else:
                messages.error(self.request, 'Proveedor no encontrado.')
                context['supplier'] = None
                
        except APIException as e:
            logger.error(f"API Error loading supplier detail: {e}")
            self.handle_api_error(e, "Error al cargar los datos del proveedor. El endpoint puede no estar disponible.")
            context['supplier'] = None
        
        return context


class SupplierCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Supplier creation view with form validation."""
    template_name = 'frontend/suppliers/supplier_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Proveedor'
        context['form_action'] = 'create'
        
        # Initialize form with POST data if available, otherwise empty form
        if self.request.method == 'POST':
            context['form'] = SupplierCreateForm(self.request.POST)
        else:
            context['form'] = SupplierCreateForm()
            
        return context
    
    def post(self, request, *args, **kwargs):
        form = SupplierCreateForm(request.POST)
        
        if form.is_valid():
            supplier_data = form.cleaned_data
            
            try:
                api_client = self.get_api_client()
                result = api_client.create_supplier(supplier_data)
                
                messages.success(request, f'Proveedor "{supplier_data["name"]}" creado exitosamente.')
                supplier_id = result.get('supplier_id') or result.get('id')
                return redirect('frontend:supplier_detail', pk=supplier_id)
                
            except APIException as e:
                self.handle_api_error(e, "Error al crear el proveedor")
        else:
            # Form validation failed
            messages.error(request, 'Por favor corrige los errores en el formulario.')
            
        # If we reach here, either API error or form validation failed
        context = self.get_context_data(**kwargs)
        context['form'] = form  # Preserve form data and errors
        return self.render_to_response(context)


class SupplierUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Supplier update view with form validation."""
    template_name = 'frontend/suppliers/supplier_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier_id = kwargs.get('pk')
        context['form_title'] = 'Editar Proveedor'
        context['form_action'] = 'update'
        
        try:
            api_client = self.get_api_client()
            supplier = api_client.get_supplier(supplier_id)
            context['supplier'] = supplier
            
            # Initialize form with supplier data
            if self.request.method == 'POST':
                context['form'] = SupplierUpdateForm(self.request.POST)
            else:
                # Populate form with existing supplier data
                initial_data = {
                    'supplier_code': supplier.get('supplier_code', ''),
                    'name': supplier.get('name', ''),
                    'contact_person': supplier.get('contact_person', ''),
                    'contact_email': supplier.get('contact_email', ''),
                    'contact_phone': supplier.get('contact_phone', ''),
                    'website': supplier.get('website', ''),
                    'address': supplier.get('address', ''),
                    'city': supplier.get('city', ''),
                    'state': supplier.get('state', ''),
                    'country': supplier.get('country', ''),
                    'tax_id': supplier.get('tax_id', ''),
                    'payment_terms': supplier.get('payment_terms', 30),
                    'currency_code': supplier.get('currency_code', 'MXN'),
                    'status': supplier.get('status', 'ACTIVE'),
                    'is_preferred': supplier.get('is_preferred', False),
                    'notes': supplier.get('notes', ''),
                }
                context['form'] = SupplierUpdateForm(initial=initial_data)
                
        except APIException as e:
            self.handle_api_error(e, "Error al cargar el proveedor")
            context['supplier'] = None
            context['form'] = SupplierUpdateForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        supplier_id = kwargs.get('pk')
        form = SupplierUpdateForm(request.POST)
        
        if form.is_valid():
            supplier_data = form.cleaned_data
            
            try:
                api_client = self.get_api_client()
                api_client.update_supplier(supplier_id, supplier_data)
                
                messages.success(request, 'Proveedor actualizado exitosamente.')
                return redirect(f"{reverse_lazy('frontend:supplier_detail', kwargs={'pk': supplier_id})}?updated=true")
                
            except APIException as e:
                self.handle_api_error(e, "Error al actualizar el proveedor")
        else:
            # Form validation failed
            messages.error(request, 'Por favor corrige los errores en el formulario.')
            
        # If we reach here, either API error or form validation failed
        context = self.get_context_data(**kwargs)
        context['form'] = form  # Preserve form data and errors
        return self.render_to_response(context)


class SupplierDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Supplier delete view."""
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        supplier_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            api_client.delete_supplier(supplier_id)
            
            messages.success(request, 'Proveedor eliminado exitosamente.')
            return redirect('frontend:supplier_list')
            
        except APIException as e:
            self.handle_api_error(e, "Error al eliminar el proveedor")
            return redirect('frontend:supplier_detail', pk=supplier_id)

