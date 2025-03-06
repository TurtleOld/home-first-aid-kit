from django.urls import path

from app.healthbox.apis import MedicamentListView

app_name = 'healthbox'
urlpatterns = [
    path('', MedicamentListView.as_view(), name='medicament_list'),
]
