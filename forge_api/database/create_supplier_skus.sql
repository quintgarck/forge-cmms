-- =============================================================================
-- Supplier SKU Mapping Table
-- Schema: inv
-- Purpose: Map internal SKUs to supplier-specific SKUs
-- =============================================================================

-- Create supplier_skus table
CREATE TABLE IF NOT EXISTS inv.supplier_skus (
    supplier_sku_id SERIAL PRIMARY KEY,
    internal_sku VARCHAR(20) NOT NULL REFERENCES inv.product_master(internal_sku) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES cat.suppliers(supplier_id) ON DELETE CASCADE,
    supplier_sku_code VARCHAR(50) NULL,
    supplier_mpn VARCHAR(50) NULL,
    is_preferred BOOLEAN DEFAULT FALSE,
    unit_cost DECIMAL(12, 2) DEFAULT 0.00,
    lead_time_days INTEGER DEFAULT 7,
    min_order_qty INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unique constraint: one mapping per supplier per product
CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_skus_unique 
ON inv.supplier_skus(internal_sku, supplier_id);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_supplier_skus_supplier 
ON inv.supplier_skus(supplier_id);

CREATE INDEX IF NOT EXISTS idx_supplier_skus_internal_sku 
ON inv.supplier_skus(internal_sku);

CREATE INDEX IF NOT EXISTS idx_supplier_skus_supplier_sku_code 
ON inv.supplier_skus(supplier_sku_code);

CREATE INDEX IF NOT EXISTS idx_supplier_skus_supplier_mpn 
ON inv.supplier_skus(supplier_mpn);

-- Comments
COMMENT ON TABLE inv.supplier_skus IS 'Maps internal product SKUs to supplier-specific SKUs. Allows multiple SKUs per product from different suppliers.';
COMMENT ON COLUMN inv.supplier_skus.internal_sku IS 'Reference to internal product SKU';
COMMENT ON COLUMN inv.supplier_skus.supplier_id IS 'Reference to supplier';
COMMENT ON COLUMN inv.supplier_skus.supplier_sku_code IS 'Supplier''s SKU/code for this product';
COMMENT ON COLUMN inv.supplier_skus.supplier_mpn IS 'Manufacturer''s Part Number from supplier';
COMMENT ON COLUMN inv.supplier_skus.is_preferred IS 'Preferred supplier for this product';
COMMENT ON COLUMN inv.supplier_skus.unit_cost IS 'Last purchase cost from this supplier';
