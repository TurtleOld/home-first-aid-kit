from django.urls import path

from app.healthbox.apis import MedicineBoxAPIView, MedicamentAPIView

app_name = 'healthbox'
urlpatterns = [
    path('', MedicineBoxAPIView.as_view(), name='medicine_box_list'),
    path('medicament/', MedicamentAPIView.as_view(), name='medicament_list'),
]
