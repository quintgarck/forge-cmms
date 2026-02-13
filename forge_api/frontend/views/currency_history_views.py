"""
Currency History Views - Visualización de Histórico y Comparación
Tarea 4.4: Visualización de histórico de monedas
"""

import logging
from datetime import datetime, timedelta, date as date_type
from decimal import Decimal
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from ..mixins import APIClientMixin
from ..services.api_client import APIException
from ..services.exchange_rate_service import ExchangeRateService

logger = logging.getLogger(__name__)


class CurrencyHistoryComparisonView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para comparar histórico de múltiples monedas."""
    template_name = 'frontend/catalog/currency_history_comparison.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parámetros de la URL
        # Obtener monedas seleccionadas de múltiples formas
        currency_codes = self.request.GET.getlist('currencies')
        if not currency_codes:
            # Intentar con formato currencies[]=CODE
            currency_codes = self.request.GET.getlist('currencies[]')
        days = int(self.request.GET.get('days', 30))
        
        try:
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            # Obtener todas las monedas activas
            all_currencies = rate_service.get_current_rates()
            active_currencies = [c for c in all_currencies if c.get('is_active') and not c.get('is_base_currency')]
            
            # Si no se especificaron monedas, usar las primeras 3
            if not currency_codes:
                currency_codes = [c['currency_code'] for c in active_currencies[:3]]
            
            # Obtener histórico para cada moneda seleccionada
            comparison_data = []
            for code in currency_codes:
                currency = next((c for c in all_currencies if c.get('currency_code') == code), None)
                if currency:
                    history = rate_service.get_rate_history(code, days)
                    
                    # Calcular estadísticas
                    if history:
                        rates = [h['rate'] for h in history]
                        change_info = rate_service.calculate_rate_change(code, days)
                        
                        comparison_data.append({
                            'currency': currency,
                            'history': history,
                            'stats': {
                                'min': min(rates),
                                'max': max(rates),
                                'avg': sum(rates) / len(rates),
                                'current': rates[0] if rates else 0,
                                'change_percent': change_info.get('change_percent', 0),
                                'direction': change_info.get('direction', 'stable')
                            }
                        })
            
            context['comparison_data'] = comparison_data
            context['selected_currencies'] = currency_codes
            context['available_currencies'] = active_currencies
            context['days'] = days
            
        except Exception as e:
            logger.error(f"Error loading comparison: {e}")
            messages.error(self.request, "Error al cargar la comparación de monedas.")
            context['comparison_data'] = []
            context['available_currencies'] = []
        
        return context


class CurrencyHistoryComparisonAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API para obtener datos de comparación de histórico."""
    
    def get(self, request):
        try:
            currency_codes = request.GET.getlist('currencies', [])
            days = int(request.GET.get('days', 30))
            
            if not currency_codes:
                return JsonResponse({
                    'error': 'Debe especificar al menos una moneda'
                }, status=400)
            
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            # Obtener todas las monedas
            all_currencies = rate_service.get_current_rates()
            
            # Preparar datos para el gráfico
            chart_data = {
                'labels': [],
                'datasets': []
            }
            
            colors = [
                {'border': 'rgba(54, 162, 235, 1)', 'background': 'rgba(54, 162, 235, 0.1)'},
                {'border': 'rgba(255, 99, 132, 1)', 'background': 'rgba(255, 99, 132, 0.1)'},
                {'border': 'rgba(75, 192, 192, 1)', 'background': 'rgba(75, 192, 192, 0.1)'},
                {'border': 'rgba(255, 206, 86, 1)', 'background': 'rgba(255, 206, 86, 0.1)'},
                {'border': 'rgba(153, 102, 255, 1)', 'background': 'rgba(153, 102, 255, 0.1)'},
                {'border': 'rgba(255, 159, 64, 1)', 'background': 'rgba(255, 159, 64, 0.1)'},
            ]
            
            for idx, code in enumerate(currency_codes):
                currency = next((c for c in all_currencies if c.get('currency_code') == code), None)
                if not currency:
                    continue
                
                history = rate_service.get_rate_history(code, days)
                
                if history:
                    # Ordenar por fecha (más antiguo a más reciente)
                    sorted_history = sorted(history, key=lambda x: x['date'])
                    
                    # Si es el primero, establecer las fechas
                    if not chart_data['labels']:
                        chart_data['labels'] = [h['date'] for h in sorted_history]
                    
                    # Obtener color
                    color = colors[idx % len(colors)]
                    
                    chart_data['datasets'].append({
                        'label': f"{currency.get('name', code)} ({code})",
                        'data': [h['rate'] for h in sorted_history],
                        'borderColor': color['border'],
                        'backgroundColor': color['background'],
                        'borderWidth': 2,
                        'fill': False,
                        'tension': 0.4
                    })
            
            return JsonResponse({
                'success': True,
                'chart_data': chart_data,
                'currencies_count': len(chart_data['datasets'])
            })
            
        except Exception as e:
            logger.error(f"Error in comparison API: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class CurrencyAlertsAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API para obtener alertas de cambios significativos en tasas."""
    
    def get(self, request):
        try:
            threshold = float(request.GET.get('threshold', 5.0))  # Porcentaje de cambio
            period_days = int(request.GET.get('period_days', 7))
            
            api_client = self.get_api_client()
            rate_service = ExchangeRateService(api_client)
            
            # Obtener todas las monedas activas
            currencies = rate_service.get_current_rates()
            active_currencies = [c for c in currencies if c.get('is_active') and not c.get('is_base_currency')]
            
            alerts = []
            
            for currency in active_currencies:
                code = currency.get('currency_code')
                change_info = rate_service.calculate_rate_change(code, period_days)
                
                change_percent = abs(change_info.get('change_percent', 0))
                
                # Si el cambio es mayor al umbral, crear alerta
                if change_percent >= threshold:
                    direction = change_info.get('direction', 'stable')
                    
                    # Determinar severidad
                    if change_percent >= 10.0:
                        severity = 'high'
                        alert_type = 'danger'
                    elif change_percent >= 7.0:
                        severity = 'medium'
                        alert_type = 'warning'
                    else:
                        severity = 'low'
                        alert_type = 'info'
                    
                    alerts.append({
                        'currency_code': code,
                        'currency_name': currency.get('name', code),
                        'change_percent': change_info.get('change_percent', 0),
                        'direction': direction,
                        'current_rate': change_info.get('current_rate', 0),
                        'previous_rate': change_info.get('previous_rate', 0),
                        'severity': severity,
                        'alert_type': alert_type,
                        'period_days': period_days,
                        'threshold': threshold,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Ordenar por severidad y porcentaje de cambio
            alerts.sort(key=lambda x: (
                0 if x['severity'] == 'high' else 1 if x['severity'] == 'medium' else 2,
                -abs(x['change_percent'])
            ))
            
            return JsonResponse({
                'success': True,
                'alerts': alerts,
                'total_alerts': len(alerts),
                'threshold': threshold,
                'period_days': period_days
            })
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class CurrencyHistoryEnhancedView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista mejorada de histórico con alertas y mejor visualización."""
    template_name = 'frontend/catalog/currency_history_enhanced.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        currency_code = self.kwargs.get('currency_code')
        days = int(self.request.GET.get('days', 30))
        show_alerts = self.request.GET.get('alerts', 'true') == 'true'
        
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
            
            # Calcular estadísticas avanzadas
            stats = {}
            if history:
                rates = [h['rate'] for h in history]
                sorted_rates = sorted(rates)
                
                # Estadísticas básicas
                stats = {
                    'min_rate': min(rates),
                    'max_rate': max(rates),
                    'avg_rate': sum(rates) / len(rates),
                    'current_rate': rates[0] if rates else 0,
                    'median_rate': sorted_rates[len(sorted_rates) // 2] if sorted_rates else 0,
                    'volatility': max(rates) - min(rates),
                    'volatility_percent': ((max(rates) - min(rates)) / min(rates) * 100) if min(rates) > 0 else 0
                }
                
                # Calcular tendencia
                if len(rates) > 1:
                    first_half = rates[:len(rates)//2]
                    second_half = rates[len(rates)//2:]
                    
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)
                    
                    if second_avg > first_avg * 1.02:
                        stats['trend'] = 'up'
                        stats['trend_strength'] = 'strong' if (second_avg / first_avg) > 1.05 else 'moderate'
                    elif second_avg < first_avg * 0.98:
                        stats['trend'] = 'down'
                        stats['trend_strength'] = 'strong' if (second_avg / first_avg) < 0.95 else 'moderate'
                    else:
                        stats['trend'] = 'stable'
                        stats['trend_strength'] = 'weak'
            
            # Obtener alertas si está habilitado
            alerts = []
            if show_alerts:
                change_info = rate_service.calculate_rate_change(currency_code, 7)
                change_percent = abs(change_info.get('change_percent', 0))
                
                if change_percent >= 5.0:
                    alerts.append({
                        'type': 'significant_change',
                        'severity': 'high' if change_percent >= 10 else 'medium',
                        'message': f"Cambio significativo del {change_percent:.2f}% en los últimos 7 días",
                        'change_percent': change_info.get('change_percent', 0),
                        'direction': change_info.get('direction', 'stable')
                    })
                
                if stats.get('volatility_percent', 0) > 10:
                    alerts.append({
                        'type': 'high_volatility',
                        'severity': 'medium',
                        'message': f"Alta volatilidad del {stats['volatility_percent']:.2f}% en el período",
                        'volatility': stats['volatility_percent']
                    })
            
            # Preparar datos para gráfico
            chart_data = {
                'labels': [h['date'] for h in reversed(history)],
                'rates': [h['rate'] for h in reversed(history)]
            }
            
            context.update({
                'currency': currency,
                'currency_code': currency_code,
                'history': history,
                'chart_data': chart_data,
                'stats': stats,
                'alerts': alerts,
                'days': days,
                'show_alerts': show_alerts
            })
            
        except APIException as e:
            logger.error(f"API error: {e}")
            messages.error(self.request, "Error al cargar el histórico.")
            context['currency'] = None
            context['history'] = []
            context['chart_data'] = {'labels': [], 'rates': []}
            context['stats'] = {}
            context['alerts'] = []
        except Exception as e:
            logger.error(f"Error: {e}")
            messages.error(self.request, "Error al cargar el histórico.")
            context['currency'] = None
            context['history'] = []
            context['chart_data'] = {'labels': [], 'rates': []}
            context['stats'] = {}
            context['alerts'] = []
        
        return context
