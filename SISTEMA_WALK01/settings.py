# settings.py

# ...existing code...

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'contas',
    'professores',
    'cursos',
    'estudantes',
    'assessments.apps.AssessmentsConfig',
    'materiais',
    'blog',
    'attendance.apps.AttendanceConfig',
    'widget_tweaks',
]

# Email settings para desenvolvimento: exibe emails no console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'contato@sistemawalk.org'

# ...existing code...