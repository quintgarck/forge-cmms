-- =============================================================================
-- Script SEGURO de Limpieza de Tablas Duplicadas (Solo Consultas, Sin Eliminar)
-- =============================================================================
-- 
-- Este script SOLO VERIFICA y LISTA las tablas duplicadas.
-- NO ELIMINA NADA. Úsalo primero para ver qué se eliminará.
--
-- =============================================================================

-- Listar todas las tablas en el esquema 'app'
SELECT 
    'Tablas en esquema app' as categoria,
    tablename as nombre_tabla,
    CASE 
        WHEN tablename LIKE '%.%' THEN 'PROBLEMA: Nombre incluye punto'
        WHEN tablename IN ('cat.clients', 'cat.equipment', 'cat.technicians',
                          'inv.warehouses', 'inv.stock', 'inv.transactions', 
                          'inv.product_master', 'svc.work_orders', 'svc.invoices',
                          'doc.documents') THEN 'PROBLEMA: Tabla de otro esquema'
        WHEN tablename IN ('alerts', 'audit_logs', 'business_rules') THEN 'OK: Debe estar en app'
        WHEN tablename LIKE 'auth_%' OR tablename LIKE 'django_%' THEN 'OK: Tabla de Django'
        ELSE 'REVISAR'
    END as estado
FROM pg_tables 
WHERE schemaname = 'app'
ORDER BY estado, tablename;

-- Verificar que las tablas correctas existen en sus esquemas
SELECT 
    'Verificacion de tablas correctas' as categoria,
    schemaname || '.' || tablename as tabla,
    'EXISTE' as estado
FROM pg_tables 
WHERE (schemaname, tablename) IN (
    ('cat', 'clients'),
    ('cat', 'technicians'),
    ('cat', 'equipment'),
    ('inv', 'warehouses'),
    ('inv', 'stock'),
    ('inv', 'transactions'),
    ('inv', 'product_master'),
    ('svc', 'work_orders'),
    ('svc', 'invoices'),
    ('doc', 'documents'),
    ('app', 'alerts'),
    ('app', 'audit_logs'),
    ('app', 'business_rules')
)
ORDER BY schemaname, tablename;

-- Mostrar las tablas que serían eliminadas (SOLO PARA REFERENCIA)
SELECT 
    'Tablas que serian eliminadas' as categoria,
    'app.' || tablename as tabla_duplicada,
    CASE 
        WHEN tablename LIKE 'app.%' THEN 'Duplicado de app.' || REPLACE(tablename, 'app.', '')
        WHEN tablename LIKE 'cat.%' THEN 'Duplicado de ' || tablename
        WHEN tablename LIKE 'inv.%' THEN 'Duplicado de ' || tablename
        WHEN tablename LIKE 'svc.%' THEN 'Duplicado de ' || tablename
        WHEN tablename LIKE 'doc.%' THEN 'Duplicado de ' || tablename
        ELSE 'Revisar manualmente'
    END as tabla_correcta
FROM pg_tables 
WHERE schemaname = 'app'
AND (
    tablename LIKE '%.%' OR
    tablename IN ('cat.clients', 'cat.equipment', 'cat.technicians',
                 'inv.warehouses', 'inv.stock', 'inv.transactions', 
                 'inv.product_master', 'svc.work_orders', 'svc.invoices',
                 'doc.documents')
)
ORDER BY tablename;

