"""
Forms for Product Catalog management (BrandType, ProductCategory, ProductType).
Used by catalog product-catalogs CRUD views.
"""
from django import forms
from core.models import BrandType, ProductCategory, ProductType


class BrandTypeForm(forms.ModelForm):
    """Form for BrandType (tipos de marca)."""

    class Meta:
        model = BrandType
        fields = ('code', 'name_es', 'name_en', 'display_order', 'is_active')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: OEM'}),
            'name_es': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre en español'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre en inglés (opcional)'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductCategoryForm(forms.ModelForm):
    """Form for ProductCategory (categorías de producto)."""

    class Meta:
        model = ProductCategory
        fields = ('code', 'name_es', 'name_en', 'display_order', 'is_active')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: part'}),
            'name_es': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre en español'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre en inglés (opcional)'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductTypeForm(forms.ModelForm):
    """Form for ProductType (tipos de producto)."""

    class Meta:
        model = ProductType
        fields = ('code', 'name_es', 'name_en', 'display_order', 'is_active')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: part'}),
            'name_es': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre en español'}),
            'name_en': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre en inglés (opcional)'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
