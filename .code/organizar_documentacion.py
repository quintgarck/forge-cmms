"""
Script para organizar la documentación del proyecto ForgeDB
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

# Mapeo de archivos a categorías
FILE_CATEGORIES = {
    # Tareas completadas
    "RESUMEN_TAREA_": ("08-tareas-completadas", "Tareas Completadas"),
    "RESUMEN_SUBTAREAS_": ("08-tareas-completadas", "Tareas Completadas"),
    
    # Reportes de sesión
    "RESUMEN_SESION_": ("09-reportes-sesion", "Reportes de Sesión"),
    
    # Guías de uso
    "GUIA_": ("10-guias-uso", "Guías de Uso"),
    "COMO_": ("10-guias-uso", "Guías de Uso"),
    "INSTRUCCIONES_": ("10-guias-uso", "Guías de Uso"),
    "REFERENCIA_RAPIDA_": ("10-guias-uso", "Guías de Uso"),
    "MAPA_VISUAL_": ("10-guias-uso", "Guías de Uso"),
    
    # Análisis de estado
    "ANALISIS_": ("11-analisis-estado", "Análisis de Estado"),
    "ESTADO_PROYECTO_": ("11-analisis-estado", "Análisis de Estado"),
    "COMPARACION_": ("11-analisis-estado", "Análisis de Estado"),
    
    # Correcciones y bugs
    "RESUMEN_CORRECCION_": ("12-correcciones-bugs", "Correcciones y Bugs"),
    "RESUMEN_FIXES_": ("12-correcciones-bugs", "Correcciones y Bugs"),
    "SOLUCION_PROBLEMA_": ("12-correcciones-bugs", "Correcciones y Bugs"),
    "CORRECCION_": ("12-correcciones-bugs", "Correcciones y Bugs"),
    
    # Mejoras UI/UX
    "RESUMEN_MEJORAS_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "RESUMEN_FINAL_MEJORAS_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "RESUMEN_AJUSTES_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "RESUMEN_REBRANDING_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "RESUMEN_FINAL_TEMA_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "RESUMEN_EJECUTIVO_MOVIAX_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "COMPONENTES_TEMATIZADOS_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "COMPARATIVA_VISUAL_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "INDICE_DOCUMENTACION_MOVIAX_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "INDICE_DOCUMENTACION_UNIFORMIDAD_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "RESUMEN_UNIFORMIDAD_": ("13-mejoras-ui", "Mejoras UI/UX"),
    "RESUMEN_EJECUTIVO_UNIFORMIDAD": ("13-mejoras-ui", "Mejoras UI/UX"),
    "README_UNIFORMIDAD": ("13-mejoras-ui", "Mejoras UI/UX"),
    "CHECKLIST_VERIFICACION_": ("13-mejoras-ui", "Mejoras UI/UX"),
    
    # Reportes y documentación
    "RESUMEN_REPORTES_": ("09-reportes-sesion", "Reportes de Sesión"),
    "RESUMEN_SPEC_": ("09-reportes-sesion", "Reportes de Sesión"),
    "RESUMEN_SITUACION_": ("09-reportes-sesion", "Reportes de Sesión"),
    "INDICE_DOCUMENTACION_REPORTES_": ("09-reportes-sesion", "Reportes de Sesión"),
    "PROPUESTA_SISTEMA_": ("09-reportes-sesion", "Reportes de Sesión"),
    
    # Planificación
    "PLAN_": ("16-planificacion-tareas", "Planificación de Tareas"),
    "SIGUIENTE_PASO_": ("16-planificacion-tareas", "Planificación de Tareas"),
    
    # Testing
    "RESUMEN_TESTING_": ("14-testing-scripts", "Testing y Scripts"),
    "test_": ("14-testing-scripts", "Testing y Scripts"),
    
    # Documentación de flujos
    "FLUJO_": ("15-documentacion-flujos", "Documentación de Flujos"),
}

# Scripts
SCRIPTS = {
    ".ps1": ("14-testing-scripts", "Scripts PowerShell"),
    ".py": ("14-testing-scripts", "Scripts Python"),
}

def get_category(filename):
    """Determina la categoría de un archivo"""
    for prefix, (category, _) in FILE_CATEGORIES.items():
        if filename.startswith(prefix):
            return category, prefix
    # Verificar extensión para scripts
    ext = Path(filename).suffix
    if ext in SCRIPTS:
        return SCRIPTS[ext][0], ext
    return None, None

def move_file(filepath, category_dir):
    """Mueve un archivo a su categoría"""
    if not category_dir.exists():
        category_dir.mkdir(parents=True, exist_ok=True)
    
    dest = category_dir / filepath.name
    if dest.exists():
        # Si existe, agregar timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = filepath.stem
        suffix = filepath.suffix
        dest = category_dir / f"{stem}_{timestamp}{suffix}"
    
    shutil.move(str(filepath), str(dest))
    return dest

def organize_root_files():
    """Organiza archivos de la raíz"""
    moved = {}
    skipped = []
    
    for filepath in ROOT.glob("*.md"):
        if filepath.name.startswith("."):
            continue
        
        category, prefix = get_category(filepath.name)
        if category:
            category_dir = CODE_DIR / category
            dest = move_file(filepath, category_dir)
            if category not in moved:
                moved[category] = []
            moved[category].append((filepath.name, dest.name))
        else:
            skipped.append(filepath.name)
    
    # Mover scripts
    for ext in [".ps1", ".py"]:
        for filepath in ROOT.glob(f"*{ext}"):
            if filepath.name.startswith(".") or filepath.name == "organizar_documentacion.py":
                continue
            
            category, _ = get_category(filepath.name)
            if category:
                category_dir = CODE_DIR / category
                dest = move_file(filepath, category_dir)
                if category not in moved:
                    moved[category] = []
                moved[category].append((filepath.name, dest.name))
            else:
                skipped.append(filepath.name)
    
    return moved, skipped

def create_index(category_dir, category_name, files):
    """Crea un índice para una categoría"""
    index_path = category_dir / "INDICE.md"
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"# Índice - {category_name}\n\n")
        f.write(f"**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write("## 📋 Archivos en esta categoría\n\n")
        
        if files:
            for original, moved in sorted(files):
                f.write(f"- [{original}](./{moved})\n")
        else:
            f.write("*No hay archivos en esta categoría aún.*\n")
        
        f.write("\n---\n\n")
        f.write("## 📝 Descripción\n\n")
        f.write(f"Esta categoría contiene documentación relacionada con: **{category_name}**\n\n")

if __name__ == "__main__":
    print("Organizando documentación...")
    print(f"Directorio raíz: {ROOT}")
    print(f"Directorio .code: {CODE_DIR}")
    
    moved, skipped = organize_root_files()
    
    print(f"\n[OK] Archivos movidos: {sum(len(files) for files in moved.values())}")
    print(f"[SKIP] Archivos omitidos: {len(skipped)}")
    
    if skipped:
        print("\nArchivos omitidos:")
        for f in skipped:
            print(f"  - {f}")
    
    # Crear índices
    print("\nCreando indices...")
    for category, files in moved.items():
        category_dir = CODE_DIR / category
        category_name = FILE_CATEGORIES.get(list(FILE_CATEGORIES.keys())[0])[1] if files else "Sin categoria"
        # Obtener nombre real de la categoría
        for prefix, (cat, name) in FILE_CATEGORIES.items():
            if cat == category:
                category_name = name
                break
        
        create_index(category_dir, category_name, files)
        print(f"  [OK] Indice creado: {category_dir}/INDICE.md")
    
    print("\n[OK] Organizacion completada!")
