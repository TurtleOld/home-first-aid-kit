from django.contrib import admin

from .models import Medicine, ShoppingItem


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ["id", "trade_name", "family", "expiry_date", "storage", "quantity", "unit"]
    list_filter = ["form", "unit", "storage", "expiry_date"]
    search_fields = ["trade_name", "active_ingredient", "family__name"]


@admin.register(ShoppingItem)
class ShoppingItemAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "family", "is_bought", "created_at"]
    list_filter = ["is_bought", "created_at"]
    search_fields = ["name", "family__name"]
