"""
API views para datos de gráficos del dashboard de servicios.
"""
import logging
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime, timedelta, date as date_type

from ..services.api_client import APIException
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class ServiceProductivityAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API view para obtener datos de productividad por técnico."""
    
    def get(self, request):
        """Retornar datos de productividad por técnico en formato JSON."""
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
            
            # Obtener técnicos activos
            try:
                technicians_data = api_client.get('technicians/', params={
                    'is_active': True,
                    'page_size': 100
                })
                technicians = technicians_data.get('results', [])
            except APIException:
                technicians = []
            
            # Obtener órdenes completadas en el período
            try:
                completed_params = {
                    'status': 'completed',
                    'completed_date__gte': date_from.isoformat(),
                    'completed_date__lte': date_to.isoformat(),
                    'page_size': 1000
                }
                completed_data = api_client.get('work-orders/', params=completed_params)
                completed_orders = completed_data.get('results', [])
            except APIException:
                completed_orders = []
            
            # Calcular productividad por técnico
            technician_stats = {}
            for tech in technicians:
                tech_id = tech.get('id')
                tech_name = tech.get('name', f"Técnico {tech_id}")
                
                # Filtrar órdenes por técnico (asumiendo que hay un campo technician_id en wo_services)
                tech_orders = [
                    wo for wo in completed_orders 
                    if wo.get('primary_technician_id') == tech_id
                ]
                
                orders_count = len(tech_orders)
                total_hours = sum(float(wo.get('actual_hours', 0)) for wo in tech_orders)
                avg_time = total_hours / orders_count if orders_count > 0 else 0
                
                technician_stats[tech_id] = {
                    'id': tech_id,
                    'name': tech_name,
                    'orders_completed': orders_count,
                    'total_hours': round(total_hours, 2),
                    'avg_time': round(avg_time, 2)
                }
            
            # Ordenar por órdenes completadas (descendente) y tomar top 10
            technicians_list = sorted(
                technician_stats.values(),
                key=lambda x: x['orders_completed'],
                reverse=True
            )[:10]
            
            return JsonResponse({
                'technicians': technicians_list,
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting productivity data: {e}")
            return JsonResponse({
                'error': 'Error al obtener datos de productividad',
                'message': str(e)
            }, status=500)


class ServiceCategoriesAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API view para obtener distribución de servicios por categoría."""
    
    def get(self, request):
        """Retornar distribución de servicios por categoría en formato JSON."""
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
            
            # Obtener órdenes de trabajo en el período
            try:
                wo_params = {
                    'created_at__gte': date_from.isoformat(),
                    'created_at__lte': date_to.isoformat(),
                    'page_size': 1000
                }
                wo_data = api_client.get('work-orders/', params=wo_params)
                work_orders = wo_data.get('results', [])
            except APIException:
                work_orders = []
            
            # Contar por tipo de servicio
            service_types = {
                'PREVENTIVO': 0,
                'CORRECTIVO': 0,
                'DIAGNÓSTICO': 0,
                'GARANTÍA': 0,
                'INSPECCIÓN': 0
            }
            
            for wo in work_orders:
                service_type = wo.get('service_type', '').upper()
                if service_type in service_types:
                    service_types[service_type] += 1
            
            # Calcular porcentajes
            total = sum(service_types.values())
            
            categories = []
            for service_type, count in service_types.items():
                percentage = (count / total * 100) if total > 0 else 0
                categories.append({
                    'name': service_type,
                    'count': count,
                    'percentage': round(percentage, 2)
                })
            
            # Ordenar por cantidad (descendente)
            categories.sort(key=lambda x: x['count'], reverse=True)
            
            return JsonResponse({
                'categories': categories,
                'total': total,
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting categories data: {e}")
            return JsonResponse({
                'error': 'Error al obtener datos de categorías',
                'message': str(e)
            }, status=500)


class ServiceTrendsAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API view para obtener tendencias temporales."""
    
    def get(self, request):
        """Retornar datos de tendencias temporales en formato JSON."""
        try:
            # Obtener parámetros
            period = request.GET.get('period', 'month')
            granularity = request.GET.get('granularity', 'day')  # day, week, month
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Calcular fechas según período
            today = date_type.today()
            
            if period == 'today':
                date_from = today
                date_to = today
                granularity = 'hour'
            elif period == 'week':
                date_from = today - timedelta(days=7)
                date_to = today
                granularity = 'day'
            elif period == 'month':
                date_from = today - timedelta(days=30)
                date_to = today
                granularity = 'day'
            elif period == 'custom' and start_date and end_date:
                try:
                    date_from = datetime.strptime(start_date, '%Y-%m-%d').date()
                    date_to = datetime.strptime(end_date, '%Y-%m-%d').date()
                    # Determinar granularidad basado en rango
                    days_diff = (date_to - date_from).days
                    if days_diff <= 7:
                        granularity = 'day'
                    elif days_diff <= 90:
                        granularity = 'week'
                    else:
                        granularity = 'month'
                except ValueError:
                    date_from = today - timedelta(days=30)
                    date_to = today
                    granularity = 'day'
            else:
                date_from = today - timedelta(days=30)
                date_to = today
                granularity = 'day'
            
            api_client = self.get_api_client()
            
            # Obtener órdenes de trabajo en el período
            try:
                wo_params = {
                    'created_at__gte': date_from.isoformat(),
                    'created_at__lte': date_to.isoformat(),
                    'page_size': 1000
                }
                wo_data = api_client.get('work-orders/', params=wo_params)
                work_orders = wo_data.get('results', [])
            except APIException:
                work_orders = []
            
            # Agrupar por período según granularidad
            trends_data = {}
            
            for wo in work_orders:
                try:
                    created_at = datetime.fromisoformat(
                        wo.get('created_at', '').replace('Z', '+00:00')
                    ).date()
                    
                    # Determinar clave según granularidad
                    if granularity == 'day':
                        key = created_at.isoformat()
                    elif granularity == 'week':
                        # Calcular inicio de semana (lunes)
                        days_since_monday = created_at.weekday()
                        week_start = created_at - timedelta(days=days_since_monday)
                        key = week_start.isoformat()
                    else:  # month
                        key = created_at.strftime('%Y-%m')
                    
                    if key not in trends_data:
                        trends_data[key] = {
                            'completed': 0,
                            'revenue': 0.0,
                            'total_hours': 0.0,
                            'count': 0
                        }
                    
                    # Si está completada, contar
                    if wo.get('status') == 'completed':
                        trends_data[key]['completed'] += 1
                        trends_data[key]['revenue'] += float(wo.get('total', 0) or 0)
                        trends_data[key]['total_hours'] += float(wo.get('actual_hours', 0) or 0)
                    
                    trends_data[key]['count'] += 1
                    
                except (ValueError, TypeError):
                    continue
            
            # Convertir a listas ordenadas
            dates = sorted(trends_data.keys())
            
            completed_series = [trends_data[d]['completed'] for d in dates]
            revenue_series = [round(trends_data[d]['revenue'], 2) for d in dates]
            avg_time_series = [
                round(trends_data[d]['total_hours'] / trends_data[d]['completed'], 2) 
                if trends_data[d]['completed'] > 0 else 0
                for d in dates
            ]
            
            return JsonResponse({
                'dates': dates,
                'series': {
                    'completed': completed_series,
                    'revenue': revenue_series,
                    'avg_time': avg_time_series
                },
                'granularity': granularity,
                'period': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting trends data: {e}")
            return JsonResponse({
                'error': 'Error al obtener datos de tendencias',
                'message': str(e)
            }, status=500)


class ServiceComparisonAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API view para comparar período actual vs anterior."""
    
    def get(self, request):
        """Retornar comparación de períodos en formato JSON."""
        try:
            # Obtener parámetros
            period = request.GET.get('period', 'month')
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            # Calcular fechas según período
            today = date_type.today()
            
            if period == 'today':
                current_from = today
                current_to = today
                previous_from = today - timedelta(days=1)
                previous_to = today - timedelta(days=1)
            elif period == 'week':
                current_from = today - timedelta(days=7)
                current_to = today
                previous_from = current_from - timedelta(days=7)
                previous_to = current_from - timedelta(days=1)
            elif period == 'month':
                current_from = today - timedelta(days=30)
                current_to = today
                previous_from = current_from - timedelta(days=30)
                previous_to = current_from - timedelta(days=1)
            elif period == 'custom' and start_date and end_date:
                try:
                    current_from = datetime.strptime(start_date, '%Y-%m-%d').date()
                    current_to = datetime.strptime(end_date, '%Y-%m-%d').date()
                    days_diff = (current_to - current_from).days
                    previous_to = current_from - timedelta(days=1)
                    previous_from = previous_to - timedelta(days=days_diff)
                except ValueError:
                    current_from = today - timedelta(days=30)
                    current_to = today
                    previous_from = current_from - timedelta(days=30)
                    previous_to = current_from - timedelta(days=1)
            else:
                current_from = today - timedelta(days=30)
                current_to = today
                previous_from = current_from - timedelta(days=30)
                previous_to = current_from - timedelta(days=1)
            
            api_client = self.get_api_client()
            
            def get_period_stats(date_from, date_to):
                """Obtener estadísticas para un período."""
                try:
                    wo_params = {
                        'created_at__gte': date_from.isoformat(),
                        'created_at__lte': date_to.isoformat(),
                        'page_size': 1000
                    }
                    wo_data = api_client.get('work-orders/', params=wo_params)
                    work_orders = wo_data.get('results', [])
                    
                    completed = [wo for wo in work_orders if wo.get('status') == 'completed']
                    
                    return {
                        'completed': len(completed),
                        'revenue': sum(float(wo.get('total', 0) or 0) for wo in completed),
                        'total_hours': sum(float(wo.get('actual_hours', 0) or 0) for wo in completed),
                        'total_orders': len(work_orders)
                    }
                except APIException:
                    return {
                        'completed': 0,
                        'revenue': 0.0,
                        'total_hours': 0.0,
                        'total_orders': 0
                    }
            
            current_stats = get_period_stats(current_from, current_to)
            previous_stats = get_period_stats(previous_from, previous_to)
            
            # Calcular promedios
            current_avg_time = (
                current_stats['total_hours'] / current_stats['completed']
                if current_stats['completed'] > 0 else 0
            )
            previous_avg_time = (
                previous_stats['total_hours'] / previous_stats['completed']
                if previous_stats['completed'] > 0 else 0
            )
            
            # Calcular porcentajes de cambio
            def calc_change(current, previous):
                if previous == 0:
                    return 100.0 if current > 0 else 0.0
                return round(((current - previous) / previous) * 100, 1)
            
            return JsonResponse({
                'current': {
                    'completed': current_stats['completed'],
                    'revenue': round(current_stats['revenue'], 2),
                    'avg_time': round(current_avg_time, 2),
                    'period': {
                        'from': current_from.isoformat(),
                        'to': current_to.isoformat()
                    }
                },
                'previous': {
                    'completed': previous_stats['completed'],
                    'revenue': round(previous_stats['revenue'], 2),
                    'avg_time': round(previous_avg_time, 2),
                    'period': {
                        'from': previous_from.isoformat(),
                        'to': previous_to.isoformat()
                    }
                },
                'changes': {
                    'completed': calc_change(current_stats['completed'], previous_stats['completed']),
                    'revenue': calc_change(current_stats['revenue'], previous_stats['revenue']),
                    'avg_time': calc_change(current_avg_time, previous_avg_time)
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting comparison data: {e}")
            return JsonResponse({
                'error': 'Error al obtener datos de comparación',
                'message': str(e)
            }, status=500)
