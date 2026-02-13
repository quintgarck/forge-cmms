"""
ForgeDB API REST - Audit Log Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import AuditLog
from ..serializers import AuditLogSerializer
from ..permissions import CanViewReports


class AuditLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Audit Logs.
    
    Provides read-only access to audit log records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewReports]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['table_name', 'action', 'changed_by']
    search_fields = ['old_values', 'new_values', 'user_agent']
    ordering_fields = ['changed_at', 'table_name', 'action']
    ordering = ['-changed_at']
    
    # Audit logs should be read-only
    http_method_names = ['get', 'head', 'options']
    
    def perform_create(self, serializer):
        """Audit logs are created automatically by the system, not through API"""
        pass