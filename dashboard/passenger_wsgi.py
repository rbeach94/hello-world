"""WSGI entrypoint for Passenger deployments on Krystal cPanel."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR / "dashboard"

# Ensure the Django project and its dependencies are importable.
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(PROJECT_DIR))

try:  # pragma: no cover - optional dependency in production
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - fall back when python-dotenv is absent
    def load_dotenv(*args, **kwargs):  # type: ignore[override]
        return False

# Allow configuration via a `.env` file alongside this script.
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
