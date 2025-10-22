from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, OrderAuditTrail


def _user_from_kwargs(**kwargs: Any):
    request = kwargs.get("request")
    if request and request.user.is_authenticated:
        return request.user
    return None


@receiver(post_save, sender=Order)
def log_order_status_change(sender, instance: Order, created: bool, **kwargs: Any) -> None:
    """Record an audit log entry whenever an order's status changes."""
    if created:
        previous_status = ""
        message = "Order created"
    else:
        previous_status = getattr(instance, "_previous_status", instance.production_status)
        message = kwargs.get("message", "Order updated")

    if not settings.ENABLE_AUDIT_LOGGING:
        return

    if created or previous_status != instance.production_status:
        OrderAuditTrail.objects.create(
            order=instance,
            user=getattr(instance, "_acting_user", None),
            previous_status=previous_status,
            new_status=instance.production_status,
            message=message,
        )
