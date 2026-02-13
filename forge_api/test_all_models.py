#!/usr/bin/env python
"""
Script de verificación: Prueba que todos los modelos Django pueden consultar la base de datos.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.db import connection

def test_all_models():
    """Prueba todos los modelos principales"""
    print("=" * 60)
    print("VERIFICACIÓN DE MODELOS DJANGO - TODOS LOS ESQUEMAS")
    print("=" * 60)
    
    models_to_test = [
        # APP Schema
        ('Alert', 'app.alerts -> alerts'),
        ('BusinessRule', 'app.business_rules -> business_rules'),
        ('AuditLog', 'app.audit_logs -> audit_logs'),
        
        # CAT Schema
        ('Technician', 'cat.technicians -> technicians'),
        ('Client', 'cat.clients -> clients'),
        ('EquipmentType', 'cat.equipment_types -> equipment_types'),
        ('FuelCode', 'cat.fuel_codes -> fuel_codes'),
        ('AspirationCode', 'cat.aspiration_codes -> aspiration_codes'),
        ('TransmissionCode', 'cat.transmission_codes -> transmission_codes'),
        ('DrivetrainCode', 'cat.drivetrain_codes -> drivetrain_codes'),
        ('ColorCode', 'cat.color_codes -> color_codes'),
        ('PositionCode', 'cat.position_codes -> position_codes'),
        ('FinishCode', 'cat.finish_codes -> finish_codes'),
        ('SourceCode', 'cat.source_codes -> source_codes'),
        ('ConditionCode', 'cat.condition_codes -> condition_codes'),
        ('UOMCode', 'cat.uom_codes -> uom_codes'),
        ('Currency', 'cat.currencies -> currencies'),
        ('Supplier', 'cat.suppliers -> suppliers'),
        ('TaxonomySystem', 'cat.taxonomy_systems -> taxonomy_systems'),
        ('TaxonomySubsystem', 'cat.taxonomy_subsystems -> taxonomy_subsystems'),
        ('TaxonomyGroup', 'cat.taxonomy_groups -> taxonomy_groups'),
        ('Equipment', 'cat.equipment -> equipment'),
        ('Fitment', 'cat.fitment -> fitment'),
        
        # INV Schema
        ('Warehouse', 'inv.warehouses -> warehouses'),
        ('ProductMaster', 'inv.product_master -> product_master'),
        ('Stock', 'inv.stock -> stock'),
        ('Transaction', 'inv.transactions -> transactions'),
        ('Bin', 'inv.bins -> bins'),
        ('PriceList', 'inv.price_lists -> price_lists'),
        ('ProductPrice', 'inv.product_prices -> product_prices'),
        ('PurchaseOrder', 'inv.purchase_orders -> purchase_orders'),
        ('POItem', 'inv.po_items -> po_items'),
        
        # SVC Schema
        ('WorkOrder', 'svc.work_orders -> work_orders'),
        ('Invoice', 'svc.invoices -> invoices'),
        ('WOItem', 'svc.wo_items -> wo_items'),
        ('FlatRateStandard', 'svc.flat_rate_standards -> flat_rate_standards'),
        ('WOService', 'svc.wo_services -> wo_services'),
        ('ServiceChecklist', 'svc.service_checklists -> service_checklists'),
        ('InvoiceItem', 'svc.invoice_items -> invoice_items'),
        ('Payment', 'svc.payments -> payments'),
        ('Quote', 'svc.quotes -> quotes'),
        ('QuoteItem', 'svc.quote_items -> quote_items'),
        
        # DOC Schema
        ('Document', 'doc.documents -> documents'),
        
        # OEM Schema
        ('OEMBrand', 'oem.brands -> brands'),
        ('OEMCatalogItem', 'oem.catalog_items -> catalog_items'),
        ('OEMEquivalence', 'oem.equivalences -> equivalences'),
        
        # KPI Schema
        ('WOMetric', 'kpi.wo_metrics -> wo_metrics'),
    ]
    
    from core.models import (Alert, BusinessRule, AuditLog, Technician, Client,
    EquipmentType, FuelCode, AspirationCode, TransmissionCode, DrivetrainCode,
    ColorCode, PositionCode, FinishCode, SourceCode, ConditionCode, UOMCode,
    Currency, Supplier, TaxonomySystem, TaxonomySubsystem, TaxonomyGroup,
    Equipment, Fitment, Warehouse, ProductMaster, Stock, Transaction,
    Bin, PriceList, ProductPrice, PurchaseOrder, POItem,
    WorkOrder, Invoice, WOItem, FlatRateStandard, WOService, ServiceChecklist,
    InvoiceItem, Payment, Quote, QuoteItem,
    Document, OEMBrand, OEMCatalogItem, OEMEquivalence, WOMetric)
    
    success_count = 0
    error_count = 0
    
    for model_name, description in models_to_test:
        # Mapeo de nombres a clases reales
        model_mapping = {
            'Alert': Alert, 'BusinessRule': BusinessRule, 'AuditLog': AuditLog,
            'Technician': Technician, 'Client': Client, 'EquipmentType': EquipmentType,
            'FuelCode': FuelCode, 'AspirationCode': AspirationCode,
            'TransmissionCode': TransmissionCode, 'DrivetrainCode': DrivetrainCode,
            'ColorCode': ColorCode, 'PositionCode': PositionCode, 'FinishCode': FinishCode,
            'SourceCode': SourceCode, 'ConditionCode': ConditionCode, 'UOMCode': UOMCode,
            'Currency': Currency, 'Supplier': Supplier,
            'TaxonomySystem': TaxonomySystem, 'TaxonomySubsystem': TaxonomySubsystem,
            'TaxonomyGroup': TaxonomyGroup, 'Equipment': Equipment, 'Fitment': Fitment,
            'Warehouse': Warehouse, 'ProductMaster': ProductMaster, 'Stock': Stock,
            'Transaction': Transaction, 'Bin': Bin, 'PriceList': PriceList,
            'ProductPrice': ProductPrice, 'PurchaseOrder': PurchaseOrder, 'POItem': POItem,
            'WorkOrder': WorkOrder, 'Invoice': Invoice, 'WOItem': WOItem,
            'FlatRateStandard': FlatRateStandard, 'WOService': WOService,
            'ServiceChecklist': ServiceChecklist, 'InvoiceItem': InvoiceItem,
            'Payment': Payment, 'Quote': Quote, 'QuoteItem': QuoteItem,
            'Document': Document, 'OEMBrand': OEMBrand, 'OEMCatalogItem': OEMCatalogItem,
            'OEMEquivalence': OEMEquivalence, 'WOMetric': WOMetric,
        }
        
        model_class = model_mapping.get(model_name)
        if not model_class:
            print(f"  ❌ {model_name}: NO ENCONTRADO")
            error_count += 1
            continue
            
        try:
            # Try to get count
            count = model_class.objects.count()
            print(f"  ✅ {model_name}: OK ({count} registros) [{description}]")
            success_count += 1
        except Exception as e:
            print(f"  ❌ {model_name}: ERROR - {str(e)[:50]} [{description}]")
            error_count += 1
    
    print("=" * 60)
    print(f"RESULTADO: {success_count} exitosos, {error_count} con errores")
    print("=" * 60)
    
    return error_count == 0

if __name__ == '__main__':
    success = test_all_models()
    sys.exit(0 if success else 1)
