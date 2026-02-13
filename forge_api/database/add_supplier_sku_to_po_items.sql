-- =============================================================================
-- Add supplier_sku_id column to po_items table
-- =============================================================================

-- Add supplier_sku_id column to po_items
ALTER TABLE inv.po_items 
ADD COLUMN IF NOT EXISTS supplier_sku_id INTEGER NULL REFERENCES inv.supplier_skus(supplier_sku_id) ON DELETE SET NULL;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_po_items_supplier_sku 
ON inv.po_items(supplier_sku_id);

-- Add comment
COMMENT ON COLUMN inv.po_items.supplier_sku_id IS 'Reference to supplier SKU mapping (inv.supplier_skus)';
