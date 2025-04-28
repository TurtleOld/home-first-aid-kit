from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

app_name = 'api'
urlpatterns = [
    path('', include('app.healthbox', namespace='healthbox')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
]
