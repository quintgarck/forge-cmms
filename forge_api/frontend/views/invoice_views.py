"""
Vistas para la gestión de facturas en la aplicación frontend.
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
from ..forms.invoice_forms import InvoiceForm, InvoiceSearchForm
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class InvoiceListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para listar facturas con paginación y búsqueda."""
    template_name = 'frontend/invoices/invoice_list.html'
    login_url = 'frontend:login'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener parámetros de búsqueda y filtro
        search = self.request.GET.get('search', '').strip()
        page = self._get_page_number()
        status_filter = self.request.GET.get('status', '')
        client_filter = self.request.GET.get('client', '')
        sort_by = self.request.GET.get('sort', 'invoice_date')
        sort_order = self.request.GET.get('order', 'desc')

        try:
            api_client = self.get_api_client()

            # Construir parámetros de filtro
            filters = {}
            if search:
                filters['search'] = search
            if status_filter:
                filters['status'] = status_filter
            if client_filter:
                filters['client'] = client_filter
            if sort_by:
                order_prefix = '-' if sort_order == 'desc' else ''
                filters['ordering'] = f"{order_prefix}{sort_by}"

            # Obtener datos de facturas con paginación
            invoices_data = api_client.get_invoices(
                page=page,
                page_size=self.paginate_by,
                **filters
            )

            context['invoices'] = invoices_data.get('results', [])

            # Contexto de paginación
            total_count = invoices_data.get('count', 0)
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by

            context['pagination'] = {
                'count': total_count,
                'next': invoices_data.get('next'),
                'previous': invoices_data.get('previous'),
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
                {'value': 'DRAFT', 'label': 'Borrador'},
                {'value': 'PENDING', 'label': 'Pendiente'},
                {'value': 'PAID', 'label': 'Pagada'},
                {'value': 'OVERDUE', 'label': 'Vencida'},
                {'value': 'CANCELLED', 'label': 'Cancelada'},
                {'value': 'REFUNDED', 'label': 'Reembolsada'},
            ]

            # Opciones de ordenación
            context['sort_options'] = [
                {'value': 'issue_date', 'label': 'Fecha de emisión'},
                {'value': 'due_date', 'label': 'Fecha de vencimiento'},
                {'value': 'total_amount', 'label': 'Monto total'},
                {'value': 'invoice_number', 'label': 'Número de factura'},
                {'value': 'client_id', 'label': 'Cliente'},
            ]

        except APIException as e:
            self.handle_api_error(e, "Error al cargar la lista de facturas")
            # Establecer contexto vacío en caso de error
            context['invoices'] = []
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


class InvoiceDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista detallada de factura."""
    template_name = 'frontend/invoices/invoice_detail.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_id = kwargs.get('pk')

        try:
            api_client = self.get_api_client()

            # Obtener datos de la factura
            invoice_data = api_client.get_invoice(invoice_id)

            if invoice_data:
                # Calcular información adicional
                total_amount = invoice_data.get('total_amount', 0)
                paid_amount = invoice_data.get('paid_amount', 0)
                
                # Calcular saldo pendiente
                balance_due = total_amount - paid_amount
                invoice_data['balance_due'] = balance_due
                
                # Determinar estado de pago
                if balance_due <= 0:
                    invoice_data['payment_status'] = 'paid'
                    invoice_data['payment_status_label'] = 'Pagada'
                    invoice_data['payment_status_class'] = 'success'
                elif balance_due < total_amount:
                    invoice_data['payment_status'] = 'partial'
                    invoice_data['payment_status_label'] = 'Parcialmente Pagada'
                    invoice_data['payment_status_class'] = 'warning'
                else:
                    invoice_data['payment_status'] = 'unpaid'
                    invoice_data['payment_status_label'] = 'No Pagada'
                    invoice_data['payment_status_class'] = 'danger'
                
                # Determinar si está vencida
                from datetime import datetime
                due_date = invoice_data.get('due_date')
                if due_date:
                    from datetime import datetime
                    try:
                        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                        if due_date_obj < datetime.now().date() and balance_due > 0:
                            invoice_data['is_overdue'] = True
                            invoice_data['overdue_label'] = 'Vencida'
                            invoice_data['overdue_class'] = 'danger'
                        else:
                            invoice_data['is_overdue'] = False
                    except:
                        invoice_data['is_overdue'] = False

            context['invoice'] = invoice_data

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos de la factura")
            # Establecer contexto vacío en caso de error
            context['invoice'] = None

        return context


class InvoiceCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para crear nuevas facturas."""
    template_name = 'frontend/invoices/invoice_form.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Crear Factura'
        context['form_action'] = 'create'

        # Inicializar formulario con datos GET (para repoblado de formulario)
        form_data = self.request.POST if self.request.method == 'POST' else None
        context['form'] = InvoiceForm(form_data)

        return context

    def post(self, request, *args, **kwargs):
        from ..forms.invoice_forms import InvoiceForm

        form = InvoiceForm(request.POST)

        if form.is_valid():
            # Extraer datos del formulario limpio con TODOS los campos
            invoice_data = {
                'invoice_number': form.cleaned_data['invoice_number'],
                'wo_id': form.cleaned_data.get('wo_id'),
                'client_id': form.cleaned_data['client_id'],
                'currency_code': form.cleaned_data.get('currency_code', 'MXN'),
                'issue_date': form.cleaned_data['issue_date'].isoformat() if form.cleaned_data.get('issue_date') else None,
                'due_date': form.cleaned_data['due_date'].isoformat() if form.cleaned_data.get('due_date') else None,
                'paid_date': form.cleaned_data['paid_date'].isoformat() if form.cleaned_data.get('paid_date') else None,
                'subtotal': float(form.cleaned_data['subtotal']),
                'tax_amount': float(form.cleaned_data.get('tax_amount', 0)),
                'discount_amount': float(form.cleaned_data.get('discount_amount', 0)),
                'total_amount': float(form.cleaned_data['total_amount']),
                'status': form.cleaned_data['status'],
                'notes': form.cleaned_data.get('notes', ''),
            }

            try:
                api_client = self.get_api_client()
                result = api_client.create_invoice(invoice_data)

                messages.success(
                    request,
                    f'Factura "{invoice_data["invoice_number"]}" creada exitosamente.'
                )
                return redirect('frontend:invoice_detail', pk=result['id'])

            except APIException as e:
                logger.error(f"Invoice creation API error: {e}")

                # Manejar errores específicos de API
                if e.status_code == 401:
                    # Error de autenticación - intentar refrescar token
                    from ..services.api_client import ForgeAPIClient
                    auth_service = AuthenticationService(request)

                    if auth_service.refresh_token():
                        # Token refrescado, intentar de nuevo
                        try:
                            api_client = self.get_api_client()
                            result = api_client.create_invoice(invoice_data)

                            messages.success(
                                request,
                                f'Factura "{invoice_data["invoice_number"]}" creada exitosamente.'
                            )
                            return redirect('frontend:invoice_detail', pk=result['id'])
                        except APIException as retry_e:
                            form.add_error(None, f"Error de autenticación: {retry_e.message}")
                    else:
                        form.add_error(None, "Sesión expirada. Por favor, inicie sesión nuevamente.")
                        messages.error(request, "Su sesión ha expirado. Por favor, inicie sesión nuevamente.")

                elif e.status_code == 500:
                    # Error de servidor - mostrar mensaje amigable
                    form.add_error(None, "Error interno del servidor. El backend API no está funcionando correctamente. Por favor, contacte al administrador.")
                    logger.error(f"Server error 500 during invoice creation: {e}")

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
                    form.add_error(None, e.message or "Error al crear la factura")

        # El formulario es inválido o ocurrió un error de API
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class InvoiceUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para actualizar facturas existentes."""
    template_name = 'frontend/invoices/invoice_form.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_id = kwargs.get('pk')

        context['form_title'] = 'Editar Factura'
        context['form_action'] = 'update'

        try:
            api_client = self.get_api_client()
            invoice_data = api_client.get_invoice(invoice_id)
            context['invoice'] = invoice_data

            # Inicializar formulario con datos de la factura o datos POST
            if self.request.method == 'POST':
                form = InvoiceForm(self.request.POST)
            else:
                # Prellenar formulario con datos existentes de la factura
                from datetime import datetime
                initial_data = {
                    'invoice_number': invoice_data.get('invoice_number', ''),
                    'wo_id': invoice_data.get('wo_id'),
                    'client_id': invoice_data.get('client_id'),
                    'currency_code': invoice_data.get('currency_code', 'MXN'),
                    'issue_date': invoice_data.get('issue_date'),
                    'due_date': invoice_data.get('due_date'),
                    'paid_date': invoice_data.get('paid_date'),
                    'subtotal': invoice_data.get('subtotal', 0),
                    'tax_amount': invoice_data.get('tax_amount', 0),
                    'discount_amount': invoice_data.get('discount_amount', 0),
                    'total_amount': invoice_data.get('total_amount', 0),
                    'status': invoice_data.get('status', 'PENDING'),
                    'notes': invoice_data.get('notes', ''),
                }
                form = InvoiceForm(initial=initial_data)

            context['form'] = form

        except APIException as e:
            self.handle_api_error(e, "Error al cargar los datos de la factura")
            context['invoice'] = None
            context['form'] = InvoiceForm()

        return context

    def post(self, request, *args, **kwargs):
        from ..forms.invoice_forms import InvoiceForm

        invoice_id = kwargs.get('pk')
        form = InvoiceForm(request.POST)

        if form.is_valid():
            # Extraer datos del formulario limpio con TODOS los campos
            invoice_data = {
                'invoice_number': form.cleaned_data['invoice_number'],
                'wo_id': form.cleaned_data.get('wo_id'),
                'client_id': form.cleaned_data['client_id'],
                'currency_code': form.cleaned_data.get('currency_code', 'MXN'),
                'issue_date': form.cleaned_data['issue_date'].isoformat() if form.cleaned_data.get('issue_date') else None,
                'due_date': form.cleaned_data['due_date'].isoformat() if form.cleaned_data.get('due_date') else None,
                'paid_date': form.cleaned_data['paid_date'].isoformat() if form.cleaned_data.get('paid_date') else None,
                'subtotal': float(form.cleaned_data['subtotal']),
                'tax_amount': float(form.cleaned_data.get('tax_amount', 0)),
                'discount_amount': float(form.cleaned_data.get('discount_amount', 0)),
                'total_amount': float(form.cleaned_data['total_amount']),
                'status': form.cleaned_data['status'],
                'notes': form.cleaned_data.get('notes', ''),
            }

            try:
                api_client = self.get_api_client()
                result = api_client.update_invoice(invoice_id, invoice_data)

                messages.success(
                    request,
                    f'Factura "{invoice_data["invoice_number"]}" actualizada exitosamente.'
                )
                return redirect('frontend:invoice_detail', pk=invoice_id)

            except APIException as e:
                logger.error(f"Invoice update API error: {e}")

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
                    form.add_error(None, e.message or "Error al actualizar la factura")

        # El formulario es inválido o ocurrió un error de API
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class InvoiceDeleteView(LoginRequiredMixin, APIClientMixin, View):
    """Vista para eliminar facturas."""
    login_url = 'frontend:login'

    def post(self, request, *args, **kwargs):
        invoice_id = kwargs.get('pk')

        try:
            api_client = self.get_api_client()
            api_client.delete_invoice(invoice_id)

            messages.success(
                request,
                f'Factura eliminada exitosamente.'
            )
            return redirect('frontend:invoice_list')

        except APIException as e:
            logger.error(f"Invoice deletion API error: {e}")

            # Manejar errores específicos de API
            if e.status_code == 400 and e.response_data:
                error_message = self._extract_error_message(e.response_data)
                messages.error(request, f"Error al eliminar la factura: {error_message}")
            else:
                messages.error(request, "Error al eliminar la factura")

            # Redirigir de vuelta a la vista de detalle en caso de error
            return redirect('frontend:invoice_detail', pk=invoice_id)

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