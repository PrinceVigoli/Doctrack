"""
Celery application entry point.
Start worker with:
  celery -A config.celery worker --loglevel=info
Start beat scheduler with:
  celery -A config.celery beat --loglevel=info
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('doctrack')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
