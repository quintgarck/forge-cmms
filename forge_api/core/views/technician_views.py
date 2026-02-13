"""
ForgeDB API REST - Technician Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Technician
from ..serializers import TechnicianSerializer
from ..permissions import IsWorkshopAdmin


class TechnicianViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Technicians.
    
    Provides CRUD operations for technician records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Technician.objects.all()
    serializer_class = TechnicianSerializer
    
    # Read access for authenticated users, write requires admin
    permission_classes = [permissions.IsAuthenticated]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['employee_code', 'first_name', 'last_name', 'email']
    ordering_fields = ['last_name', 'first_name', 'hire_date', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_permissions(self):
        """
        Override to require admin permissions for write operations
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsWorkshopAdmin()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Save the technician record"""
        serializer.save()