"""
Frontend views for ForgeDB web application.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.conf import settings
from datetime import datetime
import logging

from .viewmixins import APIClientMixin
from .views_auth import LoginView, LogoutView
from .views_dashboard import DashboardView, DashboardDataView, KPIDetailsView

from .services import ForgeAPIClient, AuthenticationService
from .services.api_client import APIException
from .forms import ClientForm, ClientSearchForm, EquipmentForm, MaintenanceScheduleForm, MaintenanceForm, MaintenanceSearchForm, StockMovementForm, StockSearchForm, WarehouseForm, WarehouseSearchForm, StockAlertForm, StockAdjustmentForm

logger = logging.getLogger(__name__)


# Client Views
class ClientListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Client list view with enhanced pagination and search functionality."""
    template_name = 'frontend/clients/client_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'name')
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
            
            # Get clients data with pagination
            clients_data = api_client.get_clients(
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            context['clients'] = clients_data.get('results', [])
            
            # Enhanced pagination context
            total_count = clients_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': clients_data.get('next'),
                'previous': clients_data.get('previous'),
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
                {'value': 'active', 'label': 'Activos'},
                {'value': 'credit_exceeded', 'label': 'Límite excedido'},
                {'value': 'with_balance', 'label': 'Con saldo pendiente'},
            ]
            
            # Sort options
            context['sort_options'] = [
                {'value': 'name', 'label': 'Nombre'},
                {'value': 'email', 'label': 'Email'},
                {'value': 'created_at', 'label': 'Fecha de creación'},
                {'value': 'credit_limit', 'label': 'Límite de crédito'},
                {'value': 'credit_used', 'label': 'Crédito utilizado'},
            ]
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar la lista de clientes")
            # Don't redirect from get_context_data, just set empty context
            context['clients'] = []
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

class ClientDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced client detail view with comprehensive information display."""
    template_name = 'frontend/clients/client_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            
            # Get client data
            client_data = api_client.get_client(client_id)
            
            if client_data:
                # Calculate available credit
                credit_limit = float(client_data.get('credit_limit', 0))
                current_balance = float(client_data.get('current_balance', 0))
                client_data['available_credit'] = credit_limit - current_balance
                
                # Calculate credit utilization percentage
                if credit_limit > 0:
                    client_data['credit_utilization'] = (current_balance / credit_limit) * 100
                else:
                    client_data['credit_utilization'] = 0
                
                # Determine credit status
                if current_balance > credit_limit:
                    client_data['credit_status'] = 'exceeded'
                    client_data['credit_status_label'] = 'Límite Excedido'
                    client_data['credit_status_class'] = 'danger'
                elif current_balance > (credit_limit * 0.8):
                    client_data['credit_status'] = 'warning'
                    client_data['credit_status_label'] = 'Cerca del Límite'
                    client_data['credit_status_class'] = 'warning'
                elif current_balance > 0:
                    client_data['credit_status'] = 'with_balance'
                    client_data['credit_status_label'] = 'Con Saldo'
                    client_data['credit_status_class'] = 'info'
                else:
                    client_data['credit_status'] = 'clear'
                    client_data['credit_status_label'] = 'Al Corriente'
                    client_data['credit_status_class'] = 'success'
            
            context['client'] = client_data
            
            # Get client's work orders with enhanced filtering
            try:
                workorders_data = api_client.get_workorders(client_id=client_id, page_size=50)
                workorders = workorders_data.get('results', [])
                
                # Process work orders for better display
                for workorder in workorders:
                    # Add status styling
                    status = workorder.get('status', '').lower()
                    if status == 'pending':
                        workorder['status_class'] = 'warning'
                        workorder['status_label'] = 'Pendiente'
                    elif status == 'in_progress':
                        workorder['status_class'] = 'info'
                        workorder['status_label'] = 'En Progreso'
                    elif status == 'completed':
                        workorder['status_class'] = 'success'
                        workorder['status_label'] = 'Completada'
                    elif status == 'cancelled':
                        workorder['status_class'] = 'danger'
                        workorder['status_label'] = 'Cancelada'
                    else:
                        workorder['status_class'] = 'secondary'
                        workorder['status_label'] = status.title()
                
                context['workorders'] = workorders
                
                # Calculate work order statistics
                total_workorders = len(workorders)
                completed_workorders = len([wo for wo in workorders if wo.get('status') == 'completed'])
                pending_workorders = len([wo for wo in workorders if wo.get('status') == 'pending'])
                in_progress_workorders = len([wo for wo in workorders if wo.get('status') == 'in_progress'])
                
                context['workorder_stats'] = {
                    'total': total_workorders,
                    'completed': completed_workorders,
                    'pending': pending_workorders,
                    'in_progress': in_progress_workorders,
                    'completion_rate': (completed_workorders / total_workorders * 100) if total_workorders > 0 else 0
                }
                
            except APIException as wo_error:
                logger.warning(f"Could not load work orders for client {client_id}: {wo_error}")
                context['workorders'] = []
                context['workorder_stats'] = {
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'in_progress': 0,
                    'completion_rate': 0
                }
            
            # Get client's equipment (if available)
            try:
                equipment_data = api_client.get_equipment(client_id=client_id, page_size=20)
                context['equipment'] = equipment_data.get('results', [])
            except APIException as eq_error:
                logger.warning(f"Could not load equipment for client {client_id}: {eq_error}")
                context['equipment'] = []
            
            # Get recent service history summary
            try:
                # This would be a custom endpoint for service history
                # For now, we'll derive it from work orders
                recent_services = []
                for wo in workorders[:5]:  # Last 5 work orders
                    if wo.get('status') == 'completed':
                        recent_services.append({
                            'date': wo.get('completed_date') or wo.get('created_date'),
                            'description': wo.get('description', 'Servicio completado'),
                            'equipment': wo.get('equipment', {}),
                            'total_amount': wo.get('total_amount', 0)
                        })
                
                context['recent_services'] = recent_services[:3]  # Show only last 3
                
            except Exception as service_error:
                logger.warning(f"Could not process service history for client {client_id}: {service_error}")
                context['recent_services'] = []
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del cliente")
            # Don't redirect from get_context_data, just set empty context
            context['client'] = None
            context['workorders'] = []
            context['workorder_stats'] = {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'in_progress': 0,
                'completion_rate': 0
            }
            context['equipment'] = []
            context['recent_services'] = []
        
        return context

class ClientCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced client creation view with Django forms and validation."""
    template_name = 'frontend/clients/client_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Cliente'
        context['form_action'] = 'create'
        
        # Initialize form with GET data if available (for form repopulation)
        form_data = self.request.POST if self.request.method == 'POST' else None
        context['form'] = ClientForm(form_data)
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import ClientForm

        form = ClientForm(request.POST)

        if form.is_valid():
            # Extract cleaned form data
            client_data = {
                'client_code': form.cleaned_data['client_code'],
                'type': form.cleaned_data['type'],
                'name': form.cleaned_data['name'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data['address'] or '',
                'credit_limit': float(form.cleaned_data['credit_limit'] or 0),
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.create_client(client_data)
                
                messages.success(
                    request, 
                    f'Cliente "{client_data["name"]}" creado exitosamente.'
                )
                return redirect('frontend:client_detail', pk=result['id'])
                
            except APIException as e:
                logger.error(f"Client creation API error: {e}")
                
                # Handle specific API errors
                if e.status_code == 401:
                    # Authentication error - try to refresh token
                    from .services import AuthenticationService
                    auth_service = AuthenticationService(request)
                    
                    if auth_service.refresh_token():
                        # Token refreshed, try again
                        try:
                            api_client = self.get_api_client()
                            result = api_client.create_client(client_data)
                            
                            messages.success(
                                request, 
                                f'Cliente "{client_data["name"]}" creado exitosamente.'
                            )
                            return redirect('frontend:client_detail', pk=result['id'])
                        except APIException as retry_e:
                            form.add_error(None, f"Error de autenticación: {retry_e.message}")
                    else:
                        form.add_error(None, "Sesión expirada. Por favor, inicie sesión nuevamente.")
                        messages.error(request, "Su sesión ha expirado. Por favor, inicie sesión nuevamente.")
                        
                elif e.status_code == 500:
                    # Server error - show user-friendly message
                    form.add_error(None, "Error interno del servidor. El backend API no está funcionando correctamente. Por favor, contacte al administrador.")
                    logger.error(f"Server error 500 during client creation: {e}")
                    
                elif e.status_code == 400 and e.response_data:
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
                    # Handle other API errors
                    error_message = e.message or "Error al crear el cliente"
                    if e.status_code == 401:
                        error_message = "Sesión expirada. Por favor, inicie sesión nuevamente."
                    elif e.status_code == 403:
                        error_message = "No tiene permisos para realizar esta acción."
                    elif e.status_code == 404:
                        error_message = "El recurso solicitado no fue encontrado."
                    elif e.status_code >= 500:
                        error_message = "Error interno del servidor. Por favor, contacte al administrador."
                    
                    form.add_error(None, error_message)
        
        # Form is invalid or API error occurred
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

class ClientUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced client update view with Django forms and validation."""
    template_name = 'frontend/clients/client_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_id = kwargs.get('pk')
        
        context['form_title'] = 'Editar Cliente'
        context['form_action'] = 'update'
        
        try:
            api_client = self.get_api_client()
            client_data = api_client.get_client(client_id)
            context['client'] = client_data
            
            # Initialize form with client data or POST data
            if self.request.method == 'POST':
                form = ClientForm(self.request.POST)
            else:
                # Pre-populate form with existing client data
                initial_data = {
                    'client_code': client_data.get('client_code', ''),
                    'type': client_data.get('type', 'individual'),
                    'name': client_data.get('name', ''),
                    'email': client_data.get('email', ''),
                    'phone': client_data.get('phone', ''),
                    'address': client_data.get('address', ''),
                    'credit_limit': client_data.get('credit_limit', 0),
                }
                form = ClientForm(initial=initial_data)
            
            context['form'] = form
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del cliente")
            context['client'] = None
            context['form'] = ClientForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import ClientForm
        
        client_id = kwargs.get('pk')
        form = ClientForm(request.POST)
        
        if form.is_valid():
            # Extract cleaned form data
            client_data = {
                'client_code': form.cleaned_data['client_code'],
                'type': form.cleaned_data['type'],
                'name': form.cleaned_data['name'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data['address'] or '',
                'credit_limit': float(form.cleaned_data['credit_limit'] or 0),
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.update_client(client_id, client_data)
                
                messages.success(
                    request, 
                    f'Cliente "{client_data["name"]}" actualizado exitosamente.'
                )
                return redirect('frontend:client_detail', pk=client_id)
                
            except APIException as e:
                logger.error(f"Client update API error: {e}")
                
                # Handle specific API errors
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
                    form.add_error(None, e.message or "Error al actualizar el cliente")
        
        # Form is invalid or API error occurred
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)

class ClientDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Client deletion view."""
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        client_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            api_client.delete_client(client_id)
            
            messages.success(request, 'Cliente eliminado exitosamente.')
        except APIException as e:
            self.handle_api_error(e, "Error al eliminar el cliente")
        
        return redirect('frontend:client_list')

# Work Order Views
class WorkOrderListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced work order list view with filtering and search."""
    template_name = 'frontend/workorders/workorder_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '')
        priority_filter = self.request.GET.get('priority', '')
        technician_filter = self.request.GET.get('technician', '')
        client_filter = self.request.GET.get('client', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        sort_by = self.request.GET.get('sort', 'created_at')
        sort_order = self.request.GET.get('order', 'desc')
        page = self._get_page_number()
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if status_filter:
                filters['status'] = status_filter
            if priority_filter:
                filters['priority'] = priority_filter
            if technician_filter:
                filters['technician'] = technician_filter
            if client_filter:
                filters['client'] = client_filter
            if date_from:
                filters['date_from'] = date_from
            if date_to:
                filters['date_to'] = date_to
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"
            
            # Get work orders data
            workorders_data = api_client.get_workorders(
                page=page,
                page_size=self.paginate_by,
                **filters
            )
            
            workorders = workorders_data.get('results', [])
            
            # Enhanced work order processing
            for workorder in workorders:
                # Add status styling
                status = workorder.get('status', '').lower()
                workorder.update(self._get_status_styling(status))
                
                # Add priority styling
                priority = workorder.get('priority', '').lower()
                workorder.update(self._get_priority_styling(priority))
                
                # Calculate days since creation
                created_date = workorder.get('created_at')
                if created_date:
                    from datetime import datetime
                    try:
                        created = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        days_old = (datetime.now(created.tzinfo) - created).days
                        workorder['days_old'] = days_old
                        
                        # Add urgency indicators
                        if status in ['pending', 'scheduled'] and days_old > 7:
                            workorder['is_overdue'] = True
                        elif status == 'in_progress' and days_old > 14:
                            workorder['is_overdue'] = True
                    except:
                        workorder['days_old'] = 0
                
                # Format estimated vs actual hours
                estimated_hours = workorder.get('estimated_hours', 0)
                actual_hours = workorder.get('actual_hours', 0)
                if estimated_hours and actual_hours:
                    variance = ((actual_hours - estimated_hours) / estimated_hours) * 100
                    workorder['hours_variance'] = variance
                    workorder['hours_variance_class'] = 'success' if variance <= 10 else 'warning' if variance <= 25 else 'danger'
            
            context['workorders'] = workorders
            
            # Enhanced pagination
            total_count = workorders_data.get('count', 0)
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
            
            # Filter context
            context['filters'] = {
                'search': search,
                'status': status_filter,
                'priority': priority_filter,
                'technician': technician_filter,
                'client': client_filter,
                'date_from': date_from,
                'date_to': date_to,
                'sort': sort_by,
                'order': sort_order,
            }
            
            # Get filter options
            context.update(self._get_filter_options(api_client))
            
            # Calculate statistics
            context['stats'] = self._calculate_workorder_stats(workorders)
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar las órdenes de trabajo")
            context.update({
                'workorders': [],
                'pagination': self._empty_pagination(),
                'filters': {
                    'search': search,
                    'status': status_filter,
                    'priority': priority_filter,
                    'technician': technician_filter,
                    'client': client_filter,
                    'date_from': date_from,
                    'date_to': date_to,
                    'sort': sort_by,
                    'order': sort_order,
                },
                'stats': self._empty_stats(),
            })
        
        return context
    
    def _get_status_styling(self, status):
        """Get status styling information."""
        status_map = {
            'draft': {'status_class': 'secondary', 'status_label': 'Borrador', 'status_icon': 'bi-file-earmark'},
            'scheduled': {'status_class': 'info', 'status_label': 'Programada', 'status_icon': 'bi-calendar-check'},
            'in_progress': {'status_class': 'warning', 'status_label': 'En Progreso', 'status_icon': 'bi-gear'},
            'waiting_parts': {'status_class': 'danger', 'status_label': 'Esperando Partes', 'status_icon': 'bi-box'},
            'waiting_approval': {'status_class': 'info', 'status_label': 'Esperando Aprobación', 'status_icon': 'bi-clock'},
            'completed': {'status_class': 'success', 'status_label': 'Completada', 'status_icon': 'bi-check-circle'},
            'invoiced': {'status_class': 'primary', 'status_label': 'Facturada', 'status_icon': 'bi-receipt'},
            'cancelled': {'status_class': 'dark', 'status_label': 'Cancelada', 'status_icon': 'bi-x-circle'},
        }
        return status_map.get(status, {
            'status_class': 'secondary',
            'status_label': status.title(),
            'status_icon': 'bi-question-circle'
        })
    
    def _get_priority_styling(self, priority):
        """Get priority styling information."""
        priority_map = {
            'low': {'priority_class': 'success', 'priority_label': 'Baja', 'priority_icon': 'bi-arrow-down'},
            'normal': {'priority_class': 'info', 'priority_label': 'Normal', 'priority_icon': 'bi-dash'},
            'high': {'priority_class': 'warning', 'priority_label': 'Alta', 'priority_icon': 'bi-arrow-up'},
            'urgent': {'priority_class': 'danger', 'priority_label': 'Urgente', 'priority_icon': 'bi-exclamation-triangle'},
        }
        return priority_map.get(priority, {
            'priority_class': 'secondary',
            'priority_label': priority.title(),
            'priority_icon': 'bi-question'
        })
    
    def _get_filter_options(self, api_client):
        """Get filter options for dropdowns."""
        options = {
            'status_options': [
                {'value': '', 'label': 'Todos los Estados'},
                {'value': 'draft', 'label': 'Borrador'},
                {'value': 'scheduled', 'label': 'Programada'},
                {'value': 'in_progress', 'label': 'En Progreso'},
                {'value': 'waiting_parts', 'label': 'Esperando Partes'},
                {'value': 'waiting_approval', 'label': 'Esperando Aprobación'},
                {'value': 'completed', 'label': 'Completada'},
                {'value': 'invoiced', 'label': 'Facturada'},
                {'value': 'cancelled', 'label': 'Cancelada'},
            ],
            'priority_options': [
                {'value': '', 'label': 'Todas las Prioridades'},
                {'value': 'low', 'label': 'Baja'},
                {'value': 'normal', 'label': 'Normal'},
                {'value': 'high', 'label': 'Alta'},
                {'value': 'urgent', 'label': 'Urgente'},
            ],
            'sort_options': [
                {'value': 'created_at', 'label': 'Fecha de Creación'},
                {'value': 'scheduled_date', 'label': 'Fecha Programada'},
                {'value': 'priority', 'label': 'Prioridad'},
                {'value': 'status', 'label': 'Estado'},
                {'value': 'client__name', 'label': 'Cliente'},
                {'value': 'wo_number', 'label': 'Número de Orden'},
            ],
            'technician_options': [{'value': '', 'label': 'Todos los Técnicos'}],
            'client_options': [{'value': '', 'label': 'Todos los Clientes'}],
        }
        
        # Try to get technicians and clients for filter dropdowns
        try:
            technicians_data = api_client.get_technicians(page_size=100)
            for tech in technicians_data.get('results', []):
                options['technician_options'].append({
                    'value': tech['id'],
                    'label': f"{tech.get('first_name', '')} {tech.get('last_name', '')}".strip()
                })
        except:
            pass
        
        try:
            clients_data = api_client.get_clients(page_size=100)
            for client in clients_data.get('results', []):
                client_id = client.get('client_id') or client.get('id')
                if client_id:
                    options['client_options'].append({
                        'value': client_id,
                        'label': client.get('name', '')
                    })
        except:
            pass
        
        return options
    
    def _calculate_workorder_stats(self, workorders):
        """Calculate work order statistics."""
        if not workorders:
            return self._empty_stats()
        
        total = len(workorders)
        by_status = {}
        by_priority = {}
        overdue_count = 0
        
        for wo in workorders:
            status = wo.get('status', 'unknown')
            priority = wo.get('priority', 'normal')
            
            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            if wo.get('is_overdue'):
                overdue_count += 1
        
        return {
            'total': total,
            'by_status': by_status,
            'by_priority': by_priority,
            'overdue': overdue_count,
            'completion_rate': (by_status.get('completed', 0) / total * 100) if total > 0 else 0,
        }
    
    def _empty_stats(self):
        """Return empty statistics."""
        return {
            'total': 0,
            'by_status': {},
            'by_priority': {},
            'overdue': 0,
            'completion_rate': 0,
        }
    
    def _empty_pagination(self):
        """Return empty pagination."""
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

class WorkOrderDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced work order detail view with status management."""
    template_name = 'frontend/workorders/workorder_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workorder_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            
            # Get work order details
            workorder_data = api_client.get_workorder(workorder_id)
            
            if workorder_data:
                # Process status information
                status = workorder_data.get('status', '').lower()
                workorder_data['status_info'] = self._get_status_info(status)
                
                # Get available status transitions
                workorder_data['available_transitions'] = self._get_available_transitions(status)
                
                # Calculate progress percentage
                workorder_data['progress_percentage'] = self._calculate_progress(status)
                
                context['workorder'] = workorder_data
                
                # Get client details
                if workorder_data.get('client_id'):
                    try:
                        client_data = api_client.get_client(workorder_data['client_id'])
                        context['client'] = client_data
                    except APIException:
                        context['client'] = None
                
                # Get equipment details
                if workorder_data.get('equipment_id'):
                    try:
                        equipment_data = api_client.get_equipment_detail(workorder_data['equipment_id'])
                        context['equipment'] = equipment_data
                    except APIException:
                        context['equipment'] = None
                
                # Get assigned technician details
                if workorder_data.get('assigned_technician_id'):
                    try:
                        technician_data = api_client.get_technician(workorder_data['assigned_technician_id'])
                        context['assigned_technician'] = technician_data
                    except APIException:
                        context['assigned_technician'] = None
                
                # Get available technicians for assignment
                try:
                    technicians_data = api_client.get_technicians(page_size=50)
                    context['available_technicians'] = technicians_data.get('results', [])
                except APIException:
                    context['available_technicians'] = []
                
                # Get work order history/timeline
                try:
                    # This would be a custom endpoint for work order history
                    # For now, we'll create a mock timeline based on status
                    context['timeline'] = self._create_timeline(workorder_data)
                except Exception:
                    context['timeline'] = []
                
            else:
                context['workorder'] = None
                
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos de la orden de trabajo")
            context['workorder'] = None
        
        return context
    
    def _get_status_info(self, status):
        """Get status display information."""
        status_map = {
            'draft': {
                'label': 'Borrador',
                'class': 'secondary',
                'icon': 'bi-file-earmark',
                'description': 'Orden de trabajo en borrador'
            },
            'pending': {
                'label': 'Pendiente',
                'class': 'warning',
                'icon': 'bi-clock',
                'description': 'Esperando asignación o programación'
            },
            'scheduled': {
                'label': 'Programada',
                'class': 'info',
                'icon': 'bi-calendar-check',
                'description': 'Programada para una fecha específica'
            },
            'in_progress': {
                'label': 'En Progreso',
                'class': 'primary',
                'icon': 'bi-gear',
                'description': 'Trabajo en curso'
            },
            'on_hold': {
                'label': 'En Espera',
                'class': 'warning',
                'icon': 'bi-pause-circle',
                'description': 'Trabajo pausado temporalmente'
            },
            'completed': {
                'label': 'Completada',
                'class': 'success',
                'icon': 'bi-check-circle',
                'description': 'Trabajo completado exitosamente'
            },
            'cancelled': {
                'label': 'Cancelada',
                'class': 'danger',
                'icon': 'bi-x-circle',
                'description': 'Orden de trabajo cancelada'
            }
        }
        
        return status_map.get(status, {
            'label': status.title(),
            'class': 'secondary',
            'icon': 'bi-question-circle',
            'description': 'Estado desconocido'
        })
    
    def _get_available_transitions(self, current_status):
        """Get available status transitions based on current status."""
        transitions = {
            'draft': ['pending', 'scheduled', 'cancelled'],
            'pending': ['scheduled', 'in_progress', 'on_hold', 'cancelled'],
            'scheduled': ['in_progress', 'on_hold', 'cancelled'],
            'in_progress': ['on_hold', 'completed', 'cancelled'],
            'on_hold': ['in_progress', 'cancelled'],
            'completed': [],  # No transitions from completed
            'cancelled': []   # No transitions from cancelled
        }
        
        available = transitions.get(current_status, [])
        
        # Convert to display format
        return [
            {
                'value': status,
                'info': self._get_status_info(status)
            }
            for status in available
        ]
    
    def _calculate_progress(self, status):
        """Calculate progress percentage based on status."""
        progress_map = {
            'draft': 0,
            'pending': 10,
            'scheduled': 25,
            'in_progress': 50,
            'on_hold': 50,
            'completed': 100,
            'cancelled': 0
        }
        
        return progress_map.get(status, 0)
    
    def _create_timeline(self, workorder_data):
        """Create a timeline of work order events."""
        timeline = []
        
        # Created event
        if workorder_data.get('created_date'):
            timeline.append({
                'date': workorder_data['created_date'],
                'title': 'Orden Creada',
                'description': 'Orden de trabajo creada',
                'icon': 'bi-plus-circle',
                'class': 'info'
            })
        
        # Scheduled event
        if workorder_data.get('scheduled_date'):
            timeline.append({
                'date': workorder_data['scheduled_date'],
                'title': 'Programada',
                'description': f'Programada para {workorder_data.get("scheduled_date")}',
                'icon': 'bi-calendar-check',
                'class': 'primary'
            })
        
        # Started event
        if workorder_data.get('started_date'):
            timeline.append({
                'date': workorder_data['started_date'],
                'title': 'Trabajo Iniciado',
                'description': 'Trabajo iniciado por el técnico',
                'icon': 'bi-play-circle',
                'class': 'success'
            })
        
        # Completed event
        if workorder_data.get('completed_date'):
            timeline.append({
                'date': workorder_data['completed_date'],
                'title': 'Trabajo Completado',
                'description': 'Orden de trabajo completada',
                'icon': 'bi-check-circle',
                'class': 'success'
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'] if x['date'] else '')
        
        return timeline
    
    def post(self, request, *args, **kwargs):
        """Handle status updates and technician assignments."""
        workorder_id = kwargs.get('pk')
        action = request.POST.get('action')
        
        try:
            api_client = self.get_api_client()
            
            if action == 'update_status':
                new_status = request.POST.get('new_status')
                notes = request.POST.get('status_notes', '')
                
                if new_status:
                    # Update work order status
                    update_data = {
                        'status': new_status,
                        'status_notes': notes
                    }
                    
                    # Add timestamp for specific status changes
                    if new_status == 'in_progress':
                        update_data['started_date'] = request.POST.get('started_date')
                    elif new_status == 'completed':
                        update_data['completed_date'] = request.POST.get('completed_date')
                    
                    result = api_client.update_workorder(workorder_id, update_data)
                    
                    status_info = self._get_status_info(new_status)
                    messages.success(
                        request,
                        f'Estado actualizado a "{status_info["label"]}" exitosamente.'
                    )
                else:
                    messages.error(request, 'Debe seleccionar un estado válido.')
            
            elif action == 'assign_technician':
                technician_id = request.POST.get('technician_id')
                
                if technician_id:
                    update_data = {
                        'assigned_technician_id': technician_id
                    }
                    
                    result = api_client.update_workorder(workorder_id, update_data)
                    
                    messages.success(
                        request,
                        'Técnico asignado exitosamente.'
                    )
                else:
                    messages.error(request, 'Debe seleccionar un técnico válido.')
            
            elif action == 'unassign_technician':
                update_data = {
                    'assigned_technician_id': None
                }
                
                result = api_client.update_workorder(workorder_id, update_data)
                
                messages.success(
                    request,
                    'Técnico desasignado exitosamente.'
                )
            
            elif action == 'add_note':
                note_text = request.POST.get('note_text', '').strip()
                
                if note_text:
                    # This would typically be a separate notes endpoint
                    # For now, we'll add it as a status update
                    update_data = {
                        'notes': note_text
                    }
                    
                    result = api_client.update_workorder(workorder_id, update_data)
                    
                    messages.success(
                        request,
                        'Nota agregada exitosamente.'
                    )
                else:
                    messages.error(request, 'La nota no puede estar vacía.')
            
        except APIException as e:
            logger.error(f"Work order update API error: {e}")
            
            if e.status_code == 400 and e.response_data:
                # Show validation errors
                for field, errors in e.response_data.items():
                    if isinstance(errors, list):
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                    else:
                        messages.error(request, f"{field}: {errors}")
            else:
                messages.error(request, f"Error al actualizar la orden de trabajo: {e.message}")
        
        except Exception as e:
            logger.error(f"Unexpected error updating work order: {e}")
            messages.error(request, "Error inesperado al actualizar la orden de trabajo.")
        
        # Redirect back to detail view
        return redirect('frontend:workorder_detail', pk=workorder_id)

class WorkOrderCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Multi-step work order creation wizard."""
    template_name = 'frontend/workorders/workorder_wizard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current step from URL or session
        current_step = self.request.GET.get('step', '1')
        context['current_step'] = int(current_step)
        
        # Initialize wizard data from session
        wizard_data = self.request.session.get('workorder_wizard', {})
        
        # Ensure wizard_data has all necessary keys
        wizard_data.setdefault('services', [])
        wizard_data.setdefault('parts', [])
        wizard_data.setdefault('client_id', None)
        wizard_data.setdefault('equipment_id', None)
        wizard_data.setdefault('technician_id', None)
        wizard_data.setdefault('description', '')
        wizard_data.setdefault('complaint', '')
        wizard_data.setdefault('priority', 'normal')
        wizard_data.setdefault('status', 'draft')
        wizard_data.setdefault('scheduled_datetime', None)
        wizard_data.setdefault('estimated_hours', None)
        
        context['wizard_data'] = wizard_data
        
        try:
            api_client = self.get_api_client()
            
            # Load data based on current step
            if current_step == '1':
                # Step 1: Client and Equipment Selection
                context.update(self._get_step1_context(api_client, wizard_data))
            elif current_step == '2':
                # Step 2: Service Selection
                context.update(self._get_step2_context(api_client, wizard_data))
            elif current_step == '3':
                # Step 3: Scheduling and Details
                context.update(self._get_step3_context(api_client, wizard_data))
            elif current_step == '4':
                # Step 4: Review and Confirmation
                context.update(self._get_step4_context(api_client, wizard_data))
                
        except APIException as e:
            self.handle_api_error(e, "Error al cargar datos del wizard")
            context.update(self._get_empty_context())
        
        # Wizard navigation
        context['steps'] = [
            {'number': 1, 'title': 'Cliente y Equipo', 'icon': 'bi-person-gear'},
            {'number': 2, 'title': 'Servicios', 'icon': 'bi-tools'},
            {'number': 3, 'title': 'Programación', 'icon': 'bi-calendar-event'},
            {'number': 4, 'title': 'Confirmación', 'icon': 'bi-check-circle'},
        ]
        
        return context
    
    def _get_step1_context(self, api_client, wizard_data):
        """Get context for step 1: Client and Equipment Selection."""
        context = {}
        
        # Get clients for selection
        try:
            clients_data = api_client.get_clients(page_size=100)
            context['clients'] = clients_data.get('results', [])
        except APIException:
            context['clients'] = []
        
        # Get equipment for selected client
        selected_client_id = wizard_data.get('client_id')
        if selected_client_id:
            try:
                equipment_data = api_client.get_equipment(client_id=selected_client_id, page_size=50)
                context['equipment_list'] = equipment_data.get('results', [])
                
                # Get selected client details
                client_data = api_client.get_client(selected_client_id)
                context['selected_client'] = client_data
            except APIException:
                context['equipment_list'] = []
                context['selected_client'] = None
        else:
            context['equipment_list'] = []
            context['selected_client'] = None
        
        return context
    
    def _get_step2_context(self, api_client, wizard_data):
        """Get context for step 2: Service Selection."""
        context = {}
        
        # Get available services/products
        try:
            services_data = api_client.get_products(type='service', page_size=100)
            context['services'] = services_data.get('results', [])
        except APIException:
            context['services'] = []
        
        # Get parts/products
        try:
            parts_data = api_client.get_products(type='part', page_size=100)
            context['parts'] = parts_data.get('results', [])
        except APIException:
            context['parts'] = []
        
        # Selected services and parts from wizard data
        context['selected_services'] = wizard_data.get('services', [])
        context['selected_parts'] = wizard_data.get('parts', [])
        
        return context
    
    def _get_step3_context(self, api_client, wizard_data):
        """Get context for step 3: Scheduling and Details."""
        context = {}
        
        # Get available technicians
        try:
            technicians_data = api_client.get_technicians(page_size=50)
            context['technicians'] = technicians_data.get('results', [])
        except APIException:
            context['technicians'] = []
        
        # Priority and status options
        context['priority_options'] = [
            {'value': 'low', 'label': 'Baja'},
            {'value': 'normal', 'label': 'Normal'},
            {'value': 'high', 'label': 'Alta'},
            {'value': 'urgent', 'label': 'Urgente'},
        ]
        
        context['status_options'] = [
            {'value': 'draft', 'label': 'Borrador'},
            {'value': 'scheduled', 'label': 'Programada'},
        ]
        
        return context
    
    def _get_step4_context(self, api_client, wizard_data):
        """Get context for step 4: Review and Confirmation."""
        context = {}
        
        # Get full details for review
        if wizard_data.get('client_id'):
            try:
                client_data = api_client.get_client(wizard_data['client_id'])
                context['client_details'] = client_data
            except APIException:
                context['client_details'] = None
        
        if wizard_data.get('equipment_id'):
            try:
                equipment_data = api_client.get_equipment_detail(wizard_data['equipment_id'])
                context['equipment_details'] = equipment_data
            except APIException:
                context['equipment_details'] = None
        
        if wizard_data.get('technician_id'):
            try:
                technician_data = api_client.get_technician(wizard_data['technician_id'])
                context['technician_details'] = technician_data
            except APIException:
                context['technician_details'] = None
        
        # Calculate totals
        total_cost = 0
        total_hours = 0
        
        for service in wizard_data.get('services', []):
            total_cost += float(service.get('price', 0)) * int(service.get('quantity', 1))
            total_hours += float(service.get('estimated_hours', 0)) * int(service.get('quantity', 1))
        
        for part in wizard_data.get('parts', []):
            total_cost += float(part.get('price', 0)) * int(part.get('quantity', 1))
        
        context['total_cost'] = total_cost
        context['total_hours'] = total_hours
        
        return context
    
    def _get_empty_context(self):
        """Get empty context for error states."""
        return {
            'clients': [],
            'equipment_list': [],
            'services': [],
            'parts': [],
            'technicians': [],
            'selected_client': None,
            'selected_services': [],
            'selected_parts': [],
            'client_details': None,
            'equipment_details': None,
            'technician_details': None,
            'total_cost': 0,
            'total_hours': 0,
        }
    
    def post(self, request, *args, **kwargs):
        """Handle wizard form submissions."""
        current_step = request.POST.get('current_step', '1')
        action = request.POST.get('action', 'next')
        
        # Get or initialize wizard data
        wizard_data = request.session.get('workorder_wizard', {})
        
        if action == 'next':
            # Process current step and move to next
            if current_step == '1':
                wizard_data = self._process_step1(request, wizard_data)
                next_step = '2'
            elif current_step == '2':
                wizard_data = self._process_step2(request, wizard_data)
                next_step = '3'
            elif current_step == '3':
                wizard_data = self._process_step3(request, wizard_data)
                next_step = '4'
            elif current_step == '4':
                # Final step - create work order
                return self._create_workorder(request, wizard_data)
            else:
                next_step = '1'
            
            # Save wizard data to session
            request.session['workorder_wizard'] = wizard_data
            
            return redirect(f"{request.path}?step={next_step}")
            
        elif action == 'prev':
            # Go to previous step
            prev_step = str(max(1, int(current_step) - 1))
            return redirect(f"{request.path}?step={prev_step}")
            
        elif action == 'cancel':
            # Clear wizard data and redirect
            request.session.pop('workorder_wizard', None)
            messages.info(request, 'Creación de orden de trabajo cancelada.')
            return redirect('frontend:workorder_list')
        
        # Default: stay on current step
        return redirect(f"{request.path}?step={current_step}")
    
    def _process_step1(self, request, wizard_data):
        """Process step 1: Client and Equipment Selection."""
        client_id = request.POST.get('client_id')
        equipment_id = request.POST.get('equipment_id')
        
        if not client_id:
            messages.error(request, 'Debe seleccionar un cliente.')
            return wizard_data
        
        if not equipment_id:
            messages.error(request, 'Debe seleccionar un equipo.')
            return wizard_data
        
        wizard_data.update({
            'client_id': client_id,
            'equipment_id': equipment_id,
        })
        
        messages.success(request, 'Cliente y equipo seleccionados correctamente.')
        return wizard_data
    
    def _process_step2(self, request, wizard_data):
        """Process step 2: Service Selection."""
        # Get selected services
        selected_services = []
        service_ids = request.POST.getlist('service_ids')
        
        for service_id in service_ids:
            quantity = request.POST.get(f'service_quantity_{service_id}', '1')
            try:
                # In a real implementation, you'd get service details from API
                selected_services.append({
                    'id': service_id,
                    'quantity': int(quantity),
                    'name': request.POST.get(f'service_name_{service_id}', ''),
                    'price': float(request.POST.get(f'service_price_{service_id}', '0')),
                    'estimated_hours': float(request.POST.get(f'service_hours_{service_id}', '0')),
                })
            except (ValueError, TypeError):
                continue
        
        # Get selected parts
        selected_parts = []
        part_ids = request.POST.getlist('part_ids')
        
        for part_id in part_ids:
            quantity = request.POST.get(f'part_quantity_{part_id}', '1')
            try:
                selected_parts.append({
                    'id': part_id,
                    'quantity': int(quantity),
                    'name': request.POST.get(f'part_name_{part_id}', ''),
                    'price': float(request.POST.get(f'part_price_{part_id}', '0')),
                })
            except (ValueError, TypeError):
                continue
        
        if not selected_services and not selected_parts:
            messages.error(request, 'Debe seleccionar al menos un servicio o parte.')
            return wizard_data
        
        wizard_data.update({
            'services': selected_services,
            'parts': selected_parts,
        })
        
        messages.success(request, 'Servicios y partes seleccionados correctamente.')
        return wizard_data
    
    def _process_step3(self, request, wizard_data):
        """Process step 3: Scheduling and Details."""
        description = request.POST.get('description', '').strip()
        complaint = request.POST.get('complaint', '').strip()
        priority = request.POST.get('priority', 'normal')
        status = request.POST.get('status', 'draft')
        technician_id = request.POST.get('technician_id')
        scheduled_date = request.POST.get('scheduled_date')
        scheduled_time = request.POST.get('scheduled_time')
        estimated_hours = request.POST.get('estimated_hours')
        
        if not description:
            messages.error(request, 'Debe proporcionar una descripción del trabajo.')
            return wizard_data
        
        # Combine date and time
        scheduled_datetime = None
        if scheduled_date:
            if scheduled_time:
                scheduled_datetime = f"{scheduled_date} {scheduled_time}"
            else:
                scheduled_datetime = f"{scheduled_date} 09:00"
        
        wizard_data.update({
            'description': description,
            'complaint': complaint,
            'priority': priority,
            'status': status,
            'technician_id': technician_id,
            'scheduled_datetime': scheduled_datetime,
            'estimated_hours': float(estimated_hours) if estimated_hours else None,
        })
        
        messages.success(request, 'Detalles de programación configurados correctamente.')
        return wizard_data
    
    def _create_workorder(self, request, wizard_data):
        """Create the work order with all collected data."""
        try:
            api_client = self.get_api_client()
            
            # Prepare work order data
            workorder_data = {
                'client_id': wizard_data['client_id'],
                'equipment_id': wizard_data['equipment_id'],
                'description': wizard_data['description'],
                'complaint': wizard_data.get('complaint', ''),
                'priority': wizard_data.get('priority', 'normal'),
                'status': wizard_data.get('status', 'draft'),
                'assigned_technician_id': wizard_data.get('technician_id'),
                'scheduled_date': wizard_data.get('scheduled_datetime'),
                'estimated_hours': wizard_data.get('estimated_hours'),
                'services': wizard_data.get('services', []),
                'parts': wizard_data.get('parts', []),
            }
            
            # Create work order via API
            result = api_client.create_workorder(workorder_data)
            
            # Clear wizard data
            request.session.pop('workorder_wizard', None)
            
            messages.success(
                request,
                f'Orden de trabajo {result.get("wo_number", "")} creada exitosamente.'
            )
            
            return redirect('frontend:workorder_detail', pk=result['id'])
            
        except APIException as e:
            logger.error(f"Work order creation API error: {e}")
            
            if e.status_code == 400 and e.response_data:
                # Show validation errors
                for field, errors in e.response_data.items():
                    if isinstance(errors, list):
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                    else:
                        messages.error(request, f"{field}: {errors}")
            else:
                messages.error(request, f"Error al crear la orden de trabajo: {e.message}")
            
            # Stay on confirmation step
            return redirect(f"{request.path}?step=4")
        
        except Exception as e:
            logger.error(f"Unexpected error creating work order: {e}")
            messages.error(request, "Error inesperado al crear la orden de trabajo.")
            return redirect(f"{request.path}?step=4")

class WorkOrderUpdateView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/workorders/workorder_form.html'
    login_url = 'frontend:login'

class WorkOrderDeleteView(LoginRequiredMixin, View):
    login_url = 'frontend:login'

class InventoryListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Inventory overview/list view - redirects to dashboard or shows summary."""
    template_name = 'frontend/inventory/inventory_list.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get inventory summary data
            # This is a summary page, so we'll get basic stats
            try:
                # Get products count
                products_data = api_client.get('products/', params={'page_size': 1})
                context['total_products'] = products_data.get('count', 0)
            except APIException:
                context['total_products'] = 0
            
            try:
                # Get stock items count
                stock_data = api_client.get('stock/', params={'page_size': 1})
                context['total_stock_items'] = stock_data.get('count', 0)
            except APIException:
                context['total_stock_items'] = 0
            
            try:
                # Get warehouses count
                warehouses_data = api_client.get('warehouses/', params={'page_size': 1})
                context['total_warehouses'] = warehouses_data.get('count', 0)
            except APIException:
                context['total_warehouses'] = 0
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar el resumen de inventario")
            context['total_products'] = 0
            context['total_stock_items'] = 0
            context['total_warehouses'] = 0
        
        return context

class ProductListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced product catalog view with comprehensive filtering and search."""
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
        price_min = self.request.GET.get('price_min', '')
        price_max = self.request.GET.get('price_max', '')
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
            products_data = api_client.get_products(
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            context['products'] = products_data.get('results', [])
            
            # Process products for better display
            for product in context['products']:
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
                {'value': 'accessory', 'label': 'Accesorios'},
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
        from .forms import ProductForm, get_uom_choices, get_product_category_choices, get_product_type_choices
        form_data = self.request.POST if self.request.method == 'POST' else None
        context['form'] = ProductForm(
            form_data,
            category_choices=get_product_category_choices(),
            type_choices=get_product_type_choices(),
            unit_choices=get_uom_choices(),
        )
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import ProductForm, get_uom_choices, get_product_category_choices, get_product_type_choices

        form = ProductForm(
            request.POST,
            category_choices=get_product_category_choices(),
            type_choices=get_product_type_choices(),
            unit_choices=get_uom_choices(),
        )

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
            from .forms import ProductForm, get_uom_choices, get_product_category_choices, get_product_type_choices
            cat_choices = get_product_category_choices()
            type_choices = get_product_type_choices()
            uom_choices = get_uom_choices()
            if self.request.method == 'POST':
                form = ProductForm(
                    self.request.POST,
                    category_choices=cat_choices,
                    type_choices=type_choices,
                    unit_choices=uom_choices,
                )
            else:
                # Pre-populate form with existing product data (API puede devolver uom_code o unit_of_measure)
                initial_data = {
                    'product_code': product_data.get('product_code', ''),
                    'name': product_data.get('name', ''),
                    'description': product_data.get('description', ''),
                    'category': product_data.get('category', 'service'),
                    'type': product_data.get('type', 'service'),
                    'unit_of_measure': product_data.get('uom_code') or product_data.get('unit_of_measure', 'unit'),
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
                form = ProductForm(
                    initial=initial_data,
                    category_choices=cat_choices,
                    type_choices=type_choices,
                    unit_choices=uom_choices,
                )
            
            context['form'] = form
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del producto")
            context['product'] = None
            from .forms import ProductForm, get_uom_choices, get_product_category_choices, get_product_type_choices
            context['form'] = ProductForm(
                category_choices=get_product_category_choices(),
                type_choices=get_product_type_choices(),
                unit_choices=get_uom_choices(),
            )
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import ProductForm, get_uom_choices, get_product_category_choices, get_product_type_choices
        
        product_id = kwargs.get('pk')
        form = ProductForm(
            request.POST,
            category_choices=get_product_category_choices(),
            type_choices=get_product_type_choices(),
            unit_choices=get_uom_choices(),
        )
        
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

class StockListView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/inventory/stock_list.html'
    login_url = 'frontend:login'

class TransactionListView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/inventory/transaction_list.html'
    login_url = 'frontend:login'

class EquipmentListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Equipment list view with enhanced pagination and search functionality."""
    template_name = 'frontend/equipment/equipment_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        client_filter = self.request.GET.get('client', '')
        make_filter = self.request.GET.get('make', '')
        status_filter = self.request.GET.get('status', '')
        fuel_type_filter = self.request.GET.get('fuel_type', '')
        year_from = self.request.GET.get('year_from', '')
        year_to = self.request.GET.get('year_to', '')
        sort_by = self.request.GET.get('sort', 'equipment_code')
        sort_order = self.request.GET.get('order', 'asc')
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if client_filter:
                filters['client'] = client_filter
            if make_filter:
                filters['make'] = make_filter
            if status_filter:
                filters['status'] = status_filter
            if fuel_type_filter:
                filters['fuel_type'] = fuel_type_filter
            if year_from:
                filters['year_from'] = year_from
            if year_to:
                filters['year_to'] = year_to
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"
            
            # Get equipment data with pagination
            equipment_data = api_client.get_equipment(
                page=page, 
                page_size=self.paginate_by,
                **filters
            )
            
            context['equipment_list'] = equipment_data.get('results', [])
            
            # Enhanced pagination context
            total_count = equipment_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': equipment_data.get('next'),
                'previous': equipment_data.get('previous'),
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
                'client': client_filter,
                'make': make_filter,
                'status': status_filter,
                'fuel_type': fuel_type_filter,
                'year_from': year_from,
                'year_to': year_to,
                'sort': sort_by,
                'order': sort_order,
            }
            
            # Get clients for filter dropdown
            try:
                clients_data = api_client.get_clients(page_size=100)
                context['client_options'] = [{'value': '', 'label': 'Todos los clientes'}]
                for client in clients_data.get('results', []):
                    client_id = client.get('client_id') or client.get('id')
                    if client_id:
                        context['client_options'].append({
                            'value': client_id,
                            'label': client['name']
                        })
            except APIException:
                context['client_options'] = [{'value': '', 'label': 'Todos los clientes'}]
            
            # Status options for filter dropdown
            context['status_options'] = [
                {'value': '', 'label': 'Todos los estados'},
                {'value': 'active', 'label': 'Activos'},
                {'value': 'inactive', 'label': 'Inactivos'},
                {'value': 'sold', 'label': 'Vendidos'},
                {'value': 'scrapped', 'label': 'Desechados'},
            ]
            
            # Fuel type options
            context['fuel_type_options'] = [
                {'value': '', 'label': 'Todos los combustibles'},
                {'value': 'gasoline', 'label': 'Gasolina'},
                {'value': 'diesel', 'label': 'Diésel'},
                {'value': 'hybrid', 'label': 'Híbrido'},
                {'value': 'electric', 'label': 'Eléctrico'},
                {'value': 'lpg', 'label': 'Gas LP'},
                {'value': 'cng', 'label': 'Gas Natural'},
            ]
            
            # Sort options
            context['sort_options'] = [
                {'value': 'equipment_code', 'label': 'Código'},
                {'value': 'make', 'label': 'Marca'},
                {'value': 'model', 'label': 'Modelo'},
                {'value': 'year', 'label': 'Año'},
                {'value': 'client__name', 'label': 'Cliente'},
                {'value': 'created_at', 'label': 'Fecha de registro'},
                {'value': 'mileage', 'label': 'Kilometraje'},
            ]
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar la lista de equipos")
            context['equipment_list'] = []
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
                'client': client_filter,
                'make': make_filter,
                'status': status_filter,
                'fuel_type': fuel_type_filter,
                'year_from': year_from,
                'year_to': year_to,
                'sort': sort_by,
                'order': sort_order,
            }
            context['client_options'] = [{'value': '', 'label': 'Todos los clientes'}]
            context['status_options'] = [{'value': '', 'label': 'Todos los estados'}]
            context['fuel_type_options'] = [{'value': '', 'label': 'Todos los combustibles'}]
            context['sort_options'] = [{'value': 'equipment_code', 'label': 'Código'}]
        
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


class EquipmentDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced equipment detail view with comprehensive information display."""
    template_name = 'frontend/equipment/equipment_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            
            # Get equipment data
            equipment_data = api_client.get_equipment_detail(equipment_id)
            
            if equipment_data:
                # Add status styling
                status = equipment_data.get('status', '').lower()
                if status == 'active':
                    equipment_data['status_class'] = 'success'
                    equipment_data['status_label'] = 'Activo'
                elif status == 'inactive':
                    equipment_data['status_class'] = 'warning'
                    equipment_data['status_label'] = 'Inactivo'
                elif status == 'sold':
                    equipment_data['status_class'] = 'info'
                    equipment_data['status_label'] = 'Vendido'
                elif status == 'scrapped':
                    equipment_data['status_class'] = 'danger'
                    equipment_data['status_label'] = 'Desechado'
                else:
                    equipment_data['status_class'] = 'secondary'
                    equipment_data['status_label'] = status.title()
                
                # Format fuel type
                fuel_type = equipment_data.get('fuel_type', '')
                fuel_type_labels = {
                    'gasoline': 'Gasolina',
                    'diesel': 'Diésel',
                    'hybrid': 'Híbrido',
                    'electric': 'Eléctrico',
                    'lpg': 'Gas LP',
                    'cng': 'Gas Natural',
                }
                equipment_data['fuel_type_label'] = fuel_type_labels.get(fuel_type, fuel_type.title())
            
            context['equipment'] = equipment_data
            
            # Get equipment's work orders
            try:
                workorders_data = api_client.get_workorders(equipment_id=equipment_id, page_size=50)
                workorders = workorders_data.get('results', [])
                
                # Process work orders for better display
                for workorder in workorders:
                    # Add status styling
                    status = workorder.get('status', '').lower()
                    if status == 'draft':
                        workorder['status_class'] = 'secondary'
                        workorder['status_label'] = 'Borrador'
                    elif status == 'scheduled':
                        workorder['status_class'] = 'info'
                        workorder['status_label'] = 'Programada'
                    elif status == 'in_progress':
                        workorder['status_class'] = 'warning'
                        workorder['status_label'] = 'En Progreso'
                    elif status == 'completed':
                        workorder['status_class'] = 'success'
                        workorder['status_label'] = 'Completada'
                    elif status == 'cancelled':
                        workorder['status_class'] = 'danger'
                        workorder['status_label'] = 'Cancelada'
                    else:
                        workorder['status_class'] = 'secondary'
                        workorder['status_label'] = status.title()
                
                context['workorders'] = workorders
                
                # Calculate work order statistics
                total_workorders = len(workorders)
                completed_workorders = len([wo for wo in workorders if wo.get('status') == 'completed'])
                pending_workorders = len([wo for wo in workorders if wo.get('status') in ['draft', 'scheduled']])
                in_progress_workorders = len([wo for wo in workorders if wo.get('status') == 'in_progress'])
                
                context['workorder_stats'] = {
                    'total': total_workorders,
                    'completed': completed_workorders,
                    'pending': pending_workorders,
                    'in_progress': in_progress_workorders,
                    'completion_rate': (completed_workorders / total_workorders * 100) if total_workorders > 0 else 0
                }
                
            except APIException as wo_error:
                logger.warning(f"Could not load work orders for equipment {equipment_id}: {wo_error}")
                context['workorders'] = []
                context['workorder_stats'] = {
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'in_progress': 0,
                    'completion_rate': 0
                }
            
            # Get maintenance history (if available)
            try:
                # This would be a custom endpoint for maintenance history
                # For now, we'll derive it from completed work orders
                maintenance_history = []
                for wo in workorders[:10]:  # Last 10 work orders
                    if wo.get('status') == 'completed':
                        maintenance_history.append({
                            'date': wo.get('completed_at') or wo.get('created_at'),
                            'description': wo.get('description', 'Mantenimiento completado'),
                            'technician': wo.get('assigned_technician', {}),
                            'total_cost': wo.get('actual_cost', 0)
                        })
                
                context['maintenance_history'] = maintenance_history[:5]  # Show only last 5
                
            except Exception as maintenance_error:
                logger.warning(f"Could not process maintenance history for equipment {equipment_id}: {maintenance_error}")
                context['maintenance_history'] = []
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del equipo")
            context['equipment'] = None
            context['workorders'] = []
            context['workorder_stats'] = {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'in_progress': 0,
                'completion_rate': 0
            }
            context['maintenance_history'] = []
        
        return context


class EquipmentCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced equipment creation view with Django forms and validation."""
    template_name = 'frontend/equipment/equipment_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Registrar Equipo'
        context['form_action'] = 'create'
        
        # Initialize form with GET data if available (for form repopulation)
        form_data = self.request.POST if self.request.method == 'POST' else None
        form = EquipmentForm(form_data)
        
        # Load clients for dropdown
        try:
            api_client = self.get_api_client()
            clients_data = api_client.get_clients(page_size=100)
            client_choices = [('', 'Seleccionar cliente')]
            for client in clients_data.get('results', []):
                # Handle both 'client_id' (primary key) and 'id' (DRF default)
                client_id = client.get('client_id') or client.get('id')
                client_name = client.get('name', 'Sin nombre')
                if client_id:
                    client_choices.append((client_id, client_name))
            form.fields['client_id'].widget.choices = client_choices
        except APIException:
            form.fields['client_id'].widget.choices = [('', 'Error al cargar clientes')]
        
        context['form'] = form
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import EquipmentForm

        form = EquipmentForm(request.POST)
        
        # Load clients for dropdown
        try:
            api_client = self.get_api_client()
            clients_data = api_client.get_clients(page_size=100)
            client_choices = [('', 'Seleccionar cliente')]
            for client in clients_data.get('results', []):
                # Handle both 'id' and 'client_id' keys
                client_id = client.get('id') or client.get('client_id')
                client_name = client.get('name', 'Sin nombre')
                if client_id:
                    client_choices.append((client_id, client_name))
            form.fields['client_id'].widget.choices = client_choices
        except APIException:
            form.fields['client_id'].widget.choices = [('', 'Error al cargar clientes')]

        if form.is_valid():
            # Extract cleaned form data
            equipment_data = {
                'equipment_code': form.cleaned_data['equipment_code'],
                'client_id': form.cleaned_data['client_id'],
                'vin': form.cleaned_data['vin'] or None,
                'license_plate': form.cleaned_data['license_plate'] or None,
                'year': form.cleaned_data['year'],
                'make': form.cleaned_data['make'],
                'model': form.cleaned_data['model'],
                'engine': form.cleaned_data['engine'] or None,
                'transmission': form.cleaned_data['transmission'] or None,
                'color': form.cleaned_data['color'] or None,
                'mileage': form.cleaned_data['mileage'],
                'fuel_type': form.cleaned_data['fuel_type'] or None,
                'status': form.cleaned_data['status'],
                'purchase_date': form.cleaned_data['purchase_date'].isoformat() if form.cleaned_data['purchase_date'] else None,
                'warranty_expiry': form.cleaned_data['warranty_expiry'].isoformat() if form.cleaned_data['warranty_expiry'] else None,
                'notes': form.cleaned_data['notes'] or None,
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.post('equipment/', data=equipment_data)
                
                messages.success(
                    request, 
                    f'Equipo "{equipment_data["equipment_code"]}" registrado exitosamente.'
                )
                return redirect('frontend:equipment_detail', pk=result['id'])
                
            except APIException as e:
                logger.error(f"Equipment creation API error: {e}")
                
                # Handle specific API errors
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
                    form.add_error(None, e.message or "Error al registrar el equipo")
        
        # Form is invalid or API error occurred
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class EquipmentUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced equipment update view with Django forms and validation."""
    template_name = 'frontend/equipment/equipment_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_id = kwargs.get('pk')
        
        context['form_title'] = 'Editar Equipo'
        context['form_action'] = 'update'
        
        try:
            api_client = self.get_api_client()
            equipment_data = api_client.get_equipment_detail(equipment_id)
            context['equipment'] = equipment_data
            
            # Load clients for dropdown
            clients_data = api_client.get_clients(page_size=100)
            client_choices = [('', 'Seleccionar cliente')]
            for client in clients_data.get('results', []):
                # Handle both 'client_id' (primary key) and 'id' (DRF default)
                client_id = client.get('client_id') or client.get('id')
                client_name = client.get('name', 'Sin nombre')
                if client_id:
                    client_choices.append((client_id, client_name))
            
            # Initialize form with equipment data or POST data
            if self.request.method == 'POST':
                form = EquipmentForm(self.request.POST)
                form.fields['client_id'].widget.choices = client_choices
            else:
                # Pre-populate form with existing equipment data
                initial_data = {
                    'equipment_code': equipment_data.get('equipment_code', ''),
                    'client_id': equipment_data.get('client', {}).get('id', ''),
                    'vin': equipment_data.get('vin', ''),
                    'license_plate': equipment_data.get('license_plate', ''),
                    'year': equipment_data.get('year', ''),
                    'make': equipment_data.get('make', ''),
                    'model': equipment_data.get('model', ''),
                    'engine': equipment_data.get('engine', ''),
                    'transmission': equipment_data.get('transmission', ''),
                    'color': equipment_data.get('color', ''),
                    'mileage': equipment_data.get('mileage', ''),
                    'fuel_type': equipment_data.get('fuel_type', ''),
                    'status': equipment_data.get('status', 'active'),
                    'purchase_date': equipment_data.get('purchase_date'),
                    'warranty_expiry': equipment_data.get('warranty_expiry'),
                    'notes': equipment_data.get('notes', ''),
                }
                form = EquipmentForm(initial=initial_data)
                form.fields['client_id'].widget.choices = client_choices
            
            context['form'] = form
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del equipo")
            context['equipment'] = None
            form = EquipmentForm()
            form.fields['client_id'].widget.choices = [('', 'Error al cargar clientes')]
            context['form'] = form
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .forms import EquipmentForm
        
        equipment_id = kwargs.get('pk')
        form = EquipmentForm(request.POST)
        
        # Load clients for dropdown
        try:
            api_client = self.get_api_client()
            clients_data = api_client.get_clients(page_size=100)
            client_choices = [('', 'Seleccionar cliente')]
            for client in clients_data.get('results', []):
                # Handle both 'client_id' (primary key) and 'id' (DRF default)
                client_id = client.get('client_id') or client.get('id')
                client_name = client.get('name', 'Sin nombre')
                if client_id:
                    client_choices.append((client_id, client_name))
            form.fields['client_id'].widget.choices = client_choices
        except APIException:
            form.fields['client_id'].widget.choices = [('', 'Error al cargar clientes')]
        
        if form.is_valid():
            # Extract cleaned form data
            equipment_data = {
                'equipment_code': form.cleaned_data['equipment_code'],
                'client_id': form.cleaned_data['client_id'],
                'vin': form.cleaned_data['vin'] or None,
                'license_plate': form.cleaned_data['license_plate'] or None,
                'year': form.cleaned_data['year'],
                'make': form.cleaned_data['make'],
                'model': form.cleaned_data['model'],
                'engine': form.cleaned_data['engine'] or None,
                'transmission': form.cleaned_data['transmission'] or None,
                'color': form.cleaned_data['color'] or None,
                'mileage': form.cleaned_data['mileage'],
                'fuel_type': form.cleaned_data['fuel_type'] or None,
                'status': form.cleaned_data['status'],
                'purchase_date': form.cleaned_data['purchase_date'].isoformat() if form.cleaned_data['purchase_date'] else None,
                'warranty_expiry': form.cleaned_data['warranty_expiry'].isoformat() if form.cleaned_data['warranty_expiry'] else None,
                'notes': form.cleaned_data['notes'] or None,
            }
            
            try:
                api_client = self.get_api_client()
                result = api_client.put(f'equipment/{equipment_id}/', data=equipment_data)
                
                messages.success(
                    request, 
                    f'Equipo "{equipment_data["equipment_code"]}" actualizado exitosamente.'
                )
                return redirect('frontend:equipment_detail', pk=equipment_id)
                
            except APIException as e:
                logger.error(f"Equipment update API error: {e}")
                
                # Handle specific API errors
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
                    form.add_error(None, e.message or "Error al actualizar el equipo")
        
        # Form is invalid or API error occurred
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class EquipmentDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Equipment deletion view."""
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        equipment_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            
            # Get equipment data for confirmation message
            equipment_data = api_client.get_equipment_detail(equipment_id)
            equipment_code = equipment_data.get('equipment_code', f'ID {equipment_id}')
            
            # Delete the equipment
            api_client.delete(f'equipment/{equipment_id}/')
            
            messages.success(
                request, 
                f'Equipo "{equipment_code}" eliminado exitosamente.'
            )
            
        except APIException as e:
            logger.error(f"Equipment deletion API error: {e}")
            messages.error(
                request, 
                f"Error al eliminar el equipo: {e.message}"
            )
        
        return redirect('frontend:equipment_list')

class MaintenanceCalendarView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Maintenance calendar view with scheduling interface."""
    template_name = 'frontend/maintenance/maintenance_calendar.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date parameters
        year = int(self.request.GET.get('year', datetime.now().year))
        month = int(self.request.GET.get('month', datetime.now().month))
        
        try:
            api_client = self.get_api_client()
            
            # Get maintenance schedules for the month
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date()
            else:
                end_date = datetime(year, month + 1, 1).date()
            
            # Get maintenance data (using work orders with maintenance type)
            maintenance_data = api_client.get('work-orders/', params={
                'scheduled_date_from': start_date.isoformat(),
                'scheduled_date_to': end_date.isoformat(),
                'maintenance_type': True,
                'page_size': 100
            })
            
            context['maintenance_schedules'] = maintenance_data.get('results', [])
            
            # Calendar context
            context['current_year'] = year
            context['current_month'] = month
            context['calendar_date'] = datetime(year, month, 1)
            
            # Generate calendar data
            import calendar
            cal = calendar.monthcalendar(year, month)
            context['calendar_weeks'] = cal
            context['month_name'] = calendar.month_name[month]
            
            # Navigation dates
            if month == 1:
                context['prev_month'] = {'year': year - 1, 'month': 12}
            else:
                context['prev_month'] = {'year': year, 'month': month - 1}
            
            if month == 12:
                context['next_month'] = {'year': year + 1, 'month': 1}
            else:
                context['next_month'] = {'year': year, 'month': month + 1}
            
            # Group maintenance by date
            maintenance_by_date = {}
            for maintenance in context['maintenance_schedules']:
                scheduled_date = maintenance.get('scheduled_date')
                if scheduled_date:
                    date_key = scheduled_date[:10]  # YYYY-MM-DD
                    if date_key not in maintenance_by_date:
                        maintenance_by_date[date_key] = []
                    maintenance_by_date[date_key].append(maintenance)
            
            context['maintenance_by_date'] = maintenance_by_date
            
        except APIException as e:
            logger.error(f"Maintenance calendar API error: {e}")
            self.handle_api_error(e, "Error al cargar el calendario de mantenimiento")
            context['maintenance_schedules'] = []
            context['maintenance_by_date'] = {}
            context['current_year'] = year
            context['current_month'] = month
            context['calendar_date'] = datetime(year, month, 1)
            context['calendar_weeks'] = []
            context['month_name'] = calendar.month_name[month]
        
        return context


class MaintenanceListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Maintenance list view with advanced filtering."""
    template_name = 'frontend/maintenance/maintenance_list.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search and filter parameters
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        equipment_filter = self.request.GET.get('equipment', '')
        maintenance_type_filter = self.request.GET.get('maintenance_type', '')
        status_filter = self.request.GET.get('status', '')
        priority_filter = self.request.GET.get('priority', '')
        technician_filter = self.request.GET.get('technician', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        sort_by = self.request.GET.get('sort', 'scheduled_date')
        sort_order = self.request.GET.get('order', 'asc')
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if equipment_filter:
                filters['equipment'] = equipment_filter
            if maintenance_type_filter:
                filters['maintenance_type'] = maintenance_type_filter
            if status_filter:
                filters['status'] = status_filter
            if priority_filter:
                filters['priority'] = priority_filter
            if technician_filter:
                filters['technician'] = technician_filter
            if date_from:
                filters['scheduled_date_from'] = date_from
            if date_to:
                filters['scheduled_date_to'] = date_to
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"
            
            # Get maintenance data (using work orders with maintenance flag)
            filters['maintenance_type'] = True
            maintenance_data = api_client.get('work-orders/', params={
                'page': page,
                'page_size': self.paginate_by,
                **filters
            })
            
            context['maintenance_list'] = maintenance_data.get('results', [])
            
            # Enhanced pagination context
            total_count = maintenance_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by
            
            context['pagination'] = {
                'count': total_count,
                'next': maintenance_data.get('next'),
                'previous': maintenance_data.get('previous'),
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
                'equipment': equipment_filter,
                'maintenance_type': maintenance_type_filter,
                'status': status_filter,
                'priority': priority_filter,
                'technician': technician_filter,
                'date_from': date_from,
                'date_to': date_to,
                'sort': sort_by,
                'order': sort_order,
            }
            
            # Get filter options
            self._load_filter_options(context, api_client)
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar la lista de mantenimientos")
            context['maintenance_list'] = []
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
                'equipment': equipment_filter,
                'maintenance_type': maintenance_type_filter,
                'status': status_filter,
                'priority': priority_filter,
                'technician': technician_filter,
                'date_from': date_from,
                'date_to': date_to,
                'sort': sort_by,
                'order': sort_order,
            }
            self._load_empty_filter_options(context)
        
        return context
    
    def _load_filter_options(self, context, api_client):
        """Load filter dropdown options."""
        try:
            # Equipment options
            equipment_data = api_client.get_equipment(page_size=100)
            context['equipment_options'] = [{'value': '', 'label': 'Todos los equipos'}]
            for equipment in equipment_data.get('results', []):
                context['equipment_options'].append({
                    'value': equipment['id'],
                    'label': f"{equipment['equipment_code']} - {equipment['make']} {equipment['model']}"
                })
            
            # Technician options
            technicians_data = api_client.get_technicians(page_size=100)
            context['technician_options'] = [{'value': '', 'label': 'Todos los técnicos'}]
            for technician in technicians_data.get('results', []):
                context['technician_options'].append({
                    'value': technician['id'],
                    'label': f"{technician['first_name']} {technician['last_name']}"
                })
        except APIException:
            self._load_empty_filter_options(context)
    
    def _load_empty_filter_options(self, context):
        """Load empty filter options on error."""
        context['equipment_options'] = [{'value': '', 'label': 'Todos los equipos'}]
        context['technician_options'] = [{'value': '', 'label': 'Todos los técnicos'}]
    
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


class MaintenanceCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Maintenance scheduling creation view."""
    template_name = 'frontend/maintenance/maintenance_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Programar Mantenimiento'
        context['form_action'] = 'create'
        
        # Initialize form
        form_data = self.request.POST if self.request.method == 'POST' else None
        form = MaintenanceScheduleForm(form_data)
        
        # Load dropdown options
        self._load_form_options(form)
        
        context['form'] = form
        return context
    
    def _load_form_options(self, form):
        """Load dropdown options for the form."""
        try:
            api_client = self.get_api_client()
            
            # Equipment options
            equipment_data = api_client.get_equipment(page_size=100)
            equipment_choices = [('', 'Seleccionar equipo')]
            for equipment in equipment_data.get('results', []):
                equipment_choices.append((
                    equipment['id'],
                    f"{equipment['equipment_code']} - {equipment['make']} {equipment['model']}"
                ))
            form.fields['equipment_id'].widget.choices = equipment_choices
            
            # Technician options
            technicians_data = api_client.get_technicians(page_size=100)
            technician_choices = [('', 'Sin asignar')]
            for technician in technicians_data.get('results', []):
                technician_choices.append((
                    technician['id'],
                    f"{technician['first_name']} {technician['last_name']}"
                ))
            form.fields['assigned_technician_id'].widget.choices = technician_choices
            
        except APIException:
            form.fields['equipment_id'].widget.choices = [('', 'Error al cargar equipos')]
            form.fields['assigned_technician_id'].widget.choices = [('', 'Error al cargar técnicos')]
    
    def post(self, request, *args, **kwargs):
        from .forms import MaintenanceScheduleForm
        
        form = MaintenanceScheduleForm(request.POST)
        self._load_form_options(form)
        
        if form.is_valid():
            # Convert maintenance schedule to work order format
            maintenance_data = {
                'equipment_id': form.cleaned_data['equipment_id'],
                'description': f"[{form.cleaned_data['maintenance_type'].upper()}] {form.cleaned_data['title']}\n\n{form.cleaned_data['description']}",
                'priority': form.cleaned_data['priority'],
                'status': 'scheduled',
                'assigned_technician_id': form.cleaned_data['assigned_technician_id'],
                'scheduled_date': form.cleaned_data['scheduled_date'].isoformat(),
                'estimated_hours': float(form.cleaned_data['estimated_duration']),
                'maintenance_type': form.cleaned_data['maintenance_type'],
                'notes': form.cleaned_data['notes'] or '',
            }
            
            # Add time if provided
            if form.cleaned_data['scheduled_time']:
                scheduled_datetime = datetime.combine(
                    form.cleaned_data['scheduled_date'],
                    form.cleaned_data['scheduled_time']
                )
                maintenance_data['scheduled_date'] = scheduled_datetime.isoformat()
            
            try:
                api_client = self.get_api_client()
                result = api_client.post('work-orders/', data=maintenance_data)
                
                messages.success(
                    request,
                    f'Mantenimiento "{form.cleaned_data["title"]}" programado exitosamente.'
                )
                return redirect('frontend:maintenance_detail', pk=result['id'])
                
            except APIException as e:
                logger.error(f"Maintenance creation API error: {e}")
                
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
                    form.add_error(None, e.message or "Error al programar el mantenimiento")
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class MaintenanceDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Maintenance detail view."""
    template_name = 'frontend/maintenance/maintenance_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            
            # Get maintenance data (work order)
            maintenance_data = api_client.get_workorder(maintenance_id)
            
            if maintenance_data:
                # Add status styling
                status = maintenance_data.get('status', '').lower()
                if status == 'scheduled':
                    maintenance_data['status_class'] = 'info'
                    maintenance_data['status_label'] = 'Programado'
                elif status == 'in_progress':
                    maintenance_data['status_class'] = 'warning'
                    maintenance_data['status_label'] = 'En Progreso'
                elif status == 'completed':
                    maintenance_data['status_class'] = 'success'
                    maintenance_data['status_label'] = 'Completado'
                elif status == 'cancelled':
                    maintenance_data['status_class'] = 'danger'
                    maintenance_data['status_label'] = 'Cancelado'
                else:
                    maintenance_data['status_class'] = 'secondary'
                    maintenance_data['status_label'] = status.title()
                
                # Check if overdue
                if status == 'scheduled' and maintenance_data.get('scheduled_date'):
                    from datetime import datetime
                    scheduled_date = datetime.fromisoformat(maintenance_data['scheduled_date'].replace('Z', '+00:00'))
                    if scheduled_date.date() < datetime.now().date():
                        maintenance_data['is_overdue'] = True
                        maintenance_data['status_class'] = 'danger'
                        maintenance_data['status_label'] = 'Vencido'
            
            context['maintenance'] = maintenance_data
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del mantenimiento")
            context['maintenance'] = None
        
        return context


# AJAX Search Views
class SearchClientsView(LoginRequiredMixin, APIClientMixin, View):
    """AJAX endpoint for client search."""
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        
        try:
            api_client = self.get_api_client()
            clients_data = api_client.search('clients/', query, limit=10)
            
            results = []
            for client in clients_data.get('results', []):
                client_id = client.get('client_id') or client.get('id')
                if client_id:
                    results.append({
                        'id': client_id,
                        'text': f"{client.get('name', '')} - {client.get('email', '')}"
                    })
            
            return JsonResponse({'results': results})
            
        except APIException as e:
            return JsonResponse({'results': [], 'error': str(e)})


class SearchEquipmentView(LoginRequiredMixin, APIClientMixin, View):
    """AJAX endpoint for equipment search."""

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')

        try:
            api_client = self.get_api_client()
            equipment_data = api_client.search('equipment/', query, limit=10)

            results = []
            for equipment in equipment_data.get('results', []):
                results.append({
                    'id': equipment['id'],
                    'text': f"{equipment.get('brand', '')} {equipment.get('model', '')} - {equipment.get('serial_number', '')}"
                })

            return JsonResponse({'results': results})

        except APIException as e:
            return JsonResponse({'results': [], 'error': str(e)})

class DebugAuthView(LoginRequiredMixin, APIClientMixin, View):
    """Debug endpoint for authentication status."""

    def get(self, request, *args, **kwargs):
        auth_service = AuthenticationService(request)
        api_client = self.get_api_client()

        debug_info = {
            'django_authenticated': request.user.is_authenticated,
            'user': {
                'username': request.user.username if request.user.is_authenticated else None,
                'email': request.user.email if request.user.is_authenticated else None,
            },
            'session_keys': list(request.session.keys()),
            'auth_token_present': bool(request.session.get('auth_token')),
            'refresh_token_present': bool(request.session.get('refresh_token')),
            'token_timestamp': request.session.get('token_timestamp'),
            'auth_service_status': auth_service.get_session_info(),
            'api_client_base_url': api_client.base_url,
            'api_health_check': api_client.health_check(),
        }

        return JsonResponse(debug_info)

class DebugAuthView(LoginRequiredMixin, View):
    """Debug endpoint to check authentication status."""
    
    def get(self, request, *args, **kwargs):
        from .services import AuthenticationService
        
        auth_service = AuthenticationService(request)
        
        debug_info = {
            'user': {
                'username': request.user.username if request.user.is_authenticated else None,
                'is_authenticated': request.user.is_authenticated,
                'is_staff': request.user.is_staff if request.user.is_authenticated else False,
                'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
            },
            'session': {
                'session_key': request.session.session_key,
                'has_auth_token': bool(request.session.get('auth_token')),
                'has_refresh_token': bool(request.session.get('refresh_token')),
                'token_timestamp': request.session.get('token_timestamp'),
                'user_data': request.session.get('user_data'),
            },
            'api_client': {},
        }
        
        # Test API client
        try:
            api_client = ForgeAPIClient(request=request)
            auth_header = api_client.session.headers.get('Authorization')
            debug_info['api_client'] = {
                'has_auth_header': bool(auth_header),
                'auth_header_preview': auth_header[:50] + '...' if auth_header else None,
                'base_url': api_client.base_url,
            }
            
            # Test API call
            try:
                dashboard_data = api_client.get('dashboard/')
                debug_info['api_test'] = {
                    'dashboard_call': 'success',
                    'data_keys': list(dashboard_data.keys())[:5],
                }
            except APIException as e:
                debug_info['api_test'] = {
                    'dashboard_call': 'failed',
                    'error': str(e),
                    'status_code': getattr(e, 'status_code', None),
                }
                
        except Exception as e:
            debug_info['api_client']['error'] = str(e)
        
        return JsonResponse(debug_info, indent=2)


# Maintenance Views

class MaintenanceListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for listing maintenance tasks with search and filtering."""
    template_name = 'frontend/maintenance/maintenance_list.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()
        
        # Initialize search form
        search_form = MaintenanceSearchForm(self.request.GET or None)
        context['search_form'] = search_form
        
        try:
            # Get maintenance tasks with filters
            params = {}
            if search_form.is_valid():
                if search_form.cleaned_data.get('search'):
                    params['search'] = search_form.cleaned_data['search']
                if search_form.cleaned_data.get('equipment_id'):
                    params['equipment_id'] = search_form.cleaned_data['equipment_id']
                if search_form.cleaned_data.get('maintenance_type'):
                    params['maintenance_type'] = search_form.cleaned_data['maintenance_type']
                if search_form.cleaned_data.get('status'):
                    params['status'] = search_form.cleaned_data['status']
                if search_form.cleaned_data.get('priority'):
                    params['priority'] = search_form.cleaned_data['priority']
                if search_form.cleaned_data.get('date_from'):
                    params['date_from'] = search_form.cleaned_data['date_from'].isoformat()
                if search_form.cleaned_data.get('date_to'):
                    params['date_to'] = search_form.cleaned_data['date_to'].isoformat()

            # Get page parameter
            page = self.request.GET.get('page', 1)
            params['page'] = page

            maintenance_data = api_client.get_maintenance_tasks(params)
            context['maintenance_tasks'] = maintenance_data.get('results', [])
            context['pagination'] = {
                'count': maintenance_data.get('count', 0),
                'next': maintenance_data.get('next'),
                'previous': maintenance_data.get('previous'),
                'current_page': int(page),
                'total_pages': (maintenance_data.get('count', 0) + 19) // 20  # Assuming 20 per page
            }

            # Get equipment list for filter dropdown
            equipment_data = api_client.get_equipment({'page_size': 1000})
            context['equipment_list'] = equipment_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar las tareas de mantenimiento")
            context['maintenance_tasks'] = []
            context['equipment_list'] = []
            context['pagination'] = {'count': 0, 'current_page': 1, 'total_pages': 0}

        return context


class MaintenanceDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for displaying maintenance task details."""
    template_name = 'frontend/maintenance/maintenance_detail.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        maintenance_id = kwargs.get('maintenance_id')
        api_client = self.get_api_client()

        try:
            maintenance = api_client.get_maintenance_task(maintenance_id)
            context['maintenance'] = maintenance

            # Get equipment details
            if maintenance.get('equipment_id'):
                equipment = api_client.get_equipment_detail(maintenance['equipment_id'])
                context['equipment'] = equipment

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los detalles del mantenimiento")
            return redirect('frontend:maintenance_list')

        return context


class MaintenanceCreateView(LoginRequiredMixin, APIClientMixin, View):
    """View for creating new maintenance tasks."""
    template_name = 'frontend/maintenance/maintenance_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request):
        form = MaintenanceForm()
        api_client = self.get_api_client()
        
        try:
            # Get equipment list for dropdown
            equipment_data = api_client.get_equipment({'page_size': 1000})
            equipment_choices = [(eq['id'], f"{eq['equipment_code']} - {eq['make']} {eq['model']}") 
                               for eq in equipment_data.get('results', [])]
            form.fields['equipment_id'].widget.choices = [('', 'Seleccionar equipo')] + equipment_choices
        except APIException as e:
            self.handle_api_error(e, "Error al cargar la lista de equipos")
            form.fields['equipment_id'].widget.choices = [('', 'Seleccionar equipo')]

        return render(request, self.template_name, {
            'form': form,
            'title': 'Crear Tarea de Mantenimiento',
            'action': 'create'
        })

    def post(self, request):
        form = MaintenanceForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                maintenance_data = {
                    'equipment_id': form.cleaned_data['equipment_id'],
                    'maintenance_type': form.cleaned_data['maintenance_type'],
                    'title': form.cleaned_data['title'],
                    'description': form.cleaned_data['description'],
                    'scheduled_date': form.cleaned_data['scheduled_date'].isoformat(),
                    'estimated_duration': form.cleaned_data['estimated_duration'],
                    'priority': form.cleaned_data['priority'],
                    'assigned_technician': form.cleaned_data['assigned_technician'],
                    'notes': form.cleaned_data['notes'],
                    'status': 'scheduled'
                }

                maintenance = api_client.create_maintenance_task(maintenance_data)
                messages.success(request, f"Tarea de mantenimiento '{maintenance['title']}' creada exitosamente.")
                return redirect('frontend:maintenance_detail', maintenance_id=maintenance['id'])

            except APIException as e:
                self.handle_api_error(e, "Error al crear la tarea de mantenimiento")

        # If form is invalid or API error, reload equipment choices
        try:
            equipment_data = api_client.get_equipment({'page_size': 1000})
            equipment_choices = [(eq['id'], f"{eq['equipment_code']} - {eq['make']} {eq['model']}") 
                               for eq in equipment_data.get('results', [])]
            form.fields['equipment_id'].widget.choices = [('', 'Seleccionar equipo')] + equipment_choices
        except APIException:
            form.fields['equipment_id'].widget.choices = [('', 'Seleccionar equipo')]

        return render(request, self.template_name, {
            'form': form,
            'title': 'Crear Tarea de Mantenimiento',
            'action': 'create'
        })


class MaintenanceUpdateView(LoginRequiredMixin, APIClientMixin, View):
    """View for updating maintenance tasks."""
    template_name = 'frontend/maintenance/maintenance_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request, maintenance_id):
        api_client = self.get_api_client()

        try:
            maintenance = api_client.get_maintenance_task(maintenance_id)
            
            # Convert datetime string to datetime object for form
            if maintenance.get('scheduled_date'):
                from datetime import datetime
                maintenance['scheduled_date'] = datetime.fromisoformat(
                    maintenance['scheduled_date'].replace('Z', '+00:00')
                ).replace(tzinfo=None)

            form = MaintenanceForm(initial=maintenance)
            
            # Get equipment list for dropdown
            equipment_data = api_client.get_equipment({'page_size': 1000})
            equipment_choices = [(eq['id'], f"{eq['equipment_code']} - {eq['make']} {eq['model']}") 
                               for eq in equipment_data.get('results', [])]
            form.fields['equipment_id'].widget.choices = [('', 'Seleccionar equipo')] + equipment_choices

        except APIException as e:
            self.handle_api_error(e, "Error al cargar la tarea de mantenimiento")
            return redirect('frontend:maintenance_list')

        return render(request, self.template_name, {
            'form': form,
            'maintenance': maintenance,
            'title': f'Editar Mantenimiento: {maintenance["title"]}',
            'action': 'update'
        })

    def post(self, request, maintenance_id):
        form = MaintenanceForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                maintenance_data = {
                    'equipment_id': form.cleaned_data['equipment_id'],
                    'maintenance_type': form.cleaned_data['maintenance_type'],
                    'title': form.cleaned_data['title'],
                    'description': form.cleaned_data['description'],
                    'scheduled_date': form.cleaned_data['scheduled_date'].isoformat(),
                    'estimated_duration': form.cleaned_data['estimated_duration'],
                    'priority': form.cleaned_data['priority'],
                    'assigned_technician': form.cleaned_data['assigned_technician'],
                    'notes': form.cleaned_data['notes']
                }

                maintenance = api_client.update_maintenance_task(maintenance_id, maintenance_data)
                messages.success(request, f"Tarea de mantenimiento '{maintenance['title']}' actualizada exitosamente.")
                return redirect('frontend:maintenance_detail', maintenance_id=maintenance['id'])

            except APIException as e:
                self.handle_api_error(e, "Error al actualizar la tarea de mantenimiento")

        # If form is invalid or API error, reload equipment choices and maintenance data
        try:
            maintenance = api_client.get_maintenance_task(maintenance_id)
            equipment_data = api_client.get_equipment({'page_size': 1000})
            equipment_choices = [(eq['id'], f"{eq['equipment_code']} - {eq['make']} {eq['model']}") 
                               for eq in equipment_data.get('results', [])]
            form.fields['equipment_id'].widget.choices = [('', 'Seleccionar equipo')] + equipment_choices
        except APIException:
            maintenance = {}
            form.fields['equipment_id'].widget.choices = [('', 'Seleccionar equipo')]

        return render(request, self.template_name, {
            'form': form,
            'maintenance': maintenance,
            'title': f'Editar Mantenimiento: {maintenance.get("title", "")}',
            'action': 'update'
        })


class MaintenanceDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """View for deleting maintenance tasks."""
    login_url = reverse_lazy('frontend:login')

    def post(self, request, maintenance_id):
        api_client = self.get_api_client()

        try:
            maintenance = api_client.get_maintenance_task(maintenance_id)
            api_client.delete_maintenance_task(maintenance_id)
            messages.success(request, f"Tarea de mantenimiento '{maintenance['title']}' eliminada exitosamente.")
        except APIException as e:
            self.handle_api_error(e, "Error al eliminar la tarea de mantenimiento")

        return redirect('frontend:maintenance_list')


class MaintenanceCalendarView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for displaying maintenance tasks in calendar format."""
    template_name = 'frontend/maintenance/maintenance_calendar.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()

        try:
            # Get maintenance tasks for calendar
            params = {'page_size': 1000}  # Get all for calendar view
            maintenance_data = api_client.get_maintenance_tasks(params)
            
            # Format maintenance tasks for calendar
            calendar_events = []
            for task in maintenance_data.get('results', []):
                calendar_events.append({
                    'id': task['id'],
                    'title': task['title'],
                    'start': task['scheduled_date'],
                    'backgroundColor': self._get_priority_color(task.get('priority', 'medium')),
                    'borderColor': self._get_priority_color(task.get('priority', 'medium')),
                    'url': f"/maintenance/{task['id']}/",
                    'extendedProps': {
                        'maintenance_type': task.get('maintenance_type'),
                        'priority': task.get('priority'),
                        'status': task.get('status'),
                        'equipment': task.get('equipment_code', 'N/A')
                    }
                })
            
            context['calendar_events'] = calendar_events

        except APIException as e:
            self.handle_api_error(e, "Error al cargar el calendario de mantenimiento")
            context['calendar_events'] = []

        return context

    def _get_priority_color(self, priority):
        """Get color based on maintenance priority."""
        colors = {
            'low': '#28a745',      # Green
            'medium': '#ffc107',   # Yellow
            'high': '#fd7e14',     # Orange
            'critical': '#dc3545'  # Red
        }
        return colors.get(priority, '#6c757d')  # Default gray


class MaintenanceStatusUpdateView(LoginRequiredMixin, APIClientMixin, View):
    """View for updating maintenance task status."""
    login_url = reverse_lazy('frontend:login')

    def post(self, request, maintenance_id):
        api_client = self.get_api_client()
        new_status = request.POST.get('status')

        if not new_status:
            messages.error(request, "Estado no especificado.")
            return redirect('frontend:maintenance_detail', maintenance_id=maintenance_id)

        try:
            maintenance_data = {'status': new_status}
            
            # If completing maintenance, add completion date
            if new_status == 'completed':
                maintenance_data['completed_date'] = datetime.now().isoformat()

            maintenance = api_client.update_maintenance_task(maintenance_id, maintenance_data)
            
            status_names = {
                'scheduled': 'Programado',
                'in_progress': 'En Progreso',
                'completed': 'Completado',
                'cancelled': 'Cancelado'
            }
            
            messages.success(request, f"Estado actualizado a '{status_names.get(new_status, new_status)}'.")
            
        except APIException as e:
            self.handle_api_error(e, "Error al actualizar el estado del mantenimiento")

        return redirect('frontend:maintenance_detail', maintenance_id=maintenance_id)


# Stock Management Views

class StockDashboardView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for stock management dashboard with KPIs and alerts."""
    template_name = 'frontend/inventory/stock_dashboard.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()

        try:
            # Get dashboard data
            dashboard_data = api_client.get_stock_dashboard()
            context['dashboard_data'] = dashboard_data

            # Get stock alerts
            alerts_data = api_client.get_stock_alerts()
            context['stock_alerts'] = alerts_data.get('results', [])

            # Get recent stock movements
            movements_data = api_client.get_stock_movements({'page_size': 10})
            context['recent_movements'] = movements_data.get('results', [])

            # Get warehouses for quick access
            warehouses_data = api_client.get_warehouses({'page_size': 100})
            context['warehouses'] = warehouses_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar el dashboard de stock")
            context['dashboard_data'] = {}
            context['stock_alerts'] = []
            context['recent_movements'] = []
            context['warehouses'] = []

        return context


class StockListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced view for listing stock levels with search and filtering."""
    template_name = 'frontend/inventory/stock_list.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()
        
        # Initialize search form
        search_form = StockSearchForm(self.request.GET or None)
        context['search_form'] = search_form
        
        try:
            # Get stock levels with filters
            params = {}
            if search_form.is_valid():
                if search_form.cleaned_data.get('search'):
                    params['search'] = search_form.cleaned_data['search']
                if search_form.cleaned_data.get('category'):
                    params['category'] = search_form.cleaned_data['category']
                if search_form.cleaned_data.get('warehouse_id'):
                    params['warehouse_id'] = search_form.cleaned_data['warehouse_id']
                if search_form.cleaned_data.get('status'):
                    params['status'] = search_form.cleaned_data['status']
                if search_form.cleaned_data.get('min_quantity'):
                    params['min_quantity'] = search_form.cleaned_data['min_quantity']
                if search_form.cleaned_data.get('max_quantity'):
                    params['max_quantity'] = search_form.cleaned_data['max_quantity']

            # Get page parameter
            page = self.request.GET.get('page', 1)
            params['page'] = page

            stock_data = api_client.get_stock_levels(params)
            context['stock_levels'] = stock_data.get('results', [])
            context['pagination'] = {
                'count': stock_data.get('count', 0),
                'next': stock_data.get('next'),
                'previous': stock_data.get('previous'),
                'current_page': int(page),
                'total_pages': (stock_data.get('count', 0) + 19) // 20
            }

            # Get warehouses for filter dropdown
            warehouses_data = api_client.get_warehouses({'page_size': 100})
            context['warehouses'] = warehouses_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los niveles de stock")
            context['stock_levels'] = []
            context['warehouses'] = []
            context['pagination'] = {'count': 0, 'current_page': 1, 'total_pages': 0}

        return context


class StockMovementListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for listing stock movements with filtering."""
    template_name = 'frontend/inventory/stock_movements.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()

        try:
            # Get movements with filters
            params = {}
            
            # Date range filters
            date_from = self.request.GET.get('date_from')
            date_to = self.request.GET.get('date_to')
            if date_from:
                params['date_from'] = date_from
            if date_to:
                params['date_to'] = date_to
                
            # Other filters
            movement_type = self.request.GET.get('movement_type')
            warehouse_id = self.request.GET.get('warehouse_id')
            product_search = self.request.GET.get('product_search')
            
            if movement_type:
                params['movement_type'] = movement_type
            if warehouse_id:
                params['warehouse_id'] = warehouse_id
            if product_search:
                params['product_search'] = product_search

            # Pagination
            page = self.request.GET.get('page', 1)
            params['page'] = page

            movements_data = api_client.get_stock_movements(params)
            context['movements'] = movements_data.get('results', [])
            context['pagination'] = {
                'count': movements_data.get('count', 0),
                'next': movements_data.get('next'),
                'previous': movements_data.get('previous'),
                'current_page': int(page),
                'total_pages': (movements_data.get('count', 0) + 19) // 20
            }

            # Get warehouses for filter
            warehouses_data = api_client.get_warehouses({'page_size': 100})
            context['warehouses'] = warehouses_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los movimientos de stock")
            context['movements'] = []
            context['warehouses'] = []
            context['pagination'] = {'count': 0, 'current_page': 1, 'total_pages': 0}

        return context


class StockMovementCreateView(LoginRequiredMixin, APIClientMixin, View):
    """View for creating stock movements."""
    template_name = 'frontend/inventory/stock_movement_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request):
        form = StockMovementForm()
        api_client = self.get_api_client()
        
        try:
            # Get products for dropdown
            products_data = api_client.get_products({'page_size': 1000})
            product_choices = [(p['id'], f"{p['code']} - {p['name']}") 
                             for p in products_data.get('results', [])]
            form.fields['product_id'].widget.choices = [('', 'Seleccionar producto')] + product_choices
            
            # Get warehouses for dropdown
            warehouses_data = api_client.get_warehouses({'page_size': 100})
            warehouse_choices = [(w['id'], f"{w['code']} - {w['name']}") 
                               for w in warehouses_data.get('results', [])]
            form.fields['warehouse_id'].widget.choices = [('', 'Seleccionar almacén')] + warehouse_choices
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del formulario")
            form.fields['product_id'].widget.choices = [('', 'Seleccionar producto')]
            form.fields['warehouse_id'].widget.choices = [('', 'Seleccionar almacén')]

        return render(request, self.template_name, {
            'form': form,
            'title': 'Registrar Movimiento de Stock',
            'action': 'create'
        })

    def post(self, request):
        form = StockMovementForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                movement_data = {
                    'product_id': form.cleaned_data['product_id'],
                    'warehouse_id': form.cleaned_data['warehouse_id'],
                    'movement_type': form.cleaned_data['movement_type'],
                    'quantity': float(form.cleaned_data['quantity']),
                    'unit_cost': float(form.cleaned_data['unit_cost']) if form.cleaned_data['unit_cost'] else None,
                    'reason': form.cleaned_data['reason'],
                    'reference_document': form.cleaned_data['reference_document'],
                    'notes': form.cleaned_data['notes']
                }

                movement = api_client.create_stock_movement(movement_data)
                messages.success(request, f"Movimiento de stock registrado exitosamente.")
                return redirect('frontend:stock_movements')

            except APIException as e:
                self.handle_api_error(e, "Error al registrar el movimiento de stock")

        # If form is invalid or API error, reload choices
        try:
            products_data = api_client.get_products({'page_size': 1000})
            product_choices = [(p['id'], f"{p['code']} - {p['name']}") 
                             for p in products_data.get('results', [])]
            form.fields['product_id'].widget.choices = [('', 'Seleccionar producto')] + product_choices
            
            warehouses_data = api_client.get_warehouses({'page_size': 100})
            warehouse_choices = [(w['id'], f"{w['code']} - {w['name']}") 
                               for w in warehouses_data.get('results', [])]
            form.fields['warehouse_id'].widget.choices = [('', 'Seleccionar almacén')] + warehouse_choices
        except APIException:
            form.fields['product_id'].widget.choices = [('', 'Seleccionar producto')]
            form.fields['warehouse_id'].widget.choices = [('', 'Seleccionar almacén')]

        return render(request, self.template_name, {
            'form': form,
            'title': 'Registrar Movimiento de Stock',
            'action': 'create'
        })


# Warehouse Management Views

class WarehouseListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for listing warehouses with search and filtering."""
    template_name = 'frontend/inventory/warehouse_list.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()
        
        # Initialize search form
        search_form = WarehouseSearchForm(self.request.GET or None)
        context['search_form'] = search_form
        
        try:
            # Get warehouses with filters
            params = {}
            if search_form.is_valid():
                if search_form.cleaned_data.get('search'):
                    params['search'] = search_form.cleaned_data['search']
                if search_form.cleaned_data.get('is_active'):
                    params['is_active'] = search_form.cleaned_data['is_active']

            # Get page parameter
            page = self.request.GET.get('page', 1)
            params['page'] = page

            warehouses_data = api_client.get_warehouses(params)
            context['warehouses'] = warehouses_data.get('results', [])
            context['pagination'] = {
                'count': warehouses_data.get('count', 0),
                'next': warehouses_data.get('next'),
                'previous': warehouses_data.get('previous'),
                'current_page': int(page),
                'total_pages': (warehouses_data.get('count', 0) + 19) // 20
            }

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los almacenes")
            context['warehouses'] = []
            context['pagination'] = {'count': 0, 'current_page': 1, 'total_pages': 0}

        return context


class WarehouseDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for displaying warehouse details and stock."""
    template_name = 'frontend/inventory/warehouse_detail.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse_id = kwargs.get('warehouse_id')
        api_client = self.get_api_client()

        try:
            warehouse = api_client.get_warehouse(warehouse_id)
            context['warehouse'] = warehouse

            # Get warehouse stock
            stock_data = api_client.get_warehouse_stock(warehouse_id, {'page_size': 100})
            context['warehouse_stock'] = stock_data.get('results', [])

            # Get recent movements for this warehouse
            movements_data = api_client.get_stock_movements({
                'warehouse_id': warehouse_id,
                'page_size': 20
            })
            context['recent_movements'] = movements_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los detalles del almacén")
            return redirect('frontend:warehouse_list')

        return context


class WarehouseCreateView(LoginRequiredMixin, APIClientMixin, View):
    """View for creating warehouses."""
    template_name = 'frontend/inventory/warehouse_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request):
        form = WarehouseForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Crear Almacén',
            'action': 'create'
        })

    def post(self, request):
        form = WarehouseForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                warehouse_data = {
                    'code': form.cleaned_data['code'],
                    'name': form.cleaned_data['name'],
                    'description': form.cleaned_data['description'],
                    'location': form.cleaned_data['location'],
                    'manager_name': form.cleaned_data['manager_name'],
                    'is_active': form.cleaned_data['is_active']
                }

                warehouse = api_client.create_warehouse(warehouse_data)
                messages.success(request, f"Almacén '{warehouse['name']}' creado exitosamente.")
                return redirect('frontend:warehouse_detail', warehouse_id=warehouse['id'])

            except APIException as e:
                self.handle_api_error(e, "Error al crear el almacén")

        return render(request, self.template_name, {
            'form': form,
            'title': 'Crear Almacén',
            'action': 'create'
        })


class WarehouseUpdateView(LoginRequiredMixin, APIClientMixin, View):
    """View for updating warehouses."""
    template_name = 'frontend/inventory/warehouse_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request, warehouse_id):
        api_client = self.get_api_client()

        try:
            warehouse = api_client.get_warehouse(warehouse_id)
            form = WarehouseForm(initial=warehouse)

        except APIException as e:
            self.handle_api_error(e, "Error al cargar el almacén")
            return redirect('frontend:warehouse_list')

        return render(request, self.template_name, {
            'form': form,
            'warehouse': warehouse,
            'title': f'Editar Almacén: {warehouse["name"]}',
            'action': 'update'
        })

    def post(self, request, warehouse_id):
        form = WarehouseForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                warehouse_data = {
                    'code': form.cleaned_data['code'],
                    'name': form.cleaned_data['name'],
                    'description': form.cleaned_data['description'],
                    'location': form.cleaned_data['location'],
                    'manager_name': form.cleaned_data['manager_name'],
                    'is_active': form.cleaned_data['is_active']
                }

                warehouse = api_client.update_warehouse(warehouse_id, warehouse_data)
                messages.success(request, f"Almacén '{warehouse['name']}' actualizado exitosamente.")
                return redirect('frontend:warehouse_detail', warehouse_id=warehouse['id'])

            except APIException as e:
                self.handle_api_error(e, "Error al actualizar el almacén")

        # If form is invalid or API error, reload warehouse data
        try:
            warehouse = api_client.get_warehouse(warehouse_id)
        except APIException:
            warehouse = {}

        return render(request, self.template_name, {
            'form': form,
            'warehouse': warehouse,
            'title': f'Editar Almacén: {warehouse.get("name", "")}',
            'action': 'update'
        })


class WarehouseDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """View for deleting warehouses."""
    login_url = reverse_lazy('frontend:login')

    def post(self, request, warehouse_id):
        api_client = self.get_api_client()

        try:
            warehouse = api_client.get_warehouse(warehouse_id)
            api_client.delete_warehouse(warehouse_id)
            messages.success(request, f"Almacén '{warehouse['name']}' eliminado exitosamente.")
        except APIException as e:
            self.handle_api_error(e, "Error al eliminar el almacén")

        return redirect('frontend:warehouse_list')


class InventoryReportsView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for inventory reports."""
    template_name = 'frontend/inventory/inventory_reports.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()
        
        report_type = self.request.GET.get('report_type', 'valuation')
        
        try:
            # Get report data
            report_data = api_client.get_inventory_reports(report_type, self.request.GET.dict())
            context['report_data'] = report_data
            context['report_type'] = report_type
            
            # Get warehouses for filtering
            warehouses_data = api_client.get_warehouses({'page_size': 100})
            context['warehouses'] = warehouses_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al generar el reporte")
            context['report_data'] = {}
            context['warehouses'] = []

        return context


# Stock Management Views

class StockDashboardView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Dashboard for stock level monitoring."""
    template_name = 'frontend/inventory/stock_dashboard.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()

        try:
            # Get stock summary data
            stock_summary = api_client.get_stock_summary()
            context['stock_summary'] = stock_summary

            # Get low stock alerts
            low_stock_items = api_client.get_low_stock_items()
            context['low_stock_items'] = low_stock_items.get('results', [])

            # Get recent stock movements
            recent_movements = api_client.get_stock_movements({'page_size': 10})
            context['recent_movements'] = recent_movements.get('results', [])

            # Get warehouse list for filters
            warehouses = api_client.get_warehouses({'page_size': 100})
            context['warehouses'] = warehouses.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar el dashboard de stock")
            context.update({
                'stock_summary': {},
                'low_stock_items': [],
                'recent_movements': [],
                'warehouses': []
            })

        return context


class StockListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Enhanced stock list view with filtering."""
    template_name = 'frontend/inventory/stock_list.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()
        
        # Initialize search form
        search_form = StockSearchForm(self.request.GET or None)
        context['search_form'] = search_form

        try:
            # Build filters
            params = {}
            if search_form.is_valid():
                if search_form.cleaned_data.get('search'):
                    params['search'] = search_form.cleaned_data['search']
                if search_form.cleaned_data.get('warehouse_id'):
                    params['warehouse_id'] = search_form.cleaned_data['warehouse_id']
                if search_form.cleaned_data.get('category'):
                    params['category'] = search_form.cleaned_data['category']
                if search_form.cleaned_data.get('stock_status'):
                    params['stock_status'] = search_form.cleaned_data['stock_status']

            # Get page parameter
            page = self.request.GET.get('page', 1)
            params['page'] = page

            # Get stock data
            stock_data = api_client.get_stock_items(params)
            context['stock_items'] = stock_data.get('results', [])
            context['pagination'] = {
                'count': stock_data.get('count', 0),
                'next': stock_data.get('next'),
                'previous': stock_data.get('previous'),
                'current_page': int(page),
                'total_pages': (stock_data.get('count', 0) + 19) // 20
            }

            # Get warehouses for filter dropdown
            warehouses = api_client.get_warehouses({'page_size': 100})
            context['warehouses'] = warehouses.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar el inventario")
            context.update({
                'stock_items': [],
                'warehouses': [],
                'pagination': {'count': 0, 'current_page': 1, 'total_pages': 0}
            })

        return context


class StockMovementCreateView(LoginRequiredMixin, APIClientMixin, View):
    """View for creating stock movements."""
    template_name = 'frontend/inventory/stock_movement_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request):
        form = StockMovementForm()
        api_client = self.get_api_client()

        try:
            # Get products for dropdown
            products_data = api_client.get_products({'page_size': 1000})
            product_choices = [(p['id'], f"{p['code']} - {p['name']}") 
                             for p in products_data.get('results', [])]
            form.fields['product_id'].widget.choices = [('', 'Seleccionar producto')] + product_choices

            # Get warehouses for dropdown
            warehouses_data = api_client.get_warehouses({'page_size': 100})
            warehouse_choices = [(w['id'], f"{w['code']} - {w['name']}") 
                               for w in warehouses_data.get('results', [])]
            form.fields['warehouse_id'].widget.choices = [('', 'Seleccionar almacén')] + warehouse_choices

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del formulario")
            form.fields['product_id'].widget.choices = [('', 'Seleccionar producto')]
            form.fields['warehouse_id'].widget.choices = [('', 'Seleccionar almacén')]

        return render(request, self.template_name, {
            'form': form,
            'title': 'Registrar Movimiento de Stock',
            'action': 'create'
        })

    def post(self, request):
        form = StockMovementForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                movement_data = {
                    'product_id': form.cleaned_data['product_id'],
                    'warehouse_id': form.cleaned_data['warehouse_id'],
                    'movement_type': form.cleaned_data['movement_type'],
                    'quantity': float(form.cleaned_data['quantity']),
                    'unit_cost': float(form.cleaned_data['unit_cost']) if form.cleaned_data['unit_cost'] else None,
                    'reference_number': form.cleaned_data['reference_number'],
                    'notes': form.cleaned_data['notes']
                }

                movement = api_client.create_stock_movement(movement_data)
                messages.success(request, f"Movimiento de stock registrado exitosamente.")
                return redirect('frontend:stock_movements')

            except APIException as e:
                self.handle_api_error(e, "Error al registrar el movimiento de stock")

        # Reload choices if form is invalid
        try:
            products_data = api_client.get_products({'page_size': 1000})
            product_choices = [(p['id'], f"{p['code']} - {p['name']}") 
                             for p in products_data.get('results', [])]
            form.fields['product_id'].widget.choices = [('', 'Seleccionar producto')] + product_choices

            warehouses_data = api_client.get_warehouses({'page_size': 100})
            warehouse_choices = [(w['id'], f"{w['code']} - {w['name']}") 
                               for w in warehouses_data.get('results', [])]
            form.fields['warehouse_id'].widget.choices = [('', 'Seleccionar almacén')] + warehouse_choices
        except APIException:
            pass

        return render(request, self.template_name, {
            'form': form,
            'title': 'Registrar Movimiento de Stock',
            'action': 'create'
        })


class StockMovementsView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for listing stock movements."""
    template_name = 'frontend/inventory/stock_movements.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()

        try:
            # Get filters from request
            params = {}
            if self.request.GET.get('product_id'):
                params['product_id'] = self.request.GET.get('product_id')
            if self.request.GET.get('warehouse_id'):
                params['warehouse_id'] = self.request.GET.get('warehouse_id')
            if self.request.GET.get('movement_type'):
                params['movement_type'] = self.request.GET.get('movement_type')
            if self.request.GET.get('date_from'):
                params['date_from'] = self.request.GET.get('date_from')
            if self.request.GET.get('date_to'):
                params['date_to'] = self.request.GET.get('date_to')

            # Get page parameter
            page = self.request.GET.get('page', 1)
            params['page'] = page

            # Get movements data
            movements_data = api_client.get_stock_movements(params)
            context['movements'] = movements_data.get('results', [])
            context['pagination'] = {
                'count': movements_data.get('count', 0),
                'next': movements_data.get('next'),
                'previous': movements_data.get('previous'),
                'current_page': int(page),
                'total_pages': (movements_data.get('count', 0) + 19) // 20
            }

            # Get filter options
            products_data = api_client.get_products({'page_size': 1000})
            context['products'] = products_data.get('results', [])

            warehouses_data = api_client.get_warehouses({'page_size': 100})
            context['warehouses'] = warehouses_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los movimientos de stock")
            context.update({
                'movements': [],
                'products': [],
                'warehouses': [],
                'pagination': {'count': 0, 'current_page': 1, 'total_pages': 0}
            })

        return context


# Warehouse Management Views

class WarehouseListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for listing warehouses."""
    template_name = 'frontend/inventory/warehouse_list.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_client = self.get_api_client()
        
        # Initialize search form
        search_form = WarehouseSearchForm(self.request.GET or None)
        context['search_form'] = search_form

        try:
            # Build filters
            params = {}
            if search_form.is_valid():
                if search_form.cleaned_data.get('search'):
                    params['search'] = search_form.cleaned_data['search']
                if search_form.cleaned_data.get('is_active'):
                    params['is_active'] = search_form.cleaned_data['is_active'] == 'true'

            # Get page parameter
            page = self.request.GET.get('page', 1)
            params['page'] = page

            # Get warehouses data
            warehouses_data = api_client.get_warehouses(params)
            context['warehouses'] = warehouses_data.get('results', [])
            context['pagination'] = {
                'count': warehouses_data.get('count', 0),
                'next': warehouses_data.get('next'),
                'previous': warehouses_data.get('previous'),
                'current_page': int(page),
                'total_pages': (warehouses_data.get('count', 0) + 19) // 20
            }

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los almacenes")
            context.update({
                'warehouses': [],
                'pagination': {'count': 0, 'current_page': 1, 'total_pages': 0}
            })

        return context


class WarehouseDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """View for displaying warehouse details."""
    template_name = 'frontend/inventory/warehouse_detail.html'
    login_url = reverse_lazy('frontend:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouse_id = kwargs.get('warehouse_id')
        api_client = self.get_api_client()

        try:
            # Get warehouse details
            warehouse = api_client.get_warehouse_detail(warehouse_id)
            context['warehouse'] = warehouse

            # Get stock items in this warehouse
            stock_data = api_client.get_stock_items({'warehouse_id': warehouse_id, 'page_size': 100})
            context['stock_items'] = stock_data.get('results', [])

            # Get recent movements for this warehouse
            movements_data = api_client.get_stock_movements({
                'warehouse_id': warehouse_id, 
                'page_size': 20
            })
            context['recent_movements'] = movements_data.get('results', [])

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los detalles del almacén")
            return redirect('frontend:warehouse_list')

        return context


class WarehouseCreateView(LoginRequiredMixin, APIClientMixin, View):
    """View for creating warehouses."""
    template_name = 'frontend/inventory/warehouse_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request):
        form = WarehouseForm()
        return render(request, self.template_name, {
            'form': form,
            'title': 'Crear Almacén',
            'action': 'create'
        })

    def post(self, request):
        form = WarehouseForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                warehouse_data = {
                    'code': form.cleaned_data['code'],
                    'name': form.cleaned_data['name'],
                    'description': form.cleaned_data['description'],
                    'address': form.cleaned_data['address'],
                    'manager_name': form.cleaned_data['manager_name'],
                    'phone': form.cleaned_data['phone'],
                    'email': form.cleaned_data['email'],
                    'is_active': form.cleaned_data['is_active']
                }

                warehouse = api_client.create_warehouse(warehouse_data)
                messages.success(request, f"Almacén '{warehouse['name']}' creado exitosamente.")
                return redirect('frontend:warehouse_detail', warehouse_id=warehouse['id'])

            except APIException as e:
                self.handle_api_error(e, "Error al crear el almacén")

        return render(request, self.template_name, {
            'form': form,
            'title': 'Crear Almacén',
            'action': 'create'
        })


class WarehouseUpdateView(LoginRequiredMixin, APIClientMixin, View):
    """View for updating warehouses."""
    template_name = 'frontend/inventory/warehouse_form.html'
    login_url = reverse_lazy('frontend:login')

    def get(self, request, warehouse_id):
        api_client = self.get_api_client()

        try:
            warehouse = api_client.get_warehouse_detail(warehouse_id)
            form = WarehouseForm(initial=warehouse)

        except APIException as e:
            self.handle_api_error(e, "Error al cargar el almacén")
            return redirect('frontend:warehouse_list')

        return render(request, self.template_name, {
            'form': form,
            'warehouse': warehouse,
            'title': f'Editar Almacén: {warehouse["name"]}',
            'action': 'update'
        })

    def post(self, request, warehouse_id):
        form = WarehouseForm(request.POST)
        api_client = self.get_api_client()

        if form.is_valid():
            try:
                warehouse_data = {
                    'code': form.cleaned_data['code'],
                    'name': form.cleaned_data['name'],
                    'description': form.cleaned_data['description'],
                    'address': form.cleaned_data['address'],
                    'manager_name': form.cleaned_data['manager_name'],
                    'phone': form.cleaned_data['phone'],
                    'email': form.cleaned_data['email'],
                    'is_active': form.cleaned_data['is_active']
                }

                warehouse = api_client.update_warehouse(warehouse_id, warehouse_data)
                messages.success(request, f"Almacén '{warehouse['name']}' actualizado exitosamente.")
                return redirect('frontend:warehouse_detail', warehouse_id=warehouse['id'])

            except APIException as e:
                self.handle_api_error(e, "Error al actualizar el almacén")

        # Reload warehouse data if form is invalid
        try:
            warehouse = api_client.get_warehouse_detail(warehouse_id)
        except APIException:
            warehouse = {}

        return render(request, self.template_name, {
            'form': form,
            'warehouse': warehouse,
            'title': f'Editar Almacén: {warehouse.get("name", "")}',
            'action': 'update'
        })


class WarehouseDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """View for deleting warehouses."""
    login_url = reverse_lazy('frontend:login')

    def post(self, request, warehouse_id):
        api_client = self.get_api_client()

        try:
            warehouse = api_client.get_warehouse_detail(warehouse_id)
            api_client.delete_warehouse(warehouse_id)
            messages.success(request, f"Almacén '{warehouse['name']}' eliminado exitosamente.")
        except APIException as e:
            self.handle_api_error(e, "Error al eliminar el almacén")

        return redirect('frontend:warehouse_list')