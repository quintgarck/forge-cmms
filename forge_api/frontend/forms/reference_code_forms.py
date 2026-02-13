"""
Forms for Reference Code management
"""
from django import forms
import os


class ReferenceCodeForm(forms.Form):
    """Formulario para crear/editar códigos de referencia"""
    
    CATEGORY_CHOICES = [
        ('fuel', 'Combustible'),
        ('transmission', 'Transmisión'),
        ('color', 'Color'),
        ('drivetrain', 'Tracción'),
        ('condition', 'Condición'),
        ('aspiration', 'Aspiración'),
    ]
    
    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        label='Categoría',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    
    code = forms.CharField(
        max_length=20,
        label='Código',
        widget=forms.TextInput(attrs={
            'class': 'form-control text-uppercase',
            'placeholder': 'Ej: DIESEL, AUTO, RED',
            'required': True,
            'maxlength': 20
        }),
        help_text='Código único dentro de la categoría (se convertirá a mayúsculas)'
    )
    
    description = forms.CharField(
        max_length=200,
        label='Descripción',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción del código',
            'required': True,
            'maxlength': 200
        }),
        help_text='Descripción clara y concisa del código'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Activo',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Indica si el código está activo y disponible para uso'
    )
    
    def clean_code(self):
        """Convierte el código a mayúsculas y valida formato"""
        code = self.cleaned_data.get('code', '').strip().upper()
        
        if not code:
            raise forms.ValidationError("El código es requerido")
        
        # Validar que solo contenga caracteres alfanuméricos y guiones
        if not all(c.isalnum() or c in ['-', '_'] for c in code):
            raise forms.ValidationError(
                "El código solo puede contener letras, números, guiones y guiones bajos"
            )
        
        return code
    
    def clean_description(self):
        """Valida y limpia la descripción"""
        description = self.cleaned_data.get('description', '').strip()
        
        if not description:
            raise forms.ValidationError("La descripción es requerida")
        
        if len(description) < 3:
            raise forms.ValidationError("La descripción debe tener al menos 3 caracteres")
        
        return description


class ReferenceCodeImportForm(forms.Form):
    """Formulario para importar códigos de referencia desde CSV o Excel"""
    
    csv_file = forms.FileField(
        label='Archivo CSV o Excel',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xls,.xlsx',
            'required': True
        }),
        help_text='Archivo CSV o Excel (.xls, .xlsx) con columnas: Código, Descripción, Activo'
    )
    
    skip_duplicates = forms.BooleanField(
        required=False,
        initial=True,
        label='Omitir duplicados',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Si está marcado, los códigos duplicados serán omitidos. Si no, serán actualizados.'
    )
    
    def clean_csv_file(self):
        """Valida el archivo CSV o Excel"""
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file:
            raise forms.ValidationError("El archivo es requerido")
        
        # Validar extensión
        ext = os.path.splitext(csv_file.name)[1].lower()
        valid_extensions = ['.csv', '.xls', '.xlsx']
        if ext not in valid_extensions:
            raise forms.ValidationError(f"El archivo debe ser CSV, XLS o XLSX. Extensión recibida: {ext}")
        
        # Validar tamaño (máximo 5MB)
        if csv_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("El archivo no debe superar los 5MB")
        
        return csv_file
