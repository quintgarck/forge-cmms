"""
Script completo para organizar la documentación del proyecto ForgeDB
Organiza archivos de la raíz en .code y estructura .kiro
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

# Directorio raíz del proyecto
ROOT = Path(__file__).parent
CODE_DIR = ROOT / ".code"
KIRO_DIR = ROOT / ".kiro"

# Mapeo de archivos a categorías (orden de prioridad)
FILE_CATEGORIES = [
    # Tareas completadas
    ("RESUMEN_TAREA_", "08-tareas-completadas", "Tareas Completadas"),
    ("RESUMEN_SUBTAREAS_", "08-tareas-completadas", "Tareas Completadas"),
    
    # Reportes de sesión
    ("RESUMEN_SESION_", "09-reportes-sesion", "Reportes de Sesión"),
    ("RESUMEN_REPORTES_", "09-reportes-sesion", "Reportes de Sesión"),
    ("RESUMEN_SPEC_", "09-reportes-sesion", "Reportes de Sesión"),
    ("RESUMEN_SITUACION_", "09-reportes-sesion", "Reportes de Sesión"),
    ("INDICE_DOCUMENTACION_REPORTES_", "09-reportes-sesion", "Reportes de Sesión"),
    ("PROPUESTA_SISTEMA_", "09-reportes-sesion", "Reportes de Sesión"),
    
    # Guías de uso
    ("GUIA_", "10-guias-uso", "Guías de Uso"),
    ("COMO_", "10-guias-uso", "Guías de Uso"),
    ("INSTRUCCIONES_", "10-guias-uso", "Guías de Uso"),
    ("REFERENCIA_RAPIDA_", "10-guias-uso", "Guías de Uso"),
    ("MAPA_VISUAL_", "10-guias-uso", "Guías de Uso"),
    
    # Análisis de estado
    ("ANALISIS_", "11-analisis-estado", "Análisis de Estado"),
    ("ESTADO_PROYECTO_", "11-analisis-estado", "Análisis de Estado"),
    ("COMPARACION_", "11-analisis-estado", "Análisis de Estado"),
    
    # Correcciones y bugs
    ("RESUMEN_CORRECCION_", "12-correcciones-bugs", "Correcciones y Bugs"),
    ("RESUMEN_FIXES_", "12-correcciones-bugs", "Correcciones y Bugs"),
    ("SOLUCION_PROBLEMA_", "12-correcciones-bugs", "Correcciones y Bugs"),
    ("CORRECCION_", "12-correcciones-bugs", "Correcciones y Bugs"),
    ("RESUMEN_FINAL_CORRECCION_", "12-correcciones-bugs", "Correcciones y Bugs"),
    
    # Mejoras UI/UX
    ("RESUMEN_MEJORAS_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("RESUMEN_FINAL_MEJORAS_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("RESUMEN_AJUSTES_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("RESUMEN_REBRANDING_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("RESUMEN_FINAL_TEMA_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("RESUMEN_EJECUTIVO_MOVIAX_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("COMPONENTES_TEMATIZADOS_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("COMPARATIVA_VISUAL_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("INDICE_DOCUMENTACION_MOVIAX_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("INDICE_DOCUMENTACION_UNIFORMIDAD_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("RESUMEN_UNIFORMIDAD_", "13-mejoras-ui", "Mejoras UI/UX"),
    ("RESUMEN_EJECUTIVO_UNIFORMIDAD", "13-mejoras-ui", "Mejoras UI/UX"),
    ("README_UNIFORMIDAD", "13-mejoras-ui", "Mejoras UI/UX"),
    ("CHECKLIST_VERIFICACION_", "13-mejoras-ui", "Mejoras UI/UX"),
    
    # Planificación
    ("PLAN_", "16-planificacion-tareas", "Planificación de Tareas"),
    ("SIGUIENTE_PASO_", "16-planificacion-tareas", "Planificación de Tareas"),
    
    # Testing
    ("RESUMEN_TESTING_", "14-testing-scripts", "Testing y Scripts"),
]

# Scripts
SCRIPTS = {
    ".ps1": ("14-testing-scripts", "Scripts PowerShell"),
    ".py": ("14-testing-scripts", "Scripts Python"),
}

def get_category(filename):
    """Determina la categoría de un archivo"""
    for prefix, category, name in FILE_CATEGORIES:
        if filename.startswith(prefix):
            return category, name
    return None, None

def move_file(filepath, category_dir, dry_run=False):
    """Mueve un archivo a su categoría"""
    if not category_dir.exists():
        category_dir.mkdir(parents=True, exist_ok=True)
    
    dest = category_dir / filepath.name
    if dest.exists() and dest != filepath:
        # Si existe, agregar timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = filepath.stem
        suffix = filepath.suffix
        dest = category_dir / f"{stem}_{timestamp}{suffix}"
    
    if not dry_run and filepath.exists() and filepath != dest:
        shutil.move(str(filepath), str(dest))
    return dest

def organize_root_files(dry_run=False):
    """Organiza archivos de la raíz"""
    moved = {}
    skipped = []
    
    # Procesar archivos .md
    for filepath in ROOT.glob("*.md"):
        if filepath.name.startswith(".") or "organizar" in filepath.name.lower():
            continue
        
        category, category_name = get_category(filepath.name)
        if category:
            category_dir = CODE_DIR / category
            dest = move_file(filepath, category_dir, dry_run)
            if category not in moved:
                moved[category] = {"name": category_name, "files": []}
            moved[category]["files"].append((filepath.name, dest.name))
        else:
            skipped.append(("md", filepath.name))
    
    # Procesar scripts
    for ext in [".ps1", ".py"]:
        for filepath in ROOT.glob(f"*{ext}"):
            if filepath.name.startswith(".") or "organizar" in filepath.name.lower():
                continue
            
            category, category_name = get_category(filepath.name)
            if not category:
                # Verificar por extensión
                if ext in SCRIPTS:
                    category, category_name = SCRIPTS[ext]
            
            if category:
                category_dir = CODE_DIR / category
                dest = move_file(filepath, category_dir, dry_run)
                if category not in moved:
                    moved[category] = {"name": category_name, "files": []}
                moved[category]["files"].append((filepath.name, dest.name))
            else:
                skipped.append((ext, filepath.name))
    
    return moved, skipped

def create_index(category_dir, category_name, files):
    """Crea un índice para una categoría"""
    index_path = category_dir / "INDICE.md"
    
    content = f"""# Índice - {category_name}

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📋 Archivos en esta categoría

