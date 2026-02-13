"""
ForgeDB API REST - Main DRF Serializers
Automotive Workshop Management System

This module contains DRF serializers for all models in the ForgeDB system.
Serializers are organized by schema and include proper validation and business logic.
"""

from rest_framework import serializers
from decimal import Decimal
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import (
    Alert, BusinessRule, AuditLog, Technician, Client, Equipment,
    Warehouse, ProductMaster, Stock, Transaction, WorkOrder, Invoice, Document,
    # Catalog models
    Category, EquipmentType, FuelCode, AspirationCode, TransmissionCode, DrivetrainCode,
    ColorCode, PositionCode, FinishCode, SourceCode, ConditionCode, UOMCode,
    Currency, Supplier, TaxonomySystem, TaxonomySubsystem, TaxonomyGroup, Fitment,
    # Inventory models
    Bin, PriceList, ProductPrice, PurchaseOrder, POItem, SupplierSKU,
    # OEM models
    OEMBrand, OEMCatalogItem, OEMEquivalence,
    # Service models
    WOItem, WOService, FlatRateStandard, ServiceChecklist, InvoiceItem, Payment,
    Quote, QuoteItem,
    # KPI models
    WOMetric
)


# =============================================================================
# APP SCHEMA - Application Management Serializers
# =============================================================================

class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model with business logic validation"""
    
    class Meta:
        model = Alert
        fields = [
            'alert_id', 'alert_type', 'ref_entity', 'ref_id', 'ref_code',
            'title', 'message', 'details', 'severity', 'status',
            'assigned_to', 'created_for', 'created_at', 'read_at',
            'acknowledged_at', 'resolved_at'
        ]
        read_only_fields = ['alert_id', 'created_at']

    def validate(self, data):
        """Custom validation for Alert"""
        # Ensure that resolved alerts have resolved_at timestamp
        if data.get('status') == 'resolved' and not data.get('resolved_at'):
            data['resolved_at'] = datetime.now()
        
        # Ensure that acknowledged alerts have acknowledged_at timestamp
        if data.get('status') == 'acknowledged' and not data.get('acknowledged_at'):
            data['acknowledged_at'] = datetime.now()
            
        # Ensure that read alerts have read_at timestamp
        if data.get('status') in ['read', 'acknowledged', 'resolved'] and not data.get('read_at'):
            data['read_at'] = datetime.now()
            
        return data


class BusinessRuleSerializer(serializers.ModelSerializer):
    """Serializer for BusinessRule model with validation logic"""
    
    class Meta:
        model = BusinessRule
        fields = [
            'rule_id', 'rule_code', 'rule_name', 'condition_text',
            'condition_type', 'action_type', 'action_text', 'applies_to_table',
            'applies_to_schema', 'trigger_event', 'severity', 'is_active',
            'is_system_rule', 'execution_order', 'stop_on_match',
            'created_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['rule_id', 'created_at', 'updated_at']

    def validate_rule_code(self, value):
        """Validate rule code format"""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                "Rule code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_execution_order(self, value):
        """Validate execution order is positive"""
        if value < 1:
            raise serializers.ValidationError(
                "Execution order must be a positive integer"
            )
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model - read-only for security"""
    
    class Meta:
        model = AuditLog
        fields = [
            'audit_id', 'table_name', 'record_id', 'action',
            'changed_by', 'changed_at', 'old_values', 'new_values',
            'ip_address', 'user_agent'
        ]
        read_only_fields = [
            'audit_id', 'table_name', 'record_id', 'action',
            'changed_by', 'changed_at', 'old_values', 'new_values',
            'ip_address', 'user_agent'
        ]  # Audit logs should never be modified


# =============================================================================
# CAT SCHEMA - Catalog and Master Data Serializers
# =============================================================================

