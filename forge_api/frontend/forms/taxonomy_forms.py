"""
Formularios para el sistema de taxonomía jerárquica
Incluye validaciones avanzadas y widgets personalizados
"""

from django import forms
from django.core.exceptions import ValidationError
import re


class TaxonomySystemForm(forms.Form):
    """Formulario para sistemas de taxonomía"""
    
    def __init__(self, *args, **kwargs):
        # Extraer categories_choices del kwargs si existe
        categories_choices = kwargs.pop('categories_choices', None)
        super().__init__(*args, **kwargs)
        
        # Si se proporcionaron categorías, actualizar el campo
        if categories_choices:
            self.fields['category'].choices = [('', '-- Seleccione una categoría --')] + categories_choices
    
    system_code = forms.CharField(
        max_length=10,
        label='Código',
        help_text='Código único del sistema (ej: ENGINE, TRANSM)',
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Ingrese código único',
            'data-validation': 'required|unique',
            'maxlength': '10'
        })
    )
    
    category = forms.ChoiceField(
        required=True,
        initial='',
        label='Categoría',
        help_text='Seleccione la categoría del sistema',
        choices=[('', '-- Seleccione una categoría --')],  # Se actualizará dinámicamente
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    name_es = forms.CharField(
        max_length=100,
        label='Nombre (Español)',
        help_text='Nombre descriptivo del sistema en español',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nombre del sistema',
            'data-validation': 'required',
            'maxlength': '100'
        })
    )
    
    name_en = forms.CharField(
        max_length=100,
        required=False,
        label='Nombre (Inglés)',
        help_text='Nombre descriptivo del sistema en inglés (opcional)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre en inglés (opcional)',
            'maxlength': '100'
        })
    )
    
    icon = forms.CharField(
        max_length=50,
        required=False,
        label='Icono',
        help_text='Clase del icono (ej: bi bi-gear, fas fa-car)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'bi bi-gear',
            'maxlength': '50'
        })
    )
    
    scope = forms.CharField(
        required=False,
        label='Alcance',
        help_text='Descripción del alcance del sistema',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción del alcance (opcional)',
            'maxlength': '500'
        })
    )
    
    sort_order = forms.IntegerField(
        required=False,
        initial=0,
        label='Orden',
        help_text='Orden de visualización (0 = primero)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '999'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Activo',
        help_text='Indica si el sistema está activo para uso',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_system_code(self):
        system_code = self.cleaned_data.get('system_code', '').upper().strip()
        
        if not system_code:
            raise ValidationError("El código es requerido.")
        
        # Validar formato del código
        if not re.match(r'^[A-Z0-9_]+$', system_code):
            raise ValidationError(
                "El código solo puede contener letras mayúsculas, números y guiones bajos."
            )
        
        if len(system_code) < 2:
            raise ValidationError("El código debe tener al menos 2 caracteres.")
        
        if len(system_code) > 10:
            raise ValidationError("El código no puede tener más de 10 caracteres.")
        
        return system_code
    
    def clean_name_es(self):
        name_es = self.cleaned_data.get('name_es', '').strip()
        
        if not name_es:
            raise ValidationError("El nombre es requerido.")
        
        if len(name_es) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        return name_es


class TaxonomySubsystemForm(forms.Form):
    """Formulario para subsistemas de taxonomía"""
    
    system = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    subsystem_code = forms.CharField(
        max_length=10,
        label='Código',
        help_text='Código único del subsistema (ej: INJ01, TRANSM)',
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Ej: INJ01, TRANSM',
            'pattern': '[A-Z0-9_]+',
            'title': 'Solo letras mayúsculas, números y guiones bajos',
            'maxlength': '10'
        })
    )
    
    name_es = forms.CharField(
        max_length=100,
        label='Nombre (Español)',
        help_text='Nombre descriptivo del subsistema',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nombre del subsistema',
            'maxlength': '100'
        })
    )
    
    name_en = forms.CharField(
        max_length=100,
        required=False,
        label='Nombre (Inglés)',
        help_text='Nombre en inglés (opcional)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre en inglés (opcional)',
            'maxlength': '100'
        })
    )
    
    icon = forms.CharField(
        max_length=50,
        required=False,
        label='Icono',
        help_text='Clase del icono (ej: bi bi-gear)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'bi bi-gear',
            'maxlength': '50'
        })
    )
    
    scope = forms.CharField(
        required=False,
        label='Alcance',
        help_text='Descripción del alcance del subsistema',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción del alcance (opcional)',
            'maxlength': '500'
        })
    )
    
    sort_order = forms.IntegerField(
        required=False,
        initial=0,
        label='Orden',
        help_text='Orden de visualización (0 = primero)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '999'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Activo',
        help_text='Indica si el subsistema está activo para uso',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_subsystem_code(self):
        subsystem_code = self.cleaned_data.get('subsystem_code', '').upper().strip()
        
        if not subsystem_code:
            raise ValidationError("El código es requerido.")
        
        if not re.match(r'^[A-Z0-9_]+$', subsystem_code):
            raise ValidationError(
                "El código solo puede contener letras mayúsculas, números y guiones bajos."
            )
        
        if len(subsystem_code) < 2:
            raise ValidationError("El código debe tener al menos 2 caracteres.")
        
        if len(subsystem_code) > 10:
            raise ValidationError("El código no puede tener más de 10 caracteres.")
        
        return subsystem_code
    
    def clean_name_es(self):
        name_es = self.cleaned_data.get('name_es', '').strip()
        
        if not name_es:
            raise ValidationError("El nombre es requerido.")
        
        if len(name_es) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        return name_es


class TaxonomyGroupForm(forms.Form):
    """Formulario para grupos de taxonomía"""
    
    subsystem = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    code = forms.CharField(
        max_length=20,
        label='Código',
        help_text='Código único del grupo dentro del subsistema',
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Ingrese código único',
            'data-validation': 'required|unique',
            'maxlength': '20'
        })
    )
    
    name = forms.CharField(
        max_length=100,
        label='Nombre',
        help_text='Nombre descriptivo del grupo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nombre del grupo',
            'data-validation': 'required',
            'maxlength': '100'
        })
    )
    
    description = forms.CharField(
        required=False,
        label='Descripción',
        help_text='Descripción detallada del grupo',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción opcional del grupo',
            'maxlength': '500'
        })
    )
    
    sort_order = forms.IntegerField(
        required=False,
        initial=0,
        label='Orden',
        help_text='Orden de visualización (0 = primero)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '999'
        })
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Activo',
        help_text='Indica si el grupo está activo para uso',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_code(self):
        code = self.cleaned_data.get('code', '').upper().strip()
        
        if not code:
            raise ValidationError("El código es requerido.")
        
        if not re.match(r'^[A-Z0-9_]+$', code):
            raise ValidationError(
                "El código solo puede contener letras mayúsculas, números y guiones bajos."
            )
        
        return code


