"""
Currency Rate Views - Gestión de Tasas de Cambio
ForgeDB Frontend Web Application

Vistas para gestión avanzada de tasas de cambio, actualización automática
y visualización de histórico.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.urls import reverse
from django.http import JsonResponse
from django.utils import timezone
import json
import logging

from ..services.api_client import ForgeAPIClient, APIException
from ..services.exchange_rate_service import ExchangeRateService
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class CurrencyRateManagementView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """
    Vista principal para gestión de tasas de cambio
    """
    template_name = 'frontend/catalog/currency_rate_management.html'
    
    def get_context_data(self, **kwargs):
        """Agregar contexto para la vista"""
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            # Obtener todas las monedas con sus tasas
            currencies = rate_service.get_current_rates()
            
            # Identificar moneda base
            base_currency = next(
                (c for c in currencies if c.get('is_base_currency')), 
                None
            )
            
            # Calcular cambios para cada moneda
            for currency in currencies:
                if not currency.get('is_base_currency'):
                    change_info = rate_service.calculate_rate_change(
                        currency.get('currency_code'),
                        period_days=7
                    )
                    currency['rate_change'] = change_info
                else:
                    currency['rate_change'] = {
                        'change_percent': 0.0,
                        'direction': 'stable'
                    }
            
            context['currencies'] = currencies
            context['base_currency'] = base_currency
            context['total_currencies'] = len(currencies)
            context['active_currencies'] = len([c for c in currencies if c.get('is_active')])
            
            # Información de última actualización
            context['last_update'] = {
                'timestamp': timezone.now(),
                'source': 'Sistema'
            }
            
            # Fuentes disponibles
            context['available_sources'] = [
                {
                    'id': 'exchangerate-api',
                    'name': 'ExchangeRate-API',
                    'free': True,
                    'description': 'API gratuita sin necesidad de registro'
                },
                {
                    'id': 'fixer',
                    'name': 'Fixer.io',
                    'free': False,
                    'description': 'API profesional (requiere API key)'
                }
            ]
            
        except APIException as e:
            logger.error(f"API error loading rates: {str(e)}")
            self.handle_api_error(e, "Error al cargar las tasas de cambio.")
            context['currencies'] = []
            context['base_currency'] = None
        except Exception as e:
            logger.error(f"Unexpected error loading rates: {str(e)}")
            messages.error(self.request, "Error al cargar las tasas de cambio.")
            context['currencies'] = []
            context['base_currency'] = None
        
        return context


class CurrencyRateUpdateView(LoginRequiredMixin, APIClientMixin, View):
    """
    Vista para actualizar tasa individual (AJAX)
    """
    
    def post(self, request):
        """Actualizar tasa de una moneda"""
        try:
            data = json.loads(request.body)
            currency_code = data.get('currency_code')
            new_rate = data.get('rate')
            
            if not currency_code or not new_rate:
                return JsonResponse({
                    'success': False,
                    'error': 'Datos incompletos'
                }, status=400)
            
            # Validar tasa
            try:
                new_rate = float(new_rate)
                if new_rate <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'La tasa debe ser mayor a 0'
                    }, status=400)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Tasa inválida'
                }, status=400)
            
            # Actualizar tasa
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            result = rate_service.update_rate_manual(
                currency_code,
                new_rate,
                source='manual',
                user=request.user
            )
            
            if result:
                return JsonResponse({
                    'success': True,
                    'message': f'Tasa actualizada para {currency_code}',
                    'currency_code': currency_code,
                    'new_rate': new_rate,
                    'timestamp': timezone.now().isoformat()
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Error al actualizar la tasa'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating rate: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)


class CurrencyRateUpdateAllView(LoginRequiredMixin, APIClientMixin, View):
    """
    Vista para actualizar todas las tasas automáticamente (AJAX)
    """
    
    def post(self, request):
        """Actualizar todas las tasas desde fuente externa"""
        try:
            data = json.loads(request.body)
            source = data.get('source', 'exchangerate-api')
            base_currency = data.get('base_currency', 'USD')
            
            # Actualizar tasas
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            result = rate_service.update_rates_automatic(
                base_currency=base_currency,
                source=source
            )
            
            if result.get('success'):
                return JsonResponse({
                    'success': True,
                    'message': f"Actualización completada: {result['updated']} tasas actualizadas",
                    'updated': result['updated'],
                    'failed': result['failed'],
                    'total': result['total'],
                    'source': result['source'],
                    'timestamp': result['timestamp'],
                    'results': result.get('results', [])
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Error desconocido')
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            logger.error(f"Error updating all rates: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class CurrencyRateHistoryView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """
    Vista para visualizar histórico de tasas
    """
    template_name = 'frontend/catalog/currency_rate_history.html'
    
    def get_context_data(self, **kwargs):
        """Agregar contexto para la vista"""
        context = super().get_context_data(**kwargs)
        
        currency_code = self.kwargs.get('currency_code')
        days = int(self.request.GET.get('days', 30))
        
        try:
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            # Obtener información de la moneda
            currency = api_client.get_currency(currency_code)
            
            if not currency:
                messages.error(self.request, "Moneda no encontrada")
                return context
            
            # Obtener histórico
            history = rate_service.get_rate_history(currency_code, days)
            
            # Preparar datos para gráfico
            chart_data = {
                'labels': [h['date'] for h in reversed(history)],
                'rates': [h['rate'] for h in reversed(history)]
            }
            
            context['currency'] = currency
            context['history'] = history
            context['chart_data'] = json.dumps(chart_data)
            context['days'] = days
            context['currency_code'] = currency_code
            
            # Estadísticas
            if history:
                rates = [h['rate'] for h in history]
                context['stats'] = {
                    'min_rate': min(rates),
                    'max_rate': max(rates),
                    'avg_rate': sum(rates) / len(rates),
                    'current_rate': rates[0] if rates else 0
                }
            
        except APIException as e:
            logger.error(f"API error loading history: {str(e)}")
            self.handle_api_error(e, "Error al cargar el histórico.")
        except Exception as e:
            logger.error(f"Unexpected error loading history: {str(e)}")
            messages.error(self.request, "Error al cargar el histórico.")
        
        return context


class CurrencyRateHistoryAjaxView(LoginRequiredMixin, APIClientMixin, View):
    """
    Vista AJAX para obtener histórico de tasas
    """
    
    def get(self, request, currency_code):
        """Obtener histórico en formato JSON"""
        try:
            days = int(request.GET.get('days', 30))
            
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            history = rate_service.get_rate_history(currency_code, days)
            
            return JsonResponse({
                'success': True,
                'currency_code': currency_code,
                'history': history,
                'count': len(history)
            })
            
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
