"""
Advanced service management views.
Handles WorkOrder with timeline, WOItem, WOService with real-time tracking,
FlatRateStandard with time calculator, and interactive ServiceChecklist.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.conf import settings
from datetime import datetime, timedelta

from ..services.api_client import ForgeAPIClient, APIException
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class WorkOrderTimelineView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Advanced work order management with visual timeline."""
    template_name = 'frontend/services/workorder_timeline.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wo_id = kwargs.get('wo_id')
        
        try:
            api_client = self.get_api_client()
            
            # Get work order details
            work_order = api_client.get(f'work-orders/{wo_id}/')
            context['work_order'] = work_order
            
            # Process timeline events
            timeline_events = []
            
            # Add creation event
            if work_order.get('created_at'):
                timeline_events.append({
                    'timestamp': work_order['created_at'],
                    'event_type': 'created',
                    'title': 'Orden Creada',
                    'description': f'Orden {work_order.get("wo_number")} creada',
                    'icon': 'bi-plus-circle',
                    'color': 'primary',
                    'user': work_order.get('created_by', {}).get('name', 'Sistema')
                })
            
            # Add scheduled event
            if work_order.get('scheduled_date'):
                timeline_events.append({
                    'timestamp': work_order['scheduled_date'],
                    'event_type': 'scheduled',
                    'title': 'Programada',
                    'description': 'Orden programada para servicio',
                    'icon': 'bi-calendar-check',
                    'color': 'info',
                    'user': work_order.get('assigned_technician', {}).get('name', 'Sistema')
                })
            
            # Add started event
            if work_order.get('started_at'):
                timeline_events.append({
                    'timestamp': work_order['started_at'],
                    'event_type': 'started',
                    'title': 'Iniciada',
                    'description': 'Trabajo iniciado por técnico',
                    'icon': 'bi-play-circle',
                    'color': 'warning',
                    'user': work_order.get('assigned_technician', {}).get('name', 'Técnico')
                })
            
            # Add completed event
            if work_order.get('completed_at'):
                timeline_events.append({
                    'timestamp': work_order['completed_at'],
                    'event_type': 'completed',
                    'title': 'Completada',
                    'description': 'Trabajo completado exitosamente',
                    'icon': 'bi-check-circle',
                    'color': 'success',
                    'user': work_order.get('assigned_technician', {}).get('name', 'Técnico')
                })
            
            # Sort timeline events by timestamp
            timeline_events.sort(key=lambda x: x['timestamp'])
            context['timeline_events'] = timeline_events
            
            # Get work order services
            try:
                services_data = api_client.get('wo-services/', params={
                    'wo': wo_id
                })
                services = services_data.get('results', [])
                
                # Process services for real-time tracking
                for service in services:
                    # Calculate progress percentage
                    if service.get('completion_status') == 'COMPLETED':
                        service['progress_percent'] = 100
                    elif service.get('completion_status') == 'IN_PROGRESS':
                        service['progress_percent'] = 50
                    else:
                        service['progress_percent'] = 0
                    
                    # Add status styling
                    status = service.get('completion_status', 'PENDING')
                    service['status_class'] = self._get_service_status_class(status)
                    service['status_icon'] = self._get_service_status_icon(status)
                    
                    # Calculate efficiency
                    flat_hours = float(service.get('flat_hours', 0))
                    actual_hours = float(service.get('actual_hours', 0))
                    if flat_hours > 0 and actual_hours > 0:
                        service['efficiency_percent'] = (flat_hours / actual_hours) * 100
                    else:
                        service['efficiency_percent'] = 0
                
                context['services'] = services
            except APIException:
                context['services'] = []
            
            # Get work order items
            try:
                items_data = api_client.get('wo-items/', params={
                    'wo': wo_id
                })
                items = items_data.get('results', [])
                
                # Process items for tracking
                for item in items:
                    # Add status styling
                    status = item.get('status', 'PENDING')
                    item['status_class'] = self._get_item_status_class(status)
                    item['status_icon'] = self._get_item_status_icon(status)
                    
                    # Calculate usage percentage
                    qty_ordered = float(item.get('qty_ordered', 0))
                    qty_used = float(item.get('qty_used', 0))
                    if qty_ordered > 0:
                        item['usage_percent'] = (qty_used / qty_ordered) * 100
                    else:
                        item['usage_percent'] = 0
                
                context['items'] = items
            except APIException:
                context['items'] = []
            
            # Calculate overall progress
            total_services = len(context['services'])
            completed_services = len([s for s in context['services'] if s.get('completion_status') == 'COMPLETED'])
            
            if total_services > 0:
                context['overall_progress'] = (completed_services / total_services) * 100
            else:
                context['overall_progress'] = 0
            
            # Add status information
            status = work_order.get('status', 'draft')
            context['status_info'] = {
                'class': self._get_wo_status_class(status),
                'icon': self._get_wo_status_icon(status),
                'label': status.replace('_', ' ').title()
            }
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar detalles de la orden de trabajo")
            context['work_order'] = None
            context['timeline_events'] = []
            context['services'] = []
            context['items'] = []
            context['overall_progress'] = 0
        
        return context
    
    def _get_service_status_class(self, status):
        """Get Bootstrap class for service status."""
        status_classes = {
            'PENDING': 'secondary',
            'IN_PROGRESS': 'warning',
            'COMPLETED': 'success',
            'SKIPPED': 'danger',
        }
        return status_classes.get(status, 'light')
    
    def _get_service_status_icon(self, status):
        """Get icon for service status."""
        status_icons = {
            'PENDING': 'bi-clock',
            'IN_PROGRESS': 'bi-gear',
            'COMPLETED': 'bi-check-circle',
            'SKIPPED': 'bi-x-circle',
        }
        return status_icons.get(status, 'bi-question-circle')
    
    def _get_item_status_class(self, status):
        """Get Bootstrap class for item status."""
        status_classes = {
            'PENDING': 'secondary',
            'RESERVED': 'info',
            'USED': 'success',
            'RETURNED': 'warning',
            'CANCELLED': 'danger',
        }
        return status_classes.get(status, 'light')
    
    def _get_item_status_icon(self, status):
        """Get icon for item status."""
        status_icons = {
            'PENDING': 'bi-clock',
            'RESERVED': 'bi-bookmark',
            'USED': 'bi-check-circle',
            'RETURNED': 'bi-arrow-return-left',
            'CANCELLED': 'bi-x-circle',
        }
        return status_icons.get(status, 'bi-question-circle')
    
    def _get_wo_status_class(self, status):
        """Get Bootstrap class for work order status."""
        status_classes = {
            'draft': 'secondary',
            'scheduled': 'info',
            'in_progress': 'warning',
            'waiting_parts': 'danger',
            'waiting_approval': 'primary',
            'completed': 'success',
            'invoiced': 'dark',
            'cancelled': 'danger',
        }
        return status_classes.get(status, 'light')
    
    def _get_wo_status_icon(self, status):
        """Get icon for work order status."""
        status_icons = {
            'draft': 'bi-file-earmark',
            'scheduled': 'bi-calendar-check',
            'in_progress': 'bi-gear',
            'waiting_parts': 'bi-box',
            'waiting_approval': 'bi-person-check',
            'completed': 'bi-check-circle',
            'invoiced': 'bi-receipt',
            'cancelled': 'bi-x-circle',
        }
        return status_icons.get(status, 'bi-question-circle')


