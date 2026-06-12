from django.test import TestCase, override_settings


class SchemaEndpointTests(TestCase):
    @override_settings(DEBUG=True)
    def test_schema_available_when_debug(self):
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.oai.openapi; charset=utf-8")

    @override_settings(DEBUG=False)
    def test_schema_not_found_when_not_debug(self):
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, 404)
