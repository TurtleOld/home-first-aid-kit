from rest_framework import serializers

from app.healthbox.models import (
    Medicament,
    MedicineBox,
    Ointment,
    Spray,
    Tablet,
)


class MedicineBoxSerialize(serializers.ModelSerializer):
    """
    Serializer for the `MedicineBox` model.

    This serializer is used to represent
    the `MedicineBox` model in API responses.
    It includes the following fields:
    - `name`: The name of the medicine box.
    - `description`: A description of the medicine box.
    - `location`: The location where the medicine box is stored.

    Meta:
        model: The `MedicineBox` model.
        fields: The fields to include in the serialized representation.
    """

    class Meta:
        model = MedicineBox
        fields = ('name', 'description', 'location')


class MedicamentSerialize(serializers.ModelSerializer):
    """
    Serializer for the `Medicament` model.

    This serializer represents the `Medicament` model in API
    responses and supports creating new medicament objects.
    It includes a `details` field that dynamically
    provides additional information based
    on the specific type of medicament.

    Attributes
    ----------
        details (SerializerMethodField):
        A read-only field that retrieves additional
        details for the medicament's specific type.

    Meta:
        model: The `Medicament` model.
        fields: The fields to include in the serialized representation,
            including:
            - `id`: The unique identifier of the medicament.
            - `name`: The name of the medicament.
            - `medicament_type`: The type of medicament
            - `quantity`: The quantity of the medicament.
            - `expiration_date`: The expiration date of the medicament.
            - `medicine_box`: The medicine box associated with the medicament.
            - `details`: Additional details specific to the medicament type.

    Methods
    -------
        get_details: Retrieves additional details
                     for the medicament's specific type.
        create: Handles the creation of
                a new medicament object based on its type.

    """

    details = serializers.SerializerMethodField()

    class Meta:
        model = Medicament
        fields = (
            'id',
            'name',
            'medicament_type',
            'quantity',
            'expiration_date',
            'medicine_box',
            'details',
        )

    def get_details(self, obj):
        """
        Retrieve additional details for the medicament's specific type.

        This method checks the type of the medicament
        and returns the serialized data for the corresponding related object.

        Args:
        ----
            obj (Medicament): The medicament instance being serialized.

        Returns:
        -------
            dict: Serialized data for the related object,
                  or `None` if no related object exists.

        """
        if hasattr(obj, 'tablet'):
            return TabletSerialize(obj.tablet).data
        if hasattr(obj, 'spray'):
            return SpraySerialize(obj.spray).data
        if hasattr(obj, 'ointment'):
            return OintmentSerialize(obj.ointment).data
        return None

    def create(self, validated_data):
        """
        Create a new medicament object based on its type.

        This method handles the creation of
        a medicament object and its associated subtype.
        It extracts additional data from the
        request context to populate the subtype-specific fields.

        Args:
        ----
            validated_data (dict): The validated data for the medicament.

        Returns:
        -------
            Medicament: The newly created medicament object.

        Raises:
        ------
            ValidationError: If the provided data is invalid or incomplete.

        """
        medicament_type = validated_data.get('medicament_type')
        extra_data = self.context['request'].data

        if medicament_type == 'tablet':
            return Tablet.objects.create(
                name=validated_data['name'],
                medicament_type=validated_data['medicament_type'],
                quantity=validated_data['quantity'],
                expiration_date=validated_data['expiration_date'],
                medicine_box=validated_data['medicine_box'],
                dosage=extra_data.get('dosage'),
                shape=extra_data.get('shape'),
            )
        if medicament_type == 'spray':
            return Spray.objects.create(
                name=validated_data['name'],
                medicament_type=validated_data['medicament_type'],
                quantity=validated_data['quantity'],
                expiration_date=validated_data['expiration_date'],
                medicine_box=validated_data['medicine_box'],
                volume=extra_data.get('volume'),
                nozzle_type=extra_data.get('nozzle_type'),
            )
        if medicament_type == 'ointment':
            return Ointment.objects.create(
                name=validated_data['name'],
                medicament_type=validated_data['medicament_type'],
                quantity=validated_data['quantity'],
                expiration_date=validated_data['expiration_date'],
                medicine_box=validated_data['medicine_box'],
                weight=extra_data.get('weight'),
                texture=extra_data.get('texture'),
            )

        return Medicament.objects.create(**validated_data)


class TabletSerialize(serializers.ModelSerializer):
    """
    Serializer for the `Tablet` model.

    This serializer represents the `Tablet` model in API responses.
    It includes the following fields:
    - `dosage`: The dosage of the tablet.
    - `shape`: The shape of the tablet.

    Meta:
        model: The `Tablet` model.
        fields: The fields to include in the serialized representation.
    """

    class Meta:
        model = Tablet
        fields = ('dosage', 'shape')


class SpraySerialize(serializers.ModelSerializer):
    """
    Serializer for the `Spray` model.

    This serializer represents the `Spray` model in API responses.
    It includes the following fields:
    - `volume`: The volume of the spray.
    - `nozzle_type`: The type of nozzle used in the spray.

    Meta:
        model: The `Spray` model.
        fields: The fields to include in the serialized representation.
    """

    class Meta:
        model = Spray
        fields = ('volume', 'nozzle_type')


class OintmentSerialize(serializers.ModelSerializer):
    """
    Serializer for the `Ointment` model.

    This serializer represents the `Ointment` model in API responses.
    It includes the following fields:
    - `weight`: The weight of the ointment.
    - `texture`: The texture of the ointment.

    Meta:
        model: The `Ointment` model.
        fields: The fields to include in the serialized representation.
    """

    class Meta:
        model = Ointment
        fields = ('weight', 'texture')
