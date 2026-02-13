"""
OEM Integration Service - Service for integrating OEM data with ProductMaster inventory.
"""
import logging
from decimal import Decimal
from django.utils import timezone

logger = logging.getLogger(__name__)


class OEMIntegrationService:
    """
    Service class for integrating OEM catalog data with ProductMaster inventory.
    
    Provides methods to:
    - Import single OEM items to ProductMaster
    - Bulk import by brand
    - Create fitments from OEM data
    - Synchronize prices and availability
    """
    
    def __init__(self, api_client=None):
        """
        Initialize the service.
        
        Args:
            api_client: Optional API client for fetching OEM data from external sources.
                       If None, uses Django ORM directly.
        """
        self.api_client = api_client
    
    def import_oem_to_product_master(self, oem_catalog_item_id, supplier_id=None, commit=True):
        """
        Import a single OEM catalog item to ProductMaster.
        
        Args:
            oem_catalog_item_id: ID of the OEM catalog item to import
            supplier_id: Optional supplier ID to link the product with
            commit: Whether to commit the transaction (default True)
        
        Returns:
            ProductMaster instance that was created or updated
        
        Raises:
            ValueError: If OEM catalog item is not found
        """
        from core.models import (
            ProductMaster, OEMCatalogItem,
            TaxonomyGroup, SupplierSKU, Supplier
        )
        
        # Get OEM catalog item
        if self.api_client:
            oem_item_data = self.api_client.get_oem_catalog_item(oem_catalog_item_id)
            if not oem_item_data:
                raise ValueError(f"OEM catalog item {oem_catalog_item_id} not found")
            
            # Create/update ProductMaster from API data
            product = self._create_product_from_api_data(oem_item_data, supplier_id)
        else:
            # Use Django ORM directly
            try:
                oem_item = OEMCatalogItem.objects.get(catalog_id=oem_catalog_item_id)
            except OEMCatalogItem.DoesNotExist:
                raise ValueError(f"OEM catalog item {oem_catalog_item_id} not found")
            
            product = self._create_product_from_orm(oem_item, supplier_id)
        
        logger.info(f"OEM item {oem_catalog_item_id} imported to ProductMaster: {product.internal_sku}")
        return product
    
    def _create_product_from_api_data(self, oem_data, supplier_id):
        """Create ProductMaster from API data"""
        from core.models import ProductMaster, Supplier
        
        # Generate internal SKU
        internal_sku = self._generate_internal_sku(oem_data)
        
        # Get brand name
        oem_code_data = oem_data.get('oem_code', {})
        brand_name = oem_code_data.get('name', '') if isinstance(oem_code_data, dict) else ''
        
        # Get group code
        group_code_data = oem_data.get('group_code', {})
        group_code = group_code_data.get('group_code', '') if isinstance(group_code_data, dict) else oem_data.get('group_code', '')
        
        # Prepare data
        product_data = {
            'name': oem_data.get('description_es') or oem_data.get('description_en', ''),
            'description': oem_data.get('description_es', ''),
            'brand': brand_name,
            'oem_ref': oem_data.get('part_number'),
            'oem_code': oem_code_data.get('oem_code', '') if isinstance(oem_code_data, dict) else '',
            'group_code': group_code,
            'standard_cost': Decimal(oem_data.get('list_price', 0)) if oem_data.get('list_price') else Decimal('0.00'),
            'avg_cost': Decimal(oem_data.get('list_price', 0)) if oem_data.get('list_price') else Decimal('0.00'),
            'is_active': oem_data.get('is_active', True),
            'source_code': 'OEM',
            'condition_code': 'NEW',
            'uom_code': 'EA',
        }
        
        # Handle dimensions and weight
        if oem_data.get('dimensions'):
            product_data['dimensions_cm'] = oem_data.get('dimensions')
        if oem_data.get('weight_kg'):
            product_data['weight_kg'] = Decimal(str(oem_data.get('weight_kg')))
        
        # Create or update product
        product, created = ProductMaster.objects.update_or_create(
            internal_sku=internal_sku,
            defaults=product_data
        )
        
        # Create SupplierSKU if supplier_id provided
        if supplier_id:
            self._create_supplier_sku(product, supplier_id, oem_data)
        
        return product
    
    def _create_product_from_orm(self, oem_item, supplier_id):
        """Create ProductMaster from ORM object"""
        from core.models import ProductMaster, Supplier
        
        # Generate internal SKU
        internal_sku = self._generate_internal_sku_from_orm(oem_item)
        
        # Prepare data
        product_data = {
            'name': oem_item.description_es or oem_item.description_en or '',
            'description': oem_item.description_es or '',
            'brand': oem_item.oem_code.name if oem_item.oem_code else '',
            'oem_ref': oem_item.part_number,
            'oem_code': oem_item.oem_code.oem_code if oem_item.oem_code else '',
            'group_code': oem_item.group_code.group_code if oem_item.group_code else '',
            'standard_cost': oem_item.list_price or Decimal('0.00'),
            'avg_cost': oem_item.list_price or Decimal('0.00'),
            'is_active': oem_item.is_active,
            'source_code': 'OEM',
            'condition_code': 'NEW',
            'uom_code': 'EA',
        }
        
        # Handle dimensions and weight
        if oem_item.dimensions:
            product_data['dimensions_cm'] = oem_item.dimensions
        if oem_item.weight_kg:
            product_data['weight_kg'] = oem_item.weight_kg
        
        # Create or update product
        product, created = ProductMaster.objects.update_or_create(
            internal_sku=internal_sku,
            defaults=product_data
        )
        
        # Create SupplierSKU if supplier_id provided
        if supplier_id:
            self._create_supplier_sku_from_orm(product, supplier_id, oem_item)
        
        return product
    
    def _generate_internal_sku(self, oem_data):
        """Generate unique internal SKU from OEM data"""
        oem_code_data = oem_data.get('oem_code', {})
        if isinstance(oem_code_data, dict):
            oem_code = oem_code_data.get('oem_code', 'GEN')[:3].upper()
        else:
            oem_code = str(oem_code_data)[:3].upper() if oem_code_data else 'GEN'
        
        part_number = oem_data.get('part_number', '')[:10]
        # Clean part number
        part_number = ''.join(c for c in part_number if c.isalnum()).upper()
        
        # Use timestamp as suffix for uniqueness
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')[-6:]
        
        return f"{oem_code}{part_number}{timestamp}"
    
    def _generate_internal_sku_from_orm(self, oem_item):
        """Generate unique internal SKU from ORM object"""
        oem_code = oem_item.oem_code.oem_code[:3].upper() if oem_item.oem_code else 'GEN'
        part_number = oem_item.part_number[:10]
        part_number = ''.join(c for c in part_number if c.isalnum()).upper()
        
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')[-6:]
        
        return f"{oem_code}{part_number}{timestamp}"
    
    def _create_supplier_sku(self, product, supplier_id, oem_data):
        """Create SupplierSKU record"""
        from core.models import SupplierSKU, Supplier
        
        try:
            supplier = Supplier.objects.get(supplier_id=supplier_id)
        except Supplier.DoesNotExist:
            logger.warning(f"Supplier {supplier_id} not found, skipping SupplierSKU creation")
            return
        
        supplier_sku_data = {
            'internal_sku': product,
            'supplier': supplier,
            'supplier_sku_code': oem_data.get('part_number'),
            'supplier_mpn': oem_data.get('part_number'),
            'unit_cost': Decimal(oem_data.get('net_price', 0)) if oem_data.get('net_price') else Decimal('0.00'),
            'is_active': True,
        }
        
        SupplierSKU.objects.update_or_create(
            internal_sku=product,
            supplier=supplier,
            defaults=supplier_sku_data
        )
    
    def _create_supplier_sku_from_orm(self, product, supplier_id, oem_item):
        """Create SupplierSKU record from ORM object"""
        from core.models import SupplierSKU, Supplier
        
        try:
            supplier = Supplier.objects.get(supplier_id=supplier_id)
        except Supplier.DoesNotExist:
            logger.warning(f"Supplier {supplier_id} not found, skipping SupplierSKU creation")
            return
        
        supplier_sku_data = {
            'internal_sku': product,
            'supplier': supplier,
            'supplier_sku_code': oem_item.part_number,
            'supplier_mpn': oem_item.part_number,
            'unit_cost': oem_item.net_price or Decimal('0.00'),
            'is_active': True,
        }
        
        SupplierSKU.objects.update_or_create(
            internal_sku=product,
            supplier=supplier,
            defaults=supplier_sku_data
        )
    
    def bulk_import_by_brand(self, oem_brand_code, batch_size=100, supplier_id=None):
        """
        Import all items from an OEM brand.
        
        Args:
            oem_brand_code: OEM brand code to import
            batch_size: Maximum number of items to import
            supplier_id: Optional supplier ID to link products with
        
        Returns:
            dict with import statistics
        """
        from core.models import OEMCatalogItem
        
        # Get OEM catalog items
        if self.api_client:
            oem_items = self.api_client.get_oem_catalog_items(
                oem_code=oem_brand_code,
                is_active=True,
                page_size=batch_size
            )
            items_list = oem_items.get('results', [])
        else:
            items_list = list(OEMCatalogItem.objects.filter(
                oem_code__oem_code=oem_brand_code,
                is_active=True
            )[:batch_size])
        
        imported = 0
        skipped = 0
        errors = []
        
        for item in items_list:
            try:
                item_id = item.get('catalog_id') if isinstance(item, dict) else item.catalog_id
                
                # Check if already imported
                if self._is_already_imported(item):
                    skipped += 1
                    continue
                
                self.import_oem_to_product_master(item_id, supplier_id, commit=False)
                imported += 1
            except Exception as e:
                errors.append({
                    'item_id': item.get('catalog_id') if isinstance(item, dict) else getattr(item, 'catalog_id', None),
                    'error': str(e)
                })
        
        return {
            'brand_code': oem_brand_code,
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }
    
    def _is_already_imported(self, oem_item):
        """Check if OEM item has already been imported"""
        from core.models import ProductMaster
        
        part_number = oem_item.get('part_number') if isinstance(oem_item, dict) else oem_item.part_number
        
        return ProductMaster.objects.filter(oem_ref=part_number).exists()
    
    def create_fitment_from_oem(self, oem_catalog_item_id, equipment_id):
        """
        Create a fitment (compatibility record) from OEM catalog data.
        
        Args:
            oem_catalog_item_id: ID of OEM catalog item
            equipment_id: ID of equipment to link with
        
        Returns:
            Fitment instance
        """
        from core.models import Fitment, ProductMaster, OEMCatalogItem, Equipment
        
        # Get OEM item
        if self.api_client:
            oem_data = self.api_client.get_oem_catalog_item(oem_catalog_item_id)
            if not oem_data:
                raise ValueError(f"OEM catalog item {oem_catalog_item_id} not found")
            
            part_number = oem_data.get('part_number')
        else:
            try:
                oem_item = OEMCatalogItem.objects.get(catalog_id=oem_catalog_item_id)
                part_number = oem_item.part_number
            except OEMCatalogItem.DoesNotExist:
                raise ValueError(f"OEM catalog item {oem_catalog_item_id} not found")
        
        # Get equipment
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
        except Equipment.DoesNotExist:
            raise ValueError(f"Equipment {equipment_id} not found")
        
        # Find or create product
        product = ProductMaster.objects.filter(oem_ref=part_number).first()
        if not product:
            product = self.import_oem_to_product_master(oem_catalog_item_id)
        
        # Calculate compatibility score
        score = self._calculate_compatibility(product, equipment, oem_data if isinstance(oem_data, dict) else None)
        
        # Create fitment
        fitment, created = Fitment.objects.update_or_create(
            internal_sku=product.internal_sku,
            equipment=equipment,
            defaults={
                'score': score,
                'is_primary_fit': score >= 90,
                'notes': f'Importado desde catálogo OEM: {part_number}'
            }
        )
        
        return fitment
    
    def _calculate_compatibility(self, product, equipment, oem_data=None):
        """Calculate compatibility score"""
        score = 50
        
        # Brand match
        if product.brand and equipment.brand:
            if product.brand.lower() == equipment.brand.lower():
                score += 30
        
        # Model reference match
        if product.oem_ref:
            if equipment.model and equipment.model.lower() in product.oem_ref.lower():
                score += 10
            if equipment.vin and equipment.vin[:8] in product.oem_ref:
                score += 10
        
        # OEM data year range (if available)
        if oem_data and isinstance(oem_data, dict):
            year_start = oem_data.get('year_start')
            year_end = oem_data.get('year_end')
            if year_start and year_end:
                if year_start <= equipment.year <= year_end:
                    score += 10
        
        return min(score, 100)
    
    def sync_prices_from_oem(self, oem_brand_code=None):
        """
        Sync prices from OEM catalog to ProductMaster.
        
        Args:
            oem_brand_code: Optional brand code to filter
        
        Returns:
            dict with sync statistics
        """
        from core.models import ProductMaster, OEMCatalogItem
        
        updated = 0
        errors = []
        
        queryset = OEMCatalogItem.objects.filter(is_active=True)
        
        if oem_brand_code:
            queryset = queryset.filter(oem_code__oem_code=oem_brand_code)
        
        for oem_item in queryset:
            try:
                updated_count = ProductMaster.objects.filter(
                    oem_ref=oem_item.part_number
                ).update(
                    standard_cost=oem_item.list_price or Decimal('0.00'),
                    avg_cost=oem_item.list_price or Decimal('0.00'),
                    updated_at=timezone.now()
                )
                if updated_count > 0:
                    updated += updated_count
            except Exception as e:
                errors.append({
                    'part_number': oem_item.part_number,
                    'error': str(e)
                })
        
        return {
            'updated': updated,
            'errors': errors
        }
    
    def get_import_status(self, oem_brand_code=None):
        """
        Get status of OEM imports.
        
        Args:
            oem_brand_code: Optional brand code to filter
        
        Returns:
            dict with import status
        """
        from core.models import ProductMaster, OEMCatalogItem
        
        # Count OEM items
        oem_queryset = OEMCatalogItem.objects.filter(is_active=True)
        if oem_brand_code:
            oem_queryset = oem_queryset.filter(oem_code__oem_code=oem_brand_code)
        
        oem_count = oem_queryset.count()
        
        # Count imported products
        imported_queryset = ProductMaster.objects.filter(source_code='OEM')
        if oem_brand_code:
            imported_queryset = imported_queryset.filter(oem_code=oem_brand_code)
        
        imported_count = imported_queryset.count()
        
        # Count by brand
        by_brand = {}
        for product in imported_queryset.select_related('oem_code'):
            brand = product.oem_code or 'Unknown'
            by_brand[brand] = by_brand.get(brand, 0) + 1
        
        return {
            'total_oem_items': oem_count,
            'imported_products': imported_count,
            'pending_import': oem_count - imported_count,
            'import_percentage': round((imported_count / oem_count * 100), 2) if oem_count > 0 else 0,
            'by_brand': by_brand
        }
