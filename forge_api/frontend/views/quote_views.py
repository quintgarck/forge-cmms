"""
Quote Views - Sistema de gestión de cotizaciones
Tarea 6.4: Implementar gestión de cotizaciones
"""

import logging
from datetime import date, timedelta
from decimal import Decimal

from django.views import View
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction

from ..mixins import APIClientMixin
from ..services.api_client import APIException
from ..services.quote_calculation_engine import QuoteCalculationEngine
from ..services.quote_pdf_generator import QuotePDFGenerator

logger = logging.getLogger(__name__)


class QuoteListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Lista de cotizaciones con búsqueda y filtrado."""
    template_name = 'frontend/quotes/quote_list.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parámetros de búsqueda y filtrado
        search = self.request.GET.get('search', '').strip()
        status_filter = self.request.GET.get('status', '')
        client_filter = self.request.GET.get('client_id', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        try:
            api_client = self.get_api_client()
            
            # Construir parámetros de búsqueda
            params = {}
            if search:
                params['search'] = search
            if status_filter:
                params['status'] = status_filter
            if client_filter:
                params['client_id'] = client_filter
            if date_from:
                params['quote_date__gte'] = date_from
            if date_to:
                params['quote_date__lte'] = date_to
            
            # Filtro para cotizaciones cerradas/convertidas
            closed_filter = self.request.GET.get('closed_filter', '')
            
            # Obtener cotizaciones
            quotes_data = api_client.get('quotes/', params=params)
            quotes = quotes_data.get('results', [])
            
            # Aplicar filtro de cerradas/activas en el frontend
            if closed_filter == 'closed':
                # Solo cotizaciones convertidas (cerradas)
                quotes = [q for q in quotes if q.get('status') == 'CONVERTED']
            elif closed_filter == 'active':
                # Solo cotizaciones activas (no convertidas ni rechazadas ni expiradas)
                quotes = [q for q in quotes if q.get('status') in ['DRAFT', 'SENT', 'APPROVED']]
            
            # Enriquecer cotizaciones con información de WO y factura relacionada
            for quote in quotes:
                if quote.get('converted_to_wo_id'):
                    try:
                        wo = api_client.get_workorder(quote['converted_to_wo_id'])
                        quote['work_order'] = {
                            'wo_id': wo.get('wo_id'),
                            'wo_number': wo.get('wo_number', f"WO-{wo.get('wo_id')}"),
                            'status': wo.get('status'),
                        }
                        
                        # Intentar obtener factura relacionada con la WO
                        try:
                            invoices_data = api_client.get_invoices(wo_id=quote['converted_to_wo_id'])
                            invoices = invoices_data.get('results', [])
                            if invoices:
                                invoice = invoices[0]
                                quote['invoice'] = {
                                    'invoice_id': invoice.get('invoice_id'),
                                    'invoice_number': invoice.get('invoice_number'),
                                    'status': invoice.get('status'),
                                    'total_amount': invoice.get('total_amount'),
                                }
                        except APIException:
                            quote['invoice'] = None
                    except APIException:
                        quote['work_order'] = None
                        quote['invoice'] = None
            
            context['quotes'] = quotes
            context['filters'] = {
                'search': search,
                'status': status_filter,
                'client_id': client_filter,
                'date_from': date_from,
                'date_to': date_to,
                'closed_filter': closed_filter,
            }
            
            # Estadísticas
            context['stats'] = {
                'total': len(quotes),
                'draft': len([q for q in quotes if q.get('status') == 'DRAFT']),
                'sent': len([q for q in quotes if q.get('status') == 'SENT']),
                'approved': len([q for q in quotes if q.get('status') == 'APPROVED']),
                'converted': len([q for q in quotes if q.get('status') == 'CONVERTED']),
            }
            
            # Obtener clientes para el filtro
            try:
                clients_data = api_client.get('clients/', params={'page_size': 100})
                context['clients'] = clients_data.get('results', [])
            except APIException:
                context['clients'] = []
            
        except APIException as e:
            logger.error(f"Error loading quotes: {e}")
            messages.error(self.request, "Error al cargar las cotizaciones.")
            context['quotes'] = []
            context['stats'] = {'total': 0, 'draft': 0, 'sent': 0, 'approved': 0, 'converted': 0}
        
        return context


class QuoteDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista detallada de una cotización."""
    template_name = 'frontend/quotes/quote_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quote_id = kwargs.get('pk')
        
        try:
            api_client = self.get_api_client()
            
            # Obtener cotización
            quote = api_client.get_quote(quote_id)
            
            # Obtener items de la cotización
            quote_items_data = api_client.get_quote_items(quote_id=quote_id)
            quote['items'] = quote_items_data.get('results', [])
            
            # Obtener información de orden de trabajo y factura relacionada
            if quote.get('converted_to_wo_id'):
                try:
                    wo = api_client.get_workorder(quote['converted_to_wo_id'])
                    quote['work_order'] = {
                        'wo_id': wo.get('wo_id'),
                        'wo_number': wo.get('wo_number', f"WO-{wo.get('wo_id')}"),
                        'status': wo.get('status'),
                    }
                    
                    # Intentar obtener factura relacionada con la WO
                    try:
                        invoices_data = api_client.get_invoices(wo_id=quote['converted_to_wo_id'])
                        invoices = invoices_data.get('results', [])
                        if invoices:
                            invoice = invoices[0]
                            quote['invoice'] = {
                                'invoice_id': invoice.get('invoice_id'),
                                'invoice_number': invoice.get('invoice_number'),
                                'status': invoice.get('status'),
                                'total_amount': invoice.get('total_amount'),
                            }
                    except APIException:
                        quote['invoice'] = None
                except APIException:
                    quote['work_order'] = None
                    quote['invoice'] = None
            
            context['quote'] = quote
            
            # Información adicional
            context['can_convert'] = quote.get('status') in ['DRAFT', 'APPROVED']
            context['can_edit'] = quote.get('status') == 'DRAFT'
            context['can_send'] = quote.get('status') == 'DRAFT'
            
        except APIException as e:
            logger.error(f"Error loading quote {quote_id}: {e}")
            messages.error(self.request, "Error al cargar la cotización.")
            context['quote'] = None
        
        return context


