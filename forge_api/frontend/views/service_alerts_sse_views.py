"""
Server-Sent Events (SSE) Views for Real-time Alert Notifications
Tarea 5.3: Notificaciones en tiempo real
"""

import json
import time
import logging
from django.http import StreamingHttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from ..mixins import APIClientMixin
from ..services.service_alert_service import ServiceAlertService

logger = logging.getLogger(__name__)


class ServiceAlertsSSEView(LoginRequiredMixin, APIClientMixin, View):
    """
    Server-Sent Events endpoint for real-time alert notifications.
    Streams alerts to clients as they are detected.
    """
    
    def get(self, request):
        """Stream alerts using Server-Sent Events."""
        
        def event_stream():
            """Generator function that yields SSE events."""
            api_client = self.get_api_client()
            user_id = request.user.id if hasattr(request.user, 'id') else None
            alert_service = ServiceAlertService(api_client, user_id=user_id)
            
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': timezone.now().isoformat()})}\n\n"
            
            last_alert_count = 0
            last_alerts_hash = None
            
            while True:
                try:
                    # Get current alerts
                    alerts = alert_service.get_active_alerts()
                    current_count = len(alerts)
                    
                    # Create a simple hash of alert IDs for change detection
                    alerts_hash = hash(tuple(sorted([a.get('id', '') for a in alerts])))
                    
                    # Check if alerts have changed
                    if current_count != last_alert_count or alerts_hash != last_alerts_hash:
                        # Send update event
                        event_data = {
                            'type': 'alerts_update',
                            'count': current_count,
                            'alerts': alerts[:10],  # Send first 10 alerts
                            'timestamp': timezone.now().isoformat(),
                            'stats': {
                                'critical': len([a for a in alerts if a.get('severity') == 'critical']),
                                'high': len([a for a in alerts if a.get('severity') == 'high']),
                                'medium': len([a for a in alerts if a.get('severity') == 'medium']),
                                'low': len([a for a in alerts if a.get('severity') == 'low'])
                            }
                        }
                        yield f"data: {json.dumps(event_data)}\n\n"
                        
                        last_alert_count = current_count
                        last_alerts_hash = alerts_hash
                    else:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': timezone.now().isoformat()})}\n\n"
                    
                    # Wait before next check (poll every 5 seconds)
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    error_data = {
                        'type': 'error',
                        'message': str(e),
                        'timestamp': timezone.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    time.sleep(10)  # Wait longer on error
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
        response['Connection'] = 'keep-alive'
        return response
