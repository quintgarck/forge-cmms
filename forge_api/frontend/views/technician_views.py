"""
Vistas para la gestión de técnicos en la aplicación frontend.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from datetime import datetime
import logging

from ..services.api_client import ForgeAPIClient, APIException
from ..services import AuthenticationService
from ..forms.technician_forms import TechnicianForm, TechnicianSearchForm
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class TechnicianListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para listar técnicos con paginación y búsqueda."""
    template_name = 'frontend/technicians/technician_list.html'
    login_url = 'frontend:login'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener parámetros de búsqueda y filtro
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        status_filter = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort', 'last_name')
        sort_order = self.request.GET.get('order', 'asc')

        try:
            api_client = self.get_api_client()

            # Construir parámetros de filtro
            filters = {}
            if search:
                filters['search'] = search
            if status_filter:
                filters['status'] = status_filter
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"

            # Obtener datos de técnicos con paginación
            technicians_data = api_client.get_technicians(
                page=page,
                page_size=self.paginate_by,
                **filters
            )

            context['technicians'] = technicians_data.get('results', [])

            # Contexto de paginación
            total_count = technicians_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by

            context['pagination'] = {
                'count': total_count,
                'next': technicians_data.get('next'),
                'previous': technicians_data.get('previous'),
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }

            # Filtros y ordenación
            context['filters'] = {
                'search': search,
                'status': status_filter,
                'sort': sort_by,
                'order': sort_order,
            }

            # Opciones de estado para filtro
            context['status_options'] = [
                {'value': '', 'label': 'Todos los estados'},
                {'value': 'ACTIVE', 'label': 'Activos'},
                {'value': 'INACTIVE', 'label': 'Inactivos'},
                {'value': 'SUSPENDED', 'label': 'Suspendidos'},
            ]

            # Opciones de ordenación
            context['sort_options'] = [
                {'value': 'last_name', 'label': 'Apellido'},
                {'value': 'first_name', 'label': 'Nombre'},
                {'value': 'employee_code', 'label': 'Código de empleado'},
                {'value': 'hire_date', 'label': 'Fecha de contratación'},
                {'value': 'hourly_rate', 'label': 'Tarifa por hora'},
            ]

        except APIException as e:
            self.handle_api_error(e, "Error al cargar la lista de técnicos")
            # Establecer contexto vacío en caso de error
            context['technicians'] = []
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
        """Obtener y validar número de página desde la solicitud."""
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)  # Asegurar que la página sea al menos 1
        except (ValueError, TypeError):
            return 1

    def _get_page_range(self, current_page, total_pages, window=5):
        """Generar un rango de páginas inteligente para la paginación."""
        if total_pages <= window:
            return list(range(1, total_pages + 1))

        # Calcular inicio y fin de la ventana
        half_window = window // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)

        # Ajustar si estamos cerca del principio o final
        if end - start < window - 1:
            if start == 1:
                end = min(total_pages, start + window - 1)
            else:
                start = max(1, end - window + 1)

        return list(range(start, end + 1))


class TechnicianDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista detallada de técnico."""
    template_name = 'frontend/technicians/technician_detail.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        technician_id = kwargs.get('pk')

        try:
            api_client = self.get_api_client()

            # Obtener datos del técnico
            technician_data = api_client.get_technician(technician_id)

            if technician_data:
                # Calcular antigüedad
                from datetime import datetime
                try:
                    hire_date = datetime.fromisoformat(technician_data.get('hire_date', '').replace('Z', '+00:00'))
                    today = datetime.now()
                    technician_data['seniority'] = (today - hire_date).days
                except:
                    technician_data['seniority'] = 0

            context['technician'] = technician_data

            # Obtener órdenes de trabajo asignadas al técnico
            try:
                workorders_data = api_client.get_workorders(assigned_technician=technician_id, page_size=50)
                workorders = workorders_data.get('results', [])

                # Procesar órdenes de trabajo para mejor visualización
                for workorder in workorders:
                    # Agregar estado de estilo
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

                # Calcular estadísticas de órdenes de trabajo
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
                logger.warning(f"Could not load work orders for technician {technician_id}: {wo_error}")
                context['workorders'] = []
                context['workorder_stats'] = {
                    'total': 0,
                    'completed': 0,
                    'pending': 0,
                    'in_progress': 0,
                    'completion_rate': 0
                }

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del técnico")
            # Establecer contexto vacío en caso de error
            context['technician'] = None
            context['workorders'] = []
            context['workorder_stats'] = {
                'total': 0,
                'completed': 0,
                'pending': 0,
                'in_progress': 0,
                'completion_rate': 0
            }

        return context


class TechnicianCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para crear nuevos técnicos."""
    template_name = 'frontend/technicians/technician_form.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Técnico'
        context['form_action'] = 'create'

        # Inicializar formulario con datos GET (para repoblado de formulario)
        form_data = self.request.POST if self.request.method == 'POST' else None
        context['form'] = TechnicianForm(form_data)

        return context

    def post(self, request, *args, **kwargs):
        from ..forms.technician_forms import TechnicianForm

        form = TechnicianForm(request.POST)

        if form.is_valid():
            # Extraer datos del formulario limpio con TODOS los campos
            
            # Convertir specialization y certifications de string a lista si es necesario
            specialization_data = form.cleaned_data.get('specialization', '')
            certifications_data = form.cleaned_data.get('certifications', '')
            
            # Si son strings, convertirlos a listas
            if isinstance(specialization_data, str) and specialization_data:
                specialization_data = [s.strip() for s in specialization_data.split(',') if s.strip()]
            elif not specialization_data:
                specialization_data = []
            
            if isinstance(certifications_data, str) and certifications_data:
                certifications_data = [c.strip() for c in certifications_data.split(',') if c.strip()]
            elif not certifications_data:
                certifications_data = []
            
            technician_data = {
                'employee_code': form.cleaned_data['employee_code'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'birth_date': form.cleaned_data['birth_date'].isoformat() if form.cleaned_data.get('birth_date') else None,
                'hire_date': form.cleaned_data['hire_date'].isoformat() if form.cleaned_data['hire_date'] else None,
                'certification_level': form.cleaned_data.get('certification_level', ''),
                'hourly_rate': float(form.cleaned_data['hourly_rate'] or 0),
                'daily_rate': float(form.cleaned_data['daily_rate'] or 0),
                'overtime_multiplier': float(form.cleaned_data['overtime_multiplier'] or 1.50),
                'status': form.cleaned_data['status'],
                'specialization': specialization_data,
                'certifications': certifications_data,
                'work_schedule': form.cleaned_data.get('work_schedule'),
                'efficiency_avg': float(form.cleaned_data['efficiency_avg'] or 100.00),
                'quality_score': float(form.cleaned_data['quality_score'] or 100.00),
                'is_active': form.cleaned_data.get('is_active', True),
                'notes': form.cleaned_data.get('notes', ''),
            }

            try:
                api_client = self.get_api_client()
                result = api_client.create_technician(technician_data)

                messages.success(
                    request,
                    f'Técnico "{technician_data["first_name"]} {technician_data["last_name"]}" creado exitosamente.'
                )
                return redirect('frontend:technician_detail', pk=result.get('technician_id', result.get('id')))

            except APIException as e:
                logger.error(f"Technician creation API error: {e}")

                # Manejar errores específicos de API
                if e.status_code == 401:
                    # Error de autenticación - intentar refrescar token
                    from ..services.api_client import ForgeAPIClient
                    auth_service = AuthenticationService(request)

                    if auth_service.refresh_token():
                        # Token refrescado, intentar de nuevo
                        try:
                            api_client = self.get_api_client()
                            result = api_client.create_technician(technician_data)

                            messages.success(
                                request,
                                f'Técnico "{technician_data["first_name"]} {technician_data["last_name"]}" creado exitosamente.'
                            )
                            return redirect('frontend:technician_detail', pk=result.get('technician_id', result.get('id')))
                        except APIException as retry_e:
                            form.add_error(None, f"Error de autenticación: {retry_e.message}")
                    else:
                        form.add_error(None, "Sesión expirada. Por favor, inicie sesión nuevamente.")
                        messages.error(request, "Su sesión ha expirado. Por favor, inicie sesión nuevamente.")

                elif e.status_code == 500:
                    # Error de servidor - mostrar mensaje amigable
                    form.add_error(None, "Error interno del servidor. El backend API no está funcionando correctamente. Por favor, contacte al administrador.")
                    logger.error(f"Server error 500 during technician creation: {e}")

                elif e.status_code == 400 and e.response_data:
                    # Agregar errores de validación de API al formulario
                    for field, errors in e.response_data.items():
                        if field in form.fields:
                            if isinstance(errors, list):
                                for error in errors:
                                    form.add_error(field, error)
                            else:
                                form.add_error(field, str(errors))
                        else:
                            form.add_error(None, f"{field}: {errors}")

                # Manejar errores de autenticación
                elif e.status_code == 401:
                    form.add_error(None, "Sesión expirada. Por favor, inicie sesión nuevamente.")
                else:
                    form.add_error(None, e.message or "Error al crear el técnico")

        # El formulario es inválido o ocurrió un error de API
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class TechnicianUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para actualizar técnicos existentes."""
    template_name = 'frontend/technicians/technician_form.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        technician_id = kwargs.get('pk')

        context['form_title'] = 'Editar Técnico'
        context['form_action'] = 'update'

        try:
            api_client = self.get_api_client()
            technician_data = api_client.get_technician(technician_id)
            context['technician'] = technician_data

            # Inicializar formulario con datos del técnico o datos POST
            if self.request.method == 'POST':
                form = TechnicianForm(self.request.POST)
            else:
                # Prellenar formulario con datos existentes del técnico
                from datetime import datetime
                
                # Convertir listas a strings separados por comas para el formulario
                specialization_str = ', '.join(technician_data.get('specialization', [])) if isinstance(technician_data.get('specialization'), list) else ''
                certifications_str = ', '.join(technician_data.get('certifications', [])) if isinstance(technician_data.get('certifications'), list) else ''
                
                # Descomponer work_schedule JSON en campos individuales
                work_schedule = technician_data.get('work_schedule') or {}
                if isinstance(work_schedule, str):
                    import json
                    try:
                        work_schedule = json.loads(work_schedule)
                    except:
                        work_schedule = {}
                elif not isinstance(work_schedule, dict):
                    work_schedule = {}
                
                initial_data = {
                    'employee_code': technician_data.get('employee_code', ''),
                    'first_name': technician_data.get('first_name', ''),
                    'last_name': technician_data.get('last_name', ''),
                    'email': technician_data.get('email', ''),
                    'phone': technician_data.get('phone', ''),
                    'birth_date': technician_data.get('birth_date'),
                    'hire_date': technician_data.get('hire_date'),
                    'certification_level': technician_data.get('certification_level', ''),
                    'hourly_rate': technician_data.get('hourly_rate', 0),
                    'daily_rate': technician_data.get('daily_rate', 0),
                    'overtime_multiplier': technician_data.get('overtime_multiplier', 1.50),
                    'status': technician_data.get('status', 'ACTIVE'),
                    'specialization': specialization_str,
                    'certifications': certifications_str,
                    # Descomponer horario semanal
                    'monday_schedule': work_schedule.get('lunes', ''),
                    'tuesday_schedule': work_schedule.get('martes', ''),
                    'wednesday_schedule': work_schedule.get('miercoles', ''),
                    'thursday_schedule': work_schedule.get('jueves', ''),
                    'friday_schedule': work_schedule.get('viernes', ''),
                    'saturday_schedule': work_schedule.get('sabado', ''),
                    'sunday_schedule': work_schedule.get('domingo', ''),
                    'efficiency_avg': technician_data.get('efficiency_avg', 100.00),
                    'quality_score': technician_data.get('quality_score', 100.00),
                    'is_active': technician_data.get('is_active', True),
                    'notes': technician_data.get('notes', ''),
                }
                form = TechnicianForm(initial=initial_data)

            context['form'] = form

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del técnico")
            context['technician'] = None
            context['form'] = TechnicianForm()

        return context

    def post(self, request, *args, **kwargs):
        from ..forms.technician_forms import TechnicianForm

        technician_id = kwargs.get('pk')
        logger.info(f"TechnicianUpdateView.post: Updating technician {technician_id}")
        form = TechnicianForm(request.POST)

        if form.is_valid():
            logger.info("TechnicianUpdateView.post: Form is valid")
            # Extraer datos del formulario limpio con TODOS los campos
            
            # Convertir specialization y certifications de string a lista si es necesario
            specialization_data = form.cleaned_data.get('specialization', '')
            certifications_data = form.cleaned_data.get('certifications', '')
            
            # Si son strings, convertirlos a listas
            if isinstance(specialization_data, str) and specialization_data:
                specialization_data = [s.strip() for s in specialization_data.split(',') if s.strip()]
            elif not specialization_data:
                specialization_data = []
            
            if isinstance(certifications_data, str) and certifications_data:
                certifications_data = [c.strip() for c in certifications_data.split(',') if c.strip()]
            elif not certifications_data:
                certifications_data = []
            
            technician_data = {
                'employee_code': form.cleaned_data['employee_code'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data['phone'],
                'birth_date': form.cleaned_data['birth_date'].isoformat() if form.cleaned_data.get('birth_date') else None,
                'hire_date': form.cleaned_data['hire_date'].isoformat() if form.cleaned_data['hire_date'] else None,
                'certification_level': form.cleaned_data.get('certification_level', ''),
                'hourly_rate': float(form.cleaned_data['hourly_rate'] or 0),
                'daily_rate': float(form.cleaned_data['daily_rate'] or 0),
                'overtime_multiplier': float(form.cleaned_data['overtime_multiplier'] or 1.50),
                'status': form.cleaned_data['status'],
                'specialization': specialization_data,
                'certifications': certifications_data,
                'work_schedule': form.cleaned_data.get('work_schedule'),
                'efficiency_avg': float(form.cleaned_data['efficiency_avg'] or 100.00),
                'quality_score': float(form.cleaned_data['quality_score'] or 100.00),
                'is_active': form.cleaned_data.get('is_active', True),
                'notes': form.cleaned_data.get('notes', ''),
            }
            logger.info(f"TechnicianUpdateView.post: Sending data: {technician_data}")

            try:
                api_client = self.get_api_client()
                result = api_client.update_technician(technician_id, technician_data)
                
                logger.info(f"TechnicianUpdateView.post: API update success: {result}")

                messages.success(
                    request,
                    f'Técnico "{technician_data["first_name"]} {technician_data["last_name"]}" actualizado exitosamente.'
                )
                return redirect('frontend:technician_detail', pk=technician_id)

            except APIException as e:
                logger.error(f"Technician update API error: {e}")
                logger.error(f"API Error Response Data: {e.response_data}")

                # Manejar errores específicos de API
                if e.status_code == 400 and e.response_data:
                    # Agregar errores de validación de API al formulario
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
                    form.add_error(None, e.message or "Error al actualizar el técnico")
        else:
            logger.warning(f"TechnicianUpdateView.post: Form is invalid: {form.errors}")

        # El formulario es inválido o ocurrió un error de API
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class TechnicianDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Vista para eliminar técnicos."""
    login_url = 'frontend:login'

    def post(self, request, *args, **kwargs):
        technician_id = kwargs.get('pk')

        try:
            api_client = self.get_api_client()
            api_client.delete_technician(technician_id)

            messages.success(
                request,
                f'Técnico eliminado exitosamente.'
            )
            return redirect('frontend:technician_list')

        except APIException as e:
            logger.error(f"Technician deletion API error: {e}")

            # Manejar errores específicos de API
            if e.status_code == 400 and e.response_data:
                error_message = self._extract_error_message(e.response_data)
                messages.error(request, f"Error al eliminar el técnico: {error_message}")
            else:
                messages.error(request, "Error al eliminar el técnico")

            # Redirigir de vuelta a la vista de detalle en caso de error
            return redirect('frontend:technician_detail', pk=technician_id)

    def _extract_error_message(self, error_data):
        """Extraer mensaje de error del cuerpo de respuesta."""
        if isinstance(error_data, dict):
            # Intentar campos comunes de mensaje de error
            for field in ['detail', 'message', 'error', 'non_field_errors']:
                if field in error_data:
                    error_value = error_data[field]
                    if isinstance(error_value, list):
                        return '; '.join(str(err) for err in error_value)
                    return str(error_value)

        return str(error_data)