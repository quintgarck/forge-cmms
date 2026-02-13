#!/usr/bin/env python
"""
Script para modificar el archivo base.html y cambiar la URL de taxonomía en el menú lateral
"""

def modify_sidebar():
    file_path = "c:/Users/Oskar QuintGarck/DataMain/02-DataCore/01-DevOps/02-Docker/project-root/building/tunning-management/forge-cmms/forge_api/templates/frontend/base/base.html"
    
    # Leer el contenido del archivo
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Reemplazar la URL de taxonomy_system_list con taxonomy_tree
    old_url = '{% url \'frontend:taxonomy_system_list\' %}'
    new_url = '{% url \'frontend:taxonomy_tree\' %}'
    
    # Realizar el reemplazo
    updated_content = content.replace(old_url, new_url)
    
    # Escribir el contenido actualizado de vuelta al archivo
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print("Archivo modificado exitosamente!")
    print(f"Se cambió la URL de taxonomía en el menú lateral")
    print(f"Antes: {old_url}")
    print(f"Después: {new_url}")

if __name__ == "__main__":
    modify_sidebar()