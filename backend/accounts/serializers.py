from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Family, Invitation, Membership
from .selectors import get_current_membership


User = get_user_model()


def tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ["id", "name", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    family = FamilySerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["role", "joined_at", "family"]


class MeSerializer(serializers.Serializer):
    user = UserSerializer()
    family = FamilySerializer(allow_null=True)
    role = serializers.CharField(allow_null=True)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    family_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        family_name = validated_data.pop("family_name")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        family = Family.objects.create(name=family_name)
        Membership.objects.create(
            user=user,
            family=family,
            role=Membership.Role.ADMIN,
        )
        return user


class InvitationSerializer(serializers.ModelSerializer):
    invite_url = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "id",
            "token",
            "family",
            "created_by",
            "created_at",
            "expires_at",
            "accepted_by",
            "is_active",
            "invite_url",
        ]
        read_only_fields = fields

    def get_invite_url(self, obj):
        request = self.context.get("request")
        path = f"/invite/{obj.token}"
        return request.build_absolute_uri(path) if request else path


class PublicInvitationSerializer(serializers.ModelSerializer):
    family = FamilySerializer(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invitation
        fields = ["token", "family", "expires_at", "is_valid"]


class AcceptInvitationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def validate(self, attrs):
        invitation = self.context["invitation"]
        if not invitation.is_valid:
            raise serializers.ValidationError("Приглашение недействительно или истекло.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        invitation = self.context["invitation"]
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        Membership.objects.create(
            user=user,
            family=invitation.family,
            role=Membership.Role.MEMBER,
        )
        invitation.accepted_by = user
        invitation.is_active = False
        invitation.save(update_fields=["accepted_by", "is_active"])
        return user


def serialize_me(user):
    membership = get_current_membership(user)
    return {
        "user": user,
        "family": membership.family if membership else None,
        "role": membership.role if membership else None,
    }
