"""
Notification views for ForgeDB API.

This module provides endpoints for notifications and alerts.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from ..models import Alert

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_list(request):
    """
    Get list of notifications for the current user.
    
    Query Parameters:
        since: ISO datetime string to get notifications since that time
        limit: Maximum number of notifications to return (default: 20)
        unread_only: If true, return only unread notifications
    
    Returns:
        JSON response with notifications list
    """
    try:
        # Get query parameters
        since_param = request.GET.get('since')
        limit = int(request.GET.get('limit', 20))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        
        # Build query
        queryset = Alert.objects.all()
        
        # Filter by date if provided
        if since_param:
            try:
                since_date = datetime.fromisoformat(since_param.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__gte=since_date)
            except ValueError:
                pass  # Ignore invalid date format
        
        # Filter by read status if requested
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        # Order by most recent first and limit results
        notifications = queryset.order_by('-created_at')[:limit]
        
        # Format notifications
        notification_list = []
        for alert in notifications:
            notification_list.append({
                'id': alert.alert_id,
                'title': alert.alert_type or 'Notificación del Sistema',
                'message': alert.message or 'Sin mensaje',
                'severity': getattr(alert, 'severity', 'info').lower(),
                'category': getattr(alert, 'category', 'general'),
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'is_read': getattr(alert, 'is_read', False),
                'action_url': getattr(alert, 'action_url', None),
                'metadata': getattr(alert, 'metadata', {})
            })
        
        return Response({
            'notifications': notification_list,
            'count': len(notification_list),
            'unread_count': len([n for n in notification_list if not n['is_read']]),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Notifications list error: {str(e)}")
        return Response({
            'notifications': [],
            'count': 0,
            'unread_count': 0,
            'error': 'Error al cargar notificaciones',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """
    Mark a specific notification as read.
    
    Args:
        notification_id: ID of the notification to mark as read
    
    Returns:
        JSON response confirming the action
    """
    try:
        alert = Alert.objects.get(alert_id=notification_id)
        
        # Mark as read (if the field exists)
        if hasattr(alert, 'is_read'):
            alert.is_read = True
            alert.save()
        
        return Response({
            'success': True,
            'message': 'Notificación marcada como leída',
            'notification_id': notification_id
        }, status=status.HTTP_200_OK)
        
    except Alert.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Notificación no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Mark notification read error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error al marcar notificación como leída'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """
    Mark all notifications as read for the current user.
    
    Returns:
        JSON response confirming the action
    """
    try:
        # Update all unread notifications
        updated_count = 0
        if hasattr(Alert, 'is_read'):
            updated_count = Alert.objects.filter(is_read=False).update(is_read=True)
        
        return Response({
            'success': True,
            'message': f'{updated_count} notificaciones marcadas como leídas',
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Mark all notifications read error: {str(e)}")
        return Response({
            'success': False,
            'error': 'Error al marcar todas las notificaciones como leídas'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_summary(request):
    """
    Get notification summary with counts by category and severity.
    
    Returns:
        JSON response with notification summary
    """
    try:
        total_notifications = Alert.objects.count()
        unread_notifications = Alert.objects.filter(is_read=False).count() if hasattr(Alert, 'is_read') else 0
        
        # Get recent notifications (last 24 hours)
        recent_cutoff = timezone.now() - timedelta(hours=24)
        recent_notifications = Alert.objects.filter(created_at__gte=recent_cutoff).count()
        
        # Summary by severity (if field exists)
        severity_summary = {}
        try:
            severity_counts = Alert.objects.values('severity').annotate(count=Count('id'))
            for item in severity_counts:
                severity = item['severity'] or 'info'
                severity_summary[severity] = item['count']
        except:
            severity_summary = {'info': total_notifications}
        
        return Response({
            'total': total_notifications,
            'unread': unread_notifications,
            'recent_24h': recent_notifications,
            'by_severity': severity_summary,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Notification summary error: {str(e)}")
        return Response({
            'total': 0,
            'unread': 0,
            'recent_24h': 0,
            'by_severity': {},
            'error': 'Error al obtener resumen de notificaciones'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)