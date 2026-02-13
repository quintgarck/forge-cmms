-- =====================================================
-- PARTE 2: VISTAS COMPLETAS - TODAS LAS VISTAS DE AMBAS VERSIONES
-- =====================================================

-- =====================================================
-- 1. VISTAS DE INVENTARIO
-- =====================================================

-- Vista para dashboard de inventario (de primera versión)
CREATE VIEW kpi.inventory_dashboard AS
SELECT 
    wh.warehouse_code,
    wh.name as warehouse_name,
    wh.type as warehouse_type,
    COUNT(DISTINCT s.internal_sku) as sku_count,
    SUM(s.qty_on_hand) as total_qty,
    SUM(s.total_cost) as total_value,
    COUNT(DISTINCT CASE WHEN s.qty_available < pm.reorder_point THEN s.internal_sku END) as low_stock_count,
    COUNT(DISTINCT CASE WHEN s.qty_available = 0 THEN s.internal_sku END) as out_of_stock_count,
    ROUND(SUM(s.total_cost) / NULLIF(SUM(wh.capacity), 0) * 100, 2) as occupancy_percent
FROM inv.warehouses wh
LEFT JOIN inv.stock s ON wh.warehouse_code = s.warehouse_code
LEFT JOIN inv.product_master pm ON s.internal_sku = pm.internal_sku
WHERE wh.is_active = TRUE
GROUP BY wh.warehouse_code, wh.name, wh.type;

-- Vista de stock con información completa (combinada de ambas versiones)
CREATE VIEW kpi.stock_view AS
SELECT 
    s.stock_id,
    s.internal_sku,
    pm.name as product_name,
    pm.group_code,
    tg.name_es as group_name,
    pm.brand,
    pm.source_code,
    cs.name_es as source_name,
    s.warehouse_code,
    wh.name as warehouse_name,
    s.bin_id,
    b.bin_code,
    s.qty_on_hand,
    s.qty_reserved,
    s.qty_available,
    s.qty_on_order,
    s.unit_cost,
    s.total_cost,
    pm.min_stock,
    pm.reorder_point,
    pm.max_stock,
    s.last_receipt_date,
    s.expiration_date,
    s.status,
    CASE 
        WHEN s.qty_available < pm.reorder_point THEN 'CRÍTICO'
        WHEN s.qty_available < pm.min_stock THEN 'BAJO'
        ELSE 'OK'
    END as stock_status,
    CASE 
        WHEN s.expiration_date IS NOT NULL AND s.expiration_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'PRÓXIMO A VENCER'
        WHEN s.expiration_date IS NOT NULL AND s.expiration_date <= CURRENT_DATE THEN 'VENCIDO'
        ELSE 'VÁLIDO'
    END as expiration_status,
    CASE 
        WHEN s.last_receipt_date <= CURRENT_DATE - INTERVAL '90 days' THEN 'LENTO'
        WHEN s.last_receipt_date <= CURRENT_DATE - INTERVAL '180 days' THEN 'MUY LENTO'
        WHEN s.last_receipt_date <= CURRENT_DATE - INTERVAL '365 days' THEN 'OBSOLETO'
        ELSE 'ACTIVO'
    END as rotation_status
FROM inv.stock s
JOIN inv.product_master pm ON s.internal_sku = pm.internal_sku
JOIN inv.warehouses wh ON s.warehouse_code = wh.warehouse_code
LEFT JOIN inv.bins b ON s.bin_id = b.bin_id
LEFT JOIN cat.taxonomy_groups tg ON pm.group_code = tg.group_code
LEFT JOIN cat.source_codes cs ON pm.source_code = cs.source_code
WHERE pm.is_active = TRUE;

-- Vista para productos con stock crítico
CREATE VIEW kpi.critical_stock AS
SELECT 
    s.internal_sku,
    pm.name,
    pm.brand,
    tg.name_es as grupo,
    s.warehouse_code,
    wh.name as warehouse_name,
    s.qty_available,
    pm.reorder_point,
    pm.min_stock,
    pm.lead_time_days,
    CASE 
        WHEN s.qty_available = 0 THEN 'AGOTADO'
        WHEN s.qty_available < pm.min_stock THEN 'MÍNIMO'
        WHEN s.qty_available < pm.reorder_point THEN 'REORDEN'
        ELSE 'OK'
    END as critical_level,
    ROUND((s.qty_available::DECIMAL / pm.reorder_point * 100), 2) as reorder_percent,
    pm.last_purchase_cost,
    pm.avg_cost,
    s.last_receipt_date,
    EXTRACT(DAY FROM CURRENT_DATE - s.last_receipt_date) as days_in_stock
FROM inv.stock s
JOIN inv.product_master pm ON s.internal_sku = pm.internal_sku
JOIN inv.warehouses wh ON s.warehouse_code = wh.warehouse_code
LEFT JOIN cat.taxonomy_groups tg ON pm.group_code = tg.group_code
WHERE pm.is_active = TRUE
AND s.qty_available <= pm.reorder_point
ORDER BY s.qty_available ASC, pm.reorder_point DESC;

