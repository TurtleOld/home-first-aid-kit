from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Invitation
from .permissions import IsFamilyAdmin
from .selectors import get_current_membership
from .serializers import (
    AcceptInvitationSerializer,
    InvitationSerializer,
    MeSerializer,
    PublicInvitationSerializer,
    RegisterSerializer,
    serialize_me,
    tokens_for_user,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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


LoginView = TokenObtainPairView
RefreshView = TokenRefreshView
