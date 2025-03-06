from django.urls import path

from app.healthbox.apis import MedicineBoxAPIView

app_name = 'healthbox'
urlpatterns = [
    path('', MedicineBoxAPIView.as_view(), name='medicine_box_list'),
]