-- Vista para rotación de inventario
CREATE VIEW kpi.inventory_turnover AS
SELECT 
    pm.internal_sku,
    pm.name,
    pm.group_code,
    tg.name_es as grupo,
    SUM(s.qty_on_hand) as total_stock,
    SUM(s.total_cost) as stock_value,
    COUNT(DISTINCT CASE WHEN t.txn_type = 'OUT' AND t.txn_date >= CURRENT_DATE - INTERVAL '90 days' THEN t.txn_id END) as transactions_90d,
    SUM(CASE WHEN t.txn_type = 'OUT' AND t.txn_date >= CURRENT_DATE - INTERVAL '90 days' THEN ABS(t.qty) ELSE 0 END) as units_sold_90d,
    SUM(CASE WHEN t.txn_type = 'OUT' AND t.txn_date >= CURRENT_DATE - INTERVAL '90 days' THEN t.total_cost ELSE 0 END) as value_sold_90d,
    CASE 
        WHEN SUM(s.qty_on_hand) > 0 
        THEN ROUND(SUM(CASE WHEN t.txn_type = 'OUT' AND t.txn_date >= CURRENT_DATE - INTERVAL '90 days' THEN ABS(t.qty) ELSE 0 END)::DECIMAL / SUM(s.qty_on_hand) * 4, 2)
        ELSE 0 
    END as turnover_rate_annualized,
    AVG(CASE WHEN t.txn_type = 'IN' THEN t.unit_cost ELSE NULL END) as avg_purchase_cost,
    MIN(s.last_receipt_date) as oldest_stock_date,
    MAX(s.last_receipt_date) as newest_stock_date
FROM inv.product_master pm
LEFT JOIN inv.stock s ON pm.internal_sku = s.internal_sku
LEFT JOIN inv.transactions t ON pm.internal_sku = t.internal_sku
LEFT JOIN cat.taxonomy_groups tg ON pm.group_code = tg.group_code
WHERE pm.is_active = TRUE
GROUP BY pm.internal_sku, pm.name, pm.group_code, tg.name_es
HAVING SUM(s.qty_on_hand) > 0;

-- =====================================================
-- 2. VISTAS DE ÓRDENES DE TRABAJO
-- =====================================================

-- Vista para órdenes de trabajo activas (combinada)
CREATE VIEW kpi.active_work_orders AS
SELECT 
    wo.wo_id,
    wo.wo_number,
    wo.status,
    wo.priority,
    wo.service_type,
    wo.created_at,
    wo.reception_date,
    wo.estimated_completion_date,
    wo.actual_completion_date,
    wo.delivery_date,
    e.equipment_code,
    e.brand || ' ' || e.model as equipment,
    c.client_code,
    c.name as client_name,
    t.first_name || ' ' || t.last_name as technician_name,
    wo.actual_hours,
    wo.flat_rate_hours,
    wo.efficiency_rate,
    wo.total_cost,
    wo.final_price,
    CASE 
        WHEN wo.delivery_date IS NOT NULL THEN 'ENTREGADO'
        WHEN wo.actual_completion_date IS NOT NULL THEN 'COMPLETADO'
        WHEN wo.actual_start_date IS NOT NULL THEN 'EN PROCESO'
        WHEN wo.reception_date IS NOT NULL THEN 'RECEPCIONADO'
        ELSE 'PENDIENTE'
    END as progress_status,
    EXTRACT(DAY FROM CURRENT_DATE - wo.reception_date) as days_in_progress,
    EXTRACT(DAY FROM wo.estimated_completion_date - CURRENT_DATE) as days_until_due
FROM svc.work_orders wo
JOIN cat.equipment e ON wo.equipment_id = e.equipment_id
JOIN cat.clients c ON wo.client_id = c.client_id
LEFT JOIN cat.technicians t ON wo.technician_id = t.technician_id
WHERE wo.status NOT IN ('CERRADO', 'CANCELLED')
ORDER BY 
    CASE wo.priority 
        WHEN 'URGENTE' THEN 1
        WHEN 'ALTA' THEN 2
        WHEN 'NORMAL' THEN 3
        WHEN 'BAJA' THEN 4
    END,
    wo.estimated_completion_date NULLS LAST,
    wo.created_at;

-- Vista para detalle completo de órdenes de trabajo
CREATE VIEW kpi.wo_detail AS
SELECT 
    wo.wo_id,
    wo.wo_number,
    wo.status,
    wo.service_type,
    wo.priority,
    wo.created_at,
    wo.reception_date,
    wo.delivery_date,
    wo.actual_hours,
    wo.flat_rate_hours,
    wo.efficiency_rate,
    wo.total_cost,
    wo.final_price,
    wo.customer_complaints,
    wo.technician_notes,
    wo.qc_notes,
    wo.final_report,
    e.equipment_id,
    e.equipment_code,
    e.brand as equipment_brand,
    e.model as equipment_model,
    e.year as equipment_year,
    e.vin,
    e.license_plate,
    e.current_mileage_hours,
    wo.mileage_in,
    wo.mileage_out,
    wo.hours_in,
    wo.hours_out,
    c.client_id,
    c.client_code,
    c.name as client_name,
    c.email as client_email,
    c.phone as client_phone,
    tech.technician_id,
    tech.first_name || ' ' || tech.last_name as technician_name,
    tech.specialization,
    advisor.first_name || ' ' || advisor.last_name as advisor_name,
    qc.first_name || ' ' || qc.last_name as qc_technician_name,
    -- Sumarizamos los items
    (SELECT COUNT(*) FROM svc.wo_items wi WHERE wi.wo_id = wo.wo_id) as item_count,
    (SELECT SUM(qty_used * unit_price) FROM svc.wo_items wi WHERE wi.wo_id = wo.wo_id AND wi.status = 'USED') as parts_cost_calc,
    (SELECT COUNT(*) FROM svc.wo_services ws WHERE ws.wo_id = wo.wo_id) as service_count,
    (SELECT SUM(labor_cost) FROM svc.wo_services ws WHERE ws.wo_id = wo.wo_id) as labor_cost_calc,
    -- Documentos
    (SELECT COUNT(*) FROM doc.documents d WHERE d.entity_type = 'WORK_ORDER' AND d.entity_id = wo.wo_id) as document_count
