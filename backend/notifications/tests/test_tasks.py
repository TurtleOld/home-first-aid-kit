from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Family, Membership
from medicines.models import Medicine
from notifications.models import PushSubscription
from notifications.tasks import build_digest, send_expiry_notifications

User = get_user_model()


class BuildDigestTests(TestCase):
    def test_no_message_when_nothing_needs_attention(self):
        family = Family.objects.create(name="Family")
        Medicine.objects.create(
            family=family,
            trade_name="Витамин С",
            expiry_date=timezone.localdate() + timedelta(days=200),
        )

        self.assertIsNone(build_digest(family.medicines.all()))

    def test_message_lists_expired_and_expiring_and_low_stock(self):
        family = Family.objects.create(name="Family")
        Medicine.objects.create(
            family=family,
            trade_name="Просрочено",
            expiry_date=timezone.localdate() - timedelta(days=1),
        )
        Medicine.objects.create(
            family=family,
            trade_name="Истекает",
            expiry_date=timezone.localdate() + timedelta(days=10),
        )
        Medicine.objects.create(
            family=family,
            trade_name="Заканчивается",
            expiry_date=timezone.localdate() + timedelta(days=200),
            quantity=1,
            low_stock_threshold=2,
        )

        message = build_digest(family.medicines.all())

        self.assertIn("просрочено: 1", message)
        self.assertIn("истекает в течение месяца: 1", message)
        self.assertIn("заканчивается: 1", message)


@override_settings(VAPID_PRIVATE_KEY="test-private-key", VAPID_CLAIMS_EMAIL="admin@example.com")
class SendExpiryNotificationsTests(TestCase):
    def setUp(self):
        self.family = Family.objects.create(name="Family")
        self.user = User.objects.create_user(username="member", password="strong-password-123")
        Membership.objects.create(user=self.user, family=self.family, role=Membership.Role.ADMIN)
        self.subscription = PushSubscription.objects.create(
            user=self.user,
            endpoint="https://push.example.com/abc",
            p256dh="p256dh-key",
            auth="auth-secret",
        )

    @patch("notifications.tasks.webpush")
    def test_sends_push_when_medicine_needs_attention(self, mock_webpush):
        Medicine.objects.create(
            family=self.family,
            trade_name="Просрочено",
            expiry_date=timezone.localdate() - timedelta(days=1),
        )

        send_expiry_notifications()

        mock_webpush.assert_called_once()
        _, kwargs = mock_webpush.call_args
        self.assertEqual(kwargs["subscription_info"]["endpoint"], self.subscription.endpoint)
        self.assertIn("просрочено: 1", kwargs["data"])

    @patch("notifications.tasks.webpush")
    def test_no_push_when_nothing_needs_attention(self, mock_webpush):
        Medicine.objects.create(
            family=self.family,
            trade_name="Витамин С",
            expiry_date=timezone.localdate() + timedelta(days=200),
        )

        send_expiry_notifications()

        mock_webpush.assert_not_called()

    @patch("notifications.tasks.webpush")
    def test_skips_when_vapid_not_configured(self, mock_webpush):
        Medicine.objects.create(
            family=self.family,
            trade_name="Просрочено",
            expiry_date=timezone.localdate() - timedelta(days=1),
        )

        with override_settings(VAPID_PRIVATE_KEY=""):
            send_expiry_notifications()

        mock_webpush.assert_not_called()


@override_settings(VAPID_PRIVATE_KEY="test-private-key", VAPID_CLAIMS_EMAIL="admin@example.com")
class SendExpiryNotificationsQueryCountTests(TestCase):
    @patch("notifications.tasks.webpush")
    def test_query_count_does_not_grow_with_number_of_families(self, mock_webpush):
        for index in range(3):
            family = Family.objects.create(name=f"Family {index}")
            user = User.objects.create_user(username=f"member{index}", password="strong-password-123")
            Membership.objects.create(user=user, family=family, role=Membership.Role.ADMIN)
            PushSubscription.objects.create(
                user=user,
                endpoint=f"https://push.example.com/{index}",
                p256dh="p256dh-key",
                auth="auth-secret",
            )
            Medicine.objects.create(
                family=family,
                trade_name="Просрочено",
                expiry_date=timezone.localdate() - timedelta(days=1),
            )

        with self.assertNumQueries(5):
            send_expiry_notifications()

        self.assertEqual(mock_webpush.call_count, 3)
