"""
Client views for ForgeDB frontend application.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views import View
import logging

from ..services import ForgeAPIClient, AuthenticationService
from ..services.api_client import APIException

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
            
            # Get client's work orders with enhanced filtering (reduced page size for speed)
            try:
                workorders_data = api_client.get_workorders(client_id=client_id, page_size=10)  # Reduced from 50 to 10
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
            
            # Get client's equipment (if available) - reduced for speed
            try:
                equipment_data = api_client.get_equipment(client_id=client_id, page_size=5)  # Reduced from 20 to 5
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
        
        # Import ClientForm here to avoid circular imports
        from ..forms import ClientForm
        
        # Initialize form - empty for GET, will be populated in POST handler
        if self.request.method == 'POST':
            # This should not happen in get_context_data for POST, but just in case
            context['form'] = ClientForm(self.request.POST)
        else:
            context['form'] = ClientForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Import ClientForm here to avoid circular imports
        from ..forms import ClientForm
        
        form = ClientForm(request.POST)
        
        # Log form validation status for debugging
        logger.info(f"Client creation POST request received. Form data: {request.POST.dict()}")
        if not form.is_valid():
            logger.warning(f"Client form is invalid. Errors: {form.errors}")
        else:
            logger.info("Client form is valid")
        
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
                'status': 'ACTIVE',  # Set default status (UPPERCASE)
            }
            logger.info(f"Prepared client_data: {client_data}")
            
            try:
                api_client = self.get_api_client()
                logger.info(f"API client created. Base URL: {api_client.base_url}")
                logger.info(f"Calling create_client with data: {client_data}")
                result = api_client.create_client(client_data)
                logger.info(f"API create_client returned: {result}")
                
                # Clear cache for clients list to ensure new client appears
                from django.core.cache import cache
                try:
                    # Try to clear cache, but don't fail if cache backend doesn't support keys()
                    if hasattr(cache, 'keys'):
                        keys = cache.keys('*forge_api*clients*')
                        if keys:
                            cache.delete_many(keys)
                    else:
                        # For backends that don't support keys(), just clear the cache
                        cache.clear()
                except Exception as cache_error:
                    logger.warning(f"Could not clear cache: {cache_error}")
                
                messages.success(
                    request, 
                    f'Cliente "{client_data["name"]}" creado exitosamente.'
                )
                # The API returns client_id, not id
                client_id = result.get('client_id') or result.get('id')
                return redirect('frontend:client_list')
                
            except APIException as e:
                logger.error(f"Client creation API error: {e}", exc_info=True)
                logger.error(f"API error status_code: {e.status_code}, message: {e.message}, response_data: {getattr(e, 'response_data', {})}")
                
                # Handle specific API errors
                if e.status_code == 401:
                    # Authentication error - try to refresh token
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
                            # The API returns client_id, not id
                            client_id = result.get('client_id') or result.get('id')
                            return redirect('frontend:client_detail', pk=client_id)
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

                # Handle authentication errors
                elif e.status_code == 401:
                    form.add_error(None, "Sesión expirada. Por favor, inicie sesión nuevamente.")
                else:
                    form.add_error(None, e.message or "Error al crear el cliente")
            except Exception as e:
                # Catch any other unexpected exceptions
                logger.error(f"Unexpected error during client creation: {e}", exc_info=True)
                form.add_error(None, f"Error inesperado al crear el cliente: {str(e)}")
        
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
        
        # Import ClientForm here to avoid circular imports
        from ..forms import ClientForm
        
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
                    'type': client_data.get('type', 'INDIVIDUAL'),  # Default to INDIVIDUAL
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
        # Import ClientForm here to avoid circular imports
        from ..forms import ClientForm
        
        client_id = kwargs.get('pk')
        form = ClientForm(request.POST)
        
        if form.is_valid():
            # Extract cleaned form data - INCLUDE status field
            client_data = {
                'client_code': form.cleaned_data['client_code'],
                'type': form.cleaned_data['type'],
                'name': form.cleaned_data['name'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'address': form.cleaned_data['address'] or '',
                'credit_limit': float(form.cleaned_data['credit_limit'] or 0),
                'status': 'ACTIVE',  # Keep status ACTIVE on update
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