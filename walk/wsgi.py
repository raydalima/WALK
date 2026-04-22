"""
WSGI entrypoint for WALK.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walk.settings')

application = get_wsgi_application()
