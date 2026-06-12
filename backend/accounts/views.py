from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Family, Invitation, Membership
from .permissions import IsFamilyAdmin, IsFamilyMember
from .selectors import get_current_membership
from .serializers import (
    AcceptInvitationSerializer,
    AdminPasswordResetSerializer,
    FamilyMemberSerializer,
    InvitationSerializer,
    MeSerializer,
    PasswordChangeSerializer,
    PublicInvitationSerializer,
    RegisterSerializer,
    serialize_me,
    tokens_for_user,
)


def revoke_all_tokens(user):
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def registration_is_open():
    return not Family.objects.exists()


class RegistrationStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"open": registration_is_open()})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not registration_is_open():
            return Response(
                {
                    "detail": (
                        "Регистрация закрыта: администратор уже зарегистрирован. "
                        "Попросите у него ссылку-приглашение."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        me = MeSerializer(serialize_me(user)).data
        return Response(
            {
                **tokens_for_user(user),
                "user": me["user"],
                "family": me["family"],
                "role": me["role"],
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(serialize_me(request.user)).data)


class InvitationListCreateView(generics.ListCreateAPIView):
    serializer_class = InvitationSerializer
    permission_classes = [IsAuthenticated, IsFamilyAdmin]

    def get_queryset(self):
        membership = get_current_membership(self.request.user)
        return Invitation.objects.filter(
            family=membership.family,
            is_active=True,
            accepted_by__isnull=True,
            expires_at__gt=timezone.now(),
        )

    def perform_create(self, serializer):
        membership = get_current_membership(self.request.user)
        serializer.save(family=membership.family, created_by=self.request.user)


class InvitationDetailView(generics.RetrieveAPIView):
    queryset = Invitation.objects.select_related("family")
    serializer_class = PublicInvitationSerializer
    permission_classes = [AllowAny]
    lookup_field = "token"


class InvitationAcceptView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request, token):
        invitation = get_object_or_404(Invitation.objects.select_related("family"), token=token)
        serializer = AcceptInvitationSerializer(
            data=request.data,
            context={"invitation": invitation},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        me = MeSerializer(serialize_me(user)).data
        return Response(
            {
                **tokens_for_user(user),
                "user": me["user"],
                "family": me["family"],
                "role": me["role"],
            },
            status=status.HTTP_201_CREATED,
        )


class InvitationRevokeView(APIView):
    permission_classes = [IsAuthenticated, IsFamilyAdmin]

    def delete(self, request, pk):
        membership = get_current_membership(request.user)
        invitation = get_object_or_404(
            Invitation,
            pk=pk,
            family=membership.family,
            is_active=True,
        )
        invitation.is_active = False
        invitation.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        revoke_all_tokens(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FamilyMembersView(generics.ListAPIView):
    serializer_class = FamilyMemberSerializer
    permission_classes = [IsAuthenticated, IsFamilyMember]

    def get_queryset(self):
        membership = get_current_membership(self.request.user)
        return (
            Membership.objects.filter(family=membership.family).select_related("user").order_by("joined_at")
        )


class MemberPasswordResetView(APIView):
    permission_classes = [IsAuthenticated, IsFamilyAdmin]

    def post(self, request, user_id):
        membership = get_current_membership(request.user)
        target = get_object_or_404(
            Membership.objects.select_related("user"),
            family=membership.family,
            user_id=user_id,
        )
        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target.user.set_password(serializer.validated_data["new_password"])
        target.user.save(update_fields=["password"])
        revoke_all_tokens(target.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            raise serializers.ValidationError({"refresh": "Обязательное поле."})

        try:
            RefreshToken(refresh).blacklist()
        except TokenError as exc:
            raise serializers.ValidationError({"refresh": str(exc)}) from exc

        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
