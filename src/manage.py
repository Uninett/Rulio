#!/usr/bin/env python3
"""Django's command-line utility for administrative tasks."""

import os
import sys

from backend.utils.logger import set_up_root_logger

logger = set_up_root_logger()
for h in logger.handlers:
    print(type(h), getattr(h, "baseFilename", None), h.level)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        logger.critical(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    logger.info("Root logger initialized")
    main()
