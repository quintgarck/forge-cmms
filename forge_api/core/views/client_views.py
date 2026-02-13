"""
ForgeDB API REST - Client Views
Automotive Workshop Management System
"""

import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Client, Technician
from ..serializers import ClientSerializer
from ..permissions import CanManageClients

logger = logging.getLogger(__name__)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Clients.

    Provides CRUD operations for client records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]  # Temporarily simplified for testing
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['city', 'state', 'country']
    search_fields = ['name', 'legal_name', 'email', 'phone', 'mobile', 'client_code']
    ordering_fields = ['name', 'created_at', 'updated_at', 'credit_used']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set created_by to current user's ID on creation"""
        # Don't set created_by - let it default to NULL
        # The created_by field references technicians table, not auth_user
        serializer.save()
    
    @action(detail=False, methods=['get'], url_path='check-code')
    def check_code(self, request):
        """
        Check if a client code already exists.
        Returns {'exists': True/False, 'code': 'code_value'}
        """
        code = request.query_params.get('code', '').strip()
        if not code:
            return Response(
                {'error': 'Code parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = Client.objects.filter(client_code=code).exists()
        return Response({'exists': exists, 'code': code})