class TechnicianSerializer(serializers.ModelSerializer):
    """Serializer for Technician model with business validation"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Technician
        fields = [
            'technician_id', 'employee_code', 'first_name', 'last_name',
            'full_name', 'email', 'phone', 'hire_date', 'birth_date',
            'specialization', 'certification_level', 'certifications',
            'hourly_rate', 'daily_rate', 'overtime_multiplier', 'work_schedule',
            'efficiency_avg', 'quality_score', 'jobs_completed',
            'status', 'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['technician_id', 'created_at', 'updated_at', 'jobs_completed']

    def to_internal_value(self, data):
        """Handle string input for ArrayField items (specialization, certifications)"""
        # Make a mutable copy of the data
        data = dict(data)
        
        # Handle specialization - can be string (comma-separated) or list
        if 'specialization' in data:
            spec = data['specialization']
            if isinstance(spec, str):
                # Convert comma-separated string to list
                spec_list = [s.strip() for s in spec.split(',') if s.strip()]
                data['specialization'] = spec_list
            elif spec and not isinstance(spec, list):
                # If it's something else (like a single value), wrap in list
                data['specialization'] = [str(spec).strip()] if str(spec).strip() else []
        
        # Handle certifications - can be string (comma-separated) or list
        if 'certifications' in data:
            cert = data['certifications']
            if isinstance(cert, str):
                # Convert comma-separated string to list
                cert_list = [c.strip() for c in cert.split(',') if c.strip()]
                data['certifications'] = cert_list
            elif cert and not isinstance(cert, list):
                # If it's something else, wrap in list
                data['certifications'] = [str(cert).strip()] if str(cert).strip() else []
        
        return super().to_internal_value(data)

    def validate_specialization(self, value):
        """Validate specialization field"""
        if value is None:
            return []
        if isinstance(value, str):
            # Convert string to list
            value = [s.strip() for s in value.split(',') if s.strip()]
        if not isinstance(value, list):
            raise serializers.ValidationError("Specialization must be a list or comma-separated string")
        return value

    def validate_certifications(self, value):
        """Validate certifications field"""
        if value is None:
            return []
        if isinstance(value, str):
            # Convert string to list
            value = [c.strip() for c in value.split(',') if c.strip()]
        if not isinstance(value, list):
            raise serializers.ValidationError("Certifications must be a list or comma-separated string")
        return value

    def validate_employee_code(self, value):
        """Validate employee code format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Employee code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_hourly_rate(self, value):
        """Validate hourly rate is reasonable"""
        if value is not None:
            if value < Decimal('0.01'):
                raise serializers.ValidationError(
                    "Hourly rate must be greater than 0"
                )
            if value > Decimal('999.99'):
                raise serializers.ValidationError(
                    "Hourly rate seems unreasonably high"
                )
        return value

    def validate_hire_date(self, value):
        """Validate hire date is not in the future"""
        if value and value > date.today():
            raise serializers.ValidationError(
                "Hire date cannot be in the future"
            )
        return value
    
    def validate_birth_date(self, value):
        """Validate birth date is reasonable"""
        if value:
            if value > date.today():
                raise serializers.ValidationError(
                    "Birth date cannot be in the future"
                )
            age = (date.today() - value).days // 365
            if age < 18:
                raise serializers.ValidationError(
                    "Technician must be at least 18 years old"
                )
            if age > 100:
                raise serializers.ValidationError(
                    "Birth date seems unreasonably old"
                )
        return value
    
    def validate_daily_rate(self, value):
        """Validate daily rate is reasonable"""
        if value is not None:
            if value < Decimal('0.01'):
                raise serializers.ValidationError(
                    "Daily rate must be greater than 0"
                )
            if value > Decimal('9999.99'):
                raise serializers.ValidationError(
                    "Daily rate seems unreasonably high"
                )
        return value
    
    def validate_overtime_multiplier(self, value):
        """Validate overtime multiplier is reasonable"""
        if value is not None:
            if value < Decimal('1.00'):
                raise serializers.ValidationError(
                    "Overtime multiplier must be at least 1.0"
                )
            if value > Decimal('5.00'):
                raise serializers.ValidationError(
                    "Overtime multiplier seems unreasonably high"
                )
        return value
    
    def validate_efficiency_avg(self, value):
        """Validate efficiency average percentage"""
        if value is not None:
            if value < Decimal('0'):
                raise serializers.ValidationError(
                    "Efficiency average cannot be negative"
                )
            if value > Decimal('200.00'):
                raise serializers.ValidationError(
                    "Efficiency average seems unreasonably high"
                )
        return value
    
    def validate_quality_score(self, value):
        """Validate quality score percentage"""
        if value is not None:
            if value < Decimal('0'):
                raise serializers.ValidationError(
                    "Quality score cannot be negative"
                )
            if value > Decimal('100.00'):
                raise serializers.ValidationError(
                    "Quality score cannot exceed 100"
                )
        return value


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model with business validation"""
    available_credit = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = [
            'client_id', 'uuid', 'client_code', 'type', 'name', 'legal_name',
            'tax_id', 'email', 'phone', 'mobile', 'address', 'city', 'state',
            'country', 'postal_code', 'credit_limit', 'payment_days', 'credit_used',
            'available_credit', 'preferred_contact_method', 'send_reminders',
            'status', 'created_by', 'created_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['client_id', 'uuid', 'created_at', 'updated_at', 'credit_used', 'created_by']

    def validate_client_code(self, value):
        """Validate client code format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Client code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_credit_limit(self, value):
        """Validate credit limit is reasonable"""
        if value is not None:
            if value < Decimal('0'):
                raise serializers.ValidationError(
                    "Credit limit cannot be negative"
                )
            if value > Decimal('9999999.99'):
                raise serializers.ValidationError(
                    "Credit limit seems unreasonably high"
                )
        return value

    def validate_payment_days(self, value):
        """Validate payment days is reasonable"""
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    "Payment days cannot be negative"
                )
            if value > 365:
                raise serializers.ValidationError(
                    "Payment days cannot exceed 365"
                )
        return value
    
    def validate_status(self, value):
        """Validate status is uppercase"""
        if value:
            return value.upper()
        return value
    
    def validate_type(self, value):
        """Validate type is uppercase and correct value"""
        if value:
            value_upper = value.upper()
            # Map common variations to valid values
            type_mapping = {
                'INDIVIDUAL': 'INDIVIDUAL',
                'BUSINESS': 'EMPRESA',
                'EMPRESA': 'EMPRESA',
                'FLEET': 'EMPRESA',  # Map fleet to empresa
                'GOVERNMENT': 'GOVERNMENT',
                'GOBIERNO': 'GOVERNMENT',
            }
            return type_mapping.get(value_upper, value_upper)
        return value
    
    def validate(self, data):
        """Business logic validation"""
        # Ensure status is UPPERCASE
        if 'status' in data and data['status']:
            data['status'] = data['status'].upper()
        
        # Validate credit usage doesn't exceed limit
        credit_limit = data.get('credit_limit')
        credit_used = data.get('credit_used', Decimal('0.00'))
        
        if credit_limit and credit_used > credit_limit:
            raise serializers.ValidationError(
                "Credit used cannot exceed credit limit"
            )
        
        return data


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer for Equipment model with VIN validation"""
    client = serializers.SerializerMethodField()
    mileage = serializers.IntegerField(source='current_mileage_hours', required=False)
    warranty_expiry = serializers.DateField(source='warranty_until', required=False)
    type_id = serializers.IntegerField(required=False, default=1)  # Optional with default value
    
    class Meta:
        model = Equipment
        fields = [
            'equipment_id', 'uuid', 'equipment_code', 'type_id', 'client', 'client_id',
            'brand', 'model', 'year', 'serial_number', 'vin', 'license_plate',
            'color', 'submodel_trim', 'body_style', 'doors', 'engine_desc', 'fuel_code',
            'aspiration_code', 'transmission_code', 'drivetrain_code',
            'purchase_date', 'warranty_until', 'warranty_expiry', 'last_service_date',
            'next_service_date', 'total_service_hours', 'total_service_cost',
            'status', 'current_mileage_hours', 'mileage', 'last_mileage_update',
            'custom_fields', 'metadata', 'created_by', 'created_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['equipment_id', 'uuid', 'client', 'mileage', 'warranty_expiry', 'created_at', 'updated_at', 'created_by']
    
    def get_client(self, obj):
        """Get client representation"""
        if obj.client_id:
            try:
                from ..models import Client
                client = Client.objects.get(client_id=obj.client_id)
                return {
                    'client_id': client.client_id,
                    'client_code': client.client_code,
                    'name': client.name
                }
            except Client.DoesNotExist:
                return None
        return None

    def validate_equipment_code(self, value):
        """Validate equipment code format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Equipment code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_vin(self, value):
        """Validate VIN format (17 characters, alphanumeric)"""
        if value:
            if len(value) != 17:
                raise serializers.ValidationError(
                    "VIN must be exactly 17 characters long"
                )
            if not value.replace('-', '').isalnum():
                raise serializers.ValidationError(
                    "VIN must contain only alphanumeric characters"
                )
        return value.upper() if value else value

    def validate_current_mileage_hours(self, value):
        """Validate current mileage/hours is reasonable"""
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    "Mileage/hours cannot be negative"
                )
            if value > 9999999:
                raise serializers.ValidationError(
                    "Mileage/hours seems unreasonably high"
                )
        return value
    
    def validate_year(self, value):
        """Validate year is reasonable"""
        if value is not None:
            from datetime import date
            current_year = date.today().year
            if value < 1900:
                raise serializers.ValidationError(
                    "Year cannot be before 1900"
                )
            if value > current_year + 2:
                raise serializers.ValidationError(
                    f"Year cannot be more than {current_year + 2}"
                )
        return value
    
    def validate_doors(self, value):
        """Validate doors count"""
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    "Doors cannot be negative"
                )
            if value > 10:
                raise serializers.ValidationError(
                    "Doors count seems unreasonable"
                )
        return value
    
    def validate_total_service_hours(self, value):
        """Validate total service hours"""
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    "Total service hours cannot be negative"
                )
        return value
    
    def validate_total_service_cost(self, value):
        """Validate total service cost"""
        if value is not None:
            if value < Decimal('0'):
                raise serializers.ValidationError(
                    "Total service cost cannot be negative"
                )
        return value

    def validate_purchase_date(self, value):
        """Validate purchase date is not in the future"""
        if value and value > date.today():
            raise serializers.ValidationError(
                "Purchase date cannot be in the future"
            )
        return value