class FlatRateCalculatorView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Flat rate standard management with time calculator."""
    template_name = 'frontend/services/flat_rate_calculator_v2.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search parameters
        search = self.request.GET.get('search', '').strip()
        equipment_type = self.request.GET.get('equipment_type', '')
        group_code = self.request.GET.get('group_code', '')
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            filters = {}
            if search:
                filters['search'] = search
            if equipment_type:
                filters['equipment_type'] = equipment_type
            if group_code:
                filters['group_code'] = group_code
            
            # Get flat rate standards
            standards_data = api_client.get('flat-rate-standards/', params=filters)
            standards = standards_data.get('results', [])
            
            # Process standards for calculator display
            for standard in standards:
                # Calculate time ranges
                standard_hours = float(standard.get('standard_hours', 0))
                min_hours = float(standard.get('min_hours', standard_hours * 0.8))
                max_hours = float(standard.get('max_hours', standard_hours * 1.2))
                
                standard['time_range'] = {
                    'min': min_hours,
                    'standard': standard_hours,
                    'max': max_hours,
                    'variance': max_hours - min_hours
                }
                
                # Add difficulty styling
                difficulty = standard.get('difficulty_level', 1)
                if difficulty >= 4:
                    standard['difficulty_class'] = 'danger'
                    standard['difficulty_label'] = 'Muy Difícil'
                elif difficulty >= 3:
                    standard['difficulty_class'] = 'warning'
                    standard['difficulty_label'] = 'Difícil'
                elif difficulty >= 2:
                    standard['difficulty_class'] = 'info'
                    standard['difficulty_label'] = 'Moderado'
                else:
                    standard['difficulty_class'] = 'success'
                    standard['difficulty_label'] = 'Fácil'
                
                # Process required tools and skills
                tools = standard.get('required_tools', [])
                skills = standard.get('required_skills', [])
                standard['tools_count'] = len(tools) if isinstance(tools, list) else 0
                standard['skills_count'] = len(skills) if isinstance(skills, list) else 0
            
            context['standards'] = standards
            
            # Get equipment types for filter
            try:
                equipment_types_data = api_client.get('equipment-types/')
                context['equipment_types'] = equipment_types_data.get('results', [])
            except APIException:
                context['equipment_types'] = []
            
            # Get taxonomy groups for filter
            try:
                groups_data = api_client.get('taxonomy-groups/')
                context['taxonomy_groups'] = groups_data.get('results', [])
            except APIException:
                context['taxonomy_groups'] = []
            
            # Filter context
            context['filters'] = {
                'search': search,
                'equipment_type': equipment_type,
                'group_code': group_code,
            }
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar estándares de tiempo")
            context['standards'] = []
            context['equipment_types'] = []
            context['taxonomy_groups'] = []
            context['filters'] = {
                'search': search,
                'equipment_type': equipment_type,
                'group_code': group_code,
            }
        
        return context


class ServiceChecklistInteractiveView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Interactive service checklist with mandatory validation."""
    template_name = 'frontend/services/service_checklist_interactive.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        flat_rate_id = kwargs.get('flat_rate_id')
        wo_service_id = kwargs.get('wo_service_id', None)
        
        try:
            api_client = self.get_api_client()
            
            # Get flat rate standard details
            flat_rate = api_client.get(f'flat-rate-standards/{flat_rate_id}/')
            context['flat_rate'] = flat_rate
            
            # Get service checklist items
            checklist_data = api_client.get('service-checklists/', params={
                'flat_rate': flat_rate_id
            })
            checklist_items = checklist_data.get('results', [])
            
            # Process checklist items for interactive display
            total_items = len(checklist_items)
            critical_items = len([item for item in checklist_items if item.get('is_critical')])
            total_time = sum(item.get('estimated_minutes', 0) for item in checklist_items)
            
            # Group items by sequence for better organization
            for item in checklist_items:
                # Add styling based on criticality
                if item.get('is_critical'):
                    item['criticality_class'] = 'danger'
                    item['criticality_icon'] = 'bi-exclamation-triangle-fill'
                    item['criticality_label'] = 'Crítico'
                else:
                    item['criticality_class'] = 'info'
                    item['criticality_icon'] = 'bi-info-circle'
                    item['criticality_label'] = 'Normal'
                
                # Add time estimation styling
                minutes = item.get('estimated_minutes', 0)
                if minutes > 30:
                    item['time_class'] = 'warning'
                elif minutes > 15:
                    item['time_class'] = 'info'
                else:
                    item['time_class'] = 'success'
                
                # Format time display
                if minutes >= 60:
                    hours = minutes // 60
                    mins = minutes % 60
                    item['time_display'] = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
                else:
                    item['time_display'] = f"{minutes}m"
            
            context['checklist_items'] = checklist_items
            context['checklist_stats'] = {
                'total_items': total_items,
                'critical_items': critical_items,
                'total_time_minutes': total_time,
                'total_time_hours': total_time / 60,
                'completion_percentage': 0  # Will be updated via JavaScript
            }
            
            # If this is for a specific work order service, get completion status
            if wo_service_id:
                try:
                    wo_service = api_client.get(f'wo-services/{wo_service_id}/')
                    context['wo_service'] = wo_service
                    
                    # Get checklist completion status (would need additional API endpoint)
                    # For now, simulate completion status
                    context['checklist_completion'] = {}
                except APIException:
                    context['wo_service'] = None
                    context['checklist_completion'] = {}
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar checklist de servicio")
            context['flat_rate'] = None
            context['checklist_items'] = []
            context['checklist_stats'] = {
                'total_items': 0,
                'critical_items': 0,
                'total_time_minutes': 0,
                'total_time_hours': 0,
                'completion_percentage': 0
            }
        
        return context


