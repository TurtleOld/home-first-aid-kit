from rest_framework import serializers
from app.healthbox.models import MedicineBox, Medicament


class MedicineBoxSerialize(serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField()
    location = serializers.CharField()

    class Meta:
        model = MedicineBox
        fields = ['name', 'description', 'location']


class MedicamentSerialize(serializers.ModelSerializer):
    name = serializers.CharField()
    medicament_type = serializers.CharField()
    quantity = serializers.IntegerField()
    expiration_date = serializers.DateField()
    medicine_box = serializers.PrimaryKeyRelatedField(
        queryset=MedicineBox.objects.all(),
        required=True,
    )

    class Meta:
        model = Medicament
        fields = ['name', 'medicament_type', 'quantity', 'medicine_box', 'expiration_date']

    def create(self, validated_data):
        medicament = Medicament.objects.create(**validated_data)
        return medicament