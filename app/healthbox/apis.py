from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response

from app.healthbox.models import Medicament, MedicineBox
from app.healthbox.serializers import MedicamentSerialize, MedicineBoxSerialize


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
    """
    API View for listing and creating Medicament objects.

    This view provides the following functionality:
    - Retrieve a list of all Medicament objects with related data.
    - Create a new Medicament object and add it to the database.

    Attributes
    ----------
        queryset (QuerySet): The base queryset
                             for retrieving Medicament objects.
        serializer_class (Serializer):
        The serializer class used
        for serializing/deserializing Medicament objects.

    Methods
    -------
        get_queryset: Customizes the queryset
                      to include related objects using `select_related`.
        list: Handles GET requests to retrieve
              and serialize a list of Medicament objects.
        create: Handles POST requests to create
                and save a new Medicament object.

    """

    queryset = Medicament.objects.all()
    serializer_class = MedicamentSerialize

    def get_queryset(self):
        """
        Customize the queryset to optimize database queries.

        Returns
        -------
            QuerySet: A queryset that includes related objects
                      using `select_related` to reduce database hits.

        """
        return Medicament.objects.select_related(
            'tablet',
            'spray',
            'ointment',
        ).all()

    def list(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve a list of Medicament objects.

        Args:
        ----
            request (HttpRequest): The incoming HTTP request.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
        -------
            Response: A serialized list of Medicament objects
                      with status code 200.

        """
        queryset = self.get_queryset()
        serializer = MedicamentSerialize(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Handle POST requests to create a new Medicament object.

        Args:
        ----
            request (HttpRequest): The incoming HTTP request containing
            the data for the new Medicament.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
        -------
            Response: The serialized data of the newly created
            Medicament object with status code 201.

        """
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)