FROM svc.work_orders wo
JOIN cat.equipment e ON wo.equipment_id = e.equipment_id
JOIN cat.clients c ON wo.client_id = c.client_id
LEFT JOIN cat.technicians tech ON wo.technician_id = tech.technician_id
LEFT JOIN cat.technicians advisor ON wo.advisor_id = advisor.technician_id
LEFT JOIN cat.technicians qc ON wo.qc_technician_id = qc.technician_id;

-- Vista para tiempos de ciclo de trabajo
CREATE VIEW kpi.wo_cycle_times AS
SELECT 
    wo.wo_id,
    wo.wo_number,
    wo.status,
    wo.service_type,
    wo.priority,
    EXTRACT(DAY FROM wo.reception_date - wo.appointment_date) as days_appointment_to_reception,
    EXTRACT(DAY FROM wo.diagnosis_date - wo.reception_date) as days_reception_to_diagnosis,
    EXTRACT(DAY FROM wo.actual_completion_date - wo.actual_start_date) as days_work_duration,
    EXTRACT(DAY FROM wo.qc_date - wo.actual_completion_date) as days_completion_to_qc,
    EXTRACT(DAY FROM wo.delivery_date - wo.qc_date) as days_qc_to_delivery,
    EXTRACT(DAY FROM wo.delivery_date - wo.reception_date) as days_total_cycle,
    EXTRACT(DAY FROM wo.estimated_completion_date - wo.reception_date) as days_estimated_cycle,
    CASE 
        WHEN wo.delivery_date IS NOT NULL AND wo.reception_date IS NOT NULL 
        THEN EXTRACT(DAY FROM wo.delivery_date - wo.reception_date) - EXTRACT(DAY FROM wo.estimated_completion_date - wo.reception_date)
        ELSE NULL
    END as days_variance,
    wo.actual_hours,
    wo.flat_rate_hours,
    ROUND(wo.efficiency_rate, 2) as efficiency_percent,
    e.brand || ' ' || e.model as equipment,
    t.first_name || ' ' || t.last_name as technician
FROM svc.work_orders wo
JOIN cat.equipment e ON wo.equipment_id = e.equipment_id
LEFT JOIN cat.technicians t ON wo.technician_id = t.technician_id
WHERE wo.delivery_date IS NOT NULL
ORDER BY wo.delivery_date DESC;

-- =====================================================
-- 3. VISTAS DE FACTURACIÓN Y FINANZAS
-- =====================================================

-- Vista para facturas pendientes (de primera versión)
CREATE VIEW kpi.pending_invoices AS
SELECT 
    i.invoice_id,
    i.invoice_number,
    i.issue_date,
    i.due_date,
    i.total_amount,
    i.status,
    i.paid_date,
    c.name as client_name,
    c.client_code,
    c.email as client_email,
    c.phone as client_phone,
    wo.wo_number,
    e.brand || ' ' || e.model as equipment,
    DATEDIFF('day', CURRENT_DATE, i.due_date) as days_until_due,
    CASE 
        WHEN i.status = 'OVERDUE' THEN 'VENCIDA'
        WHEN i.due_date < CURRENT_DATE AND i.status = 'SENT' THEN 'VENCIDA'
        WHEN i.due_date <= CURRENT_DATE + 7 AND i.status = 'SENT' THEN 'PRÓXIMA'
        ELSE 'EN TIEMPO'
    END as payment_status,
    (SELECT SUM(amount) FROM svc.payments p WHERE p.invoice_id = i.invoice_id) as amount_paid,
    i.total_amount - COALESCE((SELECT SUM(amount) FROM svc.payments p WHERE p.invoice_id = i.invoice_id), 0) as amount_due
FROM svc.invoices i
JOIN cat.clients c ON i.client_id = c.client_id
LEFT JOIN svc.work_orders wo ON i.wo_id = wo.wo_id
LEFT JOIN cat.equipment e ON wo.equipment_id = e.equipment_id
WHERE i.status IN ('SENT', 'OVERDUE')
ORDER BY i.due_date, i.total_amount DESC;

-- Vista para ingresos por período
CREATE VIEW kpi.revenue_by_period AS
WITH daily_revenue AS (
    SELECT 
        DATE(p.payment_date) as payment_day,
        EXTRACT(YEAR FROM p.payment_date) as payment_year,
        EXTRACT(MONTH FROM p.payment_date) as payment_month,
        EXTRACT(WEEK FROM p.payment_date) as payment_week,
        p.currency_code,
        SUM(p.amount) as daily_amount,
        COUNT(DISTINCT p.invoice_id) as invoice_count
    FROM svc.payments p
    WHERE p.payment_date >= CURRENT_DATE - INTERVAL '365 days'
    GROUP BY DATE(p.payment_date), EXTRACT(YEAR FROM p.payment_date), EXTRACT(MONTH FROM p.payment_date), 
             EXTRACT(WEEK FROM p.payment_date), p.currency_code
),
monthly_revenue AS (
    SELECT 
        payment_year,
        payment_month,
        currency_code,
        SUM(daily_amount) as monthly_amount,
        SUM(invoice_count) as monthly_invoices,
        AVG(daily_amount) as avg_daily_amount
    FROM daily_revenue
    GROUP BY payment_year, payment_month, currency_code
)
SELECT 
    dr.payment_day,
    dr.payment_year,
    dr.payment_month,
    dr.payment_week,
    dr.currency_code,
    dr.daily_amount,
    dr.invoice_count,
    mr.monthly_amount,
    mr.monthly_invoices,
    mr.avg_daily_amount,
    ROUND(dr.daily_amount / NULLIF(mr.monthly_amount, 0) * 100, 2) as daily_percent_of_monthly
