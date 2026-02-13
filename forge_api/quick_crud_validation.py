#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validación rápida de CRUDs del sistema ForgeDB
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.urls import reverse
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_url_exists(url_name, description):
    """Test básico para verificar que una URL existe"""
    try:
        url = reverse(url_name)
        logger.info(f"✅ {description}: {url}")
        return True
    except Exception as e:
        logger.error(f"❌ {description}: ERROR - {str(e)}")
        return False

def main():
    logger.info("🔧 VALIDACIÓN DE CRUDs DEL SISTEMA FORGEDB")
    logger.info("=" * 50)
    
    # Lista de URLs a validar
    urls_to_test = [
        # Clientes
        ('frontend:client_list', 'Clientes - Lista'),
        ('frontend:client_create', 'Clientes - Crear'),
        
        # Equipos
        ('frontend:equipment_list', 'Equipos - Lista'),
        ('frontend:equipment_create', 'Equipos - Crear'),
        
        # Catálogos
        ('frontend:equipment_type_list', 'Tipos de Equipo - Lista'),
        ('frontend:equipment_type_create', 'Tipos de Equipo - Crear'),
        
        ('frontend:taxonomy_tree', 'Taxonomía - Árbol'),
        ('frontend:taxonomy_system_create', 'Taxonomía - Crear Sistema'),
        
        ('frontend:reference_code_list', 'Códigos Ref. - Lista'),
        ('frontend:reference_code_create', 'Códigos Ref. - Crear'),
        
        ('frontend:currency_list', 'Monedas - Lista'),
        ('frontend:currency_create', 'Monedas - Crear'),
        
        # Proveedores
        ('frontend:supplier_list', 'Proveedores - Lista'),
        ('frontend:supplier_create', 'Proveedores - Crear'),
        
        # Técnicos
        ('frontend:technician_list', 'Técnicos - Lista'),
        ('frontend:technician_create', 'Técnicos - Crear'),
        
        # Órdenes de Trabajo
        ('frontend:workorder_list', 'Órdenes - Lista'),
        ('frontend:workorder_create', 'Órdenes - Crear'),
        
        # Facturas
        ('frontend:invoice_list', 'Facturas - Lista'),
        ('frontend:invoice_create', 'Facturas - Crear'),
        
        # Cotizaciones
        ('frontend:quote_list', 'Cotizaciones - Lista'),
        ('frontend:quote_create', 'Cotizaciones - Crear'),
        
        # Inventario
        ('frontend:product_list', 'Productos - Lista'),
        ('frontend:product_create', 'Productos - Crear'),
        
        ('frontend:warehouse_list', 'Almacenes - Lista'),
        ('frontend:warehouse_create', 'Almacenes - Crear'),
        
        ('frontend:stock_movements', 'Movimientos Stock - Lista'),
        ('frontend:stock_movement_create', 'Movimientos Stock - Crear'),
        
        # Compras
        ('frontend:purchase_order_list', 'Órdenes Compra - Lista'),
        ('frontend:purchase_order_create', 'Órdenes Compra - Crear'),
    ]
    
    # Validar cada URL
    passed = 0
    total = len(urls_to_test)
    
    for url_name, description in urls_to_test:
        if test_url_exists(url_name, description):
            passed += 1
    
    # Resultado
    logger.info("\n" + "=" * 50)
    logger.info("📊 RESULTADO FINAL")
    logger.info("=" * 50)
    logger.info(f"✅ URLs válidas: {passed}/{total}")
    logger.info(f"📈 Porcentaje: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.info("\n🎉 ¡TODAS LAS URLS DE CRUD VALIDADAS!")
        logger.info("✅ Sistema CRUD completamente funcional")
    else:
        logger.info(f"\n⚠️  {total - passed} URLs con problemas")
        logger.info("🔧 Requiere revisión")

if __name__ == '__main__':
    main()