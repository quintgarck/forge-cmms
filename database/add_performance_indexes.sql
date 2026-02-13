-- Performance indexes for ForgeDB
-- Run this script to add indexes for frequently queried fields

-- App schema indexes (Clients, Equipment, WorkOrders, Invoices)
\c forge_db
SET search_path TO app,cat,doc,inv,kpi,oem,svc,public;

-- Clients indexes
CREATE INDEX IF NOT EXISTS idx_clients_status ON app.clients(status);
CREATE INDEX IF NOT EXISTS idx_clients_email ON app.clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_created_at ON app.clients(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clients_credit_used ON app.clients(credit_used);

-- Equipment indexes
CREATE INDEX IF NOT EXISTS idx_equipment_client ON app.equipment(client_id);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON app.equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_vin ON app.equipment(vin);
CREATE INDEX IF NOT EXISTS idx_equipment_plate ON app.equipment(license_plate);

-- Work Orders indexes (critical for dashboard performance)
CREATE INDEX IF NOT EXISTS idx_workorders_status ON app.work_orders(status);
CREATE INDEX IF NOT EXISTS idx_workorders_client ON app.work_orders(client_id);
CREATE INDEX IF NOT EXISTS idx_workorders_equipment ON app.work_orders(equipment_id);
CREATE INDEX IF NOT EXISTS idx_workorders_technician ON app.work_orders(assigned_technician_id);
CREATE INDEX IF NOT EXISTS idx_workorders_created_at ON app.work_orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workorders_completed_at ON app.work_orders(completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_workorders_scheduled ON app.work_orders(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_workorders_priority ON app.work_orders(priority);

-- Composite index for active work orders (most common query)
CREATE INDEX IF NOT EXISTS idx_workorders_active ON app.work_orders(status, created_at DESC) 
WHERE status NOT IN ('completed', 'cancelled', 'invoiced');

-- Invoices indexes
CREATE INDEX IF NOT EXISTS idx_invoices_status ON app.invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_client ON app.invoices(client_id);
CREATE INDEX IF NOT EXISTS idx_invoices_wo ON app.invoices(work_order_id);
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON app.invoices(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON app.invoices(due_date);
CREATE INDEX IF NOT EXISTS idx_invoices_invoice_date ON app.invoices(invoice_date DESC);

-- Composite index for pending invoices
CREATE INDEX IF NOT EXISTS idx_invoices_pending ON app.invoices(status, due_date) 
WHERE status != 'paid';

-- Inventory schema indexes (Stock, Transactions)
-- Stock indexes
CREATE INDEX IF NOT EXISTS idx_stock_product ON inv.stock(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_warehouse ON inv.stock(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_quantity ON inv.stock(quantity_on_hand);
CREATE INDEX IF NOT EXISTS idx_stock_last_movement ON inv.stock(last_movement_date DESC);

-- Composite index for low stock alerts
CREATE INDEX IF NOT EXISTS idx_stock_low_quantity ON inv.stock(quantity_on_hand, warehouse_id) 
WHERE quantity_on_hand <= 10;

-- Transactions indexes
CREATE INDEX IF NOT EXISTS idx_transactions_product ON inv.transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_transactions_warehouse ON inv.transactions(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON inv.transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON inv.transactions(transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_ref ON inv.transactions(reference_type, reference_number);

-- Product Master indexes
CREATE INDEX IF NOT EXISTS idx_products_code ON inv.product_master(product_code);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON inv.product_master(barcode);
CREATE INDEX IF NOT EXISTS idx_products_status ON inv.product_master(status);
CREATE INDEX IF NOT EXISTS idx_products_category ON inv.product_master(category);
CREATE INDEX IF NOT EXISTS idx_products_type ON inv.product_master(type);

-- Cat schema indexes (Technicians, Alerts)
-- Technicians indexes
CREATE INDEX IF NOT EXISTS idx_technicians_email ON cat.technicians(email);
CREATE INDEX IF NOT EXISTS idx_technicians_status ON cat.technicians(status);
CREATE INDEX IF NOT EXISTS idx_technicians_employee_code ON cat.technicians(employee_code);

-- Alerts indexes
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON app.alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON app.alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON app.alerts(alert_type);

-- Service schema indexes
-- Invoice Items indexes
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON svc.invoice_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_items_sku ON svc.invoice_items(internal_sku);

-- Payments indexes
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON svc.payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_date ON svc.payments(payment_date DESC);
CREATE INDEX IF NOT EXISTS idx_payments_method ON svc.payments(payment_method);

-- Analyze tables to update statistics
ANALYZE app.clients;
ANALYZE app.equipment;
ANALYZE app.work_orders;
ANALYZE app.invoices;
ANALYZE inv.stock;
ANALYZE inv.transactions;
ANALYZE inv.product_master;
ANALYZE cat.technicians;
ANALYZE app.alerts;
ANALYZE svc.invoice_items;
ANALYZE svc.payments;

-- Display index creation summary
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname IN ('app', 'inv', 'cat', 'svc', 'doc', 'oem', 'kpi')
AND indexname LIKE 'idx_%'
ORDER BY schemaname, tablename, indexname;
