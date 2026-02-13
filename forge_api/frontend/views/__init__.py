"""
Vistas para la aplicación frontend de ForgeDB.
"""
# Import views from subdirectory modules
from .technician_views import (
    TechnicianListView, TechnicianDetailView, TechnicianCreateView,
    TechnicianUpdateView, TechnicianDeleteView
)
from .invoice_views import (
    InvoiceListView, InvoiceDetailView, InvoiceCreateView,
    InvoiceUpdateView, InvoiceDeleteView
)
from .client_views import (
    ClientListView, ClientDetailView, ClientCreateView,
    ClientUpdateView, ClientDeleteView
)
from .equipment_views import (
    EquipmentListView, EquipmentDetailView, EquipmentCreateView,
    EquipmentUpdateView, EquipmentDeleteView
)
from .supplier_views import (
    SupplierListView, SupplierDetailView, SupplierCreateView,
    SupplierUpdateView, SupplierDeleteView
)
from .purchase_order_views import (
    PurchaseOrderListView, PurchaseOrderDetailView, PurchaseOrderCreateView,
    PurchaseOrderUpdateView, PurchaseOrderDeleteView
)
from .oem_crud_views import (
    OEMBrandListView, OEMBrandDetailView, OEMBrandCreateView,
    OEMBrandUpdateView, OEMBrandDeleteView,
    OEMCatalogItemListView, OEMCatalogItemDetailView, OEMCatalogItemCreateView,
    OEMCatalogItemUpdateView, OEMCatalogItemDeleteView
)

# Import alert views module for URL configuration
from . import alert_views
from . import equipment_type_views
from . import taxonomy_views
from . import reference_code_views
from . import currency_views

__all__ = [
    # Client Views (from separate file)
    'ClientListView', 'ClientDetailView', 'ClientCreateView',
    'ClientUpdateView', 'ClientDeleteView',
    
    # Technician Views
    'TechnicianListView', 'TechnicianDetailView', 'TechnicianCreateView',
    'TechnicianUpdateView', 'TechnicianDeleteView',
    
    # Equipment Views
    'EquipmentListView', 'EquipmentDetailView', 'EquipmentCreateView',
    'EquipmentUpdateView', 'EquipmentDeleteView',
    
    # Invoice Views
    'InvoiceListView', 'InvoiceDetailView', 'InvoiceCreateView',
    'InvoiceUpdateView', 'InvoiceDeleteView',
    
    # Supplier Views
    'SupplierListView', 'SupplierDetailView', 'SupplierCreateView',
    'SupplierUpdateView', 'SupplierDeleteView',
    
    # Purchase Order Views
    'PurchaseOrderListView', 'PurchaseOrderDetailView', 'PurchaseOrderCreateView',
    'PurchaseOrderUpdateView', 'PurchaseOrderDeleteView',
    
    # OEM Brand Views
    'OEMBrandListView', 'OEMBrandDetailView', 'OEMBrandCreateView',
    'OEMBrandUpdateView', 'OEMBrandDeleteView',
    
    # OEM Catalog Item Views
    'OEMCatalogItemListView', 'OEMCatalogItemDetailView', 'OEMCatalogItemCreateView',
    'OEMCatalogItemUpdateView', 'OEMCatalogItemDeleteView',
]