FROM daily_revenue dr
JOIN monthly_revenue mr ON dr.payment_year = mr.payment_year 
                        AND dr.payment_month = mr.payment_month 
                        AND dr.currency_code = mr.currency_code
ORDER BY dr.payment_day DESC;

-- Vista para análisis de clientes
CREATE VIEW kpi.client_analysis AS
SELECT 
    c.client_id,
    c.client_code,
    c.name,
    c.type,
    c.status,
    c.credit_limit,
    c.credit_used,
    ROUND(c.credit_used / NULLIF(c.credit_limit, 0) * 100, 2) as credit_utilization_percent,
    COUNT(DISTINCT wo.wo_id) as total_work_orders,
    COUNT(DISTINCT CASE WHEN wo.status = 'CERRADO' THEN wo.wo_id END) as completed_work_orders,
    COUNT(DISTINCT e.equipment_id) as total_equipment,
    COUNT(DISTINCT i.invoice_id) as total_invoices,
    SUM(CASE WHEN i.status = 'PAID' THEN i.total_amount ELSE 0 END) as total_paid,
    SUM(CASE WHEN i.status IN ('SENT', 'OVERDUE') THEN i.total_amount ELSE 0 END) as total_pending,
    MAX(i.issue_date) as last_invoice_date,
    MIN(CASE WHEN i.status IN ('SENT', 'OVERDUE') THEN i.due_date END) as earliest_due_date,
    AVG(CASE WHEN i.status = 'PAID' THEN EXTRACT(DAY FROM i.paid_date - i.issue_date) END) as avg_payment_days
FROM cat.clients c
LEFT JOIN svc.work_orders wo ON c.client_id = wo.client_id
LEFT JOIN cat.equipment e ON c.client_id = e.client_id
LEFT JOIN svc.invoices i ON c.client_id = i.client_id
GROUP BY c.client_id, c.client_code, c.name, c.type, c.status, c.credit_limit, c.credit_used
ORDER BY total_pending DESC, credit_utilization_percent DESC;

-- =====================================================
-- 4. VISTAS DE TÉCNICOS Y PERSONAL
-- =====================================================

-- Vista de desempeño de técnicos (combinada)
CREATE VIEW kpi.technician_performance AS
SELECT 
    t.technician_id,
    t.employee_code,
    t.first_name || ' ' || t.last_name as technician_name,
    t.specialization,
    t.certification_level,
    t.hourly_rate,
    t.efficiency_avg,
    t.quality_score,
    t.jobs_completed,
    t.status,
    -- Estadísticas de órdenes de trabajo
    COUNT(DISTINCT wo.wo_id) as total_orders,
    COUNT(DISTINCT CASE WHEN wo.status = 'CERRADO' THEN wo.wo_id END) as completed_orders,
    COUNT(DISTINCT CASE WHEN wo.status IN ('QA', 'ENTREGADO') THEN wo.wo_id END) as delivered_orders,
    COUNT(DISTINCT CASE WHEN wo.status = 'EN_PROCESO' THEN wo.wo_id END) as in_progress_orders,
    -- Horas y costos
    SUM(wo.actual_hours) as total_hours,
    AVG(wo.efficiency_rate) as avg_efficiency,
    SUM(wo.labor_cost) as total_labor_revenue,
    -- Métricas de calidad
    AVG(kpi.quality_score) as avg_quality_score,
    AVG(kpi.customer_satisfaction) as avg_customer_satisfaction,
    -- Tiempos
    AVG(EXTRACT(HOUR FROM wo.actual_completion_date - wo.actual_start_date)) as avg_hours_per_wo,
    AVG(EXTRACT(DAY FROM wo.delivery_date - wo.reception_date)) as avg_days_per_wo,
    -- Último trabajo
    MAX(wo.delivery_date) as last_delivery_date,
    COUNT(DISTINCT CASE WHEN wo.priority = 'URGENTE' THEN wo.wo_id END) as urgent_orders
FROM cat.technicians t
LEFT JOIN svc.work_orders wo ON t.technician_id = wo.technician_id
LEFT JOIN kpi.wo_metrics kpi ON wo.wo_id = kpi.wo_id
WHERE t.is_active = TRUE
GROUP BY t.technician_id, t.employee_code, t.first_name, t.last_name, t.specialization, 
         t.certification_level, t.hourly_rate, t.efficiency_avg, t.quality_score, 
         t.jobs_completed, t.status
ORDER BY total_labor_revenue DESC, avg_efficiency DESC;

-- Vista para disponibilidad de técnicos
CREATE VIEW kpi.technician_availability AS
SELECT 
    t.technician_id,
    t.employee_code,
    t.first_name || ' ' || t.last_name as technician_name,
    t.status,
    t.specialization,
    -- Órdenes en progreso
    (SELECT COUNT(*) FROM svc.work_orders wo 
     WHERE wo.technician_id = t.technician_id AND wo.status = 'EN_PROCESO') as current_workload,
    -- Horas asignadas esta semana
    (SELECT SUM(wo.estimated_hours) FROM svc.work_orders wo 
     WHERE wo.technician_id = t.technician_id 
     AND wo.estimated_start_date >= date_trunc('week', CURRENT_DATE)
     AND wo.estimated_start_date < date_trunc('week', CURRENT_DATE) + INTERVAL '1 week') as weekly_hours_assigned,
    -- Disponibilidad según horario de trabajo
    CASE 
        WHEN t.status IN ('VACATION', 'SICK') THEN 'NO DISPONIBLE'
        WHEN (SELECT COUNT(*) FROM svc.work_orders wo 
              WHERE wo.technician_id = t.technician_id 
              AND wo.status = 'EN_PROCESO') > 2 THEN 'OCUPADO'
        WHEN (t.work_schedule->>TO_CHAR(CURRENT_DATE, 'dy'))::boolean = FALSE THEN 'NO LABORA'
        ELSE 'DISPONIBLE'
    END as current_availability,
    -- Próximas citas
    (SELECT COUNT(*) FROM svc.work_orders wo 
     WHERE wo.technician_id = t.technician_id 
     AND wo.appointment_date >= CURRENT_DATE
     AND wo.appointment_date < CURRENT_DATE + INTERVAL '7 days') as upcoming_appointments
