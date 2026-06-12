from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import Family
from core.utils import compute_expiry_status
from core.validators import (
    validate_instruction_file_content,
    validate_instruction_file_extension,
    validate_instruction_file_size,
)


class Medicine(models.Model):
    class Form(models.TextChoices):
        TABLETS = "tablets", "Tablets"
        SYRUP = "syrup", "Syrup"
        OINTMENT = "ointment", "Ointment"
        DROPS = "drops", "Drops"
        CAPSULES = "capsules", "Capsules"
        SPRAY = "spray", "Spray"
        OTHER = "other", "Other"

    class Unit(models.TextChoices):
        TABLET = "tablet", "Tablet"
        ML = "ml", "ml"
        G = "g", "g"
        PIECE = "piece", "Piece"
        DROP = "drop", "Drop"
        OTHER = "other", "Other"

    class Storage(models.TextChoices):
        KIT = "kit", "Kit"
        FRIDGE = "fridge", "Fridge"
        KIDS_KIT = "kids_kit", "Kids kit"

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="medicines")
    trade_name = models.CharField(max_length=180)
    active_ingredient = models.CharField(max_length=180, blank=True)
    form = models.CharField(max_length=20, choices=Form.choices, default=Form.OTHER)
    dosage = models.CharField(max_length=120, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    unit = models.CharField(max_length=20, choices=Unit.choices, default=Unit.PIECE)
    low_stock_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Остаток, при котором лекарство считается заканчивающимся; пусто — не отслеживать.",
    )
    expiry_date = models.DateField()
    storage = models.CharField(max_length=20, choices=Storage.choices, default=Storage.KIT)
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to="medicine_photos/", null=True, blank=True)
    instruction_file = models.FileField(
        upload_to="medicine_instructions/",
        null=True,
        blank=True,
        validators=[
            validate_instruction_file_extension,
            validate_instruction_file_size,
            validate_instruction_file_content,
        ],
    )
    instruction_url = models.URLField(blank=True)
    instruction_note = models.TextField(blank=True)
    source_url = models.URLField(blank=True)
    reference_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_medicines",
    )

    class Meta:
        ordering = ["expiry_date", "trade_name"]

    def __str__(self):
        return self.trade_name

    @property
    def status(self):
        return compute_expiry_status(self.expiry_date, timezone.localdate())

    @property
    def is_low_stock(self):
        return self.low_stock_threshold is not None and self.quantity <= self.low_stock_threshold


class ShoppingItem(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="shopping_items")
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shopping_items",
    )
    name = models.CharField(max_length=180)
    note = models.TextField(blank=True)
    is_bought = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_shopping_items",
    )

    class Meta:
        ordering = ["is_bought", "-created_at", "-id"]

    def __str__(self):
        return self.name
