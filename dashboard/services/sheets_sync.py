"""Synchronisation utilities for the General Orders Google Sheet."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from django.conf import settings
from django.contrib.auth import get_user_model

try:  # pragma: no cover - optional dependency
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except Exception:  # pragma: no cover - optional dependency
    service_account = None
    build = None

from orders.models import Order

LOGGER = logging.getLogger(__name__)


@dataclass
class SheetOrder:
    order_number: str
    customer_name: str
    description: str
    quantity: int
    due_date: str
    production_status: str
    assigned_staff_email: str
    external_reference: str
    decoration_type: str = ""
    preview_image_url: str = ""


def _get_service():
    if not settings.GOOGLE_SHEETS_CREDENTIALS_FILE:
        raise RuntimeError("GOOGLE_SHEETS_CREDENTIALS_FILE is not configured")
    if service_account is None or build is None:
        raise RuntimeError("google-api-python-client is not installed in this environment")
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SHEETS_CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=credentials)


def fetch_sheet_rows() -> Iterable[SheetOrder]:
    """Yield `SheetOrder` records from the configured Google Sheet."""
    service = _get_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
        range=f"{settings.GOOGLE_SHEETS_WORKSHEET_NAME}!A2:J",
    ).execute()
    for row in result.get("values", []):
        yield SheetOrder(
            order_number=row[0],
            customer_name=row[1],
            description=row[2],
            quantity=int(row[3] or 0),
            due_date=row[4],
            production_status=row[5],
            assigned_staff_email=row[6],
            external_reference=row[7] if len(row) > 7 else "",
            decoration_type=row[8] if len(row) > 8 else "",
            preview_image_url=row[9] if len(row) > 9 else "",
        )


def _parse_due_date(value: str):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    LOGGER.warning("Unable to parse due date %s", value)
    return None


def _normalise_status(value: str) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower().replace(" ", "_")
    for choice, _ in Order.ProductionStatus.choices:
        if cleaned == choice:
            return choice
    for choice, label in Order.ProductionStatus.choices:
        if cleaned == label.lower().replace(" ", "_"):
            return choice
    LOGGER.warning("Unknown status %s from sheet", value)
    return None


def _normalise_decoration(value: str) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower().replace(" ", "_")
    for choice, _ in Order.DecorationType.choices:
        if cleaned == choice:
            return choice
    for choice, label in Order.DecorationType.choices:
        if cleaned == label.lower().replace(" ", "_"):
            return choice
    LOGGER.warning("Unknown decoration type %s from sheet", value)
    return None


def import_orders_from_sheet() -> int:
    """Create or update orders from the Google Sheet.

    Returns the number of orders synchronised.
    """
    count = 0
    User = get_user_model()
    for record in fetch_sheet_rows():
        order, created = Order.objects.get_or_create(
            order_number=record.order_number,
            defaults={
                "customer_name": record.customer_name,
                "description": record.description,
                "quantity": record.quantity,
            },
        )
        if not created:
            order.customer_name = record.customer_name
            order.description = record.description
            order.quantity = record.quantity
        order.external_reference = record.external_reference
        status = _normalise_status(record.production_status)
        if status:
            order.production_status = status
        due_date = _parse_due_date(record.due_date)
        if due_date:
            order.due_date = due_date
        decoration = _normalise_decoration(record.decoration_type)
        if decoration:
            order.decoration_type = decoration
        if record.preview_image_url:
            order.preview_image_url = record.preview_image_url
        if record.assigned_staff_email:
            try:
                order.assigned_staff = User.objects.get(email__iexact=record.assigned_staff_email)
            except User.DoesNotExist:
                LOGGER.warning("No user with email %s", record.assigned_staff_email)
        order.save()
        count += 1
    return count


def export_order_to_sheet(order: Order) -> None:
    """Write an updated order back to the Google Sheet."""
    if not order.external_reference:
        LOGGER.info("Order %s has no external reference; skipping export", order.order_number)
        return
    service = _get_service()
    sheet = service.spreadsheets()
    body = {
        "values": [
            [
                order.order_number,
                order.customer_name,
                order.description,
                order.quantity,
                order.due_date.isoformat() if order.due_date else "",
                order.production_status,
                order.assigned_staff.email if order.assigned_staff else "",
                order.external_reference,
                order.decoration_type,
                order.preview_image_url,
            ]
        ]
    }
    sheet.values().update(
        spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
        range=f"{settings.GOOGLE_SHEETS_WORKSHEET_NAME}!A{order.external_reference}",
        valueInputOption="RAW",
        body=body,
    ).execute()


def sync_orders() -> None:
    """High-level synchronisation helper intended for scheduled execution."""
    try:
        imported = import_orders_from_sheet()
        LOGGER.info("Imported %s orders from Google Sheets", imported)
    except Exception:  # pragma: no cover - log unexpected errors
        LOGGER.exception("Failed to import orders from Google Sheets")
