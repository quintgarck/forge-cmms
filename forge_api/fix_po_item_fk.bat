@echo off
REM Script para eliminar la foreign key constraint de po_items.internal_sku
REM que referencia a product_master.internal_sku

echo Eliminando foreign key constraint po_items_internal_sku_fkey...
psql -U postgres -d forge_db -c "ALTER TABLE inv.po_items DROP CONSTRAINT IF EXISTS po_items_internal_sku_fkey;"

echo.
echo Proceso completado. La constraint ha sido eliminada.
pause
