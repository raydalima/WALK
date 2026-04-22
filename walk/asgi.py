"""
ASGI entrypoint for WALK.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walk.settings')

application = get_asgi_application()
