"""
Sistema de navegación contextual y breadcrumbs para ForgeDB
"""

from typing import List, Dict, Optional
from django.urls import reverse


class BreadcrumbBuilder:
    """Constructor de breadcrumbs dinámicos"""
    
    @staticmethod
    def build_taxonomy_breadcrumbs(current_page: str, 
                                   context_data: Optional[Dict] = None) -> List[Dict]:
        """
        Construye breadcrumbs para el módulo de taxonomía
        
        Args:
            current_page: Página actual (tree, system_list, system_detail, etc.)
            context_data: Datos contextuales (sistema, subsistema, etc.)
            
        Returns:
            List[Dict]: Lista de breadcrumbs con name y url
        """
        breadcrumbs = [
            {'name': 'Catálogos', 'url': reverse('frontend:catalog_index'), 'icon': 'house'}
        ]
        
        # Agregar breadcrumb de taxonomía
        if current_page != 'tree':
            breadcrumbs.append({
                'name': 'Taxonomía',
                'url': reverse('frontend:taxonomy_tree'),
                'icon': 'diagram-3'
            })
        
        # Breadcrumbs específicos según la página
        if current_page == 'tree':
            breadcrumbs.append({
                'name': 'Árbol de Taxonomía',
                'url': None,
                'icon': 'diagram-3'
            })
        
        elif current_page == 'system_list':
            breadcrumbs.append({
                'name': 'Sistemas',
                'url': None,
                'icon': 'diagram-2'
            })
        
        elif current_page == 'system_create':
            breadcrumbs.extend([
                {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
                {'name': 'Crear', 'url': None, 'icon': 'plus-circle'}
            ])
        
        elif current_page == 'system_detail' and context_data:
            system = context_data.get('system', {})
            breadcrumbs.extend([
                {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
                {'name': system.get('name', 'Detalle'), 'url': None, 'icon': 'eye'}
            ])
        
        elif current_page == 'system_edit' and context_data:
            system = context_data.get('system', {})
            system_id = context_data.get('system_id')
            breadcrumbs.extend([
                {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
                {
                    'name': system.get('name', 'Sistema'),
                    'url': reverse('frontend:taxonomy_system_detail', kwargs={'pk': system_id}) if system_id else None
                },
                {'name': 'Editar', 'url': None, 'icon': 'pencil'}
            ])
        
        elif current_page == 'system_delete' and context_data:
            system = context_data.get('system', {})
            system_id = context_data.get('system_id')
            breadcrumbs.extend([
                {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
                {
                    'name': system.get('name', 'Sistema'),
                    'url': reverse('frontend:taxonomy_system_detail', kwargs={'pk': system_id}) if system_id else None
                },
                {'name': 'Eliminar', 'url': None, 'icon': 'trash'}
            ])
        
        elif current_page == 'subsystem_list' and context_data:
            system = context_data.get('system', {})
            system_id = context_data.get('system_id')
            breadcrumbs.extend([
                {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
                {
                    'name': system.get('name', 'Sistema'),
                    'url': reverse('frontend:taxonomy_system_detail', kwargs={'pk': system_id}) if system_id else None
                },
                {'name': 'Subsistemas', 'url': None, 'icon': 'diagram-2'}
            ])
        
        elif current_page == 'group_list' and context_data:
            system = context_data.get('system', {})
            subsystem = context_data.get('subsystem', {})
            system_id = context_data.get('system_id')
            subsystem_id = context_data.get('subsystem_id')
            
            breadcrumbs.extend([
                {'name': 'Sistemas', 'url': reverse('frontend:taxonomy_system_list')},
                {
                    'name': system.get('name', 'Sistema'),
                    'url': reverse('frontend:taxonomy_system_detail', kwargs={'pk': system_id}) if system_id else None
                },
                {
                    'name': subsystem.get('name', 'Subsistema'),
                    'url': f'/catalog/taxonomy/subsystems/{subsystem_id}/' if subsystem_id else None
                },
                {'name': 'Grupos', 'url': None, 'icon': 'collection'}
            ])
        
        return breadcrumbs
    
    @staticmethod
    def build_catalog_breadcrumbs(current_page: str,
                                  context_data: Optional[Dict] = None) -> List[Dict]:
        """
        Construye breadcrumbs para el módulo de catálogos
        
        Args:
            current_page: Página actual
            context_data: Datos contextuales
            
        Returns:
            List[Dict]: Lista de breadcrumbs
        """
        breadcrumbs = [
            {'name': 'Catálogos', 'url': reverse('frontend:catalog_index'), 'icon': 'house'}
        ]
        
        if current_page == 'equipment_type_list':
            breadcrumbs.append({
                'name': 'Tipos de Equipo',
                'url': None,
                'icon': 'gear'
            })
        
        elif current_page == 'equipment_type_create':
            breadcrumbs.extend([
                {'name': 'Tipos de Equipo', 'url': reverse('frontend:equipment_type_list')},
                {'name': 'Crear', 'url': None, 'icon': 'plus-circle'}
            ])
        
        # Agregar más páginas según sea necesario
        
        return breadcrumbs


class NavigationContext:
    """Contexto de navegación para acciones rápidas"""
    
    @staticmethod
    def get_taxonomy_quick_actions(current_page: str, 
                                   context_data: Optional[Dict] = None) -> List[Dict]:
        """
        Obtiene acciones rápidas para el módulo de taxonomía
        
        Args:
            current_page: Página actual
            context_data: Datos contextuales
            
        Returns:
            List[Dict]: Lista de acciones rápidas
        """
        actions = []
        
        # Acciones comunes
        common_actions = [
            {
                'name': 'Vista de Árbol',
                'url': reverse('frontend:taxonomy_tree'),
                'icon': 'diagram-3',
                'class': 'btn-outline-primary'
            },
            {
                'name': 'Lista de Sistemas',
                'url': reverse('frontend:taxonomy_system_list'),
                'icon': 'list',
                'class': 'btn-outline-secondary'
            }
        ]
        
        # Acciones específicas según la página
        if current_page == 'system_list':
            actions.append({
                'name': 'Nuevo Sistema',
                'url': reverse('frontend:taxonomy_system_create'),
                'icon': 'plus-circle',
                'class': 'btn-primary'
            })
        
        elif current_page == 'system_detail' and context_data:
            system_id = context_data.get('system_id')
            if system_id:
                actions.extend([
                    {
                        'name': 'Editar',
                        'url': reverse('frontend:taxonomy_system_edit', kwargs={'pk': system_id}),
                        'icon': 'pencil',
                        'class': 'btn-primary'
                    },
                    {
                        'name': 'Eliminar',
                        'url': reverse('frontend:taxonomy_system_delete', kwargs={'pk': system_id}),
                        'icon': 'trash',
                        'class': 'btn-outline-danger'
                    }
                ])
        
        # Agregar acciones comunes al final
        actions.extend(common_actions)
        
        return actions
    
    @staticmethod
    def get_navigation_history(request) -> List[Dict]:
        """
        Obtiene el historial de navegación del usuario
        
        Args:
            request: Request de Django
            
        Returns:
            List[Dict]: Historial de navegación
        """
        # Obtener historial de la sesión
        history = request.session.get('navigation_history', [])
        
        # Limitar a las últimas 10 páginas
        return history[-10:] if len(history) > 10 else history
    
    @staticmethod
    def add_to_navigation_history(request, page_data: Dict):
        """
        Agrega una página al historial de navegación
        
        Args:
            request: Request de Django
            page_data: Datos de la página (name, url, timestamp)
        """
        history = request.session.get('navigation_history', [])
        
        # Evitar duplicados consecutivos
        if history and history[-1].get('url') == page_data.get('url'):
            return
        
        history.append(page_data)
        
        # Limitar tamaño del historial
        if len(history) > 20:
            history = history[-20:]
        
        request.session['navigation_history'] = history
        request.session.modified = True


class NavigationHelper:
    """Helper para navegación contextual"""
    
    @staticmethod
    def get_related_pages(current_page: str, context_data: Optional[Dict] = None) -> List[Dict]:
        """
        Obtiene páginas relacionadas con la actual
        
        Args:
            current_page: Página actual
            context_data: Datos contextuales
            
        Returns:
            List[Dict]: Lista de páginas relacionadas
        """
        related = []
        
        if current_page == 'system_detail' and context_data:
            system_id = context_data.get('system_id')
            if system_id:
                related.extend([
                    {
                        'name': 'Subsistemas de este Sistema',
                        'url': f'/catalog/taxonomy/systems/{system_id}/subsystems/',
                        'icon': 'diagram-2',
                        'description': 'Ver y gestionar subsistemas'
                    },
                    {
                        'name': 'Equipos con esta Taxonomía',
                        'url': f'/equipment/?taxonomy_system={system_id}',
                        'icon': 'gear',
                        'description': 'Ver equipos asociados'
                    }
                ])
        
        return related
    
    @staticmethod
    def get_keyboard_shortcuts() -> List[Dict]:
        """
        Obtiene atajos de teclado disponibles
        
        Returns:
            List[Dict]: Lista de atajos de teclado
        """
        return [
            {'key': 'Ctrl + N', 'action': 'Crear nuevo elemento', 'context': 'Listas'},
            {'key': 'Ctrl + E', 'action': 'Editar elemento actual', 'context': 'Detalle'},
            {'key': 'Ctrl + S', 'action': 'Guardar cambios', 'context': 'Formularios'},
            {'key': 'Ctrl + K', 'action': 'Búsqueda rápida', 'context': 'Global'},
            {'key': 'Esc', 'action': 'Cancelar/Cerrar', 'context': 'Modales'},
            {'key': 'Alt + ←', 'action': 'Página anterior', 'context': 'Global'},
            {'key': 'Alt + →', 'action': 'Página siguiente', 'context': 'Global'}
        ]
