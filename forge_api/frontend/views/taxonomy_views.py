"""
Vistas para el sistema de taxonomía jerárquica
Implementa CRUD completo para sistemas, subsistemas y grupos de taxonomía
"""

import json
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView, FormView
)

from ..mixins import APIClientMixin
from ..forms.taxonomy_forms import (
    TaxonomySystemForm, TaxonomySubsystemForm, TaxonomyGroupForm,
    TaxonomySearchForm, TaxonomyBulkActionForm
)
from ..utils.taxonomy_validators import TaxonomyValidator, TaxonomyWarningSystem

logger = logging.getLogger(__name__)


class TaxonomyTreeView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Vista principal del árbol de taxonomía jerárquica"""
    template_name = 'frontend/catalog/taxonomy_tree.html'
    
    def _get_categories_choices(self):
        """Obtener categorías activas de la API para el select"""
        try:
            response = self.api_client.get('categories/', params={'is_active': True, 'ordering': 'sort_order,name'})
            if response and 'results' in response:
                # Retornar tuplas (category_code, name)
                return [(cat['category_code'], cat['name']) for cat in response['results']]
        except Exception as e:
            logger.warning(f"Error loading categories for taxonomy form: {e}")
        
        # Fallback: categoría por defecto
        return [('AUTOMOTRIZ', 'Automotriz')]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener categorías para el formulario
        categories_choices = self._get_categories_choices()
        
        # Siempre inicializar los formularios (no dependen de la API)
        context['system_form'] = TaxonomySystemForm(categories_choices=categories_choices)
        context['search_form'] = TaxonomySearchForm()
        
        try:
            # Obtener todos los sistemas
            systems_data = self.api_client.get('taxonomy-systems/', params={'page_size': 1000, 'is_active': True})
            systems_list = systems_data.get('results', [])
            
            # Obtener todos los subsistemas
            try:
                subsystems_data = self.api_client.get('taxonomy-subsystems/', params={'page_size': 1000, 'is_active': True})
                subsystems_list = subsystems_data.get('results', [])
            except Exception as e:
                logger.warning(f"Error loading subsystems: {e}")
                subsystems_list = []
            
            # Obtener todos los grupos
            try:
                groups_data = self.api_client.get('taxonomy-groups/', params={'page_size': 1000, 'is_active': True})
                groups_list = groups_data.get('results', [])
            except Exception as e:
                logger.warning(f"Error loading groups: {e}")
                groups_list = []
            
            # Construir árbol jerárquico
            # Crear diccionarios para acceso rápido
            systems_dict = {s['system_code']: s for s in systems_list}
            subsystems_dict = {s['subsystem_code']: s for s in subsystems_list}
            
            # Asignar grupos a subsistemas
            for group in groups_list:
                subsystem_code = group.get('subsystem_code')
                if subsystem_code and subsystem_code in subsystems_dict:
                    if 'groups' not in subsystems_dict[subsystem_code]:
                        subsystems_dict[subsystem_code]['groups'] = []
                    subsystems_dict[subsystem_code]['groups'].append(group)
            
            # Asignar subsistemas a sistemas
            for subsystem in subsystems_list:
                system_code = subsystem.get('system_code')
                if system_code and system_code in systems_dict:
                    if 'subsystems' not in systems_dict[system_code]:
                        systems_dict[system_code]['subsystems'] = []
                    systems_dict[system_code]['subsystems'].append(subsystem)
            
            # Convertir de vuelta a lista manteniendo el orden
            taxonomy_tree = []
            for system in systems_list:
                if system['system_code'] in systems_dict:
                    system_data = systems_dict[system['system_code']]
                    # Asegurar que subsystems exista (aunque sea vacío)
                    if 'subsystems' not in system_data:
                        system_data['subsystems'] = []
                    taxonomy_tree.append(system_data)
            
            context['taxonomy_tree'] = taxonomy_tree
            
            # Calcular estadísticas
            systems_count = len(systems_list)
            subsystems_count = len(subsystems_list)
            groups_count = len(groups_list)
            
            context['taxonomy_stats'] = {
                'systems_count': systems_count,
                'subsystems_count': subsystems_count,
                'groups_count': groups_count,
                'total_nodes': systems_count + subsystems_count + groups_count
            }
            
        except Exception as e:
            logger.error(f"Error loading taxonomy tree: {e}")
            messages.error(self.request, "Error al cargar la estructura de taxonomía.")
            context['taxonomy_tree'] = []
            context['taxonomy_stats'] = {
                'systems_count': 0,
                'subsystems_count': 0,
                'groups_count': 0,
                'total_nodes': 0
            }
        
        return context


class TaxonomySystemListView(LoginRequiredMixin, APIClientMixin, ListView):
    """Lista de sistemas de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_system_list.html'
    context_object_name = 'systems'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            # Parámetros de búsqueda y filtrado
            search = self.request.GET.get('search', '')
            is_active = self.request.GET.get('is_active', '')
            
            params = {}
            if search:
                params['search'] = search
            if is_active:
                params['is_active'] = is_active
            
            response = self.api_client.get('taxonomy-systems/', params=params)
            return response.get('results', [])
            
        except Exception as e:
            logger.error(f"Error loading taxonomy systems: {e}")
            messages.error(self.request, "Error al cargar los sistemas de taxonomía.")
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = TaxonomySearchForm(self.request.GET)
        context['current_search'] = self.request.GET.get('search', '')
        return context


class TaxonomySystemCreateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Crear nuevo sistema de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_system_form.html'
    form_class = TaxonomySystemForm
    success_url = reverse_lazy('frontend:taxonomy_system_list')
    
    def _get_categories_choices(self):
        """Obtener categorías activas de la API para el select"""
        try:
            response = self.api_client.get('categories/', params={'is_active': True, 'ordering': 'sort_order,name'})
            if response and 'results' in response:
                # Retornar tuplas (category_code, name)
                return [(cat['category_code'], cat['name']) for cat in response['results']]
        except Exception as e:
            logger.warning(f"Error loading categories for taxonomy form: {e}")
        
        # Fallback: categoría por defecto
        return [('AUTOMOTRIZ', 'Automotriz')]
    
    def get_form_kwargs(self):
        """Pasamos las categorías al formulario"""
        kwargs = super().get_form_kwargs()
        kwargs['categories_choices'] = self._get_categories_choices()
        return kwargs
    
    def form_valid(self, form):
        try:
            data = form.cleaned_data
            
            # Preparar datos para la API con los nombres de campos correctos
            api_data = {
                'system_code': data['system_code'],
                'category': data.get('category', 'AUTOMOTRIZ'),
                'name_es': data['name_es'],
                'name_en': data.get('name_en', ''),
                'icon': data.get('icon', ''),
                'scope': data.get('scope', ''),
                'sort_order': data.get('sort_order', 0),
                'is_active': data.get('is_active', True)
            }
            
            response = self.api_client.post('taxonomy-systems/', api_data)
            
            messages.success(
                self.request, 
                f"Sistema de taxonomía '{data['name_es']}' creado exitosamente."
            )
            return redirect(self.success_url)
            
        except Exception as e:
            logger.error(f"Error creating taxonomy system: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 400:
                # Errores de validación del API
                try:
                    api_errors = e.response.json()
                    for field, errors in api_errors.items():
                        if field in form.fields:
                            form.add_error(field, errors)
                        else:
                            form.add_error(None, f"{field}: {errors}")
                except:
                    # Si no se puede parsear el JSON, mostrar mensaje genérico
                    form.add_error(None, "Error de validación en el servidor.")
            else:
                # Mostrar mensaje de error más específico
                error_msg = str(e)
                if hasattr(e, 'message'):
                    error_msg = e.message
                messages.error(self.request, f"Error al crear el sistema de taxonomía: {error_msg}")
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Sistema de Taxonomía'
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse('frontend:catalog_index')},
            {'name': 'Taxonomía', 'url': reverse('frontend:taxonomy_tree')},
            {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
            {'name': 'Crear', 'url': None}
        ]
        return context


class TaxonomySystemUpdateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Editar sistema de taxonomía existente"""
    template_name = 'frontend/catalog/taxonomy_system_form.html'
    form_class = TaxonomySystemForm
    success_url = reverse_lazy('frontend:taxonomy_system_list')
    
    def _get_categories_choices(self):
        """Obtener categorías activas de la API para el select"""
        try:
            response = self.api_client.get('categories/', params={'is_active': True, 'ordering': 'sort_order,name'})
            if response and 'results' in response:
                return [(cat['category_code'], cat['name']) for cat in response['results']]
        except Exception as e:
            logger.warning(f"Error loading categories for taxonomy form: {e}")
        
        return [('AUTOMOTRIZ', 'Automotriz')]
    
    def get_form_kwargs(self):
        """Pasamos las categorías al formulario"""
        kwargs = super().get_form_kwargs()
        kwargs['categories_choices'] = self._get_categories_choices()
        return kwargs
    
    def get_object(self):
        system_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-systems/{system_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy system {system_id}: {e}")
            raise Http404("Sistema de taxonomía no encontrado")
    
    def get_initial(self):
        obj = self.get_object()
        return {
            'system_code': obj.get('system_code', ''),
            'category': obj.get('category', 'AUTOMOTRIZ'),
            'name_es': obj.get('name_es', ''),
            'name_en': obj.get('name_en', ''),
            'icon': obj.get('icon', ''),
            'scope': obj.get('scope', ''),
            'sort_order': obj.get('sort_order', 0),
            'is_active': obj.get('is_active', True)
        }
    
    def form_valid(self, form):
        system_id = self.kwargs['pk']
        try:
            data = form.cleaned_data
            
            # Preparar datos para la API con los nombres de campos correctos
            api_data = {
                'system_code': data['system_code'],
                'category': data.get('category', 'AUTOMOTRIZ'),
                'name_es': data['name_es'],
                'name_en': data.get('name_en', ''),
                'icon': data.get('icon', ''),
                'scope': data.get('scope', ''),
                'sort_order': data.get('sort_order', 0),
                'is_active': data.get('is_active', True)
            }
            
            response = self.api_client.put(f'taxonomy-systems/{system_id}/', api_data)
            
            messages.success(
                self.request, 
                f"Sistema de taxonomía '{data['name_es']}' actualizado exitosamente."
            )
            return redirect(self.success_url)
            
        except Exception as e:
            logger.error(f"Error updating taxonomy system {system_id}: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 400:
                try:
                    api_errors = e.response.json()
                    for field, errors in api_errors.items():
                        if field in form.fields:
                            form.add_error(field, errors)
                        else:
                            form.add_error(None, f"{field}: {errors}")
                except:
                    form.add_error(None, "Error de validación en el servidor.")
            else:
                error_msg = str(e)
                if hasattr(e, 'message'):
                    error_msg = e.message
                messages.error(self.request, f"Error al actualizar el sistema de taxonomía: {error_msg}")
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['title'] = f'Editar Sistema: {obj.get("name", "")}'
        context['object'] = obj
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse('frontend:catalog_index')},
            {'name': 'Taxonomía', 'url': reverse('frontend:taxonomy_tree')},
            {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
            {'name': obj.get('name', 'Editar'), 'url': None}
        ]
        return context


class TaxonomySystemDetailView(LoginRequiredMixin, APIClientMixin, DetailView):
    """Vista detallada de sistema de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_system_detail.html'
    context_object_name = 'system'
    
    def get_object(self):
        system_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-systems/{system_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy system {system_id}: {e}")
            raise Http404("Sistema de taxonomía no encontrado")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system = self.get_object()
        system_id = self.kwargs['pk']
        
        try:
            # Obtener subsistemas del sistema - el API usa system_code
            subsystems = self.api_client.get(
                'taxonomy-subsystems/',
                params={'system_code': system_id}
            )
            context['subsystems'] = subsystems.get('results', [])
            
            # Calcular estadísticas localmente
            subsystems_count = len(context['subsystems'])
            groups_count = sum([len(s.get('groups', [])) for s in context['subsystems']])
            context['system_stats'] = {
                'subsystems_count': subsystems_count,
                'groups_count': groups_count,
                'total_items': subsystems_count + groups_count
            }
            
        except Exception as e:
            logger.error(f"Error loading system details: {e}")
            context['subsystems'] = []
            context['system_stats'] = {}
        
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse('frontend:catalog_index')},
            {'name': 'Taxonomía', 'url': reverse('frontend:taxonomy_tree')},
            {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
            {'name': system.get('name', 'Detalle'), 'url': None}
        ]
        
        return context


