from django.conf import settings
from django.db import models


class InventoryMovement(models.Model):
	"""Immutable audit entry for a change to a product's stock quantity."""

	class MovementType(models.TextChoices):
		ADJUSTMENT = "adjustment", "Manual adjustment"
		ORDER = "order", "Order fulfilled"
		CANCELLATION = "cancellation", "Order cancellation"

	product = models.ForeignKey(
		"catalog.Product",
		on_delete=models.PROTECT,
		related_name="inventory_movements",
	)
	movement_type = models.CharField(max_length=16, choices=MovementType.choices)
	quantity_delta = models.IntegerField(
		help_text="Signed quantity change: positive adds stock; negative removes stock."
	)
	order = models.ForeignKey(
		"orders.CustomerOrder",
		on_delete=models.SET_NULL,
		related_name="inventory_movements",
		null=True,
		blank=True,
	)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		related_name="inventory_movements",
		null=True,
		blank=True,
	)
	note = models.CharField(max_length=500, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at", "-id"]
		indexes = [
			models.Index(fields=["product", "-created_at"], name="movement_product_date_idx"),
			models.Index(fields=["movement_type", "-created_at"], name="movement_type_date_idx"),
		]
		constraints = [
			models.CheckConstraint(
				condition=~models.Q(quantity_delta=0),
				name="movement_delta_nonzero",
			),
		]

	def __str__(self):
		return f"{self.product.sku}: {self.quantity_delta:+d} ({self.get_movement_type_display()})"
