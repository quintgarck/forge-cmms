"""
Dashboard-related frontend views for ForgeDB.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.conf import settings
import logging

from .viewmixins import APIClientMixin
from .services.api_client import APIException


logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Main dashboard view with comprehensive KPI data."""
    template_name = 'frontend/dashboard/dashboard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get comprehensive dashboard data from API
            dashboard_data = api_client.get('dashboard/')
            
            # Core KPIs
            context.update({
                'active_work_orders': dashboard_data.get('active_work_orders', 0),
                'pending_invoices': dashboard_data.get('pending_invoices', 0),
                'low_stock_items': dashboard_data.get('low_stock_items', 0),
                'technician_productivity': dashboard_data.get('technician_productivity', 0),
                
                # Enhanced metrics
                'workorders_trend': dashboard_data.get('workorders_trend', 0),
                'overdue_invoices': dashboard_data.get('overdue_invoices', 0),
                'critical_stock': dashboard_data.get('critical_stock', 0),
                'avg_completion_days': dashboard_data.get('avg_completion_days', 0),
                'monthly_revenue': dashboard_data.get('monthly_revenue', 0),
                'revenue_trend': dashboard_data.get('revenue_trend', 0),
                'outstanding_receivables': dashboard_data.get('outstanding_receivables', 0),
                'equipment_utilization': dashboard_data.get('equipment_utilization', 0),
                'client_satisfaction': dashboard_data.get('client_satisfaction', 0),
                
                # Alerts and notifications
                'recent_alerts': dashboard_data.get('recent_alerts', []),
                'alert_count': dashboard_data.get('alert_count', 0),
                
                # Chart data
                'charts': dashboard_data.get('charts', {}),
                
                # Top performers
                'top_clients': dashboard_data.get('top_clients', []),
                'top_technicians': dashboard_data.get('top_technicians', []),
                'inventory_alerts': dashboard_data.get('inventory_alerts', []),
                
                # Summary statistics
                'summary': dashboard_data.get('summary', {}),
                
                # Metadata
                'last_updated': dashboard_data.get('last_updated'),
                'data_freshness': dashboard_data.get('data_freshness', 'real-time'),
                'period': dashboard_data.get('period', {})
            })
            
        except APIException as e:
            logger.error(f"Dashboard API error: {e}")
            
            # Show user-friendly error message based on error type
            if e.status_code == 500:
                messages.warning(
                    self.request, 
                    "El backend API está experimentando problemas técnicos. Mostrando datos de demostración."
                )
            elif e.status_code == 401:
                messages.error(
                    self.request,
                    "Su sesión ha expirado. Por favor, inicie sesión nuevamente."
                )
            else:
                messages.info(
                    self.request,
                    "No se pudieron cargar los datos del dashboard. Mostrando información de demostración."
                )
            
            # Fallback data if API is not available
            context.update({
                'active_work_orders': 0,
                'pending_invoices': 0,
                'low_stock_items': 0,
                'technician_productivity': 0,
                'workorders_trend': 0,
                'overdue_invoices': 0,
                'critical_stock': 0,
                'avg_completion_days': 0,
                'monthly_revenue': 0,
                'revenue_trend': 0,
                'outstanding_receivables': 0,
                'equipment_utilization': 0,
                'client_satisfaction': 0,
                'recent_alerts': [],
                'alert_count': 0,
                'charts': {},
                'top_clients': [],
                'top_technicians': [],
                'inventory_alerts': [],
                'summary': {},
                'last_updated': None,
                'data_freshness': 'offline',
                'period': {}
            })
        
        return context


class DashboardDataView(LoginRequiredMixin, APIClientMixin, View):
    """API endpoint for dashboard data (AJAX)."""
    
    def get(self, request, *args, **kwargs):
        try:
            api_client = self.get_api_client()
            data = api_client.get('dashboard/')
            return JsonResponse(data)
        except APIException as e:
            logger.error(f"DashboardDataView API error: {e}", exc_info=True)
            return JsonResponse({
                'error': str(e),
                'message': e.message if hasattr(e, 'message') else str(e),
                'status_code': e.status_code if hasattr(e, 'status_code') else 500
            }, status=e.status_code if hasattr(e, 'status_code') else 500)
        except Exception as e:
            logger.error(f"DashboardDataView unexpected error: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Error interno del servidor',
                'message': str(e) if settings.DEBUG else 'Error al obtener datos del dashboard',
                'status_code': 500
            }, status=500)


class KPIDetailsView(LoginRequiredMixin, APIClientMixin, View):
    """API endpoint for KPI details (AJAX)."""
    
    def get(self, request, kpi_type, *args, **kwargs):
        try:
            api_client = self.get_api_client()
            data = api_client.get(f'dashboard/kpi/{kpi_type}/')
            return JsonResponse(data)
        except APIException as e:
            return JsonResponse({'error': str(e)}, status=500)
