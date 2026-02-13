"""
OEM UI Views - Interfaces visibles para gestión de equivalencias y fitments.
Estas views usan Django ORM directamente en lugar de APIs HTTP.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.views.generic.edit import UpdateView
from django.http import JsonResponse, Http404
from django.conf import settings
from django.db.models import Count, Avg, Q
from django.db.utils import ProgrammingError, OperationalError
from django.urls import reverse_lazy

logger = logging.getLogger(__name__)


class OEMEquivalenceManagementView(LoginRequiredMixin, TemplateView):
    """
    Vista de gestión de equivalencias OEM ↔ Aftermarket.
    Usa Django ORM directamente.
    """
    template_name = 'frontend/oem/equivalence_management.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get import status from database
        import_status = {}
        error = None
        equivalences = []
        stats = {}
        filters = {}
        equivalence_types = [
            ('DIRECT', 'Directa'),
            ('COMPATIBLE', 'Compatible'),
            ('UPGRADE', 'Upgrade'),
            ('DOWNGRADE', 'Downgrade'),
        ]
        
        try:
            from core.models import ProductMaster, Supplier, OEMEquivalence, OEMBrand
            from django.core.exceptions import FieldError
            from django.db import connection
            
            # Verificar si las tablas existen antes de consultarlas
            def table_exists(table_name):
                try:
                    connection.cursor()
                    return True
                except:
                    return False
            
            # Contar productos importados (si la tabla existe)
            try:
                imported_products = ProductMaster.objects.filter(source_code='oem_import').count()
            except:
                imported_products = 0
            
            # Contar items OEM (si la tabla existe)
            try:
                from core.models import OEMCatalogItem
                total_oem = OEMCatalogItem.objects.count()
                pending_import = total_oem - imported_products
            except:
                total_oem = 0
                pending_import = 0
            
            import_status = {
                'total_oem_items': total_oem,
                'imported_products': imported_products,
                'pending_import': max(0, pending_import),
                'import_percentage': round((imported_products / total_oem * 100) if total_oem > 0 else 0, 1),
            }
            
            # Obtener filtros de la request
            filters = {
                'oem_part': self.request.GET.get('oem_part', ''),
                'aftermarket': self.request.GET.get('aftermarket', ''),
                'equivalence_type': self.request.GET.get('equivalence_type', ''),
                'min_confidence': self.request.GET.get('min_confidence', ''),
            }
            
            # Construir query de equivalencias (puede fallar si no existe la tabla oem.equivalences)
            try:
                equivalences_query = OEMEquivalence.objects.select_related('oem_code').all()
                if filters.get('oem_part'):
                    equivalences_query = equivalences_query.filter(oem_part_number__icontains=filters['oem_part'])
                if filters.get('aftermarket'):
                    equivalences_query = equivalences_query.filter(aftermarket_sku__icontains=filters['aftermarket'])
                if filters.get('equivalence_type'):
                    equivalences_query = equivalences_query.filter(equivalence_type=filters['equivalence_type'])
                if filters.get('min_confidence'):
                    equivalences_query = equivalences_query.filter(confidence_score__gte=int(filters['min_confidence']))
                equivalences = list(equivalences_query[:50])
                total_count = equivalences_query.count()
                stats = {
                    'total': total_count,
                    'by_confidence_ranges': {
                        'high': equivalences_query.filter(confidence_score__gte=80).count(),
                        'medium': equivalences_query.filter(confidence_score__gte=50, confidence_score__lt=80).count(),
                        'low': equivalences_query.filter(confidence_score__lt=50).count(),
                    },
                    'by_type': list(equivalences_query.values('equivalence_type').distinct()),
                }
            except (ProgrammingError, OperationalError) as db_err:
                err_msg = str(db_err)
                if 'oem.equivalences' in err_msg or 'does not exist' in err_msg.lower():
                    logger.warning("Tabla oem.equivalences no existe: %s", db_err)
                    error = (
                        'La tabla de equivalencias (oem.equivalences) no existe en la base de datos. '
                        'Ejecute las migraciones: python manage.py migrate'
                    )
                else:
                    error = f"Error de base de datos: {err_msg}"
                equivalences = []
                stats = {}
            
            # Get suppliers and brands for the forms with error checking
            suppliers = []
            brands = []
            
            try:
                suppliers = list(Supplier.objects.filter(is_active=True).values('supplier_id', 'name').order_by('name'))
            except Exception as supplier_error:
                logger.error(f"Error getting suppliers: {supplier_error}")
                error = f"Error al cargar proveedores: {str(supplier_error)}"
            
            # Cargar marcas OEM solo si la tabla existe
            try:
                brands = list(OEMBrand.objects.filter(is_active=True).values('oem_code', 'name').order_by('name'))
            except Exception as brand_error:
                logger.warning(f"Tabla de marcas OEM no disponible: {brand_error}")
                # No establecer error aquí para no afectar la carga de la página
                brands = []
            
            # Si no hay proveedores o marcas, registrar advertencia
            if not suppliers:
                logger.info("No se encontraron proveedores activos en la base de datos")
            if not brands:
                logger.info("No se encontraron marcas OEM activas en la base de datos o la tabla no existe")
            
        except ImportError as e:
            logger.error(f"Models not found: {e}")
            error = "Los modelos no están configurados. Debe ejecutar las migraciones primero."
            suppliers = []
            brands = []
        except Exception as e:
            logger.error(f"Error general en la vista: {e}")
            error = f"Error general: {str(e)}"
            suppliers = []
            brands = []
        
        context['import_status'] = import_status
        context['error'] = error
        context['suppliers'] = suppliers
        context['brands'] = brands
        context['equivalences'] = equivalences
        context['stats'] = stats
        context['filters'] = filters
        context['equivalence_types'] = equivalence_types
        return context


class OEMImportDashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard de importación de datos OEM.
    """
    template_name = 'frontend/oem/oem_import_dashboard.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get import status from database
        import_status = {}
        error = None
        
        try:
            from core.models import ProductMaster, Supplier
            from django.core.exceptions import FieldError
            from django.db import connection
            
            # Verificar si las tablas existen antes de consultarlas
            def table_exists(table_name):
                try:
                    connection.cursor()
                    return True
                except:
                    return False
            
            # Contar productos importados (si la tabla existe)
            try:
                imported_products = ProductMaster.objects.filter(source_code='oem_import').count()
            except:
                imported_products = 0
            
            # Contar items OEM (si la tabla existe)
            try:
                from core.models import OEMCatalogItem
                total_oem = OEMCatalogItem.objects.count()
                pending_import = total_oem - imported_products
            except:
                total_oem = 0
                pending_import = 0
            
            import_status = {
                'total_oem_items': total_oem,
                'imported_products': imported_products,
                'pending_import': max(0, pending_import),
                'import_percentage': round((imported_products / total_oem * 100) if total_oem > 0 else 0, 1),
            }
            
            # Get suppliers and brands for the forms with error checking
            suppliers = []
            brands = []
            
            try:
                suppliers = list(Supplier.objects.filter(is_active=True).values('supplier_id', 'name').order_by('name'))
            except Exception as supplier_error:
                logger.error(f"Error getting suppliers: {supplier_error}")
                error = f"Error al cargar proveedores: {str(supplier_error)}"
            
            # Cargar marcas OEM solo si la tabla existe
            try:
                from core.models import OEMBrand
                brands = list(OEMBrand.objects.filter(is_active=True).values('oem_code', 'name').order_by('name'))
            except Exception as brand_error:
                logger.warning(f"Tabla de marcas OEM no disponible: {brand_error}")
                # No establecer error aquí para no afectar la carga de la página
                brands = []
            
            # Si no hay proveedores o marcas, registrar advertencia
            if not suppliers:
                logger.info("No se encontraron proveedores activos en la base de datos")
            if not brands:
                logger.info("No se encontraron marcas OEM activas en la base de datos o la tabla no existe")
            
        except ImportError as e:
            logger.error(f"Models not found: {e}")
            error = "Los modelos no están configurados. Debe ejecutar las migraciones primero."
            suppliers = []
            brands = []
        except Exception as e:
            logger.error(f"Error general en la vista: {e}")
            error = f"Error general: {str(e)}"
            suppliers = []
            brands = []
        
        context['import_status'] = import_status
        context['error'] = error
        context['suppliers'] = suppliers
        context['brands'] = brands
        return context


