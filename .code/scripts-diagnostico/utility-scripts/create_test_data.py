#!/usr/bin/env python
"""
Create test data for ForgeDB system.
This script creates sample data to make the system functional.
"""
import os
import sys
import django

# Setup Django environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Client, Alert, Technician, Warehouse, ProductMaster, Stock
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

def create_test_data():
    """Create comprehensive test data for the system."""
    print("🔧 Creating Test Data for ForgeDB")
    print("=" * 50)
    
    # Step 1: Create sample clients
    print("\n1. Creating sample clients...")
    clients_data = [
        {
            'name': 'AutoTaller García',
            'email': 'garcia@autotaller.com',
            'phone': '(555) 123-4567',
            'address': 'Av. Principal 123, Ciudad de México',
            'credit_limit': Decimal('50000.00')
        },
        {
            'name': 'Mecánica Rodríguez',
            'email': 'info@mecanicarodriguez.com',
            'phone': '(555) 987-6543',
            'address': 'Calle Reforma 456, Guadalajara',
            'credit_limit': Decimal('30000.00')
        },
        {
            'name': 'Taller Express',
            'email': 'contacto@tallerexpress.com',
            'phone': '(555) 555-0123',
            'address': 'Boulevard Norte 789, Monterrey',
            'credit_limit': Decimal('25000.00')
        },
        {
            'name': 'AutoServicio López',
            'email': 'lopez@autoservicio.com',
            'phone': '(555) 444-5678',
            'address': 'Av. Insurgentes 321, Puebla',
            'credit_limit': Decimal('40000.00')
        },
        {
            'name': 'Mecánica Integral',
            'email': 'admin@mecanicaintegral.com',
            'phone': '(555) 777-8888',
            'address': 'Calle Juárez 654, Tijuana',
            'credit_limit': Decimal('35000.00')
        }
    ]
    
    created_clients = 0
    for client_data in clients_data:
        client, created = Client.objects.get_or_create(
            email=client_data['email'],
            defaults=client_data
        )
        if created:
            created_clients += 1
            print(f"   ✅ Created client: {client.name}")
        else:
            print(f"   ℹ️  Client already exists: {client.name}")
    
    print(f"   📊 Total clients created: {created_clients}")
    
    # Step 2: Create sample technicians
    print("\n2. Creating sample technicians...")
    technicians_data = [
        {
            'name': 'Juan Pérez',
            'email': 'juan.perez@forgedb.com',
            'phone': '(555) 111-2222',
            'specialization': 'Motor',
            'hourly_rate': Decimal('350.00')
        },
        {
            'name': 'María González',
            'email': 'maria.gonzalez@forgedb.com',
            'phone': '(555) 333-4444',
            'specialization': 'Transmisión',
            'hourly_rate': Decimal('400.00')
        },
        {
            'name': 'Carlos Martínez',
            'email': 'carlos.martinez@forgedb.com',
            'phone': '(555) 555-6666',
            'specialization': 'Electricidad',
            'hourly_rate': Decimal('380.00')
        },
        {
            'name': 'Ana Rodríguez',
            'email': 'ana.rodriguez@forgedb.com',
            'phone': '(555) 777-9999',
            'specialization': 'Frenos',
            'hourly_rate': Decimal('320.00')
        }
    ]
    
    created_technicians = 0
    for tech_data in technicians_data:
        try:
            technician, created = Technician.objects.get_or_create(
                email=tech_data['email'],
                defaults=tech_data
            )
            if created:
                created_technicians += 1
                print(f"   ✅ Created technician: {technician.name}")
            else:
                print(f"   ℹ️  Technician already exists: {technician.name}")
        except Exception as e:
            print(f"   ⚠️  Could not create technician {tech_data['name']}: {e}")
    
    print(f"   📊 Total technicians created: {created_technicians}")
    
    # Step 3: Create sample warehouses
    print("\n3. Creating sample warehouses...")
    warehouses_data = [
        {
            'name': 'Almacén Principal',
            'location': 'Planta Baja - Área A',
            'warehouse_type': 'main'
        },
        {
            'name': 'Almacén de Refacciones',
            'location': 'Segundo Piso - Área B',
            'warehouse_type': 'parts'
        },
        {
            'name': 'Almacén de Herramientas',
            'location': 'Taller - Área C',
            'warehouse_type': 'tools'
        }
    ]
    
    created_warehouses = 0
    for warehouse_data in warehouses_data:
        try:
            warehouse, created = Warehouse.objects.get_or_create(
                name=warehouse_data['name'],
                defaults=warehouse_data
            )
            if created:
                created_warehouses += 1
                print(f"   ✅ Created warehouse: {warehouse.name}")
            else:
                print(f"   ℹ️  Warehouse already exists: {warehouse.name}")
        except Exception as e:
            print(f"   ⚠️  Could not create warehouse {warehouse_data['name']}: {e}")
    
    print(f"   📊 Total warehouses created: {created_warehouses}")
    
    # Step 4: Create sample products and stock
    print("\n4. Creating sample products and stock...")
    products_data = [
        {
            'name': 'Aceite Motor 5W-30',
            'description': 'Aceite sintético para motor',
            'category': 'Lubricantes',
            'unit_of_measure': 'Litro',
            'standard_cost': Decimal('85.00')
        },
        {
            'name': 'Filtro de Aire',
            'description': 'Filtro de aire universal',
            'category': 'Filtros',
            'unit_of_measure': 'Pieza',
            'standard_cost': Decimal('120.00')
        },
        {
            'name': 'Pastillas de Freno',
            'description': 'Pastillas de freno delanteras',
            'category': 'Frenos',
            'unit_of_measure': 'Juego',
            'standard_cost': Decimal('450.00')
        },
        {
            'name': 'Bujías',
            'description': 'Bujías de encendido',
            'category': 'Encendido',
            'unit_of_measure': 'Pieza',
            'standard_cost': Decimal('65.00')
        },
        {
            'name': 'Anticongelante',
            'description': 'Líquido anticongelante',
            'category': 'Lubricantes',
            'unit_of_measure': 'Litro',
            'standard_cost': Decimal('95.00')
        }
    ]
    
    created_products = 0
    main_warehouse = Warehouse.objects.filter(name='Almacén Principal').first()
    
    for product_data in products_data:
        try:
            product, created = ProductMaster.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                created_products += 1
                print(f"   ✅ Created product: {product.name}")
                
                # Create stock for this product
                if main_warehouse:
                    stock_quantity = 50 if 'Aceite' in product.name else 25
                    if 'Pastillas' in product.name:
                        stock_quantity = 8  # Low stock to trigger alerts
                    
                    stock, stock_created = Stock.objects.get_or_create(
                        product=product,
                        warehouse=main_warehouse,
                        defaults={
                            'quantity_on_hand': stock_quantity,
                            'unit_cost': product.standard_cost,
                            'last_updated': timezone.now()
                        }
                    )
                    if stock_created:
                        print(f"     📦 Created stock: {stock_quantity} units")
            else:
                print(f"   ℹ️  Product already exists: {product.name}")
        except Exception as e:
            print(f"   ⚠️  Could not create product {product_data['name']}: {e}")
    
    print(f"   📊 Total products created: {created_products}")
    
    # Step 5: Create sample alerts
    print("\n5. Creating sample alerts...")
    alerts_data = [
        {
            'alert_type': 'Inventario',
            'message': 'Stock bajo: Pastillas de Freno (8 unidades restantes)',
            'severity': 'warning',
            'category': 'inventory'
        },
        {
            'alert_type': 'Sistema',
            'message': 'Respaldo de base de datos completado exitosamente',
            'severity': 'info',
            'category': 'system'
        },
        {
            'alert_type': 'Orden de Trabajo',
            'message': 'Orden #1001 vencida - Cliente: AutoTaller García',
            'severity': 'high',
            'category': 'workorders'
        },
        {
            'alert_type': 'Facturación',
            'message': 'Factura #F-2024-001 pendiente de pago (30 días)',
            'severity': 'medium',
            'category': 'billing'
        },
        {
            'alert_type': 'Mantenimiento',
            'message': 'Equipo de diagnóstico requiere calibración',
            'severity': 'low',
            'category': 'maintenance'
        }
    ]
    
    created_alerts = 0
    for alert_data in alerts_data:
        try:
            alert = Alert.objects.create(
                alert_type=alert_data['alert_type'],
                message=alert_data['message'],
                created_at=timezone.now() - timedelta(hours=created_alerts * 2),
                # Add additional fields if they exist in the model
                **{k: v for k, v in alert_data.items() if k not in ['alert_type', 'message']}
            )
            created_alerts += 1
            print(f"   ✅ Created alert: {alert.alert_type}")
        except Exception as e:
            print(f"   ⚠️  Could not create alert {alert_data['alert_type']}: {e}")
    
    print(f"   📊 Total alerts created: {created_alerts}")
    
    return True

