from typing import Any
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Product, Category
from django.shortcuts import get_object_or_404
from cart.forms import CartAddProductForm
from .recommender import Recommender
from icecream import ic



class ProductListMixin(object):
    model = Product
    template_name = 'shop/product/list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(available=True)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class ProductListView(ProductListMixin, ListView):
    pass

class ProductListByCategoryView(ProductListMixin, ListView):
    def get_queryset(self):
        category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        return Product.objects.filter(category=category, available=True)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product/detail.html'
    context_object_name = 'product'
    def get_object(self, queryset=None):
        return get_object_or_404(Product, id=self.kwargs['id'], slug=self.kwargs['slug'], available=True)

    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        context['cart_product_form'] = CartAddProductForm()
        
        r = Recommender()
        ic(self.object)
        ic(r.suggest_products_for([self.object], 1))
        context['recommended_products'] = r.suggest_products_for([self.object], 1)

        return context