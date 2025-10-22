# Generated manually to establish initial schema for Orders app.
from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_number", models.CharField(max_length=64, unique=True)),
                ("customer_name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("due_date", models.DateField(blank=True, null=True)),
                (
                    "production_status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending", "Pending"),
                            ("in_production", "In Production"),
                            ("ready", "Ready for Dispatch"),
                            ("complete", "Completed"),
                            ("on_hold", "On Hold"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "external_reference",
                    models.CharField(
                        blank=True,
                        help_text="Link to the source system such as Google Sheets row ID.",
                        max_length=128,
                    ),
                ),
                (
                    "assigned_staff",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_orders",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["due_date", "order_number"],
            },
        ),
        migrations.CreateModel(
            name="OrderAuditTrail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("previous_status", models.CharField(blank=True, max_length=32)),
                ("new_status", models.CharField(blank=True, max_length=32)),
                ("message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "order",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_trail", to="orders.order"),
                ),
                (
                    "user",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["order_number"], name="order_number_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["production_status"], name="order_status_idx"),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["due_date"], name="order_due_date_idx"),
        ),
    ]
