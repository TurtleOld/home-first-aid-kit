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
    is_low_stock = serializers.BooleanField(read_only=True)
    reference_data = MultipartFriendlyJSONField(required=False, allow_null=True)

    def to_internal_value(self, data):
        # Multipart-формы шлют пустой порог строкой "" — для DecimalField это значит null.
        if hasattr(data, "copy") and data.get("low_stock_threshold") == "":
            data = data.copy()
            data["low_stock_threshold"] = None
        return super().to_internal_value(data)

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
            "low_stock_threshold",
            "is_low_stock",
            "expiry_date",
            "storage",
            "notes",
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
        read_only_fields = ["id", "status", "is_low_stock", "created_at", "updated_at", "created_by"]


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
