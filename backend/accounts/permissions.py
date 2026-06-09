from rest_framework.permissions import BasePermission

from .models import Membership
from .selectors import get_current_membership


class IsFamilyMember(BasePermission):
    def has_permission(self, request, view):
        return get_current_membership(request.user) is not None


class IsFamilyAdmin(BasePermission):
    def has_permission(self, request, view):
        membership = get_current_membership(request.user)
        return bool(membership and membership.role == Membership.Role.ADMIN)
