"""Django settings package.

Settings are loaded based on DJANGO_ENVIRONMENT environment variable:
- local: Development settings (default)
- test: Test environment settings
- production: Production settings
"""

import os

from config.env import settings as env

# Determine which settings module to use
_environment = env.environment

if _environment == "production":
    from config.settings.production import *  # noqa: F401, F403
elif _environment == "test":
    from config.settings.test import *  # noqa: F401, F403
else:
    from config.settings.local import *  # noqa: F401, F403
