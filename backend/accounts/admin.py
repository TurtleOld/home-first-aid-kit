from django.contrib import admin

from .models import Family, Invitation, Membership


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_at"]
    search_fields = ["name"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "family", "role", "joined_at"]
    list_filter = ["role"]
    search_fields = ["user__username", "family__name"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["id", "family", "created_by", "expires_at", "accepted_by", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["family__name", "created_by__username", "accepted_by__username"]
