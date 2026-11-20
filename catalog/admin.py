from django.contrib import admin

from .models import Category, Product, ProductSupplier, Supplier


class ProductSupplierInline(admin.TabularInline):
    model = ProductSupplier
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "quantity")
    list_filter = ("category",)
    search_fields = ("name", "sku")
    inlines = (ProductSupplierInline,)


admin.site.register(Category)
admin.site.register(Supplier)
