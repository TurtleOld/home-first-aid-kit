from datetime import timedelta


def compute_expiry_status(expiry_date, today):
    if expiry_date < today:
        return "expired"
    if expiry_date <= today + timedelta(days=30):
        return "expiring_soon"
    if expiry_date <= today + timedelta(days=90):
        return "expiring_warning"
    return "ok"


def caches_config(redis_url):
    """Cache backend config: Redis when REDIS_URL is set, LocMemCache otherwise.

    LocMemCache is per-process, so with multiple gunicorn workers throttle
    limits are counted per worker and the reference cache isn't shared.
    """
    if redis_url:
        return {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": redis_url,
            }
        }
    return {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "home-first-aid-kit",
        }
    }
