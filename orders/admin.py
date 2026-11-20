from django.contrib import admin

from .models import CustomerOrder, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("unit_price",)


@admin.register(CustomerOrder)
class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ("public_id", "customer_name", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "customer_email", "public_id")
    inlines = (OrderItemInline,)
