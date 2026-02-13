"""
ForgeDB API REST - Document Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Document
from ..serializers import DocumentSerializer
from ..permissions import CanViewReports


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Documents.
    
    Provides CRUD operations for document records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewReports]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document_type', 'ref_entity', 'uploaded_by']
    search_fields = ['title', 'description', 'file_name']
    ordering_fields = ['uploaded_at', 'file_size']
    ordering = ['-uploaded_at']
    
    def perform_create(self, serializer):
        """Set uploaded_by to current user on creation"""
        serializer.save(uploaded_by=self.request.user)