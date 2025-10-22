from django.contrib import admin

from .models import Order, OrderAuditTrail


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "production_status", "due_date", "assigned_staff")
    search_fields = ("order_number", "customer_name", "description")
    list_filter = ("production_status", "due_date")
    autocomplete_fields = ("assigned_staff",)


@admin.register(OrderAuditTrail)
class OrderAuditTrailAdmin(admin.ModelAdmin):
    list_display = ("order", "previous_status", "new_status", "user", "created_at")
    list_filter = ("new_status", "created_at")
    search_fields = ("order__order_number", "message")
