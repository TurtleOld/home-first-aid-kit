from django.urls import include, path

from core.views import ProtectedMediaView, SchemaSwaggerView, SchemaView, api_root, health

urlpatterns = [
    path("api/", api_root, name="api-root"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("accounts.invitation_urls")),
    path("api/", include("medicines.urls")),
    path("api/", include("notifications.urls")),
    path("api/health/", health, name="health"),
    path("api/media/<path:path>", ProtectedMediaView.as_view(), name="protected-media"),
    path("api/schema/", SchemaView.as_view(), name="schema"),
    path("api/docs/", SchemaSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api-auth/", include("rest_framework.urls")),
]
