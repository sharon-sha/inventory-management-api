from django.db.models import F
from rest_framework import serializers
from rest_framework.filters import BaseFilterBackend


class ProductQuerySerializer(serializers.Serializer):
    category = serializers.IntegerField(min_value=1, required=False)
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)
    in_stock = serializers.BooleanField(required=False)
    low_stock = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if attrs.get("min_price") is not None and attrs.get("max_price") is not None:
            if attrs["min_price"] > attrs["max_price"]:
                raise serializers.ValidationError(
                    {"max_price": "Must be greater than or equal to min_price."}
                )
        return attrs


class ProductFilterBackend(BaseFilterBackend):
    """Validate and apply supported product list query parameters."""

    def filter_queryset(self, request, queryset, view):
        # A plain dict avoids DRF treating absent HTML-form boolean query fields as False.
        query_serializer = ProductQuerySerializer(data=request.query_params.dict())
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        if "category" in filters:
            queryset = queryset.filter(category_id=filters["category"])
        if "min_price" in filters:
            queryset = queryset.filter(price__gte=filters["min_price"])
        if "max_price" in filters:
            queryset = queryset.filter(price__lte=filters["max_price"])
        if filters.get("in_stock") is True:
            queryset = queryset.filter(quantity__gt=0)
        elif filters.get("in_stock") is False:
            queryset = queryset.filter(quantity=0)
        if filters.get("low_stock") is True:
            queryset = queryset.filter(quantity__lte=F("low_stock_threshold"))
        elif filters.get("low_stock") is False:
            queryset = queryset.filter(quantity__gt=F("low_stock_threshold"))
        return queryset
