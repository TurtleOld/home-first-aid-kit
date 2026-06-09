from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient


@override_settings(
    SECRET_KEY="test-secret-key-with-enough-length-for-jwt-signing",
    SIMPLE_JWT={"SIGNING_KEY": "test-secret-key-with-enough-length-for-jwt-signing"},
)
class DrugLookupViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        response = self.client.post(
            "/api/auth/register",
            {
                "username": "admin",
                "password": "strong-password-123",
                "family_name": "Main family",
            },
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    @patch("medicines.reference_parser.views.list_variants")
    def test_forms_endpoint_returns_variants(self, list_variants_mock):
        list_variants_mock.return_value = {
            "trade_name": "Тест",
            "source_url": "https://example.test/drug",
            "variants": [{"form": "капсулы", "dosage": "300 мг"}],
            "single_variant": False,
        }

        response = self.client.post(
            "/api/drug-lookup/forms",
            {"url": "https://example.test/drug"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["ok"])
        self.assertEqual(response.data["variants"][0]["form"], "капсулы")

    @patch("medicines.reference_parser.views.parse_variant")
    def test_parse_endpoint_returns_fields(self, parse_variant_mock):
        parse_variant_mock.return_value = {
            "source_url": "https://example.test/drug",
            "selected": {"form": "капсулы", "dosage": "300 мг"},
            "selected_matches_description": {"form_ok": True, "dosage_ok": True, "overall": True},
            "fields": {"trade_name": "Тест", "form": "капсулы", "dosage": "300 мг"},
            "reference_data": {"section": "text"},
        }

        response = self.client.post(
            "/api/drug-lookup/parse",
            {"url": "https://example.test/drug", "form": "капсулы", "dosage": "300 мг"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data["ok"])
        self.assertEqual(response.data["fields"]["trade_name"], "Тест")

    def test_rejects_non_http_url(self):
        response = self.client.post("/api/drug-lookup/forms", {"url": "ftp://example.test"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["ok"])
