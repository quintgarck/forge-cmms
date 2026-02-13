-- =============================================================================
-- Script de Limpieza de Tablas Duplicadas en esquema 'app'
-- =============================================================================
-- 
-- PROBLEMA:
-- Django creó tablas duplicadas en el esquema 'app' con nombres incorrectos
-- porque interpretó db_table='cat.clients' como nombre literal de tabla,
-- no como schema.table.
--
-- ESTADO:
-- Las tablas CORRECTAS ya existen en sus esquemas correctos:
--   - cat.clients, cat.technicians, cat.equipment
--   - inv.warehouses, inv.stock, inv.transactions, inv.product_master
--   - svc.work_orders, svc.invoices
--   - doc.documents
--   - app.alerts, app.audit_logs, app.business_rules (estas SÍ deben estar en app)
--
-- OBJETIVO:
-- Eliminar las tablas duplicadas con nombres incorrectos del esquema 'app'
--
-- PRECAUCIÓN:
-- Este script elimina tablas. Asegúrate de:
-- 1. Hacer backup de la base de datos antes de ejecutar
-- 2. Verificar que las tablas correctas existan y tengan los datos
-- 3. Ejecutar en un entorno de desarrollo primero
--
-- =============================================================================

BEGIN;

-- Verificar que estamos en la base de datos correcta
DO $$
BEGIN
    IF current_database() != 'forge_db' THEN
        RAISE EXCEPTION 'Este script debe ejecutarse en la base de datos forge_db. Base de datos actual: %', current_database();
    END IF;
END $$;

-- =============================================================================
-- PASO 1: Verificar que las tablas correctas existen
-- =============================================================================

DO $$
DECLARE
    missing_tables TEXT[];
    table_name TEXT;
BEGIN
    missing_tables := ARRAY[]::TEXT[];
    
    -- Lista de tablas que DEBEN existir en sus esquemas correctos
    FOR table_name IN 
        SELECT unnest(ARRAY[
            'cat.clients',
            'cat.technicians', 
            'cat.equipment',
            'inv.warehouses',
            'inv.stock',
            'inv.transactions',
            'inv.product_master',
            'svc.work_orders',
            'svc.invoices',
            'doc.documents',
            'app.alerts',
            'app.audit_logs',
            'app.business_rules'
        ])
    LOOP
        IF NOT EXISTS (
            SELECT 1 
            FROM pg_tables 
            WHERE schemaname = split_part(table_name, '.', 1)
            AND tablename = split_part(table_name, '.', 2)
        ) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Las siguientes tablas correctas NO existen: %. Verifica antes de continuar.', array_to_string(missing_tables, ', ');
    END IF;
    
    RAISE NOTICE 'Verificacion completada: Todas las tablas correctas existen.';
END $$;

-- =============================================================================
-- PASO 2: Eliminar tablas duplicadas del esquema 'app'
-- =============================================================================

-- Tablas con nombres que incluyen esquema (incorrectas en app)
DROP TABLE IF EXISTS app."app.alerts" CASCADE;
DROP TABLE IF EXISTS app."app.audit_logs" CASCADE;
DROP TABLE IF EXISTS app."app.business_rules" CASCADE;

-- Tablas de otros esquemas que están duplicadas en app
DROP TABLE IF EXISTS app."cat.clients" CASCADE;
DROP TABLE IF EXISTS app."cat.equipment" CASCADE;
DROP TABLE IF EXISTS app."cat.technicians" CASCADE;
DROP TABLE IF EXISTS app."doc.documents" CASCADE;
DROP TABLE IF EXISTS app."inv.product_master" CASCADE;
DROP TABLE IF EXISTS app."inv.stock" CASCADE;
DROP TABLE IF EXISTS app."inv.transactions" CASCADE;
DROP TABLE IF EXISTS app."inv.warehouses" CASCADE;
DROP TABLE IF EXISTS app."svc.invoices" CASCADE;
DROP TABLE IF EXISTS app."svc.work_orders" CASCADE;

-- =============================================================================
-- PASO 3: Verificar que las tablas duplicadas fueron eliminadas
-- =============================================================================

DO $$
DECLARE
    remaining_tables TEXT[];
    table_record RECORD;
BEGIN
    remaining_tables := ARRAY[]::TEXT[];
    
    -- Verificar si quedan tablas problemáticas en app
    FOR table_record IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'app'
        AND (
            tablename LIKE '%.%' OR
            tablename IN ('cat.clients', 'cat.equipment', 'cat.technicians',
                         'inv.warehouses', 'inv.stock', 'inv.transactions', 
                         'inv.product_master', 'svc.work_orders', 'svc.invoices',
                         'doc.documents')
        )
    LOOP
        remaining_tables := array_append(remaining_tables, table_record.tablename);
    END LOOP;
    
    IF array_length(remaining_tables, 1) > 0 THEN
        RAISE WARNING 'Aun quedan tablas problematicas en app: %', array_to_string(remaining_tables, ', ');
    ELSE
        RAISE NOTICE 'Limpieza completada: No quedan tablas duplicadas en app.';
    END IF;
END $$;

-- =============================================================================
-- PASO 4: Listar tablas finales en esquema 'app' (solo para referencia)
-- =============================================================================

DO $$
DECLARE
    table_record RECORD;
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables 
    WHERE schemaname = 'app';
    
    RAISE NOTICE 'Total de tablas en esquema app: %', table_count;
    RAISE NOTICE 'Tablas en app (solo para referencia):';
    
    FOR table_record IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'app'
        ORDER BY tablename
    LOOP
        RAISE NOTICE '  - %', table_record.tablename;
    END LOOP;
END $$;

-- =============================================================================
-- FINALIZACIÓN
-- =============================================================================

-- Si llegamos aquí sin errores, confirmar la transacción
COMMIT;

-- Mensaje final
DO $$
BEGIN
    RAISE NOTICE 'Script completado exitosamente. Las tablas duplicadas han sido eliminadas.';
END $$;

