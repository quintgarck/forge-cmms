"""
Tests de integración OEM + Equipos
Verifican que la integración entre el módulo de equipos y el catálogo OEM funcione correctamente.
"""
import json
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from core.models import OEMBrand, OEMCatalogItem, Equipment, Client as ClientModel
from frontend.views.equipment_views import EquipmentCreateView
from frontend.views.oem_views import OEMModelListAPIView
from rest_framework.test import APIClient


class OEMSchemaTestCase(TestCase):
    """Tests para verificar que el esquema OEM existe y tiene datos"""
    
    databases = ['default']
    
    def setUp(self):
        """Setup de datos de prueba"""
        # Crear marcas OEM
        self.toyota = OEMBrand.objects.create(
            oem_code='TOYOTA',
            name='Toyota Motor Corporation',
            brand_type='VEHICLE_MFG',
            country='JP',
            is_active=True,
            display_order=1
        )
        
        self.ford = OEMBrand.objects.create(
            oem_code='FORD',
            name='Ford Motor Company',
            brand_type='VEHICLE_MFG',
            country='US',
            is_active=True,
            display_order=2
        )
        
        # Crear modelos OEM para Toyota
        self.corolla = OEMCatalogItem.objects.create(
            oem_code='TOYOTA',
            part_number='COROLLA',
            description_es='Toyota Corolla',
            description_en='Toyota Corolla',
            item_type='VEHICLE_MODEL',
            body_style='Sedan',
            year_start=1966,
            year_end=2024,
            is_active=True,
            display_order=1
        )
        
        self.camry = OEMCatalogItem.objects.create(
            oem_code='TOYOTA',
            part_number='CAMRY',
            description_es='Toyota Camry',
            description_en='Toyota Camry',
            item_type='VEHICLE_MODEL',
            body_style='Sedan',
            year_start=1982,
            year_end=2024,
            is_active=True,
            display_order=2
        )
        
        # Crear modelos OEM para Ford
        self.f150 = OEMCatalogItem.objects.create(
            oem_code='FORD',
            part_number='F150',
            description_es='Ford F-150',
            description_en='Ford F-150',
            item_type='VEHICLE_MODEL',
            body_style='Pickup',
            year_start=1948,
            year_end=2024,
            is_active=True,
            display_order=1
        )
    
    def test_oem_brands_exist(self):
        """Verificar que las marcas OEM existen"""
        brands_count = OEMBrand.objects.filter(is_active=True).count()
        self.assertGreaterEqual(brands_count, 2, "Debe haber al menos 2 marcas OEM activas")
    
    def test_oem_catalog_items_exist(self):
        """Verificar que los items del catálogo OEM existen"""
        items_count = OEMCatalogItem.objects.filter(
            item_type='VEHICLE_MODEL',
            is_active=True
        ).count()
        self.assertGreaterEqual(items_count, 3, "Debe haber al menos 3 modelos de vehículos activos")
    
    def test_oem_brand_code_unique(self):
        """Verificar que los códigos OEM son únicos"""
        toyota_count = OEMBrand.objects.filter(oem_code='TOYOTA').count()
        self.assertEqual(toyota_count, 1, "Cada código OEM debe ser único")
    
    def test_catalog_items_by_brand(self):
        """Verificar que podemos filtrar modelos por marca"""
        toyota_models = OEMCatalogItem.objects.filter(
            oem_code='TOYOTA',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
        self.assertEqual(toyota_models.count(), 2, "Toyota debe tener 2 modelos")
        
        ford_models = OEMCatalogItem.objects.filter(
            oem_code='FORD',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
        self.assertEqual(ford_models.count(), 1, "Ford debe tener 1 modelo")


class OEMAPIEndpointTestCase(TestCase):
    """Tests para el endpoint API interno /api/oem/models/"""
    
    databases = ['default']
    
    def setUp(self):
        """Setup de datos de prueba y usuario"""
        # Crear usuario para autenticación
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear marcas y modelos OEM
        self.toyota = OEMBrand.objects.create(
            oem_code='TOYOTA',
            name='Toyota Motor Corporation',
            brand_type='VEHICLE_MFG',
            is_active=True
        )
        
        OEMCatalogItem.objects.create(
            oem_code='TOYOTA',
            part_number='COROLLA',
            description_es='Toyota Corolla',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
        
        OEMCatalogItem.objects.create(
            oem_code='TOYOTA',
            part_number='CAMRY',
            description_es='Toyota Camry',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_oem_models_api_without_oem_code(self):
        """Test que el endpoint requiere oem_code"""
        response = self.client.get('/api/oem/models/')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('detail', data)
    
    def test_oem_models_api_with_valid_oem_code(self):
        """Test que el endpoint retorna modelos filtrados por marca"""
        response = self.client.get('/api/oem/models/', {
            'oem_code': 'TOYOTA',
            'item_type': 'VEHICLE_MODEL'
        })
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # El response puede ser paginado o lista directa
        results = data.get('results', data)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "Debe retornar al menos un modelo")
        
        # Verificar estructura de cada modelo
        for model in results:
            self.assertIn('part_number', model)
            self.assertIn('description_es', model)
    
    def test_oem_models_api_with_invalid_oem_code(self):
        """Test que el endpoint retorna lista vacía para marca inexistente"""
        response = self.client.get('/api/oem/models/', {
            'oem_code': 'INVALID_BRAND',
            'item_type': 'VEHICLE_MODEL'
        })
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        results = data.get('results', data)
        
        # Debe retornar lista vacía
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0, "No debe retornar modelos para marca inexistente")


class EquipmentFormIntegrationTestCase(TestCase):
    """Tests para verificar que el formulario de equipos carga marcas OEM"""
    
    databases = ['default']
    
    def setUp(self):
        """Setup de datos de prueba"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear cliente para asociar al equipo
        self.test_client = ClientModel.objects.create(
            name='Cliente de Prueba',
            email='test@example.com',
            phone='1234567890'
        )
        
        # Crear marcas OEM
        OEMBrand.objects.create(
            oem_code='TOYOTA',
            name='Toyota Motor Corporation',
            brand_type='VEHICLE_MFG',
            is_active=True,
            display_order=1
        )
        
        OEMBrand.objects.create(
            oem_code='FORD',
            name='Ford Motor Company',
            brand_type='VEHICLE_MFG',
            is_active=True,
            display_order=2
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_equipment_create_view_loads_brands(self):
        """Test que la vista de crear equipo carga marcas OEM"""
        response = self.client.get('/equipment/create/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id_brand')
        self.assertContains(response, 'TOYOTA')
        self.assertContains(response, 'FORD')
    
    def test_equipment_form_has_model_field(self):
        """Test que el formulario tiene el campo modelo"""
        response = self.client.get('/equipment/create/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id_model')
    
    def test_equipment_form_has_javascript_for_dynamic_loading(self):
        """Test que el formulario tiene JavaScript para carga dinámica"""
        response = self.client.get('/equipment/create/')
        
        self.assertEqual(response.status_code, 200)
        # Verificar que existe el JavaScript para cargar modelos
        self.assertContains(response, 'loadModelsForBrand')
        self.assertContains(response, '/api/oem/models/')


class EquipmentCreationWithOEMTestCase(TestCase):
    """Tests para crear equipos usando datos del catálogo OEM"""
    
    databases = ['default']
    
    def setUp(self):
        """Setup de datos de prueba"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear cliente
        self.test_client = ClientModel.objects.create(
            name='Cliente de Prueba',
            email='test@example.com',
            phone='1234567890'
        )
        
        # Crear marcas y modelos OEM
        OEMBrand.objects.create(
            oem_code='TOYOTA',
            name='Toyota Motor Corporation',
            brand_type='VEHICLE_MFG',
            is_active=True
        )
        
        OEMCatalogItem.objects.create(
            oem_code='TOYOTA',
            part_number='COROLLA',
            description_es='Toyota Corolla',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_create_equipment_with_oem_brand_and_model(self):
        """Test crear un equipo con marca y modelo del catálogo OEM"""
        equipment_data = {
            'equipment_code': 'TEST-001',
            'client_id': self.test_client.client_id,
            'brand': 'TOYOTA',
            'model': 'COROLLA',
            'year': 2020,
            'status': 'ACTIVO',
        }
        
        response = self.client.post('/equipment/create/', equipment_data)
        
        # Debe redirigir después de creación exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el equipo fue creado
        equipment = Equipment.objects.filter(equipment_code='TEST-001').first()
        self.assertIsNotNone(equipment)
        self.assertEqual(equipment.brand, 'TOYOTA')
        self.assertEqual(equipment.model, 'COROLLA')


class OEMDataIntegrityTestCase(TestCase):
    """Tests para verificar la integridad de datos OEM"""
    
    databases = ['default']
    
    def setUp(self):
        """Setup de datos de prueba"""
        self.toyota = OEMBrand.objects.create(
            oem_code='TOYOTA',
            name='Toyota Motor Corporation',
            brand_type='VEHICLE_MFG',
            is_active=True
        )
        
        OEMCatalogItem.objects.create(
            oem_code='TOYOTA',
            part_number='COROLLA',
            description_es='Toyota Corolla',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
    
    def test_active_brands_only(self):
        """Test que solo se muestran marcas activas"""
        # Crear marca inactiva
        OEMBrand.objects.create(
            oem_code='INACTIVE',
            name='Inactive Brand',
            brand_type='VEHICLE_MFG',
            is_active=False
        )
        
        active_brands = OEMBrand.objects.filter(is_active=True)
        self.assertEqual(active_brands.count(), 1)
        self.assertEqual(active_brands.first().oem_code, 'TOYOTA')
    
    def test_active_models_only(self):
        """Test que solo se muestran modelos activos"""
        # Crear modelo inactivo
        OEMCatalogItem.objects.create(
            oem_code='TOYOTA',
            part_number='OLD_MODEL',
            description_es='Old Model',
            item_type='VEHICLE_MODEL',
            is_active=False
        )
        
        active_models = OEMCatalogItem.objects.filter(
            oem_code='TOYOTA',
            item_type='VEHICLE_MODEL',
            is_active=True
        )
        self.assertEqual(active_models.count(), 1)
        self.assertEqual(active_models.first().part_number, 'COROLLA')
    
    def test_year_range_validation(self):
        """Test que el rango de años es válido"""
        model = OEMCatalogItem.objects.get(part_number='COROLLA')
        
        if model.year_start and model.year_end:
            self.assertLessEqual(
                model.year_start,
                model.year_end,
                "year_start debe ser menor o igual a year_end"
            )
