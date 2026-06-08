import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Cargar configuraciones de celery desde settings.py usando prefijo 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodescubrir tareas en las aplicaciones de Django
app.autodiscover_tasks()
