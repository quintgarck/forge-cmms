"""
Views for Product Catalog management: hub index and CRUD for
BrandType (tipos de marca), ProductCategory, ProductType.
Uses Django ORM (core.models); no API.
"""
import logging
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.http import Http404

from core.models import BrandType, ProductCategory, ProductType
from ..forms.product_catalog_forms import BrandTypeForm, ProductCategoryForm, ProductTypeForm

logger = logging.getLogger(__name__)


# --- Hub (index) ---

class ProductCatalogsHubView(LoginRequiredMixin, TemplateView):
    """Vista índice de catálogos de producto/inventario: marcas, tipos de marca, categorías y tipos."""
    template_name = 'frontend/catalog/product_catalogs_hub.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Catálogos de producto e inventario'
        return context


# --- BrandType (tipos de marca) ---

class BrandTypeListView(LoginRequiredMixin, ListView):
    model = BrandType
    template_name = 'frontend/catalog/product_catalog_list.html'
    context_object_name = 'items'
    login_url = 'frontend:login'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Tipos de marca'
        context['catalog_label_singular'] = 'Tipo de marca'
        context['list_url_name'] = 'frontend:product_catalog_brand_type_list'
        context['create_url_name'] = 'frontend:product_catalog_brand_type_create'
        context['edit_url_name'] = 'frontend:product_catalog_brand_type_edit'
        context['delete_url_name'] = 'frontend:product_catalog_brand_type_delete'
        context['pk_field'] = 'code'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        return context

    def get_queryset(self):
        qs = BrandType.objects.all().order_by('display_order', 'code')
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(code__icontains=search) | qs.filter(name_es__icontains=search)
        status = self.request.GET.get('status', '')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


class BrandTypeCreateView(LoginRequiredMixin, CreateView):
    model = BrandType
    form_class = BrandTypeForm
    template_name = 'frontend/catalog/product_catalog_form.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Tipos de marca'
        context['catalog_label_singular'] = 'Tipo de marca'
        context['list_url_name'] = 'frontend:product_catalog_brand_type_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['is_create'] = True
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_brand_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de marca creado correctamente.')
        return super().form_valid(form)


class BrandTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = BrandType
    form_class = BrandTypeForm
    template_name = 'frontend/catalog/product_catalog_form.html'
    context_object_name = 'item'
    slug_url_kwarg = 'code'
    slug_field = 'code'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Tipos de marca'
        context['catalog_label_singular'] = 'Tipo de marca'
        context['list_url_name'] = 'frontend:product_catalog_brand_type_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['is_create'] = False
        context['pk_field'] = 'code'
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_brand_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de marca actualizado correctamente.')
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['code'].disabled = True
        return form


class BrandTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = BrandType
    template_name = 'frontend/catalog/product_catalog_confirm_delete.html'
    context_object_name = 'item'
    slug_url_kwarg = 'code'
    slug_field = 'code'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label_singular'] = 'Tipo de marca'
        context['list_url_name'] = 'frontend:product_catalog_brand_type_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['pk_field'] = 'code'
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_brand_type_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de marca eliminado correctamente.')
        return super().delete(request, *args, **kwargs)


# --- ProductCategory ---

