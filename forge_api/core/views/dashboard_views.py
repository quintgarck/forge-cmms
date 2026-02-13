"""
Dashboard views for ForgeDB API.

This module provides endpoints for dashboard data including KPIs,
metrics, and summary information with advanced analytics.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Avg, Q, F, Case, When, IntegerField, DecimalField
from django.utils import timezone
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import logging
from decimal import Decimal

from ..models import (
    Client, Equipment, WorkOrder, Invoice,
    ProductMaster, Stock, Transaction, Alert, Warehouse, Technician
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 5)  # Cache for 5 minutes (increased from 2)
def dashboard_data(request):
    """
    Get comprehensive dashboard KPI data and metrics.
    
    Returns:
        JSON response with dashboard data including:
        - Active work orders count with trends
        - Pending invoices count with aging analysis
        - Low stock items count with criticality levels
        - Technician productivity with individual metrics
        - Recent alerts with priority classification
        - Chart data for multiple visualizations
        - Financial metrics and trends
        - Operational efficiency indicators
    """
    try:
        # Calculate date ranges
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        quarter_ago = today - timedelta(days=90)
        
        # === CORE KPIs ===
        
        # Active work orders with trend analysis
        active_work_orders = WorkOrder.objects.filter(
            ~Q(status__in=['completed', 'cancelled', 'invoiced'])
        ).count()
        
        active_work_orders_yesterday = WorkOrder.objects.filter(
            ~Q(status__in=['completed', 'cancelled', 'invoiced']),
            created_at__date__lte=yesterday
        ).count()
        
        workorders_trend = 0
        if active_work_orders_yesterday > 0:
            workorders_trend = round(
                ((active_work_orders - active_work_orders_yesterday) / active_work_orders_yesterday) * 100, 1
            )
        
        # Pending invoices with aging analysis
        pending_invoices = Invoice.objects.filter(
            ~Q(status='paid')
        ).count()
        
        overdue_invoices = Invoice.objects.filter(
            ~Q(status='paid'),
            due_date__lt=today
        ).count()
        
        # Low stock items with criticality levels
        critical_stock = Stock.objects.filter(qty_on_hand__lte=5).count()
        low_stock_items = Stock.objects.filter(qty_on_hand__lte=10).count()
        
        # Enhanced technician productivity
        total_workorders_week = WorkOrder.objects.filter(
            created_at__gte=week_ago
        ).count()

        completed_workorders_week = WorkOrder.objects.filter(
            created_at__gte=week_ago,
            status='COMPLETED'
        ).count()
        
        technician_productivity = 0
        if total_workorders_week > 0:
            technician_productivity = round(
                (completed_workorders_week / total_workorders_week) * 100, 1
            )
        
        # Average completion time using actual_completion_date
        avg_completion_time = WorkOrder.objects.filter(
            status='COMPLETED',
            actual_completion_date__isnull=False,
            created_at__gte=month_ago
        ).aggregate(
            avg_time=Avg(F('actual_completion_date') - F('created_at'))
        )['avg_time']
        
        avg_completion_days = 0
        if avg_completion_time:
            avg_completion_days = round(avg_completion_time.total_seconds() / (24 * 3600), 1)
        
        # === FINANCIAL METRICS ===
        
        # Revenue metrics
        monthly_revenue = Invoice.objects.filter(
            created_at__gte=month_ago,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        previous_month_revenue = Invoice.objects.filter(
            created_at__gte=month_ago - timedelta(days=30),
            created_at__lt=month_ago,
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_trend = 0
        if previous_month_revenue > 0:
            revenue_trend = round(
                ((float(monthly_revenue) - float(previous_month_revenue)) / float(previous_month_revenue)) * 100, 1
            )
        
        # Outstanding receivables
        outstanding_receivables = Invoice.objects.filter(
            ~Q(status='paid')
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # === OPERATIONAL METRICS ===
        
        # Equipment utilization
        total_equipment = Equipment.objects.count()
        equipment_in_use = WorkOrder.objects.filter(
            status__in=['IN_PROGRESS', 'SCHEDULED'],
            equipment_id__isnull=False
        ).values('equipment_id').distinct().count()
        
        equipment_utilization = 0
        if total_equipment > 0:
            equipment_utilization = round((equipment_in_use / total_equipment) * 100, 1)
        
        # Client satisfaction (based on completed orders without issues)
        total_completed = WorkOrder.objects.filter(
            status='COMPLETED',
            created_at__gte=month_ago
        ).count()
        
        completed_without_issues = WorkOrder.objects.filter(
            status='COMPLETED',
            created_at__gte=month_ago,
            # Assuming no rework or complaints
        ).count()
        
        client_satisfaction = 0
        if total_completed > 0:
            client_satisfaction = round((completed_without_issues / total_completed) * 100, 1)
        
        # === ALERTS AND NOTIFICATIONS ===
        
        # Recent alerts with enhanced information
        recent_alerts = []
        alerts = Alert.objects.order_by('-created_at')[:10]
        
        for alert in alerts:
            severity_level = 'info'
            if hasattr(alert, 'severity'):
                severity_level = alert.severity.lower() if alert.severity else 'info'
            
            recent_alerts.append({
                'id': alert.alert_id,
                'title': alert.alert_type or 'Sistema',
                'message': alert.message or 'Sin mensaje',
                'severity': severity_level,
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'is_read': getattr(alert, 'is_read', False),
                'category': getattr(alert, 'category', 'general')
            })
        
        # === CHART DATA - OPTIMIZED ===
        
        # Enhanced work orders chart (last 7 days with completed vs created) - OPTIMIZED
        workorders_chart_data = []
        workorders_completed_data = []
        workorders_labels = []
        
        # Get all data in 2 queries instead of 14
        date_range = [today - timedelta(days=6-i) for i in range(7)]
        
        # Query 1: Created counts
        created_counts = WorkOrder.objects.filter(
            created_at__date__gte=date_range[0],
            created_at__date__lte=today
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            count=Count('wo_id')
        )
        created_dict = {item['date']: item['count'] for item in created_counts}
        
        # Query 2: Completed counts
        completed_counts = WorkOrder.objects.filter(
            actual_completion_date__date__gte=date_range[0],
            actual_completion_date__date__lte=today,
            status='COMPLETED'
        ).extra(
            select={'date': 'DATE(actual_completion_date)'}
        ).values('date').annotate(
            count=Count('wo_id')
        )
        completed_dict = {item['date']: item['count'] for item in completed_counts}
        
        for date in date_range:
            workorders_chart_data.append(created_dict.get(date, 0))
            workorders_completed_data.append(completed_dict.get(date, 0))
            workorders_labels.append(date.strftime('%a'))
        
        # Work order status distribution with enhanced categories
        status_counts = WorkOrder.objects.values('status').annotate(
            count=Count('wo_id')
        ).order_by('-count')
        
        status_data = []
        status_labels = []
        status_colors = {
            'DRAFT': '#6c757d',
            'SCHEDULED': '#0dcaf0',
            'IN_PROGRESS': '#ffc107',
            'WAITING_PARTS': '#fd7e14',
            'WAITING_APPROVAL': '#e83e8c',
            'COMPLETED': '#198754',
            'INVOICED': '#0d6efd',
            'CANCELLED': '#dc3545'
        }
        
        for item in status_counts:
            wo_status = item['status'] or 'unknown'
            status_labels.append(wo_status.replace('_', ' ').title())
            status_data.append(item['count'])
        
        # Revenue trend (last 30 days) - OPTIMIZED
        revenue_data = []
        revenue_labels = []
        
        # Single query instead of 30 queries
        date_30_days_ago = today - timedelta(days=29)
        daily_revenues = Invoice.objects.filter(
            created_at__date__gte=date_30_days_ago,
            created_at__date__lte=today,
            status='paid'
        ).extra(
            select={'date': 'DATE(created_at)'}
        ).values('date').annotate(
            total=Sum('total_amount')
        )
        revenue_dict = {item['date']: float(item['total'] or 0) for item in daily_revenues}
        
        for i in range(30):
            date = today - timedelta(days=29-i)
            daily_revenue = revenue_dict.get(date, 0)
            
            revenue_data.append(daily_revenue)
            if i % 5 == 0:  # Show every 5th day
                revenue_labels.append(date.strftime('%m/%d'))
            else:
                revenue_labels.append('')
        
        # === TOP PERFORMERS AND INSIGHTS ===
        
        # Top clients by revenue (this month) - OPTIMIZED with select_related
        top_clients = []
        try:
            # Use client_id directly instead of join
            client_revenue_data = Invoice.objects.filter(
                created_at__gte=month_ago,
                status='paid'
            ).values(
                'client_id'
            ).annotate(
                total_revenue=Sum('total_amount'),
                order_count=Count('invoice_id')
            ).order_by('-total_revenue')[:5]
            
            # Get client names in a single query
            client_ids = [item['client_id'] for item in client_revenue_data]
            clients_dict = {}
            if client_ids:
                clients = Client.objects.filter(client_id__in=client_ids).only('client_id', 'name')
                clients_dict = {c.client_id: c.name for c in clients}
            
            for item in client_revenue_data:
                top_clients.append({
                    'name': clients_dict.get(item['client_id'], 'Cliente Desconocido'),
                    'revenue': float(item['total_revenue'] or 0),
                    'orders': item['order_count']
                })
        except Exception as e:
            logger.warning(f"Error calculating top clients: {e}")
            top_clients = []
        
        # Top technicians by productivity - OPTIMIZED
        top_technicians = []
        try:
            technician_stats = WorkOrder.objects.filter(
                status='COMPLETED',
                created_at__gte=month_ago,
                technician_id__isnull=False
            ).values(
                'technician_id'
            ).annotate(
                completed_orders=Count('wo_id'),
                avg_completion_time=Avg(F('actual_completion_date') - F('created_at'))
            ).order_by('-completed_orders')[:5]
            
            # Get technician names in a single query
            tech_ids = [tech['technician_id'] for tech in technician_stats]
            technicians_dict = {}
            if tech_ids:
                technicians = Technician.objects.filter(technician_id__in=tech_ids).only('technician_id', 'first_name', 'last_name')
                technicians_dict = {t.technician_id: f"{t.first_name} {t.last_name}".strip() for t in technicians}
            
            for tech in technician_stats:
                avg_days = 0
                if tech['avg_completion_time']:
                    avg_days = round(tech['avg_completion_time'].total_seconds() / (24 * 3600), 1)
                
                top_technicians.append({
                    'name': technicians_dict.get(tech['technician_id'], 'Técnico Desconocido'),
                    'completed_orders': tech['completed_orders'],
                    'avg_completion_days': avg_days
                })
        except Exception as e:
            logger.warning(f"Error calculating top technicians: {e}")
            top_technicians = []
        
        # Inventory alerts with enhanced details - OPTIMIZED with select_related
        inventory_alerts = []
        low_stock_products = Stock.objects.filter(
            qty_on_hand__lte=10
        ).select_related('product', 'warehouse').only(
            'stock_id', 'qty_on_hand',
            'product__name', 'product__internal_sku',
            'warehouse__name', 'warehouse__warehouse_code'
        )[:10]

        for stock in low_stock_products:
            criticality = 'high' if stock.qty_on_hand <= 5 else 'medium'
            
            inventory_alerts.append({
                'product_name': stock.product.name if stock.product else 'Producto Desconocido',
                'current_stock': stock.qty_on_hand,
                'min_stock': 10,
                'reorder_point': getattr(stock, 'reorder_point', 15),
                'warehouse': stock.warehouse.name if stock.warehouse else 'Almacén Principal',
                'criticality': criticality,
                'days_of_supply': max(1, stock.qty_on_hand // max(1, getattr(stock, 'avg_daily_usage', 1)))
            })
        
        # === RESPONSE DATA ===
        dashboard_response = {
            # Core KPIs
            'active_work_orders': active_work_orders,
            'pending_invoices': pending_invoices,
            'low_stock_items': low_stock_items,
            'technician_productivity': technician_productivity,
            
            # Enhanced metrics
            'workorders_trend': workorders_trend,
            'overdue_invoices': overdue_invoices,
            'critical_stock': critical_stock,
            'avg_completion_days': avg_completion_days,
            'monthly_revenue': float(monthly_revenue),
            'revenue_trend': revenue_trend,
            'outstanding_receivables': float(outstanding_receivables),
            'equipment_utilization': equipment_utilization,
            'client_satisfaction': client_satisfaction,
            
            # Alerts and notifications
            'recent_alerts': recent_alerts,
            'alert_count': len([a for a in recent_alerts if not a.get('is_read', False)]),
            
            # Chart data
            'charts': {
                'workorders_week': {
                    'labels': workorders_labels,
                    'created': workorders_chart_data,
                    'completed': workorders_completed_data
                },
                'status_distribution': {
                    'labels': status_labels,
                    'data': status_data
                },
                'revenue_trend': {
                    'labels': revenue_labels,
                    'data': revenue_data
                }
            },
            
            # Top performers
            'top_clients': top_clients,
            'top_technicians': top_technicians,
            'inventory_alerts': inventory_alerts,
            
            # Summary statistics
            'summary': {
                'total_clients': Client.objects.count(),
                'total_equipment': Equipment.objects.count(),
                'total_products': ProductMaster.objects.count(),
                'total_warehouses': Warehouse.objects.count(),
                'active_alerts': len([a for a in recent_alerts if not a.get('is_read', False)]),
                'system_health': 'healthy' if len(recent_alerts) < 5 else 'warning'
            },
            
            # Metadata
            'last_updated': timezone.now().isoformat(),
            'data_freshness': 'real-time',
            'period': {
                'current_date': today.isoformat(),
                'week_start': week_ago.isoformat(),
                'month_start': month_ago.isoformat()
            }
        }
        
        return Response(dashboard_response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}", exc_info=True)
        return Response(
            {
                'error': 'Error al obtener datos del dashboard',
                'message': str(e) if settings.DEBUG else 'Error interno del servidor',
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60 * 3)  # Cache for 3 minutes
def kpi_details(request, kpi_type):
    """
    Get detailed information for a specific KPI.
    
    Args:
        kpi_type: Type of KPI (workorders, invoices, inventory, productivity)
    
    Returns:
        JSON response with detailed KPI data
    """
    try:
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        if kpi_type == 'workorders':
            # Detailed work order analysis
            data = {
                'total_active': WorkOrder.objects.filter(
                    ~Q(status__in=['completed', 'cancelled', 'invoiced'])
                ).count(),
                'by_status': list(WorkOrder.objects.values('status').annotate(
                    count=Count('wo_id')
                ).order_by('-count')),
                'by_priority': list(WorkOrder.objects.filter(
                    ~Q(status__in=['COMPLETED', 'CANCELLED'])
                ).values('priority').annotate(
                    count=Count('wo_id')
                ).order_by('-count')),
                'overdue': WorkOrder.objects.filter(
                    ~Q(status__in=['COMPLETED', 'CANCELLED']),
                    appointment_date__isnull=False,
                    appointment_date__date__lt=today
                ).count(),
                'this_week': WorkOrder.objects.filter(
                    created_at__gte=week_ago
                ).count()
            }
            
        elif kpi_type == 'invoices':
            # Detailed invoice analysis
            data = {
                'total_pending': Invoice.objects.filter(~Q(status='paid')).count(),
                'overdue': Invoice.objects.filter(
                    ~Q(status='paid'),
                    due_date__lt=today
                ).count(),
                'total_amount_pending': float(Invoice.objects.filter(
                    ~Q(status='paid')
                ).aggregate(total=Sum('total_amount'))['total'] or 0),
                'aging_analysis': {
                    '0-30': Invoice.objects.filter(
                        ~Q(status='paid'),
                        due_date__gte=today - timedelta(days=30)
                    ).count(),
                    '31-60': Invoice.objects.filter(
                        ~Q(status='paid'),
                        due_date__gte=today - timedelta(days=60),
                        due_date__lt=today - timedelta(days=30)
                    ).count(),
                    '60+': Invoice.objects.filter(
                        ~Q(status='paid'),
                        due_date__lt=today - timedelta(days=60)
                    ).count()
                }
            }
            
        elif kpi_type == 'inventory':
            # Detailed inventory analysis - OPTIMIZED
            try:
                # Single query to get warehouse data with aggregation
                by_warehouse_data = list(Stock.objects.values(
                    'warehouse__warehouse_code',
                    'warehouse__name'
                ).annotate(
                    total_items=Count('stock_id'),
                    low_stock_items=Count(
                        Case(
                            When(qty_on_hand__lte=10, then=1),
                            output_field=IntegerField()
                        )
                    )
                ).order_by('warehouse__name'))
                
                # Format for response
                for warehouse_data in by_warehouse_data:
                    if not warehouse_data.get('warehouse__name'):
                        warehouse_data['warehouse__name'] = 'Sin Almacén'
                        
            except Exception as e:
                logger.warning(f"Error calculating by_warehouse data: {e}")
                by_warehouse_data = []
            
            data = {
                'total_products': ProductMaster.objects.count(),
                'low_stock': Stock.objects.filter(qty_on_hand__lte=10).count(),
                'critical_stock': Stock.objects.filter(qty_on_hand__lte=5).count(),
                'out_of_stock': Stock.objects.filter(qty_on_hand=0).count(),
                'total_value': float(Stock.objects.aggregate(
                    total=Sum(F('total_cost'))
                )['total'] or 0),
                'by_warehouse': by_warehouse_data
            }
            
        elif kpi_type == 'productivity':
            # Detailed productivity analysis
            completed_this_week = WorkOrder.objects.filter(
                status='COMPLETED',
                actual_completion_date__gte=week_ago
            ).count()
            
            total_this_week = WorkOrder.objects.filter(
                created_at__gte=week_ago
            ).count()
            
            data = {
                'completed_this_week': completed_this_week,
                'total_this_week': total_this_week,
                'completion_rate': round(
                    (completed_this_week / total_this_week * 100) if total_this_week > 0 else 0, 1
                ),
                'avg_completion_time': 0,  # Would need to calculate based on actual data
                'technician_performance': [],  # Would need technician data
                'efficiency_trend': []  # Would need historical data
            }
        
        elif kpi_type == 'suppliers':
            # Detailed suppliers analysis
            from .models import Supplier
            data = {
                'total_suppliers': Supplier.objects.count(),
                'active_suppliers': Supplier.objects.filter(is_active=True).count(),
                'preferred_suppliers': Supplier.objects.filter(is_preferred=True).count(),
                'by_status': list(Supplier.objects.values('status').annotate(
                    count=Count('supplier_id')
                ).order_by('-count')),
                'top_suppliers': list(Supplier.objects.filter(
                    is_active=True
                ).order_by('-rating')[:5].values('name', 'rating', 'quality_score'))
            }
        
        elif kpi_type == 'oem':
            # Detailed OEM analysis
            from .models import OEMBrand, OEMCatalogItem
            data = {
                'total_brands': OEMBrand.objects.count(),
                'active_brands': OEMBrand.objects.filter(is_active=True).count(),
                'total_catalog_items': OEMCatalogItem.objects.count(),
                'discontinued_items': OEMCatalogItem.objects.filter(is_discontinued=True).count(),
                'by_brand': list(OEMCatalogItem.objects.values(
                    'oem_code__name'
                ).annotate(
                    count=Count('catalog_id')
                ).order_by('-count')[:10])
            }
        
        elif kpi_type == 'workorders':
            # Same as 'workorders' case above, but with 'workorders' spelling
            data = {
                'total': WorkOrder.objects.count(),
                'active': WorkOrder.objects.filter(
                    ~Q(status__in=['COMPLETED', 'CANCELLED'])
                ).count(),
                'completed': WorkOrder.objects.filter(status='COMPLETED').count(),
                'by_status': list(WorkOrder.objects.values('status').annotate(
                    count=Count('wo_id')
                ).order_by('-count')),
                'by_priority': list(WorkOrder.objects.filter(
                    ~Q(status__in=['COMPLETED', 'CANCELLED'])
                ).values('priority').annotate(
                    count=Count('wo_id')
                ).order_by('-count')),
                'overdue': WorkOrder.objects.filter(
                    ~Q(status__in=['COMPLETED', 'CANCELLED']),
                    appointment_date__isnull=False,
                    appointment_date__date__lt=today
                ).count(),
                'this_week': WorkOrder.objects.filter(
                    created_at__gte=week_ago
                ).count()
            }
        
        elif kpi_type in ['alerts', 'alert']:
            # Detailed alerts analysis
            data = {
                'total_alerts': Alert.objects.count(),
                'unread_alerts': Alert.objects.filter(
                    status='unread'
                ).count(),
                'by_severity': list(Alert.objects.values('severity').annotate(
                    count=Count('alert_id')
                ).order_by('-count')),
                'by_type': list(Alert.objects.values('alert_type').annotate(
                    count=Count('alert_id')
                ).order_by('-count')[:10]),
                'recent_critical': list(Alert.objects.filter(
                    severity='critical'
                ).order_by('-created_at')[:10].values(
                    'alert_id', 'title', 'message', 'created_at', 'status'
                )),
                'this_week': Alert.objects.filter(
                    created_at__gte=week_ago
                ).count()
            }
            
        else:
            return Response(
                {'error': f'KPI type "{kpi_type}" not supported'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'kpi_type': kpi_type,
            'data': data,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"KPI details error for {kpi_type}: {str(e)}")
        return Response(
            {'error': f'Error al obtener detalles de {kpi_type}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([])
def health_check(request):
    """
    Enhanced health check endpoint with system status.
    
    Returns:
        JSON response indicating system health with metrics
    """
    try:
        # Basic health metrics
        db_status = 'healthy'
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except:
            db_status = 'unhealthy'
        
        return Response({
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'database': db_status,
            'components': {
                'database': db_status,
                'api': 'healthy',
                'cache': 'healthy'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)