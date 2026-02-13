-- ============================================================================
-- ÍNDICES DE OPTIMIZACIÓN PARA TAXONOMÍA
-- MovIAx - Forge CMMS
-- Fecha: 31 de Enero 2026
-- ============================================================================
-- 
-- ESTE SCRIPT CREA ÍNDICES NECESARIOS PARA MEJORAR EL PERFORMANCE
-- DEL CRUD DE TAXONOMÍA (Systems, Subsystems, Groups)
--
-- Tiempos de respuesta objetivo:
-- - Listado: < 200ms
-- - Búsqueda: < 300ms
-- - Detalle: < 100ms
--
-- ============================================================================

-- ============================================================================
-- ÍNDICES PARA TAXONOMY_SYSTEMS
-- ============================================================================

-- Índice para búsquedas por nombre (usando trigram para búsqueda parcial)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_systems_name_trgm 
    ON cat.taxonomy_systems USING gin (name_es gin_trgm_ops);

-- Índice para filtrar por estado activo (muy usado en listados)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_systems_is_active 
    ON cat.taxonomy_systems (is_active) 
    WHERE is_active = true;

-- Índice compuesto para ordenamiento (sort_order + system_code)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_systems_sort_order 
    ON cat.taxonomy_systems (sort_order ASC, system_code ASC);

-- Índice para búsqueda por categoría + estado
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_systems_category_active 
    ON cat.taxonomy_systems (category, is_active, sort_order);

-- Índice para búsquedas generales (código y nombre)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_systems_code_name 
    ON cat.taxonomy_systems (system_code, name_es);

COMMENT ON INDEX cat.idx_taxonomy_systems_name_trgm IS 
    'Optimiza búsquedas de texto parcial en nombre_es';
COMMENT ON INDEX cat.idx_taxonomy_systems_is_active IS 
    'Optimiza filtrado de sistemas activos (partial index)';
COMMENT ON INDEX cat.idx_taxonomy_systems_sort_order IS 
    'Optimiza ordenamiento por sort_order y system_code';

-- ============================================================================
-- ÍNDICES PARA TAXONOMY_SUBSYSTEMS
-- ============================================================================

-- Índice para relación con system (ya existe pero verificamos)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_subsystems_system 
    ON cat.taxonomy_subsystems (system_code);

-- Índice para búsquedas por nombre
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_subsystems_name_trgm 
    ON cat.taxonomy_subsystems USING gin (name_es gin_trgm_ops);

-- Índice compuesto para ordenamiento (system + sort_order + subsystem_code)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_subsystems_order 
    ON cat.taxonomy_subsystems (system_code ASC, sort_order ASC, subsystem_code ASC);

-- Índice para conteo de subsystems por system (usado en stats)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_subsystems_count 
    ON cat.taxonomy_subsystems (system_code) 
    INCLUDE (subsystem_code);

COMMENT ON INDEX cat.idx_taxonomy_subsystems_system IS 
    'Optimiza JOIN con taxonomy_systems';
COMMENT ON INDEX cat.idx_taxonomy_subsystems_order IS 
    'Optimiza ordenamiento jerárquico';

-- ============================================================================
-- ÍNDICES PARA TAXONOMY_GROUPS
-- ============================================================================

-- Índice para relación con subsystem (ya existe en modelo Django)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_groups_subsystem 
--     ON cat.taxonomy_groups (subsystem_code);

-- Índice para relación con system
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_groups_system 
    ON cat.taxonomy_groups (system_code);

-- Índice para búsquedas por nombre
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_groups_name_trgm 
    ON cat.taxonomy_groups USING gin (name_es gin_trgm_ops);

-- Índice para búsquedas por descripción
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_groups_description_trgm 
    ON cat.taxonomy_groups USING gin (description gin_trgm_ops);

-- Índice compuesto para ordenamiento
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_groups_order 
    ON cat.taxonomy_groups (system_code ASC, subsystem_code ASC, name_es ASC);

-- Índice para filtrado por flags de negocio
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_groups_requirements 
    ON cat.taxonomy_groups (requires_position, requires_color, requires_finish, requires_side) 
    WHERE requires_position = true OR requires_color = true OR requires_finish = true OR requires_side = true;

-- Índice para estado activo + ordenamiento
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_taxonomy_groups_active_order 
    ON cat.taxonomy_groups (is_active, sort_order, name_es);

COMMENT ON INDEX cat.idx_taxonomy_groups_name_trgm IS 
    'Optimiza búsquedas por nombre de grupo';
COMMENT ON INDEX cat.idx_taxonomy_groups_order IS 
    'Optimiza ordenamiento jerárquico completo';

-- ============================================================================
-- OPTIMIZACIÓN DE SECUENCIAS (si aplica)
-- ============================================================================

-- Asegurar que las estadísticas estén actualizadas
ANALYZE cat.taxonomy_systems;
ANALYZE cat.taxonomy_subsystems;
ANALYZE cat.taxonomy_groups;

-- ============================================================================
-- VERIFICACIÓN DE ÍNDICES CREADOS
-- ============================================================================

-- Query para verificar índices creados
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'cat' 
    AND tablename LIKE 'taxonomy_%'
ORDER BY tablename, indexname;
*/

-- ============================================================================
-- INSTRUCCIONES DE USO
-- ============================================================================

/*
1. Ejecutar este script en la base de datos:
   psql -U postgres -d forge_db -f add_taxonomy_indexes.sql

2. O desde Django:
   python manage.py dbshell < database/add_taxonomy_indexes.sql

3. Verificar que los índices se crearon:
   \di cat.taxonomy_*

4. Medir mejora de performance:
   EXPLAIN ANALYZE SELECT * FROM cat.taxonomy_systems WHERE name_es LIKE '%engine%';
   
5. Si hay problemas de performance adicionales, revisar:
   - Query plan con EXPLAIN
   - Estadísticas de uso de índices
   - Fragmentación de tablas
*/

-- ============================================================================
-- ROLLBACK (en caso necesario)
-- ============================================================================

/*
Para eliminar índices si hay problemas:

DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_systems_name_trgm;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_systems_is_active;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_systems_sort_order;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_systems_category_active;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_systems_code_name;

DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_subsystems_system;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_subsystems_name_trgm;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_subsystems_order;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_subsystems_count;

DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_groups_system;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_groups_name_trgm;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_groups_description_trgm;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_groups_order;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_groups_requirements;
DROP INDEX CONCURRENTLY IF EXISTS cat.idx_taxonomy_groups_active_order;
*/

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================
