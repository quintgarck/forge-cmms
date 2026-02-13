-- Script para eliminar la foreign key constraint de po_items.internal_sku
-- que referencia a product_master.internal_sku

-- Primero, buscar las constraints existentes
SELECT 
    conname AS constraint_name,
    contype AS constraint_type
FROM pg_constraint
WHERE conrelid = 'po_items'::regclass::oid
   OR conrelid = 'inv_schema_po_items'::regclass::oid;

-- Eliminar la foreign key constraint si existe
-- (reemplazar 'fk_po_items_product_master' con el nombre real de la constraint)
-- ALTER TABLE inv_schema.po_items DROP CONSTRAINT IF EXISTS fk_po_items_product_master;

-- Si la tabla está en el esquema 'inv_schema':
-- ALTER TABLE inv_schema.po_items DROP CONSTRAINT IF EXISTS fk_po_items_product_master;

-- Si la tabla está en el esquema público:
ALTER TABLE public.po_items DROP CONSTRAINT IF EXISTS fk_po_items_product_master;

-- Verificar que la constraint fue eliminada
SELECT 
    conname AS constraint_name
FROM pg_constraint
WHERE conrelid = 'po_items'::regclass::oid
   AND contype = 'f';
