#!/usr/bin/env python3
"""
Script para corregir templates masivamente
MovIAx - Corrección de templates base
"""

import os
import re
from pathlib import Path

# Definir módulos y sus clases
MODULOS = {
    "catalog": "catalog-page",
    "inventory": "inventory-page",
    "maintenance": "maintenance-page"
}

def corregir_archivo(ruta_archivo, clase):
    """Corrige un archivo HTML"""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Verificar si usa el template antiguo
        if "{% extends 'frontend/base.html' %}" in contenido or '{% extends "frontend/base.html" %}' in contenido:
            print(f"  Corrigiendo: {ruta_archivo.name}")
            
            # Reemplazar template base
            contenido = contenido.replace("{% extends 'frontend/base.html' %}", "{% extends 'frontend/base/base.html' %}")
            contenido = contenido.replace('{% extends "frontend/base.html" %}', '{% extends "frontend/base/base.html" %}')
            
            # Agregar body_class si no existe
            if "{% block body_class %}" not in contenido:
                # Buscar la línea del título
                match = re.search(r'({% block title %}.*?{% endblock %})', contenido, re.DOTALL)
                if match:
                    titulo_block = match.group(1)
                    nuevo_contenido = contenido.replace(
                        titulo_block,
                        f"{titulo_block}\n\n{{% block body_class %}}{clase}{{% endblock %}}"
                    )
                    contenido = nuevo_contenido
            
            # Guardar archivo
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            return True
    except Exception as e:
        print(f"  Error en {ruta_archivo.name}: {e}")
    
    return False

def main():
    print("=== Corrección Masiva de Templates MovIAx ===\n")
    
    total_corregidos = 0
    base_path = Path("forge_api/templates/frontend")
    
    for modulo, clase in MODULOS.items():
        print(f"Procesando módulo: {modulo.upper()}")
        ruta_modulo = base_path / modulo
        
        if ruta_modulo.exists():
            archivos = list(ruta_modulo.glob("*.html"))
            # Excluir archivos .old.html
            archivos = [f for f in archivos if not f.name.endswith('.old.html')]
            
            for archivo in archivos:
                if corregir_archivo(archivo, clase):
                    total_corregidos += 1
        else:
            print(f"  Ruta no encontrada: {ruta_modulo}")
        
        print()
    
    print("=== Corrección Completada ===")
    print(f"Total de archivos corregidos: {total_corregidos}")
    print("\nIMPORTANTE: Reinicia el servidor Django para aplicar los cambios")

if __name__ == "__main__":
    main()
