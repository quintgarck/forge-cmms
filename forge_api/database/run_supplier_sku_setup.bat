@echo off
REM =============================================================================
REM Supplier SKU Setup Script
REM This script creates the supplier_skus table and updates po_items
REM =============================================================================

echo ============================================
echo Creating supplier_skus table...
echo ============================================
psql -h localhost -U postgres -d forge_db -f create_supplier_skus.sql
IF %ERRORLEVEL% NEQ 0 (
    echo Error creating supplier_skus table
    pause
    exit /b 1
)

echo ============================================
echo Adding supplier_sku_id column to po_items...
echo ============================================
psql -h localhost -U postgres -d forge_db -f add_supplier_sku_to_po_items.sql
IF %ERRORLEVEL% NEQ 0 (
    echo Error adding supplier_sku_id column
    pause
    exit /b 1
)

echo ============================================
echo Setup completed successfully!
echo ============================================
pause
