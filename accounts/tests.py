from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile
from .permissions import IsAdmin, IsAdminOrInventoryManager

User = get_user_model()


class TestAuthenticationApi:
	def setup_method(self):
		self.client = APIClient()

	def test_registration_hashes_password_and_assigns_staff_role(self, db):
		response = self.client.post(
			reverse("accounts:register"),
			{
				"username": "new-user",
				"email": "new@example.com",
				"password": "A-strong-password-123!",
				"role": UserProfile.Role.ADMIN,
			},
			format="json",
		)

		assert response.status_code == 201
		user = User.objects.get(username="new-user")
		assert user.check_password("A-strong-password-123!")
		assert user.password != "A-strong-password-123!"
		assert user.profile.role == UserProfile.Role.STAFF
		assert "password" not in response.data

	def test_registration_rejects_weak_password(self, db):
		response = self.client.post(
			reverse("accounts:register"),
			{"username": "weak-user", "password": "123"},
			format="json",
		)

		assert response.status_code == 400
		assert not User.objects.filter(username="weak-user").exists()

	def test_login_returns_access_and_refresh_tokens(self, db):
		User.objects.create_user(username="login-user", password="A-strong-password-123!")

		response = self.client.post(
			reverse("accounts:login"),
			{"username": "login-user", "password": "A-strong-password-123!"},
			format="json",
		)

		assert response.status_code == 200
		assert "access" in response.data
		assert "refresh" in response.data

	def test_refresh_rotates_and_returns_tokens(self, db):
		user = User.objects.create_user(username="refresh-user", password="A-strong-password-123!")
		refresh = str(RefreshToken.for_user(user))

		response = self.client.post(
			reverse("accounts:refresh"), {"refresh": refresh}, format="json"
		)

		assert response.status_code == 200
		assert "access" in response.data
		assert "refresh" in response.data

	def test_logout_blacklists_the_users_refresh_token(self, db):
		user = User.objects.create_user(username="logout-user", password="A-strong-password-123!")
		refresh = RefreshToken.for_user(user)
		self.client.force_authenticate(user=user)

		response = self.client.post(
			reverse("accounts:logout"), {"refresh": str(refresh)}, format="json"
		)

		assert response.status_code == 205
		refresh_response = self.client.post(
			reverse("accounts:refresh"),
			{"refresh": str(refresh)},
			format="json",
		)
		assert refresh_response.status_code == 401

	def test_logout_requires_authentication(self, db):
		response = self.client.post(
			reverse("accounts:logout"), {"refresh": "not-a-token"}, format="json"
		)

		assert response.status_code == 401

	def test_logout_rejects_another_users_refresh_token(self, db):
		user = User.objects.create_user(username="owner", password="A-strong-password-123!")
		other_user = User.objects.create_user(username="other", password="A-strong-password-123!")
		refresh = str(RefreshToken.for_user(other_user))
		self.client.force_authenticate(user=user)

		response = self.client.post(
			reverse("accounts:logout"), {"refresh": refresh}, format="json"
		)

		assert response.status_code == 400


class TestRolePermissions:
	def setup_method(self):
		self.factory = APIRequestFactory()

	def test_staff_is_denied_manager_permission(self, db):
		user = User.objects.create_user(username="staff", password="A-strong-password-123!")
		UserProfile.objects.create(user=user, role=UserProfile.Role.STAFF)
		request = self.factory.get("/")
		request.user = user

		assert not IsAdminOrInventoryManager().has_permission(request, None)
		assert not IsAdmin().has_permission(request, None)

	def test_inventory_manager_gets_manager_permission_but_not_admin(self, db):
		user = User.objects.create_user(username="manager", password="A-strong-password-123!")
		UserProfile.objects.create(user=user, role=UserProfile.Role.INVENTORY_MANAGER)
		request = self.factory.get("/")
		request.user = user

		assert IsAdminOrInventoryManager().has_permission(request, None)
		assert not IsAdmin().has_permission(request, None)

	def test_admin_gets_both_role_permissions(self, db):
		user = User.objects.create_user(username="admin", password="A-strong-password-123!")
		UserProfile.objects.create(user=user, role=UserProfile.Role.ADMIN)
		request = self.factory.get("/")
		request.user = user

		assert IsAdminOrInventoryManager().has_permission(request, None)
		assert IsAdmin().has_permission(request, None)