FROM cat.technicians t
WHERE t.is_active = TRUE
ORDER BY t.status, current_workload;

-- =====================================================
-- 5. VISTAS DE EQUIPOS Y ACTIVOS
-- =====================================================

-- Vista para historial de mantenimiento de equipos
CREATE VIEW kpi.equipment_maintenance_history AS
SELECT 
    e.equipment_id,
    e.equipment_code,
    e.brand,
    e.model,
    e.year,
    e.vin,
    e.license_plate,
    e.current_mileage_hours,
    e.last_service_date,
    e.next_service_date,
    e.total_service_hours,
    e.total_service_cost,
    e.status as equipment_status,
    c.client_id,
    c.name as client_name,
    -- Historial de servicios
    COUNT(DISTINCT wo.wo_id) as total_service_count,
    COUNT(DISTINCT CASE WHEN wo.service_type = 'PREVENTIVO' THEN wo.wo_id END) as preventive_count,
    COUNT(DISTINCT CASE WHEN wo.service_type = 'CORRECTIVO' THEN wo.wo_id END) as corrective_count,
    COUNT(DISTINCT CASE WHEN wo.service_type = 'GARANTÍA' THEN wo.wo_id END) as warranty_count,
    -- Fechas importantes
    MIN(wo.reception_date) as first_service_date,
    MAX(wo.reception_date) as last_service_date_actual,
    AVG(EXTRACT(DAY FROM wo.delivery_date - wo.reception_date)) as avg_service_days,
    -- Costos
    SUM(wo.total_cost) as total_service_cost_actual,
    AVG(wo.total_cost) as avg_service_cost,
    -- Próximo servicio estimado
    CASE 
        WHEN e.next_service_date IS NOT NULL THEN e.next_service_date
        WHEN MAX(wo.delivery_date) IS NOT NULL THEN MAX(wo.delivery_date) + INTERVAL '90 days'
        ELSE CURRENT_DATE + INTERVAL '90 days'
    END as next_service_estimated,
    -- Recomendaciones
    CASE 
        WHEN e.next_service_date < CURRENT_DATE THEN 'SERVICIO VENCIDO'
        WHEN e.next_service_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'SERVICIO PRÓXIMO'
        ELSE 'EN ORDEN'
    END as service_alert
FROM cat.equipment e
JOIN cat.clients c ON e.client_id = c.client_id
LEFT JOIN svc.work_orders wo ON e.equipment_id = wo.equipment_id AND wo.status = 'CERRADO'
GROUP BY e.equipment_id, e.equipment_code, e.brand, e.model, e.year, e.vin, e.license_plate,
         e.current_mileage_hours, e.last_service_date, e.next_service_date, e.total_service_hours,
         e.total_service_cost, e.status, c.client_id, c.name;

-- Vista para equipos por cliente
CREATE VIEW kpi.client_equipment_summary AS
SELECT 
    c.client_id,
    c.client_code,
    c.name as client_name,
    c.type as client_type,
    COUNT(DISTINCT e.equipment_id) as total_equipment,
    COUNT(DISTINCT CASE WHEN e.status = 'ACTIVO' THEN e.equipment_id END) as active_equipment,
    COUNT(DISTINCT CASE WHEN e.status = 'REPARACIÓN' THEN e.equipment_id END) as in_repair_equipment,
    COUNT(DISTINCT CASE WHEN e.status = 'GARANTÍA' THEN e.equipment_id END) as warranty_equipment,
    -- Tipos de equipos
    COUNT(DISTINCT CASE WHEN et.category = 'AUTOMOTRIZ' THEN e.equipment_id END) as automotive_count,
    COUNT(DISTINCT CASE WHEN et.category = 'INDUSTRIAL' THEN e.equipment_id END) as industrial_count,
    COUNT(DISTINCT CASE WHEN et.category = 'AGRÍCOLA' THEN e.equipment_id END) as agricultural_count,
    -- Marcas principales
    MODE() WITHIN GROUP (ORDER BY e.brand) as most_common_brand,
    -- Último servicio
    MAX(e.last_service_date) as last_service_overall,
    -- Próximos servicios
    COUNT(DISTINCT CASE WHEN e.next_service_date <= CURRENT_DATE + INTERVAL '30 days' THEN e.equipment_id END) as upcoming_services_30d,
    -- Costo total de mantenimiento
    SUM(e.total_service_cost) as total_maintenance_cost
FROM cat.clients c
LEFT JOIN cat.equipment e ON c.client_id = e.client_id
LEFT JOIN cat.equipment_types et ON e.type_id = et.type_id
GROUP BY c.client_id, c.client_code, c.name, c.type
ORDER BY total_equipment DESC;

-- =====================================================
-- 6. VISTAS DE ABASTECIMIENTO Y PROVEEDORES
-- =====================================================

