from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from notifications.models import PushSubscription

User = get_user_model()


@override_settings(
    SECRET_KEY="test-secret-key-with-enough-length-for-jwt-signing",
    SIMPLE_JWT={"SIGNING_KEY": "test-secret-key-with-enough-length-for-jwt-signing"},
)
class PushSubscriptionApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        response = self.client.post(
            "/api/auth/register",
            {
                "username": "subscriber",
                "password": "strong-password-123",
                "family_name": "Subscriber family",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.user = User.objects.get(username="subscriber")

    def subscription_payload(self, endpoint="https://push.example.com/abc"):
        return {
            "endpoint": endpoint,
            "keys": {"p256dh": "p256dh-key", "auth": "auth-secret"},
        }

    def test_create_and_update_subscription(self):
        response = self.client.post("/api/push/subscription", self.subscription_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PushSubscription.objects.filter(user=self.user).count(), 1)

        response = self.client.post("/api/push/subscription", self.subscription_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PushSubscription.objects.filter(user=self.user).count(), 1)

    def test_delete_subscription(self):
        self.client.post("/api/push/subscription", self.subscription_payload(), format="json")

        response = self.client.delete(
            "/api/push/subscription", {"endpoint": "https://push.example.com/abc"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PushSubscription.objects.filter(user=self.user).count(), 0)

    def test_subscription_requires_authentication(self):
        self.client.credentials()

        response = self.client.post("/api/push/subscription", self.subscription_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
