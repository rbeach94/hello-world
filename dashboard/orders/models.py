from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Order(models.Model):
    class ProductionStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        IN_PRODUCTION = "in_production", "In Production"
        READY = "ready", "Ready for Dispatch"
        COMPLETE = "complete", "Completed"
        ON_HOLD = "on_hold", "On Hold"
        CANCELLED = "cancelled", "Cancelled"

    order_number = models.CharField(max_length=64, unique=True)
    customer_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1)
    due_date = models.DateField(null=True, blank=True)
    production_status = models.CharField(
        max_length=32,
        choices=ProductionStatus.choices,
        default=ProductionStatus.DRAFT,
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
    )
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
