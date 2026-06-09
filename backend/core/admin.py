from django.contrib import admin

from .models import ChangeLog


@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ["id", "family", "actor", "action", "entity_type", "entity_repr", "created_at"]
    list_filter = ["action", "entity_type", "created_at"]
    search_fields = ["entity_repr", "actor__username", "family__name"]
