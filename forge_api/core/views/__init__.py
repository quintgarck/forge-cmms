"""
ForgeDB API REST - Views Package
"""

from .auth_views import *
from .client_views import ClientViewSet
from .equipment_views import EquipmentViewSet
from .technician_views import TechnicianViewSet
from .product_views import ProductMasterViewSet
from .stock_views import StockViewSet
from .transaction_views import TransactionViewSet
from .workorder_views import WorkOrderViewSet
from .invoice_views import InvoiceViewSet
from .alert_views import AlertViewSet
from .document_views import DocumentViewSet
from .businessrule_views import BusinessRuleViewSet
from .auditlog_views import AuditLogViewSet
from .warehouse_views import WarehouseViewSet
from .stored_procedures_views import reserve_stock

# Catalog Views
from .catalog_views import (
    CategoryViewSet, EquipmentTypeViewSet, FuelCodeViewSet, AspirationCodeViewSet,
    TransmissionCodeViewSet, DrivetrainCodeViewSet, ColorCodeViewSet,
    PositionCodeViewSet, FinishCodeViewSet, SourceCodeViewSet,
    ConditionCodeViewSet, UOMCodeViewSet, CurrencyViewSet
)
from .supplier_views import SupplierViewSet
from .taxonomy_views import (
    TaxonomySystemViewSet, TaxonomySubsystemViewSet, TaxonomyGroupViewSet
)
from .fitment_views import FitmentViewSet

# Inventory Views
from .inventory_views import (
    BinViewSet, PriceListViewSet, ProductPriceViewSet,
    PurchaseOrderViewSet, POItemViewSet
)

# OEM Views
from .oem_views import (
    OEMBrandViewSet, OEMCatalogItemViewSet, OEMEquivalenceViewSet
)

# Service Views
from .service_views import (
    WOItemViewSet, WOServiceViewSet, FlatRateStandardViewSet,
    ServiceChecklistViewSet, InvoiceItemViewSet, PaymentViewSet,
    QuoteViewSet, QuoteItemViewSet
)

# KPI Views
from .kpi_views import WOMetricViewSet