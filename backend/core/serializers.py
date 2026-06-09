from rest_framework import serializers

from .models import ChangeLog


class ChangeLogSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = ChangeLog
        fields = [
            "id",
            "actor",
            "action",
            "entity_type",
            "entity_repr",
            "changes",
            "created_at",
        ]

    def get_actor(self, obj):
        if not obj.actor_id:
            return None
        return {
            "id": obj.actor_id,
            "username": obj.actor.username,
            "email": obj.actor.email,
        }