class TaxonomySystemDeleteView(LoginRequiredMixin, APIClientMixin, DeleteView):
    """Eliminar sistema de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_system_confirm_delete.html'
    success_url = reverse_lazy('frontend:taxonomy_system_list')
    
    def get_object(self):
        system_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-systems/{system_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy system {system_id}: {e}")
            raise Http404("Sistema de taxonomía no encontrado")
    
    def delete(self, request, *args, **kwargs):
        system_id = self.kwargs['pk']
        system = self.get_object()
        
        try:
            # Verificar dependencias antes de eliminar
            dependencies = self.api_client.get(
                f'taxonomy-systems/{system_id}/dependencies/'
            )
            
            if dependencies.get('has_dependencies', False):
                messages.error(
                    request,
                    f"No se puede eliminar el sistema '{system['name']}' porque tiene dependencias: "
                    f"{', '.join(dependencies.get('dependency_types', []))}"
                )
                return redirect('frontend:taxonomy_system_detail', pk=system_id)
            
            # Proceder con la eliminación
            self.api_client.delete(f'taxonomy-systems/{system_id}/')
            
            messages.success(
                request, 
                f"Sistema de taxonomía '{system['name']}' eliminado exitosamente."
            )
            return redirect(self.success_url)
            
        except Exception as e:
            logger.error(f"Error deleting taxonomy system {system_id}: {e}")
            messages.error(request, "Error al eliminar el sistema de taxonomía.")
            return redirect('frontend:taxonomy_system_detail', pk=system_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system = self.get_object()
        system_id = self.kwargs['pk']
        
        try:
            # Obtener información de dependencias con validador mejorado
            validator = TaxonomyValidator(self.api_client)
            dependencies = validator.check_dependencies('system', system_id)
            context['dependencies'] = dependencies
            
            # Generar advertencias usando el sistema de advertencias
            warnings = TaxonomyWarningSystem.get_deletion_warnings(
                'system', system, dependencies
            )
            context['warnings'] = warnings
            
        except Exception as e:
            logger.error(f"Error loading dependencies: {e}")
            context['dependencies'] = {'has_dependencies': False}
            context['warnings'] = []
        
        context['breadcrumbs'] = [
            {'name': 'Catálogos', 'url': reverse('frontend:catalog_index')},
            {'name': 'Taxonomía', 'url': reverse('frontend:taxonomy_tree')},
            {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
            {'name': system.get('name', ''), 'url': reverse('frontend:taxonomy_system_detail', kwargs={'pk': system_id})},
            {'name': 'Eliminar', 'url': None}
        ]
        
        return context


# Vistas AJAX para funcionalidad dinámica

@method_decorator(csrf_exempt, name='dispatch')
class TaxonomyAjaxSearchView(LoginRequiredMixin, APIClientMixin, View):
    """Búsqueda AJAX en toda la taxonomía"""
    
    def get(self, request):
        try:
            query = request.GET.get('q', '').strip()
            if len(query) < 2:
                return JsonResponse({'results': []})
            
            # Buscar en todos los niveles de taxonomía
            results = self.api_client.get(
                'catalog/taxonomy/search/',
                params={'q': query, 'limit': 20}
            )
            
            return JsonResponse({
                'results': results.get('results', []),
                'total': results.get('count', 0)
            })
            
        except Exception as e:
            logger.error(f"Error in taxonomy AJAX search: {e}")
            return JsonResponse({'error': 'Error en la búsqueda'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaxonomyTreeDataView(LoginRequiredMixin, APIClientMixin, View):
    """API para obtener datos del árbol de taxonomía"""
    
    def get(self, request):
        try:
            node_id = request.GET.get('node_id')
            expand_level = int(request.GET.get('expand_level', 1))
            
            if node_id:
                # Obtener nodo específico con sus hijos
                data = self.api_client.get(
                    f'catalog/taxonomy/node/{node_id}/',
                    params={'expand_level': expand_level}
                )
            else:
                # Obtener árbol completo
                data = self.api_client.get(
                    'catalog/taxonomy/tree/',
                    params={'expand_level': expand_level}
                )
            
            return JsonResponse(data)
            
        except Exception as e:
            logger.error(f"Error loading taxonomy tree data: {e}")
            return JsonResponse({'error': 'Error al cargar datos'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaxonomyNodeActionView(LoginRequiredMixin, APIClientMixin, View):
    """Acciones AJAX sobre nodos de taxonomía"""
    
    def post(self, request):
        try:
            action = request.POST.get('action')
            node_id = request.POST.get('node_id')
            node_type = request.POST.get('node_type')
            
            if action == 'toggle_active':
                response = self.api_client.patch(
                    f'catalog/taxonomy/{node_type}s/{node_id}/toggle-active/'
                )
                return JsonResponse({
                    'success': True,
                    'is_active': response.get('is_active'),
                    'message': 'Estado actualizado exitosamente'
                })
            
            elif action == 'get_details':
                response = self.api_client.get(
                    f'catalog/taxonomy/{node_type}s/{node_id}/'
                )
                return JsonResponse({
                    'success': True,
                    'data': response
                })
            
            else:
                return JsonResponse({'error': 'Acción no válida'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in taxonomy node action: {e}")
            return JsonResponse({'error': 'Error al procesar la acción'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaxonomyBulkActionView(LoginRequiredMixin, APIClientMixin, View):
    """Vista para acciones masivas en taxonomía"""
    
    def post(self, request):
        try:
            action = request.POST.get('action')
            selected_ids = request.POST.get('selected_ids', '').split(',')
            selected_ids = [id.strip() for id in selected_ids if id.strip()]
            
            if not selected_ids:
                return JsonResponse({'error': 'No se seleccionaron elementos'}, status=400)
            
            if action == 'bulk-activate':
                return self._bulk_activate(selected_ids)
            elif action == 'bulk-deactivate':
                return self._bulk_deactivate(selected_ids)
            elif action == 'bulk-export':
                return self._bulk_export(selected_ids)
            elif action == 'bulk-delete':
                return self._bulk_delete(selected_ids)
            else:
                return JsonResponse({'error': 'Acción no válida'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in taxonomy bulk action: {e}")
            return JsonResponse({'error': 'Error al procesar la acción masiva'}, status=500)
    
    def _bulk_activate(self, selected_ids):
        """Activar sistemas seleccionados"""
        try:
            success_count = 0
            for system_id in selected_ids:
                try:
                    self.api_client.patch(f'taxonomy-systems/{system_id}/', {
                        'is_active': True
                    })
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error activating system {system_id}: {e}")
            
            return JsonResponse({
                'success': True,
                'message': f'{success_count} sistemas activados exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error in bulk activate: {e}")
            return JsonResponse({'error': 'Error al activar sistemas'}, status=500)
    
    def _bulk_deactivate(self, selected_ids):
        """Desactivar sistemas seleccionados"""
        try:
            success_count = 0
            for system_id in selected_ids:
                try:
                    self.api_client.patch(f'taxonomy-systems/{system_id}/', {
                        'is_active': False
                    })
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error deactivating system {system_id}: {e}")
            
            return JsonResponse({
                'success': True,
                'message': f'{success_count} sistemas desactivados exitosamente'
            })
            
        except Exception as e:
            logger.error(f"Error in bulk deactivate: {e}")
            return JsonResponse({'error': 'Error al desactivar sistemas'}, status=500)
    
    def _bulk_export(self, selected_ids):
        """Exportar sistemas seleccionados"""
        try:
            # Implementar lógica de exportación
            return JsonResponse({
                'success': True,
                'download_url': f'/api/v1/taxonomy-systems/export/?ids={",".join(selected_ids)}',
                'message': f'Exportando {len(selected_ids)} sistemas'
            })
            
        except Exception as e:
            logger.error(f"Error in bulk export: {e}")
            return JsonResponse({'error': 'Error al exportar sistemas'}, status=500)
    
    def _bulk_delete(self, selected_ids):
        """Eliminar sistemas seleccionados (con verificación de dependencias)"""
        try:
            # Verificar dependencias primero
            systems_with_dependencies = []
            systems_to_delete = []
            
            for system_id in selected_ids:
                try:
                    dependencies = self.api_client.get(
                        f'taxonomy-systems/{system_id}/dependencies/'
                    )
                    if dependencies.get('has_dependencies', False):
                        systems_with_dependencies.append(system_id)
                    else:
                        systems_to_delete.append(system_id)
                except Exception as e:
                    logger.error(f"Error checking dependencies for system {system_id}: {e}")
            
            # Eliminar solo los sistemas sin dependencias
            success_count = 0
            for system_id in systems_to_delete:
                try:
                    self.api_client.delete(f'taxonomy-systems/{system_id}/')
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error deleting system {system_id}: {e}")
            
            message = f'{success_count} sistemas eliminados exitosamente'
            if systems_with_dependencies:
                message += f'. {len(systems_with_dependencies)} sistemas no se pudieron eliminar por tener dependencias'
            
            return JsonResponse({
                'success': True,
                'message': message,
                'systems_with_dependencies': systems_with_dependencies
            })
            
        except Exception as e:
            logger.error(f"Error in bulk delete: {e}")
            return JsonResponse({'error': 'Error al eliminar sistemas'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TaxonomyValidateCodeView(LoginRequiredMixin, APIClientMixin, View):
    """Validación AJAX de códigos de taxonomía"""
    
    def post(self, request):
        try:
            import json
            data = json.loads(request.body)
            code = data.get('code', '').strip().upper()
            taxonomy_type = data.get('type', 'system')  # system, subsystem, group
            exclude_id = data.get('exclude_id')
            
            if not code:
                return JsonResponse({'is_unique': False, 'error': 'Código requerido'})
            
            # Determinar endpoint según el tipo
            endpoint_map = {
                'system': 'taxonomy-systems/',
                'subsystem': 'taxonomy-subsystems/',
                'group': 'taxonomy-groups/'
            }
            
            endpoint = endpoint_map.get(taxonomy_type)
            if not endpoint:
                return JsonResponse({'is_unique': False, 'error': 'Tipo no válido'})
            
            # Buscar código existente
            params = {'code': code}
            response = self.api_client.get(endpoint, params=params)
            results = response.get('results', [])
            
            # Verificar unicidad
            is_unique = True
            if results:
                # Si estamos editando, excluir el elemento actual
                # Para taxonomy systems, el ID es el system_code (string)
                # Para otros tipos, puede ser un ID numérico
                if exclude_id:
                    results = [r for r in results if str(r.get('id')) != str(exclude_id) and str(r.get('system_code')) != str(exclude_id)]
                is_unique = len(results) == 0
            
            return JsonResponse({
                'is_unique': is_unique,
                'code': code,
                'type': taxonomy_type
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'is_unique': False, 'error': 'Datos inválidos'})
        except Exception as e:
            logger.error(f"Error validating taxonomy code: {e}")
            return JsonResponse({'is_unique': False, 'error': 'Error del servidor'})



# ============================================================================
# VISTAS PARA SUBSISTEMAS DE TAXONOMÍA
# ============================================================================

class TaxonomySubsystemListView(LoginRequiredMixin, APIClientMixin, ListView):
    """Lista de subsistemas de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_subsystem_list.html'
    context_object_name = 'subsystems'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            system_id = self.kwargs.get('system_id')
            search = self.request.GET.get('search', '')
            
            params = {}
            if system_id:
                params['system_code'] = system_id
            if search:
                params['search'] = search
            
            response = self.api_client.get('taxonomy-subsystems/', params=params)
            return response.get('results', [])
            
        except Exception as e:
            logger.error(f"Error loading taxonomy subsystems: {e}")
            messages.error(self.request, "Error al cargar los subsistemas de taxonomía.")
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system_id = self.kwargs.get('system_id')
        
        if system_id:
            try:
                system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                context['system'] = system
                context['system_id'] = system_id
            except Exception as e:
                logger.error(f"Error loading system: {e}")
        
        context['search_form'] = TaxonomySearchForm(self.request.GET)
        context['current_search'] = self.request.GET.get('search', '')
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'subsystem_list',
            {'system': context.get('system', {}), 'system_id': system_id}
        )
        
        return context


class TaxonomySubsystemCreateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Crear nuevo subsistema de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_subsystem_form.html'
    form_class = TaxonomySubsystemForm
    
    def get_success_url(self):
        system_id = self.kwargs.get('system_id')
        if system_id:
            return reverse('frontend:taxonomy_subsystem_list', kwargs={'system_id': system_id})
        return reverse('frontend:taxonomy_tree')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system_id = self.kwargs.get('system_id')
        context['system_id'] = system_id
        context['title'] = 'Crear Nuevo Subsistema'
        
        # Obtener información del sistema padre
        if system_id:
            try:
                system_data = self.api_client.get(f'taxonomy-systems/{system_id}/')
                context['system'] = system_data
            except Exception as e:
                logger.warning(f"Could not fetch system data: {e}")
                context['system'] = {'system_code': system_id, 'name_es': system_id}
        
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        system_id = self.kwargs.get('system_id')
        if system_id:
            initial['system'] = system_id
        return initial
    
    def form_valid(self, form):
        try:
            data = form.cleaned_data
            system_id = self.kwargs.get('system_id') or data.get('system')
            
            # Preparar datos para validación (mapeo de campos)
            # NOTA: Validación temporalmente desactivada para pruebas
            # validation_data = {
            #     'code': data.get('subsystem_code', ''),
            #     'name': data.get('name_es', ''),
            #     'parent_id': system_id
            # }
            
            # Validar con el sistema de validación - TEMPORALMENTE DESACTIVADA
            # validator = TaxonomyValidator(self.api_client)
            # is_valid, errors = validator.validate_before_save('subsystem', validation_data)
            
            # if not is_valid:
            #     for error in errors:
            #         form.add_error(None, error)
            #     return self.form_invalid(form)
            
            # TODO: Reactivar validación después de solucionar el problema
            pass  # Continuar sin validación
            
            # Preparar datos para el API
            api_data = {
                'system_code': system_id,
                'subsystem_code': data['subsystem_code'],
                'name_es': data['name_es'],
                'name_en': data.get('name_en', ''),
                'icon': data.get('icon', ''),
                'notes': data.get('scope', ''),
                'sort_order': data.get('sort_order', 0)
            }
            
            response = self.api_client.post('taxonomy-subsystems/', api_data)
            
            messages.success(
                self.request,
                f"Subsistema '{data['name_es']}' creado exitosamente."
            )
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Error creating taxonomy subsystem: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            error_msg = str(e)
            if hasattr(e, 'response'):
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg} - Detalle: {error_detail}"
                except:
                    error_msg = f"{error_msg} - Status: {e.response.status_code}"
            
            messages.error(self.request, f"Error al crear el subsistema: {error_msg}")
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system_id = self.kwargs.get('system_id')
        
        if system_id:
            try:
                system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                context['system'] = system
                context['system_id'] = system_id
            except Exception as e:
                logger.error(f"Error loading system: {e}")
        
        context['title'] = 'Crear Subsistema de Taxonomía'
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'subsystem_create',
            {'system': context.get('system', {}), 'system_id': system_id}
        )
        
        return context


class TaxonomySubsystemUpdateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Editar subsistema de taxonomía existente"""
    template_name = 'frontend/catalog/taxonomy_subsystem_form.html'
    form_class = TaxonomySubsystemForm
    
    def get_success_url(self):
        system_id = self.kwargs.get('system_id')
        if system_id:
            return reverse('frontend:taxonomy_subsystem_list', kwargs={'system_id': system_id})
        return reverse('frontend:taxonomy_tree')
    
    def get_object(self):
        subsystem_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy subsystem {subsystem_id}: {e}")
            raise Http404("Subsistema de taxonomía no encontrado")
    
    def get_initial(self):
        obj = self.get_object()
        return {
            'system': obj.get('system_code'),  # El API retorna system_code
            'subsystem_code': obj.get('subsystem_code', ''),
            'name_es': obj.get('name_es', ''),
            'name_en': obj.get('name_en', ''),
            'icon': obj.get('icon', ''),
            'scope': obj.get('notes', ''),  # API usa 'notes', formulario usa 'scope'
            'sort_order': obj.get('sort_order', 0),
            'is_active': obj.get('is_active', True)
        }
    
    def form_valid(self, form):
        subsystem_id = self.kwargs['pk']
        try:
            data = form.cleaned_data
            
            # Validar con el sistema de validación
            validator = TaxonomyValidator(self.api_client)
            is_valid, errors = validator.validate_before_save('subsystem', data, subsystem_id)
            
            if not is_valid:
                for error in errors:
                    form.add_error(None, error)
                return self.form_invalid(form)
            
            # Preparar datos para el API
            api_data = {
                'system_code': data.get('system'),
                'subsystem_code': data['subsystem_code'],
                'name_es': data['name_es'],
                'name_en': data.get('name_en', ''),
                'icon': data.get('icon', ''),
                'notes': data.get('scope', ''),  # Form usa 'scope', API usa 'notes'
                'sort_order': data.get('sort_order', 0)
            }
            
            response = self.api_client.put(
                f'taxonomy-subsystems/{subsystem_id}/',
                api_data
            )
            
            messages.success(
                self.request,
                f"Subsistema '{data['name_es']}' actualizado exitosamente."
            )
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Error updating taxonomy subsystem {subsystem_id}: {e}")
            if hasattr(e, 'response') and e.response.status_code == 400:
                api_errors = e.response.json()
                for field, errors in api_errors.items():
                    if field in form.fields:
                        form.add_error(field, errors)
                    else:
                        form.add_error(None, f"{field}: {errors}")
            else:
                messages.error(self.request, "Error al actualizar el subsistema de taxonomía.")
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        system_id = self.kwargs.get('system_id') or obj.get('system')
        
        if system_id:
            try:
                system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                context['system'] = system
                context['system_id'] = system_id
            except Exception as e:
                logger.error(f"Error loading system: {e}")
        
        context['title'] = f'Editar Subsistema: {obj.get("name", "")}'
        context['object'] = obj
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'subsystem_edit',
            {'system': context.get('system', {}), 'system_id': system_id, 'subsystem': obj}
        )
        
        return context


class TaxonomySubsystemDetailView(LoginRequiredMixin, APIClientMixin, DetailView):
    """Vista detallada de subsistema de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_subsystem_detail.html'
    context_object_name = 'subsystem'
    
    def get_object(self):
        subsystem_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy subsystem {subsystem_id}: {e}")
            raise Http404("Subsistema de taxonomía no encontrado")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subsystem = self.get_object()
        subsystem_id = self.kwargs['pk']
        system_id = subsystem.get('system')
        
        try:
            # Obtener sistema padre
            if system_id:
                system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                context['system'] = system
                context['system_id'] = system_id
            
            # Obtener grupos del subsistema
            groups = self.api_client.get(
                'taxonomy-groups/',
                params={'subsystem': subsystem_id}
            )
            context['groups'] = groups.get('results', [])
            
            # Estadísticas del subsistema
            stats = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/stats/')
            context['subsystem_stats'] = stats
            
        except Exception as e:
            logger.error(f"Error loading subsystem details: {e}")
            context['groups'] = []
            context['subsystem_stats'] = {}
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'subsystem_detail',
            {
                'system': context.get('system', {}),
                'system_id': system_id,
                'subsystem': subsystem,
                'subsystem_id': subsystem_id
            }
        )
        
        return context


