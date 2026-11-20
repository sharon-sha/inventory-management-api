from django.db.models import Count
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdminOrInventoryManager

from .filters import ProductFilterBackend
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class ResourceConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This resource is in use and cannot be deleted."
    default_code = "resource_conflict"


class CatalogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class RoleProtectedModelViewSet(viewsets.ModelViewSet):
    """Allow authenticated reads; restrict all write actions to managers and admins."""

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            permission_classes = (IsAuthenticated,)
        else:
            permission_classes = (IsAdminOrInventoryManager,)
        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise ResourceConflict() from exc


class CategoryViewSet(RoleProtectedModelViewSet):
    serializer_class = CategorySerializer
    pagination_class = CatalogPagination

    def get_queryset(self):
        return Category.objects.annotate(product_count=Count("products")).order_by("name")


class ProductViewSet(RoleProtectedModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = CatalogPagination
    filter_backends = (ProductFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ("name", "sku", "description")
    ordering_fields = ("name", "price", "quantity", "created_at")
    ordering = ("name", "id")

    def get_queryset(self):
        return Product.objects.select_related("category").all()