class ProductCategoryCatalogListView(LoginRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'frontend/catalog/product_catalog_list.html'
    context_object_name = 'items'
    login_url = 'frontend:login'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Categorías de producto'
        context['catalog_label_singular'] = 'Categoría de producto'
        context['list_url_name'] = 'frontend:product_catalog_category_list'
        context['create_url_name'] = 'frontend:product_catalog_category_create'
        context['edit_url_name'] = 'frontend:product_catalog_category_edit'
        context['delete_url_name'] = 'frontend:product_catalog_category_delete'
        context['pk_field'] = 'code'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        return context

    def get_queryset(self):
        qs = ProductCategory.objects.all().order_by('display_order', 'code')
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(code__icontains=search) | qs.filter(name_es__icontains=search)
        status = self.request.GET.get('status', '')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


class ProductCategoryCatalogCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'frontend/catalog/product_catalog_form.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Categorías de producto'
        context['catalog_label_singular'] = 'Categoría de producto'
        context['list_url_name'] = 'frontend:product_catalog_category_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['is_create'] = True
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría de producto creada correctamente.')
        return super().form_valid(form)


class ProductCategoryCatalogUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'frontend/catalog/product_catalog_form.html'
    context_object_name = 'item'
    slug_url_kwarg = 'code'
    slug_field = 'code'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Categorías de producto'
        context['catalog_label_singular'] = 'Categoría de producto'
        context['list_url_name'] = 'frontend:product_catalog_category_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['is_create'] = False
        context['pk_field'] = 'code'
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_category_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría de producto actualizada correctamente.')
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['code'].disabled = True
        return form


class ProductCategoryCatalogDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductCategory
    template_name = 'frontend/catalog/product_catalog_confirm_delete.html'
    context_object_name = 'item'
    slug_url_kwarg = 'code'
    slug_field = 'code'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label_singular'] = 'Categoría de producto'
        context['list_url_name'] = 'frontend:product_catalog_category_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['pk_field'] = 'code'
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Categoría de producto eliminada correctamente.')
        return super().delete(request, *args, **kwargs)


# --- ProductType ---

class ProductTypeCatalogListView(LoginRequiredMixin, ListView):
    model = ProductType
    template_name = 'frontend/catalog/product_catalog_list.html'
    context_object_name = 'items'
    login_url = 'frontend:login'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Tipos de producto'
        context['catalog_label_singular'] = 'Tipo de producto'
        context['list_url_name'] = 'frontend:product_catalog_type_list'
        context['create_url_name'] = 'frontend:product_catalog_type_create'
        context['edit_url_name'] = 'frontend:product_catalog_type_edit'
        context['delete_url_name'] = 'frontend:product_catalog_type_delete'
        context['pk_field'] = 'code'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        return context

    def get_queryset(self):
        qs = ProductType.objects.all().order_by('display_order', 'code')
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(code__icontains=search) | qs.filter(name_es__icontains=search)
        status = self.request.GET.get('status', '')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


class ProductTypeCatalogCreateView(LoginRequiredMixin, CreateView):
    model = ProductType
    form_class = ProductTypeForm
    template_name = 'frontend/catalog/product_catalog_form.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Tipos de producto'
        context['catalog_label_singular'] = 'Tipo de producto'
        context['list_url_name'] = 'frontend:product_catalog_type_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['is_create'] = True
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de producto creado correctamente.')
        return super().form_valid(form)


class ProductTypeCatalogUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductType
    form_class = ProductTypeForm
    template_name = 'frontend/catalog/product_catalog_form.html'
    context_object_name = 'item'
    slug_url_kwarg = 'code'
    slug_field = 'code'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label'] = 'Tipos de producto'
        context['catalog_label_singular'] = 'Tipo de producto'
        context['list_url_name'] = 'frontend:product_catalog_type_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['is_create'] = False
        context['pk_field'] = 'code'
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_type_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de producto actualizado correctamente.')
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['code'].disabled = True
        return form


class ProductTypeCatalogDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductType
    template_name = 'frontend/catalog/product_catalog_confirm_delete.html'
    context_object_name = 'item'
    slug_url_kwarg = 'code'
    slug_field = 'code'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['catalog_label_singular'] = 'Tipo de producto'
        context['list_url_name'] = 'frontend:product_catalog_type_list'
        context['hub_url'] = reverse('frontend:product_catalogs_hub')
        context['pk_field'] = 'code'
        return context

    def get_success_url(self):
        return reverse('frontend:product_catalog_type_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de producto eliminado correctamente.')
        return super().delete(request, *args, **kwargs)
