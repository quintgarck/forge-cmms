"""
URL configuration for frontend app.
"""
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from . import views
from . import views_notification
from .views import diagnostic_views, catalog_views, service_advanced_views, oem_views, alert_views, equipment_type_views, taxonomy_views, reference_code_views, currency_views, currency_rate_views, product_catalog_views
from .views import oem_equivalence_views, fitment_views, oem_import_views, unified_search_views, oem_ui_views
from .views.currency_history_views import (
    CurrencyHistoryComparisonView,
    CurrencyHistoryComparisonAPIView,
    CurrencyAlertsAPIView,
    CurrencyHistoryEnhancedView
)
from .views.service_stats_api_view import ServiceStatsAPIView
from .views.service_charts_api_views import (
    ServiceProductivityAPIView,
    ServiceCategoriesAPIView,
    ServiceTrendsAPIView,
    ServiceComparisonAPIView
)
from .views.service_alerts_views import (
    ServiceAlertsAPIView,
    ServiceAlertsListView,
    ServiceAlertThresholdsView
)
from .views.service_alerts_sse_views import ServiceAlertsSSEView
from .views.quote_views import (
    QuoteListView,
    QuoteDetailView,
    QuoteCreateView,
    QuoteConvertToWorkOrderView,
    QuotePDFView
)
from .diagnostic_client_form import ClientFormDiagnosticView, ClientFormDebugView

# Import main views.py file directly to avoid the views package
import importlib.util
import os

# Load the main views.py file
views_path = os.path.join(os.path.dirname(__file__), 'views.py')
spec = importlib.util.spec_from_file_location("main_views", views_path)
main_views = importlib.util.module_from_spec(spec)
main_views.__package__ = 'frontend'
spec.loader.exec_module(main_views)

app_name = 'frontend'

