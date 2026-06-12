from django.urls import path

from .views import (
    FamilyMembersView,
    InvitationAcceptView,
    InvitationDetailView,
    InvitationListCreateView,
    InvitationRevokeView,
    MemberPasswordResetView,
)

urlpatterns = [
    path("invitations", InvitationListCreateView.as_view(), name="invitation-list"),
    path("invitations/<uuid:token>", InvitationDetailView.as_view(), name="invitation-detail"),
    path(
        "invitations/<uuid:token>/accept",
        InvitationAcceptView.as_view(),
        name="invitation-accept",
    ),
    path("invitations/<int:pk>", InvitationRevokeView.as_view(), name="invitation-revoke"),
    path("members", FamilyMembersView.as_view(), name="member-list"),
    path(
        "members/<int:user_id>/password",
        MemberPasswordResetView.as_view(),
        name="member-password-reset",
    ),
]
