"""Django settings for the internal production dashboard."""
from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from a .env file if present. This makes it easier
# to configure the application in development while still supporting
# configuration via process environment variables in production.
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = json.loads(
    os.getenv("DJANGO_ALLOWED_HOSTS", '["ww.printoften.co.uk", "localhost", "127.0.0.1"]')
)
CSRF_TRUSTED_ORIGINS = json.loads(
    os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        '["https://ww.printoften.co.uk", "https://*.ww.printoften.co.uk"]',
    )
)

# Applications -----------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dashboard.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "dashboard.wsgi.application"
ASGI_APPLICATION = "dashboard.asgi.application"

# Database ---------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DJANGO_DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DJANGO_DB_USER", ""),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", ""),
        "HOST": os.getenv("DJANGO_DB_HOST", ""),
        "PORT": os.getenv("DJANGO_DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Europe/London")
USE_I18N = True
USE_TZ = True

STATIC_URL = os.getenv("DJANGO_STATIC_URL", "/static/")
STATIC_ROOT = Path(os.getenv("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles"))
STATICFILES_DIRS = [path for path in [BASE_DIR / "static"] if path.exists()]

if STATICFILES_DIRS:
    for path in STATICFILES_DIRS:
        path.mkdir(parents=True, exist_ok=True)

# When deployed behind Krystal's reverse proxy, honour the HTTPS header it sets.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session configuration ensures that logins expire after inactivity.
SESSION_COOKIE_AGE = int(timedelta(hours=int(os.getenv("DJANGO_SESSION_HOURS", "8"))).total_seconds())
SESSION_SAVE_EVERY_REQUEST = True

# Google Sheets API configuration ---------------------------------------------
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "")
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
GOOGLE_SHEETS_WORKSHEET_NAME = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "General Orders")

# Audit logging configuration: toggle via env var for testing flexibility.
ENABLE_AUDIT_LOGGING = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() in {"1", "true", "yes"}


def _configure_database_engine() -> None:
    default_db = DATABASES.get("default", {})
    engine = default_db.get("ENGINE", "")
    if engine.endswith("mysql"):
        default_db.setdefault("OPTIONS", {})
        default_db["OPTIONS"].setdefault("charset", "utf8mb4")
        default_db["OPTIONS"].setdefault("init_command", "SET sql_mode='STRICT_TRANS_TABLES'")
        try:  # pragma: no cover - import depends on optional dependency
            import pymysql

            pymysql.install_as_MySQLdb()
        except ImportError:  # pragma: no cover - handle missing dependency gracefully
            pass


_configure_database_engine()
