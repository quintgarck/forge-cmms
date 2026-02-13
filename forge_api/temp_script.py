with open('templates/frontend/catalog/taxonomy_tree.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar el botón modal por un enlace de redirección
old_button = '''<button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createSystemModal">
                        <i class="bi bi-plus-circle"></i> Nuevo Sistema
                    </button>'''

new_link = '''<a href="{% url 'frontend:taxonomy_system_create' %}" class="btn btn-primary">
                        <i class="bi bi-plus-circle"></i> Nuevo Sistema
                    </a>'''

content = content.replace(old_button, new_link)

with open('templates/frontend/catalog/taxonomy_tree.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo actualizado correctamente")