"""
Service Alerts Views - Sistema de Alertas del Dashboard de Servicios
Tarea 5.3: Implementar Sistema de Alertas
"""

import logging
from datetime import datetime
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from ..mixins import APIClientMixin
from ..services.api_client import APIException
from ..services.service_alert_service import ServiceAlertService

logger = logging.getLogger(__name__)


class ServiceAlertsAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API para obtener alertas activas del sistema de servicios."""
    
    def get(self, request):
        """Retornar alertas activas en formato JSON."""
        try:
            # Obtener parámetros
            alert_types = request.GET.getlist('types', [])
            severity_filter = request.GET.get('severity', '')
            
            api_client = self.get_api_client()
            user_id = request.user.id if hasattr(request.user, 'id') else None
            alert_service = ServiceAlertService(api_client, user_id=user_id)
            
            # Obtener alertas activas
            alerts = alert_service.get_active_alerts(
                alert_types=alert_types if alert_types else None
            )
            
            # Filtrar por severidad si se especifica
            if severity_filter:
                alerts = [a for a in alerts if a.get('severity') == severity_filter]
            
            # Estadísticas
            stats = {
                'total': len(alerts),
                'by_severity': {
                    'critical': len([a for a in alerts if a.get('severity') == 'critical']),
                    'high': len([a for a in alerts if a.get('severity') == 'high']),
                    'medium': len([a for a in alerts if a.get('severity') == 'medium']),
                    'low': len([a for a in alerts if a.get('severity') == 'low'])
                },
                'by_type': {}
            }
            
            for alert in alerts:
                alert_type = alert.get('type', 'unknown')
                stats['by_type'][alert_type] = stats['by_type'].get(alert_type, 0) + 1
            
            return JsonResponse({
                'success': True,
                'alerts': alerts,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class ServiceAlertsListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista completa de todas las alertas con filtros."""
    template_name = 'frontend/services/service_alerts_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parámetros de filtro
        alert_type = self.request.GET.get('type', '')
        severity = self.request.GET.get('severity', '')
        
        try:
            api_client = self.get_api_client()
            user_id = request.user.id if hasattr(request.user, 'id') else None
            alert_service = ServiceAlertService(api_client, user_id=user_id)
            
            # Obtener alertas
            alert_types = [alert_type] if alert_type else None
            alerts = alert_service.get_active_alerts(alert_types=alert_types)
            
            # Filtrar por severidad
            if severity:
                alerts = [a for a in alerts if a.get('severity') == severity]
            
            context['alerts'] = alerts
            context['filter_type'] = alert_type
            context['filter_severity'] = severity
            
            # Estadísticas
            context['stats'] = {
                'total': len(alerts),
                'critical': len([a for a in alerts if a.get('severity') == 'critical']),
                'high': len([a for a in alerts if a.get('severity') == 'high']),
                'medium': len([a for a in alerts if a.get('severity') == 'medium']),
                'low': len([a for a in alerts if a.get('severity') == 'low'])
            }
            
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")
            messages.error(self.request, "Error al cargar las alertas.")
            context['alerts'] = []
            context['stats'] = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        return context


class ServiceAlertThresholdsView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para configurar umbrales de alertas."""
    template_name = 'frontend/services/service_alert_thresholds.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        api_client = self.get_api_client()
        alert_service = ServiceAlertService(api_client)
        
        context['thresholds'] = alert_service.thresholds
        
        return context
    
    def post(self, request):
        """Actualizar umbrales."""
        try:
            # Obtener valores del formulario
            thresholds = {
                'max_delay_percentage': float(request.POST.get('max_delay_percentage', 20)),
                'max_orders_per_technician': int(request.POST.get('max_orders_per_technician', 5)),
                'time_overrun_multiplier': float(request.POST.get('time_overrun_multiplier', 2.0)),
                'low_stock_percentage': float(request.POST.get('low_stock_percentage', 20)),
                'high_productivity_orders': int(request.POST.get('high_productivity_orders', 3)),
                'delayed_order_hours': float(request.POST.get('delayed_order_hours', 2))
            }
            
            # Validar valores
            if any(v <= 0 for v in thresholds.values()):
                messages.error(request, "Todos los umbrales deben ser mayores a 0.")
                return self.get(request)
            
            # Aquí en una implementación completa se guardarían en la base de datos
            # Por ahora, solo se aplican en la sesión actual
            api_client = self.get_api_client()
            user_id = request.user.id if hasattr(request.user, 'id') else None
            alert_service = ServiceAlertService(api_client, user_id=user_id)
            alert_service.update_thresholds(**thresholds)
            
            messages.success(request, "Umbrales actualizados correctamente.")
            
            context = self.get_context_data()
            context['thresholds'] = thresholds
            return self.render_to_response(context)
            
        except (ValueError, TypeError) as e:
            messages.error(request, f"Error en los valores: {str(e)}")
            return self.get(request)


