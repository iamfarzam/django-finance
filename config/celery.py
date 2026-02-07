"""Celery configuration for Django Finance.

This module configures Celery for asynchronous task processing.

Usage:
    # Start worker
    celery -A config worker -l INFO

    # Start beat scheduler
    celery -A config beat -l INFO

    # Start both (development only)
    celery -A config worker -l INFO -B
"""

import os

from celery import Celery
from celery.signals import setup_logging

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("django_finance")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure Celery to use Django's logging configuration."""
    from logging.config import dictConfig

    from django.conf import settings

    dictConfig(settings.LOGGING)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f"Request: {self.request!r}")
