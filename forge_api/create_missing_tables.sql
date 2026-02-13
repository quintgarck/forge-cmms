-- Script para crear las tablas faltantes en el esquema svc
-- Específicamente la tabla quotes y quote_items que están causando problemas en las migraciones

-- Crear tabla quotes
CREATE TABLE IF NOT EXISTS svc.quotes (
    quote_id SERIAL PRIMARY KEY,
    quote_number VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    quote_date DATE NOT NULL DEFAULT CURRENT_DATE,
    valid_until DATE,
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    discount_percent NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    tax_percent NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_hours NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    currency_code VARCHAR(3) NOT NULL DEFAULT 'USD',
    notes TEXT,
    terms_and_conditions TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    client_id INTEGER NOT NULL,
    converted_to_wo_id INTEGER,
    created_by_id INTEGER,
    equipment_id INTEGER,
    
    -- Foreign key constraints
    CONSTRAINT fk_quotes_client FOREIGN KEY (client_id) REFERENCES cat.clients(client_id),
    CONSTRAINT fk_quotes_equipment FOREIGN KEY (equipment_id) REFERENCES cat.equipment(equipment_id),
    CONSTRAINT fk_quotes_created_by FOREIGN KEY (created_by_id) REFERENCES cat.technicians(technician_id),
    CONSTRAINT fk_quotes_converted_wo FOREIGN KEY (converted_to_wo_id) REFERENCES svc.work_orders(wo_id)
);

-- Crear tabla quote_items
CREATE TABLE IF NOT EXISTS svc.quote_items (
    quote_item_id SERIAL PRIMARY KEY,
    service_code VARCHAR(20),
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    hours NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    hourly_rate NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    line_total NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    notes TEXT,
    flat_rate_id INTEGER,
    quote_id INTEGER NOT NULL,
    
    -- Foreign key constraints
    CONSTRAINT fk_quote_items_quote FOREIGN KEY (quote_id) REFERENCES svc.quotes(quote_id) ON DELETE CASCADE,
    CONSTRAINT fk_quote_items_flat_rate FOREIGN KEY (flat_rate_id) REFERENCES svc.flat_rate_standards(flat_rate_id)
);

-- Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_quotes_quote_number ON svc.quotes(quote_number);
CREATE INDEX IF NOT EXISTS idx_quotes_client_status ON svc.quotes(client_id, status);
CREATE INDEX IF NOT EXISTS idx_quotes_quote_date ON svc.quotes(quote_date, status);
CREATE INDEX IF NOT EXISTS idx_quote_items_quote_id ON svc.quote_items(quote_id);

-- Insertar algunos datos de ejemplo (opcional)
INSERT INTO svc.quotes (quote_number, status, quote_date, client_id, subtotal, total) VALUES
('QT-001', 'draft', CURRENT_DATE, 1, 1000.00, 1000.00),
('QT-002', 'sent', CURRENT_DATE - 1, 2, 1500.00, 1500.00)
ON CONFLICT (quote_number) DO NOTHING;

-- Verificar creación
SELECT 'Tabla quotes creada exitosamente' as resultado
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'svc' AND table_name = 'quotes');

SELECT 'Tabla quote_items creada exitosamente' as resultado
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'svc' AND table_name = 'quote_items');