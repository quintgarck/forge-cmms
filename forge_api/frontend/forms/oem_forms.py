"""
Formularios para el módulo OEM (Marcas y Catálogo)
"""
import logging
from django import forms
from django.db import connection
from datetime import date

logger = logging.getLogger(__name__)

# Fallback cuando no se puede leer desde BD
BRAND_TYPE_FALLBACK_CHOICES = [
    ('', 'Seleccione un tipo'),
    ('VEHICLE_MFG', 'Fabricante de Vehículos'),
    ('EQUIPMENT_MFG', 'Fabricante de Maquinaria'),
    ('PARTS_SUPPLIER', 'Proveedor de Partes'),
    ('MIXED', 'Mixto'),
]


def get_brand_type_choices():
    """
    Opciones desde catálogo oem.brand_types.
    Intenta ORM; si falla (p. ej. por quoting), usa SQL directo; si no, fallback fijo.
    """
    # 1) Intentar con el modelo BrandType
    try:
        from core.models import BrandType
        types = list(
            BrandType.objects.filter(is_active=True)
            .order_by('display_order', 'code')
            .values_list('code', 'name_es')
        )
        if types:
            return [('', 'Seleccione un tipo')] + types
    except Exception as e:
        logger.warning("BrandType ORM falló, intentando SQL directo: %s", e)

    # 2) SQL directo a oem.brand_types (evita problemas de quoting del ORM)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT code, name_es
                FROM oem.brand_types
                WHERE is_active = true
                ORDER BY display_order, code
                """
            )
            rows = cursor.fetchall()
        if rows:
            return [('', 'Seleccione un tipo')] + [(r[0], r[1]) for r in rows]
    except Exception as e:
        logger.warning("SQL directo a oem.brand_types falló: %s", e)

    return BRAND_TYPE_FALLBACK_CHOICES


class OEMBrandForm(forms.Form):
    """Formulario para crear/editar marcas OEM"""

    oem_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: TOYOTA',
            'required': True,
        }),
        label='Código OEM',
        help_text='Código único del fabricante (máx. 10 caracteres, mayúsculas)'
    )
    
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Toyota Motor Corporation',
            'required': True,
        }),
        label='Nombre',
        help_text='Nombre completo del fabricante'
    )
    
    brand_type = forms.ChoiceField(
        choices=[],  # se rellena en __init__ desde BD
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
        }),
        label='Tipo de Marca',
        help_text='Categoría del fabricante (catálogo oem.brand_types)'
    )

    def __init__(self, *args, **kwargs):
        brand_type_choices = kwargs.pop('brand_type_choices', None)
        super().__init__(*args, **kwargs)
        self.fields['brand_type'].choices = (
            brand_type_choices if brand_type_choices is not None else get_brand_type_choices()
        )
    
    country = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Japón',
        }),
        label='País',
        help_text='País de origen del fabricante'
    )
    
    website = forms.URLField(
        max_length=200,
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.ejemplo.com',
        }),
        label='Sitio Web',
        help_text='URL del sitio web oficial'
    )
    
    logo_url = forms.URLField(
        max_length=200,
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://ejemplo.com/logo.png',
        }),
        label='URL del Logo',
        help_text='URL de la imagen del logo'
    )
    
    support_email = forms.EmailField(
        max_length=100,
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'soporte@ejemplo.com',
        }),
        label='Email de Soporte',
        help_text='Correo electrónico de contacto'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Activo',
        help_text='Marca activa y visible en el sistema'
    )
    
    display_order = forms.IntegerField(
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
        }),
        label='Orden de Visualización',
        help_text='Orden para mostrar en listas (menor = primero)'
    )
    
    def clean_oem_code(self):
        """Validar que el código OEM esté en mayúsculas"""
        oem_code = self.cleaned_data.get('oem_code', '')
        return oem_code.upper().strip()
    
    def clean_name(self):
        """Limpiar el nombre"""
        name = self.cleaned_data.get('name', '')
        return name.strip()


class OEMCatalogItemForm(forms.Form):
    """Formulario para crear/editar items del catálogo OEM"""
    
    ITEM_TYPE_CHOICES = [
        ('', 'Seleccione un tipo'),
        ('VEHICLE_MODEL', 'Modelo de Vehículo'),
        ('EQUIPMENT_MODEL', 'Modelo de Maquinaria'),
        ('PART', 'Parte/Repuesto'),
    ]
    
    PART_NUMBER_TYPE_CHOICES = [
        ('', 'Seleccione un tipo'),
        ('BASIC_5', 'Basic 5'),
        ('DESIGN_5', 'Design 5'),
        ('FULL_12', 'Full 12'),
    ]
    
    CURRENCY_CHOICES = [
        ('', 'Predeterminado (USD)'),
        ('USD', 'USD - Dólar Americano'),
        ('EUR', 'EUR - Euro'),
        ('MXN', 'MXN - Peso Mexicano'),
        ('COP', 'COP - Peso Colombiano'),
    ]
    
    oem_code = forms.CharField(
        max_length=10,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
            'id': 'id_oem_code',
        }),
        label='Marca OEM',
        help_text='Seleccione el fabricante'
    )
    
    part_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: COROLLA, 12345-ABC',
            'required': True,
        }),
        label='Número de Parte/Modelo',
        help_text='Código del modelo o parte (máx. 30 caracteres)'
    )
    
    part_number_type = forms.ChoiceField(
        required=False,
        choices=PART_NUMBER_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Tipo de Número de Parte',
        help_text='Formato del número de parte'
    )
    
    item_type = forms.ChoiceField(
        choices=ITEM_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
        }),
        label='Tipo de Item',
        help_text='Categoría del item'
    )
    
    description_es = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Descripción en español',
        }),
        label='Descripción (Español)',
        help_text='Descripción del item en español'
    )
    
    description_en = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '3',
            'placeholder': 'Description in English',
        }),
        label='Descripción (Inglés)',
        help_text='Descripción del item en inglés (opcional)'
    )
    
    group_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código de grupo',
        }),
        label='Grupo de Taxonomía',
        help_text='Código del grupo de taxonomía (opcional)'
    )
    
    year_start = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1900',
            'max': '2100',
            'placeholder': 'Ej: 2020',
        }),
        label='Año Inicial',
        help_text='Primer año de producción'
    )
    
    year_end = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1900',
            'max': '2100',
            'placeholder': 'Ej: 2024',
        }),
        label='Año Final',
        help_text='Último año de producción (vacío si aún se produce)'
    )
    
    body_style = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Sedán, SUV, Hidráulica',
        }),
        label='Estilo/Atributos',
        help_text='Características físicas o tipo'
    )
    
    weight_kg = forms.DecimalField(
        required=False,
        max_digits=8,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'min': '0',
            'placeholder': '0.000',
        }),
        label='Peso (kg)',
        help_text='Peso en kilogramos'
    )
    
    dimensions = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 100x50x30 cm',
        }),
        label='Dimensiones',
        help_text='Dimensiones del producto (largo x ancho x alto)'
    )
    
    material = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Acero, Plástico, Goma',
        }),
        label='Material',
        help_text='Material de fabricación'
    )
    
    primary_image_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com/images/part.jpg',
        }),
        label='URL de Imagen Principal',
        help_text='URL de la imagen principal del producto (figura isométrica, foto del repuesto)'
    )
    
    list_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00',
        }),
        label='Precio de Lista (MSRP)',
        help_text='Precio sugerido de venta al público'
    )
    
    net_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00',
        }),
        label='Precio Neto (Dealer)',
        help_text='Precio para distribuidores/talleres'
    )
    
    currency_code = forms.ChoiceField(
        required=False,
        choices=CURRENCY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Moneda',
        help_text='Moneda para los precios'
    )
    
    oem_lead_time_days = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'placeholder': 'Ej: 7',
        }),
        label='Tiempo de Entrega (días)',
        help_text='Días de tiempo de entrega OEM'
    )
    
    is_discontinued = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Descontinuado',
        help_text='Item descontinuado por el fabricante'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Activo',
        help_text='Item activo y visible en el sistema'
    )
    
    display_order = forms.IntegerField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
        }),
        label='Orden de Visualización',
        help_text='Orden para mostrar en listas (menor = primero)'
    )
    
    def clean_part_number(self):
        """Limpiar el número de parte"""
        part_number = self.cleaned_data.get('part_number', '')
        return part_number.upper().strip()
    
    def clean(self):
        """Validaciones adicionales del formulario"""
        cleaned_data = super().clean()
        year_start = cleaned_data.get('year_start')
        year_end = cleaned_data.get('year_end')
        
        if year_start and year_end:
            if year_end < year_start:
                raise forms.ValidationError(
                    'El año final no puede ser menor al año inicial'
                )
        return cleaned_data


def get_brand_type_search_choices():
    """Opciones para filtro de búsqueda: 'Todos los tipos' + catálogo."""
    choices = get_brand_type_choices()
    return [('', 'Todos los tipos')] + [c for c in choices if c[0] != '']


class OEMBrandSearchForm(forms.Form):
    """Formulario de búsqueda para marcas OEM"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código o nombre...',
        }),
        label='Búsqueda'
    )

    brand_type = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Tipo'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['brand_type'].choices = get_brand_type_search_choices()

    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Estado'
    )


class OEMCatalogItemSearchForm(forms.Form):
    """Formulario de búsqueda para items del catálogo OEM"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número de parte o descripción...',
        }),
        label='Búsqueda'
    )
    
    oem_code = forms.CharField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Marca'
    )
    
    item_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + OEMCatalogItemForm.ITEM_TYPE_CHOICES[1:],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Tipo'
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Estado'
    )
    
    is_discontinued = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Descontinuados'),
            ('false', 'En Producción'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Descontinuado'
    )
