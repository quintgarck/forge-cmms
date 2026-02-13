"""
ForgeDB API REST - Nested and Complex Serializers
Automotive Workshop Management System

This module contains nested serializers and complex serializers for
advanced operations and detailed views.
"""

from rest_framework import serializers
from decimal import Decimal
from datetime import date, datetime
from django.db.models import Sum, Avg, Count

from ..models import (
    Alert, BusinessRule, AuditLog, Technician, Client, Equipment,
    Warehouse, ProductMaster, Stock, Transaction, WorkOrder, Invoice, Document
)
from .main_serializers import (
    TechnicianSerializer, ClientSerializer, EquipmentSerializer,
    WarehouseSerializer, ProductMasterSerializer, WorkOrderSerializer,
    InvoiceSerializer, DocumentSerializer
)


# =============================================================================
# Nested Serializers for Complex Views
# =============================================================================

class ClientDetailSerializer(ClientSerializer):
    """Detailed client serializer with related equipment and work orders"""
    equipment_list = EquipmentSerializer(source='equipment_set', many=True, read_only=True)
    recent_work_orders = serializers.SerializerMethodField()
    total_work_orders = serializers.SerializerMethodField()
    total_invoiced = serializers.SerializerMethodField()
    
    class Meta(ClientSerializer.Meta):
        fields = ClientSerializer.Meta.fields + [
            'equipment_list', 'recent_work_orders', 'total_work_orders', 'total_invoiced'
        ]

    def get_recent_work_orders(self, obj):
        """Get recent work orders for this client"""
        recent_wos = obj.workorder_set.order_by('-created_at')[:5]
        return WorkOrderSerializer(recent_wos, many=True, context=self.context).data

    def get_total_work_orders(self, obj):
        """Get total count of work orders for this client"""
        return obj.workorder_set.count()

    def get_total_invoiced(self, obj):
        """Get total amount invoiced to this client"""
        total = obj.invoice_set.aggregate(total=Sum('total_amount'))['total']
        return total or Decimal('0.00')


class EquipmentDetailSerializer(EquipmentSerializer):
    """Detailed equipment serializer with service history"""
    client_info = ClientSerializer(source='client', read_only=True)
    service_history = serializers.SerializerMethodField()
    total_services = serializers.SerializerMethodField()
    last_service_date = serializers.SerializerMethodField()
    
    class Meta(EquipmentSerializer.Meta):
        fields = EquipmentSerializer.Meta.fields + [
            'client_info', 'service_history', 'total_services', 'last_service_date'
        ]

    def get_service_history(self, obj):
        """Get recent service history for this equipment"""
        recent_services = obj.workorder_set.order_by('-created_at')[:10]
        return WorkOrderSerializer(recent_services, many=True, context=self.context).data

    def get_total_services(self, obj):
        """Get total count of services for this equipment"""
        return obj.workorder_set.count()

    def get_last_service_date(self, obj):
        """Get date of last service"""
        last_service = obj.workorder_set.order_by('-created_at').first()
        return last_service.created_at if last_service else None


class WorkOrderDetailSerializer(WorkOrderSerializer):
    """Detailed work order serializer with all related information"""
    client_info = ClientSerializer(source='client', read_only=True)
    equipment_info = EquipmentSerializer(source='equipment', read_only=True)
    technician_info = TechnicianSerializer(source='assigned_technician', read_only=True)
    created_by_info = TechnicianSerializer(source='created_by', read_only=True)
    related_documents = serializers.SerializerMethodField()
    parts_used = serializers.SerializerMethodField()
    labor_cost = serializers.SerializerMethodField()
    
    class Meta(WorkOrderSerializer.Meta):
        fields = WorkOrderSerializer.Meta.fields + [
            'client_info', 'equipment_info', 'technician_info', 'created_by_info',
            'related_documents', 'parts_used', 'labor_cost'
        ]

    def get_related_documents(self, obj):
        """Get documents related to this work order"""
        documents = Document.objects.filter(
            ref_entity='workorder',
            ref_id=obj.wo_id
        )
        return DocumentSerializer(documents, many=True, context=self.context).data

    def get_parts_used(self, obj):
        """Get parts/products used in this work order"""
        # This would typically come from a WorkOrderItem model
        # For now, return empty list as placeholder
        return []

    def get_labor_cost(self, obj):
        """Calculate labor cost based on hours and technician rate"""
        if obj.actual_hours and obj.assigned_technician and obj.assigned_technician.hourly_rate:
            return obj.actual_hours * obj.assigned_technician.hourly_rate
        return Decimal('0.00')