# =============================================================================
# INV SCHEMA - Inventory Management Serializers
# =============================================================================

class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer for Warehouse model"""
    
    class Meta:
        model = Warehouse
        fields = [
            'warehouse_code', 'name', 'type', 'address',
            'contact_phone', 'manager', 'capacity', 'current_occupancy',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']

    def validate_warehouse_code(self, value):
        """Validate warehouse code format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Warehouse code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate(self, data):
        """Ensure only one main warehouse exists"""
        if data.get('is_main', False):
            # Check if another main warehouse exists
            existing_main = Warehouse.objects.filter(is_main=True)
            if self.instance:
                existing_main = existing_main.exclude(pk=self.instance.pk)
            if existing_main.exists():
                raise serializers.ValidationError(
                    "Only one main warehouse can exist"
                )
        return data


class ProductMasterSerializer(serializers.ModelSerializer):
    """Serializer for ProductMaster model with inventory validation"""
    
    class Meta:
        model = ProductMaster
        fields = [
            'internal_sku', 'group_code', 'name', 'description', 'brand',
            'oem_ref', 'oem_code', 'source_code', 'condition_code',
            'position_code', 'finish_code', 'color_code', 'uom_code',
            'barcode', 'supplier_mpn', 'interchange_numbers', 'cross_references',
            'weight_kg', 'dimensions_cm', 'package_qty', 'min_stock',
            'max_stock', 'reorder_point', 'safety_stock', 'lead_time_days',
            'core_required', 'core_price', 'warranty_days', 'standard_cost',
            'avg_cost', 'last_purchase_cost', 'is_active', 'is_serialized',
            'created_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['internal_sku', 'created_at', 'updated_at']

    def validate_internal_sku(self, value):
        """Validate internal SKU format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Internal SKU must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_min_stock(self, value):
        """Validate minimum stock level"""
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Minimum stock level cannot be negative"
            )
        return value

    def validate_reorder_point(self, value):
        """Validate reorder point"""
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Reorder point cannot be negative"
            )
        return value

    def validate_package_qty(self, value):
        """Validate package quantity"""
        if value is not None and value < 1:
            raise serializers.ValidationError(
                "Package quantity must be at least 1"
            )
        return value

    def validate(self, data):
        """Cross-field validation"""
        min_stock = data.get('min_stock', 0)
        max_stock = data.get('max_stock')
        reorder_point = data.get('reorder_point', 0)
        
        if max_stock is not None and min_stock is not None and max_stock < min_stock:
            raise serializers.ValidationError(
                "Maximum stock level must be greater than minimum stock level"
            )
            
        if reorder_point is not None and min_stock is not None and reorder_point > min_stock:
            raise serializers.ValidationError(
                "Reorder point should not exceed minimum stock level"
            )
            
        return data


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model with calculated fields"""
    is_below_minimum = serializers.ReadOnlyField()
    needs_reorder = serializers.ReadOnlyField()
    
    class Meta:
        model = Stock
        fields = [
            'stock_id', 'warehouse', 'product', 'bin_id',
            'qty_on_hand', 'qty_reserved', 'qty_available', 'qty_on_order',
            'batch_number', 'serial_number', 'expiration_date', 'manufacturing_date',
            'unit_cost', 'total_cost', 'last_receipt_date',
            'last_count_date', 'next_count_date', 'status', 'notes',
            'is_below_minimum', 'needs_reorder',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'stock_id', 'last_movement_date', 'created_at', 'updated_at'
        ]

    def validate_qty_on_hand(self, value):
        """Validate quantity on hand"""
        if value < 0:
            raise serializers.ValidationError(
                "Quantity on hand cannot be negative"
            )
        return value

    def validate_qty_reserved(self, value):
        """Validate quantity reserved"""
        if value < 0:
            raise serializers.ValidationError(
                "Quantity reserved cannot be negative"
            )
        return value

    def validate_unit_cost(self, value):
        """Validate unit cost"""
        if value is not None and value < Decimal('0'):
            raise serializers.ValidationError(
                "Unit cost cannot be negative"
            )
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model with business logic"""
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'transaction_date', 'transaction_type',
            'warehouse', 'product', 'quantity', 'unit_cost', 'total_cost',
            'reference_type', 'reference_id', 'reference_number',
            'notes', 'created_by'
        ]
        read_only_fields = ['transaction_id', 'transaction_date']

    def validate_quantity(self, value):
        """Validate quantity based on transaction type"""
        if value == 0:
            raise serializers.ValidationError(
                "Quantity cannot be zero"
            )
        return value

    def validate_unit_cost(self, value):
        """Validate unit cost"""
        if value is not None and value < Decimal('0'):
            raise serializers.ValidationError(
                "Unit cost cannot be negative"
            )
        return value

    def validate(self, data):
        """Business logic validation"""
        transaction_type = data.get('transaction_type')
        quantity = data.get('quantity', 0)
        
        # Issue transactions should have negative quantities
        if transaction_type == 'issue' and quantity > 0:
            data['quantity'] = -abs(quantity)
        # Receipt transactions should have positive quantities
        elif transaction_type == 'receipt' and quantity < 0:
            data['quantity'] = abs(quantity)
            
        return data


# =============================================================================
# SVC SCHEMA - Service Management Serializers
# =============================================================================

class WorkOrderSerializer(serializers.ModelSerializer):
    """Serializer for WorkOrder model with service workflow validation"""
    client = serializers.SerializerMethodField()
    equipment = serializers.SerializerMethodField()
    assigned_technician = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkOrder
        fields = [
            'wo_id', 'wo_number', 'client_id', 'client', 'equipment_id', 'equipment',
            'advisor_id', 'technician_id', 'assigned_technician', 'qc_technician_id',
            'service_type', 'priority', 'status',
            'customer_complaints', 'initial_findings', 'final_report',
            'reception_date', 'appointment_date', 'estimated_start_date', 'estimated_completion_date',
            'diagnosis_date', 'actual_start_date', 'actual_completion_date', 'delivery_date',
            'qc_date', 'closed_at',
            'mileage_in', 'mileage_out', 'hours_in', 'hours_out',
            'estimated_hours', 'actual_hours', 'flat_rate_hours', 'efficiency_rate',
            'labor_rate', 'labor_cost', 'parts_cost', 'additional_costs', 'discount_amount',
            'quoted_price', 'final_price', 'total_cost',
            'technician_notes', 'qc_notes', 'notes',
            'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['wo_id', 'client', 'equipment', 'assigned_technician', 'created_at', 'updated_at', 'created_by']
    
    def get_client(self, obj):
        """Get client representation"""
        if obj.client_id:
            try:
                from ..models import Client
                client = Client.objects.get(client_id=obj.client_id)
                return {
                    'client_id': client.client_id,
                    'client_code': client.client_code,
                    'name': client.name
                }
            except Client.DoesNotExist:
                return None
        return None
    
    def get_equipment(self, obj):
        """Get equipment representation"""
        if obj.equipment_id:
            try:
                from ..models import Equipment
                equipment = Equipment.objects.get(equipment_id=obj.equipment_id)
                return {
                    'equipment_id': equipment.equipment_id,
                    'equipment_code': equipment.equipment_code,
                    'brand': equipment.brand,
                    'model': equipment.model,
                    'year': equipment.year
                }
            except Equipment.DoesNotExist:
                return None
        return None
    
    def get_assigned_technician(self, obj):
        """Get technician representation"""
        if obj.technician_id:
            try:
                from ..models import Technician
                tech = Technician.objects.get(technician_id=obj.technician_id)
                return {
                    'technician_id': tech.technician_id,
                    'employee_code': tech.employee_code,
                    'full_name': tech.full_name
                }
            except Technician.DoesNotExist:
                return None
        return None

    def validate_wo_number(self, value):
        """Validate work order number format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Work order number must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_estimated_hours(self, value):
        """Validate estimated hours"""
        if value is not None:
            if value <= Decimal('0'):
                raise serializers.ValidationError(
                    "Estimated hours must be greater than 0"
                )
            if value > Decimal('999.99'):
                raise serializers.ValidationError(
                    "Estimated hours seems unreasonably high"
                )
        return value

    def validate_actual_hours(self, value):
        """Validate actual hours"""
        if value is not None:
            if value <= Decimal('0'):
                raise serializers.ValidationError(
                    "Actual hours must be greater than 0"
                )
            if value > Decimal('999.99'):
                raise serializers.ValidationError(
                    "Actual hours seems unreasonably high"
                )
        return value

    def validate(self, data):
        """Status transition validation"""
        status = data.get('status')
        
        # Set timestamps based on status
        if status == 'IN_PROGRESS' and not data.get('start_time'):
            data['start_time'] = datetime.now()
        if status == 'COMPLETED' and not data.get('actual_completion_date'):
            data['actual_completion_date'] = date.today()
            
        # Validate required fields for certain statuses
        if status == 'COMPLETED':
            if not data.get('final_report'):
                raise serializers.ValidationError(
                    "Final report is required for completed work orders"
                )
                
        return data


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Invoice model with financial validation"""
    is_overdue = serializers.ReadOnlyField()
    client = serializers.SerializerMethodField()
    work_order = serializers.SerializerMethodField()
    invoice_date = serializers.DateField(source='issue_date', required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_id', 'invoice_number', 'wo_id', 'client_id', 'client',
            'work_order', 'currency_code', 'subtotal', 'tax_amount',
            'discount_amount', 'total_amount', 'is_overdue', 'status',
            'issue_date', 'invoice_date', 'due_date', 'paid_date', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'invoice_id', 'client', 'work_order', 'invoice_date', 'is_overdue',
            'created_at', 'updated_at'
        ]
    
    def get_client(self, obj):
        """Get client representation"""
        if obj.client_id:
            try:
                from ..models import Client
                client = Client.objects.get(client_id=obj.client_id)
                return {
                    'client_id': client.client_id,
                    'client_code': client.client_code,
                    'name': client.name
                }
            except Client.DoesNotExist:
                return None
        return None
    
    def get_work_order(self, obj):
        """Get work order representation"""
        if obj.wo_id:
            try:
                from ..models import WorkOrder
                wo = WorkOrder.objects.get(wo_id=obj.wo_id)
                return {
                    'wo_id': wo.wo_id,
                    'wo_number': wo.wo_number,
                    'status': wo.status
                }
            except WorkOrder.DoesNotExist:
                return None
        return None

    def validate_invoice_number(self, value):
        """Validate invoice number format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Invoice number must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()

    def validate_subtotal(self, value):
        """Validate subtotal"""
        if value < Decimal('0'):
            raise serializers.ValidationError(
                "Subtotal cannot be negative"
            )
        return value

    def validate_tax_amount(self, value):
        """Validate tax amount"""
        if value < Decimal('0'):
            raise serializers.ValidationError(
                "Tax amount cannot be negative"
            )
        return value

    def validate_discount_amount(self, value):
        """Validate discount amount"""
        if value < Decimal('0'):
            raise serializers.ValidationError(
                "Discount amount cannot be negative"
            )
        return value

    def validate_paid_date(self, value):
        """Validate paid date"""
        if value:
            issue_date = self.instance.issue_date if self.instance else None
            if issue_date and value < issue_date:
                raise serializers.ValidationError(
                    "Paid date cannot be before issue date"
                )
        return value
    
    def validate_due_date(self, value):
        """Validate due date"""
        if value:
            issue_date = self.instance.issue_date if self.instance else None
            if issue_date and value < issue_date:
                raise serializers.ValidationError(
                    "Due date cannot be before issue date"
                )
        return value

    def validate(self, data):
        """Calculate totals and validate amounts"""
        subtotal = data.get('subtotal', Decimal('0'))
        tax_amount = data.get('tax_amount', Decimal('0'))
        discount_amount = data.get('discount_amount', Decimal('0'))
        
        # Calculate total amount if not provided
        if 'total_amount' not in data or data['total_amount'] is None:
            total_amount = subtotal + tax_amount - discount_amount
            data['total_amount'] = total_amount
        
        # Validate status transitions
        status = data.get('status')
        if status == 'paid' and not data.get('paid_date'):
            data['paid_date'] = date.today()
            
        return data


# =============================================================================
# DOC SCHEMA - Document Management Serializers
# =============================================================================

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model with file validation"""
    
    class Meta:
        model = Document
        fields = [
            'document_id', 'uuid', 'document_type', 'title', 'description',
            'file_name', 'file_path', 'file_size', 'mime_type',
            'ref_entity', 'ref_id', 'is_public', 'uploaded_by', 'uploaded_at'
        ]
        read_only_fields = ['document_id', 'uuid', 'uploaded_at']

    def validate_file_size(self, value):
        """Validate file size (max 50MB)"""
        max_size = 50 * 1024 * 1024  # 50MB in bytes
        if value > max_size:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size // (1024 * 1024)}MB"
            )
        return value

    def validate_mime_type(self, value):
        """Validate allowed MIME types"""
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/gif',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"MIME type '{value}' is not allowed"
            )
        return value


# =============================================================================
# CAT SCHEMA - Catalog Reference Serializers
# =============================================================================

class EquipmentTypeSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentType model with enhanced attribute schema validation"""
    category_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    
    class Meta:
        model = EquipmentType
        fields = [
            'type_id', 'type_code', 'category', 'category_id', 'category_name',
            'name', 'icon', 'color', 'attr_schema', 'description',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['type_id', 'created_at', 'updated_at']
    
    def to_internal_value(self, data):
        """Handle category as ID instead of object"""
        # Make a mutable copy
        data = dict(data)
        
        # If category is provided as an ID, store it in category_id
        if 'category' in data and isinstance(data['category'], int):
            data['category_id'] = data.pop('category')
        elif 'category' in data and isinstance(data['category'], str) and data['category'].isdigit():
            data['category_id'] = int(data.pop('category'))
        
        return super().to_internal_value(data)
    
    def validate_attr_schema(self, value):
        """Validate the attribute schema structure"""
        if not value:
            return {}
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Attribute schema must be a JSON object")
        
        # Validate each attribute definition
        valid_types = ['string', 'number', 'boolean', 'date', 'select']
        
        for attr_name, attr_config in value.items():
            if not isinstance(attr_config, dict):
                raise serializers.ValidationError(
                    f"Configuration for attribute '{attr_name}' must be an object"
                )
            
            # Check required type field
            if 'type' not in attr_config:
                raise serializers.ValidationError(
                    f"Attribute '{attr_name}' must specify a type"
                )
            
            # Validate type
            if attr_config['type'] not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid type '{attr_config['type']}' for attribute '{attr_name}'. "
                    f"Valid types: {', '.join(valid_types)}"
                )
            
            # Validate options for select type
            if attr_config['type'] == 'select':
                if 'options' not in attr_config or not attr_config['options']:
                    raise serializers.ValidationError(
                        f"Select attribute '{attr_name}' must specify options"
                    )
                if not isinstance(attr_config['options'], list):
                    raise serializers.ValidationError(
                        f"Options for attribute '{attr_name}' must be an array"
                    )
            
            # Validate numeric constraints
            if attr_config['type'] == 'number':
                if 'min' in attr_config and not isinstance(attr_config['min'], (int, float)):
                    raise serializers.ValidationError(
                        f"Min value for attribute '{attr_name}' must be a number"
                    )
                if 'max' in attr_config and not isinstance(attr_config['max'], (int, float)):
                    raise serializers.ValidationError(
                        f"Max value for attribute '{attr_name}' must be a number"
                    )
                
                if 'min' in attr_config and 'max' in attr_config:
                    if attr_config['min'] > attr_config['max']:
                        raise serializers.ValidationError(
                            f"Min value cannot be greater than max value for attribute '{attr_name}'"
                        )
        
        return value
    
    def to_representation(self, instance):
        """Customize the output representation"""
        data = super().to_representation(instance)
        
        # Add human-readable attribute info
        if data.get('attr_schema'):
            attr_count = len(data['attr_schema'])
            data['attribute_count'] = attr_count
            data['attribute_names'] = list(data['attr_schema'].keys())
        else:
            data['attribute_count'] = 0
            data['attribute_names'] = []
        
        return data


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    equipment_type_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'category_id', 'category_code', 'name', 'description',
            'icon', 'color', 'sort_order', 'is_active',
            'created_at', 'updated_at', 'equipment_type_count'
        ]
        read_only_fields = ['category_id', 'created_at', 'updated_at']
    
    def get_equipment_type_count(self, obj):
        """Get count of equipment types in this category"""
        return obj.equipment_types.count() if hasattr(obj, 'equipment_types') else 0
    
    def validate_category_code(self, value):
        """Validate category code format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Category code must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()
    
    def validate_name(self, value):
        """Validate name is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Category name cannot be empty"
            )
        return value.strip()


