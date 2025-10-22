#!/usr/bin/env python3
import os
import sys

from pathlib import Path

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard.settings")

    # Allow executing manage.py from any working directory by ensuring the
    # repository root (containing this file) is on sys.path.
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
