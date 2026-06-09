from decimal import Decimal

from django.forms.models import model_to_dict

from .models import ChangeLog


def _json_safe(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "url"):
        return value.url if value else ""
    return value


def snapshot_instance(instance, fields):
    raw = model_to_dict(instance, fields=fields)
    return {key: _json_safe(value) for key, value in raw.items()}


def diff_snapshots(before, after):
    return {
        key: {"old": before.get(key), "new": after.get(key)}
        for key in sorted(set(before) | set(after))
        if before.get(key) != after.get(key)
    }


def create_change_log(*, family, actor, action, instance, changes):
    ChangeLog.objects.create(
        family=family,
        actor=actor if actor and actor.is_authenticated else None,
        action=action,
        entity_type=instance._meta.model_name,
        entity_repr=str(instance)[:255],
        changes=changes,
    )