-- Vista para desempeño de proveedores
CREATE VIEW kpi.supplier_performance AS
SELECT 
    s.supplier_id,
    s.supplier_code,
    s.name as supplier_name,
    s.contact_person,
    s.rating,
    s.quality_score,
    s.delivery_time_avg,
    s.is_preferred,
    s.status,
    -- Estadísticas de órdenes de compra
    COUNT(DISTINCT po.po_id) as total_purchase_orders,
    COUNT(DISTINCT CASE WHEN po.status = 'RECEIVED' THEN po.po_id END) as completed_orders,
    COUNT(DISTINCT CASE WHEN po.status = 'PENDING' THEN po.po_id END) as pending_orders,
    COUNT(DISTINCT CASE WHEN po.status = 'PARTIAL' THEN po.po_id END) as partial_orders,
    -- Volumen de compras
    SUM(po.total_amount) as total_purchase_amount,
    AVG(po.total_amount) as avg_order_amount,
    -- Tiempos de entrega
    AVG(EXTRACT(DAY FROM po.actual_delivery_date - po.order_date)) as actual_delivery_days,
    AVG(EXTRACT(DAY FROM po.actual_delivery_date - po.expected_delivery_date)) as delivery_variance,
    -- Calidad de entrega
    SUM(pi.quantity_rejected) as total_rejected_quantity,
    ROUND(SUM(pi.quantity_rejected) / NULLIF(SUM(pi.quantity), 0) * 100, 2) as rejection_rate_percent,
    -- Última orden
    MAX(po.order_date) as last_order_date,
    -- Productos más comprados
    (SELECT pm.name FROM inv.po_items pi2
     JOIN inv.product_master pm ON pi2.internal_sku = pm.internal_sku
     JOIN inv.purchase_orders po2 ON pi2.po_id = po2.po_id
     WHERE po2.supplier_id = s.supplier_id
     GROUP BY pm.name
     ORDER BY SUM(pi2.quantity) DESC
     LIMIT 1) as most_purchased_product
FROM cat.suppliers s
LEFT JOIN inv.purchase_orders po ON s.supplier_id = po.supplier_id
LEFT JOIN inv.po_items pi ON po.po_id = pi.po_id
GROUP BY s.supplier_id, s.supplier_code, s.name, s.contact_person, s.rating, 
         s.quality_score, s.delivery_time_avg, s.is_preferred, s.status
ORDER BY total_purchase_amount DESC, rating DESC;

-- Vista para necesidades de reorden
CREATE VIEW kpi.reorder_needs AS
SELECT 
    s.internal_sku,
    pm.name as product_name,
    pm.brand,
    tg.name_es as group_name,
    pm.reorder_point,
    pm.min_stock,
    pm.max_stock,
    pm.lead_time_days,
    SUM(s.qty_available) as total_available,
    SUM(s.qty_on_order) as total_on_order,
    SUM(s.qty_reserved) as total_reserved,
    pm.min_stock - SUM(s.qty_available) as deficit,
    -- Necesidad de reorden
    CASE 
        WHEN SUM(s.qty_available) <= pm.reorder_point THEN 'REORDEN URGENTE'
        WHEN SUM(s.qty_available) <= pm.min_stock THEN 'REORDEN INMEDIATA'
        WHEN SUM(s.qty_available) <= pm.reorder_point * 1.5 THEN 'EVALUAR REORDEN'
        ELSE 'STOCK SUFICIENTE'
    END as reorder_status,
    -- Cantidad sugerida
    CASE 
        WHEN SUM(s.qty_available) <= pm.reorder_point THEN pm.max_stock - SUM(s.qty_available)
        ELSE 0
    END as suggested_order_qty,
    -- Última compra
    (SELECT MAX(txn_date) FROM inv.transactions t 
     WHERE t.internal_sku = s.internal_sku AND t.txn_type = 'IN') as last_purchase_date,
    -- Proveedor principal
    (SELECT s2.name FROM inv.product_master pm2
     LEFT JOIN cat.suppliers s2 ON pm2.internal_sku = s.internal_sku
     WHERE pm2.internal_sku = s.internal_sku) as primary_supplier,
    -- Costo
    pm.last_purchase_cost,
    pm.avg_cost
FROM inv.stock s
JOIN inv.product_master pm ON s.internal_sku = pm.internal_sku
LEFT JOIN cat.taxonomy_groups tg ON pm.group_code = tg.group_code
WHERE pm.is_active = TRUE
GROUP BY s.internal_sku, pm.name, pm.brand, tg.name_es, pm.reorder_point, 
         pm.min_stock, pm.max_stock, pm.lead_time_days, pm.last_purchase_cost, pm.avg_cost
HAVING SUM(s.qty_available) <= pm.reorder_point * 1.5
ORDER BY deficit DESC, total_available ASC;

-- =====================================================
-- 7. VISTAS DE MÉTRICAS Y KPI GLOBALES
-- =====================================================