class UnifiedSearchPageView(LoginRequiredMixin, TemplateView):
    """
    Página de búsqueda unificada visible.
    """
    template_name = 'frontend/search/unified_search.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        query = self.request.GET.get('q', '').strip()
        search_type = self.request.GET.get('type', 'all')
        
        results = {}
        error = None
        
        if query and len(query) >= 2:
            try:
                from core.models import ProductMaster, OEMCatalogItem, Equipment
                
                all_results = []
                
                # Search in products
                if search_type in ['all', 'products']:
                    products = ProductMaster.objects.filter(
                        Q(name__icontains=query) | 
                        Q(internal_sku__icontains=query) |
                        Q(description__icontains=query)
                    )[:10]
                    all_results.extend([
                        {
                            'type': 'product',
                            'name': p.name,
                            'sku': p.internal_sku,
                            'description': p.description,
                        }
                        for p in products
                    ])
                
                # Search in OEM catalog
                if search_type in ['all', 'oem']:
                    oem_parts = OEMCatalogItem.objects.filter(
                        Q(part_number__icontains=query) |
                        Q(description_es__icontains=query)
                    )[:10]
                    all_results.extend([
                        {
                            'type': 'oem',
                            'name': p.part_number,
                            'sku': p.oem_code,
                            'description': p.description_es,
                        }
                        for p in oem_parts
                    ])
                
                # Search in equipment
                if search_type in ['all', 'equipment']:
                    equipment = Equipment.objects.filter(
                        Q(name__icontains=query) |
                        Q(equipment_id__icontains=query)
                    )[:10]
                    all_results.extend([
                        {
                            'type': 'equipment',
                            'name': e.name,
                            'sku': e.equipment_id,
                            'description': '',
                        }
                        for e in equipment
                    ])
                
                results = {
                    'total': len(all_results),
                    'results': all_results,
                }
                
            except ImportError as e:
                logger.warning(f"Models not found: {e}")
                error = "Los modelos no están configurados."
            except Exception as e:
                logger.error(f"Error in search: {e}")
                error = str(e)
        
        context.update({
            'query': query,
            'search_type': search_type,
            'results': results,
            'error': error,
            'search_types': [
                {'value': 'all', 'label': 'Todos'},
                {'value': 'products', 'label': 'Inventario'},
                {'value': 'oem', 'label': 'Catálogo OEM'},
                {'value': 'equipment', 'label': 'Equipos'},
            ],
        })
        
        return context


