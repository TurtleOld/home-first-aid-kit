from django.utils.autoreload import raise_last_exception
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from yaml import serialize

from app.healthbox.models import MedicineBox, Medicament
from app.healthbox.serializers import MedicineBoxSerialize, MedicamentSerialize


class MedicineBoxAPIView(ListCreateAPIView):
    """Представление списка коробок с лекарствами."""
    queryset = MedicineBox.objects.all()
    serializer_class = MedicineBoxSerialize

    def list(self, request, *args, **kwargs):
        """Показать список аптечек."""
        queryset = self.get_queryset()
        serializer = MedicineBoxSerialize(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Создать аптечку."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)


class MedicamentAPIView(ListCreateAPIView):
    """Представление списка лекарств."""
    queryset = Medicament.objects.all()
    serializer_class = MedicamentSerialize

    def list(self, request, *args, **kwargs):
        """Показать список лекарств."""
        queryset = self.get_queryset()
        serializer = MedicamentSerialize(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """Создать\добавить лекарство в аптечку."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)
