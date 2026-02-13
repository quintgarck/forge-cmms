"""
Vistas para la gestión de equipos en la aplicación frontend.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.urls import reverse_lazy
from datetime import datetime
from django import forms
import logging

from ..services.api_client import ForgeAPIClient, APIException
from ..forms.equipment_forms import EquipmentForm
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class EquipmentListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para listar equipos con paginación y búsqueda."""
    template_name = 'frontend/equipment/equipment_list.html'
    login_url = 'frontend:login'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener parámetros de búsqueda y filtro
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        status_filter = self.request.GET.get('status', '')
        client_filter = self.request.GET.get('client', '')
        sort_by = self.request.GET.get('sort', 'equipment_code')
        sort_order = self.request.GET.get('order', 'asc')

        try:
            api_client = self.get_api_client()

            # Construir parámetros de filtro
            filters = {}
            if search:
                filters['search'] = search
            if status_filter:
                filters['status'] = status_filter
            if client_filter:
                filters['client_id'] = client_filter
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"

            # Obtener datos de equipos con paginación
            equipment_data = api_client.get_equipment(
                page=page,
                page_size=self.paginate_by,
                **filters
            )

            context['equipment_list'] = equipment_data.get('results', [])

            # Contexto de paginación
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

            # Filtros y ordenación
            context['filters'] = {
                'search': search,
                'status': status_filter,
                'client': client_filter,
                'sort': sort_by,
                'order': sort_order,
            }

            # Opciones de estado para filtro
            context['status_options'] = [
                {'value': '', 'label': 'Todos los estados'},
                {'value': 'ACTIVO', 'label': 'Activos'},
                {'value': 'INACTIVO', 'label': 'Inactivos'},
                {'value': 'sold', 'label': 'Vendidos'},
                {'value': 'scrapped', 'label': 'Desechados'},
            ]

            # Opciones de clientes para filtro
            try:
                clients_data = api_client.get_clients(page_size=1000)  # Obtener todos los clientes
                client_list = clients_data.get('results', [])
                context['client_options'] = [{'value': '', 'label': 'Todos los clientes'}]
                for client in client_list:
                    context['client_options'].append({
                        'value': client['client_id'],
                        'label': f"{client['name']} ({client.get('email', 'Sin email')})"
                    })
            except APIException as client_error:
                logger.warning(f"Could not load clients for filter: {client_error}")
                context['client_options'] = [{'value': '', 'label': 'Todos los clientes'}]

            # Opciones de tipo de combustible para filtro
            context['fuel_type_options'] = [
                {'value': '', 'label': 'Todos'},
                {'value': 'GASOLINE', 'label': 'Gasolina'},
                {'value': 'DIESEL', 'label': 'Diésel'},
                {'value': 'ELECTRIC', 'label': 'Eléctrico'},
                {'value': 'HYBRID', 'label': 'Híbrido'},
                {'value': 'LPG', 'label': 'GLP'},
                {'value': 'CNG', 'label': 'GNC'},
                {'value': 'OTHER', 'label': 'Otro'},
            ]

            # Opciones de ordenación
            context['sort_options'] = [
                {'value': 'equipment_code', 'label': 'Código'},
                {'value': 'brand', 'label': 'Marca'},
                {'value': 'model', 'label': 'Modelo'},
                {'value': 'year', 'label': 'Año'},
                {'value': 'client_id', 'label': 'Cliente'},
                {'value': 'created_at', 'label': 'Fecha de registro'},
            ]

        except APIException as e:
            self.handle_api_error(e, "Error al cargar la lista de equipos")
            # Establecer contexto vacío en caso de error
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
                'status': status_filter,
                'client': client_filter,
                'sort': sort_by,
                'order': sort_order,
            }

        return context

    def _get_page_number(self):
        """Obtener y validar número de página desde la solicitud."""
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1

    def _get_page_range(self, current_page, total_pages, window=5):
        """Generar un rango de páginas inteligente para la paginación."""
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


class EquipmentDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista detallada de equipo."""
    template_name = 'frontend/equipment/equipment_detail.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_id = kwargs.get('pk')

        try:
            api_client = self.get_api_client()

            # Obtener datos del equipo
            equipment_data = api_client.get_equipment_detail(equipment_id)

            if equipment_data:
                # Calcular antigüedad del equipo
                year = equipment_data.get('year')
                if year:
                    current_year = datetime.now().year
                    equipment_data['age'] = current_year - year

            context['equipment'] = equipment_data

            # Obtener órdenes de trabajo asociadas al equipo
            try:
                workorders_data = api_client.get_workorders(equipment_id=equipment_id, page_size=50)
                workorders = workorders_data.get('results', [])

                # Procesar órdenes de trabajo
                for workorder in workorders:
                    status = workorder.get('status', '').upper()
                    if status == 'PENDING':
                        workorder['status_class'] = 'warning'
                        workorder['status_label'] = 'Pendiente'
                    elif status == 'IN_PROGRESS':
                        workorder['status_class'] = 'info'
                        workorder['status_label'] = 'En Progreso'
                    elif status == 'COMPLETED':
                        workorder['status_class'] = 'success'
                        workorder['status_label'] = 'Completada'
                    elif status == 'CANCELLED':
                        workorder['status_class'] = 'danger'
                        workorder['status_label'] = 'Cancelada'
                    else:
                        workorder['status_class'] = 'secondary'
                        workorder['status_label'] = status.title()

                context['workorders'] = workorders

                # Estadísticas de órdenes de trabajo
                total_workorders = len(workorders)
                completed = len([wo for wo in workorders if wo.get('status', '').upper() == 'COMPLETED'])
                pending = len([wo for wo in workorders if wo.get('status', '').upper() == 'PENDING'])
                in_progress = len([wo for wo in workorders if wo.get('status', '').upper() == 'IN_PROGRESS'])

                context['workorder_stats'] = {
                    'total': total_workorders,
                    'completed': completed,
                    'pending': pending,
                    'in_progress': in_progress,
                    'completion_rate': (completed / total_workorders * 100) if total_workorders > 0 else 0
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

        return context


class EquipmentCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para crear nuevos equipos."""
    template_name = 'frontend/equipment/equipment_form.html'
    login_url = 'frontend:login'
    
    def _load_dropdown_options(self, form, preserve_values=True):
        """Cargar opciones para los dropdowns de clientes, marcas y modelos."""
        # Preservar valores actuales si el formulario tiene errores
        brand_value = None
        model_value = None
        if preserve_values and form.is_bound and form.data:
            brand_value = form.data.get('brand', '')
            model_value = form.data.get('model', '')
        
        try:
            api_client = self.get_api_client()
            
            # Cargar TIPOS DE EQUIPO (Nuevo)
            try:
                types_data = api_client.get_equipment_types(page_size=100)
                type_list = types_data.get('results', [])
                
                type_choices = [('', 'Seleccione un tipo')]
                for et in type_list:
                    type_choices.append((
                        et['type_id'],
                        f"{et['name']} ({et.get('category', 'General')})"
                    ))
                form.fields['type_id'].widget.choices = type_choices
            except Exception as type_error:
                logger.error(f"Error loading equipment types: {type_error}")
                form.fields['type_id'].widget.choices = [('', 'Error al cargar tipos')]
            
            # --- CARGA PROGRESIVA DE CATALOGOS ---
            
            # 1. Combustible (Fuel Codes)
            try:
                fuel_data = api_client.get_fuel_codes(page_size=100)
                fuel_list = fuel_data.get('results', [])
                fuel_choices = [('', 'Seleccionar tipo de combustible')]
                for item in fuel_list:
                    label = item.get('name_es') or item.get('name_en') or item.get('fuel_code')
                    fuel_choices.append((item['fuel_code'], label))
                form.fields['fuel_code'].widget.choices = fuel_choices
            except Exception as e:
                logger.error(f"Error loading fuel codes: {e}")
                
            # 2. Aspiración (Aspiration Codes)
            try:
                asp_data = api_client.get_aspiration_codes(page_size=100)
                asp_list = asp_data.get('results', [])
                asp_choices = [('', 'Seleccionar tipo de aspiración')]
                for item in asp_list:
                    label = item.get('name_es') or item.get('name_en') or item.get('aspiration_code')
                    asp_choices.append((item['aspiration_code'], label))
                form.fields['aspiration_code'].widget.choices = asp_choices
            except Exception as e:
                logger.error(f"Error loading aspiration codes: {e}")

            # 3. Transmisión (Transmission Codes)
            try:
                trans_data = api_client.get_transmission_codes(page_size=100)
                trans_list = trans_data.get('results', [])
                trans_choices = [('', 'Seleccionar tipo de transmisión')]
                for item in trans_list:
                    label = item.get('name_es') or item.get('name_en') or item.get('transmission_code')
                    trans_choices.append((item['transmission_code'], label))
                form.fields['transmission_code'].widget.choices = trans_choices
            except Exception as e:
                logger.error(f"Error loading transmission codes: {e}")

            # 4. Tracción (Drivetrain Codes)
            try:
                drive_data = api_client.get_drivetrain_codes(page_size=100)
                drive_list = drive_data.get('results', [])
                drive_choices = [('', 'Seleccionar tipo de tracción')]
                for item in drive_list:
                    label = item.get('name_es') or item.get('name_en') or item.get('drivetrain_code')
                    drive_choices.append((item['drivetrain_code'], label))
                form.fields['drivetrain_code'].widget.choices = drive_choices
            except Exception as e:
                logger.error(f"Error loading drivetrain codes: {e}")

            # 5. Color (Color Codes)
            try:
                color_data = api_client.get_color_codes(page_size=100)
                color_list = color_data.get('results', [])
                color_choices = [('', 'Seleccionar color')]
                for item in color_list:
                    label = f"{item.get('name_es')} ({item.get('color_code')})"
                    color_choices.append((item['color_code'], label))
                # Fallback: si no hay colores en DB, mantenemos vacío o ponemos genéricos si quisiéramos
                form.fields['color'].widget.choices = color_choices
            except Exception as e:
                logger.error(f"Error loading color codes: {e}")

            
            # Cargar opciones de clientes
            clients_data = api_client.get_clients(page_size=1000)
            client_list = clients_data.get('results', [])
            
            client_choices = [('', 'Seleccione un cliente')]
            for client in client_list:
                client_choices.append((
                    client['client_id'],
                    f"{client['name']} - {client.get('email', 'Sin email')}"
                ))
            form.fields['client_id'].widget.choices = client_choices
            
        except APIException as e:
            logger.error(f"Error loading clients: {e}")
            form.fields['client_id'].widget.choices = [('', 'Error al cargar clientes')]
        
        # Cargar marcas OEM
        try:
            api_client = self.get_api_client()
            brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
            brand_results = brands_data.get('results', brands_data)

            brand_choices = [('', 'Seleccione una marca')]
            for brand in brand_results:
                value = brand.get('oem_code') or brand.get('name')
                label_name = (brand.get('name') or '').strip() or value
                code = (brand.get('oem_code') or '').strip()
                label = f"{label_name} ({code})" if code else label_name
                brand_choices.append((value, label))

            # Crear nuevo widget con opciones
            new_brand_widget = forms.Select(
                choices=brand_choices,
                attrs={
                    'class': 'form-select',
                    'required': True,
                    'id': 'id_brand',
                },
            )
            
            # Si hay valor preservado, establecerlo
            if brand_value:
                form.fields['brand'].initial = brand_value
            
            form.fields['brand'].widget = new_brand_widget
            
        except APIException as e:
            logger.error(f"Error loading OEM brands: {e}")
            form.fields['brand'].widget = forms.Select(
                choices=[('', 'Error al cargar marcas')],
                attrs={
                    'class': 'form-select',
                    'id': 'id_brand',
                },
            )

        # Inicializar modelo (se actualizará vía JS según la marca)
        # Si hay valor preservado, establecerlo
        if model_value:
            form.fields['model'].initial = model_value
            
        form.fields['model'].widget = forms.Select(
            choices=[('', 'Seleccione una marca primero')],
            attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_model',
            },
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Equipo'
        context['form_action'] = 'create'

        form_data = self.request.POST if self.request.method == 'POST' else None
        form = EquipmentForm(form_data)
        
        # Cargar opciones de dropdowns
        self._load_dropdown_options(form)
        
        context['form'] = form
        return context

    def post(self, request, *args, **kwargs):
        from ..forms.equipment_forms import EquipmentForm

        form = EquipmentForm(request.POST)

        if form.is_valid():
            # Extraer datos del formulario limpio con TODOS los campos
            equipment_data = {
                'equipment_code': form.cleaned_data['equipment_code'],
                'type_id': form.cleaned_data.get('type_id'),
                'client_id': form.cleaned_data['client_id'],
                'brand': form.cleaned_data['brand'],
                'model': form.cleaned_data['model'],
                'year': form.cleaned_data.get('year'),
                'serial_number': form.cleaned_data.get('serial_number', ''),
                'vin': form.cleaned_data.get('vin', ''),
                'license_plate': form.cleaned_data.get('license_plate', ''),
                'color': form.cleaned_data.get('color', ''),
                'submodel_trim': form.cleaned_data.get('submodel_trim', ''),
                'body_style': form.cleaned_data.get('body_style', ''),
                'doors': form.cleaned_data.get('doors'),
                'engine_desc': form.cleaned_data.get('engine_desc', ''),
                'fuel_code': form.cleaned_data.get('fuel_code', ''),
                'aspiration_code': form.cleaned_data.get('aspiration_code', ''),
                'transmission_code': form.cleaned_data.get('transmission_code', ''),
                'drivetrain_code': form.cleaned_data.get('drivetrain_code', ''),
                'purchase_date': form.cleaned_data['purchase_date'].isoformat() if form.cleaned_data.get('purchase_date') else None,
                'warranty_until': form.cleaned_data['warranty_until'].isoformat() if form.cleaned_data.get('warranty_until') else None,
                'last_service_date': form.cleaned_data['last_service_date'].isoformat() if form.cleaned_data.get('last_service_date') else None,
                'next_service_date': form.cleaned_data['next_service_date'].isoformat() if form.cleaned_data.get('next_service_date') else None,
                'current_mileage_hours': int(form.cleaned_data.get('current_mileage_hours', 0)),
                'last_mileage_update': form.cleaned_data['last_mileage_update'].isoformat() if form.cleaned_data.get('last_mileage_update') else None,
                'status': form.cleaned_data['status'],
                'notes': form.cleaned_data.get('notes', ''),
            }

            try:
                api_client = self.get_api_client()
                result = api_client.create_equipment(equipment_data)

                messages.success(
                    request,
                    f'Equipo "{equipment_data["equipment_code"]}" creado exitosamente.'
                )
                return redirect('frontend:equipment_detail', pk=result['equipment_id'])

            except APIException as e:
                logger.error(f"Equipment creation API error: {e}")

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
                    form.add_error(None, e.message or "Error al crear el equipo")
        
        # Cargar opciones de dropdowns después de errores de validación
        self._load_dropdown_options(form)
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class EquipmentUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para actualizar equipos existentes."""
    template_name = 'frontend/equipment/equipment_form.html'
    login_url = 'frontend:login'

    def _load_dropdown_options(self, form, preserve_values=True):
        """Cargar opciones para los dropdowns de clientes, marcas y modelos."""
        # Preservar valores actuales si el formulario tiene errores
        brand_value = None
        model_value = None
        if preserve_values and form.is_bound and form.data:
            brand_value = form.data.get('brand', '')
            model_value = form.data.get('model', '')
        
        try:
            api_client = self.get_api_client()
            
            # Cargar opciones de clientes
            clients_data = api_client.get_clients(page_size=1000)
            client_list = clients_data.get('results', [])
            
            client_choices = [('', 'Seleccione un cliente')]
            for client in client_list:
                client_choices.append((
                    client['client_id'],
                    f"{client['name']} - {client.get('email', 'Sin email')}"
                ))
            form.fields['client_id'].widget.choices = client_choices
            
        except APIException as e:
            logger.error(f"Error loading clients: {e}")
            form.fields['client_id'].widget.choices = [('', 'Error al cargar clientes')]
        
        # Cargar marcas OEM
        try:
            api_client = self.get_api_client()
            brands_data = api_client.get_oem_brands(page_size=1000, is_active=True)
            brand_results = brands_data.get('results', brands_data)

            brand_choices = [('', 'Seleccione una marca')]
            for brand in brand_results:
                value = brand.get('oem_code') or brand.get('name')
                label_name = (brand.get('name') or '').strip() or value
                code = (brand.get('oem_code') or '').strip()
                label = f"{label_name} ({code})" if code else label_name
                brand_choices.append((value, label))

            # Crear nuevo widget con opciones
            new_brand_widget = forms.Select(
                choices=brand_choices,
                attrs={
                    'class': 'form-select',
                    'required': True,
                    'id': 'id_brand',
                },
            )
            
            # Si hay valor preservado, establecerlo
            if brand_value:
                form.fields['brand'].initial = brand_value
            
            form.fields['brand'].widget = new_brand_widget
            
        except APIException as e:
            logger.error(f"Error loading OEM brands: {e}")
            form.fields['brand'].widget = forms.Select(
                choices=[('', 'Error al cargar marcas')],
                attrs={
                    'class': 'form-select',
                    'id': 'id_brand',
                },
            )

        # Inicializar modelo (se actualizará vía JS según la marca)
        # Si hay valor preservado, establecerlo
        if model_value:
            form.fields['model'].initial = model_value
            
        form.fields['model'].widget = forms.Select(
            choices=[('', 'Seleccione una marca primero')],
            attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_model',
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_id = kwargs.get('pk')

        context['form_title'] = 'Editar Equipo'
        context['form_action'] = 'update'

        try:
            api_client = self.get_api_client()
            equipment_data = api_client.get_equipment_detail(equipment_id)
            context['equipment'] = equipment_data

            if self.request.method == 'POST':
                form = EquipmentForm(self.request.POST)
            else:
                # Prellenar formulario con datos existentes
                initial_data = {
                    'equipment_code': equipment_data.get('equipment_code', ''),
                    'type_id': equipment_data.get('type_id'),
                    'client_id': equipment_data.get('client_id'),
                    'brand': equipment_data.get('brand', ''),
                    'model': equipment_data.get('model', ''),
                    'year': equipment_data.get('year'),
                    'serial_number': equipment_data.get('serial_number', ''),
                    'vin': equipment_data.get('vin', ''),
                    'license_plate': equipment_data.get('license_plate', ''),
                    'color': equipment_data.get('color', ''),
                    'submodel_trim': equipment_data.get('submodel_trim', ''),
                    'body_style': equipment_data.get('body_style', ''),
                    'doors': equipment_data.get('doors'),
                    'engine_desc': equipment_data.get('engine_desc', ''),
                    'fuel_code': equipment_data.get('fuel_code', ''),
                    'aspiration_code': equipment_data.get('aspiration_code', ''),
                    'transmission_code': equipment_data.get('transmission_code', ''),
                    'drivetrain_code': equipment_data.get('drivetrain_code', ''),
                    'purchase_date': equipment_data.get('purchase_date'),
                    'warranty_until': equipment_data.get('warranty_until'),
                    'last_service_date': equipment_data.get('last_service_date'),
                    'next_service_date': equipment_data.get('next_service_date'),
                    'current_mileage_hours': equipment_data.get('current_mileage_hours', 0),
                    'last_mileage_update': equipment_data.get('last_mileage_update'),
                    'status': equipment_data.get('status', 'ACTIVO'),
                    'notes': equipment_data.get('notes', ''),
                }
                form = EquipmentForm(initial=initial_data)

            # Cargar opciones de dropdowns
            self._load_dropdown_options(form)

            context['form'] = form

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos del equipo")
            context['equipment'] = None
            context['form'] = EquipmentForm()

        return context

    def post(self, request, *args, **kwargs):
        from ..forms.equipment_forms import EquipmentForm

        equipment_id = kwargs.get('pk')
        form = EquipmentForm(request.POST)

        if form.is_valid():
            # Extraer datos del formulario limpio con TODOS los campos
            equipment_data = {
                'equipment_code': form.cleaned_data['equipment_code'],
                'type_id': form.cleaned_data.get('type_id'),
                'client_id': form.cleaned_data['client_id'],
                'brand': form.cleaned_data['brand'],
                'model': form.cleaned_data['model'],
                'year': form.cleaned_data.get('year'),
                'serial_number': form.cleaned_data.get('serial_number', ''),
                'vin': form.cleaned_data.get('vin', ''),
                'license_plate': form.cleaned_data.get('license_plate', ''),
                'color': form.cleaned_data.get('color', ''),
                'submodel_trim': form.cleaned_data.get('submodel_trim', ''),
                'body_style': form.cleaned_data.get('body_style', ''),
                'doors': form.cleaned_data.get('doors'),
                'engine_desc': form.cleaned_data.get('engine_desc', ''),
                'fuel_code': form.cleaned_data.get('fuel_code', ''),
                'aspiration_code': form.cleaned_data.get('aspiration_code', ''),
                'transmission_code': form.cleaned_data.get('transmission_code', ''),
                'drivetrain_code': form.cleaned_data.get('drivetrain_code', ''),
                'purchase_date': form.cleaned_data['purchase_date'].isoformat() if form.cleaned_data.get('purchase_date') else None,
                'warranty_until': form.cleaned_data['warranty_until'].isoformat() if form.cleaned_data.get('warranty_until') else None,
                'last_service_date': form.cleaned_data['last_service_date'].isoformat() if form.cleaned_data.get('last_service_date') else None,
                'next_service_date': form.cleaned_data['next_service_date'].isoformat() if form.cleaned_data.get('next_service_date') else None,
                'current_mileage_hours': int(form.cleaned_data.get('current_mileage_hours', 0)),
                'last_mileage_update': form.cleaned_data['last_mileage_update'].isoformat() if form.cleaned_data.get('last_mileage_update') else None,
                'status': form.cleaned_data['status'],
                'notes': form.cleaned_data.get('notes', ''),
            }

            try:
                api_client = self.get_api_client()
                result = api_client.update_equipment(equipment_id, equipment_data)

                messages.success(
                    request,
                    f'Equipo "{equipment_data["equipment_code"]}" actualizado exitosamente.'
                )
                return redirect('frontend:equipment_detail', pk=equipment_id)

            except APIException as e:
                logger.error(f"Equipment update API error: {e}")

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
                    form.add_error(None, e.message or "Error al actualizar el equipo")
        
        # Cargar opciones de dropdowns después de errores de validación
        self._load_dropdown_options(form)
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class EquipmentDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Vista para eliminar equipos."""
    login_url = 'frontend:login'

    def post(self, request, *args, **kwargs):
        equipment_id = kwargs.get('pk')

        try:
            api_client = self.get_api_client()
            api_client.delete_equipment(equipment_id)

            messages.success(
                request,
                'Equipo eliminado exitosamente.'
            )
            return redirect('frontend:equipment_list')

        except APIException as e:
            logger.error(f"Equipment deletion API error: {e}")

            if e.status_code == 400 and e.response_data:
                error_message = self._extract_error_message(e.response_data)
                messages.error(request, f"Error al eliminar el equipo: {error_message}")
            else:
                messages.error(request, "Error al eliminar el equipo")

            return redirect('frontend:equipment_detail', pk=equipment_id)

    def _extract_error_message(self, error_data):
        """Extraer mensaje de error del cuerpo de respuesta."""
        if isinstance(error_data, dict):
            for field in ['detail', 'message', 'error', 'non_field_errors']:
                if field in error_data:
                    error_value = error_data[field]
                    if isinstance(error_value, list):
                        return '; '.join(str(err) for err in error_value)
                    return str(error_value)

        return str(error_data)
