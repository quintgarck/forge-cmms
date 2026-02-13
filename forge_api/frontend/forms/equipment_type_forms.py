"""
Forms para el módulo de Equipment Types (Tipos de Equipo)
ForgeDB Frontend Web Application

Este módulo contiene formularios para la gestión completa de tipos de equipo,
incluyendo validaciones client-side y server-side, búsqueda y filtrado.
"""

from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import json
import re


class EquipmentTypeForm(forms.Form):
    """
    Formulario principal para crear y editar tipos de equipo
    """
    
    # Validadores
    type_code_validator = RegexValidator(
        regex=r'^[A-Z0-9\-_]+$',
        message="El código solo puede contener letras mayúsculas, números, guiones y guiones bajos."
    )
    
    color_validator = RegexValidator(
        regex=r'^#[0-9A-Fa-f]{6}$',
        message="El color debe ser un código hexadecimal válido (ej: #FF0000)."
    )
    
    def __init__(self, *args, **kwargs):
        # Extraer las categorías dinámicas si se proporcionan
        categories_choices = kwargs.pop('categories_choices', None)
        super().__init__(*args, **kwargs)
        
        # Si se proporcionaron categorías dinámicas, usarlas
        if categories_choices:
            self.fields['category'].choices = [('', '-- Seleccionar Categoría --')] + categories_choices
        else:
            # Fallback a categorías estáticas
            CATEGORY_CHOICES = [
                ('', '-- Seleccionar Categoría --'),
                ('AUTOMOTRIZ', 'Automotriz'),
                ('INDUSTRIAL', 'Industrial'),
                ('AGRÍCOLA', 'Agrícola'),
                ('CONSTRUCCIÓN', 'Construcción'),
                ('ELECTRÓNICO', 'Electrónico'),
                ('OTRO', 'Otro'),
            ]
            self.fields['category'].choices = CATEGORY_CHOICES
    
    # Campos del formulario
    type_code = forms.CharField(
        max_length=20,
        validators=[type_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'AUTO-001',
            'maxlength': '20',
            'required': True,
            'style': 'text-transform: uppercase;',
            'data-validation': 'unique-code',
            'autocomplete': 'off'
        }),
        label='Código del Tipo',
        help_text='Código único para identificar el tipo de equipo (ej: AUTO-001, IND-002)'
    )
    
    category = forms.ChoiceField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Categoría',
        help_text='Categoría principal del tipo de equipo'
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Vehículo Automotriz',
            'maxlength': '100',
            'required': True
        }),
        label='Nombre',
        help_text='Nombre descriptivo del tipo de equipo'
    )
    
    icon = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'fas fa-car',
            'maxlength': '50',
            'data-toggle': 'icon-picker'
        }),
        label='Icono',
        help_text='Clase CSS del icono (ej: fas fa-car, fas fa-truck)'
    )
    
    color = forms.CharField(
        max_length=7,
        required=False,
        validators=[color_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'color',
            'placeholder': '#007bff'
        }),
        label='Color',
        help_text='Color representativo del tipo de equipo'
    )
    
    attr_schema = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': '{"brand": {"type": "string", "required": true}, "model": {"type": "string", "required": true}}',
            'rows': 6,
            'data-validation': 'json-schema'
        }),
        label='Esquema de Atributos (JSON)',
        help_text='Esquema JSON que define los atributos específicos para este tipo de equipo'
    )
    
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción detallada del tipo de equipo...',
            'rows': 3,
            'maxlength': '500'
        }),
        label='Descripción',
        help_text='Descripción detallada del tipo de equipo'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Activo',
        help_text='Indica si el tipo de equipo está disponible para uso'
    )
    
    def clean_type_code(self):
        """Limpiar y validar código del tipo"""
        type_code = self.cleaned_data.get('type_code', '').strip().upper()
        
        if not type_code:
            raise ValidationError("El código del tipo es obligatorio.")
        
        if len(type_code) < 3:
            raise ValidationError("El código debe tener al menos 3 caracteres.")
        
        # Validar formato específico
        if not re.match(r'^[A-Z]{2,5}-[0-9]{3}$', type_code):
            raise ValidationError(
                "El código debe seguir el formato: CATEGORIA-NNN (ej: AUTO-001, IND-002)"
            )
        
        return type_code
    
    def clean_name(self):
        """Limpiar y validar nombre"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError("El nombre es obligatorio.")
        
        if len(name) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")
        
        return name.title()
    
    def clean_category(self):
        """Validar categoría"""
        category = self.cleaned_data.get('category')

        if not category:
            raise ValidationError("La categoría es obligatoria.")

        # Obtener las opciones válidas del campo category
        valid_categories = [choice[0] for choice in self.fields['category'].choices if choice[0]]
        if category not in valid_categories:
            raise ValidationError("Categoría no válida.")

        return category
    
    def clean_attr_schema(self):
        """Validar esquema de atributos JSON"""
        attr_schema = self.cleaned_data.get('attr_schema', '').strip()
        
        if not attr_schema:
            return {}
        
        try:
            schema = json.loads(attr_schema)
            
            # Validar que sea un diccionario
            if not isinstance(schema, dict):
                raise ValidationError("El esquema debe ser un objeto JSON válido.")
            
            # Validar estructura básica del esquema
            for field_name, field_config in schema.items():
                if not isinstance(field_config, dict):
                    raise ValidationError(f"La configuración del campo '{field_name}' debe ser un objeto.")
                
                if 'type' not in field_config:
                    raise ValidationError(f"El campo '{field_name}' debe especificar un tipo.")
                
                valid_types = ['string', 'number', 'boolean', 'date', 'select']
                if field_config['type'] not in valid_types:
                    raise ValidationError(
                        f"Tipo '{field_config['type']}' no válido para el campo '{field_name}'. "
                        f"Tipos válidos: {', '.join(valid_types)}"
                    )
            
            return schema
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"JSON no válido: {str(e)}")
    
    def clean_color(self):
        """Validar color hexadecimal"""
        color = self.cleaned_data.get('color', '').strip()
        
        if color and not color.startswith('#'):
            color = f"#{color}"
        
        return color
    
    def clean(self):
        """Validación cruzada de campos"""
        cleaned_data = super().clean()
        
        type_code = cleaned_data.get('type_code')
        category = cleaned_data.get('category')
        
        # Validar que el prefijo del código coincida con la categoría
        if type_code and category:
            category_prefixes = {
                'AUTOMOTRIZ': ['AUTO', 'VEH'],
                'INDUSTRIAL': ['IND', 'MACH'],
                'AGRÍCOLA': ['AGR', 'FARM'],
                'CONSTRUCCIÓN': ['CONST', 'BUILD'],
                'ELECTRÓNICO': ['ELEC', 'TECH'],
                'OTRO': ['OTHER', 'MISC']
            }
            
            code_prefix = type_code.split('-')[0] if '-' in type_code else ''
            valid_prefixes = category_prefixes.get(category, [])
            
            if valid_prefixes and code_prefix not in valid_prefixes:
                self.add_error('type_code', 
                    f"Para la categoría '{category}', use uno de estos prefijos: {', '.join(valid_prefixes)}"
                )
        
        return cleaned_data


class EquipmentTypeSearchForm(forms.Form):
    """
    Formulario para búsqueda y filtrado de tipos de equipo
    """
    
    def __init__(self, *args, **kwargs):
        # Extraer las categorías dinámicas si se proporcionan
        categories_choices = kwargs.pop('categories_choices', None)
        super().__init__(*args, **kwargs)
        
        # Si se proporcionaron categorías dinámicas, usarlas
        if categories_choices:
            self.fields['category'].choices = [('', 'Todas las categorías')] + categories_choices
        else:
            # Fallback a categorías estáticas
            CATEGORY_CHOICES = [
                ('AUTOMOTRIZ', 'Automotriz'),
                ('INDUSTRIAL', 'Industrial'),
                ('AGRÍCOLA', 'Agrícola'),
                ('CONSTRUCCIÓN', 'Construcción'),
                ('ELECTRÓNICO', 'Electrónico'),
                ('OTRO', 'Otro'),
            ]
            self.fields['category'].choices = [('', 'Todas las categorías')] + CATEGORY_CHOICES
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, nombre o descripción...',
            'autocomplete': 'off'
        }),
        label='Búsqueda'
    )
    
    category = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Categoría'
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('true', 'Solo activos'),
            ('false', 'Solo inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    def clean_search(self):
        """Limpiar término de búsqueda"""
        search = self.cleaned_data.get('search', '').strip()
        return search


class EquipmentTypeQuickCreateForm(forms.Form):
    """
    Formulario simplificado para creación rápida de tipos de equipo
    """
    
    type_code = forms.CharField(
        max_length=20,
        validators=[EquipmentTypeForm.type_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'AUTO-001',
            'maxlength': '20',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código'
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Nombre del tipo',
            'maxlength': '100',
            'required': True
        }),
        label='Nombre'
    )
    
    category = forms.ChoiceField(
        choices=[
            ('', '-- Seleccionar Categoría --'),
            ('AUTOMOTRIZ', 'Automotriz'),
            ('INDUSTRIAL', 'Industrial'),
            ('AGRÍCOLA', 'Agrícola'),
            ('CONSTRUCCIÓN', 'Construcción'),
            ('ELECTRÓNICO', 'Electrónico'),
            ('OTRO', 'Otro'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'required': True
        }),
        label='Categoría'
    )
    
    def clean_type_code(self):
        """Usar la misma validación que el formulario principal"""
        return EquipmentTypeForm.clean_type_code(self)
    
    def clean_name(self):
        """Usar la misma validación que el formulario principal"""
        return EquipmentTypeForm.clean_name(self)


class EquipmentTypeBulkActionForm(forms.Form):
    """
    Formulario para acciones masivas en tipos de equipo
    """
    
    ACTION_CHOICES = [
        ('', '-- Seleccionar Acción --'),
        ('activate', 'Activar seleccionados'),
        ('deactivate', 'Desactivar seleccionados'),
        ('delete', 'Eliminar seleccionados'),
        ('export', 'Exportar seleccionados'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Acción'
    )
    
    selected_items = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    confirm = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Confirmo que deseo realizar esta acción'
    )
    
    def clean_selected_items(self):
        """Validar elementos seleccionados"""
        selected_items = self.cleaned_data.get('selected_items', '')
        
        if not selected_items:
            raise ValidationError("Debe seleccionar al menos un elemento.")
        
        try:
            items = [int(x.strip()) for x in selected_items.split(',') if x.strip()]
            if not items:
                raise ValidationError("Debe seleccionar al menos un elemento válido.")
            return items
        except ValueError:
            raise ValidationError("Los elementos seleccionados no son válidos.")
    
    def clean(self):
        """Validación cruzada"""
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        confirm = cleaned_data.get('confirm')
        
        # Requerir confirmación para acciones destructivas
        if action in ['delete', 'deactivate'] and not confirm:
            raise ValidationError("Debe confirmar la acción para proceder.")
        
        return cleaned_data


class EquipmentTypeImportForm(forms.Form):
    """
    Formulario para importación masiva de tipos de equipo
    """
    
    import_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls',
            'required': True
        }),
        label='Archivo de Importación',
        help_text='Archivo CSV o Excel con los datos de tipos de equipo'
    )
    
    has_header = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='El archivo tiene encabezados',
        help_text='Marque si la primera fila contiene los nombres de las columnas'
    )
    
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Actualizar registros existentes',
        help_text='Si encuentra códigos duplicados, actualizar en lugar de crear nuevos'
    )
    
    def clean_import_file(self):
        """Validar archivo de importación"""
        import_file = self.cleaned_data.get('import_file')
        
        if not import_file:
            raise ValidationError("Debe seleccionar un archivo.")
        
        # Validar extensión
        valid_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = import_file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in valid_extensions:
            raise ValidationError(
                f"Formato de archivo no válido. Use: {', '.join(valid_extensions)}"
            )
        
        # Validar tamaño (máximo 5MB)
        if import_file.size > 5 * 1024 * 1024:
            raise ValidationError("El archivo no puede exceder 5MB.")
        
        return import_file