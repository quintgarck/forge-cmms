#!/usr/bin/env python
"""
Script para crear las tablas faltantes en la base de datos
"""

import os
import sys
import django

# Configurar el entorno Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')

django.setup()

from django.db import connection
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_missing_tables():
    """Crear las tablas faltantes en la base de datos"""
    
    sql_commands = [
        # Crear tabla quotes
        """
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
            equipment_id INTEGER
        )
        """,
        
        # Agregar constraints por separado para evitar problemas de orden
        "ALTER TABLE svc.quotes ADD CONSTRAINT fk_quotes_client FOREIGN KEY (client_id) REFERENCES cat.clients(client_id)",
        "ALTER TABLE svc.quotes ADD CONSTRAINT fk_quotes_equipment FOREIGN KEY (equipment_id) REFERENCES cat.equipment(equipment_id)",
        "ALTER TABLE svc.quotes ADD CONSTRAINT fk_quotes_created_by FOREIGN KEY (created_by_id) REFERENCES cat.technicians(technician_id)",
        "ALTER TABLE svc.quotes ADD CONSTRAINT fk_quotes_converted_wo FOREIGN KEY (converted_to_wo_id) REFERENCES svc.work_orders(wo_id)",
        
        # Crear tabla quote_items
        """
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
            quote_id INTEGER NOT NULL
        )
        """,
        
        # Constraints para quote_items
        "ALTER TABLE svc.quote_items ADD CONSTRAINT fk_quote_items_quote FOREIGN KEY (quote_id) REFERENCES svc.quotes(quote_id) ON DELETE CASCADE",
        "ALTER TABLE svc.quote_items ADD CONSTRAINT fk_quote_items_flat_rate FOREIGN KEY (flat_rate_id) REFERENCES svc.flat_rate_standards(flat_rate_id)",
        
        # Crear índices
        "CREATE INDEX IF NOT EXISTS idx_quotes_quote_number ON svc.quotes(quote_number)",
        "CREATE INDEX IF NOT EXISTS idx_quotes_client_status ON svc.quotes(client_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_quotes_quote_date ON svc.quotes(quote_date, status)",
        "CREATE INDEX IF NOT EXISTS idx_quote_items_quote_id ON svc.quote_items(quote_id)",
        
        # Datos de ejemplo
        """
        INSERT INTO svc.quotes (quote_number, status, quote_date, client_id, subtotal, total) VALUES
        ('QT-001', 'draft', CURRENT_DATE, 1, 1000.00, 1000.00),
        ('QT-002', 'sent', CURRENT_DATE - 1, 2, 1500.00, 1500.00)
        ON CONFLICT (quote_number) DO NOTHING
        """
    ]
    
    try:
        with connection.cursor() as cursor:
            for i, sql in enumerate(sql_commands, 1):
                try:
                    logger.info(f"Ejecutando comando {i}/{len(sql_commands)}")
                    cursor.execute(sql)
                    logger.info("✓ Comando ejecutado exitosamente")
                except Exception as e:
                    logger.warning(f"⚠ Comando {i} falló (puede ser opcional): {e}")
                    continue
            
            # Verificar creación
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'svc' AND table_name IN ('quotes', 'quote_items')")
            created_tables = [row[0] for row in cursor.fetchall()]
            
            logger.info("=" * 50)
            logger.info("RESULTADO DE CREACIÓN DE TABLAS")
            logger.info("=" * 50)
            
            if 'quotes' in created_tables:
                logger.info("✓ Tabla 'svc.quotes' creada exitosamente")
            else:
                logger.error("✗ Tabla 'svc.quotes' NO se creó")
                
            if 'quote_items' in created_tables:
                logger.info("✓ Tabla 'svc.quote_items' creada exitosamente")
            else:
                logger.error("✗ Tabla 'svc.quote_items' NO se creó")
                
            return 'quotes' in created_tables and 'quote_items' in created_tables
            
    except Exception as e:
        logger.error(f"Error fatal creando tablas: {e}")
        return False

def verify_tables():
    """Verificar que las tablas existen y funcionan"""
    try:
        with connection.cursor() as cursor:
            # Verificar estructura de quotes
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'svc' AND table_name = 'quotes'
                ORDER BY ordinal_position
            """)
            quote_columns = cursor.fetchall()
            logger.info(f"Columnas en svc.quotes: {len(quote_columns)}")
            
            # Verificar estructura de quote_items
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'svc' AND table_name = 'quote_items'
                ORDER BY ordinal_position
            """)
            item_columns = cursor.fetchall()
            logger.info(f"Columnas en svc.quote_items: {len(item_columns)}")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM svc.quotes")
            quote_count = cursor.fetchone()[0]
            logger.info(f"Registros en svc.quotes: {quote_count}")
            
            cursor.execute("SELECT COUNT(*) FROM svc.quote_items")
            item_count = cursor.fetchone()[0]
            logger.info(f"Registros en svc.quote_items: {item_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error verificando tablas: {e}")
        return False

if __name__ == '__main__':
    logger.info("Iniciando creación de tablas faltantes...")
    
    # Crear tablas
    creation_success = create_missing_tables()
    
    if creation_success:
        logger.info("Creación de tablas completada. Verificando...")
        verify_tables()
        logger.info("✓ Proceso completado exitosamente")
    else:
        logger.error("✗ Fallo en la creación de tablas")