"""
    
    if files:
        # Ordenar por nombre
        for original, moved in sorted(files):
            content += f"- [{original}](./{moved})\n"
    else:
        content += "*No hay archivos en esta categoría aún.*\n"
    
    content += f"""
---

## 📝 Descripción

Esta categoría contiene documentación relacionada con: **{category_name}**

Los archivos están organizados cronológicamente y por caso de uso.

---

## 🔗 Navegación

- [Volver al índice principal](../../.code/INDICE_MAESTRO.md)
- [Estado del proyecto](../../.code/control/ESTADO_PROYECTO_ACTUAL.md)
"""
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_master_index():
    """Crea el índice maestro de .code"""
    index_path = CODE_DIR / "INDICE_MAESTRO.md"
    
    categories = [
        ("08-tareas-completadas", "Tareas Completadas", "Resúmenes de tareas completadas del proyecto"),
        ("09-reportes-sesion", "Reportes de Sesión", "Reportes y documentación de sesiones de trabajo"),
        ("10-guias-uso", "Guías de Uso", "Guías, instrucciones y referencias rápidas"),
        ("11-analisis-estado", "Análisis de Estado", "Análisis del estado del proyecto y comparaciones"),
        ("12-correcciones-bugs", "Correcciones y Bugs", "Documentación de correcciones y soluciones"),
        ("13-mejoras-ui", "Mejoras UI/UX", "Mejoras de interfaz, branding y uniformidad"),
        ("14-testing-scripts", "Testing y Scripts", "Scripts de prueba y herramientas"),
        ("15-documentacion-flujos", "Documentación de Flujos", "Documentación de flujos de trabajo"),
        ("16-planificacion-tareas", "Planificación de Tareas", "Planes y próximos pasos"),
    ]
    
    content = f"""# Índice Maestro - Documentación ForgeDB

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📚 Estructura de Documentación

