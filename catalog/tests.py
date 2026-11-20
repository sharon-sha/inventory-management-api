from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest
from rest_framework.test import APIClient

from accounts.models import UserProfile
from .models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestCatalogApi:
    def setup_method(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Office")

    def create_user(self, username, role):
        user = User.objects.create_user(username=username, password="A-strong-password-123!")
        UserProfile.objects.create(user=user, role=role)
        return user

    def test_api_requires_authentication(self, db):
        response = self.client.get(reverse("product-list"))

        assert response.status_code == 401

    def test_staff_can_read_but_cannot_create_products(self, db):
        staff = self.create_user("catalog-staff", UserProfile.Role.STAFF)
        self.client.force_authenticate(user=staff)

        get_response = self.client.get(reverse("product-list"))
        post_response = self.client.post(
            reverse("product-list"),
            {"name": "Pen", "sku": "PEN-1", "price": "1.25", "category": self.category.id},
            format="json",
        )

        assert get_response.status_code == 200
        assert post_response.status_code == 403

    def test_manager_can_create_update_and_delete_product(self, db):
        manager = self.create_user("catalog-manager", UserProfile.Role.INVENTORY_MANAGER)
        self.client.force_authenticate(user=manager)
        payload = {
            "name": "Blue Pen",
            "sku": "PEN-BLUE-1",
            "description": "Ballpoint pen",
            "price": "1.25",
            "category": self.category.id,
            "quantity": 50,
        }

        create_response = self.client.post(reverse("product-list"), payload, format="json")

        assert create_response.status_code == 201
        product_id = create_response.data["id"]
        product = Product.objects.get(pk=product_id)
        assert product.quantity == 0
        assert create_response.data["quantity"] == 0

        update_response = self.client.patch(
            reverse("product-detail", args=[product_id]),
            {"price": "1.50"},
            format="json",
        )
        assert update_response.status_code == 200
        assert update_response.data["price"] == "1.50"

        delete_response = self.client.delete(reverse("product-detail", args=[product_id]))
        assert delete_response.status_code == 204
        assert not Product.objects.filter(pk=product_id).exists()

    def test_duplicate_sku_is_rejected(self, db):
        manager = self.create_user("sku-manager", UserProfile.Role.INVENTORY_MANAGER)
        self.client.force_authenticate(user=manager)
        payload = {
            "name": "Pen",
            "sku": "UNIQUE-1",
            "price": "2.00",
            "category": self.category.id,
        }
        first = self.client.post(reverse("product-list"), payload, format="json")
        second = self.client.post(reverse("product-list"), payload, format="json")

        assert first.status_code == 201
        assert second.status_code == 400

    def test_search_and_product_filters(self, db):
        manager = self.create_user("filter-manager", UserProfile.Role.INVENTORY_MANAGER)
        self.client.force_authenticate(user=manager)
        Product.objects.create(
            name="Red Notebook",
            sku="NOTE-RED",
            price="4.50",
            category=self.category,
        )
        Product.objects.create(
            name="Green Notebook",
            sku="NOTE-GREEN",
            price="8.00",
            category=self.category,
        )

        response = self.client.get(
            reverse("product-list"),
            {"search": "Red", "category": self.category.id, "min_price": "4.00", "max_price": "5.00"},
        )

        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["sku"] == "NOTE-RED"

    def test_invalid_price_range_is_rejected(self, db):
        user = self.create_user("range-user", UserProfile.Role.STAFF)
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("product-list"), {"min_price": "10", "max_price": "2"})

        assert response.status_code == 400

    def test_product_list_is_paginated(self, db):
        user = self.create_user("page-user", UserProfile.Role.STAFF)
        self.client.force_authenticate(user=user)
        Product.objects.bulk_create(
            [
                Product(name=f"Item {number}", sku=f"ITEM-{number}", price="1.00", category=self.category)
                for number in range(25)
            ]
        )

        response = self.client.get(reverse("product-list"))

        assert response.status_code == 200
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20
        assert response.data["next"] is not None

    def test_category_product_count_and_protected_delete(self, db):
        manager = self.create_user("category-manager", UserProfile.Role.INVENTORY_MANAGER)
        self.client.force_authenticate(user=manager)
        Product.objects.create(
            name="Stapler",
            sku="STAPLER-1",
            price="5.99",
            category=self.category,
        )

        list_response = self.client.get(reverse("category-list"))
        delete_response = self.client.delete(
            reverse("category-detail", args=[self.category.id])
        )

        assert list_response.data["results"][0]["product_count"] == 1
        assert delete_response.status_code == 409
