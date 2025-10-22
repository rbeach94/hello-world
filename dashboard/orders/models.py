from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Order(models.Model):
    class ProductionStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        AWAITING_GARMENTS = "awaiting_garments", "Awaiting Garments"
        READY = "ready", "Ready"
        COMPLETE = "complete", "Complete"

    class DecorationType(models.TextChoices):
        EMBROIDERY = "embroidery", "Embroidery"
        PRINT = "print", "Print"
        BOTH = "both", "Both"

    order_number = models.CharField(max_length=64, unique=True)
    customer_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    production_status = models.CharField(
        max_length=32,
        choices=ProductionStatus.choices,
        default=ProductionStatus.PENDING,
    )
    decoration_type = models.CharField(
        max_length=32,
        choices=DecorationType.choices,
        default=DecorationType.PRINT,
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
    )
    preview_image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    external_reference = models.CharField(
        max_length=128,
        blank=True,
        help_text="Link to the source system such as Google Sheets row ID.",
    )

    class Meta:
        ordering = ["due_date", "order_number"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["production_status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["decoration_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.order_number} - {self.customer_name}"


class OrderAuditTrail(models.Model):
    order = models.ForeignKey(Order, related_name="audit_trail", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    previous_status = models.CharField(max_length=32, blank=True)
    new_status = models.CharField(max_length=32, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.order.order_number} changed to {self.new_status}"


class OrderGarment(models.Model):
    class GarmentStatus(models.TextChoices):
        NEEDS_ORDERING = "needs_ordering", "Needs Ordering"
        ORDERED = "ordered", "Ordered"
        IN_STOCK = "in_stock", "In Stock"

    order = models.ForeignKey(Order, related_name="garments", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    colour = models.CharField(max_length=128, blank=True)
    size = models.CharField(max_length=64, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=32,
        choices=GarmentStatus.choices,
        default=GarmentStatus.NEEDS_ORDERING,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["order__due_date", "order__order_number", "name"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.name} ({self.quantity})"

    @property
    def needs_purchase(self) -> bool:
        return self.status == self.GarmentStatus.NEEDS_ORDERING
