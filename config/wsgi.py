"""WSGI config for Django Finance project.

This module exposes the WSGI callable as a module-level variable named ``application``.
This is a fallback for WSGI-only deployments (not recommended for this project).

For more information on this file, see:
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
