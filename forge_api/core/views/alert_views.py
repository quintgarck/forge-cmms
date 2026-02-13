"""
ForgeDB API REST - Alert Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Alert
from ..serializers import AlertSerializer
from ..permissions import CanViewReports


class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Alerts.
    
    Provides CRUD operations for alert records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewReports]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['alert_type', 'severity', 'status', 'assigned_to']
    search_fields = ['title', 'message', 'ref_code']
    ordering_fields = ['created_at', 'severity', 'resolved_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set created_for to current user on creation if not specified"""
        if not serializer.validated_data.get('created_for'):
            serializer.save(created_for=self.request.user.id)
        else:
            serializer.save()