class OEMEquivalenceCreateView(LoginRequiredMixin, FormView):
    """
    Vista para crear nuevas equivalencias OEM.
    """
    template_name = 'frontend/oem/equivalence_form.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'create'
        
        # Cargar marcas OEM
        try:
            from core.models import OEMBrand
            brands = list(OEMBrand.objects.filter(is_active=True).values('oem_code', 'name').order_by('name'))
            context['brands'] = brands
        except Exception as e:
            logger.error(f"Error loading OEM brands: {e}")
            context['brands'] = []
        
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            from core.models import OEMEquivalence, OEMBrand
            
            oem_part_number = request.POST.get('oem_part_number', '').strip()
            aftermarket_sku = request.POST.get('aftermarket_sku', '').strip()
            oem_code = request.POST.get('oem_code', '').strip()
            equivalence_type = request.POST.get('equivalence_type', 'DIRECT')
            confidence_score = int(request.POST.get('confidence_score', 50))
            notes = request.POST.get('notes', '').strip()
            
            # Validaciones básicas
            if not oem_part_number:
                return JsonResponse({'success': False, 'error': 'El número de parte OEM es requerido'})
            if not oem_code:
                return JsonResponse({'success': False, 'error': 'La marca OEM es requerida'})
            
            # Crear la equivalencia
            equivalence = OEMEquivalence.objects.create(
                oem_part_number=oem_part_number,
                oem_code_id=oem_code,
                aftermarket_sku=aftermarket_sku if aftermarket_sku else None,
                equivalence_type=equivalence_type,
                confidence_score=confidence_score,
                notes=notes,
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Equivalencia creada correctamente',
                'equivalence_id': equivalence.equivalence_id
            })
        except Exception as e:
            logger.error(f"Error creating equivalence: {e}")
            return JsonResponse({'success': False, 'error': str(e)})


class OEMEquivalenceEditView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar equivalencias OEM existentes.
    """
    template_name = 'frontend/oem/equivalence_form.html'
    login_url = 'frontend:login'
    
    def get_object(self, queryset=None):
        """Obtener la equivalencia por su ID"""
        from core.models import OEMEquivalence
        equivalence_id = self.kwargs.get('equivalence_id')
        try:
            return OEMEquivalence.objects.get(equivalence_id=equivalence_id)
        except OEMEquivalence.DoesNotExist:
            raise Http404("Equivalencia no encontrada")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'edit'
        
        # Cargar marcas OEM
        try:
            from core.models import OEMBrand
            brands = list(OEMBrand.objects.filter(is_active=True).values('oem_code', 'name').order_by('name'))
            context['brands'] = brands
        except Exception as e:
            logger.error(f"Error loading OEM brands: {e}")
            context['brands'] = []
        
        return context
    
    def post(self, request, *args, **kwargs):
        try:
            from core.models import OEMEquivalence
            
            equivalence = self.get_object()
            
            oem_part_number = request.POST.get('oem_part_number', '').strip()
            aftermarket_sku = request.POST.get('aftermarket_sku', '').strip()
            oem_code = request.POST.get('oem_code', '').strip()
            equivalence_type = request.POST.get('equivalence_type', 'DIRECT')
            confidence_score = int(request.POST.get('confidence_score', 50))
            notes = request.POST.get('notes', '').strip()
            
            # Validaciones básicas
            if not oem_part_number:
                return JsonResponse({'success': False, 'error': 'El número de parte OEM es requerido'})
            if not oem_code:
                return JsonResponse({'success': False, 'error': 'La marca OEM es requerida'})
            
            # Actualizar la equivalencia
            equivalence.oem_part_number = oem_part_number
            equivalence.oem_code_id = oem_code
            equivalence.aftermarket_sku = aftermarket_sku if aftermarket_sku else None
            equivalence.equivalence_type = equivalence_type
            equivalence.confidence_score = confidence_score
            equivalence.notes = notes
            equivalence.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Equivalencia actualizada correctamente',
                'equivalence_id': equivalence.equivalence_id
            })
        except Exception as e:
            logger.error(f"Error updating equivalence: {e}")
            return JsonResponse({'success': False, 'error': str(e)})

