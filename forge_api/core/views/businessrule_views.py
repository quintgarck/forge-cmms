"""
ForgeDB API REST - Business Rule Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import BusinessRule
from ..serializers import BusinessRuleSerializer
from ..permissions import IsWorkshopAdmin


class BusinessRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Business Rules.
    
    Provides CRUD operations for business rule records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = BusinessRule.objects.all()
    serializer_class = BusinessRuleSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorkshopAdmin]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['applies_to_schema', 'trigger_event', 'severity', 'is_active']
    search_fields = ['rule_code', 'rule_name', 'condition_text', 'action_text']
    ordering_fields = ['execution_order', 'created_at', 'updated_at']
    ordering = ['execution_order']
    
    def perform_create(self, serializer):
        """Save the business rule record"""
        serializer.save()