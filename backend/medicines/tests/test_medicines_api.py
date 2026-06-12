import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Family, Membership
from accounts.serializers import tokens_for_user
from core.models import ChangeLog
from medicines.models import Medicine, ShoppingItem

User = get_user_model()


def png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="PNG")
    return buffer.getvalue()


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

    def test_intake_decrements_quantity_and_logs(self):
        medicine = Medicine.objects.create(
            family=self.family,
            created_by=self.user,
            **self.medicine_payload(),
        )

        response = self.client.post(f"/api/medicines/{medicine.id}/intake", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["quantity"], "11.00")

        response = self.client.post(f"/api/medicines/{medicine.id}/intake", {"amount": "2.5"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["quantity"], "8.50")

        log_entry = ChangeLog.objects.filter(action=ChangeLog.Action.INTAKE).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.entity_type, "medicine")
        self.assertEqual(log_entry.changes["amount"], "2.50")
        self.assertEqual(log_entry.changes["quantity"], {"old": "11.00", "new": "8.50"})

    def test_intake_validates_amount_and_clamps_at_zero(self):
        medicine = Medicine.objects.create(
            family=self.family,
            created_by=self.user,
            **self.medicine_payload(quantity="2.00"),
        )

        for bad_amount in ["0", "-1", "abc"]:
            response = self.client.post(
                f"/api/medicines/{medicine.id}/intake", {"amount": bad_amount}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, bad_amount)

        response = self.client.post(f"/api/medicines/{medicine.id}/intake", {"amount": "100"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["quantity"], "0.00")

        response = self.client.post(f"/api/medicines/{medicine.id}/intake", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_intake_not_allowed_for_other_family(self):
        medicine = Medicine.objects.create(
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

        response = self.client.post(f"/api/medicines/{medicine.id}/intake", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_low_stock_flag_and_filter(self):
        low_medicine = Medicine.objects.create(
            family=self.family,
            created_by=self.user,
            **self.medicine_payload(quantity="3.00", low_stock_threshold="5.00"),
        )
        Medicine.objects.create(
            family=self.family,
            created_by=self.user,
            **self.medicine_payload(trade_name="Парацетамол", quantity="3.00"),
        )

        list_response = self.client.get("/api/medicines")
        flags = {item["trade_name"]: item["is_low_stock"] for item in list_response.data}
        self.assertTrue(flags["Нурофен"])
        self.assertFalse(flags["Парацетамол"])

        filtered_response = self.client.get("/api/medicines", {"low_stock": "true"})
        self.assertEqual(len(filtered_response.data), 1)
        self.assertEqual(filtered_response.data[0]["id"], low_medicine.id)

        patch_response = self.client.patch(
            f"/api/medicines/{low_medicine.id}",
            {"quantity": "10.00"},
            format="json",
        )
        self.assertFalse(patch_response.data["is_low_stock"])

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

    def test_instruction_file_rejects_disguised_html(self):
        malicious_file = SimpleUploadedFile(
            "instruction.pdf",
            b"<script>alert(1)</script>",
            content_type="application/pdf",
        )
        response = self.client.post(
            "/api/medicines",
            self.medicine_payload(instruction_file=malicious_file),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("instruction_file", response.data)

    def test_instruction_file_rejects_disallowed_extension(self):
        malicious_file = SimpleUploadedFile(
            "instruction.svg",
            b"<svg onload=alert(1)></svg>",
            content_type="image/svg+xml",
        )
        response = self.client.post(
            "/api/medicines",
            self.medicine_payload(instruction_file=malicious_file),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("instruction_file", response.data)

    def test_instruction_file_accepts_valid_pdf(self):
        valid_file = SimpleUploadedFile(
            "instruction.pdf",
            b"%PDF-1.4 minimal pdf content",
            content_type="application/pdf",
        )
        response = self.client.post(
            "/api/medicines",
            self.medicine_payload(instruction_file=valid_file),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    def test_photo_url_uses_random_family_scoped_path(self):
        photo = SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png")
        response = self.client.post(
            "/api/medicines",
            self.medicine_payload(photo=photo),
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        photo_url = response.data["photo"]
        self.assertIn(f"/api/media/medicine_photos/{self.family.id}/", photo_url)
        self.assertNotIn("photo.png", photo_url)

    def test_protected_media_access_control(self):
        photo = SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png")
        create_response = self.client.post(
            "/api/medicines",
            self.medicine_payload(photo=photo),
            format="multipart",
        )
        photo_url = create_response.data["photo"]

        own_response = self.client.get(photo_url)
        self.assertEqual(own_response.status_code, status.HTTP_200_OK)

        anonymous_client = APIClient()
        anonymous_response = anonymous_client.get(photo_url)
        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)

        other_user = User.objects.create_user(username="outsider", password="strong-password-123")
        other_family = Family.objects.create(name="Other family")
        Membership.objects.create(user=other_user, family=other_family, role=Membership.Role.ADMIN)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens_for_user(other_user)['access']}")
        other_response = other_client.get(photo_url)
        self.assertEqual(other_response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(DEBUG=False)
    def test_protected_media_uses_accel_redirect_outside_debug(self):
        photo = SimpleUploadedFile("photo.png", png_bytes(), content_type="image/png")
        create_response = self.client.post(
            "/api/medicines",
            self.medicine_payload(photo=photo),
            format="multipart",
        )
        photo_url = create_response.data["photo"]

        response = self.client.get(photo_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response["X-Accel-Redirect"].startswith("/protected-media/medicine_photos/"))
