from django.core.management.base import BaseCommand

from services.sheets_sync import sync_orders


class Command(BaseCommand):
    help = "Synchronise General Orders with Google Sheets"

    def handle(self, *args, **options):
        sync_orders()
        self.stdout.write(self.style.SUCCESS("Google Sheets synchronisation complete"))
