-- SQL to add type_id column to equipment table in the cat schema
-- Run this in your PostgreSQL database (pgAdmin or psql)

ALTER TABLE cat.equipment ADD COLUMN type_id INTEGER NULL DEFAULT 1;

-- Verify the column was added
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'equipment' AND table_schema = 'cat'
ORDER BY ordinal_position;
