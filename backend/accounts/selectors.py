from .models import Membership


def get_current_membership(user):
    if not user or not user.is_authenticated:
        return None
    return (
        Membership.objects.select_related("family", "user")
        .filter(user=user)
        .order_by("joined_at")
        .first()
    )


def get_current_family(user):
    membership = get_current_membership(user)
    return membership.family if membership else None
