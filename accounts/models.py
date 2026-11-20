from django.conf import settings
from django.db import models


class UserProfile(models.Model):
	"""Stores an application's role without replacing Django's existing user model."""

	class Role(models.TextChoices):
		ADMIN = "admin", "Admin"
		INVENTORY_MANAGER = "inventory_manager", "Inventory Manager"
		STAFF = "staff", "Staff"

	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="profile",
	)
	role = models.CharField(max_length=32, choices=Role.choices, default=Role.STAFF)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.user.get_username()} ({self.get_role_display()})"
