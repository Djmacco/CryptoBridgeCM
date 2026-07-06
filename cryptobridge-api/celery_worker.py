"""
Start the Celery worker:
  celery -A celery_worker.celery_app worker --loglevel=info

Start Flower dashboard (monitor jobs):
  celery -A celery_worker.celery_app flower --port=5555
"""
import os
from app import create_app
from app.extensions import celery_app, db

app = create_app(os.getenv('FLASK_ENV', 'development'))

class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery_app.Task = ContextTask
