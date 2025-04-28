from rest_framework import serializers
from app.healthbox.models import MedicineBox, Medicament, Tablet, Spray, \
    Ointment


class MedicineBoxSerialize(serializers.ModelSerializer):

    class Meta:
        model = MedicineBox
        fields = ['name', 'description', 'location']


class MedicamentSerialize(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()

    class Meta:
        model = Medicament
        fields = [
            'id',
            'name',
            'medicament_type',
            'quantity',
            'expiration_date',
            'medicine_box',
            'details'
        ]

    def get_details(self, obj):
        # Возвращаем специфические данные в зависимости от типа лекарства
        if hasattr(obj, 'tablet'):
            return TabletSerialize(obj.tablet).data
        elif hasattr(obj, 'spray'):
            return SpraySerialize(obj.spray).data
        elif hasattr(obj, 'ointment'):
            return OintmentSerialize(obj.ointment).data
        return None

    def create(self, validated_data):
        medicament_type = validated_data.get('medicament_type')
        extra_data = self.context['request'].data

        # Создаем объект подкласса напрямую
        if medicament_type == 'tablet':
            return Tablet.objects.create(
                name=validated_data['name'],
                medicament_type=validated_data['medicament_type'],
                quantity=validated_data['quantity'],
                expiration_date=validated_data['expiration_date'],
                medicine_box=validated_data['medicine_box'],
                dosage=extra_data.get('dosage'),
                shape=extra_data.get('shape')
            )
        elif medicament_type == 'spray':
            return Spray.objects.create(
                name=validated_data['name'],
                medicament_type=validated_data['medicament_type'],
                quantity=validated_data['quantity'],
                expiration_date=validated_data['expiration_date'],
                medicine_box=validated_data['medicine_box'],
                volume=extra_data.get('volume'),
                nozzle_type=extra_data.get('nozzle_type')
            )
        elif medicament_type == 'ointment':
            return Ointment.objects.create(
                name=validated_data['name'],
                medicament_type=validated_data['medicament_type'],
                quantity=validated_data['quantity'],
                expiration_date=validated_data['expiration_date'],
                medicine_box=validated_data['medicine_box'],
                weight=extra_data.get('weight'),
                texture=extra_data.get('texture')
            )

        # Если тип лекарства не определен, создаем обычный Medicament
        return Medicament.objects.create(**validated_data)


class TabletSerialize(serializers.ModelSerializer):
    class Meta:
        model = Tablet
        fields = ['dosage', 'shape']


class SpraySerialize(serializers.ModelSerializer):
    class Meta:
        model = Spray
        fields = ['volume', 'nozzle_type']


class OintmentSerialize(serializers.ModelSerializer):
    class Meta:
        model = Ointment
        fields = ['weight', 'texture']