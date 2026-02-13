"""
ForgeDB API REST - Catalog Reference Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import (
    Category, EquipmentType, FuelCode, AspirationCode, TransmissionCode, DrivetrainCode,
    ColorCode, PositionCode, FinishCode, SourceCode, ConditionCode, UOMCode, Currency
)
from ..serializers import (
    CategorySerializer, EquipmentTypeSerializer, FuelCodeSerializer, AspirationCodeSerializer,
    TransmissionCodeSerializer, DrivetrainCodeSerializer, ColorCodeSerializer,
    PositionCodeSerializer, FinishCodeSerializer, SourceCodeSerializer,
    ConditionCodeSerializer, UOMCodeSerializer, CurrencySerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['category_code', 'name', 'description']
    ordering_fields = ['sort_order', 'name', 'category_code']
    ordering = ['sort_order', 'name']


class EquipmentTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Equipment Types"""
    queryset = EquipmentType.objects.all()
    serializer_class = EquipmentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['type_code', 'name', 'description']
    ordering_fields = ['category', 'name', 'created_at']
    ordering = ['category', 'name']


class FuelCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Fuel Codes"""
    queryset = FuelCode.objects.all()
    serializer_class = FuelCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['fuel_code', 'name_es', 'name_en']
    ordering = ['fuel_code']


class AspirationCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Aspiration Codes"""
    queryset = AspirationCode.objects.all()
    serializer_class = AspirationCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['aspiration_code', 'name_es', 'name_en']
    ordering = ['aspiration_code']


class TransmissionCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Transmission Codes"""
    queryset = TransmissionCode.objects.all()
    serializer_class = TransmissionCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['transmission_code', 'name_es', 'name_en']
    ordering = ['transmission_code']


class DrivetrainCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Drivetrain Codes"""
    queryset = DrivetrainCode.objects.all()
    serializer_class = DrivetrainCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['drivetrain_code', 'name_es', 'name_en']
    ordering = ['drivetrain_code']


class ColorCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Color Codes"""
    queryset = ColorCode.objects.all()
    serializer_class = ColorCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['brand', 'is_metallic']
    search_fields = ['color_code', 'name_es', 'name_en']
    ordering_fields = ['brand', 'sort_order', 'color_code']
    ordering = ['brand', 'sort_order', 'color_code']


class PositionCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Position Codes"""
    queryset = PositionCode.objects.all()
    serializer_class = PositionCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['position_code', 'name_es', 'name_en']
    ordering_fields = ['sort_order', 'position_code']
    ordering = ['sort_order', 'position_code']


class FinishCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Finish Codes"""
    queryset = FinishCode.objects.all()
    serializer_class = FinishCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['finish_code', 'name_es', 'name_en']
    ordering_fields = ['sort_order', 'finish_code']
    ordering = ['sort_order', 'finish_code']


class SourceCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Source Codes"""
    queryset = SourceCode.objects.all()
    serializer_class = SourceCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['quality_level']
    search_fields = ['source_code', 'name_es', 'name_en']
    ordering_fields = ['sort_order', 'source_code']
    ordering = ['sort_order', 'source_code']


class ConditionCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Condition Codes"""
    queryset = ConditionCode.objects.all()
    serializer_class = ConditionCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['condition_code', 'name_es', 'name_en']
    ordering_fields = ['sort_order', 'condition_code']
    ordering = ['sort_order', 'condition_code']


class UOMCodeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing UOM Codes"""
    queryset = UOMCode.objects.all()
    serializer_class = UOMCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_fractional']
    search_fields = ['uom_code', 'name_es', 'name_en']
    ordering = ['uom_code']


class CurrencyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Currencies"""
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['currency_code', 'name', 'symbol']
    ordering = ['currency_code']
    lookup_field = 'currency_code'  # Usar currency_code para el lookup
    
    def get_serializer(self, *args, **kwargs):
        """Ensure partial updates work correctly"""
        if self.action in ['update', 'partial_update']:
            kwargs['partial'] = True
        return super().get_serializer(*args, **kwargs)

