"""
URL configuration for the core app.

This module defines all the API endpoints for the ForgeDB system,
organized by functional areas.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.auth_views import (
    CustomTokenObtainPairView,
    refresh_token,
    logout,
    user_profile,
    update_profile,
    change_password,
    check_permission,
    user_permissions,
)

# Dashboard views
from .views.dashboard_views import dashboard_data, health_check, kpi_details

# Health check views
from .views.health_views import HealthCheckView, DetailedHealthCheckView, SimpleHealthView

# Notification views
from .views.notification_views import (
    notifications_list, mark_notification_read, 
    mark_all_notifications_read, notification_summary
)

# Stored procedures views
from .views.stored_procedures_views import (
    reserve_stock, release_reserved_stock, auto_replenishment, 
    calculate_inventory_aging, advance_work_order_status,
    add_service_to_work_order, create_invoice_from_work_order
)

# Analytics stored procedures views
from .views.analytics_stored_procedures_views import (
    abc_analysis_inventory, technician_productivity_report,
    demand_forecasting, financial_kpi_dashboard
)

# Create a router for ViewSets
router = DefaultRouter()

# Register ViewSets
from .views import (
    ClientViewSet, EquipmentViewSet, TechnicianViewSet,
    ProductMasterViewSet, StockViewSet, TransactionViewSet,
    WorkOrderViewSet, InvoiceViewSet, AlertViewSet,
    DocumentViewSet, BusinessRuleViewSet, AuditLogViewSet,
    WarehouseViewSet,
    # Catalog
    CategoryViewSet, EquipmentTypeViewSet, FuelCodeViewSet, AspirationCodeViewSet,
    TransmissionCodeViewSet, DrivetrainCodeViewSet, ColorCodeViewSet,
    PositionCodeViewSet, FinishCodeViewSet, SourceCodeViewSet,
    ConditionCodeViewSet, UOMCodeViewSet, CurrencyViewSet,
    SupplierViewSet,
    TaxonomySystemViewSet, TaxonomySubsystemViewSet, TaxonomyGroupViewSet,
    FitmentViewSet,
    # Inventory
    BinViewSet, PriceListViewSet, ProductPriceViewSet,
    PurchaseOrderViewSet, POItemViewSet,
    # OEM
    OEMBrandViewSet, OEMCatalogItemViewSet, OEMEquivalenceViewSet,
    # Service
    WOItemViewSet, WOServiceViewSet, FlatRateStandardViewSet,
    ServiceChecklistViewSet, InvoiceItemViewSet, PaymentViewSet,
    QuoteViewSet, QuoteItemViewSet,
    WOItemViewSet, WOServiceViewSet, FlatRateStandardViewSet,
    ServiceChecklistViewSet, InvoiceItemViewSet, PaymentViewSet,
    # KPI
    WOMetricViewSet
)

# Core ViewSets
router.register(r'clients', ClientViewSet)
router.register(r'equipment', EquipmentViewSet)
router.register(r'technicians', TechnicianViewSet)
router.register(r'products', ProductMasterViewSet)
router.register(r'stock', StockViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'work-orders', WorkOrderViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'alerts', AlertViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'business-rules', BusinessRuleViewSet)
router.register(r'audit-logs', AuditLogViewSet)
router.register(r'warehouses', WarehouseViewSet)

# Catalog ViewSets
router.register(r'categories', CategoryViewSet)
router.register(r'equipment-types', EquipmentTypeViewSet)
router.register(r'fuel-codes', FuelCodeViewSet)
router.register(r'aspiration-codes', AspirationCodeViewSet)
router.register(r'transmission-codes', TransmissionCodeViewSet)
router.register(r'drivetrain-codes', DrivetrainCodeViewSet)
router.register(r'color-codes', ColorCodeViewSet)
router.register(r'position-codes', PositionCodeViewSet)
router.register(r'finish-codes', FinishCodeViewSet)
router.register(r'source-codes', SourceCodeViewSet)
router.register(r'condition-codes', ConditionCodeViewSet)
router.register(r'uom-codes', UOMCodeViewSet)
router.register(r'currencies', CurrencyViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'taxonomy-systems', TaxonomySystemViewSet)
router.register(r'taxonomy-subsystems', TaxonomySubsystemViewSet)
router.register(r'taxonomy-groups', TaxonomyGroupViewSet)
router.register(r'fitments', FitmentViewSet)

# Inventory ViewSets
router.register(r'bins', BinViewSet)
router.register(r'price-lists', PriceListViewSet)
router.register(r'product-prices', ProductPriceViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'po-items', POItemViewSet)

# OEM ViewSets
router.register(r'oem-brands', OEMBrandViewSet)
router.register(r'oem-catalog-items', OEMCatalogItemViewSet)
router.register(r'oem-equivalences', OEMEquivalenceViewSet)

# Service ViewSets
router.register(r'wo-items', WOItemViewSet)
router.register(r'wo-services', WOServiceViewSet)
router.register(r'flat-rate-standards', FlatRateStandardViewSet)
router.register(r'service-checklists', ServiceChecklistViewSet)
router.register(r'invoice-items', InvoiceItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'quotes', QuoteViewSet)
router.register(r'quote-items', QuoteItemViewSet)

# KPI ViewSets
router.register(r'wo-metrics', WOMetricViewSet)

app_name = 'core'

urlpatterns = [
    # Health check endpoints
    path('health/', HealthCheckView.as_view(), name='health_check_simple'),
    path('health/detailed/', DetailedHealthCheckView.as_view(), name='health_check_detailed'),
    path('ping/', SimpleHealthView.as_view(), name='ping'),
    
    # Dashboard endpoints
    path('dashboard/', dashboard_data, name='dashboard_data'),
    path('dashboard/kpi/<str:kpi_type>/', kpi_details, name='kpi_details'),
    
    # Notification endpoints
    path('notifications/', notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/summary/', notification_summary, name='notification_summary'),
    
    # Authentication endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', refresh_token, name='token_refresh'),
    path('auth/logout/', logout, name='logout'),
    path('auth/profile/', user_profile, name='user_profile'),
    path('auth/profile/update/', update_profile, name='update_profile'),
    path('auth/change-password/', change_password, name='change_password'),
    path('auth/check-permission/', check_permission, name='check_permission'),
    path('auth/permissions/', user_permissions, name='user_permissions'),
    
    # API endpoints (will be populated as ViewSets are created)
    path('', include(router.urls)),

    # Stored procedures endpoints
    path('inventory/reserve-stock/', reserve_stock, name='reserve_stock'),
    path('inventory/release-reserved-stock/', release_reserved_stock, name='release_reserved_stock'),
    path('inventory/auto-replenishment/', auto_replenishment, name='auto_replenishment'),
    path('inventory/aging/', calculate_inventory_aging, name='calculate_inventory_aging'),
    # Work order stored procedure endpoints
    path('work-orders/advance-status/', advance_work_order_status, name='advance_work_order_status'),
    path('work-orders/add-service/', add_service_to_work_order, name='add_service_to_work_order'),
    path('work-orders/create-invoice/', create_invoice_from_work_order, name='create_invoice_from_work_order'),
    # Analytics/KPI stored procedure endpoints
    path('analytics/abc-analysis/', abc_analysis_inventory, name='abc_analysis_inventory'),
    path('analytics/technician-productivity/', technician_productivity_report, name='technician_productivity_report'),
    path('analytics/demand-forecast/', demand_forecasting, name='demand_forecasting'),
    path('analytics/financial-kpis/', financial_kpi_dashboard, name='financial_kpi_dashboard'),

    # Custom endpoints will be added here
    # path('custom-endpoint/', CustomView.as_view(), name='custom-endpoint'),
]