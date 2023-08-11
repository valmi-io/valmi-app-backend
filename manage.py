#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from opentelemetry.instrumentation.django import DjangoInstrumentor
from core.observability import setup_observability


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'valmi_app_backend.settings')

    # Initialize the Opentelemetry Django instrumentation
    print("Setting up instrumentation")
    setup_observability()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
