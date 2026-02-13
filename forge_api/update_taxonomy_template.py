import re

# Leer el archivo
with open('templates/frontend/catalog/taxonomy_tree.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar el segundo botón modal por un enlace de redirección
content = re.sub(
    r'<button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createSystemModal">\s*<i class="bi bi-plus-circle"></i> Crear Primer Sistema\s*</button>',
    '                                <a href="{% url \'frontend:taxonomy_system_create\' %}" class="btn btn-primary">\n                                    <i class="bi bi-plus-circle"></i> Crear Primer Sistema\n                                </a>',
    content
)

# Eliminar todo el modal #createSystemModal (desde la definición hasta el cierre)
content = re.sub(
    r'<!-- Modal para crear sistema -->.*?</div>\s*</div>\s*</div>\s*</div>\s*</div>\s*</div>',
    '',
    content,
    flags=re.DOTALL
)

# Agregar comentario indicando que se eliminó el modal
content = content.replace(
    '<!-- Loading overlay -->',
    '\n<!-- Modal eliminado - redirección directa a creación de sistema -->\n\n<!-- Loading overlay -->'
)

with open('templates/frontend/catalog/taxonomy_tree.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo actualizado correctamente eliminando el modal y actualizando los botones")