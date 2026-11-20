from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base for records that need creation and update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["name"], name="supplier_name_idx")]

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    suppliers = models.ManyToManyField(
        Supplier,
        through="ProductSupplier",
        related_name="products",
        blank=True,
    )

    class Meta:
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["category", "name"], name="product_category_name_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="product_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=0),
                name="product_quantity_nonnegative",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductSupplier(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    supplier_sku = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "supplier"],
                name="unique_product_supplier",
            ),
        ]

    def __str__(self):
        return f"{self.product.sku} supplied by {self.supplier.name}"
