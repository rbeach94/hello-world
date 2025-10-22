from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "orders"
    verbose_name = "General Orders"

    def ready(self) -> None:  # pragma: no cover - import side effects
        from . import signals  # noqa: F401