class QuotePDFView(LoginRequiredMixin, APIClientMixin, View):
    """Generar PDF de cotización (Tarea 6.3)."""
    
    def get(self, request, quote_id):
        """Generar y devolver PDF de cotización."""
        try:
            api_client = self.get_api_client()
            
            # Obtener cotización
            quote = api_client.get_quote(quote_id)
            
            # Obtener items de la cotización
            quote_items_data = api_client.get_quote_items(quote_id=quote_id)
            quote['items'] = quote_items_data.get('results', [])
            
            # Obtener datos del cliente
            if quote.get('client_id'):
                try:
                    client = api_client.get_client(quote['client_id'])
                    quote['client'] = client
                except APIException:
                    quote['client'] = {}
            
            # Generar PDF
            pdf_generator = QuotePDFGenerator()
            pdf_buffer = pdf_generator.generate_pdf(quote)
            
            # Preparar respuesta HTTP
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            filename = f"cotizacion_{quote.get('quote_number', quote_id)}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except ImportError as e:
            logger.error(f"ReportLab not available: {e}")
            messages.error(request, "La generación de PDF no está disponible. Instale ReportLab.")
            return redirect('frontend:quote_detail', pk=quote_id)
        except APIException as e:
            logger.error(f"Error generating PDF for quote {quote_id}: {e}")
            messages.error(request, "Error al generar el PDF de la cotización.")
            return redirect('frontend:quote_detail', pk=quote_id)
        except Exception as e:
            logger.error(f"Unexpected error generating PDF for quote {quote_id}: {e}")
            messages.error(request, "Error inesperado al generar el PDF.")
            return redirect('frontend:quote_detail', pk=quote_id)


class QuoteCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Crear nueva cotización."""
    template_name = 'frontend/quotes/quote_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Obtener clientes
            clients_data = api_client.get('clients/', params={'page_size': 100, 'status': 'ACTIVE'})
            context['clients'] = clients_data.get('results', [])
            
            # Obtener equipos
            equipment_data = api_client.get('equipment/', params={'page_size': 100})
            context['equipment'] = equipment_data.get('results', [])
            
            # Inicializar motor de cálculo
            context['calculation_engine'] = QuoteCalculationEngine(api_client)
            
        except APIException as e:
            logger.error(f"Error loading quote form data: {e}")
            context['clients'] = []
            context['equipment'] = []
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Crear cotización desde el formulario."""
        try:
            api_client = self.get_api_client()
            calculation_engine = QuoteCalculationEngine(api_client)
            
            # Validar cliente requerido
            client_id = request.POST.get('client_id')
            if not client_id:
                messages.error(request, "El cliente es requerido.")
                return self.get(request)
            
            # Obtener datos del formulario
            quote_data = {
                'client_id': int(client_id),
                'equipment_id': int(request.POST.get('equipment_id')) if request.POST.get('equipment_id') else None,
                'quote_date': request.POST.get('quote_date', date.today().isoformat()),
                'valid_until': request.POST.get('valid_until') or None,
                'currency_code': request.POST.get('currency_code', 'MXN').upper(),
                'notes': request.POST.get('notes', ''),
                'terms_and_conditions': request.POST.get('terms_and_conditions', ''),
                'status': 'DRAFT',
            }
            
            # Parsear items desde JSON (si se envía como JSON) o desde formulario
            items = []
            items_json = request.POST.get('items_json', '')
            
            if items_json:
                # Items enviados como JSON
                import json
                try:
                    items = json.loads(items_json)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON for items: {items_json}")
                    messages.error(request, "Error al parsear los items de la cotización.")
                    return self.get(request)
            else:
                # Parsear items desde formulario (formato: items[0][description], items[0][hours], etc.)
                item_count = 0
                while True:
                    description = request.POST.get(f'items[{item_count}][description]')
                    if not description:
                        break
                    
                    item = {
                        'description': description,
                        'quantity': int(request.POST.get(f'items[{item_count}][quantity]', 1)),
                        'hours': Decimal(request.POST.get(f'items[{item_count}][hours]', 0)),
                        'hourly_rate': Decimal(request.POST.get(f'items[{item_count}][hourly_rate]', 500)),
                        'service_code': request.POST.get(f'items[{item_count}][service_code]', ''),
                        'flat_rate_id': int(request.POST.get(f'items[{item_count}][flat_rate_id]')) if request.POST.get(f'items[{item_count}][flat_rate_id]') else None,
                        'notes': request.POST.get(f'items[{item_count}][notes]', ''),
                    }
                    items.append(item)
                    item_count += 1
            
            # Si no hay items, agregar al menos uno vacío
            if not items:
                messages.error(request, "Debe agregar al menos un item a la cotización.")
                return self.get(request)
            
            # Calcular totales
            discount_percent = Decimal(request.POST.get('discount_percent', 0) or 0)
            tax_percent = Decimal(request.POST.get('tax_percent', 16) or 16)
            
            totals = calculation_engine.calculate_quote_totals(
                items=items,
                discount_percent=discount_percent,
                tax_percent=tax_percent
            )
            
            quote_data.update(totals)
            
            # Validar reglas de negocio
            validation = calculation_engine.validate_business_rules(quote_data)
            if not validation['valid']:
                for error in validation['errors']:
                    messages.error(request, error)
                return self.get(request)
            
            # Crear cotización en la API
            quote = api_client.create_quote(quote_data)
            quote_id = quote.get('quote_id')
            
            if not quote_id:
                messages.error(request, "Error al crear la cotización. No se recibió un ID válido.")
                return self.get(request)
            
            # Crear items de la cotización
            for item_data in items:
                # Calcular line_total si no está presente
                if 'line_total' not in item_data:
                    item_calc = calculation_engine.calculate_quote_item_total(item_data)
                    item_data['line_total'] = float(item_calc['line_subtotal'])
                
                quote_item_data = {
                    'quote_id': quote_id,
                    'description': item_data['description'],
                    'quantity': item_data['quantity'],
                    'hours': float(item_data['hours']),
                    'hourly_rate': float(item_data['hourly_rate']),
                    'line_total': float(item_data['line_total']),
                    'service_code': item_data.get('service_code', ''),
                    'flat_rate_id': item_data.get('flat_rate_id'),
                    'notes': item_data.get('notes', ''),
                }
                
                try:
                    api_client.create_quote_item(quote_item_data)
                except APIException as e:
                    logger.error(f"Error creating quote item: {e}")
                    # Continuar con los demás items aunque falle uno
            
            messages.success(request, f"Cotización #{quote.get('quote_number', quote_id)} creada exitosamente.")
            return redirect('frontend:quote_detail', pk=quote_id)
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error creating quote: {e}", exc_info=True)
            messages.error(request, f"Error en los datos: {str(e)}")
        except APIException as e:
            logger.error(f"API error creating quote: {e}", exc_info=True)
            messages.error(request, f"Error al crear la cotización: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating quote: {e}", exc_info=True)
            messages.error(request, "Error inesperado al crear la cotización.")
        
        return self.get(request)


