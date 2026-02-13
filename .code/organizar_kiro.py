"""
Script para organizar la documentación en .kiro
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
KIRO_DIR = ROOT / ".kiro"

def create_kiro_structure():
    """Crea la estructura organizada de .kiro"""
    
    # Estructura propuesta
    structure = {
        "01-especificaciones": {
            "description": "Especificaciones técnicas y de diseño",
            "subdirs": ["specs"]
        },
        "02-documentacion-tecnica": {
            "description": "Documentación técnica detallada",
            "subdirs": []
        },
        "03-reportes-finales": {
            "description": "Reportes finales y entregables",
            "subdirs": []
        },
        "04-archivos-historicos": {
            "description": "Archivos históricos y versiones anteriores",
            "subdirs": []
        }
    }
    
    # Crear directorios
    for dir_name, info in structure.items():
        dir_path = KIRO_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Crear subdirectorios
        for subdir in info.get("subdirs", []):
            (dir_path / subdir).mkdir(parents=True, exist_ok=True)
    
    # Mover specs existentes si están en la raíz de .kiro
    specs_root = KIRO_DIR / "specs"
    specs_dest = KIRO_DIR / "01-especificaciones" / "specs"
    
    if specs_root.exists() and specs_root != specs_dest:
        # Mover contenido
        for item in specs_root.iterdir():
            if item.is_dir():
                dest = specs_dest / item.name
                if not dest.exists():
                    shutil.move(str(item), str(dest))
                else:
                    # Si existe, mover archivos individuales
                    for file in item.iterdir():
                        dest_file = dest / file.name
                        if not dest_file.exists():
                            shutil.move(str(file), str(dest_file))
    
    return structure

def create_kiro_index():
    """Crea el índice maestro de .kiro"""
    index_path = KIRO_DIR / "INDICE_MAESTRO.md"
    
    content = f"""# Índice Maestro - Especificaciones y Documentación Técnica

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📚 Estructura de Documentación Técnica

Esta documentación contiene las especificaciones técnicas, diseños y documentación formal del proyecto.

### 📂 Directorios Principales

#### [01-especificaciones](./01-especificaciones/)
**Descripción:** Especificaciones técnicas y de diseño del sistema

**Contenido:**
- Especificaciones de diseño
- Requirements funcionales y no funcionales
- Tasks y planificación de implementación
- Documentación de APIs

**Subdirectorios:**
- `specs/` - Especificaciones por módulo
  - `forge-api-rest/` - Especificaciones del backend API
  - `forge-frontend-web/` - Especificaciones del frontend web
  - `forge-frontend-catalog-services-completion/` - Especificaciones de catálogos y servicios
  - `scheduled-reports-system/` - Especificaciones del sistema de reportes

#### [02-documentacion-tecnica](./02-documentacion-tecnica/)
**Descripción:** Documentación técnica detallada

**Contenido:**
- Arquitectura del sistema
- Diagramas técnicos
- Guías de desarrollo
- Documentación de APIs

#### [03-reportes-finales](./03-reportes-finales/)
**Descripción:** Reportes finales y entregables

**Contenido:**
- Reportes de completación
- Documentación de entregables
- Reportes de calidad

#### [04-archivos-historicos](./04-archivos-historicos/)
**Descripción:** Archivos históricos y versiones anteriores

**Contenido:**
- Versiones anteriores de documentos
- Historial de cambios
- Archivos deprecados

---

## 🔍 Navegación Rápida

### Por Módulo

- **Backend API:** [forge-api-rest](./01-especificaciones/specs/forge-api-rest/)
- **Frontend Web:** [forge-frontend-web](./01-especificaciones/specs/forge-frontend-web/)
- **Catálogos y Servicios:** [forge-frontend-catalog-services-completion](./01-especificaciones/specs/forge-frontend-catalog-services-completion/)
- **Reportes Programados:** [scheduled-reports-system](./01-especificaciones/specs/scheduled-reports-system/)

### Por Tipo de Documento

- **Especificaciones:** [01-especificaciones](./01-especificaciones/)
- **Documentación Técnica:** [02-documentacion-tecnica](./02-documentacion-tecnica/)
- **Reportes:** [03-reportes-finales](./03-reportes-finales/)

---

## 📋 Estado de Especificaciones

### Especificaciones Activas

| Especificación | Estado | Última Actualización |
|----------------|--------|----------------------|
| forge-api-rest | ✅ Completada | 2025-12-30 |
| forge-frontend-web | ✅ Completada | 2026-01-10 |
| forge-frontend-catalog-services-completion | ⏸️ En Progreso | 2026-01-16 |
| scheduled-reports-system | ⏸️ Planificada | - |

### Progreso de Implementación

- **Backend API:** 100% según especificación
- **Frontend Web Base:** 100% según especificación
- **Catálogos y Servicios:** 82% según especificación
- **Reportes Programados:** 0% (pendiente)

---

## 🔗 Enlaces Relacionados

- [Documentación del Proyecto](../.code/INDICE_MAESTRO.md)
- [Estado Actual del Proyecto](../.code/control/ESTADO_PROYECTO_ACTUAL.md)
- [Control de Tareas](../.code/control/SEGUIMIENTO_TAREAS_ACTIVAS.md)

---

**Nota:** Esta documentación es de referencia técnica. Para documentación de desarrollo y reportes, ver [.code](../.code/INDICE_MAESTRO.md).

"""
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_specs_index():
    """Crea índice para cada especificación"""
    specs_dir = KIRO_DIR / "01-especificaciones" / "specs"
    
    if not specs_dir.exists():
        return
    
    index_path = specs_dir / "INDICE.md"
    
    content = f"""# Índice - Especificaciones Técnicas

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📋 Especificaciones Disponibles

"""
    
    for spec_dir in sorted(specs_dir.iterdir()):
        if spec_dir.is_dir() and not spec_dir.name.startswith('.'):
            content += f"### [{spec_dir.name}](./{spec_dir.name}/)\n\n"
            
            # Buscar archivos principales
            design_file = spec_dir / "design.md"
            requirements_file = spec_dir / "requirements.md"
            tasks_file = spec_dir / "tasks.md"
            
            if design_file.exists():
                content += f"- [Diseño](./{spec_dir.name}/design.md)\n"
            if requirements_file.exists():
                content += f"- [Requisitos](./{spec_dir.name}/requirements.md)\n"
            if tasks_file.exists():
                content += f"- [Tareas](./{spec_dir.name}/tasks.md)\n"
            
            content += "\n"
    
    content += """
---

## 📝 Descripción

Este directorio contiene las especificaciones técnicas de cada módulo del sistema.

Cada especificación incluye:
- **design.md**: Diseño técnico y arquitectura
- **requirements.md**: Requisitos funcionales y no funcionales
- **tasks.md**: Plan de implementación y tareas

---

## 🔗 Navegación

- [Volver al índice maestro](../../INDICE_MAESTRO.md)
- [Documentación del proyecto](../../../.code/INDICE_MAESTRO.md)

"""
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    print("Organizando .kiro...")
    print(f"Directorio .kiro: {KIRO_DIR}")
    
    structure = create_kiro_structure()
    print("[OK] Estructura creada")
    
    create_kiro_index()
    print("[OK] Indice maestro creado")
    
    create_specs_index()
    print("[OK] Indice de especificaciones creado")
    
    print("\n[OK] Organizacion de .kiro completada!")