class InvoiceDetailSerializer(InvoiceSerializer):
    """Detailed invoice serializer with line items and payment history"""
    client_info = ClientSerializer(source='client', read_only=True)
    work_order_info = WorkOrderSerializer(source='work_order', read_only=True)
    created_by_info = TechnicianSerializer(source='created_by', read_only=True)
    line_items = serializers.SerializerMethodField()
    payment_history = serializers.SerializerMethodField()
    
    class Meta(InvoiceSerializer.Meta):
        fields = InvoiceSerializer.Meta.fields + [
            'client_info', 'work_order_info', 'created_by_info',
            'line_items', 'payment_history'
        ]

    def get_line_items(self, obj):
        """Get invoice line items"""
        # This would typically come from an InvoiceItem model
        # For now, return empty list as placeholder
        return []

    def get_payment_history(self, obj):
        """Get payment history for this invoice"""
        # This would typically come from a Payment model
        # For now, return empty list as placeholder
        return []


class ProductStockSerializer(ProductMasterSerializer):
    """Product serializer with stock information across all warehouses"""
    stock_levels = serializers.SerializerMethodField()
    total_on_hand = serializers.SerializerMethodField()
    total_available = serializers.SerializerMethodField()
    total_reserved = serializers.SerializerMethodField()
    warehouses_with_stock = serializers.SerializerMethodField()
    
    class Meta(ProductMasterSerializer.Meta):
        fields = ProductMasterSerializer.Meta.fields + [
            'stock_levels', 'total_on_hand', 'total_available',
            'total_reserved', 'warehouses_with_stock'
        ]

    def get_stock_levels(self, obj):
        """Get stock levels by warehouse"""
        from .main_serializers import StockSerializer
        stocks = obj.stock_set.select_related('warehouse')
        return StockSerializer(stocks, many=True, context=self.context).data

    def get_total_on_hand(self, obj):
        """Get total quantity on hand across all warehouses"""
        total = obj.stock_set.aggregate(total=Sum('quantity_on_hand'))['total']
        return total or 0

    def get_total_available(self, obj):
        """Get total available quantity across all warehouses"""
        total = obj.stock_set.aggregate(total=Sum('quantity_available'))['total']
        return total or 0

    def get_total_reserved(self, obj):
        """Get total reserved quantity across all warehouses"""
        total = obj.stock_set.aggregate(total=Sum('quantity_reserved'))['total']
        return total or 0

    def get_warehouses_with_stock(self, obj):
        """Get count of warehouses that have this product in stock"""
        return obj.stock_set.filter(quantity_on_hand__gt=0).count()


# =============================================================================
# Summary and Dashboard Serializers
# =============================================================================

class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    total_equipment = serializers.IntegerField()
    total_work_orders = serializers.IntegerField()
    open_work_orders = serializers.IntegerField()
    completed_work_orders_today = serializers.IntegerField()
    total_invoices = serializers.IntegerField()
    unpaid_invoices = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
    total_revenue_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_revenue_year = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_products = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()


class ClientSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for client list views"""
    equipment_count = serializers.SerializerMethodField()
    open_work_orders = serializers.SerializerMethodField()
    last_service_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'client_id', 'client_code', 'name', 'type', 'email', 'phone',
            'status', 'equipment_count', 'open_work_orders', 'last_service_date'
        ]

    def get_equipment_count(self, obj):
        """Get count of equipment for this client"""
        return obj.equipment_set.count()

    def get_open_work_orders(self, obj):
        """Get count of open work orders for this client"""
        return obj.workorder_set.exclude(status__in=['completed', 'cancelled']).count()

    def get_last_service_date(self, obj):
        """Get date of last service for this client"""
        last_wo = obj.workorder_set.order_by('-created_at').first()
        return last_wo.created_at if last_wo else None


class TechnicianSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for technician list views"""
    assigned_work_orders = serializers.SerializerMethodField()
    completed_work_orders_month = serializers.SerializerMethodField()
    average_completion_time = serializers.SerializerMethodField()
    specializations = serializers.ListField(
        child=serializers.CharField(),
        source='specialization',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Technician
        fields = [
            'technician_id', 'employee_code', 'first_name', 'last_name',
            'email', 'specializations', 'status', 'assigned_work_orders',
            'completed_work_orders_month', 'average_completion_time'
        ]

    def get_assigned_work_orders(self, obj):
        """Get count of currently assigned work orders"""
        return obj.assigned_work_orders.exclude(status__in=['completed', 'cancelled']).count()

    def get_completed_work_orders_month(self, obj):
        """Get count of work orders completed this month"""
        from django.utils import timezone
        from datetime import datetime
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return obj.assigned_work_orders.filter(
            status='completed',
            completed_at__gte=start_of_month
        ).count()

    def get_average_completion_time(self, obj):
        """Get average completion time in hours"""
        completed_wos = obj.assigned_work_orders.filter(
            status='completed',
            actual_hours__isnull=False
        )
        if completed_wos.exists():
            avg_hours = completed_wos.aggregate(avg=Avg('actual_hours'))['avg']
            return float(avg_hours) if avg_hours else 0.0
        return 0.0


# =============================================================================
# Bulk Operation Serializers
# =============================================================================

class BulkWorkOrderUpdateSerializer(serializers.Serializer):
    """Serializer for bulk work order updates"""
    work_order_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    status = serializers.ChoiceField(
        choices=WorkOrder.STATUS_CHOICES,
        required=False
    )
    assigned_technician = serializers.PrimaryKeyRelatedField(
        queryset=Technician.objects.filter(status='active'),
        required=False
    )
    priority = serializers.ChoiceField(
        choices=WorkOrder.PRIORITY_CHOICES,
        required=False
    )

    def validate_work_order_ids(self, value):
        """Validate that all work order IDs exist"""
        existing_ids = set(
            WorkOrder.objects.filter(wo_id__in=value).values_list('wo_id', flat=True)
        )
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid work order IDs: {list(invalid_ids)}"
            )
        return value


class BulkStockUpdateSerializer(serializers.Serializer):
    """Serializer for bulk stock updates"""
    updates = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=100
    )

    def validate_updates(self, value):
        """Validate stock update entries"""
        for update in value:
            if 'warehouse_id' not in update or 'product_id' not in update:
                raise serializers.ValidationError(
                    "Each update must include warehouse_id and product_id"
                )
            if 'quantity_on_hand' not in update:
                raise serializers.ValidationError(
                    "Each update must include quantity_on_hand"
                )
            if update['quantity_on_hand'] < 0:
                raise serializers.ValidationError(
                    "Quantity on hand cannot be negative"
                )
        return value


# =============================================================================
# Search and Filter Serializers
# =============================================================================

class SearchResultSerializer(serializers.Serializer):
    """Generic search result serializer"""
    entity_type = serializers.CharField()
    entity_id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    url = serializers.CharField()
    relevance_score = serializers.FloatField()


class FilterOptionsSerializer(serializers.Serializer):
    """Serializer for filter options"""
    field_name = serializers.CharField()
    display_name = serializers.CharField()
    field_type = serializers.ChoiceField(choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('choice', 'Choice'),
        ('boolean', 'Boolean')
    ])
    choices = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    min_value = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    max_value = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)


# =============================================================================
# Validation and Error Serializers
# =============================================================================

class ValidationErrorSerializer(serializers.Serializer):
    """Serializer for validation error responses"""
    field = serializers.CharField()
    message = serializers.CharField()
    code = serializers.CharField()
    value = serializers.CharField(required=False)


class BulkOperationResultSerializer(serializers.Serializer):
    """Serializer for bulk operation results"""
    total_processed = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    errors = ValidationErrorSerializer(many=True)
    warnings = serializers.ListField(child=serializers.CharField(), required=False)