def create_summary():
    """Create a summary of the test data."""
    print("\n" + "=" * 50)
    print("📊 Test Data Summary")
    print("=" * 50)
    
    try:
        summary = {
            'Users': User.objects.count(),
            'Clients': Client.objects.count(),
            'Technicians': Technician.objects.count() if hasattr(Technician, 'objects') else 0,
            'Warehouses': Warehouse.objects.count() if hasattr(Warehouse, 'objects') else 0,
            'Products': ProductMaster.objects.count() if hasattr(ProductMaster, 'objects') else 0,
            'Stock Items': Stock.objects.count() if hasattr(Stock, 'objects') else 0,
            'Alerts': Alert.objects.count(),
        }
        
        for item, count in summary.items():
            print(f"   {item}: {count}")
        
        print(f"\n✅ System is now populated with test data!")
        print(f"🔑 You can now login and test the system functionality")
        
    except Exception as e:
        print(f"   ⚠️  Error generating summary: {e}")

def main():
    """Run test data creation."""
    print("🔧 ForgeDB Test Data Creation Tool")
    print("Creating sample data for system testing...")
    
    try:
        success = create_test_data()
        
        if success:
            create_summary()
            
            print("\n💡 Next Steps:")
            print("   1. Login to the system with existing credentials")
            print("   2. Navigate to the dashboard to see KPIs")
            print("   3. Browse clients, products, and other data")
            print("   4. Test creating new records")
            
            return True
        else:
            print("\n❌ Test data creation failed!")
            return False
        
    except Exception as e:
        print(f"\n❌ Test data creation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)