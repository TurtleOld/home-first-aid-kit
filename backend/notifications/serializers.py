from rest_framework import serializers

from .models import PushSubscription


class PushSubscriptionKeysSerializer(serializers.Serializer):
    p256dh = serializers.CharField()
    auth = serializers.CharField()


class PushSubscriptionSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=500)
    keys = PushSubscriptionKeysSerializer()

    def create(self, validated_data):
        keys = validated_data["keys"]
        subscription, _ = PushSubscription.objects.update_or_create(
            endpoint=validated_data["endpoint"],
            defaults={
                "user": self.context["request"].user,
                "p256dh": keys["p256dh"],
                "auth": keys["auth"],
            },
        )
        return subscription