class FuelCodeSerializer(serializers.ModelSerializer):
    """Serializer for FuelCode model"""
    
    class Meta:
        model = FuelCode
        fields = ['fuel_code', 'name_es', 'name_en', 'is_alternative']


class AspirationCodeSerializer(serializers.ModelSerializer):
    """Serializer for AspirationCode model"""
    
    class Meta:
        model = AspirationCode
        fields = ['aspiration_code', 'name_es', 'name_en']


class TransmissionCodeSerializer(serializers.ModelSerializer):
    """Serializer for TransmissionCode model"""
    
    class Meta:
        model = TransmissionCode
        fields = ['transmission_code', 'name_es', 'name_en']


class DrivetrainCodeSerializer(serializers.ModelSerializer):
    """Serializer for DrivetrainCode model"""
    
    class Meta:
        model = DrivetrainCode
        fields = ['drivetrain_code', 'name_es', 'name_en']


class ColorCodeSerializer(serializers.ModelSerializer):
    """Serializer for ColorCode model"""
    
    class Meta:
        model = ColorCode
        fields = [
            'color_id', 'color_code', 'brand', 'name_es', 'name_en',
            'hex_code', 'paint_type', 'is_metallic', 'sort_order', 'created_at'
        ]
        read_only_fields = ['color_id', 'created_at']


