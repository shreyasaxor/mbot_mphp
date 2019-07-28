import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dsproject.settings')

app = Celery('Dsproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()