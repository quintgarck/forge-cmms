"""
API view para estadísticas de servicios (AJAX).
"""
import logging
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime, timedelta, date as date_type

from ..services.api_client import APIException
from ..mixins import APIClientMixin
from .service_advanced_views import ServiceDashboardView

logger = logging.getLogger(__name__)


class ServiceStatsAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API view para obtener estadísticas de servicios (AJAX)."""
    
    def get(self, request):
        """Retornar estadísticas de servicios en formato JSON."""
        try:
            # Obtener parámetros
            period = request.GET.get('period', 'today')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Calcular fechas según período
            today = date_type.today()
            
            if period == 'today':
                date_from = today
                date_to = today
            elif period == 'week':
                date_from = today - timedelta(days=7)
                date_to = today
            elif period == 'month':
                date_from = today - timedelta(days=30)
                date_to = today
            elif period == 'custom' and start_date and end_date:
                try:
                    date_from = datetime.strptime(start_date, '%Y-%m-%d').date()
                    date_to = datetime.strptime(end_date, '%Y-%m-%d').date()
                except ValueError:
                    date_from = today - timedelta(days=30)
                    date_to = today
            else:
                date_from = today - timedelta(days=30)
                date_to = today
            
            api_client = self.get_api_client()
            
            # Crear una instancia temporal para acceder a los métodos privados
            dashboard_view = ServiceDashboardView()
            
            # Obtener estadísticas usando los métodos del dashboard view
            stats = {}
            wo_stats = dashboard_view._get_work_order_stats(api_client, date_from, date_to)
            tech_stats = dashboard_view._get_technician_stats(api_client, date_from, date_to)
            service_metrics = dashboard_view._get_service_metrics(api_client, date_from, date_to)
            
            stats.update(wo_stats)
            stats.update(tech_stats)
            stats.update(service_metrics)
            
            return JsonResponse(stats)
            
        except APIException as e:
            logger.error(f"Error getting service stats: {e}")
            return JsonResponse({
                'error': 'Error al obtener estadísticas',
                'message': str(e)
            }, status=500)
        except Exception as e:
            logger.error(f"Unexpected error in ServiceStatsAPIView: {e}")
            return JsonResponse({
                'error': 'Error inesperado',
                'message': str(e)
            }, status=500)
