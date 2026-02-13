"""
Django admin configuration for ForgeDB Core models.

This module configures the Django admin interface for managing
ForgeDB entities through the web interface.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Alert, BusinessRule, AuditLog, Technician,
    Client, Equipment, Warehouse, ProductMaster,
    Stock, Transaction, WorkOrder, Invoice, Document,
    # Catalog models
    EquipmentType, FuelCode, AspirationCode, TransmissionCode, DrivetrainCode,
    ColorCode, PositionCode, FinishCode, SourceCode, ConditionCode, UOMCode,
    ProductCategory, ProductType,
    Currency, Supplier, TaxonomySystem, TaxonomySubsystem, TaxonomyGroup, Fitment,
    # Inventory models
    Bin, PriceList, ProductPrice, PurchaseOrder, POItem,
    # OEM models
    BrandType, OEMBrand, OEMCatalogItem, OEMEquivalence,
    # Service models
    WOItem, WOService, FlatRateStandard, ServiceChecklist, InvoiceItem, Payment,
    # KPI models
    WOMetric
)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_id', 'alert_type', 'title', 'severity', 'status', 'created_at')
    list_filter = ('alert_type', 'severity', 'status', 'created_at')
    search_fields = ('title', 'message', 'ref_code')
    ordering = ('-created_at',)
    readonly_fields = ('alert_id', 'created_at', 'read_at', 'acknowledged_at', 'resolved_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('alert_id', 'alert_type', 'title', 'message', 'details')
        }),
        ('Status', {
            'fields': ('severity', 'status', 'assigned_to', 'created_for')
        }),
        ('References', {
            'fields': ('ref_entity', 'ref_id', 'ref_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'read_at', 'acknowledged_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BusinessRule)
class BusinessRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_code', 'rule_name', 'condition_type', 'action_type', 'is_active', 'created_at')
    list_filter = ('condition_type', 'action_type', 'is_active', 'created_at')
    search_fields = ('rule_code', 'rule_name', 'condition_text', 'action_text')
    ordering = ('-created_at',)
    readonly_fields = ('rule_id', 'created_at', 'updated_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('audit_id', 'table_name', 'action', 'record_id', 'changed_by', 'changed_at')
    list_filter = ('table_name', 'action', 'changed_at')
    search_fields = ('table_name', 'record_id', 'changed_by__username')
    ordering = ('-changed_at',)
    readonly_fields = ('audit_id', 'table_name', 'record_id', 'action', 'changed_by', 
                       'changed_at', 'old_values', 'new_values', 'ip_address', 'user_agent')
    date_hierarchy = 'changed_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('technician_id', 'first_name', 'last_name', 'email', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'employee_number')
    ordering = ('-created_at',)
    readonly_fields = ('technician_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('technician_id', 'first_name', 'last_name', 'email', 'phone', 'employee_number')
        }),
        ('Specializations', {
            'fields': ('specializations',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_code', 'name', 'type', 'status', 'email', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('client_code', 'name', 'legal_name', 'email', 'phone', 'tax_id')
    ordering = ('-created_at',)
    readonly_fields = ('client_id', 'uuid', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('client_id', 'uuid', 'client_code', 'type', 'name', 'legal_name', 'tax_id')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'mobile', 'preferred_contact_method', 'send_reminders')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('credit_limit', 'credit_used', 'payment_days')
        }),
        ('Status', {
            'fields': ('status', 'created_by', 'created_at', 'updated_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('equipment_code', 'get_display_name', 'client_id', 'brand', 'model', 'year', 'status', 'created_at')
    list_filter = ('status', 'brand', 'year', 'created_at')
    search_fields = ('equipment_code', 'vin', 'license_plate', 'brand', 'model')
    ordering = ('-created_at',)
    readonly_fields = ('equipment_id', 'uuid', 'created_at', 'updated_at')
    
    def get_display_name(self, obj):
        year_str = str(obj.year) if obj.year else 'N/A'
        return f"{year_str} {obj.brand} {obj.model}"
    get_display_name.short_description = 'Vehicle'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('equipment_id', 'uuid', 'equipment_code', 'client_id', 'type_id')
        }),
        ('Identification', {
            'fields': ('vin', 'license_plate', 'serial_number', 'year', 'brand', 'model')
        }),
        ('Details', {
            'fields': ('engine_desc', 'transmission_code', 'color', 'fuel_code', 'current_mileage_hours',
                      'submodel_trim', 'body_style', 'doors', 'aspiration_code', 'drivetrain_code')
        }),
        ('Warranty', {
            'fields': ('purchase_date', 'warranty_until',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('warehouse_code', 'name', 'type', 'address', 'is_active', 'created_at')
    list_filter = ('is_active', 'type', 'created_at')
    search_fields = ('warehouse_code', 'name', 'address', 'manager')
    ordering = ('warehouse_code',)
    readonly_fields = ('created_at',)


@admin.register(ProductMaster)
class ProductMasterAdmin(admin.ModelAdmin):
    list_display = ('internal_sku', 'name', 'brand', 'group_code', 'is_active', 'created_at')
    list_filter = ('is_active', 'group_code', 'source_code', 'condition_code', 'created_at')
    search_fields = ('internal_sku', 'name', 'barcode', 'brand', 'oem_ref', 'supplier_mpn')
    ordering = ('internal_sku',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('stock_id', 'product', 'warehouse', 'qty_on_hand', 'qty_available', 'updated_at')
    list_filter = ('warehouse', 'updated_at', 'status')
    search_fields = ('product__internal_sku', 'product__name', 'warehouse__name', 'warehouse__warehouse_code')
    ordering = ('-updated_at',)
    readonly_fields = ('stock_id', 'created_at', 'updated_at')
    raw_id_fields = ('product', 'warehouse')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'product', 'warehouse', 'transaction_type', 'quantity', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date', 'warehouse')
    search_fields = ('product__product_code', 'product__name', 'reference_number')
    ordering = ('-transaction_date',)
    readonly_fields = ('transaction_id', 'transaction_date')
    raw_id_fields = ('product', 'warehouse', 'created_by')
    date_hierarchy = 'transaction_date'


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('wo_number', 'client_id', 'equipment_id', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'service_type', 'created_at')
    search_fields = ('wo_number', 'customer_complaints', 'initial_findings', 'technician_notes')
    ordering = ('-created_at',)
    readonly_fields = ('wo_id', 'created_at', 'updated_at', 'closed_at', 'actual_completion_date')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('wo_id', 'wo_number', 'client_id', 'equipment_id', 'status', 'priority', 'service_type')
        }),
        ('Dates', {
            'fields': ('appointment_date', 'reception_date', 'diagnosis_date', 'actual_start_date', 'actual_completion_date', 'delivery_date')
        }),
        ('Work Details', {
            'fields': ('customer_complaints', 'initial_findings', 'technician_notes', 'qc_notes', 'final_report')
        }),
        ('Hours & Efficiency', {
            'fields': ('flat_rate_hours', 'estimated_hours', 'actual_hours', 'efficiency_rate')
        }),
        ('Costs & Pricing', {
            'fields': ('labor_rate', 'labor_cost', 'parts_cost', 'additional_costs', 'total_cost', 'quoted_price', 'discount_amount', 'final_price')
        }),
        ('Personnel', {
            'fields': ('advisor_id', 'technician_id', 'qc_technician_id', 'created_by')
        }),
        ('Vehicle Tracking', {
            'fields': ('mileage_in', 'mileage_out', 'hours_in', 'hours_out'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'closed_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client_id', 'wo_id', 'status', 'total_amount', 'due_date', 'issue_date')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number',)
    ordering = ('-issue_date',)
    readonly_fields = ('invoice_id', 'created_at', 'updated_at')
    date_hierarchy = 'issue_date'
    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_id', 'invoice_number', 'client_id', 'wo_id', 'status', 'currency_code')
        }),
        ('Financial', {
            'fields': ('issue_date', 'due_date', 'paid_date', 'subtotal', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_id', 'document_type', 'title', 'ref_entity', 'ref_id', 'uploaded_at')
    list_filter = ('document_type', 'ref_entity', 'uploaded_at', 'is_public')
    search_fields = ('title', 'description', 'file_name', 'ref_code')
    ordering = ('-uploaded_at',)
    readonly_fields = ('document_id', 'uuid', 'file_size', 'uploaded_at')
    raw_id_fields = ('uploaded_by',)
    date_hierarchy = 'uploaded_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('document_id', 'uuid', 'document_type', 'title', 'description')
        }),
        ('File', {
            'fields': ('file_name', 'file_path', 'file_size', 'mime_type', 'is_public')
        }),
        ('References', {
            'fields': ('ref_entity', 'ref_id'),
            'classes': ('collapse',)
        }),
        ('Upload', {
            'fields': ('uploaded_by', 'uploaded_at')
        }),
    )


# =============================================================================
# CAT SCHEMA - Catalog Reference Models Admin
# =============================================================================

@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ('type_code', 'name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('type_code', 'name', 'description')
    ordering = ('category', 'name')
    readonly_fields = ('type_id', 'created_at', 'updated_at')


@admin.register(FuelCode)
class FuelCodeAdmin(admin.ModelAdmin):
    list_display = ('fuel_code', 'name_es', 'name_en', 'is_alternative')
    search_fields = ('fuel_code', 'name_es', 'name_en')
    ordering = ('fuel_code',)


@admin.register(AspirationCode)
class AspirationCodeAdmin(admin.ModelAdmin):
    list_display = ('aspiration_code', 'name_es', 'name_en')
    search_fields = ('aspiration_code', 'name_es', 'name_en')
    ordering = ('aspiration_code',)


@admin.register(TransmissionCode)
class TransmissionCodeAdmin(admin.ModelAdmin):
    list_display = ('transmission_code', 'name_es', 'name_en')
    search_fields = ('transmission_code', 'name_es', 'name_en')
    ordering = ('transmission_code',)


@admin.register(DrivetrainCode)
class DrivetrainCodeAdmin(admin.ModelAdmin):
    list_display = ('drivetrain_code', 'name_es', 'name_en')
    search_fields = ('drivetrain_code', 'name_es', 'name_en')
    ordering = ('drivetrain_code',)


@admin.register(ColorCode)
class ColorCodeAdmin(admin.ModelAdmin):
    list_display = ('color_code', 'name_es', 'brand', 'is_metallic', 'sort_order')
    list_filter = ('brand', 'is_metallic')
    search_fields = ('color_code', 'name_es', 'name_en', 'brand')
    ordering = ('brand', 'sort_order', 'color_code')
    readonly_fields = ('color_id', 'created_at')


@admin.register(PositionCode)
class PositionCodeAdmin(admin.ModelAdmin):
    list_display = ('position_code', 'name_es', 'category', 'sort_order')
    list_filter = ('category',)
    search_fields = ('position_code', 'name_es', 'name_en')
    ordering = ('sort_order', 'position_code')
    readonly_fields = ('created_at',)


@admin.register(FinishCode)
class FinishCodeAdmin(admin.ModelAdmin):
    list_display = ('finish_code', 'name_es', 'requires_color', 'sort_order')
    list_filter = ('requires_color',)
    search_fields = ('finish_code', 'name_es', 'name_en')
    ordering = ('sort_order', 'finish_code')
    readonly_fields = ('created_at',)


@admin.register(SourceCode)
class SourceCodeAdmin(admin.ModelAdmin):
    list_display = ('source_code', 'name_es', 'quality_level', 'sort_order')
    list_filter = ('quality_level',)
    search_fields = ('source_code', 'name_es', 'name_en')
    ordering = ('sort_order', 'source_code')


@admin.register(ConditionCode)
class ConditionCodeAdmin(admin.ModelAdmin):
    list_display = ('condition_code', 'name_es', 'requires_core', 'sort_order')
    list_filter = ('requires_core',)
    search_fields = ('condition_code', 'name_es', 'name_en')
    ordering = ('sort_order', 'condition_code')


@admin.register(UOMCode)
class UOMCodeAdmin(admin.ModelAdmin):
    list_display = ('uom_code', 'name_es', 'category', 'is_fractional')
    list_filter = ('category', 'is_fractional')
    search_fields = ('uom_code', 'name_es', 'name_en')
    ordering = ('uom_code',)


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_es', 'name_en', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'code')
    search_fields = ('code', 'name_es', 'name_en')


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_es', 'name_en', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'code')
    search_fields = ('code', 'name_es', 'name_en')


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('currency_code', 'name', 'symbol', 'exchange_rate', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('currency_code', 'name', 'symbol')
    ordering = ('currency_code',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_code', 'name', 'status', 'is_preferred', 'country', 'rating')
    list_filter = ('status', 'is_active', 'is_preferred', 'country')
    search_fields = ('supplier_code', 'name', 'contact_person', 'contact_email', 'contact_phone')
    ordering = ('name',)
    readonly_fields = ('supplier_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('supplier_id', 'supplier_code', 'name', 'status', 'is_preferred', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_email', 'contact_phone', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'tax_id')
        }),
        ('Terms & Ratings', {
            'fields': ('payment_terms', 'currency_code', 'rating', 'quality_score', 'delivery_time_avg')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaxonomySystem)
class TaxonomySystemAdmin(admin.ModelAdmin):
    list_display = ('system_code', 'name_es', 'category', 'is_active', 'sort_order')
    list_filter = ('category', 'is_active')
    search_fields = ('system_code', 'name_es', 'name_en')
    ordering = ('sort_order', 'system_code')
    readonly_fields = ('created_at',)


@admin.register(TaxonomySubsystem)
class TaxonomySubsystemAdmin(admin.ModelAdmin):
    list_display = ('subsystem_code', 'name_es', 'system_code', 'sort_order')
    list_filter = ('system_code',)
    search_fields = ('subsystem_code', 'name_es', 'name_en')
    ordering = ('system_code', 'sort_order', 'subsystem_code')
    readonly_fields = ('created_at',)


@admin.register(TaxonomyGroup)
class TaxonomyGroupAdmin(admin.ModelAdmin):
    list_display = ('group_code', 'name_es', 'system_code', 'subsystem_code', 'is_active')
    list_filter = ('system_code', 'subsystem_code', 'is_active')
    search_fields = ('group_code', 'name_es', 'name_en', 'description')
    ordering = ('system_code', 'subsystem_code', 'name_es')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('system_code', 'subsystem_code')


@admin.register(Fitment)
class FitmentAdmin(admin.ModelAdmin):
    list_display = ('fitment_id', 'internal_sku', 'equipment', 'score', 'is_primary_fit', 'verified_by')
    list_filter = ('is_primary_fit', 'verified_by')
    search_fields = ('internal_sku', 'notes')
    ordering = ('equipment', '-is_primary_fit', '-score')
    readonly_fields = ('fitment_id', 'created_at')
    raw_id_fields = ('equipment', 'verified_by')


# =============================================================================
# INV SCHEMA - Additional Inventory Models Admin
# =============================================================================

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('bin_code', 'warehouse_code', 'zone', 'aisle', 'rack', 'level', 'is_active')
    list_filter = ('warehouse_code', 'zone', 'is_active', 'hazard_level')
    search_fields = ('bin_code', 'description', 'zone', 'aisle')
    ordering = ('warehouse_code', 'zone', 'aisle', 'rack', 'level')
    readonly_fields = ('bin_id', 'created_at')
    raw_id_fields = ('warehouse_code',)


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ('price_list_code', 'name', 'currency_code', 'is_active', 'valid_from', 'valid_until')
    list_filter = ('currency_code', 'is_active', 'is_tax_included')
    search_fields = ('price_list_code', 'name', 'description')
    ordering = ('price_list_code',)
    readonly_fields = ('price_list_id', 'created_at', 'updated_at')


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ('product_price_id', 'price_list', 'internal_sku', 'unit_price', 'valid_from', 'valid_until')
    list_filter = ('price_list', 'valid_from', 'valid_until')
    search_fields = ('internal_sku',)
    ordering = ('price_list', 'internal_sku', '-valid_from')
    readonly_fields = ('product_price_id',)
    raw_id_fields = ('price_list',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'status', 'order_date', 'subtotal', 'created_by')
    list_filter = ('status', 'order_date', 'supplier')
    search_fields = ('po_number', 'notes')
    ordering = ('-order_date', 'po_number')
    readonly_fields = ('po_id', 'created_at', 'updated_at')
    raw_id_fields = ('supplier', 'created_by', 'approved_by')
    date_hierarchy = 'order_date'


@admin.register(POItem)
class POItemAdmin(admin.ModelAdmin):
    list_display = ('po_item_id', 'po', 'internal_sku', 'quantity', 'unit_price', 'quantity_received')
    list_filter = ('po',)
    search_fields = ('internal_sku', 'notes')
    ordering = ('po', 'po_item_id')
    readonly_fields = ('po_item_id',)
    raw_id_fields = ('po',)


# =============================================================================
# OEM SCHEMA - OEM Models Admin
# =============================================================================

@admin.register(BrandType)
class BrandTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_es', 'name_en', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'code')
    search_fields = ('code', 'name_es', 'name_en')


@admin.register(OEMBrand)
class OEMBrandAdmin(admin.ModelAdmin):
    list_display = ('oem_code', 'name', 'brand_type', 'country', 'is_active', 'created_at')
    list_filter = ('is_active', 'brand_type', 'country')
    search_fields = ('oem_code', 'name', 'country')
    ordering = ('name',)
    readonly_fields = ('brand_id', 'created_at')


@admin.register(OEMCatalogItem)
class OEMCatalogItemAdmin(admin.ModelAdmin):
    list_display = ('catalog_id', 'oem_code', 'part_number', 'group_code', 'is_discontinued')
    list_filter = ('oem_code', 'group_code', 'is_discontinued')
    search_fields = ('part_number', 'description_es', 'description_en')
    ordering = ('oem_code', 'part_number')
    readonly_fields = ('catalog_id', 'created_at', 'updated_at')
    raw_id_fields = ('oem_code', 'group_code')


@admin.register(OEMEquivalence)
class OEMEquivalenceAdmin(admin.ModelAdmin):
    list_display = ('equivalence_id', 'oem_code', 'oem_part_number', 'aftermarket_sku', 'equivalence_type', 'confidence_score')
    list_filter = ('oem_code', 'equivalence_type', 'verified_by')
    search_fields = ('oem_part_number', 'aftermarket_sku', 'notes')
    ordering = ('oem_code', 'oem_part_number')
    readonly_fields = ('equivalence_id', 'created_at')
    raw_id_fields = ('oem_code', 'verified_by')


# =============================================================================
# SVC SCHEMA - Additional Service Models Admin
# =============================================================================

@admin.register(WOItem)
class WOItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'wo', 'internal_sku', 'qty_used', 'unit_price', 'status')
    list_filter = ('status', 'wo')
    search_fields = ('internal_sku', 'notes')
    ordering = ('wo', 'item_id')
    readonly_fields = ('item_id', 'created_at')
    raw_id_fields = ('wo',)


@admin.register(WOService)
class WOServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'wo', 'service_code', 'actual_hours', 'completion_status', 'technician')
    list_filter = ('completion_status', 'wo', 'technician')
    search_fields = ('description', 'service_code', 'notes')
    ordering = ('wo', 'service_id')
    readonly_fields = ('service_id', 'created_at')
    raw_id_fields = ('wo', 'flat_rate', 'technician')


@admin.register(FlatRateStandard)
class FlatRateStandardAdmin(admin.ModelAdmin):
    list_display = ('service_code', 'description_es', 'standard_hours', 'equipment_type', 'is_active')
    list_filter = ('equipment_type', 'group_code', 'is_active')
    search_fields = ('service_code', 'description_es', 'description_en')
    ordering = ('service_code',)
    readonly_fields = ('standard_id', 'created_at', 'updated_at')
    raw_id_fields = ('equipment_type', 'group_code')


@admin.register(ServiceChecklist)
class ServiceChecklistAdmin(admin.ModelAdmin):
    list_display = ('checklist_id', 'flat_rate', 'sequence_no', 'description', 'is_critical')
    list_filter = ('flat_rate', 'is_critical')
    search_fields = ('description', 'expected_result', 'tool_required')
    ordering = ('flat_rate', 'sequence_no')
    readonly_fields = ('checklist_id',)
    raw_id_fields = ('flat_rate',)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice_item_id', 'invoice', 'internal_sku', 'qty', 'unit_price')
    list_filter = ('invoice',)
    search_fields = ('description', 'internal_sku')
    ordering = ('invoice', 'invoice_item_id')
    readonly_fields = ('invoice_item_id',)
    raw_id_fields = ('invoice',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'invoice', 'payment_date', 'amount', 'payment_method', 'reference_number')
    list_filter = ('payment_method', 'currency_code', 'payment_date')
    search_fields = ('reference_number', 'notes')
    ordering = ('-payment_date', 'invoice')
    readonly_fields = ('payment_id', 'created_at')
    raw_id_fields = ('invoice',)
    date_hierarchy = 'payment_date'


# =============================================================================
# KPI SCHEMA - KPI Models Admin
# =============================================================================

@admin.register(WOMetric)
class WOMetricAdmin(admin.ModelAdmin):
    list_display = ('metric_id', 'wo', 'efficiency_score', 'quality_score', 'profitability', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('wo__wo_number',)
    ordering = ('-created_at',)
    readonly_fields = ('metric_id', 'created_at', 'updated_at')
    raw_id_fields = ('wo',)
