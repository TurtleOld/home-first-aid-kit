from django.urls import path

from .views import PushSubscriptionView

urlpatterns = [
    path("push/subscription", PushSubscriptionView.as_view(), name="push-subscription"),
]
