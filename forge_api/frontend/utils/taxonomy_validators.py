"""
Utilidades de validación para el sistema de taxonomía jerárquica
Incluye validaciones de integridad referencial y detección de referencias circulares
"""

import logging
from typing import Dict, List, Set, Optional, Tuple

logger = logging.getLogger(__name__)


class TaxonomyValidator:
    """Validador de integridad para taxonomía jerárquica"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def validate_hierarchy(self, parent_type: str, parent_id: int, 
                          child_type: str) -> Tuple[bool, Optional[str]]:
        """
        Valida que la jerarquía sea válida según las reglas del sistema
        
        Args:
            parent_type: Tipo del padre (system, subsystem)
            parent_id: ID del padre
            child_type: Tipo del hijo (subsystem, group)
            
        Returns:
            Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
        """
        # Jerarquías válidas
        valid_hierarchies = {
            'system': ['subsystem'],
            'subsystem': ['group']
        }
        
        if parent_type not in valid_hierarchies:
            return False, f"Tipo de padre inválido: {parent_type}"
        
        if child_type not in valid_hierarchies[parent_type]:
            return False, f"No se puede agregar {child_type} a {parent_type}"
        
        return True, None
    
    def check_circular_reference(self, node_type: str, node_id: int, 
                                 parent_id: int) -> Tuple[bool, Optional[str]]:
        """
        Detecta referencias circulares en la jerarquía
        
        Args:
            node_type: Tipo del nodo (subsystem, group)
            node_id: ID del nodo que se está editando
            parent_id: ID del nuevo padre propuesto
            
        Returns:
            Tuple[bool, Optional[str]]: (tiene_circular, mensaje_error)
        """
        try:
            # Obtener todos los descendientes del nodo actual
            descendants = self._get_all_descendants(node_type, node_id)
            
            # Si el nuevo padre está en los descendientes, hay referencia circular
            if parent_id in descendants:
                return True, "Referencia circular detectada: el padre propuesto es descendiente de este nodo"
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking circular reference: {e}")
            return False, "Error al verificar referencias circulares"
    
    def _get_all_descendants(self, node_type: str, node_id: int) -> Set[int]:
        """
        Obtiene recursivamente todos los descendientes de un nodo
        
        Args:
            node_type: Tipo del nodo
            node_id: ID del nodo
            
        Returns:
            Set[int]: Conjunto de IDs de todos los descendientes
        """
        descendants = set()
        
        try:
            # Determinar el tipo de hijos según el tipo de nodo
            if node_type == 'system':
                child_type = 'subsystem'
                endpoint = '/api/v1/catalog/taxonomy-subsystems/'
                parent_param = 'system'
            elif node_type == 'subsystem':
                child_type = 'group'
                endpoint = '/api/v1/catalog/taxonomy-groups/'
                parent_param = 'subsystem'
            else:
                return descendants
            
            # Obtener hijos directos
            response = self.api_client.get(endpoint, params={parent_param: node_id})
            children = response.get('results', [])
            
            # Agregar hijos y obtener sus descendientes recursivamente
            for child in children:
                child_id = child.get('id')
                if child_id:
                    descendants.add(child_id)
                    # Recursión para obtener descendientes del hijo
                    child_descendants = self._get_all_descendants(child_type, child_id)
                    descendants.update(child_descendants)
            
        except Exception as e:
            logger.error(f"Error getting descendants for {node_type} {node_id}: {e}")
        
        return descendants
    
    def check_dependencies(self, node_type: str, node_id: int) -> Dict:
        """
        Verifica todas las dependencias de un nodo antes de eliminarlo
        
        Args:
            node_type: Tipo del nodo (system, subsystem, group)
            node_id: ID del nodo
            
        Returns:
            Dict con información de dependencias
        """
        dependencies = {
            'has_dependencies': False,
            'dependency_types': [],
            'dependency_counts': {},
            'can_delete': True,
            'warnings': []
        }
        
        try:
            # Verificar según el tipo de nodo
            if node_type == 'system':
                # Verificar subsistemas
                subsystems = self.api_client.get(
                    '/api/v1/catalog/taxonomy-subsystems/',
                    params={'system': node_id}
                )
                subsystem_count = len(subsystems.get('results', []))
                
                if subsystem_count > 0:
                    dependencies['has_dependencies'] = True
                    dependencies['dependency_types'].append('subsistemas')
                    dependencies['dependency_counts']['subsistemas'] = subsystem_count
                    dependencies['can_delete'] = False
                    dependencies['warnings'].append(
                        f"Este sistema tiene {subsystem_count} subsistema(s) asociado(s)"
                    )
            
            elif node_type == 'subsystem':
                # Verificar grupos
                groups = self.api_client.get(
                    '/api/v1/catalog/taxonomy-groups/',
                    params={'subsystem': node_id}
                )
                group_count = len(groups.get('results', []))
                
                if group_count > 0:
                    dependencies['has_dependencies'] = True
                    dependencies['dependency_types'].append('grupos')
                    dependencies['dependency_counts']['grupos'] = group_count
                    dependencies['can_delete'] = False
                    dependencies['warnings'].append(
                        f"Este subsistema tiene {group_count} grupo(s) asociado(s)"
                    )
            
            # Verificar equipos asociados (para cualquier nivel)
            equipment_count = self._check_equipment_dependencies(node_type, node_id)
            if equipment_count > 0:
                dependencies['has_dependencies'] = True
                dependencies['dependency_types'].append('equipos')
                dependencies['dependency_counts']['equipos'] = equipment_count
                dependencies['warnings'].append(
                    f"Hay {equipment_count} equipo(s) asociado(s) a esta taxonomía"
                )
        
        except Exception as e:
            logger.error(f"Error checking dependencies for {node_type} {node_id}: {e}")
            dependencies['warnings'].append("Error al verificar dependencias")
        
        return dependencies
    
    def _check_equipment_dependencies(self, node_type: str, node_id: int) -> int:
        """
        Verifica si hay equipos asociados a un nodo de taxonomía
        
        Args:
            node_type: Tipo del nodo
            node_id: ID del nodo
            
        Returns:
            int: Cantidad de equipos asociados
        """
        try:
            # Construir parámetro de búsqueda según el tipo
            param_name = f'taxonomy_{node_type}'
            
            response = self.api_client.get(
                '/api/v1/equipment/',
                params={param_name: node_id}
            )
            
            return response.get('count', 0)
            
        except Exception as e:
            logger.error(f"Error checking equipment dependencies: {e}")
            return 0
    
    def validate_code_uniqueness(self, node_type: str, code: str, 
                                 parent_id: Optional[int] = None,
                                 exclude_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Valida que un código sea único dentro de su contexto
        
        Args:
            node_type: Tipo del nodo (system, subsystem, group)
            code: Código a validar
            parent_id: ID del padre (para subsistemas y grupos)
            exclude_id: ID a excluir (para edición)
            
        Returns:
            Tuple[bool, Optional[str]]: (es_único, mensaje_error)
        """
        try:
            # Determinar endpoint y campo de código
            endpoint_map = {
                'system': 'taxonomy-systems/',
                'subsystem': 'taxonomy-subsystems/',
                'group': 'taxonomy-groups/'
            }
            
            code_field_map = {
                'system': 'system_code',
                'subsystem': 'subsystem_code',
                'group': 'group_code'
            }
            
            endpoint = endpoint_map.get(node_type)
            code_field = code_field_map.get(node_type)
            
            if not endpoint or not code_field:
                return False, "Tipo de nodo inválido"
            
            # Construir parámetros de búsqueda usando el campo correcto
            params = {code_field: code.upper()}
            
            # Para subsistemas y grupos, verificar unicidad dentro del padre
            if node_type == 'subsystem' and parent_id:
                params['system'] = parent_id
            elif node_type == 'group' and parent_id:
                params['subsystem'] = parent_id
            
            # Buscar códigos existentes
            response = self.api_client.get(endpoint, params=params)
            results = response.get('results', [])
            
            # Excluir el elemento actual si estamos editando
            if exclude_id:
                results = [r for r in results if r.get('id') != exclude_id]
            
            if results:
                context = ""
                if parent_id:
                    context = " en este contexto"
                return False, f"El código '{code}' ya existe{context}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating code uniqueness: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, f"Error al validar unicidad del código: {str(e)}"
    
    def validate_before_save(self, node_type: str, data: Dict, 
                            node_id: Optional[int] = None) -> Tuple[bool, List[str]]:
        """
        Validación completa antes de guardar un nodo
        
        Args:
            node_type: Tipo del nodo
            data: Datos del nodo
            node_id: ID del nodo (para edición)
            
        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []
        
        # Validar código único
        code = data.get('code', '').strip().upper()
        parent_id = data.get('parent_id')
        
        is_unique, error_msg = self.validate_code_uniqueness(
            node_type, code, parent_id, node_id
        )
        if not is_unique:
            errors.append(error_msg)
        
        # Validar jerarquía si hay padre
        if parent_id and node_type in ['subsystem', 'group']:
            parent_type = 'system' if node_type == 'subsystem' else 'subsystem'
            is_valid, error_msg = self.validate_hierarchy(
                parent_type, parent_id, node_type
            )
            if not is_valid:
                errors.append(error_msg)
        
        # Validar referencias circulares si estamos editando y cambiando padre
        if node_id and parent_id:
            has_circular, error_msg = self.check_circular_reference(
                node_type, node_id, parent_id
            )
            if has_circular:
                errors.append(error_msg)
        
        # Validar campos requeridos
        if not code:
            errors.append("El código es requerido")
        
        if not data.get('name', '').strip():
            errors.append("El nombre es requerido")
        
        return len(errors) == 0, errors


class TaxonomyWarningSystem:
    """Sistema de advertencias para cambios críticos en taxonomía"""
    
    @staticmethod
    def get_deletion_warnings(node_type: str, node_data: Dict, 
                             dependencies: Dict) -> List[Dict]:
        """
        Genera advertencias para eliminación de nodos
        
        Args:
            node_type: Tipo del nodo
            node_data: Datos del nodo
            dependencies: Información de dependencias
            
        Returns:
            List[Dict]: Lista de advertencias con nivel y mensaje
        """
        warnings = []
        
        # Advertencia crítica si hay dependencias
        if dependencies.get('has_dependencies'):
            warnings.append({
                'level': 'danger',
                'icon': 'exclamation-triangle',
                'title': 'Eliminación Bloqueada',
                'message': 'Este elemento tiene dependencias y no puede ser eliminado.',
                'details': dependencies.get('warnings', [])
            })
        
        # Advertencia si está activo
        if node_data.get('is_active'):
            warnings.append({
                'level': 'warning',
                'icon': 'exclamation-circle',
                'title': 'Elemento Activo',
                'message': 'Este elemento está actualmente activo en el sistema.',
                'details': ['Considere desactivarlo antes de eliminarlo']
            })
        
        # Advertencia informativa
        warnings.append({
            'level': 'info',
            'icon': 'info-circle',
            'title': 'Acción Irreversible',
            'message': 'Esta acción no se puede deshacer.',
            'details': ['Asegúrese de tener respaldos si es necesario']
        })
        
        return warnings
    
    @staticmethod
    def get_deactivation_warnings(node_type: str, node_data: Dict) -> List[Dict]:
        """
        Genera advertencias para desactivación de nodos
        
        Args:
            node_type: Tipo del nodo
            node_data: Datos del nodo
            
        Returns:
            List[Dict]: Lista de advertencias
        """
        warnings = []
        
        # Advertencia sobre impacto en hijos
        if node_type in ['system', 'subsystem']:
            child_type = 'subsistemas' if node_type == 'system' else 'grupos'
            warnings.append({
                'level': 'warning',
                'icon': 'exclamation-triangle',
                'title': 'Impacto en Jerarquía',
                'message': f'Desactivar este elemento puede afectar a sus {child_type}.',
                'details': [f'Los {child_type} asociados podrían quedar inaccesibles']
            })
        
        return warnings
    
    @staticmethod
    def get_modification_warnings(node_type: str, old_data: Dict, 
                                  new_data: Dict) -> List[Dict]:
        """
        Genera advertencias para modificación de nodos
        
        Args:
            node_type: Tipo del nodo
            old_data: Datos anteriores
            new_data: Datos nuevos
            
        Returns:
            List[Dict]: Lista de advertencias
        """
        warnings = []
        
        # Advertencia si se cambia el código
        if old_data.get('code') != new_data.get('code'):
            warnings.append({
                'level': 'warning',
                'icon': 'exclamation-circle',
                'title': 'Cambio de Código',
                'message': 'Está cambiando el código de este elemento.',
                'details': [
                    'Esto puede afectar referencias en otros sistemas',
                    'Verifique que no haya integraciones que dependan del código actual'
                ]
            })
        
        # Advertencia si se desactiva
        if old_data.get('is_active') and not new_data.get('is_active'):
            warnings.extend(
                TaxonomyWarningSystem.get_deactivation_warnings(node_type, old_data)
            )
        
        return warnings