-- Vista para dashboard ejecutivo
CREATE VIEW kpi.executive_dashboard AS
WITH monthly_stats AS (
    SELECT 
        DATE_TRUNC('month', wo.delivery_date) as month,
        COUNT(DISTINCT wo.wo_id) as total_orders,
        COUNT(DISTINCT wo.client_id) as unique_clients,
        SUM(wo.total_cost) as total_revenue,
        SUM(wo.labor_cost) as labor_revenue,
        SUM(wo.parts_cost) as parts_revenue,
        AVG(wo.efficiency_rate) as avg_efficiency,
        COUNT(DISTINCT wo.technician_id) as active_technicians,
        AVG(EXTRACT(DAY FROM wo.delivery_date - wo.reception_date)) as avg_cycle_time
    FROM svc.work_orders wo
    WHERE wo.delivery_date >= CURRENT_DATE - INTERVAL '6 months'
    AND wo.status = 'CERRADO'
    GROUP BY DATE_TRUNC('month', wo.delivery_date)
),
inventory_stats AS (
    SELECT 
        SUM(s.total_cost) as total_inventory_value,
        COUNT(DISTINCT s.internal_sku) as active_skus,
        COUNT(DISTINCT CASE WHEN s.qty_available <= pm.reorder_point THEN s.internal_sku END) as low_stock_skus,
        ROUND(SUM(s.total_cost) / NULLIF(SUM(pm.max_stock * pm.avg_cost), 0) * 100, 2) as inventory_utilization
    FROM inv.stock s
    JOIN inv.product_master pm ON s.internal_sku = pm.internal_sku
    WHERE pm.is_active = TRUE
),
financial_stats AS (
    SELECT 
        SUM(CASE WHEN i.status = 'PAID' THEN i.total_amount ELSE 0 END) as revenue_paid,
        SUM(CASE WHEN i.status IN ('SENT', 'OVERDUE') THEN i.total_amount ELSE 0 END) as revenue_pending,
        COUNT(DISTINCT CASE WHEN i.status = 'OVERDUE' THEN i.client_id END) as clients_overdue,
        AVG(CASE WHEN i.status = 'PAID' THEN EXTRACT(DAY FROM i.paid_date - i.issue_date) END) as avg_collection_days
    FROM svc.invoices i
    WHERE i.issue_date >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    -- Órdenes de trabajo
    (SELECT COUNT(*) FROM svc.work_orders WHERE status NOT IN ('CERRADO', 'CANCELLED')) as active_work_orders,
    (SELECT COUNT(*) FROM svc.work_orders WHERE status = 'EN_PROCESO') as in_progress_orders,
    (SELECT COUNT(*) FROM svc.work_orders WHERE priority = 'URGENTE' AND status NOT IN ('CERRADO', 'CANCELLED')) as urgent_orders,
    
    -- Clientes
    (SELECT COUNT(*) FROM cat.clients WHERE status = 'ACTIVE') as active_clients,
    (SELECT COUNT(DISTINCT client_id) FROM svc.work_orders WHERE delivery_date >= CURRENT_DATE - INTERVAL '30 days') as recent_clients,
    
    -- Inventario
    inv_stats.total_inventory_value,
    inv_stats.active_skus,
    inv_stats.low_stock_skus,
    inv_stats.inventory_utilization,
    
    -- Finanzas
    fin_stats.revenue_paid,
    fin_stats.revenue_pending,
    fin_stats.clients_overdue,
    fin_stats.avg_collection_days,
    
    -- Técnicos
    (SELECT COUNT(*) FROM cat.technicians WHERE status = 'ACTIVE' AND is_active = TRUE) as active_technicians,
    (SELECT COUNT(*) FROM cat.technicians WHERE status = 'EN_PROCESO' AND is_active = TRUE) as busy_technicians,
    
    -- Métricas del mes actual
    curr_month.total_orders as current_month_orders,
    curr_month.total_revenue as current_month_revenue,
    curr_month.avg_efficiency as current_month_efficiency,
    curr_month.avg_cycle_time as current_month_cycle_time,
    
    -- Comparación con mes anterior
    ROUND((curr_month.total_orders - prev_month.total_orders) / NULLIF(prev_month.total_orders, 0) * 100, 2) as order_growth_percent,
    ROUND((curr_month.total_revenue - prev_month.total_revenue) / NULLIF(prev_month.total_revenue, 0) * 100, 2) as revenue_growth_percent
    
FROM monthly_stats curr_month
LEFT JOIN monthly_stats prev_month ON curr_month.month = prev_month.month + INTERVAL '1 month'
CROSS JOIN inventory_stats inv_stats
CROSS JOIN financial_stats fin_stats
WHERE curr_month.month = DATE_TRUNC('month', CURRENT_DATE)
ORDER BY curr_month.month DESC
LIMIT 1;

-- =====================================================
-- 8. MATERIALIZED VIEWS PARA PERFORMANCE
-- =====================================================

-- Materialized View para análisis ABC (mejorado de segunda versión)
CREATE MATERIALIZED VIEW kpi.inventory_abc_analysis AS
WITH inventory_stats AS (
    SELECT 
        pm.internal_sku, 
        pm.name, 
        pm.group_code,
        tg.name_es as group_name,
        pm.brand,
        SUM(s.qty_on_hand * COALESCE(s.unit_cost, pm.standard_cost)) as total_value,
        SUM(s.qty_on_hand) as total_qty,
        COUNT(DISTINCT t.txn_id) as transaction_count,
        SUM(CASE WHEN t.txn_type = 'OUT' THEN ABS(t.qty) ELSE 0 END) as out_qty,
        AVG(CASE WHEN t.txn_type = 'IN' THEN t.unit_cost ELSE NULL END) as avg_purchase_cost,
        MIN(t.txn_date) as first_transaction_date,
        MAX(t.txn_date) as last_transaction_date,
        EXTRACT(DAY FROM CURRENT_DATE - MAX(t.txn_date)) as days_since_last_movement
    FROM inv.product_master pm
    LEFT JOIN inv.stock s ON pm.internal_sku = s.internal_sku
    LEFT JOIN inv.transactions t ON pm.internal_sku = t.internal_sku 
        AND t.txn_date >= CURRENT_DATE - INTERVAL '1 year'
    LEFT JOIN cat.taxonomy_groups tg ON pm.group_code = tg.group_code
    WHERE pm.is_active = TRUE
    GROUP BY pm.internal_sku, pm.name, pm.group_code, tg.name_es, pm.brand
),
with_ranks AS (
    SELECT 
        *,
        SUM(total_value) OVER (ORDER BY total_value DESC NULLS LAST) / 
        NULLIF(SUM(total_value) OVER (), 0) as cumulative_value_pct,
        SUM(out_qty) OVER (ORDER BY out_qty DESC NULLS LAST) / 
        NULLIF(SUM(out_qty) OVER (), 0) as cumulative_movement_pct,
        SUM(transaction_count) OVER (ORDER BY transaction_count DESC NULLS LAST) / 
        NULLIF(SUM(transaction_count) OVER (), 0) as cumulative_frequency_pct
    FROM inventory_stats
)
SELECT 
    *,
    CASE 
        WHEN cumulative_value_pct <= 0.7 THEN 'A' 
        WHEN cumulative_value_pct <= 0.9 THEN 'B' 
        ELSE 'C' 
    END as abc_class_value,
    CASE 
        WHEN cumulative_movement_pct <= 0.8 THEN 'A' 
        WHEN cumulative_movement_pct <= 0.95 THEN 'B' 
        ELSE 'C' 
    END as abc_class_movement,
    CASE 
        WHEN cumulative_frequency_pct <= 0.8 THEN 'A' 
        WHEN cumulative_frequency_pct <= 0.95 THEN 'B' 
        ELSE 'C' 
    END as abc_class_frequency,
    -- Recomendaciones basadas en clasificación
    CASE 
        WHEN cumulative_value_pct <= 0.7 AND cumulative_movement_pct <= 0.8 THEN 'ALTA PRIORIDAD - CONTROL ESTRICTO'
        WHEN cumulative_value_pct <= 0.7 AND cumulative_movement_pct > 0.8 THEN 'ALTO VALOR - BAJA ROTACIÓN - REVISAR'
        WHEN cumulative_value_pct > 0.9 AND cumulative_movement_pct <= 0.8 THEN 'BAJO VALOR - ALTA ROTACIÓN - MANTENER'
        WHEN cumulative_value_pct > 0.9 AND cumulative_movement_pct > 0.8 THEN 'BAJA PRIORIDAD - REVISAR NECESIDAD'
        ELSE 'PRIORIDAD MEDIA'
    END as recommendation
FROM with_ranks
ORDER BY total_value DESC;

-- Materialized View para tendencias mensuales
CREATE MATERIALIZED VIEW kpi.monthly_trends AS
SELECT 
    DATE_TRUNC('month', wo.delivery_date) as month,
    EXTRACT(YEAR FROM wo.delivery_date) as year,
    EXTRACT(MONTH FROM wo.delivery_date) as month_number,
    -- Estadísticas de órdenes
    COUNT(DISTINCT wo.wo_id) as total_orders,
    COUNT(DISTINCT wo.client_id) as unique_clients,
    COUNT(DISTINCT wo.technician_id) as active_technicians,
    -- Ingresos
    SUM(wo.total_cost) as total_revenue,
    SUM(wo.labor_cost) as labor_revenue,
    SUM(wo.parts_cost) as parts_revenue,
    SUM(wo.additional_costs) as additional_revenue,
    -- Métricas de eficiencia
    AVG(wo.efficiency_rate) as avg_efficiency,
    AVG(wo.actual_hours) as avg_hours_per_order,
    AVG(EXTRACT(DAY FROM wo.delivery_date - wo.reception_date)) as avg_cycle_days,
    -- Métricas de calidad
    AVG(km.quality_score) as avg_quality_score,
    AVG(km.customer_satisfaction) as avg_customer_satisfaction,
    -- Inventario relacionado
    SUM(CASE WHEN wi.status = 'USED' THEN wi.qty_used * wi.unit_price ELSE 0 END) as parts_usage_cost,
    COUNT(DISTINCT wi.internal_sku) as unique_parts_used
FROM svc.work_orders wo
LEFT JOIN svc.wo_items wi ON wo.wo_id = wi.wo_id
LEFT JOIN kpi.wo_metrics km ON wo.wo_id = km.wo_id
WHERE wo.delivery_date IS NOT NULL
AND wo.status = 'CERRADO'
GROUP BY DATE_TRUNC('month', wo.delivery_date), EXTRACT(YEAR FROM wo.delivery_date), EXTRACT(MONTH FROM wo.delivery_date)
ORDER BY month DESC;

-- =====================================================
-- 9. ÍNDICES PARA VISTAS (si se materializan)
-- =====================================================

-- Índices para las vistas materializadas
CREATE INDEX idx_inventory_abc_sku ON kpi.inventory_abc_analysis(internal_sku);
CREATE INDEX idx_inventory_abc_value ON kpi.inventory_abc_analysis(total_value DESC);
CREATE INDEX idx_inventory_abc_class ON kpi.inventory_abc_analysis(abc_class_value, abc_class_movement);

CREATE INDEX idx_monthly_trends_month ON kpi.monthly_trends(month DESC);
CREATE INDEX idx_monthly_trends_year ON kpi.monthly_trends(year, month_number);

-- =====================================================
-- 10. FUNCIONES PARA REFRESCAR VISTAS MATERIALIZADAS
-- =====================================================

CREATE OR REPLACE FUNCTION kpi.refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY kpi.inventory_abc_analysis;
    REFRESH MATERIALIZED VIEW CONCURRENTLY kpi.monthly_trends;
    
    RAISE NOTICE 'Vistas materializadas refrescadas exitosamente';
END;
$$ LANGUAGE plpgsql;

-- Función para refrescar vista materializada específica
CREATE OR REPLACE FUNCTION kpi.refresh_materialized_view(view_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY kpi.%I', view_name);
    RAISE NOTICE 'Vista materializada % refrescada', view_name;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al refrescar vista %: %', view_name, SQLERRM;
END;
$$ LANGUAGE plpgsql;