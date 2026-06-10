from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Family, Membership
from core.models import ChangeLog
from medicines.models import Medicine, ShoppingItem


User = get_user_model()


@override_settings(
    SECRET_KEY="test-secret-key-with-enough-length-for-jwt-signing",
    SIMPLE_JWT={"SIGNING_KEY": "test-secret-key-with-enough-length-for-jwt-signing"},
)
class MedicinesApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_response = self.client.post(
            "/api/auth/register",
            {
                "username": "admin",
                "password": "strong-password-123",
                "family_name": "Main family",
            },
            format="json",
        )
        self.assertEqual(self.admin_response.status_code, status.HTTP_201_CREATED)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_response.data['access']}")
        self.family = Family.objects.get(id=self.admin_response.data["family"]["id"])
        self.user = User.objects.get(username="admin")

    def medicine_payload(self, **overrides):
        payload = {
            "trade_name": "Нурофен",
            "active_ingredient": "ибупрофен",
            "form": Medicine.Form.TABLETS,
            "dosage": "200 мг",
            "quantity": "12.00",
            "unit": Medicine.Unit.TABLET,
            "expiry_date": (timezone.localdate() + timedelta(days=20)).isoformat(),
            "storage": Medicine.Storage.KIT,
            "notes": "После еды",
        }
        payload.update(overrides)
        return payload

    def test_create_search_filter_and_changelog_for_medicine(self):
        create_response = self.client.post("/api/medicines", self.medicine_payload(), format="json")

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED, create_response.data)
        self.assertEqual(create_response.data["status"], "expiring_soon")
        medicine_id = create_response.data["id"]

        search_response = self.client.get("/api/medicines", {"search": "ибупрофен"})
        self.assertEqual(len(search_response.data), 1)
        self.assertEqual(search_response.data[0]["id"], medicine_id)

        status_response = self.client.get("/api/medicines", {"status": "expiring_soon"})
        self.assertEqual(len(status_response.data), 1)

        storage_response = self.client.get("/api/medicines", {"storage": Medicine.Storage.FRIDGE})
        self.assertEqual(storage_response.data, [])

        patch_response = self.client.patch(
            f"/api/medicines/{medicine_id}",
            {"quantity": "10.00"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK, patch_response.data)

        log_response = self.client.get("/api/changelog")
        self.assertIn("results", log_response.data)
        actions = [item["action"] for item in log_response.data["results"]]
        self.assertIn(ChangeLog.Action.CREATE, actions)
        self.assertIn(ChangeLog.Action.UPDATE, actions)

    def test_other_family_cannot_see_medicine(self):
        Medicine.objects.create(
            family=self.family,
            created_by=self.user,
            **self.medicine_payload(),
        )
        second_user = User.objects.create_user(username="other", password="strong-password-123")
        second_family = Family.objects.create(name="Other")
        Membership.objects.create(user=second_user, family=second_family, role=Membership.Role.ADMIN)
        login_response = self.client.post(
            "/api/auth/login",
            {"username": "other", "password": "strong-password-123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")

        response = self.client.get("/api/medicines")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_shopping_item_crud_writes_changelog(self):
        create_response = self.client.post(
            "/api/shopping-items",
            {"name": "Пластырь", "note": "Взять большой"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED, create_response.data)

        patch_response = self.client.patch(
            f"/api/shopping-items/{create_response.data['id']}",
            {"is_bought": True},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK, patch_response.data)

        delete_response = self.client.delete(f"/api/shopping-items/{create_response.data['id']}")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(ShoppingItem.objects.exists())
        self.assertEqual(ChangeLog.objects.filter(entity_type="shoppingitem").count(), 3)