class PositionCodeSerializer(serializers.ModelSerializer):
    """Serializer for PositionCode model"""
    
    class Meta:
        model = PositionCode
        fields = [
            'position_code', 'name_es', 'name_en', 'category',
            'sort_order', 'synonyms', 'created_at'
        ]
        read_only_fields = ['created_at']


class FinishCodeSerializer(serializers.ModelSerializer):
    """Serializer for FinishCode model"""
    
    class Meta:
        model = FinishCode
        fields = [
            'finish_code', 'name_es', 'name_en', 'requires_color',
            'sort_order', 'created_at'
        ]
        read_only_fields = ['created_at']


class SourceCodeSerializer(serializers.ModelSerializer):
    """Serializer for SourceCode model"""
    
    class Meta:
        model = SourceCode
        fields = ['source_code', 'name_es', 'name_en', 'quality_level', 'sort_order']


class ConditionCodeSerializer(serializers.ModelSerializer):
    """Serializer for ConditionCode model"""
    
    class Meta:
        model = ConditionCode
        fields = ['condition_code', 'name_es', 'name_en', 'requires_core', 'sort_order']


class UOMCodeSerializer(serializers.ModelSerializer):
    """Serializer for UOMCode model"""
    
    class Meta:
        model = UOMCode
        fields = ['uom_code', 'name_es', 'name_en', 'is_fractional', 'category']


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency model with validation for updates"""
    currency_code = serializers.CharField(
        max_length=3,
        required=False,  # No requerido en actualizaciones
        allow_blank=True,
        allow_null=True
    )
    
    class Meta:
        model = Currency
        fields = [
            'currency_code', 'name', 'symbol', 'exchange_rate',
            'decimals', 'is_active', 'is_base_currency', 'last_updated'
        ]
        verbose_name_plural = 'Currencies'
    
    def validate_currency_code(self, value):
        """Validate currency code format"""
        if value is not None and value != '':
            if len(value) != 3:
                raise serializers.ValidationError(
                    "Currency code must be exactly 3 characters"
                )
            if not value.isalpha():
                raise serializers.ValidationError(
                    "Currency code must contain only letters"
                )
            return value.upper()
        return value
    
    def validate(self, data):
        """Validate currency code uniqueness on update"""
        # Si se está actualizando y se proporciona un nuevo currency_code
        if self.instance and data.get('currency_code'):
            new_code = data['currency_code'].upper()
            old_code = self.instance.currency_code.upper()
            # Verificar si el código ya existe y es diferente al actual
            if new_code != old_code:
                if Currency.objects.filter(currency_code=new_code).exists():
                    raise serializers.ValidationError({
                        'currency_code': f"Currency with code '{new_code}' already exists. Use a different code or update the existing one."
                    })
        return data
    
    def create(self, validated_data):
        """Ensure currency code is uppercase on create"""
        if validated_data.get('currency_code'):
            validated_data['currency_code'] = validated_data['currency_code'].upper()
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle currency code update - allow PK changes by creating new record"""
        import logging
        logger = logging.getLogger(__name__)
        
        new_code = validated_data.get('currency_code')
        old_code = instance.currency_code
        
        logger.debug(f"CurrencySerializer.update: old_code={old_code}, new_code={new_code}")
        
        # Si no se proporciona currency_code o está vacío, usar el código actual
        if not new_code or new_code.strip() == '':
            # Eliminar currency_code de validated_data para que no intente actualizarlo
            validated_data.pop('currency_code', None)
            new_code = old_code
        
        # Si se está cambiando el código de moneda
        if new_code.upper() != old_code.upper():
            new_code_upper = new_code.upper()
            
            # Verificar si el nuevo código ya existe (excluyendo el registro actual)
            if Currency.objects.filter(currency_code=new_code_upper).exclude(currency_code=old_code).exists():
                raise serializers.ValidationError({
                    'currency_code': f"Currency with code '{new_code_upper}' already exists."
                })
            
            # Crear un nuevo registro con el nuevo código
            from django.db import transaction
            with transaction.atomic():
                # Copiar todos los datos del registro antiguo
                currency_data = {
                    'currency_code': new_code_upper,
                    'name': validated_data.get('name', instance.name),
                    'symbol': validated_data.get('symbol', instance.symbol),
                    'exchange_rate': validated_data.get('exchange_rate', instance.exchange_rate),
                    'decimals': validated_data.get('decimals', instance.decimals),
                    'is_active': validated_data.get('is_active', instance.is_active),
                    'is_base_currency': validated_data.get('is_base_currency', instance.is_base_currency),
                }
                # Crear el nuevo registro
                new_currency = Currency.objects.create(**currency_data)
                # Eliminar el registro antiguo
                instance.delete()
                logger.debug(f"Currency code changed from {old_code} to {new_code_upper}")
                return new_currency
        
        # Si no se cambia el código, actualizar normalmente
        logger.debug("Currency code not changed, updating in place")
        return super().update(instance, validated_data)


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer for Supplier model"""
    
    class Meta:
        model = Supplier
        fields = [
            'supplier_id', 'supplier_code', 'name', 'contact_person', 'contact_email',
            'contact_phone', 'website', 'address', 'city', 'state', 'country',
            'tax_id', 'payment_terms', 'currency_code', 'rating', 'delivery_time_avg',
            'quality_score', 'status', 'is_preferred', 'is_active',
            'created_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['supplier_id', 'created_at', 'updated_at']
    
    def validate_supplier_code(self, value):
        """Validate supplier code format and uniqueness (excluding current instance during update)"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Supplier code must contain only alphanumeric characters, hyphens, and underscores"
            )
        
        # During update, exclude the current instance from uniqueness check
        if self.instance:
            # Check if another supplier already has this code
            if Supplier.objects.filter(supplier_code=value.upper()).exclude(supplier_id=self.instance.supplier_id).exists():
                raise serializers.ValidationError(
                    "Ya existe un proveedor con este código."
                )
        else:
            # During create, check for any existing supplier with this code
            if Supplier.objects.filter(supplier_code=value.upper()).exists():
                raise serializers.ValidationError(
                    "Ya existe un proveedor con este código."
                )
        
        return value.upper()
    
    def to_internal_value(self, data):
        # Handle empty string values for fields that accept null
        for field_name in ['contact_email', 'contact_phone', 'website', 'address', 'city', 'state', 'country', 'tax_id', 'notes']:
            if field_name in data and data[field_name] == '':
                data = data.copy()  # Make a copy to avoid modifying original
                data[field_name] = None
        
        return super().to_internal_value(data)


