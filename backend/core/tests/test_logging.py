import structlog
from django.test import TestCase
from structlog.testing import capture_logs


class StructlogMiddlewareTests(TestCase):
    def test_request_is_logged_with_request_id(self):
        with capture_logs(processors=[structlog.contextvars.merge_contextvars]) as captured:
            response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)

        events = {entry["event"]: entry for entry in captured}
        self.assertIn("request_started", events)
        self.assertIn("request_finished", events)
        self.assertIn("request_id", events["request_started"])
        self.assertEqual(events["request_started"]["log_level"], "info")