class ServiceDashboardView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Comprehensive service management dashboard with KPIs and real-time updates."""
    template_name = 'frontend/services/service_dashboard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener parámetros de fecha del request
        period = self.request.GET.get('period', 'today')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        
            # Calcular fechas según período
        from datetime import timedelta, date as date_type
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
        
        context['period'] = period
        context['date_from'] = date_from.strftime('%Y-%m-%d')
        context['date_to'] = date_to.strftime('%Y-%m-%d')
        
        try:
            api_client = self.get_api_client()
            
            # Obtener estadísticas de órdenes de trabajo
            context.update(self._get_work_order_stats(api_client, date_from, date_to))
            
            # Obtener estadísticas de técnicos
            context.update(self._get_technician_stats(api_client, date_from, date_to))
            
            # Obtener métricas de servicio
            context.update(self._get_service_metrics(api_client, date_from, date_to))
            
            # Obtener órdenes recientes
            context['recent_work_orders'] = self._get_recent_work_orders(api_client)
            
        except APIException as e:
            logger.error(f"Error loading service dashboard: {e}")
            self.handle_api_error(e, "Error al cargar dashboard de servicios")
            context.update(self._get_empty_context())
        
        return context
    
    def _get_work_order_stats(self, api_client, date_from, date_to):
        """Obtener estadísticas de órdenes de trabajo."""
        stats = {
            'work_order_stats': {
                'total_active': 0,
                'completed_today': 0,
                'completed_period': 0,
                'scheduled': 0,
                'in_progress': 0,
                'by_status': {}
            }
        }
        
        try:
            # Órdenes activas (excluyendo completadas y canceladas)
            active_params = {'page_size': 1, 'exclude_status': 'completed,cancelled,invoiced'}
            active_data = api_client.get('work-orders/', params=active_params)
            stats['work_order_stats']['total_active'] = active_data.get('count', 0)
            
            # Órdenes completadas hoy
            from datetime import date as date_type
            today = date_type.today()
            completed_today_params = {
                'status': 'completed',
                'completed_date__gte': today.isoformat(),
                'completed_date__lte': today.isoformat(),
                'page_size': 1
            }
            try:
                completed_today_data = api_client.get('work-orders/', params=completed_today_params)
                stats['work_order_stats']['completed_today'] = completed_today_data.get('count', 0)
            except:
                stats['work_order_stats']['completed_today'] = 0
            
            # Órdenes completadas en el período
            completed_period_params = {
                'status': 'completed',
                'completed_date__gte': date_from.isoformat(),
                'completed_date__lte': date_to.isoformat(),
                'page_size': 1
            }
            try:
                completed_period_data = api_client.get('work-orders/', params=completed_period_params)
                stats['work_order_stats']['completed_period'] = completed_period_data.get('count', 0)
            except:
                stats['work_order_stats']['completed_period'] = 0
            
            # Contar por estado
            status_counts = {}
            for status in ['draft', 'scheduled', 'in_progress', 'waiting_parts', 'completed']:
                try:
                    status_data = api_client.get('work-orders/', params={
                        'status': status,
                        'page_size': 1
                    })
                    status_counts[status] = status_data.get('count', 0)
                except APIException:
                    status_counts[status] = 0
            
            stats['work_order_stats']['by_status'] = status_counts
            stats['work_order_stats']['scheduled'] = status_counts.get('scheduled', 0)
            stats['work_order_stats']['in_progress'] = status_counts.get('in_progress', 0)
            
        except APIException:
            pass
        
        return stats
    
    def _get_technician_stats(self, api_client, date_from, date_to):
        """Obtener estadísticas de técnicos."""
        stats = {
            'top_technicians': [],
            'active_technicians_count': 0
        }
        
        try:
            technicians_data = api_client.get('technicians/', params={'is_active': True, 'page_size': 100})
            technicians = technicians_data.get('results', [])
            
            # Filtrar técnicos activos
            active_technicians = [t for t in technicians if t.get('is_active', False)]
            stats['active_technicians_count'] = len(active_technicians)
            
            # Calcular métricas básicas (simplificado - idealmente desde API de métricas)
            for tech in active_technicians[:5]:
                tech['active_orders'] = 0  # Se calcularía desde API de métricas
                tech['completed_wo'] = 0
                tech['efficiency'] = 0
            
            stats['top_technicians'] = active_technicians[:5]
            
        except APIException:
            pass
        
        return stats
    
    def _get_service_metrics(self, api_client, date_from, date_to):
        """Obtener métricas de servicio."""
        from datetime import datetime
        
        metrics = {
            'service_metrics': {
                'avg_completion_time': 0.0,
                'total_revenue': 0.0,
                'completion_rate': 0.0,
                'customer_satisfaction': 0.0
            }
        }
        
        try:
            # Intentar obtener métricas desde API (si existe endpoint específico)
            try:
                metrics_data = api_client.get('services/metrics/', params={
                    'date_from': date_from.isoformat(),
                    'date_to': date_to.isoformat()
                })
                metrics['service_metrics'].update(metrics_data)
            except APIException:
                # Calcular métricas básicas desde órdenes de trabajo
                completed_params = {
                    'status': 'completed',
                    'completed_date__gte': date_from.isoformat(),
                    'completed_date__lte': date_to.isoformat(),
                    'page_size': 100
                }
                
                try:
                    completed_data = api_client.get('work-orders/', params=completed_params)
                    completed_orders = completed_data.get('results', [])
                    total_count = completed_data.get('count', 0)
                    
                    # Calcular ingresos totales (simplificado)
                    total_revenue = 0.0
                    total_hours = 0.0
                    
                    for wo in completed_orders:
                        # Sumar total si está disponible
                        if wo.get('total'):
                            total_revenue += float(wo.get('total', 0))
                        
                        # Calcular tiempo promedio (simplificado)
                        if wo.get('completed_date') and wo.get('created_at'):
                            try:
                                created = datetime.fromisoformat(wo['created_at'].replace('Z', '+00:00'))
                                completed = datetime.fromisoformat(wo['completed_date'].replace('Z', '+00:00'))
                                diff = (completed - created).total_seconds() / 3600 / 24  # días
                                total_hours += diff
                            except:
                                pass
                    
                    metrics['service_metrics']['total_revenue'] = round(total_revenue, 2)
                    
                    if total_count > 0:
                        metrics['service_metrics']['avg_completion_time'] = round(total_hours / total_count, 2) if total_hours > 0 else 0.0
                    
                    # Calcular tasa de completación
                    all_orders_params = {
                        'created_at__gte': date_from.isoformat(),
                        'created_at__lte': date_to.isoformat(),
                        'page_size': 1
                    }
                    try:
                        all_orders_data = api_client.get('work-orders/', params=all_orders_params)
                        all_count = all_orders_data.get('count', 0)
                        if all_count > 0:
                            metrics['service_metrics']['completion_rate'] = round((total_count / all_count) * 100, 1)
                    except:
                        pass
                        
                except APIException:
                    pass
        
        except Exception as e:
            logger.error(f"Error calculating service metrics: {e}")
        
        return metrics
    
    def _get_recent_work_orders(self, api_client, limit=10):
        """Obtener órdenes de trabajo recientes."""
        try:
            recent_wo_data = api_client.get('work-orders/', params={
                'ordering': '-created_at',
                'page_size': limit
            })
            recent_work_orders = recent_wo_data.get('results', [])
            
            # Procesar para mostrar en dashboard
            for wo in recent_work_orders:
                status = wo.get('status', 'draft')
                wo['status_class'] = self._get_wo_status_class(status)
                wo['status_icon'] = self._get_wo_status_icon(status)
                wo['wo_number'] = wo.get('wo_number', f"WO-{wo.get('id', '')}")
                wo['client_name'] = wo.get('client_name', 'N/A')
                wo['service_description'] = wo.get('description', 'Sin descripción')
                
            return recent_work_orders
        except APIException:
            return []
    
    def _get_empty_context(self):
        """Retornar contexto vacío para manejo de errores."""
        return {
            'work_order_stats': {
                'total_active': 0,
                'completed_today': 0,
                'completed_period': 0,
                'scheduled': 0,
                'in_progress': 0,
                'by_status': {}
            },
            'top_technicians': [],
            'active_technicians_count': 0,
            'recent_work_orders': [],
            'service_metrics': {
                'avg_completion_time': 0.0,
                'total_revenue': 0.0,
                'completion_rate': 0.0,
                'customer_satisfaction': 0.0
            }
        }
    
    def _get_wo_status_class(self, status):
        """Get Bootstrap class for work order status."""
        status_classes = {
            'draft': 'secondary',
            'scheduled': 'info',
            'in_progress': 'warning',
            'waiting_parts': 'danger',
            'waiting_approval': 'primary',
            'completed': 'success',
            'invoiced': 'dark',
            'cancelled': 'danger',
        }
        return status_classes.get(status, 'light')
    
    def _get_wo_status_icon(self, status):
        """Get icon for work order status."""
        status_icons = {
            'draft': 'bi-file-earmark',
            'scheduled': 'bi-calendar-check',
            'in_progress': 'bi-gear',
            'waiting_parts': 'bi-box',
            'waiting_approval': 'bi-person-check',
            'completed': 'bi-check-circle',
            'invoiced': 'bi-receipt',
            'cancelled': 'bi-x-circle',
        }
        return status_icons.get(status, 'bi-question-circle')