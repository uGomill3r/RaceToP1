"""
Django settings for F1 Championship Visualizer backend.
Used only for data generation — no database, no server in production.
"""

SECRET_KEY = 'local-only-key-not-used-in-production'
DEBUG = True
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'app',
]
DATABASES = {}  # No database needed
