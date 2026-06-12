import json

from django.conf import settings
from pywebpush import WebPushException, webpush

from accounts.models import Family
from celery import shared_task

from .models import PushSubscription


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


@shared_task
def send_expiry_notifications():
    if not settings.VAPID_PRIVATE_KEY:
        return

    for family in Family.objects.all():
        medicines = list(family.medicines.all())
        message = build_digest(medicines)
        if not message:
            continue

        payload = {"title": "Домашняя аптечка", "body": message}
        subscriptions = PushSubscription.objects.filter(
            user__memberships__family=family
        ).distinct()
        for subscription in subscriptions:
            send_push(subscription, payload)
