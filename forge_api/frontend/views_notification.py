"""
Notification views for ForgeDB frontend.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.urls import reverse_lazy
import logging

from .viewmixins import APIClientMixin
from .services.api_client import APIException


logger = logging.getLogger(__name__)


class NotificationListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista para listar notificaciones."""
    template_name = 'frontend/notifications/notification_list.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Parámetros de búsqueda
            params = {}
            params['limit'] = self.request.GET.get('limit', 50)
            
            # Si se solicita solo no leídas
            unread_only = self.request.GET.get('unread', False)
            if unread_only:
                params['unread_only'] = 'true'
            
            # Desde una fecha específica
            since = self.request.GET.get('since', '')
            if since:
                params['since'] = since
            
            # Obtener notificaciones desde la API
            notifications_data = api_client.get('alerts/', params=params)
            
            if notifications_data and 'results' in notifications_data:
                notifications = notifications_data['results']
            else:
                notifications = notifications_data if isinstance(notifications_data, list) else []
            
            # Procesar notificaciones para mejorar la presentación
            for notification in notifications:
                # Determinar clase CSS según la gravedad
                severity = notification.get('severity', 'info').lower()
                if severity == 'critical':
                    notification['css_class'] = 'alert-danger'
                    notification['icon'] = 'fa-exclamation-circle'
                elif severity == 'high':
                    notification['css_class'] = 'alert-warning'
                    notification['icon'] = 'fa-exclamation-triangle'
                elif severity == 'medium':
                    notification['css_class'] = 'alert-info'
                    notification['icon'] = 'fa-info-circle'
                else:
                    notification['css_class'] = 'alert-secondary'
                    notification['icon'] = 'fa-bell'
            
            context['notifications'] = notifications
            context['total_count'] = len(notifications)
            context['unread_count'] = len([n for n in notifications if not n.get('is_read', True)])
            
        except APIException as e:
            self.handle_api_error(e, "Error al cargar las notificaciones")
            context['notifications'] = []
            context['total_count'] = 0
            context['unread_count'] = 0
        except Exception as e:
            logger.error(f"Unexpected error loading notifications: {str(e)}")
            messages.error(self.request, "Error inesperado al cargar las notificaciones")
            context['notifications'] = []
            context['total_count'] = 0
            context['unread_count'] = 0
        
        # Parámetros actuales para mantener en la paginación y filtros
        context['current_filters'] = {
            'limit': self.request.GET.get('limit', 50),
            'unread': self.request.GET.get('unread', False),
            'since': self.request.GET.get('since', ''),
        }
        
        return context