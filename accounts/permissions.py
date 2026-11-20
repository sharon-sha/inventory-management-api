from rest_framework.permissions import BasePermission

from .models import UserProfile


class HasApplicationRole(BasePermission):
    """Base permission for users whose UserProfile role is in the allowed set."""

    allowed_roles = frozenset()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return UserProfile.objects.filter(
            user=user,
            role__in=self.allowed_roles,
        ).exists()


class IsAdmin(HasApplicationRole):
    allowed_roles = frozenset({UserProfile.Role.ADMIN})


class IsAdminOrInventoryManager(HasApplicationRole):
    allowed_roles = frozenset(
        {UserProfile.Role.ADMIN, UserProfile.Role.INVENTORY_MANAGER}
    )
