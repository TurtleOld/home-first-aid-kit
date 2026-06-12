from datetime import date, timedelta

from django.test import SimpleTestCase

from core.utils import caches_config, compute_expiry_status


class CachesConfigTests(SimpleTestCase):
    def test_uses_locmem_when_redis_url_is_empty(self):
        config = caches_config("")
        self.assertEqual(config["default"]["BACKEND"], "django.core.cache.backends.locmem.LocMemCache")

    def test_uses_redis_when_redis_url_is_set(self):
        config = caches_config("redis://redis:6379/0")
        self.assertEqual(config["default"]["BACKEND"], "django.core.cache.backends.redis.RedisCache")
        self.assertEqual(config["default"]["LOCATION"], "redis://redis:6379/0")


class ExpiryStatusTests(SimpleTestCase):
    def setUp(self):
        self.today = date(2026, 6, 9)

    def test_expired_boundary(self):
        self.assertEqual(compute_expiry_status(self.today - timedelta(days=1), self.today), "expired")
        self.assertEqual(compute_expiry_status(self.today, self.today), "expiring_soon")

    def test_soon_boundaries(self):
        self.assertEqual(compute_expiry_status(self.today + timedelta(days=29), self.today), "expiring_soon")
        self.assertEqual(compute_expiry_status(self.today + timedelta(days=30), self.today), "expiring_soon")
        self.assertEqual(
            compute_expiry_status(self.today + timedelta(days=31), self.today), "expiring_warning"
        )

    def test_warning_boundaries(self):
        self.assertEqual(
            compute_expiry_status(self.today + timedelta(days=89), self.today), "expiring_warning"
        )
        self.assertEqual(
            compute_expiry_status(self.today + timedelta(days=90), self.today), "expiring_warning"
        )
        self.assertEqual(compute_expiry_status(self.today + timedelta(days=91), self.today), "ok")