class TaxonomySystemSerializer(serializers.ModelSerializer):
    """Serializer for TaxonomySystem model"""
    
    class Meta:
        model = TaxonomySystem
        fields = [
            'system_code', 'category', 'name_es', 'name_en', 'icon',
            'scope', 'sort_order', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class TaxonomySystemListSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for list views.
    Includes subsystems_count annotation from queryset.
    """
    subsystems_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_is_active_display', read_only=True)
    
    class Meta:
        model = TaxonomySystem
        fields = [
            'system_code', 'category', 'name_es', 'name_en', 'icon',
            'sort_order', 'is_active', 'status_display', 'subsystems_count', 'created_at'
        ]
        read_only_fields = ['created_at', 'subsystems_count', 'status_display']


class TaxonomySubsystemSerializer(serializers.ModelSerializer):
    """Serializer for TaxonomySubsystem model"""
    system_name = serializers.CharField(source='system_code.name_es', read_only=True)
    
    class Meta:
        model = TaxonomySubsystem
        fields = [
            'subsystem_code', 'system_code', 'system_name', 'name_es', 'name_en',
            'icon', 'notes', 'sort_order', 'created_at'
        ]
        read_only_fields = ['created_at', 'system_name']


class TaxonomySubsystemListSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for list views.
    Includes groups_count annotation from queryset.
    """
    system_name = serializers.CharField(source='system_code.name_es', read_only=True)
    groups_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = TaxonomySubsystem
        fields = [
            'subsystem_code', 'system_code', 'system_name', 'name_es', 'name_en',
            'sort_order', 'groups_count', 'created_at'
        ]
        read_only_fields = ['created_at', 'system_name', 'groups_count']


class TaxonomyGroupSerializer(serializers.ModelSerializer):
    """Serializer for TaxonomyGroup model"""
    system_name = serializers.CharField(source='system_code.name_es', read_only=True)
    subsystem_name = serializers.CharField(source='subsystem_code.name_es', read_only=True)
    full_path = serializers.CharField(read_only=True)  # From annotation
    
    class Meta:
        model = TaxonomyGroup
        fields = [
            'group_code', 'subsystem_code', 'subsystem_name', 'system_code', 
            'system_name', 'full_path', 'name_es', 'name_en',
            'description', 'examples', 'keywords', 'requires_position',
            'requires_color', 'requires_finish', 'requires_side',
            'typical_position_set', 'typical_uom', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'system_name', 'subsystem_name', 'full_path']


class TaxonomyGroupListSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for list views.
    Minimal fields for faster serialization.
    """
    system_name = serializers.CharField(source='system_code.name_es', read_only=True)
    subsystem_name = serializers.CharField(source='subsystem_code.name_es', read_only=True)
    
    class Meta:
        model = TaxonomyGroup
        fields = [
            'group_code', 'subsystem_code', 'subsystem_name', 
            'system_code', 'system_name', 'name_es', 'name_en',
            'is_active', 'requires_position', 'requires_color',
            'requires_finish', 'requires_side', 'created_at'
        ]
        read_only_fields = ['created_at', 'system_name', 'subsystem_name']


class FitmentSerializer(serializers.ModelSerializer):
    """Serializer for Fitment model"""
    
    class Meta:
        model = Fitment
        fields = [
            'fitment_id', 'internal_sku', 'equipment', 'score', 'notes',
            'verified_by', 'verified_date', 'is_primary_fit', 'created_at'
        ]
        read_only_fields = ['fitment_id', 'created_at']


# =============================================================================
# INV SCHEMA - Additional Inventory Serializers
# =============================================================================

class BinSerializer(serializers.ModelSerializer):
    """Serializer for Bin model"""
    
    class Meta:
        model = Bin
        fields = [
            'bin_id', 'warehouse_code', 'bin_code', 'description', 'zone',
            'aisle', 'rack', 'level', 'position', 'capacity', 'max_weight_kg',
            'current_occupancy', 'temperature_zone', 'hazard_level',
            'is_active', 'created_at'
        ]
        read_only_fields = ['bin_id', 'created_at']


class PriceListSerializer(serializers.ModelSerializer):
    """Serializer for PriceList model"""
    
    class Meta:
        model = PriceList
        fields = [
            'price_list_id', 'price_list_code', 'name', 'description',
            'currency_code', 'is_tax_included', 'is_active',
            'valid_from', 'valid_until', 'created_at', 'updated_at'
        ]
        read_only_fields = ['price_list_id', 'created_at', 'updated_at']


class ProductPriceSerializer(serializers.ModelSerializer):
    """Serializer for ProductPrice model"""
    
    class Meta:
        model = ProductPrice
        fields = [
            'product_price_id', 'price_list', 'internal_sku', 'unit_price',
            'tax_percent', 'discount_percent', 'min_qty',
            'valid_from', 'valid_until'
        ]
        read_only_fields = ['product_price_id']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseOrder model"""
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'po_id', 'po_number', 'supplier', 'order_date',
            'expected_delivery_date', 'actual_delivery_date', 'status',
            'subtotal', 'tax_amount', 'shipping_cost', 'created_by',
            'approved_by', 'created_at', 'updated_at', 'notes'
        ]
        read_only_fields = ['po_id', 'created_at', 'updated_at']
    
    def validate_po_number(self, value):
        """Validate PO number format"""
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "PO number must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper()
    
    def create(self, validated_data):
        """Override create to generate PO number if not provided"""
        po_number = validated_data.get('po_number')
        
        if not po_number:
            # Generate PO number automatically
            from datetime import datetime
            today = datetime.now()
            prefix = f"PO-{today.strftime('%Y%m')}"
            
            # Get last PO number for this month
            last_po = PurchaseOrder.objects.filter(
                po_number__startswith=prefix
            ).order_by('-po_number').first()
            
            if last_po:
                try:
                    last_num = int(last_po.po_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            validated_data['po_number'] = f"{prefix}-{new_num:04d}"
        
        return super().create(validated_data)


class POItemSerializer(serializers.ModelSerializer):
    """Serializer for POItem model"""
    internal_sku = serializers.CharField(
        max_length=20, 
        required=False,  # Making it optional
        allow_blank=True, 
        allow_null=True,
        default=''
    )
    supplier_sku = serializers.PrimaryKeyRelatedField(
        queryset=SupplierSKU.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = POItem
        fields = [
            'po_item_id', 'po', 'internal_sku', 'supplier_sku', 'quantity', 'unit_price',
            'discount_percent', 'tax_percent', 'quantity_received',
            'quantity_rejected', 'notes'
        ]
        read_only_fields = ['po_item_id']
    
    def validate_internal_sku(self, value):
        """Validate internal SKU format and handle null/empty values"""
        # Convert empty string to None
        if value == '' or value is None:
            return None
        
        # Validate format
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Internal SKU must contain only alphanumeric characters, hyphens, and underscores"
            )
        return value.upper() if value else None


class SupplierSKUSerializer(serializers.ModelSerializer):
    """Serializer for SupplierSKU model"""
    internal_sku_code = serializers.CharField(source='internal_sku.internal_sku', read_only=True)
    internal_sku_name = serializers.CharField(source='internal_sku.name', read_only=True)
    supplier_code = serializers.CharField(source='supplier.supplier_code', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = SupplierSKU
        fields = [
            'supplier_sku_id', 'internal_sku', 'internal_sku_code', 'internal_sku_name',
            'supplier', 'supplier_code', 'supplier_name',
            'supplier_sku_code', 'supplier_mpn', 'is_preferred',
            'unit_cost', 'lead_time_days', 'min_order_qty',
            'is_active', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['supplier_sku_id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate unique constraint for internal_sku and supplier"""
        internal_sku = data.get('internal_sku')
        supplier = data.get('supplier')
        
        # During create, check for duplicate
        if not self.instance and internal_sku and supplier:
            if SupplierSKU.objects.filter(internal_sku=internal_sku, supplier=supplier).exists():
                raise serializers.ValidationError(
                    "Ya existe un mapeo de SKU para este producto y proveedor."
                )
        
        # During update, check for duplicate (excluding current instance)
        if self.instance and internal_sku and supplier:
            if SupplierSKU.objects.filter(
                internal_sku=internal_sku, 
                supplier=supplier
            ).exclude(supplier_sku_id=self.instance.supplier_sku_id).exists():
                raise serializers.ValidationError(
                    "Ya existe un mapeo de SKU para este producto y proveedor."
                )
        
        return data


# =============================================================================
# OEM SCHEMA - OEM Catalog Serializers
# =============================================================================

class OEMBrandSerializer(serializers.ModelSerializer):
    """Serializer for OEMBrand model"""
    
    class Meta:
        model = OEMBrand
        fields = [
            'brand_id', 'oem_code', 'name', 'country', 'website',
            'support_email', 'is_active', 'created_at'
        ]
        read_only_fields = ['brand_id', 'created_at']


class OEMCatalogItemSerializer(serializers.ModelSerializer):
    """Serializer for OEMCatalogItem model"""
    
    class Meta:
        model = OEMCatalogItem
        fields = [
            'catalog_id', 'oem_code', 'item_type', 'part_number', 'part_number_type',
            'description_es', 'description_en', 'group_code', 'weight_kg',
            'dimensions', 'material', 'vin_patterns', 'model_codes',
            'body_codes', 'engine_codes', 'transmission_codes', 'axle_codes',
            'color_codes', 'trim_codes', 'manual_types', 'manual_refs',
            'list_price', 'net_price', 'currency_code', 'oem_lead_time_days',
            'is_discontinued', 'is_active', 'valid_from', 'valid_until',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['catalog_id', 'created_at', 'updated_at']


class OEMEquivalenceSerializer(serializers.ModelSerializer):
    """Serializer for OEMEquivalence model"""
    
    class Meta:
        model = OEMEquivalence
        fields = [
            'equivalence_id', 'oem_part_number', 'oem_code', 'aftermarket_sku',
            'equivalence_type', 'confidence_score', 'notes',
            'verified_by', 'verified_date', 'created_at'
        ]
        read_only_fields = ['equivalence_id', 'created_at']


# =============================================================================
# SVC SCHEMA - Additional Service Serializers
# =============================================================================

class WOItemSerializer(serializers.ModelSerializer):
    """Serializer for WOItem model"""
    
    class Meta:
        model = WOItem
        fields = [
            'item_id', 'wo', 'internal_sku', 'qty_ordered', 'qty_used',
            'qty_returned', 'unit_price', 'discount_percent', 'tax_percent',
            'reserved_stock_id', 'reserved_stock_date', 'used_stock_id',
            'used_stock_date', 'status', 'notes', 'created_at'
        ]
        read_only_fields = ['item_id', 'created_at']


class FlatRateStandardSerializer(serializers.ModelSerializer):
    """Serializer for FlatRateStandard model"""
    
    class Meta:
        model = FlatRateStandard
        fields = [
            'standard_id', 'service_code', 'description_es', 'description_en',
            'equipment_type', 'group_code', 'standard_hours', 'min_hours',
            'max_hours', 'difficulty_level', 'required_tools', 'required_skills',
            'manual_source', 'manual_ref', 'oem_ref', 'valid_from',
            'valid_until', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['standard_id', 'created_at', 'updated_at']


class WOServiceSerializer(serializers.ModelSerializer):
    """Serializer for WOService model"""
    
    class Meta:
        model = WOService
        fields = [
            'service_id', 'wo', 'flat_rate', 'service_code', 'description',
            'flat_hours', 'estimated_hours', 'actual_hours', 'hourly_rate',
            'completion_status', 'technician', 'started_at', 'completed_at',
            'notes', 'created_at'
        ]
        read_only_fields = ['service_id', 'created_at']


class ServiceChecklistSerializer(serializers.ModelSerializer):
    """Serializer for ServiceChecklist model"""
    
    class Meta:
        model = ServiceChecklist
        fields = [
            'checklist_id', 'flat_rate', 'description', 'sequence_no',
            'is_critical', 'expected_result', 'tool_required', 'estimated_minutes'
        ]
        read_only_fields = ['checklist_id']


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem model"""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'invoice_item_id', 'invoice', 'internal_sku', 'description',
            'qty', 'unit_price', 'tax_percent', 'discount_percent'
        ]
        read_only_fields = ['invoice_item_id']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'invoice', 'payment_date', 'amount', 'currency_code',
            'payment_method', 'reference_number', 'notes', 'created_at'
        ]
        read_only_fields = ['payment_id', 'created_at']


class QuoteItemSerializer(serializers.ModelSerializer):
    """Serializer for QuoteItem model"""
    
    class Meta:
        model = QuoteItem
        fields = [
            'quote_item_id', 'quote', 'flat_rate', 'service_code', 'description',
            'quantity', 'hours', 'hourly_rate', 'line_total', 'notes'
        ]
        read_only_fields = ['quote_item_id', 'line_total']


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for Quote model"""
    items = QuoteItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'quote_id', 'quote_number', 'client', 'equipment', 'status',
            'quote_date', 'valid_until', 'subtotal', 'discount_percent',
            'discount_amount', 'tax_percent', 'tax_amount', 'total',
            'total_hours', 'currency_code', 'notes', 'terms_and_conditions',
            'created_by', 'converted_to_wo', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = [
            'quote_id', 'quote_number', 'subtotal', 'discount_amount',
            'tax_amount', 'total', 'total_hours', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Override create to generate quote number"""
        quote = Quote(**validated_data)
        quote.generate_quote_number()
        quote.save()
        return quote


# =============================================================================
# KPI SCHEMA - Key Performance Indicators Serializers
# =============================================================================

class WOMetricSerializer(serializers.ModelSerializer):
    """Serializer for WOMetric model"""
    
    class Meta:
        model = WOMetric
        fields = [
            'metric_id', 'wo', 'efficiency_score', 'productivity_score',
            'quality_score', 'customer_satisfaction', 'lead_time_days',
            'process_time_days', 'wait_time_days', 'parts_fill_rate',
            'parts_accuracy', 'return_rate', 'profitability',
            'labor_utilization', 'created_at', 'updated_at'
        ]
        read_only_fields = ['metric_id', 'created_at', 'updated_at']