from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import F, Q
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsFamilyMember
from accounts.selectors import get_current_family
from core.mixins import create_change_log, diff_snapshots, snapshot_instance
from core.models import ChangeLog
from core.pagination import ChangeLogPagination
from core.serializers import ChangeLogSerializer

from .models import Medicine, ShoppingItem
from .serializers import MedicineSerializer, ShoppingItemSerializer


class FamilyScopedModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsFamilyMember]
    log_fields = []

    def get_family(self):
        return get_current_family(self.request.user)

    def perform_create(self, serializer):
        instance = serializer.save(family=self.get_family(), created_by=self.request.user)
        create_change_log(
            family=instance.family,
            actor=self.request.user,
            action=ChangeLog.Action.CREATE,
            instance=instance,
            changes={"created": snapshot_instance(instance, self.log_fields)},
        )

    def perform_update(self, serializer):
        before = snapshot_instance(self.get_object(), self.log_fields)
        instance = serializer.save()
        after = snapshot_instance(instance, self.log_fields)
        changes = diff_snapshots(before, after)
        if changes:
            create_change_log(
                family=instance.family,
                actor=self.request.user,
                action=ChangeLog.Action.UPDATE,
                instance=instance,
                changes=changes,
            )

    def perform_destroy(self, instance):
        family = instance.family
        changes = {"deleted": snapshot_instance(instance, self.log_fields)}
        create_change_log(
            family=family,
            actor=self.request.user,
            action=ChangeLog.Action.DELETE,
            instance=instance,
            changes=changes,
        )
        instance.delete()


class MedicineViewSet(FamilyScopedModelViewSet):
    serializer_class = MedicineSerializer
    log_fields = [
        "trade_name",
        "active_ingredient",
        "form",
        "dosage",
        "quantity",
        "unit",
        "low_stock_threshold",
        "expiry_date",
        "storage",
        "notes",
        "instruction_url",
        "instruction_note",
        "source_url",
        "reference_data",
    ]

    def get_queryset(self):
        queryset = Medicine.objects.filter(family=self.get_family()).select_related("created_by")
        search = self.request.query_params.get("search")
        storage = self.request.query_params.get("storage")
        ordering = self.request.query_params.get("ordering")

        if search:
            queryset = queryset.filter(
                Q(trade_name__icontains=search) | Q(active_ingredient__icontains=search)
            )
        if storage:
            queryset = queryset.filter(storage=storage)
        if self.request.query_params.get("low_stock") in {"true", "1"}:
            queryset = queryset.filter(
                low_stock_threshold__isnull=False,
                quantity__lte=F("low_stock_threshold"),
            )
        allowed_orderings = {
            "expiry_date",
            "-expiry_date",
            "trade_name",
            "-trade_name",
            "created_at",
            "-created_at",
        }
        if ordering in allowed_orderings:
            queryset = queryset.order_by(ordering)
        return queryset

    def list(self, request, *args, **kwargs):
        status_filter = request.query_params.get("status")
        if not status_filter:
            return super().list(request, *args, **kwargs)

        queryset = [obj for obj in self.filter_queryset(self.get_queryset()) if obj.status == status_filter]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def intake(self, request, pk=None):
        """Отметить приём: списать amount (по умолчанию 1) с остатка, не уходя в минус."""
        medicine = self.get_object()

        try:
            amount = Decimal(str(request.data.get("amount", "1"))).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise serializers.ValidationError({"amount": "Укажите число больше нуля."}) from exc
        if amount <= 0:
            raise serializers.ValidationError({"amount": "Укажите число больше нуля."})

        with transaction.atomic():
            medicine = Medicine.objects.select_for_update().get(pk=medicine.pk)

            if medicine.quantity <= 0:
                raise serializers.ValidationError({"amount": "Лекарство закончилось — остаток уже нулевой."})

            old_quantity = medicine.quantity
            medicine.quantity = max(Decimal("0"), old_quantity - amount)
            medicine.save(update_fields=["quantity", "updated_at"])

            create_change_log(
                family=medicine.family,
                actor=request.user,
                action=ChangeLog.Action.INTAKE,
                instance=medicine,
                changes={
                    "amount": str(amount),
                    "quantity": {"old": str(old_quantity), "new": str(medicine.quantity)},
                },
            )
        return Response(self.get_serializer(medicine).data)


class ShoppingItemViewSet(FamilyScopedModelViewSet):
    serializer_class = ShoppingItemSerializer
    log_fields = ["medicine", "name", "note", "is_bought"]

    def get_queryset(self):
        return ShoppingItem.objects.filter(family=self.get_family()).select_related("medicine", "created_by")

    def perform_create(self, serializer):
        medicine = serializer.validated_data.get("medicine")
        if medicine and medicine.family_id != self.get_family().id:
            raise serializers.ValidationError({"medicine": "Лекарство не найдено."})
        super().perform_create(serializer)

    def perform_update(self, serializer):
        medicine = serializer.validated_data.get("medicine")
        if medicine and medicine.family_id != self.get_family().id:
            raise serializers.ValidationError({"medicine": "Лекарство не найдено."})
        super().perform_update(serializer)


class ChangeLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ChangeLogSerializer
    permission_classes = [IsAuthenticated, IsFamilyMember]
    pagination_class = ChangeLogPagination

    def get_queryset(self):
        return (
            ChangeLog.objects.filter(family=get_current_family(self.request.user))
            .select_related("actor", "family")
            .order_by("-created_at", "-id")
        )
