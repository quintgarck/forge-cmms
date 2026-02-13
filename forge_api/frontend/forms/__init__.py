""" 
Formularios para la aplicación frontend de ForgeDB.
"""
# Import forms from subdirectory modules
from .technician_forms import (
    TechnicianForm, TechnicianSearchForm
)
from .invoice_forms import (
    InvoiceForm, InvoiceSearchForm
)
from .client_forms import (
    ClientForm, ClientSearchForm
)
from .equipment_forms import (
    EquipmentForm
)
from .equipment_type_forms import (
    EquipmentTypeForm, EquipmentTypeSearchForm
)
from .reference_code_forms import (
    ReferenceCodeForm, ReferenceCodeImportForm
)
from .currency_forms import (
    CurrencyForm, CurrencySearchForm
)

# Import forms from main forms.py file using dynamic import to avoid circular imports
def __getattr__(name):
    """
    Dynamic import of forms from the main forms.py file.
    This avoids circular import issues while still providing access to all forms.
    """
    # List of forms and helpers from the main forms.py file
    main_forms = {
        'EquipmentForm', 'EquipmentSearchForm',
        'MaintenanceScheduleForm', 'MaintenanceSearchForm', 'MaintenanceForm',
        'WorkOrderWizardForm', 'WorkOrderForm', 'WorkOrderSearchForm',
        'ProductForm', 'ProductSearchForm',
        'StockMovementForm', 'StockSearchForm', 'StockAdjustmentForm', 'StockAlertForm',
        'WarehouseForm', 'WarehouseSearchForm',
        'get_uom_choices', 'get_product_category_choices', 'get_product_type_choices',
    }
    
    if name in main_forms:
        # Import from the main forms.py file directly
        import importlib.util
        import os
        
        # Get the path to the main forms.py file
        forms_path = os.path.join(os.path.dirname(__file__), '..', 'forms.py')
        forms_path = os.path.abspath(forms_path)
        
        # Load the module
        spec = importlib.util.spec_from_file_location("frontend_main_forms", forms_path)
        main_forms_module = importlib.util.module_from_spec(spec)
        
        # Set up the module's __package__ to enable relative imports
        main_forms_module.__package__ = 'frontend'
        
        # Execute the module
        spec.loader.exec_module(main_forms_module)
        
        return getattr(main_forms_module, name)
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'ClientForm', 'ClientSearchForm',
    'TechnicianForm', 'TechnicianSearchForm',
    'InvoiceForm', 'InvoiceSearchForm',
    'EquipmentForm', 'EquipmentSearchForm',
    'MaintenanceScheduleForm', 'MaintenanceSearchForm', 'MaintenanceForm',
    'WorkOrderWizardForm', 'WorkOrderForm', 'WorkOrderSearchForm',
    'ProductForm', 'ProductSearchForm', 'get_uom_choices', 'get_product_category_choices', 'get_product_type_choices',
    'StockMovementForm', 'StockSearchForm', 'StockAdjustmentForm', 'StockAlertForm',
    'WarehouseForm', 'WarehouseSearchForm',
    'EquipmentTypeForm', 'EquipmentTypeSearchForm',
    'ReferenceCodeForm', 'ReferenceCodeImportForm',
    'CurrencyForm', 'CurrencySearchForm'
]