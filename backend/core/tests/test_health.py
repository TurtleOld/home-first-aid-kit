from unittest.mock import patch

from django.test import TestCase


class HealthEndpointTests(TestCase):
    def test_returns_ok_when_all_checks_pass(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "checks": {"database": "ok", "cache": "ok"}},
        )

    @patch("core.views._check_database", return_value="error")
    def test_returns_degraded_when_database_check_fails(self, mock_check):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertEqual(response.json()["checks"]["database"], "error")

    @patch("core.views._check_cache", return_value="error")
    def test_returns_degraded_when_cache_check_fails(self, mock_check):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertEqual(response.json()["checks"]["cache"], "error")