urlpatterns = [
    # Authentication
    path('login/', main_views.LoginView.as_view(), name='login'),
    path('logout/', main_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('', main_views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', main_views.DashboardView.as_view(), name='dashboard'),

    # Clients
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),

    # Work Orders
    path('workorders/', main_views.WorkOrderListView.as_view(), name='workorder_list'),
    path('workorders/create/', main_views.WorkOrderCreateView.as_view(), name='workorder_create'),
    path('workorders/<int:pk>/', main_views.WorkOrderDetailView.as_view(), name='workorder_detail'),
    path('workorders/<int:pk>/edit/', main_views.WorkOrderUpdateView.as_view(), name='workorder_update'),
    path('workorders/<int:pk>/delete/', main_views.WorkOrderDeleteView.as_view(), name='workorder_delete'),

    # Inventory
    path('inventory/', main_views.InventoryListView.as_view(), name='inventory_list'),
    path('inventory/products/', main_views.ProductListView.as_view(), name='product_list'),
    path('inventory/products/create/', main_views.ProductCreateView.as_view(), name='product_create'),
    path('inventory/products/<int:pk>/', main_views.ProductDetailView.as_view(), name='product_detail'),
    path('inventory/products/<int:pk>/edit/', main_views.ProductUpdateView.as_view(), name='product_update'),

    # Stock Management
    path('inventory/stock/', main_views.StockListView.as_view(), name='stock_list'),
    path('inventory/stock/dashboard/', main_views.StockDashboardView.as_view(), name='stock_dashboard'),
    path('inventory/stock/movements/', main_views.StockMovementsView.as_view(), name='stock_movements'),
    path('inventory/stock/movements/create/', main_views.StockMovementCreateView.as_view(), name='stock_movement_create'),

    # Transaction Management
    path('inventory/transactions/', main_views.TransactionListView.as_view(), name='transaction_list'),

    # Warehouse Management
    path('inventory/warehouses/', main_views.WarehouseListView.as_view(), name='warehouse_list'),
    path('inventory/warehouses/create/', main_views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('inventory/warehouses/<int:warehouse_id>/', main_views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('inventory/warehouses/<int:warehouse_id>/edit/', main_views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('inventory/warehouses/<int:warehouse_id>/delete/', main_views.WarehouseDeleteView.as_view(), name='warehouse_delete'),

    # Inventory Reports
    path('inventory/reports/', main_views.InventoryReportsView.as_view(), name='inventory_reports'),

    # Equipment
    path('equipment/', views.EquipmentListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.EquipmentCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment_delete'),

    # Technicians
    path('technicians/', views.TechnicianListView.as_view(), name='technician_list'),
    path('technicians/create/', views.TechnicianCreateView.as_view(), name='technician_create'),
    path('technicians/<int:pk>/', views.TechnicianDetailView.as_view(), name='technician_detail'),
    path('technicians/<int:pk>/edit/', views.TechnicianUpdateView.as_view(), name='technician_update'),
    path('technicians/<int:pk>/delete/', views.TechnicianDeleteView.as_view(), name='technician_delete'),

    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),

    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),

    # Purchase Orders
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('purchase-orders/create/', views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/edit/', views.PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
    path('purchase-orders/<int:pk>/delete/', views.PurchaseOrderDeleteView.as_view(), name='purchase_order_delete'),

    # Maintenance
    path('maintenance/', main_views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/calendar/', main_views.MaintenanceCalendarView.as_view(), name='maintenance_calendar'),
    path('maintenance/create/', main_views.MaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:maintenance_id>/', main_views.MaintenanceDetailView.as_view(), name='maintenance_detail'),
    path('maintenance/<int:maintenance_id>/edit/', main_views.MaintenanceUpdateView.as_view(), name='maintenance_update'),
    path('maintenance/<int:maintenance_id>/delete/', main_views.MaintenanceDeleteView.as_view(), name='maintenance_delete'),
    path('maintenance/<int:maintenance_id>/status/', main_views.MaintenanceStatusUpdateView.as_view(), name='maintenance_status_update'),
    path('maintenance/schedule/', main_views.MaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/', main_views.MaintenanceDetailView.as_view(), name='maintenance_detail'),

    # API endpoints for AJAX calls
    path('api/dashboard-data/', main_views.DashboardDataView.as_view(), name='dashboard_data'),
    path('api/kpi/<str:kpi_type>/', main_views.KPIDetailsView.as_view(), name='kpi_details'),
    path('api/search-clients/', main_views.SearchClientsView.as_view(), name='search_clients'),
    path('api/search-equipment/', main_views.SearchEquipmentView.as_view(), name='search_equipment'),
    path('api/debug-auth/', main_views.DebugAuthView.as_view(), name='debug_auth'),
    path('api/oem/models/', oem_views.OEMModelListAPIView.as_view(), name='oem_model_list'),
    
    # Diagnostic endpoints
    path('diagnostic/', diagnostic_views.APIDiagnosticView.as_view(), name='api_diagnostic'),
    path('diagnostic/client-form/', ClientFormDiagnosticView.as_view(), name='client_form_diagnostic'),
    path('diagnostic/client-form/debug/', ClientFormDebugView.as_view(), name='client_form_debug'),
    path('api/health-check/', diagnostic_views.APIHealthCheckView.as_view(), name='api_health_check'),
    path('api/connection-monitor/', diagnostic_views.APIConnectionMonitorView.as_view(), name='api_connection_monitor'),
    path('api/error-rate-tracking/', diagnostic_views.APIErrorRateTrackingView.as_view(), name='api_error_rate_tracking'),
    
    # Expanded Catalog Management
    path('catalog/', catalog_views.CatalogIndexView.as_view(), name='catalog_index'),
    path('catalog/product-catalogs/', RedirectView.as_view(url=reverse_lazy('frontend:reference_code_list'), permanent=False), name='product_catalogs_hub'),
    path('catalog/product-catalogs/brand-types/', product_catalog_views.BrandTypeListView.as_view(), name='product_catalog_brand_type_list'),
    path('catalog/product-catalogs/brand-types/create/', product_catalog_views.BrandTypeCreateView.as_view(), name='product_catalog_brand_type_create'),
    path('catalog/product-catalogs/brand-types/<str:code>/edit/', product_catalog_views.BrandTypeUpdateView.as_view(), name='product_catalog_brand_type_edit'),
    path('catalog/product-catalogs/brand-types/<str:code>/delete/', product_catalog_views.BrandTypeDeleteView.as_view(), name='product_catalog_brand_type_delete'),
    path('catalog/product-catalogs/categories/', product_catalog_views.ProductCategoryCatalogListView.as_view(), name='product_catalog_category_list'),
    path('catalog/product-catalogs/categories/create/', product_catalog_views.ProductCategoryCatalogCreateView.as_view(), name='product_catalog_category_create'),
    path('catalog/product-catalogs/categories/<str:code>/edit/', product_catalog_views.ProductCategoryCatalogUpdateView.as_view(), name='product_catalog_category_edit'),
    path('catalog/product-catalogs/categories/<str:code>/delete/', product_catalog_views.ProductCategoryCatalogDeleteView.as_view(), name='product_catalog_category_delete'),
    path('catalog/product-catalogs/types/', product_catalog_views.ProductTypeCatalogListView.as_view(), name='product_catalog_type_list'),
    path('catalog/product-catalogs/types/create/', product_catalog_views.ProductTypeCatalogCreateView.as_view(), name='product_catalog_type_create'),
    path('catalog/product-catalogs/types/<str:code>/edit/', product_catalog_views.ProductTypeCatalogUpdateView.as_view(), name='product_catalog_type_edit'),
    path('catalog/product-catalogs/types/<str:code>/delete/', product_catalog_views.ProductTypeCatalogDeleteView.as_view(), name='product_catalog_type_delete'),
    path('catalog/reports/', catalog_views.CatalogReportsView.as_view(), name='catalog_reports'),
    path('catalog/reports/export/', catalog_views.CatalogReportExportView.as_view(), name='catalog_report_export'),
    
    # Category Management
    path('catalog/categories/', catalog_views.CategoryListView.as_view(), name='category_list'),
    path('catalog/categories/create/', catalog_views.CategoryCreateView.as_view(), name='category_create'),
    path('catalog/categories/<int:pk>/', catalog_views.CategoryDetailView.as_view(), name='category_detail'),
    path('catalog/categories/<int:pk>/edit/', catalog_views.CategoryUpdateView.as_view(), name='category_edit'),
    path('catalog/categories/<int:pk>/toggle-active/', catalog_views.CategoryToggleActiveView.as_view(), name='category_toggle_active'),
    path('catalog/categories/<int:pk>/delete/', catalog_views.CategoryDeleteView.as_view(), name='category_delete'),
    path('api/categories/search/', catalog_views.CategoryListView.as_view(), name='category_ajax_search'),
    
    # Equipment Types
    path('catalog/equipment-types/', equipment_type_views.EquipmentTypeListView.as_view(), name='equipment_type_list'),
    path('catalog/equipment-types/create/', equipment_type_views.EquipmentTypeCreateView.as_view(), name='equipment_type_create'),
    path('catalog/equipment-types/<int:pk>/', equipment_type_views.EquipmentTypeDetailView.as_view(), name='equipment_type_detail'),
    path('catalog/equipment-types/<int:pk>/edit/', equipment_type_views.EquipmentTypeUpdateView.as_view(), name='equipment_type_edit'),
    path('catalog/equipment-types/<int:pk>/toggle-active/', equipment_type_views.EquipmentTypeToggleActiveView.as_view(), name='equipment_type_toggle_active'),
    path('catalog/equipment-types/<int:pk>/delete/', equipment_type_views.EquipmentTypeDeleteView.as_view(), name='equipment_type_delete'),
    
    # Taxonomy Management
    path('catalog/taxonomy/', taxonomy_views.TaxonomyTreeView.as_view(), name='taxonomy_tree'),
    path('catalog/taxonomy/systems/', taxonomy_views.TaxonomySystemListView.as_view(), name='taxonomy_system_list'),
    path('catalog/taxonomy/systems/create/', taxonomy_views.TaxonomySystemCreateView.as_view(), name='taxonomy_system_create'),
    path('catalog/taxonomy/systems/<str:pk>/', taxonomy_views.TaxonomySystemDetailView.as_view(), name='taxonomy_system_detail'),
    path('catalog/taxonomy/systems/<str:pk>/edit/', taxonomy_views.TaxonomySystemUpdateView.as_view(), name='taxonomy_system_edit'),
    path('catalog/taxonomy/systems/<str:pk>/delete/', taxonomy_views.TaxonomySystemDeleteView.as_view(), name='taxonomy_system_delete'),
    
    # Taxonomy Subsystems
    path('catalog/taxonomy/systems/<str:system_id>/subsystems/', taxonomy_views.TaxonomySubsystemListView.as_view(), name='taxonomy_subsystem_list'),
    path('catalog/taxonomy/systems/<str:system_id>/subsystems/create/', taxonomy_views.TaxonomySubsystemCreateView.as_view(), name='taxonomy_subsystem_create'),
    path('catalog/taxonomy/subsystems/<str:pk>/', taxonomy_views.TaxonomySubsystemDetailView.as_view(), name='taxonomy_subsystem_detail'),
    path('catalog/taxonomy/systems/<str:system_id>/subsystems/<str:pk>/edit/', taxonomy_views.TaxonomySubsystemUpdateView.as_view(), name='taxonomy_subsystem_edit'),
    path('catalog/taxonomy/systems/<str:system_id>/subsystems/<str:pk>/delete/', taxonomy_views.TaxonomySubsystemDeleteView.as_view(), name='taxonomy_subsystem_delete'),
    
    # Taxonomy Groups
    path('catalog/taxonomy/subsystems/<str:subsystem_id>/groups/', taxonomy_views.TaxonomyGroupListView.as_view(), name='taxonomy_group_list'),
    path('catalog/taxonomy/subsystems/<str:subsystem_id>/groups/create/', taxonomy_views.TaxonomyGroupCreateView.as_view(), name='taxonomy_group_create'),
    path('catalog/taxonomy/groups/<str:pk>/', taxonomy_views.TaxonomyGroupDetailView.as_view(), name='taxonomy_group_detail'),
    path('catalog/taxonomy/subsystems/<str:subsystem_id>/groups/<str:pk>/edit/', taxonomy_views.TaxonomyGroupUpdateView.as_view(), name='taxonomy_group_edit'),
    path('catalog/taxonomy/subsystems/<str:subsystem_id>/groups/<str:pk>/delete/', taxonomy_views.TaxonomyGroupDeleteView.as_view(), name='taxonomy_group_delete'),
    
    # Reference Codes Management
    path('catalog/reference-codes/', reference_code_views.ReferenceCodeListView.as_view(), name='reference_code_list'),
    path('catalog/reference-codes/create/', reference_code_views.ReferenceCodeCreateView.as_view(), name='reference_code_create'),
    path('catalog/reference-codes/import/', reference_code_views.ReferenceCodeImportView.as_view(), name='reference_code_import'),
    path('catalog/reference-codes/export/', reference_code_views.ReferenceCodeExportView.as_view(), name='reference_code_export'),
    path('catalog/reference-codes/<str:category>/<str:pk>/', reference_code_views.ReferenceCodeDetailView.as_view(), name='reference_code_detail'),
    path('catalog/reference-codes/<str:category>/<str:pk>/edit/', reference_code_views.ReferenceCodeUpdateView.as_view(), name='reference_code_edit'),
    path('catalog/reference-codes/<str:category>/<str:pk>/delete/', reference_code_views.ReferenceCodeDeleteView.as_view(), name='reference_code_delete'),
    
    # Reference Codes AJAX endpoints
    path('api/reference-codes/search/', reference_code_views.ReferenceCodeAjaxSearchView.as_view(), name='reference_code_ajax_search'),
    path('api/reference-codes/import-preview/', reference_code_views.ReferenceCodeImportPreviewView.as_view(), name='reference_code_import_preview'),
    path('api/reference-codes/bulk-delete/', reference_code_views.ReferenceCodeBulkDeleteView.as_view(), name='reference_code_bulk_delete'),
    
    path('catalog/currencies/', currency_views.CurrencyListView.as_view(), name='currency_list'),
    path('catalog/currencies/create/', currency_views.CurrencyCreateView.as_view(), name='currency_create'),
    
    # Currency Rate Management (Tarea 4.2) - DEBE IR ANTES de las rutas con <str:pk>
    path('catalog/currencies/rates/', currency_rate_views.CurrencyRateManagementView.as_view(), name='currency_rates'),
    path('catalog/currencies/rates/update/', currency_rate_views.CurrencyRateUpdateView.as_view(), name='currency_rate_update'),
    path('catalog/currencies/rates/update-all/', currency_rate_views.CurrencyRateUpdateAllView.as_view(), name='currency_rate_update_all'),
    path('catalog/currencies/rates/history/<str:currency_code>/', currency_rate_views.CurrencyRateHistoryView.as_view(), name='currency_rate_history'),
    path('api/currencies/rates/history/<str:currency_code>/', currency_rate_views.CurrencyRateHistoryAjaxView.as_view(), name='currency_rate_history_ajax'),
    
    # Currency History Enhanced (Tarea 4.4)
    path('catalog/currencies/history/<str:currency_code>/', CurrencyHistoryEnhancedView.as_view(), name='currency_history_enhanced'),
    path('catalog/currencies/history/comparison/', CurrencyHistoryComparisonView.as_view(), name='currency_history_comparison'),
    path('api/currencies/history/comparison/', CurrencyHistoryComparisonAPIView.as_view(), name='currency_history_comparison_api'),
    path('api/currencies/alerts/', CurrencyAlertsAPIView.as_view(), name='currency_alerts_api'),
    
    # Currency CRUD - Estas rutas con <str:pk> deben ir DESPUÉS
    path('catalog/currencies/<str:pk>/', currency_views.CurrencyDetailView.as_view(), name='currency_detail'),
    path('catalog/currencies/<str:pk>/edit/', currency_views.CurrencyUpdateView.as_view(), name='currency_edit'),
    path('catalog/currencies/<str:pk>/delete/', currency_views.CurrencyDeleteView.as_view(), name='currency_delete'),
    path('api/currencies/search/', currency_views.CurrencyAjaxSearchView.as_view(), name='currency_ajax_search'),
    path('api/currencies/check-code/', currency_views.currency_check_code, name='currency_check_code'),
    path('catalog/suppliers/advanced/', catalog_views.SupplierAdvancedListView.as_view(), name='supplier_advanced_list'),
    
    # Equipment Type AJAX endpoints
    path('api/equipment-types/search/', equipment_type_views.EquipmentTypeAjaxSearchView.as_view(), name='equipment_type_ajax_search'),
    path('api/equipment-types/check-code/', equipment_type_views.equipment_type_check_code, name='equipment_type_check_code'),
    
    # Equipment Type Export endpoints
    path('catalog/equipment-types/export/xls/', equipment_type_views.EquipmentTypeExportXLSView.as_view(), name='equipment_type_export_xls'),
    path('catalog/equipment-types/export/pdf/', equipment_type_views.EquipmentTypeExportPDFView.as_view(), name='equipment_type_export_pdf'),
    
    # Taxonomy AJAX endpoints
    path('api/taxonomy/search/', taxonomy_views.TaxonomyAjaxSearchView.as_view(), name='taxonomy_ajax_search'),
    path('api/taxonomy/tree-data/', taxonomy_views.TaxonomyTreeDataView.as_view(), name='taxonomy_tree_data'),
    path('api/taxonomy/node-action/', taxonomy_views.TaxonomyNodeActionView.as_view(), name='taxonomy_node_action'),
    path('api/taxonomy/bulk-action/', taxonomy_views.TaxonomyBulkActionView.as_view(), name='taxonomy_bulk_action'),
    path('api/taxonomy/validate-code/', taxonomy_views.TaxonomyValidateCodeView.as_view(), name='taxonomy_validate_code'),
    
    # Advanced Service Management
    path('services/dashboard/', service_advanced_views.ServiceDashboardView.as_view(), name='service_dashboard'),
    path('api/services/stats/', ServiceStatsAPIView.as_view(), name='service_stats_api'),
    path('api/services/productivity/', ServiceProductivityAPIView.as_view(), name='service_productivity_api'),
    path('api/services/categories/', ServiceCategoriesAPIView.as_view(), name='service_categories_api'),
    path('api/services/trends/', ServiceTrendsAPIView.as_view(), name='service_trends_api'),
    path('api/services/comparison/', ServiceComparisonAPIView.as_view(), name='service_comparison_api'),
    path('api/services/alerts/', ServiceAlertsAPIView.as_view(), name='service_alerts_api'),
    path('api/services/alerts/stream/', ServiceAlertsSSEView.as_view(), name='service_alerts_sse'),
    path('services/alerts/', ServiceAlertsListView.as_view(), name='service_alerts_list'),
    path('services/alerts/thresholds/', ServiceAlertThresholdsView.as_view(), name='service_alert_thresholds'),
    path('services/work-orders/<int:wo_id>/timeline/', service_advanced_views.WorkOrderTimelineView.as_view(), name='workorder_timeline'),
    path('services/flat-rate-calculator/', service_advanced_views.FlatRateCalculatorView.as_view(), name='flat_rate_calculator'),
    path('services/checklist/<int:flat_rate_id>/', service_advanced_views.ServiceChecklistInteractiveView.as_view(), name='service_checklist_interactive'),
    path('services/checklist/<int:flat_rate_id>/wo/<int:wo_service_id>/', service_advanced_views.ServiceChecklistInteractiveView.as_view(), name='service_checklist_wo'),
    
    # OEM Catalog Management - CONSOLIDADO
    path('oem/', oem_views.OEMCatalogIndexView.as_view(), name='oem_catalog_index'),
    path('oem/manufacturers/', oem_views.OEMManufacturerManagementView.as_view(), name='oem_manufacturer_management'),
    path('oem/parts/', oem_views.OEMPartCatalogView.as_view(), name='oem_part_catalog'),
    path('oem/cross-reference/', oem_views.CrossReferenceToolView.as_view(), name='oem_cross_reference_tool'),
    path('oem/catalog/', oem_views.CrossReferenceToolView.as_view(), name='oem_catalog_search'),
    path('oem/brands/', oem_views.OEMManufacturerManagementView.as_view(), name='oem_brand_management'),
    
    # OEM Brand CRUD
    path('oem/brands/list/', views.OEMBrandListView.as_view(), name='oem_brand_list'),
    path('oem/brands/create/', views.OEMBrandCreateView.as_view(), name='oem_brand_create'),
    path('oem/brands/<int:pk>/', views.OEMBrandDetailView.as_view(), name='oem_brand_detail'),
    path('oem/brands/<int:pk>/edit/', views.OEMBrandUpdateView.as_view(), name='oem_brand_update'),
    path('oem/brands/<int:pk>/delete/', views.OEMBrandDeleteView.as_view(), name='oem_brand_delete'),
    
    # OEM Catalog Item CRUD
    path('oem/catalog/items/', views.OEMCatalogItemListView.as_view(), name='oem_catalog_item_list'),
    path('oem/catalog/items/create/', views.OEMCatalogItemCreateView.as_view(), name='oem_catalog_item_create'),
    path('oem/catalog/items/<int:pk>/', views.OEMCatalogItemDetailView.as_view(), name='oem_catalog_item_detail'),
    path('oem/catalog/items/<int:pk>/edit/', views.OEMCatalogItemUpdateView.as_view(), name='oem_catalog_item_update'),
    path('oem/catalog/items/<int:pk>/delete/', views.OEMCatalogItemDeleteView.as_view(), name='oem_catalog_item_delete'),
    
    # Quote Management (Tarea 6.4)
    path('quotes/', QuoteListView.as_view(), name='quote_list'),
    path('quotes/create/', QuoteCreateView.as_view(), name='quote_create'),
    path('quotes/<int:pk>/', QuoteDetailView.as_view(), name='quote_detail'),
    path('quotes/<int:quote_id>/pdf/', QuotePDFView.as_view(), name='quote_pdf'),
    path('quotes/<int:quote_id>/convert/', QuoteConvertToWorkOrderView.as_view(), name='quote_convert_to_wo'),
    
    # Alert and Audit System
    path('alerts/', alert_views.AlertDashboardView.as_view(), name='alert_dashboard'),
    path('alerts/<int:alert_id>/', alert_views.AlertDetailView.as_view(), name='alert_detail'),
    path('alerts/<int:alert_id>/action/', alert_views.AlertActionView.as_view(), name='alert_action'),
    path('business-rules/', alert_views.BusinessRuleManagementView.as_view(), name='business_rule_management'),
    path('audit-log/', alert_views.AuditLogView.as_view(), name='audit_log'),
    path('api/notifications/', alert_views.NotificationAPIView.as_view(), name='notifications_api'),
    
    # Notifications
    path('notifications/', views_notification.NotificationListView.as_view(), name='notification_list'),
    
    # OEM Equivalences Management
    path('oem/equivalences/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
        'get': 'list'
    }), name='oem_equivalence_list'),
    path('oem/equivalences/create/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
        'post': 'create'
    }), name='oem_equivalence_create'),
    path('oem/equivalences/<int:pk>/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
        'get': 'retrieve'
    }), name='oem_equivalence_detail'),
    path('oem/equivalences/<int:pk>/edit/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
        'put': 'update', 'patch': 'partial_update'
    }), name='oem_equivalence_edit'),
    path('oem/equivalences/<int:pk>/delete/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
        'delete': 'destroy'
    }), name='oem_equivalence_delete'),
    
    # OEM Equivalences API
    path('api/oem/equivalences/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='api_oem_equivalences'),
    path('api/oem/equivalences/<int:pk>/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    }), name='api_oem_equivalence_detail'),
    path('api/oem/equivalences/by-oem-part/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({'get': 'by_oem_part'}), name='api_oem_equivalences_by_oem'),
    path('api/oem/equivalences/by-aftermarket/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({'get': 'by_aftermarket'}), name='api_oem_equivalences_by_aftermarket'),
    path('api/oem/equivalences/statistics/', oem_equivalence_views.OEMEquivalenceViewSet.as_view({'get': 'statistics'}), name='api_oem_equivalences_stats'),
    path('api/oem/equivalences/search/', oem_equivalence_views.OEMEquivalenceSearchView.as_view(), name='api_oem_equivalences_search'),
    
    # Fitment (Compatibility) Management
    path('fitments/', fitment_views.FitmentViewSet.as_view({
        'get': 'list'
    }), name='fitment_list'),
    path('fitments/create/', fitment_views.FitmentViewSet.as_view({
        'post': 'create'
    }), name='fitment_create'),
    path('fitments/<int:pk>/', fitment_views.FitmentViewSet.as_view({
        'get': 'retrieve'
    }), name='fitment_detail'),
    path('fitments/<int:pk>/edit/', fitment_views.FitmentViewSet.as_view({
        'put': 'update', 'patch': 'partial_update'
    }), name='fitment_edit'),
    path('fitments/<int:pk>/delete/', fitment_views.FitmentViewSet.as_view({
        'delete': 'destroy'
    }), name='fitment_delete'),
    
    # Fitment API
    path('api/fitments/', fitment_views.FitmentViewSet.as_view({
        'get': 'list', 'post': 'create'
    }), name='api_fitments'),
    path('api/fitments/<int:pk>/', fitment_views.FitmentViewSet.as_view({
        'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
    }), name='api_fitment_detail'),
    path('api/fitments/by-equipment/', fitment_views.FitmentViewSet.as_view({'get': 'by_equipment'}), name='api_fitments_by_equipment'),
    path('api/fitments/by-product/', fitment_views.FitmentViewSet.as_view({'get': 'by_product'}), name='api_fitments_by_product'),
    path('api/fitments/auto-create/', fitment_views.FitmentViewSet.as_view({'post': 'auto_create'}), name='api_fitments_auto_create'),
    path('api/fitments/statistics/', fitment_views.FitmentViewSet.as_view({'get': 'statistics'}), name='api_fitments_stats'),
    path('api/fitments/compatibility-check/', fitment_views.FitmentCompatibilityCheckView.as_view(), name='api_fitments_compatibility_check'),
    
    # OEM Import
    path('oem/import/', oem_import_views.OEMImportView.as_view(), name='oem_import'),
    path('api/oem/import/', oem_import_views.OEMImportAPIView.as_view(), name='api_oem_import'),
    
    # Unified Search
    path('search/', unified_search_views.UnifiedSearchView.as_view(), name='unified_search'),
    path('api/search/unified/', unified_search_views.UnifiedSearchAPIView.as_view(), name='api_unified_search'),
    path('api/search/suggestions/', unified_search_views.UnifiedSearchSuggestionsView.as_view(), name='api_unified_search_suggestions'),
    path('api/search/stats/', unified_search_views.UnifiedSearchStatsView.as_view(), name='api_unified_search_stats'),
    path('api/search/cache/clear/', unified_search_views.UnifiedSearchCacheClearView.as_view(), name='api_unified_search_cache_clear'),
    
    # OEM UI Views - Interfaces visibles
    path('oem/equivalences/manage/', oem_ui_views.OEMEquivalenceManagementView.as_view(), name='equivalence_management'),
    path('oem/equivalences/create/', oem_ui_views.OEMEquivalenceCreateView.as_view(), name='oem_equivalence_create_ui'),
    path('oem/equivalences/<int:equivalence_id>/edit/', oem_ui_views.OEMEquivalenceEditView.as_view(), name='oem_equivalence_edit_ui'),
    path('oem/import/dashboard/', oem_ui_views.OEMImportDashboardView.as_view(), name='oem_import_dashboard'),
    
    # Fitment UI Views - Interfaces visibles
    # path('catalog/fitments/', oem_ui_views.FitmentManagementView.as_view(), name='fitment_management'),
    # path('catalog/fitments/auto-create/', oem_ui_views.FitmentAutoCreateView.as_view(), name='fitment_auto_create'),
]