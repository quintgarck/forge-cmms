"""
Template tags para navegación y breadcrumbs
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag('frontend/components/breadcrumbs.html')
def render_breadcrumbs(breadcrumbs):
    """
    Renderiza breadcrumbs con iconos y estilos mejorados
    
    Args:
        breadcrumbs: Lista de breadcrumbs con name, url e icon
        
    Returns:
        Dict con contexto para el template
    """
    return {'breadcrumbs': breadcrumbs}


@register.inclusion_tag('frontend/components/quick_actions.html')
def render_quick_actions(actions):
    """
    Renderiza botones de acciones rápidas
    
    Args:
        actions: Lista de acciones con name, url, icon y class
        
    Returns:
        Dict con contexto para el template
    """
    return {'actions': actions}


@register.inclusion_tag('frontend/components/navigation_history.html')
def render_navigation_history(history):
    """
    Renderiza historial de navegación
    
    Args:
        history: Lista de páginas visitadas
        
    Returns:
        Dict con contexto para el template
    """
    return {'history': history}


@register.inclusion_tag('frontend/components/related_pages.html')
def render_related_pages(pages):
    """
    Renderiza páginas relacionadas
    
    Args:
        pages: Lista de páginas relacionadas
        
    Returns:
        Dict con contexto para el template
    """
    return {'pages': pages}


@register.simple_tag
def breadcrumb_separator():
    """
    Retorna el separador de breadcrumbs
    
    Returns:
        HTML del separador
    """
    return mark_safe('<i class="bi bi-chevron-right mx-2 text-muted"></i>')


@register.filter
def get_icon_class(icon_name):
    """
    Convierte nombre de icono a clase de Bootstrap Icons
    
    Args:
        icon_name: Nombre del icono
        
    Returns:
        Clase CSS completa
    """
    return f'bi bi-{icon_name}'
