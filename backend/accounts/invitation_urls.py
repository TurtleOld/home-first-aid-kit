from django.urls import path

from .views import (
    InvitationAcceptView,
    InvitationDetailView,
    InvitationListCreateView,
    InvitationRevokeView,
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
]