class TaxonomySubsystemDeleteView(LoginRequiredMixin, APIClientMixin, DeleteView):
    """Eliminar subsistema de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_subsystem_confirm_delete.html'
    
    def get_success_url(self):
        system_id = self.kwargs.get('system_id')
        if system_id:
            return reverse('frontend:taxonomy_subsystem_list', kwargs={'system_id': system_id})
        return reverse('frontend:taxonomy_tree')
    
    def get_object(self):
        subsystem_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy subsystem {subsystem_id}: {e}")
            raise Http404("Subsistema de taxonomía no encontrado")
    
    def delete(self, request, *args, **kwargs):
        subsystem_id = self.kwargs['pk']
        subsystem = self.get_object()
        system_id = subsystem.get('system')
        
        try:
            # Verificar dependencias con el validador
            validator = TaxonomyValidator(self.api_client)
            dependencies = validator.check_dependencies('subsystem', subsystem_id)
            
            if dependencies.get('has_dependencies', False):
                messages.error(
                    request,
                    f"No se puede eliminar el subsistema '{subsystem['name']}' porque tiene dependencias."
                )
                return redirect('frontend:taxonomy_subsystem_detail', pk=subsystem_id, system_id=system_id)
            
            # Proceder con la eliminación
            self.api_client.delete(f'taxonomy-subsystems/{subsystem_id}/')
            
            messages.success(
                request,
                f"Subsistema '{subsystem['name']}' eliminado exitosamente."
            )
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Error deleting taxonomy subsystem {subsystem_id}: {e}")
            messages.error(request, "Error al eliminar el subsistema de taxonomía.")
            return redirect('frontend:taxonomy_subsystem_detail', pk=subsystem_id, system_id=system_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subsystem = self.get_object()
        subsystem_id = self.kwargs['pk']
        system_id = subsystem.get('system')
        
        try:
            # Obtener sistema padre
            if system_id:
                system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                context['system'] = system
                context['system_id'] = system_id
            
            # Obtener información de dependencias con validador
            validator = TaxonomyValidator(self.api_client)
            dependencies = validator.check_dependencies('subsystem', subsystem_id)
            context['dependencies'] = dependencies
            
            # Generar advertencias
            warnings = TaxonomyWarningSystem.get_deletion_warnings(
                'subsystem', subsystem, dependencies
            )
            context['warnings'] = warnings
            
        except Exception as e:
            logger.error(f"Error loading dependencies: {e}")
            context['dependencies'] = {'has_dependencies': False}
            context['warnings'] = []
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'subsystem_delete',
            {
                'system': context.get('system', {}),
                'system_id': system_id,
                'subsystem': subsystem,
                'subsystem_id': subsystem_id
            }
        )
        
        return context



# ============================================================================
# VISTAS PARA GRUPOS DE TAXONOMÍA
# ============================================================================

class TaxonomyGroupListView(LoginRequiredMixin, APIClientMixin, ListView):
    """Lista de grupos de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_group_list.html'
    context_object_name = 'groups'
    paginate_by = 20
    
    def get_queryset(self):
        try:
            subsystem_id = self.kwargs.get('subsystem_id')
            search = self.request.GET.get('search', '')
            is_active = self.request.GET.get('is_active', '')
            
            params = {}
            if subsystem_id:
                params['subsystem'] = subsystem_id
            if search:
                params['search'] = search
            if is_active:
                params['is_active'] = is_active
            
            response = self.api_client.get('taxonomy-groups/', params=params)
            return response.get('results', [])
            
        except Exception as e:
            logger.error(f"Error loading taxonomy groups: {e}")
            messages.error(self.request, "Error al cargar los grupos de taxonomía.")
            return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subsystem_id = self.kwargs.get('subsystem_id')
        
        if subsystem_id:
            try:
                subsystem = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
                context['subsystem'] = subsystem
                context['subsystem_id'] = subsystem_id
                
                system_id = subsystem.get('system')
                if system_id:
                    system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                    context['system'] = system
                    context['system_id'] = system_id
            except Exception as e:
                logger.error(f"Error loading subsystem: {e}")
        
        context['search_form'] = TaxonomySearchForm(self.request.GET)
        context['current_search'] = self.request.GET.get('search', '')
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'group_list',
            {
                'system': context.get('system', {}),
                'system_id': context.get('system_id'),
                'subsystem': context.get('subsystem', {}),
                'subsystem_id': subsystem_id
            }
        )
        
        return context


class TaxonomyGroupCreateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Crear nuevo grupo de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_group_form.html'
    form_class = TaxonomyGroupForm
    
    def get_success_url(self):
        subsystem_id = self.kwargs.get('subsystem_id')
        if subsystem_id:
            return reverse('frontend:taxonomy_group_list', kwargs={'subsystem_id': subsystem_id})
        return reverse('frontend:taxonomy_tree')
    
    def get_initial(self):
        initial = super().get_initial()
        subsystem_id = self.kwargs.get('subsystem_id')
        if subsystem_id:
            initial['subsystem'] = subsystem_id
        return initial
    
    def form_valid(self, form):
        try:
            data = form.cleaned_data
            subsystem_id = self.kwargs.get('subsystem_id') or data.get('subsystem')
            
            # Validar con el sistema de validación
            validator = TaxonomyValidator(self.api_client)
            is_valid, errors = validator.validate_before_save('group', data)
            
            if not is_valid:
                for error in errors:
                    form.add_error(None, error)
                return self.form_invalid(form)
            
            # Preparar datos para el API
            api_data = {
                'subsystem': subsystem_id,
                'code': data['code'],
                'name': data['name'],
                'description': data.get('description', ''),
                'sort_order': data.get('sort_order', 0),
                'is_active': data.get('is_active', True)
            }
            
            response = self.api_client.post('taxonomy-groups/', api_data)
            
            messages.success(
                self.request,
                f"Grupo '{data['name']}' creado exitosamente."
            )
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Error creating taxonomy group: {e}")
            if hasattr(e, 'response') and e.response.status_code == 400:
                api_errors = e.response.json()
                for field, errors in api_errors.items():
                    if field in form.fields:
                        form.add_error(field, errors)
                    else:
                        form.add_error(None, f"{field}: {errors}")
            else:
                messages.error(self.request, "Error al crear el grupo de taxonomía.")
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subsystem_id = self.kwargs.get('subsystem_id')
        
        if subsystem_id:
            try:
                subsystem = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
                context['subsystem'] = subsystem
                context['subsystem_id'] = subsystem_id
                
                system_id = subsystem.get('system')
                if system_id:
                    system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                    context['system'] = system
                    context['system_id'] = system_id
            except Exception as e:
                logger.error(f"Error loading subsystem: {e}")
        
        context['title'] = 'Crear Grupo de Taxonomía'
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'group_create',
            {
                'system': context.get('system', {}),
                'system_id': context.get('system_id'),
                'subsystem': context.get('subsystem', {}),
                'subsystem_id': subsystem_id
            }
        )
        
        return context


class TaxonomyGroupUpdateView(LoginRequiredMixin, APIClientMixin, FormView):
    """Editar grupo de taxonomía existente"""
    template_name = 'frontend/catalog/taxonomy_group_form.html'
    form_class = TaxonomyGroupForm
    
    def get_success_url(self):
        subsystem_id = self.kwargs.get('subsystem_id')
        if subsystem_id:
            return reverse('frontend:taxonomy_group_list', kwargs={'subsystem_id': subsystem_id})
        return reverse('frontend:taxonomy_tree')
    
    def get_object(self):
        group_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-groups/{group_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy group {group_id}: {e}")
            raise Http404("Grupo de taxonomía no encontrado")
    
    def get_initial(self):
        obj = self.get_object()
        return {
            'subsystem': obj.get('subsystem'),
            'code': obj.get('code', ''),
            'name': obj.get('name', ''),
            'description': obj.get('description', ''),
            'sort_order': obj.get('sort_order', 0),
            'is_active': obj.get('is_active', True)
        }
    
    def form_valid(self, form):
        group_id = self.kwargs['pk']
        try:
            data = form.cleaned_data
            
            # Validar con el sistema de validación
            validator = TaxonomyValidator(self.api_client)
            is_valid, errors = validator.validate_before_save('group', data, group_id)
            
            if not is_valid:
                for error in errors:
                    form.add_error(None, error)
                return self.form_invalid(form)
            
            # Preparar datos para el API
            api_data = {
                'subsystem': data.get('subsystem'),
                'code': data['code'],
                'name': data['name'],
                'description': data.get('description', ''),
                'sort_order': data.get('sort_order', 0),
                'is_active': data.get('is_active', True)
            }
            
            response = self.api_client.put(
                f'taxonomy-groups/{group_id}/',
                api_data
            )
            
            messages.success(
                self.request,
                f"Grupo '{data['name']}' actualizado exitosamente."
            )
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Error updating taxonomy group {group_id}: {e}")
            if hasattr(e, 'response') and e.response.status_code == 400:
                api_errors = e.response.json()
                for field, errors in api_errors.items():
                    if field in form.fields:
                        form.add_error(field, errors)
                    else:
                        form.add_error(None, f"{field}: {errors}")
            else:
                messages.error(self.request, "Error al actualizar el grupo de taxonomía.")
            
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        subsystem_id = self.kwargs.get('subsystem_id') or obj.get('subsystem')
        
        if subsystem_id:
            try:
                subsystem = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
                context['subsystem'] = subsystem
                context['subsystem_id'] = subsystem_id
                
                system_id = subsystem.get('system')
                if system_id:
                    system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                    context['system'] = system
                    context['system_id'] = system_id
            except Exception as e:
                logger.error(f"Error loading subsystem: {e}")
        
        context['title'] = f'Editar Grupo: {obj.get("name", "")}'
        context['object'] = obj
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'group_edit',
            {
                'system': context.get('system', {}),
                'system_id': context.get('system_id'),
                'subsystem': context.get('subsystem', {}),
                'subsystem_id': subsystem_id,
                'group': obj
            }
        )
        
        return context


