-- Migraciones para mejoras del sistema de alertas
-- Tarea 5.3: Persistencia, escalamiento e historial

BEGIN;

-- =============================================================================
-- Tabla: service_alert_thresholds
-- Propósito: Almacenar umbrales configurables para detección de alertas
-- =============================================================================

CREATE TABLE IF NOT EXISTS app.service_alert_thresholds (
    threshold_id SERIAL PRIMARY KEY,
    threshold_key VARCHAR(50) NOT NULL UNIQUE,
    threshold_name VARCHAR(100) NOT NULL,
    value DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20),
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by INT REFERENCES cat.technicians(technician_id),
    CONSTRAINT chk_positive_value CHECK (value > 0)
);

CREATE INDEX idx_service_alert_thresholds_key ON app.service_alert_thresholds(threshold_key, is_active);
CREATE INDEX idx_service_alert_thresholds_category ON app.service_alert_thresholds(category);

-- Insertar umbrales por defecto
INSERT INTO app.service_alert_thresholds (threshold_key, threshold_name, value, unit, category, description) VALUES
    ('max_delay_percentage', 'Porcentaje Máximo de Retraso', 20.00, '%', 'orders', 'Porcentaje sobre tiempo estimado para considerar retraso significativo'),
    ('max_orders_per_technician', 'Máximo de Órdenes por Técnico', 5.00, 'count', 'technicians', 'Número máximo de órdenes activas por técnico antes de generar alerta'),
    ('time_overrun_multiplier', 'Multiplicador de Tiempo para Servicios Anómalos', 2.00, 'multiplier', 'orders', 'Factor para considerar un servicio como anómalo (tiempo real vs estimado)'),
    ('low_stock_percentage', 'Porcentaje de Stock Bajo', 20.00, '%', 'inventory', 'Porcentaje del stock mínimo para considerar como "stock bajo"'),
    ('high_productivity_orders', 'Órdenes para Alta Productividad', 3.00, 'count', 'technicians', 'Número mínimo de órdenes completadas en un día para reconocimiento'),
    ('delayed_order_hours', 'Retraso Mínimo para Alerta', 2.00, 'hours', 'orders', 'Tiempo mínimo de retraso para generar una alerta'),
    ('escalation_time_hours', 'Tiempo de Escalamiento General', 24.00, 'hours', 'escalation', 'Tiempo transcurrido antes de escalar una alerta'),
    ('escalation_time_critical_hours', 'Tiempo de Escalamiento Crítico', 4.00, 'hours', 'escalation', 'Tiempo transcurrido antes de escalar una alerta crítica')
ON CONFLICT (threshold_key) DO NOTHING;

-- =============================================================================
-- Tabla: service_alert_escalations
-- Propósito: Registrar escalamientos de alertas cuando no se resuelven a tiempo
-- =============================================================================

CREATE TABLE IF NOT EXISTS app.service_alert_escalations (
    escalation_id SERIAL PRIMARY KEY,
    alert_id INT NOT NULL REFERENCES app.alerts(alert_id) ON DELETE CASCADE,
    original_severity VARCHAR(10) NOT NULL CHECK (original_severity IN ('low', 'medium', 'high', 'critical')),
    escalated_severity VARCHAR(10) NOT NULL CHECK (escalated_severity IN ('low', 'medium', 'high', 'critical')),
    escalation_level INT DEFAULT 1 CHECK (escalation_level > 0),
    escalated_at TIMESTAMP DEFAULT NOW(),
    escalated_by INT REFERENCES cat.technicians(technician_id),
    notes TEXT
);

CREATE INDEX idx_service_alert_escalations_alert ON app.service_alert_escalations(alert_id, escalated_at);
CREATE INDEX idx_service_alert_escalations_level ON app.service_alert_escalations(escalation_level);

-- =============================================================================
-- Actualizar tabla de alertas para incluir campo de escalamiento
-- (Si no existe ya)
-- =============================================================================

-- Verificar si la columna escalated ya existe, si no, agregarla
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'app' 
        AND table_name = 'alerts' 
        AND column_name = 'escalated'
    ) THEN
        ALTER TABLE app.alerts ADD COLUMN escalated BOOLEAN DEFAULT FALSE;
        ALTER TABLE app.alerts ADD COLUMN escalation_level INT DEFAULT 0;
        ALTER TABLE app.alerts ADD COLUMN original_severity VARCHAR(10);
        CREATE INDEX idx_alerts_escalated ON app.alerts(escalated, escalation_level);
    END IF;
END $$;

-- =============================================================================
-- Trigger para actualizar updated_at en service_alert_thresholds
-- =============================================================================

CREATE OR REPLACE FUNCTION app.update_service_alert_thresholds_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_service_alert_thresholds_updated_at ON app.service_alert_thresholds;
CREATE TRIGGER trigger_update_service_alert_thresholds_updated_at
    BEFORE UPDATE ON app.service_alert_thresholds
    FOR EACH ROW
    EXECUTE FUNCTION app.update_service_alert_thresholds_updated_at();

-- =============================================================================
-- Vista: service_alerts_history
-- Propósito: Vista para consultar historial de alertas con información de escalamiento
-- =============================================================================

CREATE OR REPLACE VIEW app.service_alerts_history AS
SELECT 
    a.alert_id,
    a.alert_type,
    a.ref_entity,
    a.ref_id,
    a.ref_code,
    a.title,
    a.message,
    a.details,
    a.severity,
    a.status,
    a.assigned_to,
    a.created_for,
    a.created_at,
    a.read_at,
    a.acknowledged_at,
    a.resolved_at,
    a.escalated,
    a.escalation_level,
    a.original_severity,
    CASE 
        WHEN a.resolved_at IS NOT NULL THEN EXTRACT(EPOCH FROM (a.resolved_at - a.created_at)) / 3600
        ELSE NULL
    END AS resolution_time_hours,
    CASE 
        WHEN a.read_at IS NOT NULL THEN EXTRACT(EPOCH FROM (a.read_at - a.created_at)) / 3600
        ELSE NULL
    END AS time_to_read_hours,
    (SELECT COUNT(*) FROM app.service_alert_escalations WHERE alert_id = a.alert_id) AS total_escalations
FROM app.alerts a;

COMMENT ON VIEW app.service_alerts_history IS 'Vista histórica de alertas con información de escalamiento y tiempos de resolución';

COMMIT;
