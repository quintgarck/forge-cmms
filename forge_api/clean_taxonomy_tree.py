#!/usr/bin/env python
"""
Script para limpiar el archivo taxonomy_tree.html y remover la funcionalidad duplicada de JavaScript
"""

def clean_taxonomy_tree():
    file_path = "c:/Users/Oskar QuintGarck/DataMain/02-DataCore/01-DevOps/02-Docker/project-root/building/tunning-management/forge-cmms/forge_api/templates/frontend/catalog/taxonomy_tree.html"
    
    # Leer el contenido del archivo
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Eliminar el bloque de JavaScript adicional que duplica la funcionalidad
    # Este bloque está entre líneas 467-970 aproximadamente en el archivo original
    start_marker = "<script>\n"
    end_marker = "</script>\n{% endblock %}"
    
    # Encontrar la posición del script que comienza con la inicialización de TaxonomyTree
    script_start = content.find(start_marker, content.find("TaxonomyTree.init"))
    if script_start != -1:
        # Encontrar el final del script
        script_end = content.find(end_marker, script_start)
        if script_end != -1:
            # Incluir el marcador de fin para eliminarlo completamente
            script_end += len(end_marker)
            
            # Extraer el bloque a eliminar
            script_to_remove = content[script_start:script_end]
            
            # Remover el bloque duplicado de JavaScript
            content = content.replace(script_to_remove, "")
            
            # Agregar el script limpio que solo inicializa la clase
            clean_script = f"""
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar el árbol de taxonomía
    console.log('Initializing taxonomy tree...');
    try {
        TaxonomyTree.init({{
            container: '#taxonomy-tree',
            searchUrl: '{% url "frontend:taxonomy_ajax_search" %}',
            treeDataUrl: '{% url "frontend:taxonomy_tree_data" %}',
            nodeActionUrl: '{% url "frontend:taxonomy_node_action" %}',
            csrfToken: '{{ csrf_token }}'
        }});
        console.log('Taxonomy tree initialized successfully');
    } catch (error) {
        console.error('Error initializing taxonomy tree:', error);
    }
});
</script>
{{% endblock %}}"""
            
            # Insertar el script limpio antes del final del bloque
            content = content.rstrip() + clean_script
    
    # Escribir el contenido actualizado de vuelta al archivo
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("Archivo taxonomy_tree.html limpiado exitosamente!")
    print("Se ha removido la funcionalidad duplicada de JavaScript")
    print("Ahora solo usa la clase TaxonomyTree del archivo externo")


if __name__ == "__main__":
    clean_taxonomy_tree()