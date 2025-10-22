from __future__ import annotations

from django.db import migrations, models


def _migrate_statuses(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    mapping = {
        "draft": "pending",
        "pending": "pending",
        "in_production": "ready",
        "ready": "ready",
        "complete": "complete",
        "on_hold": "pending",
        "cancelled": "complete",
    }
    for order in Order.objects.all():
        new_value = mapping.get(order.production_status, "pending")
        if order.production_status != new_value:
            order.production_status = new_value
            order.save(update_fields=["production_status"])
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(_migrate_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="production_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("awaiting_garments", "Awaiting Garments"),
                    ("ready", "Ready"),
                    ("complete", "Complete"),
                ],
                default="pending",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="decoration_type",
            field=models.CharField(
                choices=[
                    ("embroidery", "Embroidery"),
                    ("print", "Print"),
                    ("both", "Both"),
                ],
                default="print",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="preview_image_url",
            field=models.URLField(blank=True),
        ),
        migrations.CreateModel(
            name="OrderGarment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("colour", models.CharField(blank=True, max_length=128)),
                ("size", models.CharField(blank=True, max_length=64)),
                ("quantity", models.PositiveIntegerField(default=1)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("needs_ordering", "Needs Ordering"),
                            ("ordered", "Ordered"),
                            ("in_stock", "In Stock"),
                        ],
                        default="needs_ordering",
                        max_length=32,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="garments",
                        to="orders.order",
                    ),
                ),
            ],
            options={
                "ordering": ["order__due_date", "order__order_number", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["decoration_type"], name="order_decoration_idx"),
        ),
    ]