class TaxonomyGroupDetailView(LoginRequiredMixin, APIClientMixin, DetailView):
    """Vista detallada de grupo de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_group_detail.html'
    context_object_name = 'group'
    
    def get_object(self):
        group_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-groups/{group_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy group {group_id}: {e}")
            raise Http404("Grupo de taxonomía no encontrado")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        group_id = self.kwargs['pk']
        subsystem_id = group.get('subsystem')
        
        try:
            # Obtener subsistema padre
            if subsystem_id:
                subsystem = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
                context['subsystem'] = subsystem
                context['subsystem_id'] = subsystem_id
                
                system_id = subsystem.get('system')
                if system_id:
                    system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                    context['system'] = system
                    context['system_id'] = system_id
            
            # Estadísticas del grupo
            stats = self.api_client.get(f'taxonomy-groups/{group_id}/stats/')
            context['group_stats'] = stats
            
        except Exception as e:
            logger.error(f"Error loading group details: {e}")
            context['group_stats'] = {}
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'group_detail',
            {
                'system': context.get('system', {}),
                'system_id': context.get('system_id'),
                'subsystem': context.get('subsystem', {}),
                'subsystem_id': subsystem_id,
                'group': group,
                'group_id': group_id
            }
        )
        
        return context


class TaxonomyGroupDeleteView(LoginRequiredMixin, APIClientMixin, DeleteView):
    """Eliminar grupo de taxonomía"""
    template_name = 'frontend/catalog/taxonomy_group_confirm_delete.html'
    
    def get_success_url(self):
        subsystem_id = self.kwargs.get('subsystem_id')
        if subsystem_id:
            return reverse('frontend:taxonomy_group_list', kwargs={'subsystem_id': subsystem_id})
        return reverse('frontend:taxonomy_tree')
    
    def get_object(self):
        group_id = self.kwargs['pk']
        try:
            response = self.api_client.get(f'taxonomy-groups/{group_id}/')
            return response
        except Exception as e:
            logger.error(f"Error loading taxonomy group {group_id}: {e}")
            raise Http404("Grupo de taxonomía no encontrado")
    
    def delete(self, request, *args, **kwargs):
        group_id = self.kwargs['pk']
        group = self.get_object()
        subsystem_id = group.get('subsystem')
        
        try:
            # Verificar dependencias con el validador
            validator = TaxonomyValidator(self.api_client)
            dependencies = validator.check_dependencies('group', group_id)
            
            if dependencies.get('has_dependencies', False):
                messages.error(
                    request,
                    f"No se puede eliminar el grupo '{group['name']}' porque tiene dependencias."
                )
                return redirect('frontend:taxonomy_group_detail', pk=group_id, subsystem_id=subsystem_id)
            
            # Proceder con la eliminación
            self.api_client.delete(f'taxonomy-groups/{group_id}/')
            
            messages.success(
                request,
                f"Grupo '{group['name']}' eliminado exitosamente."
            )
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Error deleting taxonomy group {group_id}: {e}")
            messages.error(request, "Error al eliminar el grupo de taxonomía.")
            return redirect('frontend:taxonomy_group_detail', pk=group_id, subsystem_id=subsystem_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        group_id = self.kwargs['pk']
        subsystem_id = group.get('subsystem')
        
        try:
            # Obtener subsistema padre
            if subsystem_id:
                subsystem = self.api_client.get(f'taxonomy-subsystems/{subsystem_id}/')
                context['subsystem'] = subsystem
                context['subsystem_id'] = subsystem_id
                
                system_id = subsystem.get('system')
                if system_id:
                    system = self.api_client.get(f'taxonomy-systems/{system_id}/')
                    context['system'] = system
                    context['system_id'] = system_id
            
            # Obtener información de dependencias con validador
            validator = TaxonomyValidator(self.api_client)
            dependencies = validator.check_dependencies('group', group_id)
            context['dependencies'] = dependencies
            
            # Generar advertencias
            warnings = TaxonomyWarningSystem.get_deletion_warnings(
                'group', group, dependencies
            )
            context['warnings'] = warnings
            
        except Exception as e:
            logger.error(f"Error loading dependencies: {e}")
            context['dependencies'] = {'has_dependencies': False}
            context['warnings'] = []
        
        # Breadcrumbs
        from ..utils.navigation import BreadcrumbBuilder
        context['breadcrumbs'] = BreadcrumbBuilder.build_taxonomy_breadcrumbs(
            'group_delete',
            {
                'system': context.get('system', {}),
                'system_id': context.get('system_id'),
                'subsystem': context.get('subsystem', {}),
                'subsystem_id': subsystem_id,
                'group': group,
                'group_id': group_id
            }
        )
        
        return context