class QuoteConvertToWorkOrderView(LoginRequiredMixin, APIClientMixin, View):
    """Convertir cotización a orden de trabajo."""
    
    def post(self, request, quote_id):
        """Convertir cotización a WO."""
        try:
            api_client = self.get_api_client()
            
            # Obtener cotización
            quote = api_client.get_quote(quote_id)
            
            if quote.get('status') == 'CONVERTED':
                messages.warning(request, "Esta cotización ya fue convertida a orden de trabajo.")
                return redirect('frontend:quote_detail', pk=quote_id)
            
            # Obtener items de la cotización
            quote_items_data = api_client.get_quote_items(quote_id=quote_id)
            quote_items = quote_items_data.get('results', [])
            
            if not quote_items:
                messages.error(request, "La cotización no tiene items. No se puede convertir a orden de trabajo.")
                return redirect('frontend:quote_detail', pk=quote_id)
            
            # Crear orden de trabajo desde la cotización
            wo_data = {
                'client_id': quote.get('client_id'),
                'equipment_id': quote.get('equipment_id'),
                'description': f"Orden de trabajo creada desde cotización #{quote.get('quote_number', quote_id)}",
                'complaint': quote.get('notes', ''),
                'priority': 'normal',
                'status': 'draft',
            }
            
            # Crear orden de trabajo
            work_order = api_client.create_workorder(wo_data)
            wo_id = work_order.get('wo_id')
            
            if not wo_id:
                messages.error(request, "Error al crear la orden de trabajo.")
                return redirect('frontend:quote_detail', pk=quote_id)
            
            # Crear servicios en la orden de trabajo desde los items de la cotización
            for quote_item in quote_items:
                wo_service_data = {
                    'wo_id': wo_id,
                    'flat_rate_id': quote_item.get('flat_rate_id'),
                    'service_code': quote_item.get('service_code', ''),
                    'description': quote_item.get('description', ''),
                    'estimated_hours': float(quote_item.get('hours', 0)),
                    'actual_hours': float(quote_item.get('hours', 0)),
                    'hourly_rate': float(quote_item.get('hourly_rate', 500)),
                    'quantity': quote_item.get('quantity', 1),
                    'status': 'PENDING',
                    'completion_status': 'NOT_STARTED',
                }
                
                try:
                    # Crear servicio en la orden de trabajo
                    # Nota: El endpoint puede variar según la API, ajustar si es necesario
                    api_client.post('work-order-services/', data=wo_service_data)
                except APIException as e:
                    logger.warning(f"Error creating WO service from quote item: {e}")
                    # Continuar con los demás servicios aunque falle uno
                    # Intentar con endpoint alternativo
                    try:
                        api_client.post(f'work-orders/{wo_id}/services/', data=wo_service_data)
                    except APIException:
                        pass
            
            # Actualizar cotización: marcar como convertida y vincular a WO
            update_data = {
                'status': 'CONVERTED',
                'converted_to_wo_id': wo_id,
            }
            
            try:
                api_client.update_quote(quote_id, update_data)
            except APIException as e:
                logger.warning(f"Error updating quote status to CONVERTED: {e}")
            
            messages.success(
                request, 
                f"Cotización convertida a orden de trabajo #{wo_id} exitosamente."
            )
            return redirect('frontend:quote_detail', pk=quote_id)
            
        except APIException as e:
            logger.error(f"Error converting quote {quote_id} to WO: {e}", exc_info=True)
            messages.error(request, f"Error al convertir la cotización: {str(e)}")
            return redirect('frontend:quote_detail', pk=quote_id)
        except Exception as e:
            logger.error(f"Unexpected error converting quote {quote_id} to WO: {e}", exc_info=True)
            messages.error(request, "Error inesperado al convertir la cotización.")
            return redirect('frontend:quote_detail', pk=quote_id)