class TaxonomySearchForm(forms.Form):
    """Formulario de búsqueda en taxonomía"""
    
    search = forms.CharField(
        required=False,
        max_length=100,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar en taxonomía...',
            'data-search': 'taxonomy',
            'autocomplete': 'off'
        })
    )
    
    level = forms.ChoiceField(
        required=False,
        label='Nivel',
        choices=[
            ('', 'Todos los niveles'),
            ('system', 'Solo sistemas'),
            ('subsystem', 'Solo subsistemas'),
            ('group', 'Solo grupos')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class TaxonomyBulkActionForm(forms.Form):
    """Formulario para acciones masivas en taxonomía"""
    
    ACTION_CHOICES = [
        ('activate', 'Activar seleccionados'),
        ('deactivate', 'Desactivar seleccionados'),
        ('export', 'Exportar seleccionados'),
        ('delete', 'Eliminar seleccionados')
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label='Acción',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    selected_items = forms.CharField(
        widget=forms.HiddenInput(),
        help_text='IDs de elementos seleccionados (separados por coma)'
    )
    
    confirm = forms.BooleanField(
        required=False,
        label='Confirmar acción',
        help_text='Marque para confirmar que desea ejecutar esta acción',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_selected_items(self):
        selected = self.cleaned_data.get('selected_items', '')
        
        if not selected:
            raise ValidationError("Debe seleccionar al menos un elemento.")
        
        try:
            # Validar que sean números separados por coma
            ids = [int(id.strip()) for id in selected.split(',') if id.strip()]
            if not ids:
                raise ValidationError("No se encontraron elementos válidos.")
            return ids
        except ValueError:
            raise ValidationError("Los IDs seleccionados no son válidos.")
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        confirm = cleaned_data.get('confirm')
        
        # Acciones destructivas requieren confirmación
        if action in ['delete', 'deactivate'] and not confirm:
            raise ValidationError(
                "Debe confirmar la acción para operaciones destructivas."
            )
        
        return cleaned_data


class TaxonomyImportForm(forms.Form):
    """Formulario para importación masiva de taxonomía"""
    
    import_file = forms.FileField(
        label='Archivo de importación',
        help_text='Archivo CSV o Excel con la estructura de taxonomía',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    import_mode = forms.ChoiceField(
        choices=[
            ('create_only', 'Solo crear nuevos'),
            ('update_only', 'Solo actualizar existentes'),
            ('create_update', 'Crear y actualizar'),
            ('replace_all', 'Reemplazar todo')
        ],
        initial='create_update',
        label='Modo de importación',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    validate_only = forms.BooleanField(
        required=False,
        label='Solo validar',
        help_text='Marque para solo validar el archivo sin importar',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_import_file(self):
        file = self.cleaned_data.get('import_file')
        
        if not file:
            raise ValidationError("Debe seleccionar un archivo.")
        
        # Validar tamaño del archivo (máximo 5MB)
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("El archivo no puede ser mayor a 5MB.")
        
        # Validar extensión
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = '.' + file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f"Tipo de archivo no permitido. Use: {', '.join(allowed_extensions)}"
            )
        
        return file


class TaxonomyHierarchyValidatorForm(forms.Form):
    """Formulario para validación de jerarquía de taxonomía"""
    
    parent_type = forms.ChoiceField(
        choices=[
            ('system', 'Sistema'),
            ('subsystem', 'Subsistema')
        ],
        label='Tipo de padre',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    parent_id = forms.IntegerField(
        label='ID del padre',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        })
    )
    
    child_type = forms.ChoiceField(
        choices=[
            ('subsystem', 'Subsistema'),
            ('group', 'Grupo')
        ],
        label='Tipo de hijo',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        parent_type = cleaned_data.get('parent_type')
        child_type = cleaned_data.get('child_type')
        
        # Validar jerarquía válida
        valid_hierarchies = {
            'system': ['subsystem'],
            'subsystem': ['group']
        }
        
        if parent_type and child_type:
            if child_type not in valid_hierarchies.get(parent_type, []):
                raise ValidationError(
                    f"Jerarquía inválida: {parent_type} no puede tener hijos de tipo {child_type}"
                )
        
        return cleaned_data