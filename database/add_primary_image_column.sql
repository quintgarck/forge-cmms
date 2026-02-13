-- Migration: Add primary_image_url column to catalog_items table
-- Generated: 2024-02-05
-- This script adds support for product images in the OEM catalog
-- Schema: oem

-- Add primary_image_url column to catalog_items table
ALTER TABLE oem.catalog_items ADD COLUMN IF NOT EXISTS primary_image_url VARCHAR(500) NULL;

-- Add comment to the column
COMMENT ON COLUMN oem.catalog_items.primary_image_url IS 'URL de la imagen principal del producto (figura isométrica, foto del repuesto)';

-- Create oem_part_images table for technical images
CREATE TABLE IF NOT EXISTS oem.oem_part_images (
    image_id SERIAL PRIMARY KEY,
    catalog_id INTEGER NOT NULL REFERENCES oem.catalog_items(catalog_id) ON DELETE CASCADE,
    image_type VARCHAR(20) NOT NULL DEFAULT 'PRIMARY',
    image_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500) NULL,
    title VARCHAR(200) NULL,
    description TEXT NULL,
    hotspot_data JSONB DEFAULT '[]'::jsonb,
    part_position JSONB DEFAULT '{}'::jsonb,
    page_number INTEGER NULL,
    total_pages INTEGER NULL,
    image_width INTEGER NULL,
    image_height INTEGER NULL,
    file_size BIGINT NULL,
    mime_type VARCHAR(50) NULL,
    reference_codes JSONB DEFAULT '[]'::jsonb,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments to oem_part_images table
COMMENT ON TABLE oem.oem_part_images IS 'Imágenes técnicas para partes OEM (figuras isométricas, diagramas arquitectónicos, vistas explodidas, etc.)';

COMMENT ON COLUMN oem.oem_part_images.image_type IS 'Tipo de imagen técnica: PRIMARY, ISOMETRIC, EXPLODED, DIAGRAM, DETAIL, INSTALLATION, REFERENCE, THUMBNAIL, OTHER';
COMMENT ON COLUMN oem.oem_part_images.image_url IS 'URL de la imagen';
COMMENT ON COLUMN oem.oem_part_images.thumbnail_url IS 'URL de la miniatura';
COMMENT ON COLUMN oem.oem_part_images.hotspot_data IS 'Datos de hotspots para diagramas interactivos [{x, y, part_number, label}]';
COMMENT ON COLUMN oem.oem_part_images.part_position IS 'Posición del número de parte en el diagrama {x, y, page_number}';
COMMENT ON COLUMN oem.oem_part_images.reference_codes IS 'Lista de códigos de parte referenciados en el diagrama';

-- Create indexes for oem_part_images
CREATE INDEX IF NOT EXISTS idx_oem_part_images_catalog_id ON oem.oem_part_images(catalog_id);
CREATE INDEX IF NOT EXISTS idx_oem_part_images_image_type ON oem.oem_part_images(image_type);
CREATE INDEX IF NOT EXISTS idx_oem_part_images_is_active ON oem.oem_part_images(is_active);

-- Add foreign key constraint
ALTER TABLE oem.oem_part_images DROP CONSTRAINT IF EXISTS fk_oem_part_images_catalog;
ALTER TABLE oem.oem_part_images ADD CONSTRAINT fk_oem_part_images_catalog 
    FOREIGN KEY (catalog_id) REFERENCES oem.catalog_items(catalog_id) ON DELETE CASCADE;

PRINT 'Migration completed successfully: Added primary_image_url column and oem_part_images table';
