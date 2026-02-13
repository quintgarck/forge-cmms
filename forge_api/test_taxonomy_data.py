#!/usr/bin/env python
import os
import sys
import django

# Configurar el entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import TaxonomySystem, TaxonomySubsystem

# Obtener todos los sistemas
systems = TaxonomySystem.objects.all()
print('=== SISTEMAS ===')
for s in systems:
    print(f"- {s.system_code}: {s.name_es}")

# Obtener todos los subsistemas
subsystems = TaxonomySubsystem.objects.all()
print('\n=== SUBSISTEMAS ===')
for sub in subsystems:
    print(f"- {sub.subsystem_code}: {sub.name_es} (system={sub.system_code_id})")

print('\n=== VERIFICANDO RELACION ===')
# Verificar si los subsistemas tienen el campo 'system' correcto
system_codes = [s.system_code for s in systems]
print(f'Codigos de sistema: {system_codes}')

for sub in subsystems:
    sys_code = sub.system_code_id
    if sys_code in system_codes:
        print(f"OK Subsistema {sub.subsystem_code} -> Sistema {sys_code} (ENCONTRADO)")
    else:
        print(f"ERROR Subsistema {sub.subsystem_code} -> Sistema {sys_code} (NO ENCONTRADO)")

print('\n=== DATOS CRUDOS PARA TEMPLATE ===')
# Simular lo que el template recibe
print(f"Total sistemas: {systems.count()}")
print(f"Total subsistemas: {subsystems.count()}")

# Verificar sistema ENGINE específicamente
engine_systems = TaxonomySystem.objects.filter(system_code='ENGINE')
if engine_systems.exists():
    engine = engine_systems.first()
    print(f"\nSistema ENGINE encontrado: {engine.name_es}")
    engine_subsystems = TaxonomySubsystem.objects.filter(system_code=engine)
    print(f"Subsistemas de ENGINE: {engine_subsystems.count()}")
    for sub in engine_subsystems:
        print(f"  - {sub.subsystem_code}: {sub.name_es}")
else:
    print("\nWARNING: Sistema ENGINE NO encontrado!")
