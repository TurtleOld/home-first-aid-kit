import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("home_first_aid_kit")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "check-medicine-expiry": {
        "task": "notifications.tasks.send_expiry_notifications",
        "schedule": crontab(hour=9, minute=0),
    },
}
