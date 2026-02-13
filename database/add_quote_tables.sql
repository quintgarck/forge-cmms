-- Migración para Sistema de Cotizaciones
-- Tarea 6: Sistema de Cotizaciones

BEGIN;

-- =============================================================================
-- Tabla: svc.quotes
-- Propósito: Almacenar cotizaciones/presupuestos de servicios
-- =============================================================================

CREATE TABLE IF NOT EXISTS svc.quotes (
    quote_id SERIAL PRIMARY KEY,
    quote_number VARCHAR(20) UNIQUE NOT NULL,
    client_id INT NOT NULL REFERENCES cat.clients(client_id) ON DELETE CASCADE,
    equipment_id INT REFERENCES cat.equipment(equipment_id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'SENT', 'APPROVED', 'REJECTED', 'EXPIRED', 'CONVERTED')),
    quote_date DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    subtotal DECIMAL(12, 2) DEFAULT 0.00 CHECK (subtotal >= 0),
    discount_percent DECIMAL(5, 2) DEFAULT 0.00 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    discount_amount DECIMAL(12, 2) DEFAULT 0.00 CHECK (discount_amount >= 0),
    tax_percent DECIMAL(5, 2) DEFAULT 16.00 CHECK (tax_percent >= 0),
    tax_amount DECIMAL(12, 2) DEFAULT 0.00 CHECK (tax_amount >= 0),
    total DECIMAL(12, 2) DEFAULT 0.00 CHECK (total >= 0),
    total_hours DECIMAL(6, 2) DEFAULT 0.00 CHECK (total_hours >= 0),
    currency_code VARCHAR(3) DEFAULT 'MXN',
    notes TEXT,
    terms_and_conditions TEXT,
    created_by INT REFERENCES auth_user(id) ON DELETE SET NULL,
    converted_to_wo_id INT REFERENCES svc.work_orders(wo_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_quote_dates CHECK (valid_until IS NULL OR valid_until >= quote_date)
);

CREATE INDEX idx_quotes_quote_number ON svc.quotes(quote_number);
CREATE INDEX idx_quotes_client_status ON svc.quotes(client_id, status);
CREATE INDEX idx_quotes_date_status ON svc.quotes(quote_date, status);
CREATE INDEX idx_quotes_equipment ON svc.quotes(equipment_id) WHERE equipment_id IS NOT NULL;

-- =============================================================================
-- Tabla: svc.quote_items
-- Propósito: Almacenar líneas de items de cotización (servicios)
-- =============================================================================

CREATE TABLE IF NOT EXISTS svc.quote_items (
    quote_item_id SERIAL PRIMARY KEY,
    quote_id INT NOT NULL REFERENCES svc.quotes(quote_id) ON DELETE CASCADE,
    flat_rate_id INT REFERENCES svc.flat_rate_standards(flat_rate_id) ON DELETE SET NULL,
    service_code VARCHAR(20),
    description TEXT NOT NULL,
    quantity INT DEFAULT 1 CHECK (quantity > 0),
    hours DECIMAL(5, 2) DEFAULT 0.00 CHECK (hours >= 0),
    hourly_rate DECIMAL(10, 2) DEFAULT 500.00 CHECK (hourly_rate >= 0),
    line_total DECIMAL(12, 2) DEFAULT 0.00 CHECK (line_total >= 0),
    notes TEXT
);

CREATE INDEX idx_quote_items_quote ON svc.quote_items(quote_id);
CREATE INDEX idx_quote_items_flat_rate ON svc.quote_items(flat_rate_id) WHERE flat_rate_id IS NOT NULL;

-- =============================================================================
-- Trigger para calcular line_total automáticamente
-- =============================================================================

CREATE OR REPLACE FUNCTION svc.calculate_quote_item_total()
RETURNS TRIGGER AS $$
BEGIN
    NEW.line_total = NEW.hours * NEW.hourly_rate * NEW.quantity;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_calculate_quote_item_total ON svc.quote_items;
CREATE TRIGGER trigger_calculate_quote_item_total
    BEFORE INSERT OR UPDATE ON svc.quote_items
    FOR EACH ROW
    EXECUTE FUNCTION svc.calculate_quote_item_total();

-- =============================================================================
-- Trigger para actualizar updated_at en quotes
-- =============================================================================

CREATE OR REPLACE FUNCTION svc.update_quotes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_quotes_updated_at ON svc.quotes;
CREATE TRIGGER trigger_update_quotes_updated_at
    BEFORE UPDATE ON svc.quotes
    FOR EACH ROW
    EXECUTE FUNCTION svc.update_quotes_updated_at();

-- =============================================================================
-- Comentarios
-- =============================================================================

COMMENT ON TABLE svc.quotes IS 'Cotizaciones/presupuestos de servicios para clientes';
COMMENT ON TABLE svc.quote_items IS 'Líneas de items de cotización (servicios individuales)';
COMMENT ON COLUMN svc.quotes.converted_to_wo_id IS 'Referencia a la orden de trabajo creada a partir de esta cotización';
COMMENT ON COLUMN svc.quote_items.line_total IS 'Total calculado automáticamente: hours * hourly_rate * quantity';

COMMIT;
