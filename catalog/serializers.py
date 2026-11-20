from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "description", "product_count", "created_at", "updated_at")
        read_only_fields = ("id", "product_count", "created_at", "updated_at")


class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "sku",
            "description",
            "price",
            "category",
            "quantity",
            "low_stock_threshold",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "quantity", "created_at", "updated_at")