Esta documentación está organizada por categorías y casos de uso.

### 📂 Categorías Principales

"""
    
    for cat_dir, cat_name, cat_desc in categories:
        cat_path = CODE_DIR / cat_dir
        if cat_path.exists():
            file_count = len(list(cat_path.glob("*.md"))) + len(list(cat_path.glob("*.ps1"))) + len(list(cat_path.glob("*.py")))
            content += f"#### [{cat_name}](./{cat_dir}/INDICE.md)\n"
            content += f"{cat_desc}\n"
            content += f"- **Archivos:** {file_count}\n\n"
    
    content += """
---

## 🚀 Estado del Proyecto

Para ver el estado actual del proyecto, avances y próximos pasos:

- [Estado Actual del Proyecto](./control/ESTADO_PROYECTO_ACTUAL.md)
- [Control de Tareas](./control/)

---

## 📖 Guías Rápidas

- [Inicio Rápido](./INICIO_RAPIDO_2026-01-10.md)
- [Estructura Organizada](./ESTRUCTURA_ORGANIZADA.md)

---

## 🔍 Búsqueda Rápida

### Por Tipo de Documento

- **Tareas:** [08-tareas-completadas](./08-tareas-completadas/INDICE.md)
- **Reportes:** [09-reportes-sesion](./09-reportes-sesion/INDICE.md)
- **Guías:** [10-guias-uso](./10-guias-uso/INDICE.md)
- **Análisis:** [11-analisis-estado](./11-analisis-estado/INDICE.md)
- **Correcciones:** [12-correcciones-bugs](./12-correcciones-bugs/INDICE.md)
- **Mejoras UI:** [13-mejoras-ui](./13-mejoras-ui/INDICE.md)
- **Scripts:** [14-testing-scripts](./14-testing-scripts/INDICE.md)
- **Flujos:** [15-documentacion-flujos](./15-documentacion-flujos/INDICE.md)
- **Planificación:** [16-planificacion-tareas](./16-planificacion-tareas/INDICE.md)

---
"""
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    print("Organizando documentacion...")
    print(f"Directorio raiz: {ROOT}")
    print(f"Directorio .code: {CODE_DIR}")
    
    # Primero hacer dry run
    print("\n[DRY RUN] Analizando archivos...")
    moved, skipped = organize_root_files(dry_run=True)
    
    print(f"\n[INFO] Archivos a mover: {sum(len(info['files']) for info in moved.values())}")
    print(f"[INFO] Archivos sin categoria: {len(skipped)}")
    
    if skipped:
        print("\nArchivos sin categoria:")
        for ext, f in skipped[:10]:  # Mostrar solo los primeros 10
            print(f"  - {f}")
        if len(skipped) > 10:
            print(f"  ... y {len(skipped) - 10} mas")
    
    # Confirmar y mover
    print("\n[MOVING] Moviendo archivos...")
    moved, skipped = organize_root_files(dry_run=False)
    
    print(f"\n[OK] Archivos movidos: {sum(len(info['files']) for info in moved.values())}")
    
    # Crear índices
    print("\n[CREATING] Creando indices...")
    for category, info in moved.items():
        category_dir = CODE_DIR / category
        create_index(category_dir, info["name"], info["files"])
        print(f"  [OK] Indice creado: {category_dir}/INDICE.md")
    
    # Crear índice maestro
    create_master_index()
    print(f"  [OK] Indice maestro creado: {CODE_DIR}/INDICE_MAESTRO.md")
    
    print("\n[OK] Organizacion completada!")
