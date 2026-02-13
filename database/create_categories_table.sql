-- Migration script for Category table
-- Run this in PostgreSQL to create the categories table

-- Create the categories table in the cat schema
CREATE TABLE IF NOT EXISTS cat.categories (
    category_id SERIAL PRIMARY KEY,
    category_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    icon VARCHAR(50) NULL,
    color VARCHAR(20) NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add comments
COMMENT ON TABLE cat.categories IS 'Equipment categories - replaces static CATEGORY_CHOICES';
COMMENT ON COLUMN cat.categories.category_id IS 'Primary key';
COMMENT ON COLUMN cat.categories.category_code IS 'Unique category code';
COMMENT ON COLUMN cat.categories.name IS 'Category name';
COMMENT ON COLUMN cat.categories.description IS 'Category description';
COMMENT ON COLUMN cat.categories.icon IS 'Bootstrap icon class';
COMMENT ON COLUMN cat.categories.color IS 'Category color for UI';
COMMENT ON COLUMN cat.categories.sort_order IS 'Display order';
COMMENT ON COLUMN cat.categories.is_active IS 'Active status';
COMMENT ON COLUMN cat.categories.created_at IS 'Creation timestamp';
COMMENT ON COLUMN cat.categories.updated_at IS 'Update timestamp';

-- Create index for ordering
CREATE INDEX IF NOT EXISTS idx_cat_categories_sort_order 
ON cat.categories (sort_order, name);

-- Seed initial categories
INSERT INTO cat.categories (category_code, name, description, icon, color, sort_order, is_active)
VALUES 
    ('AUTOMOTRIZ', 'Automotriz', 'Vehículos automobiles y ligeros', 'bi-car-front', '#3498db', 1, TRUE),
    ('INDUSTRIAL', 'Industrial', 'Equipos y maquinaria industrial', 'bi-gear-wide-connected', '#9b59b6', 2, TRUE),
    ('AGRICOLA', 'Agrícola', 'Maquinaria agrícola', 'bi-tree', '#27ae60', 3, TRUE),
    ('CONSTRUCCION', 'Construcción', 'Equipos de construcción', 'bi-hammer', '#e67e22', 4, TRUE),
    ('ELECTRONICO', 'Electrónico', 'Equipos electrónicos', 'bi-cpu', '#1abc9c', 5, TRUE),
    ('OTRO', 'Otro', 'Otras categorías', 'bi-box', '#95a5a6', 99, TRUE)
ON CONFLICT (category_code) DO NOTHING;

-- Update equipment_types to use category_id
-- First, add the category_id column as nullable
ALTER TABLE cat.equipment_types ADD COLUMN IF NOT EXISTS category_id INTEGER NULL;

-- Map existing category values to category_id
UPDATE cat.equipment_types et
SET category_id = (
    SELECT c.category_id 
    FROM cat.categories c 
    WHERE UPPER(c.category_code) = UPPER(et.category)
);

-- Check how many records have NULL category_id
SELECT COUNT(*) as null_count FROM cat.equipment_types WHERE category_id IS NULL;

-- If you have data that didn't map, set a default category or handle manually
-- For now, set NULLs to category 6 (OTRO)
UPDATE cat.equipment_types SET category_id = 6 WHERE category_id IS NULL;

-- Set not null constraint
ALTER TABLE cat.equipment_types ALTER COLUMN category_id SET NOT NULL;

-- Drop the old category column
ALTER TABLE cat.equipment_types DROP COLUMN IF EXISTS category;

-- Add foreign key constraint
ALTER TABLE cat.equipment_types 
ADD CONSTRAINT fk_equipment_types_category 
FOREIGN KEY (category_id) REFERENCES cat.categories(category_id) 
ON DELETE SET NULL;

-- Create index
CREATE INDEX IF NOT EXISTS idx_equipment_types_category_id 
ON cat.equipment_types (category_id);

-- Verify the changes
SELECT 'Categories created:' as message, COUNT(*) as count FROM cat.categories;
SELECT 'Equipment types updated:' as message, COUNT(*) as count FROM cat.equipment_types;
