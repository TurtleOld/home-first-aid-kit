import json

import structlog
from celery import shared_task
from django.conf import settings
from pywebpush import WebPushException, webpush

from accounts.models import Family

logger = structlog.get_logger(__name__)


def build_digest(medicines):
    expired = sum(1 for medicine in medicines if medicine.status == "expired")
    expiring_soon = sum(1 for medicine in medicines if medicine.status == "expiring_soon")
    low_stock = sum(1 for medicine in medicines if medicine.is_low_stock)

    parts = []
    if expired:
        parts.append(f"просрочено: {expired}")
    if expiring_soon:
        parts.append(f"истекает в течение месяца: {expiring_soon}")
    if low_stock:
        parts.append(f"заканчивается: {low_stock}")

    if not parts:
        return None

    return "Аптечка: " + ", ".join(parts)


def send_push(subscription, payload):
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"},
        )
    except WebPushException as error:
        if error.response is not None and error.response.status_code in (404, 410):
            subscription.delete()
        else:
            logger.warning(
                "push_send_failed",
                subscription_id=subscription.id,
                status_code=getattr(error.response, "status_code", None),
            )


@shared_task
def send_expiry_notifications():
    if not settings.VAPID_PRIVATE_KEY:
        return

    families = Family.objects.prefetch_related("medicines", "memberships__user__push_subscriptions")
    for family in families:
        medicines = list(family.medicines.all())
        message = build_digest(medicines)
        if not message:
            continue

        payload = {"title": "Домашняя аптечка", "body": message}
        subscriptions = {
            subscription
            for membership in family.memberships.all()
            for subscription in membership.user.push_subscriptions.all()
        }
        for subscription in subscriptions:
            send_push(subscription, payload)
