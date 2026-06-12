from django.test import TestCase


class AdminRouteRemovedTests(TestCase):
    def test_admin_route_returns_404(self):
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 404)
