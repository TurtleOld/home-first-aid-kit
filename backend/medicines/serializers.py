import json

from rest_framework import serializers

from .models import Medicine, ShoppingItem


class MultipartFriendlyJSONField(serializers.JSONField):
    """JSONField, принимающий JSON-строку — multipart-формы передают объект текстом."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            if not data.strip():
                return None
            try:
                data = json.loads(data)
            except ValueError:
                self.fail("invalid")
        return super().to_internal_value(data)


class MedicineSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    reference_data = MultipartFriendlyJSONField(required=False, allow_null=True)

    class Meta:
        model = Medicine
        fields = [
            "id",
            "trade_name",
            "active_ingredient",
            "form",
            "dosage",
            "quantity",
            "unit",
            "expiry_date",
            "storage",
            "notes",
            "photo",
            "instruction_file",
            "instruction_url",
            "instruction_note",
            "source_url",
            "reference_data",
            "status",
            "created_at",
            "updated_at",
            "created_by",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at", "created_by"]


class ShoppingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingItem
        fields = [
            "id",
            "medicine",
            "name",
            "note",
            "is_bought",
            "created_at",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "created_by"]
